import mimetypes
import os
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

SOUTUBOT_SOURCE_HOSTS = {
    "nhentai": "nhentai.net",
    "ehentai": "e-hentai.org",
    "panda": "panda.chaika.moe",
}


class WebImageSearchError(RuntimeError):
    pass


def search_soutubot(image_path, factor=1.2, timeout=45):
    """Search soutubot.moe through its current browser endpoint."""
    load_dotenv()
    local_api_url = os.getenv("IMSEARCH_API_URL") or os.getenv("SOUTUBOT_API_URL")
    if local_api_url:
        return search_imsearch_api(image_path, local_api_url, timeout=timeout)

    with requests.Session() as session:
        session.headers.update(DEFAULT_HEADERS)
        session.get("https://soutubot.moe/", timeout=timeout)
        with open(image_path, "rb") as fp:
            files = {"file": (os.path.basename(image_path), fp, content_type(image_path))}
            response = session.post(
                "https://soutubot.moe/api/search",
                data={"factor": str(factor)},
                files=files,
                timeout=timeout,
            )
    if response.status_code in (401, 403):
        raise WebImageSearchError("Soutubot 拒絕請求，可能需要重新整理網頁憑證或遇到 Cloudflare 驗證。")
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data")
    if not data:
        raise WebImageSearchError("Soutubot 沒有找到結果。")
    return payload


def search_imsearch_api(image_path, api_url, timeout=45):
    """Search through a self-hosted lolishinshi/imsearch HTTP server."""
    endpoint = api_url.rstrip("/")
    if not endpoint.endswith("/search"):
        endpoint += "/search"
    headers = DEFAULT_HEADERS.copy()
    token = os.getenv("IMSEARCH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with open(image_path, "rb") as fp:
        files = {"file": (os.path.basename(image_path), fp, content_type(image_path))}
        response = requests.post(endpoint, headers=headers, files=files, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("result"):
        raise WebImageSearchError("imsearch 沒有找到結果。")
    return {
        "data": [
            {
                "title": path,
                "similarity": round(float(score), 3),
                "source": "imsearch",
                "pageUrl": path if str(path).startswith(("http://", "https://")) else "",
                "path": path,
            }
            for score, path in payload.get("result", [])
        ],
        "executionTime": payload.get("time"),
    }


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
        raise WebImageSearchError("GGJAV 拒絕請求，可能被 Cloudflare 或站方限制。")
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise WebImageSearchError("GGJAV 回傳格式不是 JSON，可能網站流程已變更。") from exc
    if not isinstance(payload, list) or not payload:
        raise WebImageSearchError("GGJAV 沒有辨識到女優，請換更清楚的臉部圖片。")
    return payload


def format_soutubot_result(payload, limit=5):
    rows = []
    for index, item in enumerate(payload.get("data", [])[:limit], start=1):
        title = best_value(item, "title", "name", "subjectName") or "無標題"
        similarity = best_value(item, "similarity", "score")
        source = best_value(item, "source", "sourceName", "site") or "未知來源"
        page = build_soutubot_url(item, "pagePath", "pageUrl")
        subject = build_soutubot_url(item, "subjectPath", "subjectUrl")
        url = page or subject or best_url(item) or "N/A"
        line = f"{index}. {title}\n來源：{source}"
        if similarity is not None:
            line += f"\n相似度：{similarity}%"
        line += f"\n網址：{url}"
        rows.append(line)
    execution = payload.get("executionTime")
    header = "Soutubot 搜圖結果"
    if execution:
        header += f"\n耗時：{execution}s"
    return header + "\n\n" + "\n\n".join(rows)


def format_ggjav_result(models, limit=5):
    rows = []
    for index, model in enumerate(models[:limit], start=1):
        name = best_value(model, "name_zh", "name", "name_ja", "name_en") or "未知女優"
        model_id = best_value(model, "id", "model_id")
        url = "https://ggjav.com/main/model?name=" + str(name)
        image_url = f"https://cdn-1.ggjav.com/media/model/{model_id}.jpg" if model_id else "N/A"
        rows.append(f"{index}. {name}\n頁面：{url}\n圖片：{image_url}")
    return "GGJAV 女優人臉辨識結果\n\n" + "\n\n".join(rows)


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


def build_soutubot_url(item, path_key, url_key):
    direct = best_value(item, url_key)
    if direct:
        return direct
    host = soutubot_host(item)
    path = best_value(item, path_key)
    if host and path:
        return urljoin(f"https://{host}", str(path))
    return ""


def soutubot_host(item):
    source = item.get("source") if isinstance(item, dict) else ""
    configs = item.get("sourceConfig") if isinstance(item, dict) else None
    if isinstance(configs, dict) and source in configs:
        variants = configs[source].get("variants") or []
        if variants and variants[0].get("host"):
            return variants[0]["host"]
        return configs[source].get("host")
    if isinstance(item, dict) and item.get("host"):
        return item["host"]
    return SOUTUBOT_SOURCE_HOSTS.get(str(source), "")


def best_url(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value.startswith(("http://", "https://")):
                return value
            nested = best_url(value)
            if nested:
                return nested
    if isinstance(data, list):
        for item in data:
            nested = best_url(item)
            if nested:
                return nested
    return ""
