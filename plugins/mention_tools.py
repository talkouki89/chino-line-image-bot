import json
import os


FEATURE_KEY = "mention_tools"


def handle(ctx):
    if ctx.cmd == "誰標我":
        return handle_who_mentioned_me(ctx)
    if ctx.cmd == "清空標註":
        return handle_clear_mentions(ctx)
    return False


def handle_who_mentioned_me(ctx):
    data = load_mentions(ctx)
    chat_mentions = data.get(ctx.to, {})
    if not chat_mentions:
        ctx.reply("目前沒有人標註你。")
        return True

    latest_key = latest_numeric_key(chat_mentions)
    if latest_key is None:
        data.pop(ctx.to, None)
        save_mentions(ctx, data)
        ctx.reply("目前沒有人標註你。")
        return True

    item = chat_mentions.pop(latest_key)
    if not chat_mentions:
        data.pop(ctx.to, None)
    save_mentions(ctx, data)

    sender = str(item.get("sender", ""))
    name = sender
    try:
        name = ctx.cl.getContact(sender).displayName
    except Exception:
        pass
    message = (
        "最近標註你的人\n"
        f"名稱：{name}\n"
        f"MID：{sender}\n"
        f"時間：{item.get('tagtime', '未知')}\n"
        f"剩餘標註紀錄：{len(chat_mentions)}"
    )
    ctx.cl.relatedMessage(ctx.to, message, item.get("msgid") or ctx.msg_id)
    return True


def handle_clear_mentions(ctx):
    data = load_mentions(ctx)
    if ctx.to in data:
        removed = len(data.get(ctx.to, {}))
        data.pop(ctx.to, None)
        save_mentions(ctx, data)
        ctx.reply(f"已清空本聊天室標註紀錄，共 {removed} 筆。")
        return True
    ctx.reply("本聊天室沒有標註紀錄。")
    return True


def mention_file(ctx):
    return os.path.join(ctx.tag_dir, f"{ctx.sender}.json")


def load_mentions(ctx):
    path = mention_file(ctx)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_mentions(ctx, data):
    path = mention_file(ctx)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)


def latest_numeric_key(values):
    keys = []
    for key in values:
        try:
            keys.append(int(key))
        except (TypeError, ValueError):
            continue
    if not keys:
        return None
    return str(max(keys))
