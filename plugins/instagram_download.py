import os
import re
import tempfile
import threading

import instaloader
from instaloader import Post

from plugins.ytdlp_download import (
    download_media,
    download_urls,
    extract_url,
    is_http_url,
    safe_remove_tree,
    scan_output_files,
    send_file,
)


FEATURE_KEY = "instagram_download"
SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel|tv)/([^/?#]+)", re.IGNORECASE)
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".m4v", ".webm"}


def handle(ctx):
    if not ctx.cmd.startswith("ig:"):
        return False
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入 Instagram 連結。\n範例：ig:https://www.instagram.com/p/xxxxx/")
        return True
    if not is_http_url(url) or "instagram.com" not in url.lower():
        ctx.reply("Instagram 連結格式不正確。")
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
        files = download_instagram_media(url, temp_dir)
        if not files:
            ctx.reply("Instagram 下載失敗，可能是私人貼文、需要登入或連結已失效。")
            return
        failed = 0
        for path in files:
            if not send_file(ctx, path):
                failed += 1
        if failed:
            ctx.reply(f"有 {failed} 個 Instagram 檔案傳送失敗。")
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("Instagram 下載失敗，請確認連結是否公開或稍後再試。")
    finally:
        safe_remove_tree(temp_dir)


def download_instagram_media(url, output_dir):
    shortcode = extract_shortcode(url)
    if shortcode:
        try:
            download_with_instaloader(shortcode, output_dir)
            files = [path for path in scan_output_files(output_dir) if is_media_file(path)]
            if files:
                return files
        except Exception:
            pass
    return download_media(url, output_dir, prefer_direct=True)


def download_with_instaloader(shortcode, output_dir):
    loader = instaloader.Instaloader(
        quiet=True,
    )
    session_user = os.getenv("INSTALOADER_SESSION_USER", "").strip()
    if session_user:
        loader.load_session_from_file(session_user)
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


def extract_shortcode(url):
    match = SHORTCODE_RE.search(str(url or ""))
    return match.group(1) if match else ""


def is_media_file(path):
    return os.path.splitext(path)[1].lower() in MEDIA_EXTENSIONS
