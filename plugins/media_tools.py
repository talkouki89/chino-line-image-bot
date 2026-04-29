import json
import os
import re
import shutil
import tempfile
import threading
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

from plugins.core.cooldown import check_draw_cooldown
from plugins.core.text_convert import to_simplified, to_traditional
from plugins.core.x import detect_file_type, fetch_media_urls


FEATURE_KEY = "media_tools"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOLICON_API_URL = "https://api.lolicon.app/setu/v2"
URL_RE = re.compile(r"https?://[^\s<>\"]+")
RANDOM_IMAGE_COMMANDS = {
    "隨機圖": (0, False),
    "隨機色圖": (0, False),
    "一般色圖": (0, False),
    "test1": (0, False),
    "隨機無ai": (0, True),
    "無ai隨機圖": (0, True),
    "隨機圖無ai": (0, True),
    "隨機r18": (1, False),
    "r18色圖": (1, False),
    "色圖": (1, False),
    "test2": (1, False),
    "r18無ai": (1, True),
    "無ai r18": (1, True),
    "r18色圖無ai": (1, True),
}
TAG_IMAGE_PREFIXES = ("tag色圖", "色圖tag", "找色圖", "test3")


def handle(ctx):
    if ctx.cmd.startswith("x;"):
        return handle_x_url(ctx)
    if ctx.cmd == "回覆搜x":
        return handle_reply_x(ctx)
    if ctx.cmd.startswith("ytmp4:"):
        return handle_ytdlp(ctx)
    if ctx.cmd in RANDOM_IMAGE_COMMANDS:
        if not check_lolicon_cooldown(ctx):
            return True
        r18, exclude_ai = RANDOM_IMAGE_COMMANDS[ctx.cmd]
        return handle_random_lolicon(ctx, r18=r18, exclude_ai=exclude_ai)
    if ctx.cmd.startswith(TAG_IMAGE_PREFIXES):
        return handle_lolicon_tags(ctx)
    return False


def check_lolicon_cooldown(ctx):
    if getattr(ctx, "is_admin", False):
        return True
    allowed, remaining = check_draw_cooldown(ctx.sender)
    if not allowed:
        ctx.reply(f"抽圖冷卻中，請 {remaining} 秒後再試。")
        return False
    return True


def handle_x_url(ctx):
    parts = ctx.text.split(";", 1)
    url = extract_url(parts[1] if len(parts) == 2 else "")
    if not url:
        ctx.reply("請輸入 X/Twitter 網址。\n範例：x;https://x.com/user/status/123")
        return True
    send_x_media(ctx, url)
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
            url = extract_url(getattr(recent, "text", "") or "")
            if not url:
                url = extract_url(json.dumps(str(recent), ensure_ascii=False))
            if not url:
                ctx.reply("找不到 X/Twitter 網址。")
                return True
            send_x_media(ctx, url)
            return True
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("回覆搜x 查詢失敗。")
        return True

    ctx.reply("找不到回覆的訊息。")
    return True


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
    for index, media_url in enumerate(media_urls, start=1):
        if not send_media_url(ctx, media_url):
            failed += 1
    if failed:
        ctx.reply(f"有 {failed} 個 X/Twitter 媒體傳送失敗。")


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


def handle_ytdlp(ctx):
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入影片網址。\n範例：ytmp4:https://youtu.be/xxxx")
        return True
    if not is_http_url(url):
        ctx.reply("影片網址格式不正確。")
        return True
    threading.Thread(
        target=download_and_send_video,
        args=(ctx, url),
        daemon=True,
    ).start()
    return True


def download_and_send_video(ctx, url):
    temp_dir = tempfile.mkdtemp(prefix=f"chino-{ctx.sender}-")
    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, "開始下載影片，完成後會自動傳送。")
    try:
        output_file = download_video(url, temp_dir)
        ctx.cl.sendVideo(ctx.to, output_file)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("影片下載失敗，請確認網址是否可公開觀看，或稍後再試。")
    finally:
        safe_remove_tree(temp_dir)


