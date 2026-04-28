# -*- coding: utf-8 -*-
"""Chino LINE image-search bot.

This file is the stable runtime core: it logs in once, keeps polling LINE,
routes built-in commands, and dispatches hot-reload plugins from plugins/.

When adding new commands, prefer plugins/*.py so the bot does not need to log
in again. Edit main.py only for shared helpers, API integration, or core
routing behavior.
"""

# LINE compatibility layer.
from line_api_compat import LINE, OEPoll
from plugin_loader import PluginManager, make_context
from plugins.core.features import (
    FEATURE_INDEX,
    is_enabled as feature_is_enabled,
    load_feature_flags,
    toggle_feature,
)
from plugins.core.help_template import GITHUB_URL, build_help_flex, build_settings_flex, build_status_flex, build_version_check_flex
from dotenv import load_dotenv
from datetime import datetime
import threading
import time
import random
import sys
import json
import pytz
import ast
import os
import re
import asyncio
import base64
import subprocess
import traceback
import urllib.request

# Project paths. Runtime json/tag/plugin folders are created on startup.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "json")
TAG_DIR = os.path.join(ROOT_DIR, "tag")
PLUGIN_DIR = os.path.join(ROOT_DIR, "plugins")
ERROR_LOG = os.path.join(ROOT_DIR, "errorLog.txt")
FEATURE_FLAGS_PATH = os.path.join(DATA_DIR, "features.json")
VERSION_FILE = os.path.join(ROOT_DIR, "VERSION")
VERSION_NOTES_FILE = os.path.join(ROOT_DIR, "VERSION_NOTES.md")
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/talkouki89/chino-line-image-bot/master/VERSION"
REMOTE_VERSION_API_URL = "https://api.github.com/repos/talkouki89/chino-line-image-bot/contents/VERSION?ref=master"
REMOTE_VERSION_NOTES_URL = "https://raw.githubusercontent.com/talkouki89/chino-line-image-bot/master/VERSION_NOTES.md"
REMOTE_VERSION_NOTES_API_URL = "https://api.github.com/repos/talkouki89/chino-line-image-bot/contents/VERSION_NOTES.md?ref=master"
GITHUB_PULLS_API = "https://api.github.com/repos/talkouki89/chino-line-image-bot/pulls?state=closed&base=master&sort=updated&direction=desc&per_page=5"
LIFF_ALLOW_MESSAGE = "請Bot允許liff line://app/1660845055-GMJrEOVY?type=text&text=LiffOk"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TAG_DIR, exist_ok=True)
os.makedirs(PLUGIN_DIR, exist_ok=True)


