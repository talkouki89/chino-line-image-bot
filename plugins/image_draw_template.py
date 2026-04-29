FEATURE_KEY = "image_draw_template"

from urllib.parse import quote

LIFF_COMMAND_URL = "line://app/2009929108-vOiudUbo?type=text&text={text}&auto=yes"
LOLICON_API_DOCS_URL = "https://docs.api.lolicon.app/"

GAME_TAGS = [
    ("Nikke", "Nikke"),
    ("原神", "原神"),
    ("崩鐵", "崩鐵"),
    ("明日方舟", "明日方舟"),
    ("終末地", "終末地"),
    ("異環", "異環"),
    ("Fate/GrandOrder", "fgo"),
    ("公主連結", "pcr"),
    ("碧藍幻想", "gbf"),
    ("碧藍航線", "艦B"),
    ("艦隊collection", "艦C"),
    ("少女前線", "少前"),
    ("蔚藍檔案", "蔚藍檔案"),
    ("絕區零", "絕區零"),
    ("鳴潮", "鳴潮"),
    ("Shadowverse", "Shadowverse"),
]

OTHER_TAGS = [
    ("JC", "JC"),
    ("正太", "正太"),
    ("蘿莉", "蘿莉"),
    ("御姐", "御姐"),
    ("白髮", "白髮"),
    ("黑髮", "黑髮"),
    ("白絲", "白絲"),
    ("黑絲", "黑絲"),
    ("制服", "制服"),
    ("女僕", "女僕"),
    ("泳衣", "泳衣"),
    ("白虎", "白虎"),
    ("男娘", "男娘"),
    ("扶他", "扶他"),
    ("性轉", "性轉"),
    ("VTB", "vtb"),
]

CHARACTER_TAGS = [
    ("真尋", "真尋"),
    ("伊莉雅", "伊莉雅"),
    ("酒吞童子", "酒吞童子"),
    ("星野愛", "星野愛"),
    ("水宮樞", "水宮樞"),
    ("初音", "初音"),
    ("草神", "草神"),
    ("花火", "花火"),
    ("星見雅", "星見雅"),
    ("長離", "長離"),
    ("大黑塔", "大黑塔"),
    ("聖園彌香", "聖園彌香"),
    ("優香", "優香"),
    ("小春", "小春"),
    ("白子", "白子"),
    ("妃咲", "妃咲"),
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
                tag_bubble("遊戲 / 作品標籤", GAME_TAGS),
                tag_bubble("其他標籤", OTHER_TAGS),
                tag_bubble("人物標籤", CHARACTER_TAGS),
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
            url_button("Lolicon API", LOLICON_API_DOCS_URL),
        ],
    )


def tag_bubble(title_text, tags):
    contents = [
        title(title_text),
        note("這邊為標籤 Tags 抽圖，所以可能會出 R18 的圖，請小心服用。"),
        note("有時也會出現可能跟標籤有差別的圖。"),
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


def url_button(label, url):
    return {
        "type": "button",
        "style": "primary",
        "height": "sm",
        "color": "#f08ab8",
        "action": {
            "type": "uri",
            "label": label,
            "uri": url,
        },
    }
