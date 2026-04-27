CREATOR_URL = "https://line.me/ti/p/~talkouki"
LABEL_COLOR = "#666666"


def _text(text, **extra):
    data = {"type": "text", "text": str(text or "N/A")}
    data.update(extra)
    return data


def _row(label, value):
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "contents": [
            _text(label, flex=1, size="sm", color=LABEL_COLOR),
            _text(value, flex=2, size="sm", wrap=True),
        ],
    }


def _link_row(label, url, text="點我開啟"):
    return {
        "type": "box",
        "layout": "horizontal",
        "spacing": "sm",
        "contents": [
            _text(label, flex=1, size="sm", color=LABEL_COLOR),
            _text(
                text,
                flex=2,
                size="sm",
                wrap=True,
                color="#2563eb",
                decoration="underline",
                action={"type": "uri", "label": text, "uri": str(url or CREATOR_URL)},
            ),
        ],
    }


def _bubble(title, thumbnail, action_url, rows, colors):
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "image",
                    "url": str(thumbnail or "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png"),
                    "size": "full",
                    "aspectRatio": "1:1",
                    "aspectMode": "cover",
                    "action": {"type": "uri", "label": "open", "uri": str(action_url or CREATOR_URL)},
                },
                _text(title, size="xl", weight="bold", align="center", wrap=True),
                {"type": "separator"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": rows,
                },
                {"type": "separator", "margin": "lg"},
                _text(
                    "作者：智乃妹妹",
                    size="xs",
                    align="end",
                    color="#555555",
                    action={"type": "uri", "label": "creator", "uri": CREATOR_URL},
                ),
            ],
            "background": {
                "type": "linearGradient",
                "angle": "0deg",
                "startColor": colors[0],
                "endColor": colors[1],
            },
        },
    }


class Chino:
    def __init__(self, client):
        self.client = client

    def Sauceliff(self, thumbnail, url, similarity, title, author):
        return _bubble(
            "SauceNAO 圖搜結果",
            thumbnail,
            url,
            [
                _row("相似度", similarity),
                _row("標題", title),
                _row("作者", author),
                _link_row("連結", url),
            ],
            ("#FFAAD5", "#B15BFF"),
        )

    def Asciiliff(self, thumbnail, url, authors_url):
        return _bubble(
            "Ascii2D 圖搜結果",
            thumbnail,
            url,
            [
                _link_row("作者連結", authors_url),
                _link_row("圖片連結", url),
            ],
            ("#436EEE", "#66CDAA"),
        )

    def Traceliff(self, image, video, title_chinese, title_native, title_english, isAdult, episode):
        return _bubble(
            "TraceMoe 圖搜結果",
            image,
            video,
            [
                _row("中文名", title_chinese),
                _row("原文名", title_native),
                _row("英文名", title_english),
                _row("R18", isAdult),
                _row("集數", episode),
                _link_row("預覽影片", video),
            ],
            ("#FFBD9D", "#9393FF"),
        )
