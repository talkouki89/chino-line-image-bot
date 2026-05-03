from urllib.parse import quote

from plugins.core.features import FEATURE_DEFINITIONS, is_enabled


GITHUB_URL = "https://github.com/talkouki89/chino-line-image-bot"
GITHUB_PULLS_URL = "https://github.com/talkouki89/chino-line-image-bot/pulls?q=is%3Apr+is%3Amerged"
CREATOR_NAME = "智乃妹妹"
LIFF_COMMAND_URL = "line://app/2009929108-vOiudUbo?type=text&text={text}&auto=yes"

IMAGE_ENGINE_KEYS = [
    "engine_saucenao",
    "engine_ascii2d",
    "engine_tracemoe",
    "engine_yandex",
    "engine_iqdb",
    "engine_animetrace",
    "engine_ggjav",
]

OTHER_FEATURE_KEYS = [
    "help_templates",
    "x_download",
    "ytdlp_download",
    "facebook_download",
    "pornhub_download",
    "instagram_download",
    "tiktok_download",
    "admin_profile_tools",
    "runtime_tools",
    "mention_tools",
    "broadcast",
    "image_draw_template",
    "freeimage_upload",
    "nhentai",
    "wnacg",
    "jmcomic",
    "pixiv",
    "auto_friend",
    "group_min_member_check",
    "search_quota",
    "announcement_notify",
]


def build_help_flex(flags, is_admin=False):
    public_lines = [
        "智乃搜圖機器人",
        "",
        "圖片搜尋",
        "回覆搜1 SauceNAO",
        "回覆搜2 Ascii2D",
        "回覆搜3 TraceMoe",
        "回覆搜4 Yandex",
        "回覆搜5 Iqdb",
        "回覆搜6 AnimeTrace",
        "回覆搜7 GGJAV 女優辨識",
        "",
        "使用方式",
        "回覆一張圖片後輸入上方指令",
        "",
        "作品解析",
        "n:數字 / n:popular",
        "w:數字 / c:數字 / p:數字",
        "",
        "其他功能",
        "抽圖 / 隨機圖 / r18色圖 / tag色圖 標籤",
        "誰標我 / 清空標註",
        "#圖片上傳",
    ]
    download_lines = [
        "媒體下載",
        "",
        "X / Twitter",
        "x:URL 下載單一貼文圖片或影片",
        "x:URL URL 可一次貼多個 X 網址",
        "回覆搜x 回覆 X 網址後下載",
        "",
        "影片平台",
        "yt:URL 下載 YouTube 或 yt-dlp 支援網址",
        "回覆搜yt 回覆影片網址後下載",
        "fb:URL / 回覆搜fb 下載 Facebook 影片",
        "ph:URL / 回覆搜ph 下載 Pornhub 影片",
        "",
        "社群圖片 / 影片",
        "ig:URL / 回覆搜ig 下載 Instagram 媒體",
        "tk:URL 下載 TikTok 圖片或影片",
        "",
        "多張圖片會合併成一組傳送",
    ]
    admin_lines = [
        "管理員功能",
        "功能狀態",
        "功能設定",
        "功能切換 <key>",
        "版本檢查 / 版本更新 / 圖搜api版本檢查",
        "更新圖搜api",
        "群發 / 確認群發 / 取消群發",
        "pic:about / rg / 群組資訊 / data",
        "mymid / gid / mid @人",
        "mid:MID / Contact @人 / speedtest",
        "ren / res / 登入狀態 / lg",
        "查詢剩餘次數 / 查詢使用次數",
        "加次數:數字 / 減次數:數字",
        "圖搜退 / sp / speedtest / un 數量",
        "ad@ @人 / pic:reb / reb @bot",
        "",
        "BotCreator 專用",
        "清圖搜權限表 / 圖搜權限表",
        "標註加圖搜權限 @人 / 標註刪除圖搜權限 @人",
        "add:MID / del:MID / exec:",
        "bottoken / botauthtoken",
        f"功能狀態：{feature_status_text(flags)}",
    ]
    public_bubble = simple_bubble(public_lines)
    public_bubble["footer"] = footer_buttons([uri_button("開啟 GitHub", GITHUB_URL)])
    bubbles = [
        public_bubble,
        simple_bubble(download_lines),
    ]
    if is_admin:
        bubbles.append(simple_bubble(admin_lines))
    return {
        "type": "flex",
        "altText": "ChinoBot 指令說明",
        "contents": {
            "type": "carousel",
            "contents": bubbles,
        },
    }


