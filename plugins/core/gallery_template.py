import html as html_module
import re
from urllib.parse import urljoin


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 20
MAX_PREVIEW_PAGES = 5


def build_gallery_flex(item):
    bubbles = [build_info_bubble(item)]
    if item.get("show_previews", True):
        bubbles.extend(build_preview_bubble(preview) for preview in item.get("previews", [])[:MAX_PREVIEW_PAGES])
    return {
        "type": "flex",
        "altText": f"{item['site']} {item['id_label']}:{item['id']} - {item['title']}",
        "contents": {
            "type": "carousel",
            "contents": bubbles[:10],
        },
    }


def build_fallback_item(site, id_label, item_id, url):
    return {
        "site": site,
        "id_label": id_label,
        "id": item_id,
        "title": f"{site} #{item_id}",
        "url": url,
        "fields": [("狀態", "解析失敗，已提供原始連結")],
        "previews": [],
    }


def build_info_bubble(item):
    contents = [
        {"type": "text", "text": item["site"], "size": "sm", "color": "#777777"},
        {"type": "text", "text": item["title"], "weight": "bold", "size": "lg", "wrap": True},
        field("No.", f"{item['id_label']}:{item['id']}"),
    ]
    contents.extend(field(label, value) for label, value in item.get("fields", []))
    if item.get("show_previews", True) and item.get("previews"):
        contents.append({"type": "text", "text": "右滑查看前五頁", "size": "sm", "color": "#777777"})
    elif not item.get("show_previews", True):
        contents.append({"type": "text", "text": "請用按鈕開啟網站查看內容", "size": "sm", "color": "#777777", "wrap": True})
    else:
        contents.append({"type": "text", "text": "無法取得預覽圖，請用按鈕開啟網站", "size": "sm", "color": "#777777", "wrap": True})

    return {
        "type": "bubble",
        "size": "mega",
        "body": {"type": "box", "layout": "vertical", "spacing": "md", "contents": contents},
        "footer": button_footer(item["url"]),
    }


def build_preview_bubble(preview):
    bubble = {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": preview.get("title") or "Preview", "weight": "bold", "size": "md"},
                {"type": "text", "text": "點擊開啟網站頁面", "size": "xs", "color": "#777777"},
            ],
        },
        "footer": button_footer(preview.get("url") or "#"),
    }
    if preview.get("image_url"):
        bubble["hero"] = {
            "type": "image",
            "url": preview["image_url"],
            "size": "full",
            "aspectRatio": "2:3",
            "aspectMode": "cover",
            "action": {"type": "uri", "label": preview.get("title") or "Preview", "uri": preview.get("url") or "#"},
        }
    return bubble


def button_footer(url):
    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "button",
                "style": "primary",
                "height": "sm",
                "action": {"type": "uri", "label": "開啟網站觀看", "uri": url},
            }
        ],
    }


def field(label, value):
    return {
        "type": "box",
        "layout": "baseline",
        "spacing": "sm",
        "contents": [
            {"type": "text", "text": str(label), "color": "#777777", "size": "sm", "flex": 2},
            {"type": "text", "text": str(value or "N/A"), "wrap": True, "size": "sm", "flex": 5},
        ],
    }


def html_headers(referer):
    return {"User-Agent": USER_AGENT, "Referer": referer, "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"}


def normalize_url(url, base):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urljoin(base, url)


def clean_text(value):
    return html_module.unescape(" ".join(str(value or "").split()))


def split_tags(value):
    return [tag.strip() for tag in re.split(r"[,，、/ ]+", value or "") if tag.strip()]


def format_list(values, limit):
    values = [clean_text(value) for value in to_list(values) if clean_text(value)]
    if not values:
        return "N/A"
    text = ", ".join(values[:limit])
    if len(values) > limit:
        text += f" ... +{len(values) - limit}"
    return text


def to_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def first_text(values):
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def first_value_starting(values, prefix):
    for value in values:
        if value.startswith(prefix):
            return value
    return ""


def strip_label(value):
    return re.sub(r"^[^：:]+[：:]\s*", "", value or "").strip()


def extract_first_number(value):
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else ""
