import json
import re
import tempfile
import threading
from urllib.parse import urlparse, urlunparse

import requests

from plugins.ytdlp_download import download_urls, safe_remove_tree, scan_output_files, send_image_files


FEATURE_KEY = "x_download"
URL_RE = re.compile(r"https?://[^\s<>\"]+")
SUPPORTED_HOSTS = {
    "vxtwitter.com",
    "fxtwitter.com",
    "fixvx.com",
    "fixupx.com",
    "x.com",
    "twitter.com",
    "www.x.com",
    "www.twitter.com",
    "www.fixvx.com",
    "www.fixupx.com",
    "mobile.twitter.com",
}
MEDIA_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def handle(ctx):
    if ctx.cmd.startswith("x:"):
        return handle_x_url(ctx)
    if ctx.cmd == "回覆搜x":
        return handle_reply_x(ctx)
    return False


def handle_x_url(ctx):
    value = ctx.text.split(":", 1)[1] if ":" in ctx.text else ""
    urls = extract_supported_urls(value)
    if not urls:
        ctx.reply("請輸入 X/Twitter 網址。\n範例：x:https://x.com/user/status/123")
        return True
    send_x_media_async(ctx, urls)
    return True


def handle_reply_x(ctx):
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("請回覆含有 X/Twitter 網址的訊息，再輸入回覆搜x。")
        return True

    try:
        for recent in ctx.cl.getRecentMessagesV2(ctx.to, 1000):
            if str(getattr(recent, "id", "")) != str(related_message_id):
                continue
            urls = extract_supported_urls(getattr(recent, "text", "") or "")
            if not urls:
                urls = extract_supported_urls(json.dumps(str(recent), ensure_ascii=False))
            if not urls:
                ctx.reply("找不到 X/Twitter 網址。")
                return True
            send_x_media_async(ctx, urls)
            return True
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("回覆搜x 查詢失敗。")
        return True

    ctx.reply("找不到原始回覆訊息。")
    return True


def send_x_media_async(ctx, original_urls):
    threading.Thread(
        target=send_x_media,
        args=(ctx, list(dict.fromkeys(original_urls))),
        daemon=True,
    ).start()


def send_x_media(ctx, original_urls):
    temp_dir = tempfile.mkdtemp(prefix=f"chino-x-{ctx.sender}-")
    try:
        image_urls = []
        video_urls = []
        failed_sources = []
        for original_url in original_urls:
            try:
                media_urls = fetch_media_urls(original_url)
            except ValueError:
                failed_sources.append(original_url)
                continue
            except Exception as exc:
                ctx.log_error(exc)
                failed_sources.append(original_url)
                continue
            for media_url in media_urls:
                media_type = detect_file_type(media_url)
                if media_type == "image":
                    image_urls.append(media_url)
                elif media_type == "video":
                    video_urls.append(media_url)

        image_urls = list(dict.fromkeys(image_urls))
        video_urls = list(dict.fromkeys(video_urls))
        total = len(image_urls) + len(video_urls)
        if not total:
            ctx.reply("沒有找到可傳送的 X/Twitter 圖片或影片。")
            return

        ctx.cl.sendReplyMessage(
            ctx.msg_id,
            ctx.to,
            f"找到 {total} 個 X/Twitter 媒體，開始傳送。",
        )
        failed = 0
        if image_urls:
            download_urls(image_urls, temp_dir, referer=original_urls[0])
            image_files = [path for path in scan_output_files(temp_dir) if detect_file_type(path) == "image"]
            if image_files:
                if not send_image_files(ctx, image_files):
                    failed += len(image_files)
                    if getattr(ctx.msg, "toType", None) == 0:
                        ctx.reply("私訊可能因為 E2EE/Letter Sealing 無法傳送影片，請直接開啟：\n" + "\n".join(image_urls))
            else:
                failed += len(image_urls)

        for media_url in video_urls:
            if not send_media_url(ctx, media_url):
                failed += 1

        if failed_sources:
            ctx.reply("有部分 X/Twitter 網址解析失敗：\n" + "\n".join(failed_sources[:5]))
        if failed:
            ctx.reply(f"有 {failed} 個 X/Twitter 媒體傳送失敗。")
    finally:
        safe_remove_tree(temp_dir)


def convert_url(original_url):
    parsed = urlparse(original_url.strip())
    host = parsed.netloc.lower()
    if parsed.scheme not in {"http", "https"} or host not in SUPPORTED_HOSTS:
        raise ValueError("Only X/Twitter URLs are supported")
    return urlunparse(parsed._replace(scheme="https", netloc="api.vxtwitter.com"))


def is_supported_url(url):
    if not url:
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in {"http", "https"} and parsed.netloc.lower() in SUPPORTED_HOSTS


def fetch_media_urls(original_url, timeout=20):
    response = requests.get(
        convert_url(original_url),
        headers={"User-Agent": "chino-line-image-bot"},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("mediaURLs", [])


def send_media_url(ctx, media_url):
    media_type = detect_file_type(media_url)
    try:
        if media_type == "video":
            ctx.cl.sendVideoWithURL(ctx.to, media_url)
            return True
        if media_type == "image":
            ctx.cl.sendImageWithURL(ctx.to, media_url)
            return True
        ctx.reply(f"不支援的媒體格式：{media_url}")
    except Exception as exc:
        ctx.log_error(exc)
        if is_private_e2ee_send_error(ctx, exc):
            ctx.reply(f"私訊可能因為 E2EE/Letter Sealing 無法傳送影片，請直接開啟：\n{media_url}")
    return False


def is_private_e2ee_send_error(ctx, exc):
    if getattr(ctx.msg, "toType", None) != 0:
        return False
    text = str(exc)
    return "can not send using plain mode" in text or "selfKey should not be None" in text


def detect_file_type(url):
    path = urlparse(str(url)).path.lower()
    if path.endswith(".mp4"):
        return "video"
    if any(path.endswith(ext) for ext in MEDIA_IMAGE_EXTENSIONS):
        return "image"
    return "unknown"


def extract_url(value):
    urls = extract_urls(value)
    return urls[0] if urls else ""


def extract_urls(value):
    urls = []
    for match in URL_RE.finditer(str(value or "")):
        urls.append(match.group(0).rstrip("，。！？、；：,.!?)]}>\"'"))
    return urls


def extract_supported_url(value):
    urls = extract_supported_urls(value)
    return urls[0] if urls else ""


def extract_supported_urls(value):
    return [url for url in extract_urls(value) if is_supported_url(url)]