def build_help_text(flags=None, is_admin=False):
    lines = [
        "智乃搜圖機器人",
        "使用方式：先回覆一張圖片，再輸入回覆搜指令。",
        "",
        "回覆搜1：SauceNAO，找圖片來源。",
        "回覆搜2：Ascii2D，找二次元原圖。",
        "回覆搜3：TraceMoe，找動畫截圖。",
        "回覆搜4 / 5：Yandex / Iqdb，找相似圖。",
        "回覆搜6：AnimeTrace，辨識角色或作品。",
        "回覆搜7：GGJAV，辨識女優。",
        "",
        "其他：#圖片上傳、抽圖、tag色圖、誰標我、清空標註、n/w/c/p作品解析。",
        "媒體下載：x:URL、回覆搜x、yt:URL、回覆搜yt、fb:URL、回覆搜fb、ph:URL、回覆搜ph、ig:URL、回覆搜ig、tk:URL。",
    ]
    if is_admin:
        lines.extend([
            "",
            "管理員：功能狀態、功能設定、版本檢查、版本更新、圖搜api版本檢查、更新圖搜api、群發。",
        ])
        if flags is not None:
            lines.append(f"功能狀態：{feature_status_text(flags)}")
    return "\n".join(lines)


def build_settings_flex(flags):
    messages = []
    for message in (
        flex("ChinoBot 搜圖引擎開關", [
            settings_intro_bubble("搜圖引擎開關"),
            *feature_bubbles(flags, IMAGE_ENGINE_KEYS),
        ]),
        flex("ChinoBot 其他功能開關", [
            settings_intro_bubble("其他功能開關"),
            *feature_bubbles(flags, OTHER_FEATURE_KEYS),
        ]),
    ):
        if isinstance(message, list):
            messages.extend(message)
        else:
            messages.append(message)
    return messages


def build_status_flex(flags):
    enabled = []
    disabled = []
    index = feature_index()
    for item in FEATURE_DEFINITIONS:
        target = enabled if is_enabled(flags, item["key"]) else disabled
        target.append(index[item["key"]]["name"])
    return flex("ChinoBot 功能狀態", [
        status_bubble("已開啟", enabled, "ON"),
        status_bubble("已關閉", disabled, "OFF"),
    ])


def build_version_check_flex(local_version, remote_version=None, prs=None, error=None, version_notes=""):
    prs = prs or []
    has_update = bool(remote_version and remote_version != local_version)
    if error:
        lines = [
            "版本檢查",
            f"目前版本：{local_version}",
            f"狀態：{error}",
        ]
    else:
        lines = [
            "版本檢查",
            f"目前版本：{local_version}",
            f"遠端版本：{remote_version}",
            "狀態：發現新版本。" if has_update else "狀態：目前已是最新版本。",
        ]
        if prs:
            lines.extend(["", "最近更新內容"])
            for pr in prs[:5]:
                line = f"#{pr['number']} {pr['title']}"
                if pr.get("summary"):
                    line += f"\n{pr['summary']}"
                lines.append(line)
        if version_notes:
            lines.extend(["", "版本更新內容"])
            lines.extend(version_notes_lines(version_notes))

    buttons = [uri_button("查看新功能 PR", GITHUB_PULLS_URL)]
    if has_update:
        buttons.append(command_button("版本更新", "版本更新"))
    return simple_flex("ChinoBot 版本檢查", lines, footer_buttons=buttons)


def build_picsearch_api_version_check_flex(local_version, remote_version=None, error=None):
    has_update = bool(remote_version and remote_version != local_version)
    if error:
        lines = [
            "圖搜api版本檢查",
            f"目前版本：{local_version}",
            f"狀態：{error}",
        ]
    else:
        lines = [
            "圖搜api版本檢查",
            f"目前版本：{local_version}",
            f"遠端版本：{remote_version}",
            "狀態：發現新版 PicImageSearch。" if has_update else "狀態：目前已是最新版本。",
        ]
    buttons = []
    if has_update:
        buttons.append(command_button("更新圖搜api", "更新圖搜api"))
    return simple_flex("ChinoBot 圖搜api版本檢查", lines, footer_buttons=buttons or None)


