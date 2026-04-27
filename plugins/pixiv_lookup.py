import re

import requests

from plugins.core.gallery_template import (
    MAX_PREVIEW_PAGES,
    TIMEOUT,
    build_fallback_item,
    build_gallery_flex,
    format_list,
    html_headers,
)


PIXIV_ARTWORK_URL = "https://www.pixiv.net/artworks/{illust_id}"
PIXIV_AJAX_URL = "https://www.pixiv.net/ajax/illust/{illust_id}"
PIXIV_PAGES_URL = "https://www.pixiv.net/ajax/illust/{illust_id}/pages"
FEATURE_KEY = "pixiv"


def handle(ctx):
    match = re.fullmatch(r"p:(\d{1,12})", ctx.cmd.strip())
    if not match:
        return False

    illust_id = match.group(1)
    try:
        item = fetch_pixiv(illust_id)
    except Exception as exc:
        ctx.log_error(exc)
        item = build_fallback_item("Pixiv", "P", illust_id, PIXIV_ARTWORK_URL.format(illust_id=illust_id))

    ctx.send_template(ctx.to, build_gallery_flex(item))
    return True


def fetch_pixiv(illust_id):
    info = fetch_json(PIXIV_AJAX_URL.format(illust_id=illust_id))
    if info.get("error"):
        raise RuntimeError(info.get("message") or "Pixiv API error")
    body = info.get("body") or {}

    pages_data = fetch_json(PIXIV_PAGES_URL.format(illust_id=illust_id))
    pages = pages_data.get("body") or []
    previews = [
        {
            "title": f"Page {index + 1}",
            # Pixiv's image CDN requires a Referer header, so LINE Flex cannot
            # reliably render these URLs directly. Keep page cards link-only.
            "image_url": "",
            "url": PIXIV_ARTWORK_URL.format(illust_id=illust_id),
        }
        for index, _page in enumerate(pages[:MAX_PREVIEW_PAGES])
    ]

    tags = [
        tag.get("translation", {}).get("en") or tag.get("tag")
        for tag in (body.get("tags") or {}).get("tags", [])
        if tag.get("tag")
    ]
    return {
        "site": "Pixiv",
        "id_label": "P",
        "id": illust_id,
        "title": body.get("illustTitle") or body.get("title") or f"Pixiv #{illust_id}",
        "url": PIXIV_ARTWORK_URL.format(illust_id=illust_id),
        "show_previews": False,
        "fields": [
            ("作者", body.get("userName") or "N/A"),
            ("Pages", body.get("pageCount") or len(previews) or "N/A"),
            ("Tags", format_list(tags, 12)),
            ("觀看", body.get("viewCount") or "N/A"),
            ("預覽圖", "Pixiv 圖片防盜連，請點網站查看"),
        ],
        "previews": previews,
    }


def fetch_json(url):
    response = requests.get(url, headers=html_headers("https://www.pixiv.net/"), timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()
