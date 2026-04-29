import os
import tempfile

from plugins.core.freeimage import FreeimageHost


FEATURE_KEY = "freeimage_upload"
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
        try:
            ctx.cl.downloadReplyImage(ctx.to, related_message_id, saveAs=tmp_path, objFrom=ctx.to)
        except Exception as exc:
            if getattr(ctx.msg, "toType", None) == 0:
                raise RuntimeError("私訊 E2EE 圖片解密失敗，請確認 Bot 已收到該圖片或重傳後再試。") from exc
            if "Invalid response code: 404" in str(exc) and "/talk/m/" in str(exc):
                raise RuntimeError("圖片下載失敗：此聊天室可能是 OpenChat，已改用聊天室 ID 判斷下載路徑；請重傳圖片後再試一次。") from exc
            raise
        result = FreeimageHost(ctx.cl).upload(
            tmp_path,
            title=f"LINE upload by {ctx.sender}",
            description=f"Uploaded from chat {ctx.to}",
        )
        image = result.get("image") or {}
        viewer_link = image.get("url_viewer") or image.get("url_short")
        direct_link = image.get("url") or image.get("display_url")
        if not viewer_link and not direct_link:
            raise RuntimeError(result)
        lines = ["圖片上傳完成："]
        if viewer_link:
            lines.append(f"頁面連結：{viewer_link}")
        if direct_link:
            lines.append(f"圖片URL：{direct_link}")
        ctx.cl.relatedMessage(ctx.to, "\n".join(lines), ctx.msg_id)
    except Exception as exc:
        ctx.log_error(exc)
        if "私訊 E2EE" in str(exc) or str(exc).startswith("圖片下載失敗："):
            ctx.reply(str(exc))
        else:
            ctx.reply("圖片上傳失敗，請確認已設定 FREEIMAGE_API_KEY。")
    finally:
        safe_remove(tmp_path)
    return True


def make_temp_path(sender):
    safe_sender = "".join(ch for ch in str(sender) if ch.isalnum() or ch in ("_", "-"))[:48]
    return os.path.join(tempfile.gettempdir(), f"line_freeimage_{safe_sender or 'upload'}.jpg")


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
