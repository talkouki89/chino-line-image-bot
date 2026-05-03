import os
import re
import shutil
import tempfile
import threading
from html import unescape
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


FEATURE_KEY = "ytdlp_download"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_RE = re.compile(r"https?://[^\s<>\"]+")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
SCRAPE_MEDIA_RE = re.compile(
    r"https?:\\?/\\?/[^\"'<>\\\s]+?\.(?:jpg|jpeg|png|webp|gif|mp4|mov|m4v|webm)(?:\?[^\"'<>\\\s]*)?",
    re.IGNORECASE,
)
META_TAG_RE = re.compile(r"<meta\b[^>]+>", re.IGNORECASE)
META_PROP_RE = re.compile(r"\b(?:property|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)
META_CONTENT_RE = re.compile(r"\bcontent=[\"']([^\"']+)[\"']", re.IGNORECASE)
MIN_DIRECT_BYTES = 8 * 1024


def handle(ctx):
    if ctx.cmd.startswith("yt:"):
        return handle_ytdlp(ctx)
    return False


def handle_ytdlp(ctx):
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入影片網址。\n範例：yt:https://youtu.be/xxxx")
        return True
    if not is_http_url(url):
        ctx.reply("影片網址格式不正確。")
        return True
    send_ytdlp_media_async(ctx, url, label="影片")
    return True


def send_ytdlp_media_async(ctx, url, label="媒體", prefer_direct=False, use_douyin_wtf=False):
    threading.Thread(
        target=download_and_send_media,
        args=(ctx, url, label, prefer_direct, use_douyin_wtf),
        daemon=True,
    ).start()


def download_and_send_media(ctx, url, label="媒體", prefer_direct=False, use_douyin_wtf=False):
    temp_dir = tempfile.mkdtemp(prefix=f"chino-{ctx.sender}-")
    ctx.cl.sendReplyMessage(ctx.msg_id, ctx.to, f"開始下載{label}，完成後會自動傳送。")
    try:
        files = download_media(url, temp_dir, prefer_direct=prefer_direct, use_douyin_wtf=use_douyin_wtf)
        if not files:
            ctx.reply(f"{label}下載失敗，沒有取得可傳送的檔案。")
            return
        failed = send_files(ctx, files)
        if failed:
            ctx.reply(f"有 {failed} 個{label}檔案傳送失敗。")
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply(f"{label}下載失敗，請確認網址是否可公開觀看，或稍後再試。")
    finally:
        safe_remove_tree(temp_dir)


def download_media(url, output_dir, prefer_direct=False, use_douyin_wtf=False):
    load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
    ydl_opts = {
        "format": "best[ext=mp4][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]/best",
        "outtmpl": os.path.join(output_dir, "%(id)s-%(autonumber)03d.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "windowsfilenames": True,
    }
    ydl_opts.update(load_cookie_options())
    cookies_file = os.getenv("YTDLP_COOKIES_FILE", "cookies.txt")
    if cookies_file and os.path.exists(cookies_file):
        ydl_opts["cookiefile"] = cookies_file
    with YoutubeDL(ydl_opts) as ydl:
        if use_douyin_wtf:
            download_douyin_wtf_media(url, output_dir)
            existing = unique_existing_files(scan_output_files(output_dir))
            if existing:
                return existing
        if prefer_direct:
            scrape_direct_media(url, output_dir)
            existing = unique_existing_files(scan_output_files(output_dir))
            if existing:
                return existing
            try:
                info = ydl.extract_info(url, download=False)
                download_direct_media(info, output_dir)
                existing = unique_existing_files(scan_output_files(output_dir))
                if existing:
                    return existing
            except DownloadError:
                return unique_existing_files(scan_output_files(output_dir))
        info = ydl.extract_info(url, download=True)
        files = collect_downloaded_files(info)
        files.extend(scan_output_files(output_dir))
        existing = unique_existing_files(files)
        if existing:
            return existing
        download_direct_media(info, output_dir)
        return unique_existing_files(scan_output_files(output_dir))


def load_cookie_options():
    browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip()
    if not browser:
        return {}
    parts = [part.strip() for part in browser.split(",") if part.strip()]
    if not parts:
        return {}
    return {"cookiesfrombrowser": tuple(parts)}


def collect_downloaded_files(info):
    files = []
    if not isinstance(info, dict):
        return files
    for item in info.get("requested_downloads") or []:
        path = item.get("filepath")
        if path:
            files.append(path)
    for entry in info.get("entries") or []:
        files.extend(collect_downloaded_files(entry))
    return files


def scan_output_files(output_dir):
    files = []
    for root, _, names in os.walk(output_dir):
        for name in names:
            path = os.path.join(root, name)
            if os.path.isfile(path) and media_extension(path):
                files.append(path)
    return files


def download_direct_media(info, output_dir):
    urls = collect_direct_media_urls(info)
    download_urls(urls, output_dir)


def scrape_direct_media(url, output_dir):
    try:
        response = requests.get(url, timeout=30, headers=request_headers(url), allow_redirects=True)
        response.raise_for_status()
    except Exception:
        return
    urls = collect_html_media_urls(response.text)
    download_urls(urls, output_dir, referer=response.url)


def collect_html_media_urls(html):
    html = unescape(str(html or ""))
    html = html.replace("\\/", "/")
    meta_urls = collect_meta_media_urls(html)
    if meta_urls:
        return meta_urls
    urls = []
    for match in SCRAPE_MEDIA_RE.finditer(html):
        value = match.group(0).replace("\\/", "/")
        value = value.encode("utf-8").decode("unicode_escape", errors="ignore")
        if is_direct_media_url(value):
            urls.append(value)
    return list(dict.fromkeys(urls))


def collect_meta_media_urls(html):
    urls = []
    for tag in META_TAG_RE.findall(html):
        prop_match = META_PROP_RE.search(tag)
        content_match = META_CONTENT_RE.search(tag)
        if not prop_match or not content_match:
            continue
        prop = prop_match.group(1).lower()
        if prop not in {"og:image", "og:image:url", "og:video", "og:video:url", "twitter:image", "twitter:player"}:
            continue
        value = content_match.group(1).replace("\\/", "/")
        if is_direct_media_url(value):
            urls.append(value)
    return list(dict.fromkeys(urls))


def download_douyin_wtf_media(url, output_dir):
    api_base = os.getenv("DOUYIN_WTF_API_BASE", "https://douyin.wtf").rstrip("/")
    data = fetch_douyin_wtf_data(api_base, url)
    if not isinstance(data, dict):
        return
    urls = collect_douyin_wtf_urls(data)
    download_urls(urls, output_dir, referer=url)


def fetch_douyin_wtf_data(api_base, url):
    try:
        response = requests.get(
            f"{api_base}/api/hybrid/video_data",
            params={"url": url, "minimal": "false"},
            timeout=60,
            headers=request_headers(url),
        )
        if response.ok:
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    aweme_id = extract_aweme_id(url)
    if not aweme_id:
        return None
    try:
        response = requests.get(
            f"{api_base}/api/douyin/web/fetch_one_video",
            params={"aweme_id": aweme_id},
            timeout=60,
            headers=request_headers(url),
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None
    data = payload.get("data") if isinstance(payload, dict) else None
    return data if isinstance(data, dict) else None


def collect_douyin_wtf_urls(data):
    urls = []
    image_post = data.get("image_post_info")
    images = image_post.get("images") if isinstance(image_post, dict) else None
    if isinstance(images, list):
        for image in images:
            if not isinstance(image, dict):
                continue
            urls.extend(url_list_from_path(image, "display_image"))
            if not urls:
                urls.extend(url_list_from_path(image, "thumbnail"))
    if not urls:
        video = data.get("video")
        if isinstance(video, dict):
            for key in ("download_addr", "play_addr"):
                urls.extend(url_list_from_path(video, key))
                if urls:
                    break
            for bitrate in video.get("bit_rate") or []:
                if urls:
                    break
                if isinstance(bitrate, dict):
                    urls.extend(url_list_from_path(bitrate, "play_addr"))
    return list(dict.fromkeys(url for url in urls if isinstance(url, str) and url.startswith("http")))


def url_list_from_path(data, key):
    value = data.get(key) if isinstance(data, dict) else None
    if isinstance(value, dict):
        url_list = value.get("url_list")
        if isinstance(url_list, list):
            return [url for url in url_list if isinstance(url, str)]
        url = value.get("url")
        return [url] if isinstance(url, str) else []
    return [value] if isinstance(value, str) else []


def extract_aweme_id(url):
    patterns = [
        r"/video/(\d+)",
        r"/photo/(\d+)",
        r"aweme_id=(\d+)",
        r"modal_id=(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, str(url))
        if match:
            return match.group(1)
    return ""


def download_urls(urls, output_dir, referer=None):
    for index, url in enumerate(urls, start=1):
        ext = media_extension(url) or ".jpg"
        path = os.path.join(output_dir, f"media-{index:03d}{ext}")
        try:
            with requests.get(url, stream=True, timeout=120, headers=request_headers(referer or url)) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "").lower()
                if ext == ".jpg" and "video" in content_type:
                    path = os.path.splitext(path)[0] + ".mp4"
                elif ext == ".jpg" and "image/webp" in content_type:
                    path = os.path.splitext(path)[0] + ".webp"
                elif ext == ".jpg" and "image/png" in content_type:
                    path = os.path.splitext(path)[0] + ".png"
                elif ext == ".jpg" and "image/gif" in content_type:
                    path = os.path.splitext(path)[0] + ".gif"
                if "image" not in content_type and "video" not in content_type:
                    continue
                total = 0
                with open(path, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            total += len(chunk)
                            fp.write(chunk)
                if total < MIN_DIRECT_BYTES:
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        except Exception:
            continue


def collect_direct_media_urls(info):
    urls = []
    fallback_urls = []
    if not isinstance(info, dict):
        return urls
    for key in ("url", "webpage_url"):
        value = info.get(key)
        if is_direct_media_url(value):
            urls.append(value)
    for item in info.get("formats") or []:
        value = item.get("url")
        if is_direct_media_url(value):
            urls.append(value)
    for item in info.get("images") or []:
        value = item.get("url")
        if is_direct_media_url(value):
            urls.append(value)
    for key in ("thumbnail",):
        value = info.get(key)
        if is_direct_media_url(value):
            fallback_urls.append(value)
    for item in info.get("thumbnails") or []:
        value = item.get("url")
        if is_direct_media_url(value):
            fallback_urls.append(value)
    for entry in info.get("entries") or []:
        urls.extend(collect_direct_media_urls(entry))
    return list(dict.fromkeys(urls or fallback_urls))


def is_direct_media_url(value):
    if not value or not isinstance(value, str):
        return False
    return media_extension(value) is not None


def media_extension(url):
    path = urlparse(str(url)).path.lower()
    _, ext = os.path.splitext(path)
    return ext if ext in MEDIA_EXTENSIONS else None


def request_headers(referer=None):
    headers = {
        "User-Agent": os.getenv(
            "YTDLP_USER_AGENT",
            "Mozilla/5.0",
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    cookie = os.getenv("YTDLP_COOKIE") or os.getenv("YTDLP_COOKIES") or ""
    if cookie:
        headers["Cookie"] = cookie
    return headers


def unique_existing_files(paths):
    seen = set()
    files = []
    for path in paths:
        normalized = os.path.abspath(path)
        if normalized in seen:
            continue
        seen.add(normalized)
        if os.path.exists(normalized) and os.path.getsize(normalized) > 0:
            files.append(normalized)
    return files


def send_files(ctx, files):
    image_paths = [path for path in files if detect_file_type(path) == "image"]
    other_paths = [path for path in files if detect_file_type(path) != "image"]
    failed = 0
    if image_paths and not send_image_files(ctx, image_paths):
        failed += len(image_paths)
    for path in other_paths:
        if not send_file(ctx, path):
            failed += 1
    return failed


def send_image_files(ctx, paths):
    try:
        sender = getattr(ctx, "send_multiple_images", None)
        if sender:
            sender(ctx.to, paths)
        elif len(paths) > 1 and hasattr(ctx.cl, "uploadMultipleImageToTalk"):
            ctx.cl.uploadMultipleImageToTalk(ctx.to, paths)
        else:
            ctx.cl.sendImage(ctx.to, paths[0])
        return True
    except Exception as exc:
        ctx.log_error(exc)
        if is_private_e2ee_send_error(ctx, exc):
            ctx.reply("私訊可能因為 E2EE/Letter Sealing 無法傳送影片，請改到群組或重新建立私訊加密金鑰後再試。")
    return False


def send_file(ctx, path):
    media_type = detect_file_type(path)
    try:
        if media_type == "image":
            ctx.cl.sendImage(ctx.to, path)
            return True
        if media_type == "video":
            ctx.cl.sendVideo(ctx.to, path)
            return True
        ctx.reply(f"不支援的檔案格式：{os.path.basename(path)}")
    except Exception as exc:
        ctx.log_error(exc)
        if is_private_e2ee_send_error(ctx, exc):
            ctx.reply("私訊可能因為 E2EE/Letter Sealing 無法傳送影片，請改到群組或重新建立私訊加密金鑰後再試。")
    return False


def is_private_e2ee_send_error(ctx, exc):
    if getattr(ctx.msg, "toType", None) != 0:
        return False
    text = str(exc)
    return "can not send using plain mode" in text or "selfKey should not be None" in text


def detect_file_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "unknown"


def extract_url(value):
    match = URL_RE.search(str(value or ""))
    if not match:
        return ""
    return match.group(0).rstrip("。．，、；：！？.,;:!?)]}>\"'")


def is_http_url(url):
    parsed = urlparse(str(url))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def safe_remove_tree(path):
    for _ in range(20):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            import time
            time.sleep(0.25)
