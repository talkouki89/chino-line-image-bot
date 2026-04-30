FEATURE_KEY = "image_draw_template"

import threading
from urllib.parse import quote

import requests

from plugins.core.cooldown import check_draw_cooldown
from plugins.core.text_convert import to_simplified, to_traditional

LIFF_COMMAND_URL = "line://app/2009929108-vOiudUbo?type=text&text={text}&auto=yes"
LOLICON_API_URL = "https://api.lolicon.app/setu/v2"
LOLICON_API_DOCS_URL = "https://docs.api.lolicon.app/"
RANDOM_IMAGE_COMMANDS = {
    "隨機圖": (0, False),
    "隨機色圖": (0, False),
    "一般色圖": (0, False),
    "test1": (0, False),
    "隨機無ai": (0, True),
    "無ai隨機圖": (0, True),
    "隨機圖無ai": (0, True),
    "隨機r18": (1, False),
    "r18色圖": (1, False),
    "色圖": (1, False),
    "test2": (1, False),
    "r18無ai": (1, True),
    "無ai r18": (1, True),
    "r18色圖無ai": (1, True),
}
TAG_IMAGE_PREFIXES = ("tag色圖", "色圖tag", "找色圖", "test3")

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
    if ctx.cmd.strip() in {"抽圖", "抽圖片", "抽色圖"}:
        ctx.send_template(ctx.to, build_draw_template())
        return True
    if ctx.cmd in RANDOM_IMAGE_COMMANDS:
        if not check_lolicon_cooldown(ctx):
            return True
        r18, exclude_ai = RANDOM_IMAGE_COMMANDS[ctx.cmd]
        return handle_random_lolicon(ctx, r18=r18, exclude_ai=exclude_ai)
    if ctx.cmd.startswith(TAG_IMAGE_PREFIXES):
        return handle_lolicon_tags(ctx)
    return False


def check_lolicon_cooldown(ctx):
    if getattr(ctx, "is_admin", False):
        return True
    allowed, remaining = check_draw_cooldown(ctx.sender)
    if not allowed:
        ctx.reply(f"抽圖冷卻中，請 {remaining} 秒後再試。")
        return False
    return True


def handle_random_lolicon(ctx, r18=0, exclude_ai=False):
    threading.Thread(
        target=send_random_lolicon_async,
        args=(ctx, r18, exclude_ai),
        daemon=True,
    ).start()
    return True


def send_random_lolicon_async(ctx, r18=0, exclude_ai=False):
    try:
        data = request_lolicon({"r18": r18, "excludeAI": exclude_ai})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("隨機色圖讀取失敗")
        return

    label = "R18 隨機色圖" if r18 else "一般隨機色圖"
    if exclude_ai:
        label += "（無 AI）"
    send_lolicon_result(ctx, data, label=label)


def handle_lolicon_tags(ctx):
    tags = extract_tag_query(ctx.text)
    if not tags:
        ctx.reply("請輸入標籤 範例:tag色圖 蘿莉")
        return True
    if not check_lolicon_cooldown(ctx):
        return True
    query_tags = [to_simplified(tag) for tag in tags.split()]
    display_tags = " ".join(to_traditional(tag) for tag in query_tags)
    try:
        data = request_lolicon({"tag": [[tag] for tag in query_tags], "r18": 1})
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("tag 色圖讀取失敗")
        return True

    send_lolicon_result(ctx, data, label=f"Tag 色圖：{display_tags}")
    return True


def extract_tag_query(text):
    for prefix in TAG_IMAGE_PREFIXES:
        if text.lower().startswith(prefix):
            return text[len(prefix):].strip()
    return ""


def request_lolicon(extra_payload):
    payload = {
        "num": 1,
        "size": ["regular", "original"],
        "excludeAI": False,
    }
    payload.update(extra_payload)
    response = requests.post(
        LOLICON_API_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data


def send_lolicon_result(ctx, data, label):
    if not data.get("data"):
        ctx.reply("搜尋不到你的標籤 可以嘗試用簡體搜尋喔")
        return
    item = data["data"][0]
    urls = item.get("urls") or {}
    image_url = urls.get("regular") or urls.get("original")
    text = (
        str(label) +
        f"\n\n圖片標題⇛ {item.get('title')}"
        f"\n圖片作者⇛ {item.get('author')}"
        f"\n是否R18⇛ {format_bool_flag(item.get('r18'))}"
        f"\n是否AI⇛ {format_ai_flag(item.get('aiType'))}"
        f"\n圖源Url⇛ www.pixiv.net/artworks/{item.get('pid')}"
        "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و"
    )
    ctx.cl.relatedMessage(ctx.to, text, ctx.msg_id)
    if not image_url:
        ctx.reply("找不到圖片 URL")
        return
    try:
        ctx.cl.sendImageWithURL(ctx.to, image_url)
    except Exception as exc:
        # LINE sometimes raises even after the image was accepted. Log only so a
        # successful text/image response does not get followed by a false failure.
        ctx.log_error(exc)


def format_ai_flag(ai_type):
    try:
        return "否" if int(ai_type or 0) == 0 else "是"
    except (TypeError, ValueError):
        return "否" if not ai_type else "是"


def format_bool_flag(value):
    if isinstance(value, str):
        return "是" if value.strip().lower() in ("1", "true", "yes", "on") else "否"
    return "是" if bool(value) else "否"


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
