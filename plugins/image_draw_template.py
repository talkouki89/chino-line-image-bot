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
            "styles": {
                "body": {"backgroundColor": "#fff7fb"},
                "footer": {"backgroundColor": "#fff7fb"},
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "paddingAll": "20px",
                "backgroundColor": "#fff7fb",
                "contents": [
                    {"type": "text", "text": "抽圖片", "weight": "bold", "size": "xl", "color": "#5b3b73"},
                    {"type": "text", "text": "選一個按鈕，我會幫你抽一張圖。", "size": "sm", "color": "#6b5876", "wrap": True},
                    {"type": "separator", "margin": "md", "color": "#f6c6d9"},
                    {"type": "text", "text": "一般：隨機圖", "size": "sm", "color": "#555555", "wrap": True},
                    {"type": "text", "text": "一般無 AI：隨機無ai", "size": "sm", "color": "#555555", "wrap": True},
                    {"type": "text", "text": "R18：r18色圖", "size": "sm", "color": "#555555", "wrap": True},
                    {"type": "text", "text": "R18 無 AI：r18無ai", "size": "sm", "color": "#555555", "wrap": True},
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
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
        "color": "#f08ab8",
        "action": {
            "type": "uri",
            "label": label,
            "uri": LIFF_COMMAND_URL.format(text=quote(command, safe="")),
        },
    }