def download_video(url, output_dir):
    load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
    ydl_opts = {
        # This bot usually runs without ffmpeg, so prefer a single mp4 file that
        # already contains both audio and video instead of split streams.
        "format": "best[ext=mp4][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "windowsfilenames": True,
    }
    cookies_file = os.getenv("YTDLP_COOKIES_FILE", "cookies.txt")
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        for item in info.get("requested_downloads") or []:
            path = item.get("filepath")
            if path and os.path.exists(path) and os.path.getsize(path) > 0:
                return path
        path = ydl.prepare_filename(info)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    for filename in os.listdir(output_dir):
        path = os.path.join(output_dir, filename)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    raise FileNotFoundError("yt-dlp did not create a downloadable video file")


def extract_url(value):
    match = URL_RE.search(str(value or ""))
    if not match:
        return ""
    return match.group(0).rstrip("。．，、；：！？.,;:!?)]}>\"'")


def is_http_url(url):
    parsed = urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def handle_random_lolicon(ctx, r18=0, exclude_ai=False):
    threading.Thread(
        target=send_random_lolicon_async,
        args=(ctx, r18, exclude_ai),
        daemon=True,
    ).start()
    return True


def send_random_lolicon_async(ctx, r18=0, exclude_ai=False):
    try:
        data = request_lolicon({"r18": r18, "excludeAI": exclude_ai})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("隨機色圖讀取失敗")
        return

    label = "R18 隨機色圖" if r18 else "一般隨機色圖"
    if exclude_ai:
        label += "（無 AI）"
    send_lolicon_result(ctx, data, label=label)


def handle_lolicon_tags(ctx):
    tags = extract_tag_query(ctx.text)
    if not tags:
        ctx.reply("請輸入標籤 範例:tag色圖 蘿莉")
        return True
    if not check_lolicon_cooldown(ctx):
        return True
    query_tags = [to_simplified(tag) for tag in tags.split()]
    display_tags = " ".join(to_traditional(tag) for tag in query_tags)
    try:
        data = request_lolicon({"tag": [[tag] for tag in query_tags], "r18": 1})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("tag 色圖讀取失敗")
        return True

    send_lolicon_result(ctx, data, label=f"Tag 色圖：{display_tags}")
    return True


def extract_tag_query(text):
    for prefix in TAG_IMAGE_PREFIXES:
        if text.lower().startswith(prefix):
            return text[len(prefix):].strip()
    return ""


def request_lolicon(extra_payload):
    payload = {
        "num": 1,
        "size": ["regular", "original"],
        "excludeAI": False,
    }
    payload.update(extra_payload)
    response = requests.post(
        LOLICON_API_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def send_lolicon_result(ctx, data, label):
    if not data.get("data"):
        ctx.reply("搜尋不到你的標籤 可以嘗試用簡體搜尋喔")
        return
    item = data["data"][0]
    urls = item.get("urls") or {}
    image_url = urls.get("regular") or urls.get("original")
    text = (
        str(label) +
        f"\n\n圖片標題⇛ {item.get('title')}"
        f"\n圖片作者⇛ {item.get('author')}"
        f"\n是否R18⇛ {format_bool_flag(item.get('r18'))}"
        f"\n是否AI⇛ {format_ai_flag(item.get('aiType'))}"
        f"\n圖源Url⇛ www.pixiv.net/artworks/{item.get('pid')}"
        "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و"
    )
    ctx.cl.relatedMessage(ctx.to, text, ctx.msg_id)
    if not image_url:
        ctx.reply("找不到圖片 URL")
        return
    try:
        ctx.cl.sendImageWithURL(ctx.to, image_url)
    except Exception as exc:
        # LINE sometimes raises even after the image was accepted. Log only so a
        # successful text/image response does not get followed by a false failure.
        ctx.log_error(exc)


def format_ai_flag(ai_type):
    try:
        return "否" if int(ai_type or 0) == 0 else "是"
    except (TypeError, ValueError):
        return "否" if not ai_type else "是"


def format_bool_flag(value):
    if isinstance(value, str):
        return "是" if value.strip().lower() in ("1", "true", "yes", "on") else "否"
    return "是" if bool(value) else "否"


def safe_remove(path):
    for _ in range(20):
        try:
            os.remove(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            import time
            time.sleep(0.25)


def safe_remove_tree(path):
    for _ in range(20):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            import time
            time.sleep(0.25)
