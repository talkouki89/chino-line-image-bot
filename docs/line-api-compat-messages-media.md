# 訊息、LIFF 與媒體傳送

本頁整理文字訊息、回覆訊息、LIFF、聯絡人卡片與媒體傳送 API。

## 文字訊息

### `sendMessage(to, text, contentMetadata=None, contentType=0, relatedMessageId=None)`

傳送文字或指定內容類型訊息。

```python
cl.sendMessage(group_mid, "hello")
```

帶入 `relatedMessageId` 時，LINE 會把訊息關聯到原訊息。

```python
cl.sendMessage(
    to=msg.to,
    text="收到",
    relatedMessageId=msg.id,
)
```

### `relatedMessage(to, text, relatedMessageId=None, contentMetadata=None)`

舊寫法相容，等同呼叫 `sendMessage(..., contentType=0, relatedMessageId=...)`。

```python
cl.relatedMessage(msg.to, "這是關聯訊息", msg.id)
```

### `sendReplyMessage(relatedMessageId, to, text, contentMetadata=None, contentType=0)`

常用回覆方法。參數順序符合本專案既有插件寫法。

```python
cl.sendReplyMessage(msg.id, msg.to, "pong")
```

在插件中通常建議使用 `ctx.reply("文字")`；需要直接操作 LINE API 時再用 `sendReplyMessage()`。

## LIFF

### `sendLiff(to, messages, liffId="2009929108-vOiudUbo")`

用指定 LIFF ID 發送 Flex Message 或其他 LIFF 支援的 message payload。

```python
flex = {
    "type": "flex",
    "altText": "功能選單",
    "contents": {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Hello"}
            ],
        },
    },
}

cl.sendLiff(group_mid, [flex])
```

預設 LIFF ID 是本專案目前使用的 `2009929108-vOiudUbo`。如果你 fork 後有自己的 LIFF，可以自行傳入：

```python
cl.sendLiff(group_mid, [flex], liffId="your-liff-id")
```

## 聯絡人與撤回

### `sendContact(to, mid, displayName=None)`

傳送聯絡人卡片。

```python
cl.sendContact(group_mid, user_mid)
cl.sendContact(group_mid, user_mid, displayName="User")
```

### `unsendMessage(messageId)`

撤回指定訊息。

```python
cl.unsendMessage(message_id)
```

## 本機媒體傳送

### `sendImage(to, path)`

傳送本機圖片檔案。

```python
cl.sendImage(group_mid, r"C:\temp\image.jpg")
```

### `sendReplyImage(relatedMessageId, to, path)`

圖片回覆 API。傳入要回覆的訊息 ID、聊天室 MID 與本機圖片路徑，會用圖片訊息回覆指定訊息。

```python
cl.sendReplyImage(msg.id, msg.to, r"C:\temp\reply.png")
```

在 plugin 裡通常可以直接使用目前事件的內容：

```python
def handle(ctx):
    if ctx.cmd == "圖片回覆":
        ctx.cl.sendReplyImage(ctx.msg_id, ctx.to, r"C:\temp\reply.png")
        return True
    return False
```

這個方法適合之後需要「用圖片回覆某則訊息」的功能，例如產生圖片、下載圖片後再回覆原指令。

### `sendVideo(to, path)`

傳送本機影片檔案。

```python
cl.sendVideo(group_mid, r"C:\temp\video.mp4")
```

## URL 媒體傳送

相容層提供從 URL 下載到暫存檔再傳送的便利方法。下載完成或傳送失敗後會嘗試清理暫存檔。

### `sendImageWithURL(to, url)`

```python
cl.sendImageWithURL(group_mid, "https://example.com/image.jpg")
```

### `sendVideoWithURL(to, url)`

```python
cl.sendVideoWithURL(group_mid, "https://example.com/video.mp4")
```

### `sendAudioWithURL(to, url)`

```python
cl.sendAudioWithURL(group_mid, "https://example.com/audio.m4a")
```

## 注意事項

- URL 媒體方法會使用 `requests.get(..., timeout=120)`。
- 如果 URL 沒有副檔名，會依媒體類型補上預設副檔名：圖片 `.jpg`、影片 `.mp4`、音訊 `.m4a`。
- URL 媒體方法適合插件快速使用；若要大量下載或需要進度控制，建議自己處理下載流程後再呼叫 `sendImage()` 或 `sendVideo()`。
