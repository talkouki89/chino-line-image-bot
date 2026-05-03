import json
import os


FEATURE_DEFINITIONS = [
    {
        "key": "help_templates",
        "name": "Help 模板",
        "description": "圖搜說明、GitHub 按鈕、功能狀態摘要。",
        "commands": "圖搜說明 / 功能狀態",
    },
    {
        "key": "engine_saucenao",
        "name": "SauceNAO",
        "description": "通用以圖搜圖引擎。",
        "commands": "回覆搜1 / 模板搜1 / #1",
    },
    {
        "key": "engine_ascii2d",
        "name": "Ascii2D",
        "description": "二次元圖片來源搜尋。",
        "commands": "回覆搜2 / 模板搜2 / #2",
    },
    {
        "key": "engine_tracemoe",
        "name": "TraceMoe",
        "description": "動畫截圖辨識。",
        "commands": "回覆搜3 / 模板搜3 / #3",
    },
    {
        "key": "engine_yandex",
        "name": "Yandex",
        "description": "Yandex 圖片搜尋，網站改版時可能不穩。",
        "commands": "回覆搜4",
    },
    {
        "key": "engine_iqdb",
        "name": "Iqdb",
        "description": "Iqdb 圖片搜尋。",
        "commands": "回覆搜5",
    },
    {
        "key": "engine_animetrace",
        "name": "AnimeTrace",
        "description": "AnimeTrace 角色/作品辨識。",
        "commands": "回覆搜6",
    },
    {
        "key": "engine_ggjav",
        "name": "GGJAV 女優辨識",
        "description": "AV 女優人臉辨識，建議回覆清楚臉部圖片。",
        "commands": "回覆搜7",
    },
    {
        "key": "x_download",
        "name": "X/Twitter 下載",
        "description": "下載 X/Twitter 圖片或影片。",
        "commands": "x:URL / 回覆搜x",
    },
    {
        "key": "ytdlp_download",
        "name": "yt-dlp 下載",
        "description": "使用 yt-dlp 下載一般影片網址。",
        "commands": "yt:URL / 回覆搜yt",
    },
    {
        "key": "facebook_download",
        "name": "Facebook 下載",
        "description": "透過 yt-dlp 下載 Facebook 影片。",
        "commands": "fb:URL / 回覆搜fb",
    },
    {
        "key": "pornhub_download",
        "name": "Pornhub 下載",
        "description": "透過 yt-dlp 下載 Pornhub 影片。",
        "commands": "ph:URL / 回覆搜ph",
    },
    {
        "key": "instagram_download",
        "name": "Instagram 下載",
        "description": "使用 yt-dlp 下載 Instagram 圖片或影片。",
        "commands": "ig:URL / 回覆搜ig",
    },
    {
        "key": "tiktok_download",
        "name": "TikTok 下載",
        "description": "使用 yt-dlp 下載 TikTok 圖片或影片。",
        "commands": "tk:URL",
    },
    {
        "key": "admin_profile_tools",
        "name": "管理員查詢工具",
        "description": "管理員查詢 MID、好友資料與執行 Speedtest 測速。",
        "commands": "speedtest / mid:MID / Contact @人",
    },
    {
        "key": "runtime_tools",
        "name": "運行時間模板",
        "description": "使用模板顯示 Bot 運行時間。",
        "commands": "ren",
    },
    {
        "key": "mention_tools",
        "name": "標註查詢",
        "description": "查詢或清空被標註紀錄。",
        "commands": "誰標我 / 清空標註",
    },
    {
        "key": "broadcast",
        "name": "群發消息",
        "description": "管理員建立預覽並確認後，背景每秒向一個群組發送文字、圖片或影片。",
        "commands": "群發 / 確認群發 / 取消群發",
    },
    {
        "key": "image_draw_template",
        "name": "抽圖模板",
        "description": "抽圖模板、隨機圖、標籤隨機圖、R18 圖、無 AI 圖。",
        "commands": "抽圖 / 隨機圖 / r18色圖 / tag色圖",
    },
    {
        "key": "freeimage_upload",
        "name": "圖片上傳",
        "description": "回覆圖片上傳到 Freeimage.host。",
        "commands": "#圖片上傳",
    },
    {
        "key": "nhentai",
        "name": "nHentai",
        "description": "nHentai 作品解析與 Popular Now。",
        "commands": "n:數字 / n:popular",
    },
    {
        "key": "wnacg",
        "name": "紳士漫畫",
        "description": "wnacg 作品解析。",
        "commands": "w:數字",
    },
    {
        "key": "jmcomic",
        "name": "禁漫天堂",
        "description": "禁漫天堂作品解析。",
        "commands": "c:數字",
    },
    {
        "key": "pixiv",
        "name": "Pixiv",
        "description": "Pixiv 作品解析。",
        "commands": "p:數字",
    },
    {
        "key": "auto_friend",
        "name": "自動加好友",
        "description": "有人加入 Bot 好友時自動加入並回覆專案連結。",
        "commands": "自動處理好友事件",
    },
    {
        "key": "group_min_member_check",
        "name": "最低入群人數",
        "description": "Bot 被邀請入群時檢查最低人數，門檻由 .env 的 GROUP_MIN_MEMBERS 設定。",
        "commands": "邀請入群事件",
    },
    {
        "key": "search_quota",
        "name": "圖搜次數限制",
        "description": "開啟後一般使用者圖搜會扣次數；關閉後不看次數。管理員一律不扣次數。",
        "commands": "回覆搜1 ~ 回覆搜7",
    },
    {
        "key": "announcement_notify",
        "name": "公告通知",
        "description": "群組公告被建立時，自動回報公告內容。",
        "commands": "事件自動觸發",
        "default": False,
    },
]


DEFAULT_FEATURES = {item["key"]: item.get("default", True) for item in FEATURE_DEFINITIONS}
FEATURE_INDEX = {item["key"]: item for item in FEATURE_DEFINITIONS}


def load_feature_flags(path):
    data = DEFAULT_FEATURES.copy()
    try:
        with open(path, "r", encoding="utf-8") as fp:
            raw = json.load(fp)
    except (FileNotFoundError, json.JSONDecodeError):
        save_feature_flags(path, data)
        return data
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key in data:
                data[key] = bool(value)
    if data != raw:
        save_feature_flags(path, data)
    return data


def save_feature_flags(path, flags):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(flags, fp, sort_keys=True, indent=4, ensure_ascii=False)


def is_enabled(flags, key, default=True):
    if not key:
        return default
    return bool(flags.get(key, default))


def set_enabled(path, flags, key, enabled):
    if key not in FEATURE_INDEX:
        raise KeyError(key)
    flags[key] = bool(enabled)
    save_feature_flags(path, flags)
    return flags[key]


def toggle_feature(path, flags, key):
    return set_enabled(path, flags, key, not is_enabled(flags, key))
