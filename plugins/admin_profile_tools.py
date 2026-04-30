import ast
import re
import subprocess
import sys
import threading


FEATURE_KEY = "admin_profile_tools"
MID_RE = re.compile(r"^mid:([A-Za-z0-9_-]+)$")
FALLBACK_IMAGE = "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png"


def handle(ctx):
    if ctx.cmd in {"speedtest", "測速"}:
        if not ctx.is_admin:
            return True
        threading.Thread(target=run_speedtest, args=(ctx,), daemon=True).start()
        return True
    if ctx.cmd.startswith("mid:"):
        if not ctx.is_admin:
            return True
        return handle_mid_lookup(ctx)
    if ctx.cmd.startswith("contact "):
        if not ctx.is_admin:
            return True
        return handle_contact_mention(ctx)
    return False


def handle_mid_lookup(ctx):
    match = MID_RE.match(ctx.text.strip())
    if not match:
        ctx.reply("請輸入 MID，範例：mid:u1234567890")
        return True
    send_contact_template(ctx, match.group(1))
    return True


def handle_contact_mention(ctx):
    mids = parse_mentions(getattr(ctx.msg, "contentMetadata", None))
    if not mids:
        ctx.reply("請標註要查詢的人，範例：Contact @使用者")
        return True
    send_contact_template(ctx, mids[0])
    return True


def send_contact_template(ctx, mid):
    try:
        contact = ctx.cl.getContact(mid)
        ctx.send_template(ctx.to, build_contact_template(ctx, contact, mid))
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("好友資料查詢失敗，請確認 MID 或標註對象是否正確。")


def build_contact_template(ctx, contact, mid):
    name = value(contact, "displayName", "name", default="未知")
    status = value(contact, "statusMessage", default="未設定")
    picture = profile_image_url(contact)
    cover = profile_cover_url(ctx, mid) or picture
    return {
        "type": "flex",
        "altText": f"{name} 的好友資料",
        "contents": {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": cover or FALLBACK_IMAGE,
                "size": "full",
                "aspectRatio": "20:9",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "paddingAll": "18px",
                "contents": [
                    {"type": "text", "text": name, "weight": "bold", "size": "xl", "wrap": True, "color": "#111827"},
                    {"type": "text", "text": status or "未設定狀態消息", "size": "sm", "wrap": True, "color": "#6b7280"},
                    {"type": "separator"},
                    row("MID", mid),
                    row("名稱", name),
                    row("狀態消息", status or "未設定"),
                    row("頭貼", picture or "無"),
                    row("封面", cover or "無"),
                ],
            },
        },
    }


def row(label, text):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "xs",
        "contents": [
            {"type": "text", "text": label, "size": "xs", "color": "#6b7280"},
            {"type": "text", "text": str(text), "size": "sm", "wrap": True, "color": "#111827"},
        ],
    }


def run_speedtest(ctx):
    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, "開始測速，完成後會回傳結果圖片。")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "speedtest", "--share", "--simple"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        output = (result.stdout or "") + "\n" + (result.stderr or "")
        image_url = find_speedtest_image(output)
        if image_url:
            ctx.cl.sendImageWithURL(ctx.to, image_url)
            ctx.cl.relatedMessage(ctx.to, cleanup_speedtest_text(output), ctx.msg_id)
            return
        ctx.reply("測速失敗，無法取得結果圖片。\n請確認已安裝 speedtest-cli。")
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("測速失敗，請稍後再試。")


def find_speedtest_image(output):
    for token in str(output).split():
        if "speedtest.net/result/" in token:
            token = token.strip()
            if not token.endswith(".png"):
                token = token.rstrip("/") + ".png"
            return token.replace("http://", "https://")
    return ""


def cleanup_speedtest_text(output):
    lines = [line.strip() for line in str(output).splitlines() if line.strip()]
    return "\n".join(lines[:8]) or "測速完成。"


def parse_mentions(content_metadata):
    if not content_metadata or "MENTION" not in content_metadata:
        return []
    try:
        mention = ast.literal_eval(content_metadata["MENTION"])
    except Exception:
        return []
    return [item.get("M") for item in mention.get("MENTIONEES", []) if item.get("M")]


def value(obj, *names, default=""):
    for name in names:
        try:
            data = getattr(obj, name)
        except Exception:
            data = None
        if data:
            return data
    return default


def profile_image_url(contact):
    thumbnail = value(contact, "thumbnailUrl", default="")
    if thumbnail:
        return str(thumbnail).replace("http://", "https://")
    picture_status = value(contact, "pictureStatus", default="")
    if picture_status:
        return f"https://dl.profile.line-cdn.net/{picture_status}"
    return FALLBACK_IMAGE


def profile_cover_url(ctx, mid):
    try:
        data = ctx.cl.getProfileCoverObjIdAndUrl(mid)
        if isinstance(data, (list, tuple)) and data:
            url = data[0]
            if url:
                return str(url).replace("http://", "https://")
    except Exception:
        return ""
    return ""
