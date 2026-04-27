import re
from urllib.parse import urljoin

import requests
from lxml import html

from plugins.core.gallery_template import (
    MAX_PREVIEW_PAGES,
    TIMEOUT,
    build_fallback_item,
    build_gallery_flex,
    clean_text,
    extract_first_number,
    first_text,
    first_value_starting,
    format_list,
    html_headers,
    normalize_url,
    split_tags,
    strip_label,
)


WNACG_HOME = "https://www.wnacg.com/"
WNACG_ALBUM_URL = "https://www.wnacg.com/photos-index-aid-{album_id}.html"
FEATURE_KEY = "wnacg"


def handle(ctx):
    match = re.fullmatch(r"w:(\d{1,12})", ctx.cmd.strip())
    if not match:
        return False

    album_id = match.group(1)
    try:
        item = fetch_wnacg(album_id)
    except Exception as exc:
        ctx.log_error(exc)
        item = build_fallback_item("紳士漫畫", "W", album_id, WNACG_ALBUM_URL.format(album_id=album_id))

    ctx.send_template(ctx.to, build_gallery_flex(item))
    return True


def fetch_wnacg(album_id):
    url = WNACG_ALBUM_URL.format(album_id=album_id)
    response = requests.get(url, headers=html_headers(WNACG_HOME), timeout=TIMEOUT)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    tree = html.fromstring(response.text)

    title = first_text(tree.xpath("//h2/text()")) or cleanup_title(tree.xpath("string(//title)"))
    tags = tree.xpath("//meta[translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='keywords']/@content")
    tags = split_tags(first_text(tags))
    info_text = [clean_text(text) for text in tree.xpath("//*[contains(@class,'asTB')]//text()")]
    page_count = extract_first_number(first_value_starting(info_text, "頁數"))
    category = strip_label(first_value_starting(info_text, "分類"))
    previews = build_wnacg_previews(tree)

    return {
        "site": "紳士漫畫",
        "id_label": "W",
        "id": album_id,
        "title": title or f"紳士漫畫 #{album_id}",
        "url": url,
        "fields": [
            ("分類", category or "N/A"),
            ("Pages", page_count or len(previews) or "N/A"),
            ("Tags", format_list(tags, 12)),
        ],
        "previews": previews,
    }


def build_wnacg_previews(tree):
    image_urls = tree.xpath("//*[contains(@class,'pic_box')]//img/@src")
    page_urls = tree.xpath("//*[contains(@class,'pic_box')]//a/@href")
    previews = []
    for index, image_url in enumerate(image_urls[:MAX_PREVIEW_PAGES]):
        page_url = page_urls[index] if index < len(page_urls) else ""
        previews.append(
            {
                "title": f"Page {index + 1}",
                "image_url": normalize_url(image_url, WNACG_HOME),
                "url": urljoin(WNACG_HOME, page_url) if page_url else "",
            }
        )
    return previews


def cleanup_title(value):
    value = clean_text(value)
    return re.sub(r"\s*-\s*紳士漫畫.*$", "", value)
