import time


FEATURE_KEY = "runtime_tools"


def handle(ctx):
    if ctx.cmd != "ren":
        return False
    started_at = getattr(ctx, "started_at", None)
    elapsed = max(0, int(time.time() - started_at)) if started_at else 0
    ctx.send_template(ctx.to, build_runtime_template(elapsed))
    return True


def build_runtime_template(seconds):
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    runtime = f"{days}天 {hours}小時 {minutes}分 {secs}秒"
    return {
        "type": "flex",
        "altText": "Bot 運行時間",
        "contents": {
            "type": "bubble",
            "styles": {"body": {"backgroundColor": "#f7fbff"}},
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "paddingAll": "20px",
                "contents": [
                    {"type": "text", "text": "Bot 運行時間", "weight": "bold", "size": "xl", "color": "#2563eb"},
                    {"type": "separator"},
                    {"type": "text", "text": runtime, "size": "lg", "weight": "bold", "wrap": True, "color": "#111827"},
                    {"type": "text", "text": "目前 Bot 仍在線並可接收指令。", "size": "sm", "wrap": True, "color": "#6b7280"},
                ],
            },
        },
    }
