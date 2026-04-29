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
