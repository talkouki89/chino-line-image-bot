from typing import TYPE_CHECKING, List, Literal, Optional

from ..base import BaseBIZApi
from .internal.define_typed.Album import TAlbumPhoto

if TYPE_CHECKING:
    from ...client import CHRLINE

T_ORDER_BY = Literal["createTimeDesc", "updateTimeDesc"]
T_FILTER_TYPE = Literal["specificUser"]
T_VIEW_TYPE = Literal["chatMenu", "selectAlbum"]
T_LIKE_TYPE = Literal["1001", "1002", "1003", "1004", "1005", "1006"]
T_REFERRER_TYPE = Literal["MOA", "NOTI_LIKE", "NONE"]

V_NEW_VERSION = None


class Album(BaseBIZApi):
    def __init__(self, client: "CHRLINE", version: int):
        super().__init__(client, version=version, prefix="/ext/album")

    @property
    def token(self):
        return self.client.biz.token_with_timeline

    @property
    def headers(self):
        return self.client.server.additionalHeaders(
            self.client.biz.headers_with_timeline,
            {"X-Line-ChannelToken": self.client.biz.token_with_album},
        )

    def ext_headers(
        self,
        *,
        chatId: Optional[str] = None,
        referrerType: Optional[T_REFERRER_TYPE] = None,
    ):
        hr = {}
        if chatId is not None:
            hr["x-line-chat-id"] = chatId

            # TODO: auto repair referrerType to MOA?

        if referrerType is not None:
            hr["x-line-album-referrer"] = referrerType
        return self.client.server.additionalHeaders(self.headers, hr)

    def url(self, path: str, *, version: Optional[int] = None, prefix: str = "albums"):
        if version is not None:
            return super().url_with_prefix(f"/api/v{version}/{prefix}" + path)
        return super().url(f"/{prefix}" + path)

    def url_with_moa(self, path: str):
        return super().url_with_prefix("/moa/v2" + path)

    def get_hidden_chats(self):
        r = self.request(
            "GET", self.url_with_moa("/users/hiddenChats"), headers=self.headers
        )
        return r.json()

    def hide_chat(self, chatId: str):
        data = {"chatId": chatId}
        r = self.request(
            "POST",
            self.url_with_moa("/users/hiddenChats/create"),
            headers=self.headers,
            json=data,
        )
        return r.json()

    def delete_hidden_chat(self, chatId: str):
        data = {"chatId": chatId}
        r = self.request(
            "POST",
            self.url_with_moa("/users/hiddenChats/delete"),
            headers=self.headers,
            json=data,
        )
        return r.json()

    def get_moa_albums(
        self,
        *,
        cursor: str,
        orderBy: T_ORDER_BY,
        include: str,
    ):
        params = {"cursor": cursor, "orderBy": orderBy, "include": include}
        r = self.request(
            "GET",
            self.url_with_moa("/albums"),
            headers=self.headers,
            params=params,
        )
        return r.json()

    def get_moa_photos(
        self,
        *,
        cursor: str,
        include: str,
    ):
        params = {"cursor": cursor, "include": include}
        r = self.request(
            "GET",
            self.url_with_moa("/photos"),
            headers=self.headers,
            params=params,
        )
        return r.json()

    def get_album(self, chatId: str, *, albumId: int, syncRevision: int):
        params = {"syncRevision": syncRevision}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "GET",
            self.url(f"/{albumId}"),
            headers=hr,
            params=params,
        )
        return r.json()

    def share_to_chat(self, chatId: str, *, albumId: int):
        # method: POST
        hr = self.ext_headers(chatId=chatId)
        r = self.request("POST", self.url(f"/{albumId}/share"), headers=hr)
        return r.json()

    def get_album_photos(
        self,
        chatId: str,
        *,
        albumId: int,
        cursor: str,
        pageSize: int,
        orderBy: T_ORDER_BY,
        include: str,
        filterType: str,
        targetUserMid: Optional[str] = None,
    ):
        # version: v6
        params = {
            "cursor": cursor,
            "pageSize": pageSize,
            "orderBy": orderBy,
            "include": include,
            "filterType": filterType,
            "targetUser": targetUserMid,
        }
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "GET", self.url(f"/{albumId}/photos"), headers=hr, params=params
        )
        return r.json()

    def fetch_albums(self, chatId: str, *, syncRevision: str, markReading: bool):
        # version: v5
        # path: /albums
        params = {"syncRevision": syncRevision, "markReading": markReading}
        hr = self.ext_headers(chatId=chatId)
        r = self.request("GET", self.url(""), headers=hr, params=params)
        return r.json()

    def fetch_albums_v6(self, chatId: str, *, cursor: str, pageSize: int):
        # version: v6
        # path: /albums
        params = {"cursor": cursor, "pageSize": pageSize}
        hr = self.ext_headers(chatId=chatId)
        r = self.request("GET", self.url("", version=6), headers=hr, params=params)
        return r.json()

    def get_preview_albums(
        self,
        chatId: str,
        *,
        cursor: str,
        pageSize: int,
        viewType: T_VIEW_TYPE,
        thumbnailCount: int = 1,
    ):
        # version: v6
        # path: /albums
        params = {
            "cursor": cursor,
            "pageSize": pageSize,
            "thumbnailCount": thumbnailCount,
            "viewType": viewType,
        }
        hr = self.ext_headers(chatId=chatId)
        r = self.request("GET", self.url("/preview"), headers=hr, params=params)
        return r.json()

    def get_album_promotion_item(
        self,
        *,
        country: str,
        language: int,
        isPremium: bool,
        os: str = "Android",
    ):
        params = {
            "country": country,
            "language": language,
            "isPremium": isPremium,
            "os": os,
        }
        r = self.request(
            "GET",
            self.url_with_prefix("/support/v1/promotion"),
            headers=self.headers,
            params=params,
        )
        return r.json()

    def agree_terms(self, *, version: int):
        data = {"version": version}
        r = self.request(
            "POST",
            self.url("/lypPremium/terms/agree", prefix="user"),
            headers=self.headers,
            json=data,
        )
        return r.json()

    def get_agreement_status(self):
        r = self.request(
            "GET",
            self.url("/lypPremium/latestTerms", prefix="user"),
            headers=self.headers,
        )
        return r.json()

    def get_album_id(self, chatId: str, *, legacyAlbumId: int):
        params = {"legacyAlbumId": legacyAlbumId}
        hr = self.ext_headers(chatId=chatId)
        r = self.request("GET", self.url("/id"), headers=hr, params=params)
        return r.json()

    def add_photos(self, chatId: str, *, albumId: int, photos: List[TAlbumPhoto]):
        data = {"photos": photos}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "POST", self.url(f"/{albumId}/photos/create"), headers=hr, json=data
        )
        return r.json()

    def create_album(self, chatId: str, *, title: str, modifyDuplicateTitle: bool):
        params = {"modifyDuplicateTitle": modifyDuplicateTitle}
        data = {"title": title}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "POST", self.url("/create"), headers=hr, params=params, json=data
        )
        return r.json()

    def delete_album(self, chatId: str, *, albumId: int):
        # method: POST
        hr = self.ext_headers(chatId=chatId)
        r = self.request("POST", self.url(f"/{albumId}/delete"), headers=hr)
        return r.json()

    def delete_photos(self, chatId: str, *, albumId: int, photoIds: List[int]):
        data = {"photoIds": photoIds}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "POST", self.url(f"/{albumId}/photos/delete"), headers=hr, json=data
        )
        return r.json()

    def update_album(self, chatId: str, *, albumId: int, title: str):
        data = {"title": title}
        hr = self.ext_headers(chatId=chatId)
        r = self.request("POST", self.url(f"/{albumId}/update"), headers=hr, json=data)
        return r.json()

    def get_photo_download_info(
        self,
        chatId: str,
        *,
        albumId: int,
        orderBy: T_ORDER_BY,
        filterType: T_FILTER_TYPE,
        targetUserMid: Optional[str],
    ):
        params = {
            "orderBy": orderBy,
            "filterType": filterType,
            "targetUser": targetUserMid,
        }
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "GET",
            self.url(f"/{albumId}/photos/obsDownloadInfo"),
            headers=hr,
            params=params,
        )
        return r.json()

    def get_photo_likes(
        self, chatId: str, *, albumId: int, photoId: int, cursor: str, pageSize: int
    ):
        params = {"cursor": cursor, "pageSize": pageSize}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "GET",
            self.url(f"/{albumId}/photos/{photoId}/likes"),
            headers=hr,
            params=params,
        )
        return r.json()

    def get_photo_likes_preview(
        self, chatId: str, *, albumId: int, photoId: int, cursor: str, pageSize: int
    ):
        params = {}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "GET",
            self.url(f"/{albumId}/photos/{photoId}/likes/preview"),
            headers=hr,
            params=params,
        )
        return r.json()

    def delete_photo_like(self, chatId: str, *, albumId: int, photoId: int):
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "POST", self.url(f"/{albumId}/photos/{photoId}/likes/delete"), headers=hr
        )
        return r.json()

    def create_photo_like(
        self, chatId: str, *, albumId: int, photoId: int, likeType: T_LIKE_TYPE
    ):
        data = {"likeType": likeType}
        hr = self.ext_headers(chatId=chatId)
        r = self.request(
            "POST",
            self.url(f"/{albumId}/photos/{photoId}/likes/create"),
            headers=hr,
            json=data,
        )
        return r.json()
