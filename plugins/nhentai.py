import re
import os
from pathlib import Path
from urllib.parse import urljoin

import requests
from lxml import html
from dotenv import load_dotenv


API_URL = "https://nhentai.net/api/v2/galleries/{gallery_id}"
POPULAR_API_URL = "https://nhentai.net/api/v2/galleries/popular"
HOME_URL = "https://nhentai.net/"
GALLERY_URL = "https://nhentai.net/g/{gallery_id}/"
PAGE_URL = "https://nhentai.net/g/{gallery_id}/{page}/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MAX_TAGS = 18
MAX_PAGE_LINKS = 5
MAX_POPULAR_ITEMS = 10
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
FEATURE_KEY = "nhentai"


def handle(ctx):
    if ctx.cmd.strip() in {"n:popular", "n:pop", "n:熱門"}:
        try:
            popular_items = fetch_popular_now()
        except Exception as exc:
            ctx.log_error(exc)
            ctx.reply("nHentai Popular Now 讀取失敗，可能需要更新 NHENTAI_COOKIE。")
            return True

        if not popular_items:
            ctx.reply("目前抓不到 Popular Now 排名，可能是頁面結構有更新。")
            return True

        ctx.send_template(ctx.to, build_popular_flex(popular_items))
        return True

    match = re.fullmatch(r"n:(\d{1,8})", ctx.cmd.strip())
    if not match:
        return False

    gallery_id = match.group(1)
    try:
        gallery = fetch_gallery(gallery_id)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply("nHentai 解析失敗，請確認編號是否存在。")
        return True

    ctx.send_template(ctx.to, build_flex(gallery))
    return True


def fetch_gallery(gallery_id):
    response = requests.get(
        API_URL.format(gallery_id=gallery_id),
        headers=build_headers(),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    data["url"] = GALLERY_URL.format(gallery_id=data["id"])
    return data


def fetch_popular_now():
    api_items = fetch_popular_now_from_api()
    if api_items:
        return api_items

    response = requests.get(
        HOME_URL,
        headers=build_headers(accept="text/html,application/xhtml+xml"),
        timeout=20,
    )
    response.raise_for_status()
    tree = html.fromstring(response.text)
    galleries = extract_popular_gallery_nodes(tree)
    return [parse_popular_item(node, index + 1) for index, node in enumerate(galleries[:MAX_POPULAR_ITEMS])]


def fetch_popular_now_from_api():
    response = requests.get(
        POPULAR_API_URL,
        headers=build_headers(),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        return []
    return [
        parse_popular_api_item(item, index + 1)
        for index, item in enumerate(data[:MAX_POPULAR_ITEMS])
    ]


def build_headers(accept="application/json"):
    load_dotenv(ENV_PATH, override=True)
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    cookie = os.getenv("NHENTAI_COOKIE") or os.getenv("NHENTAI_COOKIES")
    if cookie:
        headers["Cookie"] = cookie
    return headers


def extract_popular_gallery_nodes(tree):
    headings = tree.xpath(
        "//*[self::h1 or self::h2 or self::h3][contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'popular now')]"
    )
    for heading in headings:
        galleries = heading.xpath(
            "following::*[contains(concat(' ', normalize-space(@class), ' '), ' gallery ')]"
        )
        if galleries:
            return galleries
    return tree.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' gallery ')]")


def parse_popular_item(node, rank):
    href = first_text(node.xpath(".//a[starts-with(@href, '/g/')]/@href"))
    gallery_id = extract_gallery_id(href)
    title = first_text(node.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' caption ')]//text()"))
    image_url = first_text(
        node.xpath(".//img/@data-src | .//img/@data-original | .//img/@src")
    )
    return {
        "rank": rank,
        "id": gallery_id or "?",
        "title": clean_text(title) or f"nHentai #{gallery_id or '?'}",
        "url": urljoin(HOME_URL, href or ""),
        "image_url": normalize_image_url(image_url),
    }


def parse_popular_api_item(item, rank):
    gallery_id = item.get("id")
    title = (
        item.get("english_title")
        or item.get("pretty_title")
        or item.get("japanese_title")
        or f"nHentai #{gallery_id or '?'}"
    )
    return {
        "rank": rank,
        "id": gallery_id or "?",
        "title": clean_text(title),
        "url": GALLERY_URL.format(gallery_id=gallery_id) if gallery_id else HOME_URL,
        "image_url": normalize_image_url(item.get("thumbnail")),
    }


def build_popular_flex(items):
    return {
        "type": "flex",
        "altText": "nHentai Popular Now",
        "contents": {
            "type": "carousel",
            "contents": [build_popular_bubble(item) for item in items],
        },
    }


