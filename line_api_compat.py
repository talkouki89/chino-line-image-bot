# -*- coding: utf-8 -*-
"""Compatibility layer from the old linepy API to CHRLINE-Patch.

The bot was written against a linepy style client where thrift
responses expose attributes (`msg.text`, `op.param1`, `group.members`).
CHRLINE-Patch returns thrift data mostly as dict/list containers.  This
module keeps the bot code small while the underlying LINE API is replaced.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import time
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

import requests

from CHRLINE import CHRLINE
from CHRLINE.helpers.bulders.message import Message as WrappedMessage
from CHRLINE.serializers.DummyProtocol import DummyThrift


DEFAULT_LINE_DOMAINS = {
    "LINE_HOST_DOMAIN": "https://ga2.line.naver.jp",
    "LINE_OBS_DOMAIN": "https://obs.line-apps.com",
    "LINE_API_DOMAIN": "https://api.line.me",
    "LINE_ACCESS_DOMAIN": "https://access.line.me",
    "LINE_BIZ_TIMELINE_DOMAIN": "https://ga2.line.naver.jp/mh",
}


FIELD_ALIASES = {
    "Operation": {
        "revision": 1,
        "createdTime": 2,
        "type": 3,
        "reqSeq": 4,
        "checksum": 5,
        "status": 7,
        "param1": 10,
        "param2": 11,
        "param3": 12,
        "message": 20,
    },
    "Message": {
        "_from": 1,
        "to": 2,
        "toType": 3,
        "id": 4,
        "createdTime": 5,
        "deliveredTime": 6,
        "text": 10,
        "location": 11,
        "hasContent": 14,
        "contentType": 15,
        "contentPreview": 17,
        "contentMetadata": 18,
        "sessionId": 19,
        "chunks": 20,
        "relatedMessageId": 21,
    },
    "Profile": {
        "mid": 1,
        "userid": 3,
        "phone": 10,
        "email": 11,
        "regionCode": 12,
        "displayName": 20,
        "pictureStatus": 22,
        "thumbnailUrl": 23,
        "statusMessage": 24,
    },
    "Settings": {
        "privacySearchByUserid": 13,
        "privacySearchByPhoneNumber": 7,
        "privacySearchByEmail": 14,
        "privacyAllowSecondaryDeviceLogin": 21,
        "preferenceLocale": 15,
        "privacyReceiveMessagesFromNotFriend": 25,
        "e2eeEnable": 33,
    },
    "Contact": {
        "mid": 1,
        "type": 10,
        "status": 11,
        "relation": 21,
        "displayName": 22,
        "pictureStatus": 24,
        "thumbnailUrl": 25,
        "statusMessage": 26,
    },
    "Chat": {
        "type": 1,
        "chatMid": 2,
        "id": 2,
        "createdTime": 3,
        "notificationDisabled": 4,
        "favoriteTimestamp": 5,
        "chatName": 6,
        "name": 6,
        "picturePath": 7,
        "extra": 8,
    },
    "Extra": {
        "groupExtra": 1,
        "peerExtra": 2,
    },
    "Group": {
        "id": 1,
        "createdTime": 2,
        "name": 10,
        "pictureStatus": 11,
        "preventedJoinByTicket": 13,
        "members": 20,
        "creator": 21,
        "invitee": 22,
    },
    "GroupExtra": {
        "creator": 1,
        "preventedJoinByTicket": 2,
        "invitationTicket": 3,
        "memberMids": 4,
        "inviteeMids": 5,
        "addFriendDisabled": 6,
        "ticketDisabled": 7,
        "autoName": 8,
    },
    "GetAllChatMidsResponse": {
        "memberChatMids": 1,
        "invitedChatMids": 2,
    },
    "ChatRoomAnnouncement": {
        "announcementSeq": 1,
        "type": 2,
        "contents": 3,
        "creatorMid": 4,
        "createdTime": 5,
        "deletePermission": 6,
    },
    "ChatRoomAnnouncementContents": {
        "displayFields": 1,
        "text": 2,
        "link": 3,
        "thumbnail": 4,
        "contentMetadata": 5,
    },
}


def _install_default_domains() -> None:
    for key, value in DEFAULT_LINE_DOMAINS.items():
        os.environ.setdefault(key, value)


def _get(data: Any, key: str, field_id: Optional[int] = None, default: Any = None) -> Any:
    if data is None:
        return default
    if isinstance(data, AttrProxy):
        data = data._data
    if isinstance(data, dict):
        if key in data:
            return data[key]
        if field_id is not None and field_id in data:
            return data[field_id]
        val_key = f"val_{field_id}" if field_id is not None else None
        if val_key and val_key in data:
            return data[val_key]
        return default
    if isinstance(data, (list, tuple)) and field_id is not None:
        if 0 <= field_id < len(data):
            return data[field_id]
        return default
    for attr in (key, f"val_{field_id}" if field_id is not None else None):
        if not attr:
            continue
        try:
            return getattr(data, attr)
        except AttributeError:
            pass
    try:
        if field_id is not None:
            return data[field_id]
    except Exception:
        pass
    return default


def _wrap(value: Any, kind: Optional[str] = None) -> Any:
    if isinstance(value, AttrProxy):
        if kind is not None and getattr(value, "_kind", None) is None:
            return AttrProxy(value._data, kind)
        return value
    if isinstance(value, dict):
        return AttrProxy(value, kind)
    if isinstance(value, list):
        if kind is not None:
            return AttrProxy(value, kind)
        return [_wrap(v) for v in value]
    if isinstance(value, set):
        return [_wrap(v) for v in value]
    return value


def _is_liff_share_error(result: Any) -> bool:
    if not isinstance(result, str):
        return False
    text = result.lower()
    return "invalid" in text or "unauthorized" in text or "token" in text


class AttrProxy:
    def __init__(self, data: Any, kind: Optional[str] = None):
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_kind", kind)

    def __getitem__(self, key: Any) -> Any:
        return _wrap(self._data[key])

    def __contains__(self, key: Any) -> bool:
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return repr(self._data)

    def __getattr__(self, name: str) -> Any:
        aliases = FIELD_ALIASES.get(self._kind or "", {})
        value = _get(self._data, name, aliases.get(name))
        if value is not None:
            return _wrap(value, _infer_kind(name, value))
        if self._kind == "Chat" and name == "members":
            extra = _wrap(_get(self._data, "extra", FIELD_ALIASES["Chat"]["extra"]), "GroupExtra")
            mids = getattr(extra, "memberMids", []) or []
            return list(mids)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        aliases = FIELD_ALIASES.get(self._kind or "", {})
        field_id = aliases.get(name)
        if isinstance(self._data, dict):
            if name in self._data:
                self._data[name] = value
            elif field_id is not None:
                self._data[field_id] = value
            else:
                self._data[name] = value
            return
        if isinstance(self._data, list) and field_id is not None:
            while len(self._data) <= field_id:
                self._data.append(None)
            self._data[field_id] = value
            return
        object.__setattr__(self, name, value)


def _infer_kind(name: str, value: Any) -> Optional[str]:
    if name == "message":
        return "Message"
    if name in {"profile"}:
        return "Profile"
    if name in {"contact"}:
        return "Contact"
    if name == "group":
        return "Group"
    if name == "chat":
        return "Chat"
    if name == "extra":
        return "Extra"
    if name == "groupExtra":
        return "GroupExtra"
    if name == "contents":
        return "ChatRoomAnnouncementContents"
    return None


def _extract_chats(response: Any) -> list:
    """Normalize CHRLINE getChats responses into a list of Chat objects."""
    if response is None:
        return []
    data = response._data if isinstance(response, AttrProxy) else response
    if isinstance(data, list):
        return data
    if isinstance(data, tuple):
        return list(data)
    if isinstance(data, set):
        return list(data)
    if isinstance(data, dict):
        chats = data.get("chats") or data.get(1) or data.get("val_1")
        if isinstance(chats, dict):
            return list(chats.values())
        if isinstance(chats, (list, tuple, set)):
            return list(chats)
        if chats is not None:
            return [chats]
        return list(data.values())
    chats = _get(data, "chats", 1, None)
    if isinstance(chats, dict):
        return list(chats.values())
    if isinstance(chats, (list, tuple, set)):
        return list(chats)
    if chats is not None:
        return [chats]
    return [data]


class LINE:
    def __init__(self, idOrAuthToken: Optional[str] = None, passwd: Optional[str] = None, **kwargs):
        _install_default_domains()
        device = kwargs.pop("device", os.getenv("CHRLINE_DEVICE", "DESKTOPWIN"))
        version = kwargs.pop("version", os.getenv("CHRLINE_VERSION") or None)
        use_thrift = kwargs.pop("useThrift", True)
        debug = kwargs.pop("debug", os.getenv("CHRLINE_DEBUG", "").lower() == "true")
        self._client = CHRLINE(
            idOrAuthToken,
            passwd,
            device=device,
            version=version,
            useThrift=use_thrift,
            debug=debug,
            **kwargs,
        )
        self.profile = _wrap(self._client.profile, "Profile")

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    @property
    def revision(self) -> int:
        return self._client.revision

    @revision.setter
    def revision(self, value: int) -> None:
        self._client.revision = value

    @property
    def authToken(self) -> str:
        return self._client.authToken

    @property
    def mid(self) -> str:
        return self._client.mid

    def log(self, text: Any, debug: bool = False) -> None:
        self._client.log(text, debug)

    def getProfile(self):
        self.profile = _wrap(self._client.getProfile(), "Profile")
        return self.profile

    def updateProfile(self, profile) -> Any:
        display_name = getattr(profile, "displayName", None)
        status_message = getattr(profile, "statusMessage", None)
        result = None
        if display_name is not None:
            result = self._client.updateProfileAttribute(2, display_name)
        if status_message is not None:
            result = self._client.updateProfileAttribute(16, status_message)
        return result

    def updateProfileAttribute(self, attrId: int, value: str) -> Any:
        return self._client.updateProfileAttribute(attrId, value)

    def getSettings(self, syncReason: int = 2):
        return _wrap(self._client.getSettings(syncReason), "Settings")

    def getContact(self, mid: str):
        return _wrap(self._client.getContact(mid), "Contact")

    def getContacts(self, mids: Iterable[str]):
        return _wrap(self._client.getContacts(list(mids)))

    def getGroup(self, mid: str):
        return _wrap(self._client.getGroup(mid), "Group")

    def getGroups(self, mids: Iterable[str]):
        return [_wrap(item, "Group") for item in self._client.getGroups(list(mids))]

    def getChats(self, chat_mids, *args, **kwargs):
        single = isinstance(chat_mids, str)
        mids = [chat_mids] if single else list(chat_mids)
        response = _wrap(self._client.getChats(mids, *args, **kwargs))
        chats = _extract_chats(response)
        if single:
            return _wrap(chats[0], "Chat") if chats else None
        return [_wrap(chat, "Chat") for chat in chats]

    def getChatV2(self, chat_mid: str):
        return self.getChats(chat_mid)

    def reissueChatTicket(self, groupMid: str):
        return self._client.reissueChatTicket(groupMid)

    def getAllChatMids(self, *args, **kwargs):
        return _wrap(self._client.getAllChatMids(*args, **kwargs), "GetAllChatMidsResponse")

    def getGroupIdsJoined(self):
        return self._client.getGroupIdsJoined()

    def fetchOperation(self, revision: int, count: int = 100):
        return self.fetchOps(revision, count)

    def fetchOps(self, revision: int, count: int = 100):
        fetch = self._client.fetchOps
        if getattr(self._client, "DEVICE_TYPE", None) in getattr(self._client, "SYNC_SUPPORT", []):
            fetch = self._client.sync
        return [_wrap(op, "Operation") for op in fetch(revision, count)]

    def getRecentMessagesV2(self, to: str, count: int = 300):
        return [_wrap(msg, "Message") for msg in self._client.getRecentMessagesV2(to, count)]

    def getChatRoomAnnouncements(self, chatRoomMid: str):
        return [_wrap(item, "ChatRoomAnnouncement") for item in self._client.getChatRoomAnnouncements(chatRoomMid)]

    def setRevision(self, revision: int) -> None:
        self._client.setRevision(revision)

    def acceptChatInvitation(self, to: str) -> Any:
        return self._client.acceptChatInvitation(to)

    def deleteSelfFromChat(self, to: str) -> Any:
        return self._client.deleteSelfFromChat(to)

    def deleteOtherFromChat(self, to: str, mid) -> Any:
        return self._client.deleteOtherFromChat(to, mid)

    def addFriendByMid(
        self,
        mid: str,
        reference: str = '{"spec":"native","screen":"talkroom:message"}',
        trackingMetaType: int = 5,
        trackingMetaHint: Optional[str] = None,
    ) -> Any:
        return self._client.addFriendByMid(
            mid,
            reference=reference,
            trackingMetaType=trackingMetaType,
            trackingMetaHint=trackingMetaHint,
        )

    def findAndAddContactsByMid(self, mid: str, reference: str = '{"screen":"groupMemberList","spec":"native"}') -> Any:
        if hasattr(self._client, "addFriendByMid"):
            return self.addFriendByMid(mid, reference=reference)
        return self._client.findAndAddContactsByMid(mid, reference=reference)

    def getAllContactIds(self, *args, **kwargs):
        return self._client.getAllContactIds(*args, **kwargs)

    def getBlockedContactIds(self, *args, **kwargs):
        return self._client.getBlockedContactIds(*args, **kwargs)

    def sendMessage(self, to, text, contentMetadata=None, contentType=0, relatedMessageId=None):
        return self._client.sendMessage(
            to,
            text,
            contentType=contentType,
            contentMetadata=contentMetadata or {},
            relatedMessageId=relatedMessageId,
        )

    def relatedMessage(self, to, text, relatedMessageId=None, contentMetadata=None):
        return self.sendMessage(to, text, contentMetadata or {}, 0, relatedMessageId)

    def sendReplyMessage(self, relatedMessageId, to, text, contentMetadata=None, contentType=0):
        return self.sendMessage(to, text, contentMetadata or {}, contentType, relatedMessageId)

    def sendReplyImage(self, relatedMessageId: str, to: str, path: str):
        return self._client.uploadObjTalk(
            pathOrBytes=path,
            oType="image",
            to=to,
            talkMeta=self._reply_talk_meta(relatedMessageId, to),
        )

    def _reply_talk_meta(self, relatedMessageId: str, to: str):
        related_service_code = 2 if self._client.getToType(to) == 4 else 1
        params = [
            [11, 21, relatedMessageId],
            [8, 22, 3],
            [8, 24, related_service_code],
        ]
        data = self._client.generateDummyProtocolField(params, 3) + [0]
        message = base64.b64encode(bytes(data)).decode("utf-8")
        return base64.b64encode(json.dumps({"message": message}).encode("utf-8")).decode("utf-8")

    def sendLiff(self, to, messages, liffId="2009929108-vOiudUbo"):
        payload = messages if isinstance(messages, list) else [messages]
        result = self._client.sendLiff(to, payload, liffId=liffId)
        if _is_liff_share_error(result):
            result = self._client.sendLiff(to, payload, forceIssue=True, liffId=liffId)
        return result

    def sendContact(self, to: str, mid: str, displayName: Optional[str] = None):
        return self._client.sendContact(to, mid, displayName=displayName)

    def sendImage(self, to: str, path: str):
        return self._client.sendImage(to, path)

    def sendVideo(self, to: str, path: str):
        return self._client.sendVideo(to, path)

    def uploadMultipleImageToTalk(self, to: str, paths: list[str]):
        return self._client.uploadMultipleImageToTalk(paths, to)

    def unsendMessage(self, messageId: str):
        return self._client.unsendMessage(messageId)

    def downloadReplyImage(self, chatId, messageId, returnAs="path", saveAs="", objFrom=None):
        obj_from = objFrom or chatId
        message = self._find_recent_message(chatId, messageId)
        if message is not None and self._is_e2ee_image_message(message):
            data = self._download_e2ee_image_message(message)
            if saveAs:
                with open(saveAs, "wb") as fp:
                    fp.write(data)
                return saveAs if returnAs == "path" else data
            return data
        return self.downloadObjectMsg(messageId, returnAs=returnAs, saveAs=saveAs, objFrom=obj_from)

    def downloadObjectMsg(self, messageId, returnAs="path", saveAs="", objFrom="c"):
        path = saveAs or None
        data = self._client.downloadObjectMsg(messageId, path=path, objFrom=objFrom)
        if returnAs == "path":
            return saveAs or path
        return data

    def _find_recent_message(self, chatId, messageId, count=1000):
        try:
            for message in self._client.getRecentMessagesV2(chatId, count):
                if str(_get(message, "id", 4, "")) == str(messageId):
                    return message
        except Exception:
            return None
        return None

    def _is_e2ee_image_message(self, message):
        return bool(
            _get(message, "contentType", 15) == 1
            and _get(message, "chunks", 20)
            and (_get(message, "contentMetadata", 18, {}) or {}).get("OID")
        )

    def _download_e2ee_image_message(self, message):
        message = self._ensure_wrapped_message(message)
        metadata = _get(message, "contentMetadata", 18, {}) or {}
        key_material = self._client.decryptE2EEMessage(message, message.from_type == 2)["keyMaterial"]
        encrypted = self._client.downloadObjectForService(
            metadata["OID"],
            None,
            "talk/" + metadata["SID"],
            additionalHeaders={"X-Talk-Meta": self._e2ee_image_meta(_get(message, "id", 4))},
        )
        return self._client.decryptByKeyMaterial(encrypted, key_material)

    def _ensure_wrapped_message(self, message):
        if isinstance(message, WrappedMessage):
            wrapped = message
        else:
            wrapped = WrappedMessage("Message", ins=message, cl=self._client)
        op = DummyThrift("Operation", cl=self._client)
        op[3] = 25 if _get(message, "_from", 1) == self._client.mid else 26
        wrapped.set_ref(op)
        return wrapped

    def _e2ee_image_meta(self, message_id):
        data = [11, 0, 4]
        data += self._client.getStringBytes(str(message_id))
        data += [15, 0, 27, 12, 0, 0, 0, 0, 0]
        message = base64.b64encode(bytes(data)).decode()
        return base64.b64encode(json.dumps({"message": message}).encode()).decode()

    def sendImageWithURL(self, to: str, url: str):
        return self._send_url_media(to, url, "image")

    def sendVideoWithURL(self, to: str, url: str):
        return self._send_url_media(to, url, "video")

    def sendAudioWithURL(self, to: str, url: str):
        return self._send_url_media(to, url, "audio")

    def _send_url_media(self, to: str, url: str, media_type: str):
        suffix = os.path.splitext(urlparse(url).path)[1] or {
            "image": ".jpg",
            "video": ".mp4",
            "audio": ".m4a",
        }.get(media_type, ".bin")
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        try:
            with requests.get(url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                with open(path, "wb") as fp:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fp.write(chunk)
            if media_type == "image":
                return self._client.sendImage(to, path)
            if media_type == "video":
                return self._client.sendVideo(to, path)
            if media_type == "audio":
                return self._client.sendAudio(to, path)
            return self._client.sendFile(to, path)
        finally:
            _safe_remove(path)


def _safe_remove(path: str, retries: int = 20, delay: float = 0.25) -> None:
    for _ in range(retries):
        try:
            os.remove(path)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            time.sleep(delay)


class OEPoll:
    def __init__(self, client: LINE):
        self.client = client

    def setRevision(self, revision: int) -> None:
        self.client.setRevision(revision)

    def singleTrace(self, count: int = 1, fetchOperations=None):
        fetch = fetchOperations or self.client.fetchOperation
        try:
            return fetch(self.client.revision, count=count)
        except TimeoutError:
            return []
        except Exception as exc:
            self.client.log(f"[OEPoll] fetch failed: {exc}")
            return []
