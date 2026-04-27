from urllib.parse import urlparse, urlunparse

import requests


SUPPORTED_HOSTS = {"vxtwitter.com", "x.com", "twitter.com"}
MEDIA_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def convert_url(original_url):
    parsed = urlparse(original_url.strip())
    host = parsed.netloc.lower()
    if parsed.scheme != "https" or host not in SUPPORTED_HOSTS:
        raise ValueError("Only https://vxtwitter.com, https://x.com, or https://twitter.com URLs are supported")
    return urlunparse(parsed._replace(netloc="api.vxtwitter.com"))


def fetch_media_urls(original_url, timeout=20):
    response = requests.get(convert_url(original_url), timeout=timeout)
    response.raise_for_status()
    data = response.json()
    return data.get("mediaURLs", [])


def detect_file_type(url):
    path = urlparse(url).path.lower()
    if path.endswith(".mp4"):
        return "video"
    if any(path.endswith(ext) for ext in MEDIA_IMAGE_EXTENSIONS):
        return "image"
    return "unknown"


if __name__ == "__main__":
    sample_url = "https://vxtwitter.com/eco_mak1/status/1862797468897038508"
    for media_url in fetch_media_urls(sample_url):
        print(media_url, detect_file_type(media_url))
