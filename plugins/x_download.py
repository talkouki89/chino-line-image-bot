import json
import re
import threading
from urllib.parse import urlparse, urlunparse

import requests


FEATURE_KEY = "x_download"
URL_RE = re.compile(r"https?://[^\s<>\"]+")
SUPPORTED_HOSTS = {
    "vxtwitter.com",
    "fxtwitter.com",
    "x.com",
    "twitter.com",
    "www.x.com",
    "www.twitter.com",
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
    parts = ctx.text.split(":", 1)
    url = extract_url(parts[1] if len(parts) == 2 else "")
    if not url:
        ctx.reply("請輸入 X/Twitter 網址。\n範例：x:https://x.com/user/status/123")
        return True
    send_x_media_async(ctx, url)
    return True


def handle_reply_x(ctx):
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("請回覆含有 X/Twitter 網址的訊息，再輸入 回覆搜x。")
        return True

    try:
        for recent in ctx.cl.getRecentMessagesV2(ctx.to, 1000):
            if recent.id != related_message_id:
                continue
            url = extract_supported_url(getattr(recent, "text", "") or "")
            if not url:
                url = extract_supported_url(json.dumps(str(recent), ensure_ascii=False))
            if not url:
                ctx.reply("找不到 X/Twitter 網址。")
                return True
            send_x_media_async(ctx, url)
            return True
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("回覆搜x 查詢失敗。")
        return True

    ctx.reply("找不到回覆的訊息。")
    return True


def send_x_media_async(ctx, original_url):
    threading.Thread(
        target=send_x_media,
        args=(ctx, original_url),
        daemon=True,
    ).start()


def send_x_media(ctx, original_url):
    try:
        media_urls = fetch_media_urls(original_url)
    except ValueError:
        ctx.reply("這不是支援的 X/Twitter 網址。\n支援 x.com、twitter.com、vxtwitter.com、fxtwitter.com。")
        return
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("X/Twitter 解析失敗，請確認網址是否正確或稍後再試。")
        return
    if not media_urls:
        ctx.reply("沒有找到可下載的 X/Twitter 圖片或影片。")
        return

    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, f"找到 {len(media_urls)} 個 X/Twitter 媒體，開始傳送。")
    failed = 0
    for media_url in media_urls:
        if not send_media_url(ctx, media_url):
            failed += 1
    if failed:
        ctx.reply(f"有 {failed} 個 X/Twitter 媒體傳送失敗。")


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
    return False


def detect_file_type(url):
    path = urlparse(url).path.lower()
    if path.endswith(".mp4"):
        return "video"
    if any(path.endswith(ext) for ext in MEDIA_IMAGE_EXTENSIONS):
        return "image"
    return "unknown"


def extract_url(value):
    match = URL_RE.search(str(value or ""))
    if not match:
        return ""
    return match.group(0).rstrip("。．，、；：！？.,;:!?)]}>\"'")


def extract_supported_url(value):
    for match in URL_RE.finditer(str(value or "")):
        url = match.group(0).rstrip("。．，、；：！？.,;:!?)]}>\"'")
        if is_supported_url(url):
            return url
    return ""
