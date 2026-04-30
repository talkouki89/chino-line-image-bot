from plugins.ytdlp_download import extract_url, is_http_url, send_ytdlp_media_async


FEATURE_KEY = "pornhub_download"


def handle(ctx):
    if not ctx.cmd.startswith("ph:"):
        return False
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入 Pornhub 影片網址。\n範例：ph:https://www.pornhub.com/view_video.php?viewkey=xxxxx")
        return True
    if not is_http_url(url) or "pornhub.com" not in url.lower():
        ctx.reply("Pornhub 網址格式不正確。")
        return True
    send_ytdlp_media_async(ctx, url, label="Pornhub 影片")
    return True