def load_json(path, default):
    """Load JSON data, returning default when the file is missing or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def dump_json(path, data):
    """Write JSON using UTF-8 so Chinese command/state text is preserved."""
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)


def read_text_file(path):
    """Read a UTF-8 text asset, such as help/*.txt."""
    with open(path, "r", encoding="utf-8") as fp:
        return fp.read()


def env_bool(name, default=False):
    """Parse .env boolean values like true/false, yes/no, 1/0."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    """Parse .env integer values with a safe fallback."""
    raw = os.getenv(name)
    try:
        return int(raw) if raw not in (None, "") else int(default)
    except (TypeError, ValueError):
        return int(default)


# Environment and bot configuration.
load_dotenv(os.path.join(ROOT_DIR, '.env'))
account = os.getenv('LINE_ACCOUNT')
password = os.getenv('LINE_PASSWORD')
HOT_RELOAD_PLUGINS = env_bool("HOT_RELOAD_PLUGINS", True)
botcreator = os.getenv('Creator')
# Legacy variable names kept to avoid a large risky rewrite:
# - botcreator: creator/admin MID string from .env
# - background: chat/group id that receives status notifications
# - datadir["gid"]: current target chat for image-search helper functions
background = os.getenv('Dio_GID')
GROUP_MIN_MEMBER_CHECK = env_bool("GROUP_MIN_MEMBER_CHECK", True)
GROUP_MIN_MEMBERS = env_int("GROUP_MIN_MEMBERS", 10)

# LINE login happens here. Editing main.py after this point still requires a
# process restart; use plugins/ for commands that should hot-reload.
cl = LINE(account, password)

# Persistent bot state.
settings = load_json(os.path.join(DATA_DIR, "temp.json"), {"days": 0, "sc": 0})
ban = load_json(os.path.join(DATA_DIR, "ban.json"), {"admin": []})
feature_flags = load_feature_flags(FEATURE_FLAGS_PATH)

# Shared service objects.
oepoll = OEPoll(cl)
clProfile = cl.getProfile()
clMID = cl.profile.mid
mulai = time.time()
datadir = {"gid": ""}
plugins = PluginManager(PLUGIN_DIR, enabled=HOT_RELOAD_PLUGINS)

# Ensure the configured creator is always an admin.
if botcreator not in ban["admin"]:
    ban["admin"].append(botcreator)

DEFAULT_BOT_DISPLAY_NAME = "智乃搜圖機器人🍥"
DEFAULT_BOT_STATUS_MESSAGE = f"使用請輸入 圖搜說明\nGitHub: {GITHUB_URL}\n作者: 智乃妹妹"
DEFAULT_AUTO_FRIEND_MESSAGE = (
    "感謝加入智乃搜圖機器人٩(ˊᗜˋ*)و\n\n"
    "建議把我邀請到群組使用，圖片解析會比私訊穩定。\n"
    "私訊可能因為 E2EE/Letter Sealing 無法下載圖片。\n\n"
    "使用方式：輸入「圖搜說明」查看指令\n"
    f"GitHub：{GITHUB_URL}\n\n"
    "遇到 bug 可以開 issue。\n"
    "想加新功能也歡迎發 PR (๑•̀ㅂ•́)و✧"
)
BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", DEFAULT_BOT_DISPLAY_NAME)
BOT_STATUS_MESSAGE = os.getenv("BOT_STATUS_MESSAGE", DEFAULT_BOT_STATUS_MESSAGE).replace("\\n", "\n")
AUTO_FRIEND_MESSAGE = os.getenv("AUTO_FRIEND_MESSAGE", DEFAULT_AUTO_FRIEND_MESSAGE).replace("\\n", "\n")

try:
    cl.updateProfileAttribute(2, BOT_DISPLAY_NAME)
    cl.updateProfileAttribute(16, BOT_STATUS_MESSAGE)
except Exception as exc:
    print(f"Profile update failed: {exc}")

# General utilities.
def color():
    """Return a random terminal color escape code for startup logs."""
    color_num1 = ["0", "1"]
    color_num2 = ["31", "32", "33", "34", "35", "36", "37"]
    color_list = [
        "\033[0;32;31m",
        "\033[0;32;32m",
        "\033[0;32;34m",
        "\033["+random.choice(color_num1)+";"+random.choice(color_num2)+"m"]
    return random.choice(color_list)

def logError(text):
    """Log an exception/message to LINE logger and errorLog.txt."""
    cl.log("[ 錯誤 ] " + str(text))
    time_ = datetime.now()
    with open(ERROR_LOG, "a", encoding="utf-8") as error:
        error.write("\n[%s] %s" % (str(time_), text))    

def backupData():
    """Persist runtime counters and permission lists."""
    dump_json(os.path.join(DATA_DIR, "temp.json"), settings)
    dump_json(os.path.join(DATA_DIR, "ban.json"), ban)
    return True


def is_feature_enabled(key):
    """Return whether a bot feature is enabled."""
    return feature_is_enabled(feature_flags, key)


def toggle_feature_command(key):
    """Toggle a feature and persist it to json/features.json."""
    return toggle_feature(FEATURE_FLAGS_PATH, feature_flags, key)


def is_manager(sender):
    """Return True when sender can manage bot settings."""
    return sender in ban["admin"] or (botcreator and sender in botcreator)

def UpgradePicapi():
    """Upgrade PicImageSearch from GitHub without restarting LINE login first."""
    print("更新api中")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--no-deps", "git+https://github.com/kitUIN/PicImageSearch.git"],
        check=True,
    )
    print("api更新完畢!")

def restartBot():
    """Save state and restart the whole process. This will log in again."""
    print("重啟中")
    backupData()
    python = sys.executable
    os.execl(python, python, *sys.argv)

def ChinoRestart():
    """Restart the whole process without saving runtime state first."""
    print("重啟中")
    python = sys.executable
    os.execl(python, python, *sys.argv)
    
def sendTemplate(to, data):
    """Send a LIFF message through the configured LIFF id."""
    result = cl.sendLiff(to, data, liffId='1660845055-GMJrEOVY')
    if is_liff_error(result):
        alt_text = template_alt_text(data)
        logError(f"LIFF template send failed: {result}")
        fallback = template_fallback_text(data)
        lines = [fallback or alt_text, LIFF_ALLOW_MESSAGE]
        cl.sendMessage(to, "\n\n".join(line for line in lines if line))
    return result


def sendFlex(to, alt, flex):
    """Wrap a Flex bubble/container and send it through LIFF."""
    data = {"type": "flex", "altText": alt, "contents": flex}
    sendTemplate(to, data)    


def is_liff_error(result):
    """CHRLINE sendLiff returns response text instead of raising on API errors."""
    if isinstance(result, Exception):
        return True
    if not isinstance(result, str):
        return False
    normalized = result.strip()
    if normalized in ("", "{}", "[]", "null"):
        return False
    lowered = normalized.lower()
    return any(token in lowered for token in ("error", "invalid", "failed", "message", "details"))


def template_alt_text(data):
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("altText"):
                return item["altText"]
        return "模板訊息"
    if isinstance(data, dict):
        return data.get("altText") or data.get("text") or "模板訊息"
    return "模板訊息"


def template_fallback_text(data):
    messages = data if isinstance(data, list) else [data]
    lines = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("type") == "text":
            lines.append(str(message.get("text", "")))
            continue
        if message.get("type") == "flex":
            alt_text = message.get("altText")
            if alt_text:
                lines.append(f"【{alt_text}】")
            lines.extend(extract_flex_text(message.get("contents")))
    return "\n".join(line for line in lines if line).strip()


def extract_flex_text(node):
    if isinstance(node, list):
        values = []
        for item in node:
            values.extend(extract_flex_text(item))
        return values
    if not isinstance(node, dict):
        return []
    values = []
    if node.get("type") == "text" and node.get("text"):
        values.append(str(node["text"]))
    for key in ("contents", "body", "hero", "footer", "header"):
        if key in node:
            values.extend(extract_flex_text(node[key]))
    return values


def build_auto_friend_message():
    """Message sent when a user adds the bot as a friend."""
    return AUTO_FRIEND_MESSAGE

def Runtime(secs):
    """Format process uptime for the ren command."""
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    return '【 %02d天 %02d時 %02d鐘 %02d秒】\n以上為ㄐㄐ的運行時間' % (days, hours, mins, secs)

def sendMention(to, text="", mids=None):
    """Send a text message with LINE mention metadata.

    Use @! placeholders inside text when mentioning multiple mids.
    """
    if mids is None:
        mids = []
    arrData = ""
    arr = []
    mention = "@chino__bot "
    if mids == []:
        raise Exception("Invalid mids")
    if "@!" in text:
        if text.count("@!") != len(mids):
            raise Exception("Invalid mid")
        texts = text.split("@!")
        textx = ""
        for mid in mids:
            textx += str(texts[mids.index(mid)])
            slen = len(textx)
            elen = len(textx) + 15
            arrData = {'S': str(slen), 'E': str(elen - 4), 'M': mid}
            arr.append(arrData)
            textx += mention
        textx += str(texts[len(mids)])
    else:
        textx = ""
        slen = len(textx)
        elen = len(textx) + 15
        arrData = {'S': str(slen), 'E': str(elen - 4), 'M': mids[0]}
        arr.append(arrData)
        textx += mention + str(text)
    cl.sendMessage(to, textx, {'MENTION': str(
        '{"MENTIONEES":' + json.dumps(arr) + '}')}, 0)


def get_object_value(obj, *names, default=None):
    """Read fields safely from CHRLINE objects, dicts, or compatibility wrappers."""
    for name in names:
        if not name:
            continue
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if not isinstance(name, str):
            continue
        try:
            value = getattr(obj, name)
        except (AttributeError, TypeError):
            continue
        if value not in (None, ""):
            return value
    return default


def safe_send_background(message):
    """Send a status message to the configured background chat when available."""
    if not background:
        return
    try:
        cl.sendMessage(background, message)
    except Exception as exc:
        logError(f"background notify failed: {exc}")


def get_chat_summary(chat_id):
    """Best-effort chat name lookup used by restart/status notifications."""
    chat = None
    last_error = None
    for getter_name in ("getChats", "getChatV2", "getGroup", "getCompactGroup"):
        getter = getattr(cl, getter_name, None)
        if getter is None:
            continue
        try:
            chat = getter(chat_id)
        except Exception as exc:
            last_error = exc
            continue
        name = get_object_value(chat, "name", "chatName", "displayName", default="")
        mid = get_object_value(chat, "id", "chatMid", "mid", default=chat_id)
        if name and name != chat_id:
            return name, mid

    if last_error:
        logError(f"chat name lookup failed for {chat_id}: {last_error}")
    if str(chat_id).startswith("u"):
        return "私訊聊天室", chat_id
    if str(chat_id).startswith("c"):
        return "群組名稱取得失敗", chat_id
    if str(chat_id).startswith("r"):
        return "多人聊天室名稱取得失敗", chat_id
    return "聊天室名稱取得失敗", chat_id


def get_chat_member_count(chat_id):
    """Best-effort member count for group list output."""
    for getter_name in ("getChats", "getChatV2", "getGroup", "getCompactGroup"):
        getter = getattr(cl, getter_name, None)
        if getter is None:
            continue
        try:
            chat = getter(chat_id)
        except Exception:
            continue
        members = get_object_value(chat, "members", "memberMids", default=None)
        if members is None:
            extra = get_object_value(chat, "extra", default=None)
            group_extra = get_object_value(extra, "groupExtra", 1, default=None)
            members = get_object_value(group_extra, "memberMids", default=None)
        try:
            return len(members)
        except TypeError:
            continue
    return "未知"


def should_enforce_group_min_members():
    """Return whether group invite member-count checks are enabled."""
    return GROUP_MIN_MEMBER_CHECK and is_feature_enabled("group_min_member_check")


def member_count_passes_minimum(member_count):
    if not should_enforce_group_min_members():
        return True
    if not isinstance(member_count, int):
        # Unknown counts should not unexpectedly kick the bot after an API change.
        return True
    return member_count >= GROUP_MIN_MEMBERS


def read_local_version():
    try:
        return read_text_file(VERSION_FILE).strip()
    except FileNotFoundError:
        return "0.0.0"


def read_local_version_notes():
    try:
        return read_text_file(VERSION_NOTES_FILE).strip()
    except FileNotFoundError:
        return ""


def fetch_text(url, timeout=15):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "chino-line-image-bot",
            "Accept": "application/vnd.github+json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_github_content(api_url, raw_url):
    try:
        payload = json.loads(fetch_text(api_url))
        content = payload.get("content", "")
        encoding = payload.get("encoding", "")
        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="replace").strip()
    except Exception as exc:
        logError(f"GitHub content API fetch failed, fallback to raw URL: {exc}")
    return fetch_text(raw_url).strip()


def fetch_remote_version():
    return fetch_github_content(REMOTE_VERSION_API_URL, REMOTE_VERSION_URL)


def fetch_remote_version_notes():
    return fetch_github_content(REMOTE_VERSION_NOTES_API_URL, REMOTE_VERSION_NOTES_URL)


def fetch_recent_merged_prs():
    try:
        data = json.loads(fetch_text(GITHUB_PULLS_API))
    except Exception as exc:
        logError(f"version PR fetch failed: {exc}")
        return []
    prs = []
    for item in data:
        if not item.get("merged_at"):
            continue
        body = (item.get("body") or "").strip().replace("\r", "")
        summary = body.split("\n", 1)[0][:120] if body else ""
        prs.append({
            "number": item.get("number"),
            "title": item.get("title") or "",
            "summary": summary,
        })
    return prs


def build_version_check_template():
    local_version = read_local_version()
    try:
        remote_version = fetch_remote_version()
    except Exception as exc:
        logError(f"version check failed: {exc}")
        return build_version_check_flex(local_version, error="無法讀取遠端 VERSION。")

    prs = fetch_recent_merged_prs() if remote_version != local_version else []
    try:
        notes = fetch_remote_version_notes() if remote_version != local_version else read_local_version_notes()
    except Exception as exc:
        logError(f"version notes fetch failed: {exc}")
        notes = read_local_version_notes()
    return build_version_check_flex(local_version, remote_version=remote_version, prs=prs, version_notes=notes)


def update_from_git():
    local_version = read_local_version()
    try:
        remote_version = fetch_remote_version()
    except Exception as exc:
        logError(f"version update check failed: {exc}")
        return False, False, "無法讀取遠端 VERSION，已取消更新。"
    if remote_version == local_version:
        return True, False, f"目前已是最新版本（{local_version}），不需要更新。"

    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    if branch != "master":
        return False, False, f"目前分支是 {branch}，請切回 master 後再更新。"

    subprocess.run(["git", "fetch", "origin", "master"], cwd=ROOT_DIR, check=True)
    result = subprocess.run(
        ["git", "pull", "--ff-only", "origin", "master"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return False, False, (result.stderr or result.stdout or "git pull failed").strip()
    return True, True, (result.stdout or "已更新到最新版本。").strip()


def parse_mentioned_mids(content_metadata):
    """Return MID values from LINE mention metadata."""
    if not content_metadata or "MENTION" not in content_metadata:
        return []
    try:
        mention_data = ast.literal_eval(content_metadata["MENTION"])
    except (SyntaxError, ValueError, TypeError):
        return []
    mentionees = mention_data.get("MENTIONEES", [])
    return [
        item.get("M")
        for item in mentionees
        if isinstance(item, dict) and item.get("M")
    ]


def build_plugin_context(op, msg, text, cmd, to, sender, receiver, msg_id):
    """Build the object passed to hot-reload plugins."""
    def reply(message):
        return cl.relatedMessage(to, str(message), msg_id)

    return make_context(
        cl=cl,
        op=op,
        msg=msg,
        text=text or "",
        cmd=cmd,
        to=to,
        sender=sender,
        receiver=receiver,
        msg_id=msg_id,
        settings=settings,
        ban=ban,
        datadir=datadir,
        tag_dir=TAG_DIR,
        is_creator=sender in botcreator,
        is_admin=sender in ban["admin"],
        reply=reply,
        send_template=sendTemplate,
        send_flex=sendFlex,
        backup=backupData,
        log_error=logError,
        feature_flags=feature_flags,
        is_feature_enabled=is_feature_enabled,
    )
                                   
# txt指令表
def help():  # 指令總表
    return read_text_file(os.path.join(ROOT_DIR, "help", "help.txt"))

def help0():  # 公開功能
    return read_text_file(os.path.join(ROOT_DIR, "help", "help0.txt"))

def help1():  # 一般功能
    return read_text_file(os.path.join(ROOT_DIR, "help", "help1.txt"))

# Startup notification. If this sends successfully but the bot cannot respond,
# the problem is usually the polling loop below, not login.
print(color()+"登入者名稱:"+clProfile.displayName+"\n登入者MID:"+clMID)
print("===== 智乃圖搜2.0已登入完成 =====")
try:
    safe_send_background("【自動發送】\n智乃圖搜2.0登入成功\n➜登錄時間:{time}".format(
        time=(time.time() - mulai)))
except Exception as exc:
    logError(f"startup notify failed: {exc}")

def PicBot(op):
    """Route one LINE operation to the built-in command handlers.

    Important: this is the core runtime router. New experimental commands should
    usually live in plugins/*.py instead, so they can hot-reload without forcing
    a LINE re-login.
    """
    try:
        if op.type == 5 and is_feature_enabled("auto_friend"):
            user_mid = get_object_value(op, "param1", default=None)
            if user_mid and user_mid != clMID:
                try:
                    cl.findAndAddContactsByMid(user_mid)
                except Exception as exc:
                    logError(f"auto friend add failed: {exc}")
                cl.sendMessage(user_mid, build_auto_friend_message())
                return

        if op.type == 13 or op.type == 124:
            contact1 = cl.getContact(op.param2)
            group = cl.getChats(op.param1)
            if clMID in op.param3:
                if op.param2 in botcreator:
                    cl.acceptChatInvitation(op.param1)
                    cl.sendMessage(op.param1, "感謝創作者邀我入群(⁎⁍̴̛ᴗ⁍̴̛⁎)")
                else:
                    group = cl.getChats(op.param1)
                    member_count = get_chat_member_count(op.param1)
                    if member_count_passes_minimum(member_count):
                        cl.acceptChatInvitation(op.param1)
                        cl.sendMessage(op.param1, "感謝您邀請我入群\n此為智乃圖搜器~\n作者友資:")
                        cl.sendContact(
                            op.param1, botcreator)
                        cl.sendMessage(op.param1, "輸入圖搜說明可以查看指令")
                        group_name, group_id = get_chat_summary(op.param1)
                        safe_send_background("通知邀請群組:\n" + str(group_name)+"群組 \n" + str(
                            group_id) + "\n邀請者:\n" + contact1.displayName + "\nMid:\n" + contact1.mid)
                    else:
                        cl.acceptChatInvitation(op.param1)
                        cl.sendMessage(
                            op.param1, f"群組人數小於{GROUP_MIN_MEMBERS}人\n機器將離開群組\n如有特殊需求請洽以下友資")
                        cl.sendContact(
                            op.param1, botcreator)
                        group_name, group_id = get_chat_summary(op.param1)
                        safe_send_background(f"群組人數小於{GROUP_MIN_MEMBERS}人:\n" + str(group_name)+"群組 \n" + str(
                            group_id) + "\n邀請者:\n" + contact1.displayName + "\nMid:\n" + contact1.mid)
                        cl.deleteSelfFromChat(op.param1)
        if op.type == 30 and is_feature_enabled("announcement_notify"):
            update_type = op.param3
            if update_type == "c":
                a = cl.getChatRoomAnnouncements(op.param1)[0]
                creator = a.creatorMid
                ret = (
                    f"[公告已被創建]\n"
                    f"創建者:@!\n"
                    f"文字: {a.contents.text}"
                    #f"連結: {a.contents.link}"
                )
                sendMention(op.param1,ret,[creator])                        
        if op.type == 26 or op.type == 25:  # 25,26發話
            msg = op.message
            text = msg.text
            msg_id = msg.id
            receiver = msg.to
            sender = msg._from
            if msg.toType == 0:
                if sender != cl.profile.mid:
                    to = sender
                else:
                    to = receiver
            else:
                to = receiver
            if text is None:
                cmd = ""
            else:
                cmd = text.lower() 
            if msg.contentMetadata is not None and 'MENTION' in msg.contentMetadata:
                mentions = ast.literal_eval(msg.contentMetadata["MENTION"])["MENTIONEES"]
                for mention in mentions:
                    user_id = mention["M"]
                    tag_file = os.path.join(TAG_DIR, f"{user_id}.json")
                    if os.path.isfile(tag_file):
                        with open(tag_file, "r", encoding="utf-8") as f:
                            who_mark_me = json.load(f)
                    else:
                        who_mark_me = {}
                    if to not in who_mark_me: who_mark_me[to] = {}
                    tag_num = len(who_mark_me[to]) + 1
                    who_mark_me[to][str(tag_num)] = {
                        "sender": sender,
                        "msgid": msg_id,
                        "tagtime": datetime.now(pytz.timezone("Asia/Taipei")).strftime('%m/%d %H:%M:%S')
                    }
                    with open(tag_file, "w", encoding="utf-8") as f:
                        json.dump(who_mark_me, f, sort_keys=True, indent=4, ensure_ascii=False)                                                  
            plugin_context = build_plugin_context(op, msg, text, cmd, to, sender, receiver, msg_id)
            if cmd in {"功能狀態", "功能状态", "功能開啟狀態", "功能列表狀態"}:
                if not is_manager(sender):
                    cl.relatedMessage(to, "此功能只有管理員可以使用。", op.message.id)
                    return
                sendTemplate(to, build_status_flex(feature_flags))
                return
            if cmd in {"功能設定", "功能開關", "功能列表"}:
                if is_manager(sender):
                    sendTemplate(to, build_settings_flex(feature_flags))
                else:
                    cl.relatedMessage(to, "此功能只有管理員可以使用。", op.message.id)
                return
            if cmd.startswith("功能切換 "):
                if not is_manager(sender):
                    cl.relatedMessage(to, "此功能只有管理員可以使用。", op.message.id)
                    return
                feature_key = text.split(None, 1)[1].strip() if text and len(text.split(None, 1)) == 2 else ""
                if feature_key not in FEATURE_INDEX:
                    cl.relatedMessage(to, f"找不到功能：{feature_key}", op.message.id)
                    return
                enabled = toggle_feature_command(feature_key)
                state = "開啟" if enabled else "關閉"
                cl.relatedMessage(to, f"{FEATURE_INDEX[feature_key]['name']} 已{state}", op.message.id)
                return
            if cmd == "版本檢查":
                if not is_manager(sender):
                    cl.relatedMessage(to, "此功能只有管理員可以使用。", op.message.id)
                    return
                sendTemplate(to, build_version_check_template())
                return
            if cmd == "版本更新":
                if not is_manager(sender):
                    cl.relatedMessage(to, "此功能只有管理員可以使用。", op.message.id)
                    return
                cl.relatedMessage(to, "開始更新版本，請稍候。", op.message.id)
                ok, updated, message = update_from_git()
                if ok and updated:
                    cl.relatedMessage(to, f"版本更新完成。\n{message}\nBot 將自動重啟套用新程式。", op.message.id)
                    time.sleep(2)
                    restartBot()
                elif ok:
                    cl.relatedMessage(to, message, op.message.id)
                else:
                    cl.relatedMessage(to, f"版本更新失敗。\n{message}", op.message.id)
                return
            if plugins.dispatch(plugin_context):
                # A hot-reload plugin handled this message. Stop here so built-in
                # command branches do not also process the same text.
                return
            # 半垢主人專屬
            if sender in botcreator:
                # 刪除全部權限
                if cmd == '清圖搜':
                    ban["admin"] = []
                    ban["admin"].append(clMID)
                    ban["admin"].append(botcreator)
                    backupData()
                    cl.relatedMessage(to, "清除全部人的權限ㄌ", op.message.id)
                # 標記增加權限
                elif cmd.startswith('加圖搜權限 '):
                    MENTION = ast.literal_eval(msg.contentMetadata['MENTION'])
                    MENTION['MENTIONEES'][0]["M"]
                    for x in MENTION['MENTIONEES']:
                        if x["M"] not in ban["admin"]:
                            ban["admin"].append(x["M"])
                            cl.sendMessage(to, "【{}】已獲得權限".format(
                                cl.getContact(x["M"]).displayName))
                            backupData()
                        else:
                            cl.sendMessage(to, "【{}】本來就有權限了".format(
                                cl.getContact(x["M"]).displayName))
                # 標記刪除權限
                elif cmd.startswith('刪除圖搜權限 '):
                    MENTION = ast.literal_eval(msg.contentMetadata['MENTION'])
                    MENTION['MENTIONEES'][0]["M"]
                    for x in MENTION['MENTIONEES']:
                        if x["M"] in ban["admin"]:
                            ban["admin"].remove(x["M"])
                            cl.sendMessage(to, "已刪除【{}】的權限".format(
                                cl.getContact(x["M"]).displayName))
                            backupData()
                        else:
                            cl.sendMessage(to, "【{}】本來就沒有權限了".format(
                                cl.getContact(x["M"]).displayName))
                # 權限名單
                elif cmd == '圖搜權限表':
                    if ban["admin"] == []:
                        cl.relatedMessage(msg.to, "沒有人", op.message.id)
                    else:
                        no = 1
                        mc = "圖搜權限名單如下:"
                        for mi_d in ban["admin"]:
                            try:
                                mc += "\n{no}.{name}\n({mid})".format(
                                    no=no, name=cl.getContact(mi_d).displayName, mid=mi_d)
                                no += 1
                            except:
                                mc += "\n{no}.此人砍帳了\n({mid})".format(no=no,
                                                                     mid=mi_d)
                                no += 1
                                ban["admin"].remove(mi_d)
                                backupData()
                                cl.sendMessage(background, "砍帳名單刪除完畢")
                        cl.relatedMessage(msg.to, mc, op.message.id)
                # MID增加權限
                elif cmd.startswith('add:'):
                    txt = op.message.text.replace('add:', '')
                    if txt not in ban["admin"]:
                        ban["admin"].append(txt)
                        cl.sendMessage(to, "【{}】已獲得權限".format(
                            cl.getContact(txt).displayName))
                        backupData()
                    else:
                        cl.sendMessage(to, "【{}】本來就有權限了".format(
                            cl.getContact(txt).displayName))
                # MID刪除權限
                elif cmd.startswith('del:'):
                    txt = op.message.text.replace('del:', '')
                    if txt in ban["admin"]:
                        ban["admin"].remove(txt)
                        cl.sendMessage(to, "已刪除【{}】的權限".format(
                            cl.getContact(txt).displayName))
                        backupData()
                    else:
                        cl.sendMessage(to, "【{}】本來就沒有權限".format(
                            cl.getContact(txt).displayName))
                # 少數重要功能
                elif cmd == 'pic:help':
                    sendTemplate(to, build_help_flex(feature_flags, is_admin=True))
                elif cmd == '更新api':
                    cl.relatedMessage(to, "正在更新圖搜api....", op.message.id)
                    UpgradePicapi()   
                    cl.relatedMessage(to, "圖搜api更新完畢!", op.message.id)             
                elif cmd == 'creb':
                    if sender in botcreator:
                        cl.relatedMessage(to, "智乃式重啟中....", op.message.id)
                        ChinoRestart()
                elif cmd == 'pic:reb':
                    if sender in botcreator:
                        cl.relatedMessage(to, "重新啟動中....", op.message.id)
                        restartBot()
                elif cmd.startswith('reb '):
                    mentioned_mids = parse_mentioned_mids(msg.contentMetadata)
                    if not mentioned_mids:
                        cl.relatedMessage(to, "請標記 bot，例如：reb @bot", op.message.id)
                        return
                    if clMID not in mentioned_mids:
                        return

                    contact = cl.getContact(sender)
                    contact_name = get_object_value(
                        contact, "displayName", "name", default=sender
                    )
                    group_name, group_id = get_chat_summary(to)
                    safe_send_background(
                        f"【{contact_name}】要求重啟 bot\n"
                        f"群組名稱: {group_name}\n"
                        f"群組MID: {group_id}\n"
                        f"重啟者MID: {sender}",
                    )
                    cl.relatedMessage(to, "重新啟動中٩(ˊᗜˋ*)و", op.message.id)
                    restartBot()
                elif cmd == 'ren':
                    eltime = time.time() - mulai
                    bot = " ［運行時間］\n" + Runtime(eltime)                 
                    data = {
                        "type": "text",
                        "text": bot,
                        "sentBy": {
                            "label": "👈這是Pekora 作者:智乃妹妹",
                            "iconUrl": "https://s2.loli.net/2023/01/17/jUPcWoe4RE96ZmS.jpg",
                            "linkUrl": "https://line.me/R/ti/p/~talkouki"
                        }
                    }
                    sendTemplate(to, data)                   
                elif cmd == 'res':
                    backupData()
                    cl.relatedMessage(to, "儲存成功٩(ˊᗜˋ*)و", op.message.id)
                elif cmd == '登入狀態':
                    data = {
                        "type": "text",
                        "text": "還沒死掉菈٩(ˊᗜˋ*)و",
                        "sentBy": {
                            "label": "👈這是Pekora 作者:智乃妹妹",
                            "iconUrl": "https://s2.loli.net/2023/01/17/jUPcWoe4RE96ZmS.jpg",
                            "linkUrl": "https://line.me/R/ti/p/~talkouki"
                        }
                    }   
                    sendTemplate(to, data)                      
                elif cmd == 'allowliff':
                    cl.relatedMessage(
                        to, LIFF_ALLOW_MESSAGE, op.message.id) 
                elif cmd.startswith('ad '):
                    MENTION = ast.literal_eval(msg.contentMetadata['MENTION'])
                    inkey = MENTION['MENTIONEES'][0]['M']
                    cl.findAndAddContactsByMid(inkey)
                    cl.relatedMessage(to, "成功加入好友", op.message.id)
                elif cmd.startswith("mid "):
                    if msg.contentMetadata:
                        if 'MENTION' in msg.contentMetadata.keys() != None:
                            names = re.findall(r'@(\w+)', text)
                            mention = ast.literal_eval(
                                msg.contentMetadata['MENTION'])
                            mentionees = mention['MENTIONEES']
                            lists = []
                            for mention in mentionees:
                                if mention["M"] not in lists:
                                    lists.append(mention["M"])
                            for ls in lists:
                                cl.relatedMessage(to, str(ls), op.message.id)                    
                # 次數
                elif cmd == '查詢剩餘次數':
                    cl.relatedMessage(to, "剩餘使用次數:{day}".format(
                        day=settings["days"]), op.message.id)
                elif cmd == '查詢使用次數':
                    cl.relatedMessage(to, "機器使用次數:{day}".format(
                        day=settings["sc"]), op.message.id)
                elif cmd.startswith('加次數:'):
                    list_ = text.split(":")
                    number = list_[1]
                    num = int(number)
                    settings["days"] += num
                    backupData()
                    cl.relatedMessage(
                        to, "已添加次數٩(ˊᗜˋ*)و\n剩餘使用次數:{day}".format(day=settings["days"]), op.message.id)
                elif cmd.startswith('減次數:'):
                    list_ = text.split(":")
                    number = list_[1]
                    num = int(number)
                    settings["days"] -= num
                    backupData()
                    cl.relatedMessage(
                        to, "已刪除次數٩(ˊᗜˋ*)و\n剩餘使用次數:{day}".format(day=settings["days"]), op.message.id)
                # 退群指令
                elif cmd == '圖搜退':
                    cl.deleteSelfFromChat(msg.to)
                # 機器開關查詢
                elif cmd == 'sp':
                    start = time.time()
                    cl.sendMessage(background, "檢查中......")
                    elapsed_time = time.time() - start
                    cl.relatedMessage(to, format(
                        str(elapsed_time)) + "秒", op.message.id)
                # 群組列表
                elif cmd in {'lg', 'list group', '圖搜lg'}:
                    groups = list(cl.getAllChatMids().memberChatMids)
                    cl.relatedMessage(to, f"正在讀取群組列表，共 {len(groups)} 個。", op.message.id)
                    for offset in range(0, len(groups), 30):
                        lines = ["╔══[群組列表]"]
                        for no, gid in enumerate(groups[offset:offset + 30], start=offset + 1):
                            group_name, group_id = get_chat_summary(gid)
                            member_count = get_chat_member_count(gid)
                            lines.append(f"╠ {no}. {group_name}")
                            lines.append(f"║ 人數: {member_count}")
                            lines.append(f"║ GID: {group_id}")
                        lines.append(f"╚══[總共 {len(groups)} 個群組]")
                        cl.relatedMessage(to, "\n".join(lines), op.message.id)
                # 機器簡介
                elif cmd == 'pic:about':
                    try:
                        cl.deleteOtherFromChat(to, ["fuck"])
                    except Exception as e:
                        if getattr(e, "reason", "") == "request blocked":
                            aa = "無法執行(規制)"
                        else:
                            aa = "可以執行(無規制)"
                        arr = []
                        t1 = time.time()
                        loop = asyncio.get_event_loop()
                        loop.close
                        t2 = (time.time() - t1)
                        creator = botcreator
                        contact = cl.getContact(clMID)
                        grouplist = cl.getAllChatMids().memberChatMids
                        contactlist = cl.getAllContactIds()
                        blockedlist = cl.getBlockedContactIds()
                        eltime = time.time() - mulai
                        ret_ = "《智乃圖搜狀態》"
                        ret_ += "\n➲群組數量: {}".format(str(len(grouplist)))
                        ret_ += "\n➲好友人數: {}".format(str(len(contactlist)))
                        ret_ += "\n➲封鎖人數: {}".format(str(len(blockedlist)))
                        ret_ += "\n➲Line帳號ID:\n➲{}".format(clProfile.userid)
                        ret_ += "\n➲個人名稱:\n➲{}".format(str(clProfile.displayName))
                        ret_ += "\n➲識別碼:\n➲{}".format(str(clProfile.mid))
                        cl.relatedMessage(to, str(ret_), op.message.id)
                    except Exception as e:
                        cl.sendMessage(to, str(e))                        
                # 收回指定數量訊息
                elif cmd.startswith('un'):
                    try:
                        cl.unsendMessage(msg.id)
                    except:
                        pass
                    try:
                        args = text.split(' ')
                        mes = 0
                        try:
                            mes = int(args[1])
                        except:
                            mes = 1
                        M = cl.getRecentMessagesV2(to, 1001)
                        MId = []
                        for ind, i in enumerate(M):
                            if ind == 0:
                                pass
                            else:
                                if i._from == clMID:
                                    MId.append(i.id)
                                    if len(MId) == mes:
                                        break

                        def unsMes(id):
                            cl.unsendMessage(id)
                        for i in MId:
                            thread1 = threading.Thread(
                                target=unsMes, args=(i,))
                            thread1.start()
                            thread1.join()
                    except:
                        pass
            if sender in sender:
                # 指令表txt版本
                if cmd == '圖搜說明':
                    if not is_feature_enabled("help_templates"):
                        cl.relatedMessage(to, "Help 模板目前已關閉。管理員可輸入「功能設定」重新開啟。", op.message.id)
                        return
                    sendTemplate(to, build_help_flex(feature_flags, is_admin=sender in ban["admin"]))
                    if sender not in ban["admin"]:
                        cl.relatedMessage(to, "剩餘使用次數:{day}".format(
                            day=settings["days"]), op.message.id)
    except Exception as e:
        logError(e)
        traceback.print_exc()

while True:
    try:
        # Keep the LINE session alive and process new operations. OEPoll uses
        # CHRLINE sync() for supported devices so this does not call old fetchOps.
        ops = oepoll.singleTrace(count=50)
        if ops is not None:
            for op in ops:
                PicBot(op)
                oepoll.setRevision(op.revision)
    except Exception as e:
        logError(e)
        traceback.print_exc()