def version_notes_lines(value, limit=10):
    lines = []
    for line in str(value).replace("\r", "").split("\n"):
        line = line.strip()
        if not line:
            continue
        lines.append(line.lstrip("#").strip())
        if len(lines) >= limit:
            break
    return lines


def status_bubble(title_text, names, marker):
    lines = [title_text, "", f"共 {len(names)} 個"]
    lines.extend(f"{marker}  {name}" for name in names)
    return simple_bubble(lines)


def feature_bubbles(flags, keys):
    index = feature_index()
    return [feature_button_bubble(index[key], is_enabled(flags, key)) for key in keys if key in index]


def feature_index():
    return {item["key"]: item for item in FEATURE_DEFINITIONS}


def settings_intro_bubble(title_text):
    return bubble([
        title(title_text),
        text("只有管理員可以切換功能。"),
        text("按下按鈕會透過 LIFF 發送切換指令，不會再次洗出設定模板。", "#666666"),
    ])


def feature_button_bubble(item, enabled):
    state = "開啟" if enabled else "關閉"
    command = f"功能切換 {item['key']}"
    return {
        "type": "bubble",
        "styles": {"body": {"backgroundColor": "#fff7fb"}, "footer": {"backgroundColor": "#fff7fb"}},
        "body": box([
            title(item["name"]),
            text(f"狀態：{state}", "#16a34a" if enabled else "#dc2626"),
            text(f"指令：{item['commands']}", "#555555"),
            text(item["description"], "#777777"),
        ]),
        "footer": footer_buttons([
            {
                "type": "button",
                "style": "primary",
                "height": "sm",
                "action": {
                    "type": "uri",
                    "label": "切換",
                    "uri": liff_command_url(command),
                },
            }
        ]),
    }


def simple_flex(alt_text, lines, footer_buttons=None):
    body = simple_bubble(lines)
    message = {
        "type": "flex",
        "altText": alt_text,
        "contents": body,
    }
    if footer_buttons:
        message["contents"]["footer"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": footer_buttons,
        }
    return message


def simple_bubble(lines):
    contents = [title(lines[0])]
    for line in lines[1:]:
        contents.append(text(line or " ", "#555555"))
    return {
        "type": "bubble",
        "styles": {"body": {"backgroundColor": "#fff7fb"}, "footer": {"backgroundColor": "#fff7fb"}},
        "body": box(contents[:45]),
    }


def feature_status_text(flags):
    enabled_count = sum(1 for item in FEATURE_DEFINITIONS if is_enabled(flags, item["key"]))
    return f"{enabled_count}/{len(FEATURE_DEFINITIONS)} 開啟"


def flex(alt_text, bubbles):
    messages = []
    for index in range(0, len(bubbles), 10):
        messages.append({
            "type": "flex",
            "altText": alt_text if index == 0 else f"{alt_text} {index // 10 + 1}",
            "contents": {"type": "carousel", "contents": bubbles[index:index + 10]},
        })
    return messages[0] if len(messages) == 1 else messages


def bubble(contents):
    return {
        "type": "bubble",
        "styles": {"body": {"backgroundColor": "#fff7fb"}},
        "body": box(contents),
    }


def box(contents):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "backgroundColor": "#fff7fb",
        "paddingAll": "18px",
        "contents": contents,
    }


def title(value):
    return {
        "type": "text",
        "text": str(value),
        "weight": "bold",
        "size": "lg",
        "color": "#5b3b73",
        "wrap": True,
    }


def text(value, color="#333333"):
    return {
        "type": "text",
        "text": str(value),
        "size": "sm",
        "color": color,
        "wrap": True,
    }


def footer_buttons(buttons):
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": buttons,
    }


def uri_button(label, uri):
    return {
        "type": "button",
        "style": "link",
        "color": "#f08ab8",
        "height": "sm",
        "action": {
            "type": "uri",
            "label": label,
            "uri": uri,
        },
    }


def command_button(label, command):
    return uri_button(label, liff_command_url(command))


def liff_command_url(command):
    return LIFF_COMMAND_URL.format(text=quote(command, safe=""))
