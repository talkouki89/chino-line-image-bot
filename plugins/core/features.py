import json
import os


FEATURE_DEFINITIONS = [
    {
        "key": "help_templates",
        "name": "Help 模板",
        "description": "圖搜說明、更新說明、GitHub 連結與功能狀態。",
        "commands": "圖搜說明 / 功能設定",
    },
    {
        "key": "engine_saucenao",
        "name": "SauceNAO",
        "description": "回覆搜1 / 模板搜1 / #1",
        "commands": "回覆搜1 / 模板搜1",
    },
    {
        "key": "engine_ascii2d",
        "name": "Ascii2D",
        "description": "回覆搜2 / 模板搜2 / #2",
        "commands": "回覆搜2 / 模板搜2",
    },
    {
        "key": "engine_tracemoe",
        "name": "TraceMoe",
        "description": "回覆搜3 / 模板搜3 / #3",
        "commands": "回覆搜3 / 模板搜3",
    },
    {
        "key": "engine_ehentai",
        "name": "E-Hentai",
        "description": "回覆搜4",
        "commands": "回覆搜4",
    },
    {
        "key": "engine_exhentai",
        "name": "ExHentai",
        "description": "回覆搜5",
        "commands": "回覆搜5",
    },
    {
        "key": "engine_copyseeker",
        "name": "Copyseeker",
        "description": "回覆搜6",
        "commands": "回覆搜6",
    },
    {
        "key": "engine_yandex",
        "name": "Yandex",
        "description": "回覆搜7。PicImageSearch 目前容易因頁面結構變動失敗。",
        "commands": "回覆搜7",
    },
    {
        "key": "engine_iqdb",
        "name": "Iqdb",
        "description": "回覆搜8",
        "commands": "回覆搜8",
    },
    {
        "key": "engine_animetrace",
        "name": "AnimeTrace",
        "description": "回覆搜9",
        "commands": "回覆搜9",
    },
    {
        "key": "media_tools",
        "name": "媒體與隨機圖",
        "description": "X/Twitter、yt-dlp、隨機圖、R18 色圖、標註查詢。",
        "commands": "x;URL / ytmp4:URL / 隨機圖 / r18色圖",
    },
    {
        "key": "image_draw_template",
        "name": "抽圖片模板",
        "description": "用按鈕呼叫隨機圖與 R18 色圖。",
        "commands": "抽圖 / 抽圖片",
    },
    {
        "key": "freeimage_upload",
        "name": "圖片上傳",
        "description": "回覆圖片後上傳到 Freeimage.host。",
        "commands": "#圖片上傳",
    },
    {
        "key": "nhentai",
        "name": "nHentai",
        "description": "nHentai 編號解析與 Popular Now。",
        "commands": "n:數字 / n:popular",
    },
    {
        "key": "wnacg",
        "name": "紳士漫畫",
        "description": "wnacg 編號解析。",
        "commands": "w:數字",
    },
    {
        "key": "jmcomic",
        "name": "禁漫天堂",
        "description": "禁漫天堂編號解析。",
        "commands": "c:數字",
    },
    {
        "key": "pixiv",
        "name": "Pixiv",
        "description": "Pixiv 作品編號解析。",
        "commands": "p:數字",
    },
    {
        "key": "auto_friend",
        "name": "自動加好友",
        "description": "有人加 Bot 好友時自動加回並發送歡迎訊息。",
        "commands": "事件自動觸發",
    },
]


DEFAULT_FEATURES = {item["key"]: True for item in FEATURE_DEFINITIONS}
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
