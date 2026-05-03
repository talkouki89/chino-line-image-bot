import contextlib
import io
import os
import re
import tempfile
import threading

import instaloader
from instaloader import Post
from instaloader.exceptions import ConnectionException, LoginRequiredException, QueryReturnedForbiddenException

from plugins.ytdlp_download import (
    download_media,
    download_urls,
    extract_url,
    is_http_url,
    safe_remove_tree,
    scan_output_files,
    send_files,
)


FEATURE_KEY = "instagram_download"
SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel|tv)/([^/?#]+)", re.IGNORECASE)
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".m4v", ".webm"}
MAX_INSTAGRAM_MEDIA = 20
ACCESS_LIMIT_MARKERS = (
    "403",
    "Forbidden",
    "login",
    "Login",
    "private",
    "Private",
    "restricted",
    "Restricted",
    "not found",
    "not exist",
    "Please wait",
    "rate limit",
    "checkpoint",
    "challenge",
    "metadata failed",
    "Fetching Post metadata failed",
    "too many files",
)


def handle(ctx):
    if not ctx.cmd.startswith("ig:"):
        return False
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入 Instagram 網址。\n範例：ig:https://www.instagram.com/p/xxxxx/")
        return True
    if not is_http_url(url) or "instagram.com" not in url.lower():
        ctx.reply("Instagram 網址格式不正確。")
        return True
    send_instagram_async(ctx, url)
    return True


def send_instagram_async(ctx, url):
    threading.Thread(
        target=download_and_send_instagram,
        args=(ctx, url),
        daemon=True,
    ).start()


def download_and_send_instagram(ctx, url):
    temp_dir = tempfile.mkdtemp(prefix=f"chino-ig-{ctx.sender}-")
    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, "開始下載 Instagram 媒體，完成後會自動傳送。")
    try:
        files, warning = download_instagram_media(url, temp_dir)
        if warning:
            ctx.reply(warning)
        if not files:
            ctx.reply("Instagram 下載失敗，可能是私人貼文、帳號限制、需要登入，或 Instagram 暫時阻擋解析。")
            return
        failed = send_files(ctx, files)
        if failed:
            ctx.reply(f"有 {failed} 個 Instagram 檔案傳送失敗。")
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("Instagram 下載失敗，請確認網址是否公開可看，或稍後再試。")
    finally:
        safe_remove_tree(temp_dir)


def download_instagram_media(url, output_dir):
    shortcode = extract_shortcode(url)
    instaloader_warning = ""
    if shortcode:
        try:
            download_with_instaloader(shortcode, output_dir)
            files = [path for path in scan_output_files(output_dir) if is_media_file(path)]
            if files:
                return files, ""
        except (LoginRequiredException, QueryReturnedForbiddenException, ConnectionException) as exc:
            instaloader_warning = instagram_blocked_message(exc)
            if is_instagram_access_limited(exc):
                return [], instaloader_warning
        except Exception as exc:
            instaloader_warning = instagram_blocked_message(exc)
            if is_instagram_access_limited(exc):
                return [], instaloader_warning
    files = download_media(url, output_dir, prefer_direct=True)
    if shortcode and len(files) > MAX_INSTAGRAM_MEDIA:
        return [], instagram_blocked_message("fallback collected too many files from instagram html")
    return files, instaloader_warning if not files else ""


def download_with_instaloader(shortcode, output_dir):
    loader = instaloader.Instaloader(
        quiet=True,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )
    session_user = os.getenv("INSTALOADER_SESSION_USER", "").strip()
    if session_user:
        loader.load_session_from_file(session_user)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        post = Post.from_shortcode(loader.context, shortcode)
        urls = instagram_post_media_urls(post)
        download_urls(urls, output_dir, referer=f"https://www.instagram.com/p/{shortcode}/")


def instagram_post_media_urls(post):
    if post.typename == "GraphSidecar":
        urls = []
        for node in post.get_sidecar_nodes():
            if getattr(node, "is_video", False) and getattr(node, "video_url", None):
                urls.append(node.video_url)
            elif getattr(node, "display_url", None):
                urls.append(node.display_url)
        return urls
    if post.is_video and post.video_url:
        return [post.video_url]
    return [post.url] if post.url else []


def instagram_blocked_message(exc):
    text = str(exc)
    if is_instagram_access_limited(exc):
        return "Instagram 下載失敗：這篇貼文或帳號可能有限制、需要登入、非公開，或 Instagram 暫時阻擋第三方解析。為避免傳出登入頁或錯誤圖片，這次不會改用 fallback 抓取。可先確認瀏覽器是否能開啟，或設定 INSTALOADER_SESSION_USER 登入 session 後再試。"
    return ""


def is_instagram_access_limited(exc):
    text = str(exc)
    return any(marker in text for marker in ACCESS_LIMIT_MARKERS)


def extract_shortcode(url):
    match = SHORTCODE_RE.search(str(url or ""))
    return match.group(1) if match else ""


def is_media_file(path):
    return os.path.splitext(path)[1].lower() in MEDIA_EXTENSIONS
