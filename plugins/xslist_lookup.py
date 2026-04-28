import os
import re
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from lxml import html


FEATURE_KEY = "xslist"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://xslist.org"
COMMAND_RE = re.compile(r"^(?:xs|xslist):(.{1,80})$")


def handle(ctx):
    match = COMMAND_RE.fullmatch(ctx.cmd.strip())
    if not match:
        return False
    query = match.group(1).strip()
    if not query:
        ctx.reply("請輸入 XSList 搜尋關鍵字，例如：xs:三上悠亞")
        return True
    try:
        results = search_xslist(query)
    except Exception as exc:
        ctx.log_error(exc)
        ctx.reply(
            "XSList 目前無法讀取，可能被 Cloudflare 擋住。\n"
            "可以在 .env 補 XSList cookie 後再試，或直接開啟：\n"
            f"{search_url(query)}"
        )
        return True
    ctx.send_template(ctx.to, build_xslist_template(query, results))
    return True


def search_xslist(query):
    load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }
    cookie = os.getenv("XSLIST_COOKIE", "").strip()
    if cookie:
        headers["Cookie"] = cookie
    response = requests.get(search_url(query), headers=headers, timeout=30)
    response.raise_for_status()
    if "cf_chl" in response.text or "Enable JavaScript and cookies" in response.text:
        raise RuntimeError("XSList Cloudflare challenge")
    doc = html.fromstring(response.text)
    rows = []
    for node in doc.xpath("//a[@href]"):
        href = node.get("href") or ""
        text = normalize(" ".join(node.xpath(".//text()")))
        if not text or len(text) < 2:
            continue
        if "/zh/" not in href and "/model" not in href and "/star" not in href:
            continue
        url = href if href.startswith("http") else BASE_URL + href
        if url in {row["url"] for row in rows}:
            continue
        rows.append({"title": text[:80], "url": url})
        if len(rows) >= 8:
            break
    if not rows:
        raise RuntimeError("XSList no results")
    return rows


def search_url(query):
    return f"{BASE_URL}/zh/search?query={quote_plus(query)}"


def normalize(value):
    return re.sub(r"\s+", " ", value or "").strip()


def build_xslist_template(query, results):
    contents = [
        {"type": "text", "text": "XSList 搜尋", "weight": "bold", "size": "xl", "color": "#5b3b73"},
        {"type": "text", "text": f"關鍵字：{query}", "size": "sm", "color": "#666666", "wrap": True},
        {"type": "separator", "margin": "md"},
    ]
    for index, item in enumerate(results[:6], start=1):
        contents.extend([
            {"type": "text", "text": f"{index}. {item['title']}", "size": "sm", "weight": "bold", "wrap": True},
            {"type": "button", "height": "sm", "style": "link", "action": {"type": "uri", "label": "開啟頁面", "uri": item["url"]}},
        ])
    return {
        "type": "flex",
        "altText": "XSList 搜尋結果",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "backgroundColor": "#fff7fb",
                "contents": contents[:45],
            },
        },
    }
