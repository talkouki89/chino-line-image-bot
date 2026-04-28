# line_api_compat 總覽

`line_api_compat.py` 是本專案放在 CHRLINE-Patch 上方的相容層。Bot 原本的寫法偏向舊 linepy 風格，例如 `cl.sendMessage(...)`、`op.message.text`、`msg.contentMetadata`；但 CHRLINE-Patch 回傳的資料常是 `dict`、`list` 或 Thrift 容器。這個檔案負責把常用 API 包成比較容易在 bot 與插件中使用的介面。

## 主要類別

| 類別 | 用途 |
| --- | --- |
| `LINE` | 包裝 CHRLINE-Patch client，提供登入、收訊、傳訊、好友、群組、媒體下載等常用方法。 |
| `OEPoll` | 簡化 operation 輪詢，讓主程式可以用 `singleTrace()` 取新事件。 |
| `AttrProxy` | 把 `dict/list` 資料包成可以用屬性存取的物件，例如 `msg.text`、`group.name`。 |

## 基本使用

```python
from line_api_compat import LINE, OEPoll

cl = LINE("line@example.com", "password")
poll = OEPoll(cl)

profile = cl.getProfile()
print(profile.mid, profile.displayName)

for op in poll.singleTrace(count=10):
    msg = getattr(op, "message", None)
    if msg and getattr(msg, "text", "") == "ping":
        cl.sendReplyMessage(msg.id, msg.to, "pong")
```

## 初始化參數

```python
cl = LINE(
    idOrAuthToken="line@example.com",
    passwd="password",
    device="DESKTOPWIN",
    version=None,
    useThrift=True,
    debug=False,
)
```

| 參數 | 預設 | 說明 |
| --- | --- | --- |
| `idOrAuthToken` | 無 | LINE 帳號或 auth token。 |
| `passwd` | 無 | LINE 密碼。使用 token 時通常可省略。 |
| `device` | `CHRLINE_DEVICE` 或 `DESKTOPWIN` | CHRLINE 裝置類型。 |
| `version` | `CHRLINE_VERSION` 或 `None` | 指定 LINE client version。 |
| `useThrift` | `True` | 是否使用 Thrift。 |
| `debug` | `CHRLINE_DEBUG=true` 時為 `True` | CHRLINE debug log。 |

初始化時會自動補上常用 LINE domain 環境變數：

| 環境變數 | 預設值 |
| --- | --- |
| `LINE_HOST_DOMAIN` | `https://ga2.line.naver.jp` |
| `LINE_OBS_DOMAIN` | `https://obs.line-apps.com` |
| `LINE_API_DOMAIN` | `https://api.line.me` |
| `LINE_ACCESS_DOMAIN` | `https://access.line.me` |
| `LINE_BIZ_TIMELINE_DOMAIN` | `https://ga2.line.naver.jp/mh` |

## 轉交 CHRLINE-Patch

`LINE.__getattr__()` 會把相容層沒有定義的方法轉交給底層 `self._client`。因此如果 CHRLINE-Patch 有提供新 API，而相容層尚未包裝，也可以先直接呼叫：

```python
result = cl.someChrlineMethod(...)
```

若要寫給插件或多人維護的程式碼，建議優先使用本文件列出的包裝方法。這些方法通常已經處理本專案常見的資料格式差異。

## 文件索引

- [登入、個人資料與輪詢](line-api-compat-auth-polling.md)
- [好友、群組與聊天室](line-api-compat-chats-contacts.md)
- [訊息、LIFF 與媒體傳送](line-api-compat-messages-media.md)
- [圖片下載與 E2EE 圖片](line-api-compat-e2ee-images.md)
- [資料結構與 AttrProxy](line-api-compat-data-model.md)
