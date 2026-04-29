FEATURE_KEY = "image_draw_template"

from urllib.parse import quote

LIFF_COMMAND_URL = "line://app/2009929108-vOiudUbo?type=text&text={text}&auto=yes"

GAME_TAGS = [
    ("Nikke（妮姬）", "Nikke"),
    ("原神", "原神"),
    ("崩鐵（崩铁）", "崩铁"),
    ("明日方舟", "明日方舟"),
    ("終末地", "終末地"),
    ("異環（异环）", "异环"),
    ("FGO（Fate/GrandOrder）", "fgo"),
    ("PCR（公主連結）", "pcr"),
    ("GBF（碧藍幻想）", "gbf"),
    ("艦B（碧藍航線）", "舰b"),
    ("艦C（艦隊 Collection）", "舰c"),
    ("少前（少女前線）", "少前"),
]

OTHER_TAGS = [
    ("正太", "正太"),
    ("蘿莉", "蘿莉"),
    ("御姐", "御姐"),
    ("白髮", "白髮"),
    ("黑髮", "黑髮"),
    ("白絲（白丝）", "白丝"),
    ("黑絲（黑丝）", "黑丝"),
    ("制服", "制服"),
    ("女僕", "女僕"),
    ("VTB（VTuber）", "vtb"),
]


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
            "type": "carousel",
            "contents": [
                random_draw_bubble(),
                tag_bubble("遊戲 / 作品標籤", "第二頁", GAME_TAGS),
                tag_bubble("其他標籤", "第三頁", OTHER_TAGS),
            ],
        },
    }


def random_draw_bubble():
    return bubble(
        [
            title("抽圖片"),
            note("選一個按鈕，我會幫你抽一張圖。"),
            separator(),
            note("一般：隨機圖"),
            note("一般無 AI：隨機無ai"),
            note("R18：r18色圖"),
            note("R18 無 AI：r18無ai"),
            separator(),
            note("標籤抽圖：tag色圖 標籤"),
            note("如果沒有輸入標籤，Bot 會提示輸入範例。"),
        ],
        [
            button("隨機圖", "隨機圖"),
            button("隨機圖 無 AI", "隨機無ai"),
            button("R18 色圖", "r18色圖"),
            button("R18 無 AI", "r18無ai"),
            button("Tag 色圖", "tag色圖"),
        ],
    )


def tag_bubble(title_text, page_text, tags):
    contents = [
        title(title_text),
        note(page_text),
        note("這邊為標籤 Tags 抽圖，所以可能會出 R18 的圖，請小心服用。"),
        note("有時也會出現可能跟標籤有差別的圖。"),
        note("括號內只是備註，實際輸出時只會送出標籤本身。"),
        separator(),
    ]
    return bubble(contents, [tag_button(label, tag) for label, tag in tags])


def bubble(body_contents, footer_contents):
    return {
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
            "contents": body_contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": button_rows(footer_contents),
        },
    }


def title(text):
    return {"type": "text", "text": text, "weight": "bold", "size": "xl", "color": "#5b3b73", "wrap": True}


def note(text):
    return {"type": "text", "text": text, "size": "sm", "color": "#555555", "wrap": True}


def separator():
    return {"type": "separator", "margin": "md", "color": "#f6c6d9"}


def tag_button(label, tag):
    return button(label, f"tag色圖 {tag}")


def button_rows(buttons, columns=2):
    rows = []
    for index in range(0, len(buttons), columns):
        row_buttons = buttons[index:index + columns]
        while len(row_buttons) < columns:
            row_buttons.append({"type": "box", "layout": "vertical", "contents": [], "flex": 1})
        rows.append({
            "type": "box",
            "layout": "horizontal",
            "spacing": "sm",
            "contents": row_buttons,
        })
    return rows


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
