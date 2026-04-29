# -*- coding: utf-8 -*-

import os
import tempfile
import threading
import time


FEATURE_KEY = "broadcast"
BROADCAST_PREFIX = "群發"
CONFIRM_COMMAND = "確認群發"
CANCEL_COMMAND = "取消群發"
STATUS_COMMAND = "群發狀態"
SEND_INTERVAL_SECONDS = 1

_pending = {}
_jobs = {}
_lock = threading.Lock()


def handle(ctx):
    command = ctx.cmd.strip()
    if command == STATUS_COMMAND:
        return handle_status(ctx)
    if command == CANCEL_COMMAND:
        return handle_cancel(ctx)
    if command == CONFIRM_COMMAND:
        return handle_confirm(ctx)
    if command == BROADCAST_PREFIX or command.startswith(BROADCAST_PREFIX + " "):
        return handle_preview(ctx)
    return False


def require_admin(ctx):
    if getattr(ctx, "is_admin", False):
        return True
    ctx.reply("此功能只有管理員可以使用。")
    return False


def handle_preview(ctx):
    if not require_admin(ctx):
        return True
    text = ctx.text.strip()[len(BROADCAST_PREFIX):].strip()
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    media = None
    if related_message_id:
        try:
            media = download_related_media(ctx, related_message_id)
        except Exception as exc:
            ctx.log_error(exc)
            ctx.reply(f"群發媒體讀取失敗：{exc}")
            return True
    if not text and not media:
        ctx.reply("請輸入群發內容，或回覆圖片/影片後輸入：群發 文字")
        return True

    targets = broadcast_targets(ctx)
    if not targets:
        cleanup_media(media)
        ctx.reply("找不到可群發的群組。")
        return True

    with _lock:
        cleanup_media(_pending.pop(ctx.sender, {}).get("media"))
        _pending[ctx.sender] = {
            "text": text,
            "media": media,
            "targets": targets,
            "created_at": time.time(),
        }

    ctx.reply(preview_text(text, media, targets))
    if media:
        send_media(ctx, ctx.to, media)
    return True


def handle_confirm(ctx):
    if not require_admin(ctx):
        return True
    with _lock:
        if ctx.sender in _jobs and _jobs[ctx.sender].get("running"):
            ctx.reply("已有群發任務執行中，請等待完成。")
            return True
        task = _pending.pop(ctx.sender, None)
        if not task:
            ctx.reply("目前沒有待確認的群發。請先輸入：群發 內容")
            return True
        _jobs[ctx.sender] = {"running": True, "sent": 0, "total": len(task["targets"]), "failed": 0}

    threading.Thread(target=run_broadcast, args=(ctx, task), daemon=True).start()
    ctx.reply(f"已開始群發，共 {len(task['targets'])} 個群組；每 {SEND_INTERVAL_SECONDS} 秒發送 1 個。")
    return True


def handle_cancel(ctx):
    if not require_admin(ctx):
        return True
    with _lock:
        task = _pending.pop(ctx.sender, None)
    cleanup_media(task.get("media") if task else None)
    ctx.reply("已取消待確認群發。" if task else "目前沒有待確認的群發。")
    return True


def handle_status(ctx):
    if not require_admin(ctx):
        return True
    with _lock:
        pending = _pending.get(ctx.sender)
        job = _jobs.get(ctx.sender)
    if job and job.get("running"):
        ctx.reply(f"群發中：{job['sent']}/{job['total']}，失敗 {job['failed']}。")
    elif pending:
        ctx.reply(f"有待確認群發：共 {len(pending['targets'])} 個群組。輸入「確認群發」開始，或「取消群發」取消。")
    else:
        ctx.reply("目前沒有群發任務。")
    return True


def run_broadcast(ctx, task):
    failed = 0
    try:
        for index, target in enumerate(task["targets"], start=1):
            try:
                if task["text"]:
                    ctx.cl.sendMessage(target, task["text"])
                if task["media"]:
                    send_media(ctx, target, task["media"])
            except Exception as exc:
                failed += 1
                ctx.log_error(exc)
            with _lock:
                job = _jobs.get(ctx.sender)
                if job:
                    job["sent"] = index
                    job["failed"] = failed
            if index < len(task["targets"]):
                time.sleep(SEND_INTERVAL_SECONDS)
        ctx.cl.sendMessage(ctx.to, f"群發完成：成功 {len(task['targets']) - failed}，失敗 {failed}。")
    finally:
        cleanup_media(task.get("media"))
        with _lock:
            _jobs.pop(ctx.sender, None)


def broadcast_targets(ctx):
    response = ctx.cl.getAllChatMids()
    mids = list(getattr(response, "memberChatMids", []) or [])
    return [mid for mid in mids if str(mid).startswith(("c", "r"))]


def preview_text(text, media, targets):
    media_text = "無"
    if media:
        media_text = "圖片" if media["type"] == "image" else "影片"
    return (
        "群發預覽\n"
        f"群組數量：{len(targets)}\n"
        f"文字：{text or '無'}\n"
        f"媒體：{media_text}\n\n"
        "確認請輸入：確認群發\n"
        "取消請輸入：取消群發"
    )


def download_related_media(ctx, message_id):
    message = find_recent_message(ctx, message_id)
    content_type = getattr(message, "contentType", None)
    if content_type == 1:
        path = temp_media_path(ctx.sender, ".jpg")
        ctx.cl.downloadReplyImage(ctx.to, message_id, saveAs=path, objFrom=ctx.to)
        return {"type": "image", "path": path}
    if content_type == 2:
        path = temp_media_path(ctx.sender, ".mp4")
        ctx.cl.downloadObjectMsg(message_id, returnAs="path", saveAs=path, objFrom=ctx.to)
        return {"type": "video", "path": path}
    raise RuntimeError("目前只支援回覆圖片或影片。")


def find_recent_message(ctx, message_id):
    for message in ctx.cl.getRecentMessagesV2(ctx.to, 1000):
        if str(getattr(message, "id", "")) == str(message_id):
            return message
    raise RuntimeError("找不到回覆的訊息，請重傳圖片/影片後再試。")


def send_media(ctx, to, media):
    if media["type"] == "image":
        return ctx.cl.sendImage(to, media["path"])
    if media["type"] == "video":
        return ctx.cl.sendVideo(to, media["path"])
    raise RuntimeError(f"不支援的媒體類型：{media['type']}")


def temp_media_path(sender, suffix):
    safe_sender = "".join(ch for ch in str(sender) if ch.isalnum() or ch in ("_", "-"))[:48]
    fd, path = tempfile.mkstemp(prefix=f"line_broadcast_{safe_sender or 'admin'}_", suffix=suffix)
    os.close(fd)
    return path


def cleanup_media(media):
    if not media:
        return
    try:
        os.remove(media.get("path", ""))
    except FileNotFoundError:
        pass
    except Exception:
        pass
