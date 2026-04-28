# 資料結構與 AttrProxy

`AttrProxy` 是 `line_api_compat.py` 裡讓 CHRLINE-Patch 回傳值更接近 linepy 用法的資料包裝器。它讓 `dict`、`list` 或 Thrift 風格資料可以用屬性存取。

## 為什麼需要 AttrProxy

CHRLINE-Patch 的回傳資料可能長這樣：

```python
{"text": "hello", "to": "c...", 4: "message-id"}
```

Bot 舊程式通常想這樣寫：

```python
msg.text
msg.to
msg.id
```

`AttrProxy` 會透過欄位別名表，把 `id` 對應到 Message 的 field id `4`，讓舊寫法可繼續使用。

## 基本行為

```python
msg = op.message
print(msg.text)
print(msg["text"])
```

支援：

| 行為 | 說明 |
| --- | --- |
| `obj.name` | 用屬性讀取欄位。 |
| `obj["name"]` | 用原始 key 讀取欄位。 |
| `name in obj` | 檢查原始資料是否有 key。 |
| `len(obj)` | 回傳底層資料長度。 |
| `repr(obj)` | 顯示底層資料。 |

## 目前支援的資料類型

| 類型 | 常用欄位 |
| --- | --- |
| `Operation` | `revision`、`type`、`param1`、`param2`、`param3`、`message` |
| `Message` | `_from`、`to`、`id`、`text`、`contentType`、`contentMetadata`、`relatedMessageId` |
| `Profile` | `mid`、`userid`、`displayName`、`pictureStatus`、`statusMessage` |
| `Contact` | `mid`、`displayName`、`pictureStatus`、`statusMessage` |
| `Chat` | `id`、`chatMid`、`chatName`、`name`、`picturePath`、`extra`、`members` |
| `Group` | `id`、`name`、`members`、`creator`、`invitee` |
| `GroupExtra` | `creator`、`memberMids`、`inviteeMids`、`ticketDisabled` |
| `ChatRoomAnnouncement` | `announcementSeq`、`type`、`contents`、`creatorMid` |
| `ChatRoomAnnouncementContents` | `text`、`link`、`thumbnail`、`contentMetadata` |

## 巢狀資料

當讀取到 `message`、`profile`、`contact`、`group`、`chat`、`extra`、`groupExtra`、`contents` 等欄位時，相容層會嘗試推斷類型並繼續包成 `AttrProxy`。

```python
msg = op.message
print(msg.text)

announcement = cl.getChatRoomAnnouncements(chat_mid)[0]
print(announcement.contents.text)
```

## 寫入欄位

`AttrProxy` 支援簡單寫入。若底層是 dict，會寫入原 key 或 field id；若底層是 list，會依 field id 擴充清單後寫入。

```python
profile = cl.getProfile()
profile.displayName = "New Name"
cl.updateProfile(profile)
```

## Chat.members 特例

部分 `Chat` 回應不會直接提供 `members`，但會在 `extra.groupExtra.memberMids` 裡提供成員 MID。當 `chat.members` 不存在時，相容層會嘗試從這個位置組出成員清單。

```python
chat = cl.getChats(group_mid)
for mid in chat.members:
    print(mid)
```

## 直接取原始資料

如果需要 debug，可讀取內部 `_data`。

```python
raw = msg._data
print(raw)
```

一般插件不建議依賴 `_data` 的形狀，因為 CHRLINE-Patch 回傳格式可能會因 API 更新而變動。
