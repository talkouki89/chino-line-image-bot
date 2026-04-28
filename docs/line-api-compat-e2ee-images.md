# 圖片下載與 E2EE 圖片

本頁整理 `downloadReplyImage()`、`downloadObjectMsg()` 與私訊 E2EE 圖片處理方式。

## `downloadReplyImage(chatId, messageId, returnAs="path", saveAs="", objFrom=None)`

下載使用者回覆的圖片。這是本專案圖搜與圖片上傳插件建議使用的方法。

```python
path = cl.downloadReplyImage(
    chatId=msg.to,
    messageId=reply_message_id,
    returnAs="path",
    saveAs="reply.jpg",
)
```

若要取得 bytes：

```python
data = cl.downloadReplyImage(
    chatId=msg.to,
    messageId=reply_message_id,
    returnAs="bytes",
)
```

處理流程：

1. 用 `getRecentMessagesV2(chatId, 1000)` 找出原訊息。
2. 如果原訊息是 E2EE 圖片，使用 CHRLINE-Patch 的 E2EE 解密流程下載原圖。
3. 如果不是 E2EE 圖片，退回 `downloadObjectMsg()`。

## 參數

| 參數 | 說明 |
| --- | --- |
| `chatId` | 聊天室 MID，通常是 `msg.to`。 |
| `messageId` | 要下載的圖片訊息 ID。 |
| `returnAs` | `"path"` 回傳檔案路徑；其他值會回傳 bytes。 |
| `saveAs` | 指定儲存路徑。未指定時交給底層下載流程。 |
| `objFrom` | 傳給 `downloadObjectMsg()` 的來源，未指定時使用 `chatId`。 |

## E2EE 判斷條件

目前相容層會用下列條件判斷是否走 E2EE 圖片流程：

```python
contentType == 1
chunks 存在
contentMetadata 內有 OID
```

符合時會呼叫：

```python
self._client.decryptE2EEMessage(...)
self._client.downloadObjectForService(...)
self._client.decryptByKeyMaterial(...)
```

## `downloadObjectMsg(messageId, returnAs="path", saveAs="", objFrom="c")`

一般 LINE object 下載方法。

```python
path = cl.downloadObjectMsg(message_id, returnAs="path", saveAs="image.jpg", objFrom=chat_mid)
data = cl.downloadObjectMsg(message_id, returnAs="bytes", objFrom=chat_mid)
```

`returnAs == "path"` 時回傳路徑；其他值回傳底層下載取得的 bytes。

## 插件建議寫法

如果插件要處理「回覆圖片」功能，建議先取出原訊息 ID，再呼叫 `downloadReplyImage()`：

```python
reply_id = msg.contentMetadata.get("REPLACE") or msg.relatedMessageId
image_path = cl.downloadReplyImage(msg.to, reply_id, returnAs="path", saveAs="reply.jpg")
```

實際 reply metadata 名稱可能依 LINE 訊息類型而不同，請以本專案現有插件的取法為準。

## 限制

- E2EE 圖片解密需要 Bot 端具有正確 E2EE key material。
- `downloadReplyImage()` 會從近期訊息搜尋原訊息；如果訊息太舊或不在近期清單內，會退回一般 object 下載。
- 這個流程依賴 CHRLINE-Patch 內部 E2EE API；若 CHRLINE-Patch 更新介面，這裡可能也需要同步調整。
