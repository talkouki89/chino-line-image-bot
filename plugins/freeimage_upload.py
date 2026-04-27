import os
import tempfile

from plugins.core.freeimage import FreeimageHost


COMMANDS = {"#圖片上傳", "圖片上傳", "#上傳圖片"}


def handle(ctx):
    if ctx.cmd.strip() not in COMMANDS:
        return False

    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("請回覆一張圖片後輸入 #圖片上傳")
        return True

    tmp_path = make_temp_path(ctx.sender)
    try:
        ctx.cl.downloadObjectMsg(related_message_id, saveAs=tmp_path)
        result = FreeimageHost(ctx.cl).upload(
            tmp_path,
            title=f"LINE upload by {ctx.sender}",
            description=f"Uploaded from chat {ctx.to}",
        )
        image = result.get("image") or {}
        link = image.get("url_viewer") or image.get("url") or image.get("display_url")
        if not link:
            raise RuntimeError(result)
        ctx.cl.relatedMessage(ctx.to, f"圖片上傳完成：\n{link}", ctx.msg_id)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("圖片上傳失敗，請確認已設定 FREEIMAGE_API_KEY。")
    finally:
        safe_remove(tmp_path)
    return True


def make_temp_path(sender):
    safe_sender = "".join(ch for ch in str(sender) if ch.isalnum() or ch in ("_", "-"))[:48]
    return os.path.join(tempfile.gettempdir(), f"line_freeimage_{safe_sender or 'upload'}.jpg")


def safe_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
