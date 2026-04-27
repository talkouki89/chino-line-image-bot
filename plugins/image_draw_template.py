FEATURE_KEY = "image_draw_template"
from urllib.parse import quote


LIFF_COMMAND_URL = "line://app/1660845055-GMJrEOVY?type=text&text={text}&auto=yes"


def handle(ctx):
    if ctx.cmd.strip() not in {"抽圖", "抽圖片", "抽色圖"}:
        return False
    ctx.send_template(ctx.to, build_draw_template())
    return True


def build_draw_template():
    return {
        "type": "flex",
        "altText": "抽圖片模板",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "抽圖片", "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "點擊按鈕會自動送出抽圖指令。", "size": "sm", "color": "#666666", "wrap": True},
                    {"type": "text", "text": "一般：隨機圖", "size": "md", "wrap": True},
                    {"type": "text", "text": "一般無 AI：隨機無ai", "size": "md", "wrap": True},
                    {"type": "text", "text": "R18：r18色圖", "size": "md", "wrap": True},
                    {"type": "text", "text": "R18 無 AI：r18無ai", "size": "md", "wrap": True},
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    button("隨機圖", "隨機圖"),
                    button("隨機圖 無 AI", "隨機無ai"),
                    button("R18 色圖", "r18色圖"),
                    button("R18 無 AI", "r18無ai"),
                ],
            },
        },
    }


def button(label, command):
    return {
        "type": "button",
        "style": "primary",
        "height": "sm",
        "action": {
            "type": "uri",
            "label": label,
            "uri": LIFF_COMMAND_URL.format(text=quote(command, safe="")),
        },
    }
