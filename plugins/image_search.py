import os

from dotenv import load_dotenv
from PicImageSearch.sync import (
    SauceNAO as SauceNAOSync,
    Ascii2D as Ascii2DSync,
    TraceMoe as TraceMoeSync,
    AnimeTrace as AnimeTraceSync,
    EHentai as EHentaiSync,
    Copyseeker as CopyseekerSync,
    Yandex as YandexSync,
    Iqdb as IqdbSync,
    Network as PicNetworkSync,
)

from plugins.core.template import Chino


FEATURE_KEY = "image_search"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

ENGINE_FEATURE_KEYS = {
    "SauceNAO": "engine_saucenao",
    "Ascii2D": "engine_ascii2d",
    "TraceMoe": "engine_tracemoe",
    "EHentai": "engine_ehentai",
    "ExHentai": "engine_exhentai",
    "Copyseeker": "engine_copyseeker",
    "Yandex": "engine_yandex",
    "Iqdb": "engine_iqdb",
    "AnimeTrace": "engine_animetrace",
}

SEARCH_COMMANDS = {
    "回覆搜1": ("SauceNAO.jpg", "SauceNAO", "SauceNAO"),
    "回覆搜2": ("Ascii2D.jpg", "Ascii2D", "Ascii2D"),
    "回覆搜3": ("TraceMoe.jpg", "TraceMoe", "TraceMoe"),
    "回覆搜4": ("EHentai.jpg", "E-Hentai", "EHentai"),
    "回覆搜5": ("ExHentai.jpg", "ExHentai", "ExHentai"),
    "回覆搜6": ("Copyseeker.jpg", "Copyseeker", "Copyseeker"),
    "回覆搜7": ("Yandex.jpg", "Yandex", "Yandex"),
    "回覆搜8": ("Iqdb.jpg", "Iqdb", "Iqdb"),
    "回覆搜9": ("AnimeTrace.jpg", "AnimeTrace", "AnimeTrace"),
}

TEMPLATE_COMMANDS = {
    "模板搜1": "SauceNAO",
    "#1": "SauceNAO",
    "模板搜2": "Ascii2D",
    "#2": "Ascii2D",
    "模板搜3": "TraceMoe",
    "#3": "TraceMoe",
}


def handle(ctx):
    if ctx.cmd in SEARCH_COMMANDS:
        return handle_reply_search(ctx)
    if ctx.cmd in TEMPLATE_COMMANDS:
        return handle_template_search(ctx)
    return False


def handle_reply_search(ctx):
    save_name, engine_label, engine = SEARCH_COMMANDS[ctx.cmd]
    if not is_engine_enabled(ctx, engine, engine_label):
        return True

    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("請回覆一張圖片再使用圖搜指令。")
        return True

    if not consume_search_quota(ctx):
        return True

    try:
        download_reply_image(ctx, related_message_id, save_name)
        result_text, video_url = search_as_text(engine, save_name)
        ctx.cl.relatedMessage(ctx.to, result_text, ctx.msg_id)
        if video_url:
            ctx.cl.sendVideoWithURL(ctx.to, str(video_url))
    except Exception as exc:
        ctx.log_error(exc)
        message = user_facing_error(exc) or "搜尋失敗,請換個方式或重新搜尋"
        ctx.cl.relatedMessage(ctx.to, message, ctx.msg_id)
    finally:
        safe_remove(save_name)

    finish_search(ctx)
    return True


def handle_template_search(ctx):
    if not ctx.is_creator:
        ctx.reply("此為作者使用功能٩(ˊᗜˋ*)و")
        return True
    related_message_id = getattr(ctx.msg, "relatedMessageId", None)
    if not related_message_id:
        ctx.reply("請回覆一張圖片再使用模板搜。")
        return True

    engine = TEMPLATE_COMMANDS[ctx.cmd]
    if not is_engine_enabled(ctx, engine, engine):
        return True

    save_name = SEARCH_COMMANDS[f"回覆搜{template_engine_number(engine)}"][0]
    try:
        download_reply_image(ctx, related_message_id, save_name)
        send_template_result(ctx, engine, save_name)
    except Exception as exc:
        ctx.log_error(exc)
        message = user_facing_error(exc) or "搜尋失敗,請換個方式或重新搜尋"
        ctx.cl.relatedMessage(ctx.to, message, ctx.msg_id)
    finally:
        safe_remove(save_name)
    return True


def consume_search_quota(ctx):
    if ctx.is_admin:
        return True
    if ctx.settings["days"] <= 0:
        ctx.reply("沒次數了٩(ˊᗜˋ*)و\n請找智乃添加٩(ˊᗜˋ*)و")
        return False
    ctx.settings["days"] -= 1
    ctx.settings["sc"] += 1
    ctx.backup()
    return True


def finish_search(ctx):
    if not ctx.is_admin:
        ctx.cl.relatedMessage(
            ctx.to,
            "剩餘使用次數:{day}".format(day=ctx.settings["days"]),
            ctx.msg_id,
        )