def build_popular_bubble(item):
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": f"#{item['rank']}  No. {item['id']}",
                    "weight": "bold",
                    "size": "md",
                },
                {
                    "type": "text",
                    "text": item["title"],
                    "wrap": True,
                    "size": "sm",
                    "maxLines": 4,
                },
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
                        "label": "開啟網站觀看",
                        "uri": item["url"],
                    },
                }
            ],
        },
    }
    if item.get("image_url"):
        bubble["hero"] = {
            "type": "image",
            "url": item["image_url"],
            "size": "full",
            "aspectRatio": "3:4",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "label": f"Rank {item['rank']}",
                "uri": item["url"],
            },
        }
    return bubble


def build_flex(gallery):
    title = gallery.get("title", {})
    display_title = title.get("pretty") or title.get("english") or title.get("japanese") or f"nHentai #{gallery['id']}"
    tags = format_tags(gallery.get("tags", []))
    pages = gallery.get("num_pages", 0)
    page_bubbles = build_page_bubbles(gallery)

    return {
        "type": "flex",
        "altText": f"nHentai #{gallery['id']} - {display_title}",
        "contents": {
            "type": "carousel",
            "contents": [
                build_info_bubble(gallery, display_title, pages, tags),
                *page_bubbles,
            ],
        },
    }


def build_info_bubble(gallery, display_title, pages, tags):
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": display_title,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        field("No.", gallery["id"]),
                        field("Pages", pages),
                        field("Tags", tags),
                    ],
                },
                {
                    "type": "text",
                    "text": "右滑查看前五頁",
                    "size": "sm",
                    "color": "#777777",
                    "wrap": True,
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "開啟網站觀看",
                        "uri": gallery["url"],
                    },
                }
            ],
        },
    }


def field(label, value):
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {
                "type": "text",
                "text": str(label),
                "color": "#777777",
                "size": "sm",
                "flex": 2,
            },
            {
                "type": "text",
                "text": str(value or "N/A"),
                "wrap": True,
                "size": "sm",
                "flex": 5,
            },
        ],
    }


def build_page_bubbles(gallery):
    gallery_id = gallery["id"]
    pages = gallery.get("pages") or []
    limit = min(len(pages), MAX_PAGE_LINKS)
    if limit <= 0:
        return [empty_page_bubble(gallery["url"])]

    bubbles = []
    for index in range(limit):
        page = pages[index]
        page_number = page.get("number") or index + 1
        page_url = PAGE_URL.format(gallery_id=gallery_id, page=page_number)
        bubbles.append(
            {
                "type": "bubble",
                "size": "mega",
                "hero": {
                    "type": "image",
                    "url": page_preview_url(page),
                    "size": "full",
                    "aspectRatio": "2:3",
                    "aspectMode": "cover",
                    "action": {
                        "type": "uri",
                        "label": f"Page {page_number}",
                        "uri": page_url,
                    },
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"Page {page_number}",
                            "weight": "bold",
                            "size": "md",
                        },
                        {
                            "type": "text",
                            "text": "點圖片開啟網站頁面",
                            "size": "xs",
                            "color": "#777777",
                        },
                    ],
                },
            }
        )
    return bubbles


def empty_page_bubble(url):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "沒有頁面資料", "size": "sm", "color": "#777777"}
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
                    "action": {"type": "uri", "label": "開啟網站", "uri": url},
                }
            ],
        },
    }


def format_tags(tags):
    names = []
    for tag in tags:
        if tag.get("type") == "tag":
            names.append(tag.get("name", ""))
    names = [name for name in names if name]
    if not names:
        names = [tag.get("name", "") for tag in tags if tag.get("name")]
    text = ", ".join(names[:MAX_TAGS])
    if len(names) > MAX_TAGS:
        text += f" ... +{len(names) - MAX_TAGS}"
    return text


def page_preview_url(page):
    path = page.get("thumbnail") or page.get("path")
    if path:
        return "https://t.nhentai.net/" + path.lstrip("/")
    return "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png"


def first_text(values):
    for value in values:
        if value:
            return value
    return ""


def clean_text(value):
    return " ".join(str(value or "").split())


def extract_gallery_id(href):
    match = re.search(r"/g/(\d+)/?", href or "")
    return match.group(1) if match else ""


def normalize_image_url(url):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/galleries/") or url.startswith("galleries/"):
        return "https://t.nhentai.net/" + url.lstrip("/")
    if url.startswith("https://nhentai.net/galleries/"):
        return url.replace("https://nhentai.net/galleries/", "https://t.nhentai.net/galleries/", 1)
    return urljoin(HOME_URL, url)
