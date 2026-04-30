from plugins.ytdlp_download import extract_url, is_http_url, send_ytdlp_media_async


FEATURE_KEY = "facebook_download"


def handle(ctx):
    if not ctx.cmd.startswith("fb:"):
        return False
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入 Facebook 影片網址。\n範例：fb:https://www.facebook.com/watch/?v=xxxxx")
        return True
    lowered = url.lower()
    if not is_http_url(url) or not any(host in lowered for host in ("facebook.com", "fb.watch")):
        ctx.reply("Facebook 網址格式不正確。")
        return True
    send_ytdlp_media_async(ctx, url, label="Facebook 影片")
    return True
