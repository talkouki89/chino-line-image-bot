from urllib.parse import quote

from plugins.core.features import FEATURE_DEFINITIONS, is_enabled


GITHUB_URL = "https://github.com/talkouki89/chino-line-image-bot"
CREATOR_NAME = "智乃妹妹"
LIFF_COMMAND_URL = "line://app/1660845055-GMJrEOVY?type=text&text={text}&auto=yes"


def build_help_flex(flags, is_admin=False):
    lines = [
        "智乃搜圖機器人",
        "",
        "初次使用",
        "請先輸入 Allowliff",
        "依照畫面授權 LIFF 模板權限。",
        "",
        "圖片反搜",
        "回覆搜1 SauceNAO",
        "回覆搜2 Ascii2D",
        "回覆搜3 TraceMoe",
        "回覆搜4 E-Hentai",
        "回覆搜5 ExHentai",
        "回覆搜6 Copyseeker",
        "回覆搜7 Yandex",
        "回覆搜8 Iqdb",
        "回覆搜9 AnimeTrace",
        "",
        "作品解析",
        "n:數字 / n:popular",
        "w:數字 / c:數字 / p:數字",
        "",
        "媒體工具",
        "抽圖 / 隨機圖 / r18色圖",
        "#圖片上傳 / 誰標我 / 清空標註",
        "",
        "GitHub",
        GITHUB_URL,
        "",
        "功能狀態",
        feature_status_text(flags),
    ]
    if is_admin:
        lines.extend(["", "管理", "功能設定 / 功能切換 <key> / pic:reb"])
    return simple_flex("ChinoBot 指令說明", lines)


def build_settings_flex(flags):
    engines = [
        settings_intro_bubble("功能設定：搜圖引擎"),
        *feature_bubbles(flags, [
            "engine_saucenao",
            "engine_ascii2d",
            "engine_tracemoe",
            "engine_ehentai",
            "engine_exhentai",
            "engine_copyseeker",
            "engine_yandex",
            "engine_iqdb",
            "engine_animetrace",
        ]),
    ]
    others = [
        settings_intro_bubble("功能設定：其他功能"),
        *feature_bubbles(flags, [
            "help_templates",
            "media_tools",
            "image_draw_template",
            "freeimage_upload",
            "nhentai",
            "wnacg",
            "jmcomic",
            "pixiv",
            "auto_friend",
        ]),
    ]
    return [
        flex("ChinoBot 功能設定：搜圖引擎", engines),
        flex("ChinoBot 功能設定：其他功能", others),
    ]


def feature_bubbles(flags, keys):
    index = {item["key"]: item for item in FEATURE_DEFINITIONS}
    return [feature_button_bubble(index[key], is_enabled(flags, key)) for key in keys]


def settings_intro_bubble(title_text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                title(title_text),
                text("只有管理員可以使用。", "#555555"),
                text("點擊按鈕會開啟 LIFF 並自動送出切換指令。", "#555555"),
            ],
        },
    }


def feature_button_bubble(item, enabled):
    state = "開啟" if enabled else "關閉"
    command = f"功能切換 {item['key']}"
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                title(item["name"]),
                text(f"目前：{state}", "#16a34a" if enabled else "#dc2626"),
                text(f"指令：{command}", "#555555"),
                text(item["description"], "#777777"),
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "切換開關",
                        "uri": liff_command_url(command),
                    },
                }
            ],
        },
    }


def liff_command_url(command):
    return LIFF_COMMAND_URL.format(text=quote(command, safe=""))


def _legacy_settings_lines(flags):
    intro = [
        "功能設定",
        "",
        "只有管理員可以使用。",
        "要切換請輸入：",
        "功能切換 key",
        "",
    ]
    engines = intro + section_lines(flags, "搜圖引擎", [
        "engine_saucenao",
        "engine_ascii2d",
        "engine_tracemoe",
        "engine_ehentai",
        "engine_exhentai",
        "engine_copyseeker",
        "engine_yandex",
        "engine_iqdb",
        "engine_animetrace",
    ])
    others = ["其他功能", ""] + section_lines(flags, "其他功能", [
        "help_templates",
        "media_tools",
        "image_draw_template",
        "freeimage_upload",
        "nhentai",
        "wnacg",
        "jmcomic",
        "pixiv",
        "auto_friend",
    ])
    return [
        simple_flex("ChinoBot 功能設定：搜圖引擎", engines),
        simple_flex("ChinoBot 功能設定：其他功能", others),
    ]


def section_lines(flags, title_text, keys):
    lines = [f"【{title_text}】"]
    index = {item["key"]: item for item in FEATURE_DEFINITIONS}
    for key in keys:
        item = index[key]
        state = "開" if is_enabled(flags, key) else "關"
        lines.append(f"{state}｜{item['name']}")
        lines.append(f"功能切換 {key}")
    return lines


