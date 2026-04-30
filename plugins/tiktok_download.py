from plugins.ytdlp_download import extract_url, is_http_url, send_ytdlp_media_async


FEATURE_KEY = "tiktok_download"


def handle(ctx):
    if not ctx.cmd.startswith("tk:"):
        return False
    url = extract_url(ctx.text.split(":", 1)[1] if ":" in ctx.text else "")
    if not url:
        ctx.reply("請輸入 TikTok 網址。\n範例：tk:https://www.tiktok.com/@user/video/xxxxx")
        return True
    lowered = url.lower()
    if not is_http_url(url) or not any(host in lowered for host in ("tiktok.com", "vm.tiktok.com", "vt.tiktok.com")):
        ctx.reply("TikTok 網址格式不正確。")
        return True
    send_ytdlp_media_async(ctx, url, label="TikTok 媒體", prefer_direct=True, use_douyin_wtf=True)
    return True
