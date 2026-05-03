import json

from plugins.instagram_download import send_instagram_async
from plugins.ytdlp_download import extract_url, is_http_url, send_ytdlp_media_async


COMMANDS = {
    "回覆搜yt": {
        "label": "影片",
        "hosts": (),
        "send": lambda ctx, url: send_ytdlp_media_async(ctx, url, label="影片"),
    },
    "回覆搜fb": {
        "label": "Facebook 影片",
        "hosts": ("facebook.com", "fb.watch"),
        "send": lambda ctx, url: send_ytdlp_media_async(ctx, url, label="Facebook 影片"),
    },
    "回覆搜ph": {
        "label": "Pornhub 影片",
        "hosts": ("pornhub.com",),
        "send": lambda ctx, url: send_ytdlp_media_async(ctx, url, label="Pornhub 影片"),
    },
    "回覆搜ig": {
        "label": "Instagram 媒體",
        "hosts": ("instagram.com",),
        "send": lambda ctx, url: send_instagram_async(ctx, url),
    },
}


def handle(ctx):
    if ctx.cmd not in COMMANDS:
        return False
    return handle_reply_download(ctx, COMMANDS[ctx.cmd])


def handle_reply_download(ctx, config):
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply(f"請回覆含有網址的訊息，再輸入 {ctx.cmd}。")
        return True
    try:
        for recent in ctx.cl.getRecentMessagesV2(ctx.to, 1000):
            if str(getattr(recent, "id", "")) != str(related_message_id):
                continue
            url = find_matching_url(getattr(recent, "text", "") or "", config["hosts"])
            if not url:
                url = find_matching_url(json.dumps(str(recent), ensure_ascii=False), config["hosts"])
            if not url:
                ctx.reply(f"找不到可用的{config['label']}網址。")
                return True
            config["send"](ctx, url)
            return True
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply(f"{ctx.cmd} 查詢失敗。")
        return True
    ctx.reply("找不到原始回覆訊息。")
    return True


def find_matching_url(value, hosts):
    text = str(value or "")
    while text:
        url = extract_url(text)
        if not url:
            return ""
        if is_http_url(url) and host_allowed(url, hosts):
            return url
        text = text[text.find(url) + len(url):]
    return ""


def host_allowed(url, hosts):
    if not hosts:
        return True
    lowered = url.lower()
    return any(host in lowered for host in hosts)