def simple_flex(alt_text, lines):
    contents = [title(lines[0])]
    for line in lines[1:]:
        contents.append(text(line or " ", "#555555"))
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": contents[:45],
            },
        },
    }


def feature_status_text(flags):
    enabled_count = sum(1 for item in FEATURE_DEFINITIONS if is_enabled(flags, item["key"]))
    return f"{enabled_count}/{len(FEATURE_DEFINITIONS)} 開啟"


def flex_messages(alt_text, bubbles, chunk_size=4):
    messages = [
        flex(f"{alt_text} {index + 1}", bubbles[index:index + chunk_size])
        for index in range(0, len(bubbles), chunk_size)
    ]
    return messages[0] if len(messages) == 1 else messages


def flex(alt_text, bubbles):
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": {"type": "carousel", "contents": bubbles[:10]},
    }


def intro_bubble(flags):
    enabled_count = sum(1 for item in FEATURE_DEFINITIONS if is_enabled(flags, item["key"]))
    return {
        "type": "bubble",
        "size": "mega",
        "body": box([
            title("智乃搜圖機器人"),
            text("使用請輸入：圖搜說明", "#666666"),
            separator(),
            row("功能狀態", f"{enabled_count}/{len(FEATURE_DEFINITIONS)} 開啟"),
            row("作者", CREATOR_NAME),
            text("有 bug 可以提交 issue；新功能或想加的功能可以提交 PR。", "#555555"),
        ]),
        "footer": footer_buttons([
            uri_button("GitHub", GITHUB_URL),
        ]),
    }


def legacy_settings_intro_bubble():
    return {
        "type": "bubble",
        "size": "mega",
        "body": box([
            title("功能設定"),
            text("只有管理員或作者可以切換。請複製卡片中的切換指令送出。", "#555555"),
            separator(),
            text("關閉後，對應插件指令會被 PluginManager 擋下，不會進入功能處理。", "#777777"),
        ]),
    }


def status_bubble(flags):
    contents = [title("功能狀態")]
    for item in FEATURE_DEFINITIONS:
        mark = "ON" if is_enabled(flags, item["key"]) else "OFF"
        color = "#16a34a" if mark == "ON" else "#dc2626"
        contents.append(row(item["name"], mark, value_color=color))
    return {"type": "bubble", "size": "mega", "body": box(contents)}


def feature_toggle_bubble(item, enabled):
    state = "開啟" if enabled else "關閉"
    return {
        "type": "bubble",
        "size": "mega",
        "body": box([
            text(item["key"], "#777777"),
            title(item["name"]),
            row("目前", state, value_color="#16a34a" if enabled else "#dc2626"),
            row("指令", item["commands"]),
            row("切換", f"功能切換 {item['key']}"),
            text(item["description"], "#555555"),
        ]),
    }


def command_bubble(name, commands):
    contents = [title(name)]
    contents.extend(row(command, description) for command, description in commands)
    return {"type": "bubble", "size": "mega", "body": box(contents)}


def update_bubble(is_admin):
    rows = [
        title("更新說明"),
        text("Help 已改為 Flex 模板，並整合 GitHub、更新說明與功能開關狀態。", "#555555"),
        text("圖片上傳目前使用 Freeimage.host。私訊 E2EE 圖片若 LINE 不提供可下載原圖，會提示改用群組或關閉 E2EE。", "#555555"),
    ]
    if is_admin:
        rows.append(text("管理指令：功能設定 / 功能切換 <key> / pic:help / pic:reb", "#555555"))
    return {
        "type": "bubble",
        "size": "mega",
        "body": box(rows),
        "footer": footer_buttons([uri_button("開啟 GitHub", GITHUB_URL)]),
    }


def box(contents):
    return {"type": "box", "layout": "vertical", "spacing": "md", "contents": contents}


def title(value):
    return {"type": "text", "text": value, "weight": "bold", "size": "xl", "wrap": True}


def text(value, color="#111111"):
    return {"type": "text", "text": value, "size": "sm", "wrap": True, "color": color}


def row(label, value, value_color="#111111"):
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": str(label), "size": "sm", "color": "#777777", "flex": 3},
            {"type": "text", "text": str(value), "size": "sm", "color": value_color, "wrap": True, "flex": 5},
        ],
    }


def separator():
    return {"type": "separator"}


def footer_buttons(buttons):
    return {"type": "box", "layout": "vertical", "spacing": "sm", "contents": buttons}


def uri_button(label, url):
    return {"type": "button", "style": "primary", "height": "sm", "action": {"type": "uri", "label": label, "uri": url}}
