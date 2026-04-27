import json
import os
import re

import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

from plugins.core.x import detect_file_type, fetch_media_urls


FEATURE_KEY = "media_tools"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOLICON_API_URL = "https://api.lolicon.app/setu/v2"
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
TAG_IMAGE_PREFIXES = ("tag色圖 ", "色圖tag ", "找色圖 ", "test3 ")


def handle(ctx):
    if ctx.cmd.startswith("x;"):
        return handle_x_url(ctx)
    if ctx.cmd == "回覆搜x":
        return handle_reply_x(ctx)
    if ctx.cmd.startswith("ytmp4:"):
        return handle_ytdlp(ctx)
    if ctx.cmd in RANDOM_IMAGE_COMMANDS:
        r18, exclude_ai = RANDOM_IMAGE_COMMANDS[ctx.cmd]
        return handle_random_lolicon(ctx, r18=r18, exclude_ai=exclude_ai)
    if ctx.cmd.startswith(TAG_IMAGE_PREFIXES):
        return handle_lolicon_tags(ctx)
    if ctx.cmd == "誰標我":
        return handle_who_mentioned_me(ctx)
    if ctx.cmd == "清空標註":
        return handle_clear_mentions(ctx)
    return False


def handle_x_url(ctx):
    if not ctx.is_creator:
        ctx.reply("此為作者使用功能٩(ˊᗜˋ*)و")
        return True
    parts = ctx.text.split(";", 1)
    if len(parts) < 2 or not parts[1].strip():
        ctx.reply("請輸入 X/Twitter 網址。")
        return True
    send_x_media(ctx, parts[1].strip())
    return True


def handle_reply_x(ctx):
    if not ctx.is_creator:
        ctx.reply("此為作者使用功能٩(ˊᗜˋ*)و")
        return True
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("需回覆訊息來查詢")
        return True

    try:
        for recent in ctx.cl.getRecentMessagesV2(ctx.to, 1000):
            if recent.id != related_message_id:
                continue
            match = re.search(r"text='(https?://\S+)'", json.dumps(str(recent)))
            if not match:
                ctx.reply("找不到網址")
                return True
            send_x_media(ctx, match.group(1))
            return True
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("查詢失敗")
        return True

    ctx.reply("找不到回覆的訊息")
    return True


def send_x_media(ctx, original_url):
    try:
        media_urls = fetch_media_urls(original_url)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("X/Twitter 解析失敗，請確認網址是否正確")
        return
    if not media_urls:
        ctx.reply("沒有找到可下載的 X/Twitter 媒體")
        return
    for media_url in media_urls:
        send_media_url(ctx, media_url)


def send_media_url(ctx, media_url):
    media_type = detect_file_type(media_url)
    if media_type == "video":
        ctx.cl.sendVideoWithURL(ctx.to, media_url)
    elif media_type == "image":
        ctx.cl.sendImageWithURL(ctx.to, media_url)
    else:
        ctx.reply("不支援的媒體格式")


def handle_ytdlp(ctx):
    url = ctx.text.split(":", 1)[1].strip()
    if not url:
        ctx.reply("請輸入影片網址。")
        return True
    output_file = f"{ctx.sender}.mp4"
    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, "開始下載影片")
    try:
        download_video(url, output_file)
        ctx.cl.sendVideo(ctx.to, output_file)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("影片下載失敗")
    finally:
        safe_remove(output_file)
    return True


def download_video(url, output_file):
    load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
    ydl_opts = {"format": "best", "outtmpl": output_file}
    cookies_file = os.getenv("YTDLP_COOKIES_FILE", "cookies.txt")
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def handle_random_lolicon(ctx, r18=0, exclude_ai=False):
    if not ctx.is_creator:
        return True
    try:
        data = request_lolicon({"r18": r18, "excludeAI": exclude_ai})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("隨機色圖讀取失敗")
        return True

    label = "R18 隨機色圖" if r18 else "一般隨機色圖"
    if exclude_ai:
        label += "（無 AI）"
    send_lolicon_result(ctx, data, label=label)
    return True


def handle_lolicon_tags(ctx):
    if not ctx.is_creator:
        return True
    tags = extract_tag_query(ctx.text)
    if not tags:
        ctx.reply("請輸入 tag，例如：tag色圖 貓耳")
        return True
    try:
        data = request_lolicon({"tag": [[tag] for tag in tags.split()], "r18": 1})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("tag 色圖讀取失敗")
        return True

    send_lolicon_result(ctx, data, label=f"Tag 色圖：{tags}")
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
        ctx.reply("No data found in response.")
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


def handle_who_mentioned_me(ctx):
    tag_file = os.path.join(ctx.tag_dir, f"{ctx.sender}.json")
    if not os.path.isfile(tag_file):
        ctx.cl.sendMessage(ctx.to, "沒人要標你")
        return True

    with open(tag_file, "r", encoding="utf-8") as fp:
        who_mark_me = json.load(fp)

    if ctx.to not in who_mark_me or not who_mark_me[ctx.to]:
        ctx.cl.sendMessage(ctx.to, "沒人要標你")
        return True

    tag_num = len(who_mark_me[ctx.to])
    latest = who_mark_me[ctx.to].get(str(tag_num))
    if not latest:
        ctx.cl.sendMessage(ctx.to, "沒人要標你")
        return True

    contact = ctx.cl.getContact(str(latest["sender"]))
    message = (
        "上一位標註者\n"
        f"{contact.displayName}\n"
        f"時間：{latest['tagtime']}\n"
        f"剩餘查詢次數：{tag_num - 1}"
    )
    ctx.cl.relatedMessage(ctx.to, message, latest["msgid"])
    del who_mark_me[ctx.to][str(tag_num)]
    with open(tag_file, "w", encoding="utf-8") as fp:
        json.dump(who_mark_me, fp, sort_keys=True, indent=4, ensure_ascii=False)
    return True


def handle_clear_mentions(ctx):
    tag_file = os.path.join(ctx.tag_dir, f"{ctx.sender}.json")
    try:
        os.remove(tag_file)
        ctx.cl.sendMessage(ctx.to, "成功")
    except FileNotFoundError:
        ctx.reply("沒東西清")
    return True


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
