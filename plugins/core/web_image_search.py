import mimetypes
import os

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class WebImageSearchError(RuntimeError):
    pass


def search_ggjav_pornstar(image_path, timeout=30):
    """Send an image to GGJAV's current pornstar recognition endpoint."""
    with requests.Session() as session:
        session.headers.update(DEFAULT_HEADERS)
        session.headers.update({"Referer": "https://ggjav.com/main/recognize_pornstar"})
        session.get("https://ggjav.com/main/recognize_pornstar", timeout=timeout)
        with open(image_path, "rb") as fp:
            files = {"face": (os.path.basename(image_path), fp, content_type(image_path))}
            response = session.post(
                "https://ggjav.com/main/recognize_pornstar",
                files=files,
                timeout=timeout,
            )
    if response.status_code in (401, 403):
        raise WebImageSearchError("GGJAV 拒絕請求，可能需要 Cloudflare 驗證。")
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise WebImageSearchError("GGJAV 回傳不是 JSON，可能網站結構已更新。") from exc
    if not isinstance(payload, list) or not payload:
        raise WebImageSearchError("GGJAV 沒有辨識到女優。")
    return payload


def format_ggjav_result(models, limit=5):
    rows = []
    for index, model in enumerate(models[:limit], start=1):
        name = best_value(model, "name_zh", "name", "name_ja", "name_en") or "未知女優"
        model_id = best_value(model, "id", "model_id")
        url = "https://ggjav.com/main/model?name=" + str(name)
        image_url = f"https://cdn-1.ggjav.com/media/model/{model_id}.jpg" if model_id else "N/A"
        rows.append(f"{index}. {name}\n頁面：{url}\n圖片：{image_url}")
    return "GGJAV 女優辨識結果\n\n" + "\n\n".join(rows)


def content_type(path):
    return mimetypes.guess_type(path)[0] or "image/jpeg"


def best_value(data, *keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None