def is_engine_enabled(ctx, engine, label):
    feature_key = ENGINE_FEATURE_KEYS.get(engine)
    if feature_key and not ctx.is_feature_enabled(feature_key):
        ctx.reply(f"{label} 目前已被管理員關閉。")
        return False
    return True


def search_as_text(engine, image_path):
    if engine == "SauceNAO":
        result = first_search_result(
            SauceNAOSync(**picsearch_kwargs(api_key=os.getenv("SauceNAO_api_key"), hide=3)).search(file=image_path),
            "SauceNAO",
        )
        return (
            "下面為SauceNAO的圖搜結果"
            f"\n\n相似度⇛ {result.similarity}"
            f"\n圖片標題⇛ {result.title}"
            f"\n圖片Url⇛ {result.url}"
            f"\n作者⇛ {result.author}"
            f"\n作者Url⇛ {result.author_url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "Ascii2D":
        result = selected_ascii2d_result(ascii2d_search(file=image_path))
        return (
            "下面為Ascii2D的圖搜結果"
            f"\n\n圖片Url⇛ {result.url}"
            f"\n作者Url⇛ {result.author_url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "TraceMoe":
        result = first_search_result(
            TraceMoeSync(**picsearch_kwargs(mute=False, size=None)).search(file=image_path),
            "TraceMoe",
        )
        return (
            "下面為TraceMoe的圖搜結果"
            f"\n\n➮番劇中文名稱⇛ {result.title_chinese}"
            f"\n➮番劇世界名稱⇛ {result.title_native}"
            f"\n➮番劇英文名稱⇛ {result.title_english}"
            f"\n➮番劇是否R18⇛ {result.isAdult}"
            f"\n➮番劇匹配的集數⇛ {result.episode}"
            f"\n➮縮略圖預覽Url⇛ {result.image}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            result.video,
        )

    if engine in {"EHentai", "ExHentai"}:
        label = "E-Hentai" if engine == "EHentai" else "ExHentai"
        result = first_search_result(ehentai_client(is_ex=engine == "ExHentai").search(file=image_path), label)
        return (
            f"下面為{label}的圖搜結果"
            f"\n\n➮本本的標題⇛ {result.title}"
            f"\n➮本本的分類⇛ {result.type}"
            f"\n➮本本的日期⇛ {result.date}"
            f"\n➮本本的url⇛ {result.url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "Copyseeker":
        result = first_search_result(copyseeker_search(file=image_path), "Copyseeker")
        return (
            "下面為Copyseeker的圖搜結果"
            f"\n\n網址排名⇛ {result.website_rank}"
            f"\n圖片標題⇛ {result.title}"
            f"\n圖片Url⇛ {result.url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "Yandex":
        result = first_search_result(YandexSync(**picsearch_kwargs()).search(file=image_path), "Yandex")
        return (
            "下面為Yandex的圖搜結果"
            f"\n\n圖片標題⇛ {result.title}"
            f"\n圖片Url⇛ {result.url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "Iqdb":
        result = first_search_result(IqdbSync(**picsearch_kwargs()).search(file=image_path), "Iqdb")
        return (
            "下面為Iqdb的圖搜結果"
            f"\n\n相似度⇛ {result.similarity}"
            f"\n描述⇛ {result.content}"
            f"\n圖片Url⇛ {result.url}"
            "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و",
            None,
        )

    if engine == "AnimeTrace":
        resp = AnimeTraceSync(**picsearch_kwargs()).search(file=image_path)
        result = first_search_result(resp, "AnimeTrace")
        text = (
            "下面為AnimeTrace的圖搜結果"
            f"\n\nTrace ID⇛ {getattr(resp, 'trace_id', 'N/A')}"
            f"\nAI判定⇛ {getattr(resp, 'ai', 'N/A')}"
            f"\nBox ID⇛ {result.box_id}"
            f"\n座標⇛ {result.box}"
        )
        if result.characters:
            text += "\n\n可能角色:"
            for index, character in enumerate(result.characters[:5], start=1):
                text += f"\n{index}. {character.name} / {character.work}"
        else:
            text += "\n\n可能角色: N/A"
        return text + "\n\n作者:智乃妹妹٩(ˊᗜˋ*)و", None

    raise ValueError(f"Unknown image search engine: {engine}")


def send_template_result(ctx, engine, image_path):
    flex = Chino(ctx.cl)
    if engine == "SauceNAO":
        result = first_search_result(
            SauceNAOSync(**picsearch_kwargs(api_key=os.getenv("SauceNAO_api_key"), hide=3)).search(file=image_path),
            "SauceNAO",
        )
        ctx.send_flex(
            ctx.to,
            "SauceNAO圖搜結果(模版)",
            flex.Sauceliff(
                thumbnail=result.thumbnail,
                url=result.url,
                similarity=result.similarity,
                title=result.title,
                author=result.author,
            ),
        )
        return

    if engine == "Ascii2D":
        result = selected_ascii2d_result(ascii2d_search(file=image_path))
        ctx.send_flex(
            ctx.to,
            "Ascii2D圖搜結果(模版)",
            flex.Asciiliff(result.thumbnail, result.url, result.author_url),
        )
        return

    if engine == "TraceMoe":
        result = first_search_result(
            TraceMoeSync(**picsearch_kwargs(mute=False, size=None)).search(file=image_path),
            "TraceMoe",
        )
        ctx.send_flex(
            ctx.to,
            "TraceMoe圖搜結果(模版)",
            flex.Traceliff(
                result.image,
                result.video,
                result.title_chinese,
                result.title_native,
                result.title_english,
                result.isAdult,
                result.episode,
            ),
        )
        ctx.cl.sendVideoWithURL(ctx.to, str(result.video))
        return

    raise ValueError(f"Unknown template engine: {engine}")


def template_engine_number(engine):
    return {"SauceNAO": 1, "Ascii2D": 2, "TraceMoe": 3}[engine]


def first_search_result(resp, engine_name):
    if not getattr(resp, "raw", None):
        raise ValueError(f"{engine_name} returned no results")
    return resp.raw[0]


def selected_ascii2d_result(resp):
    if not getattr(resp, "raw", None):
        raise ValueError("Ascii2D returned no results")
    return next((item for item in resp.raw if item.title or item.url_list), resp.raw[0])


def picsearch_kwargs(**extra):
    load_dotenv(os.path.join(ROOT_DIR, ".env"), override=True)
    kwargs = dict(extra)
    proxies = os.getenv("PICSEARCH_PROXIES") or None
    if proxies:
        kwargs["proxies"] = proxies
    return kwargs


def ascii2d_client():
    return Ascii2DSync(
        **picsearch_kwargs(
            base_url=ascii2d_base_urls()[0],
            bovw=False,
            verify_ssl=env_bool("PICSEARCH_VERIFY_SSL", True),
        )
    )


def ascii2d_search(file):
    last_error = None
    for base_url in ascii2d_base_urls():
        try:
            client = Ascii2DSync(
                **picsearch_kwargs(
                    base_url=base_url,
                    bovw=False,
                    verify_ssl=env_bool("PICSEARCH_VERIFY_SSL", True),
                )
            )
            return client.search(file=file)
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("Ascii2D search failed")


def ascii2d_base_urls():
    raw = os.getenv("ASCII2D_BASE_URLS") or os.getenv("ASCII2D_BASE_URL") or "https://ascii2d.net"
    urls = [url.strip().rstrip("/") for url in raw.split(",") if url.strip()]
    if "https://ascii2d.net" not in urls:
        urls.append("https://ascii2d.net")
    return urls


def copyseeker_search(file):
    proxies = os.getenv("PICSEARCH_PROXIES") or None
    network = PicNetworkSync(proxies=proxies) if proxies else PicNetworkSync()
    client = network.start()
    try:
        return CopyseekerSync(client=client).search(file=file)
    finally:
        network.close()


def ehentai_client(is_ex=False):
    timeout = int(os.getenv("PICSEARCH_TIMEOUT", "60"))
    kwargs = {"is_ex": is_ex, "timeout": timeout if not is_ex else max(timeout, 120)}
    if is_ex:
        cookies = os.getenv("EXHENTAI_COOKIES")
        if not cookies:
            raise ValueError("EXHENTAI_COOKIES is required for ExHentai search")
        kwargs["cookies"] = cookies
    else:
        cookies = os.getenv("EHENTAI_COOKIES")
        if cookies:
            kwargs["cookies"] = cookies
    return EHentaiSync(**picsearch_kwargs(**kwargs))


def env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def safe_remove(path):
    for _ in range(20):
        try:
            os.remove(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            import time
            time.sleep(0.25)


def download_reply_image(ctx, related_message_id, save_name):
    try:
        return ctx.cl.downloadObjectMsg(related_message_id, saveAs=save_name, objFrom=ctx.to)
    except Exception as exc:
        if is_private_e2ee_image_context(ctx, exc):
            raise RuntimeError(
                "私訊 E2EE 圖片目前無法下載原圖。請改到群組使用，或在該聊天室關閉 Letter Sealing/E2EE 後重傳圖片。"
            ) from exc
        if is_openchat_download_404(ctx, exc):
            raise RuntimeError("圖片下載失敗：此聊天室可能是 OpenChat，已改用聊天室 ID 判斷下載路徑；請重傳圖片後再試一次。") from exc
        raise


def is_private_e2ee_image_context(ctx, exc):
    text = str(exc)
    if "Invalid response code: 404" not in text and "Download failed" not in text:
        return False
    if getattr(ctx.msg, "toType", None) != 0:
        return False
    return True


def is_openchat_download_404(ctx, exc):
    text = str(exc)
    return "Invalid response code: 404" in text and "/talk/m/" in text and getattr(ctx.msg, "toType", None) != 0


def user_facing_error(exc):
    text = str(exc)
    prefixes = (
        "私訊 E2EE 圖片目前無法下載原圖",
        "圖片下載失敗：",
    )
    if text.startswith(prefixes):
        return text
    return ""
