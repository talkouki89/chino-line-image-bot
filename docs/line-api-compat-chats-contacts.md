# 好友、群組與聊天室

本頁整理聯絡人、好友、群組與聊天室相關 API。

## 聯絡人

### `getContact(mid)`

取得單一聯絡人資料。

```python
contact = cl.getContact(user_mid)
print(contact.displayName)
```

常用欄位：

| 欄位 | 說明 |
| --- | --- |
| `mid` | 使用者 MID。 |
| `displayName` | 顯示名稱。 |
| `pictureStatus` | 頭像狀態。 |
| `statusMessage` | 狀態訊息。 |

### `getContacts(mids)`

批次取得聯絡人。

```python
contacts = cl.getContacts([mid1, mid2])
for contact in contacts:
    print(contact.displayName)
```

### `getAllContactIds(...)`

直接轉呼叫 CHRLINE-Patch，取得好友 MID 清單。

```python
friend_mids = cl.getAllContactIds()
```

### `getBlockedContactIds(...)`

直接轉呼叫 CHRLINE-Patch，取得封鎖名單 MID。

```python
blocked = cl.getBlockedContactIds()
```

## 加好友

### `addFriendByMid(mid, reference=..., trackingMetaType=5, trackingMetaHint=None)`

使用 CHRLINE-Patch 的 `addFriendByMid` 加好友。

```python
cl.addFriendByMid(user_mid)
```

可自訂來源 reference：

```python
cl.addFriendByMid(
    user_mid,
    reference='{"spec":"native","screen":"talkroom:message"}',
)
```

### `findAndAddContactsByMid(mid, reference=...)`

保留舊 linepy 命名。如果底層 CHRLINE-Patch 有 `addFriendByMid`，會優先轉呼叫 `addFriendByMid()`；否則才呼叫底層 `findAndAddContactsByMid()`。

```python
cl.findAndAddContactsByMid(user_mid)
```

新程式建議直接使用 `addFriendByMid()`。

## 群組與聊天室

### `getGroup(mid)`

取得群組資料。

```python
group = cl.getGroup(group_mid)
print(group.name)
```

常用欄位：

| 欄位 | 說明 |
| --- | --- |
| `id` | 群組 MID。 |
| `name` | 群組名稱。 |
| `members` | 成員清單或 MID 清單。 |
| `creator` | 建立者。 |
| `invitee` | 邀請中成員。 |

### `getGroups(mids)`

批次取得群組。

```python
groups = cl.getGroups([gid1, gid2])
```

### `getChats(chat_mids, *args, **kwargs)`

取得聊天室資料，支援單一 MID 或 MID 清單。

```python
chat = cl.getChats(group_mid)
print(chat.chatName)

chats = cl.getChats([group_mid, room_mid])
for chat in chats:
    print(chat.id, chat.name)
```

若傳入單一字串，回傳單一 `Chat`；若傳入清單，回傳 `Chat` 清單。相容層會把 CHRLINE-Patch 不同形狀的 `getChats` 回應整理成一致格式。

### `getChatV2(chat_mid)`

舊名稱相容，實際上呼叫 `getChats(chat_mid)`。

```python
chat = cl.getChatV2(group_mid)
```

### `getAllChatMids(...)`

取得聊天室 MID 資訊，回傳 `GetAllChatMidsResponse` 類型的 `AttrProxy`。

```python
response = cl.getAllChatMids()
print(response.memberChatMids)
print(response.invitedChatMids)
```

### `getGroupIdsJoined()`

取得已加入群組 ID。

```python
group_ids = cl.getGroupIdsJoined()
```

## 群組操作

### `acceptChatInvitation(to)`

接受聊天室或群組邀請。

```python
cl.acceptChatInvitation(group_mid)
```

### `deleteSelfFromChat(to)`

讓 Bot 離開聊天室或群組。

```python
cl.deleteSelfFromChat(group_mid)
```

### `deleteOtherFromChat(to, mid)`

從聊天室或群組移除指定成員。

```python
cl.deleteOtherFromChat(group_mid, user_mid)
```

## 公告

### `getChatRoomAnnouncements(chatRoomMid)`

取得聊天室公告。

```python
announcements = cl.getChatRoomAnnouncements(group_mid)
for item in announcements:
    print(item.contents.text)
```

回傳項目會被包成 `ChatRoomAnnouncement`，其中 `contents` 可讀取 `text`、`link`、`thumbnail`、`contentMetadata`。
