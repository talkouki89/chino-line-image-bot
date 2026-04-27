import logging
import re

from plugins.core.gallery_template import (
    MAX_PREVIEW_PAGES,
    build_fallback_item,
    build_gallery_flex,
    format_list,
    to_list,
)


try:
    import jmcomic
except Exception:  # pragma: no cover - optional dependency fallback
    jmcomic = None


JM_ALBUM_URL = "https://18comic.vip/album/{album_id}/"
FEATURE_KEY = "jmcomic"


def handle(ctx):
    match = re.fullmatch(r"c:(\d{1,12})", ctx.cmd.strip())
    if not match:
        return False

    album_id = match.group(1)
    try:
        item = fetch_jmcomic(album_id)
    except Exception as exc:
        ctx.log_error(exc)
        item = build_fallback_item("禁漫天堂", "JM", album_id, JM_ALBUM_URL.format(album_id=album_id))

    ctx.send_template(ctx.to, build_gallery_flex(item))
    return True


def fetch_jmcomic(album_id):
    if jmcomic is None:
        raise RuntimeError("jmcomic is not installed")

    jmcomic.JmModuleConfig.disable_jm_log()
    logging.getLogger("jmcomic").disabled = True
    client = jmcomic.JmOption.default().new_jm_client()
    album = client.get_album_detail(album_id)
    props = album.get_properties_dict()
    episodes = props.get("Aepisode_list") or []
    previews = []
    for index, episode in enumerate(episodes[:MAX_PREVIEW_PAGES]):
        episode_id = str(episode[0] if isinstance(episode, (list, tuple)) else episode)
        previews.append(
            {
                "title": f"章節 {index + 1}",
                "image_url": "",
                "url": JM_ALBUM_URL.format(album_id=episode_id),
            }
        )

    return {
        "site": "禁漫天堂",
        "id_label": "JM",
        "id": album_id,
        "title": getattr(album, "title", "") or f"JM{album_id}",
        "url": JM_ALBUM_URL.format(album_id=album_id),
        "show_previews": False,
        "fields": [
            ("作者", format_list(to_list(props.get("Aauthors") or props.get("Aauthor")), 8)),
            ("Pages", props.get("Apage_count") or "N/A"),
            ("Tags", format_list(to_list(props.get("Atags")), 12)),
            ("更新", props.get("Aupdate_date") or "N/A"),
        ],
        "previews": previews,
    }
