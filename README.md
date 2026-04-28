# Chino LINE Image Search Bot

這是一個 Python LINE Bot，主要提供 LINE 群組/聊天室內的圖片反搜、影片下載、標籤管理與 Flex Message 回覆功能。

## 風險提醒

本專案是第三方 LINE Bot，並非 LINE 官方工具。使用非官方 API、自動化登入或長時間自動化操作，都可能違反服務條款或觸發風控機制，導致帳號被限制、登出或封鎖。請自行評估風險，建議使用專門的測試帳號，不要使用重要主帳號運行。

## 使用建議

因為 LINE 私訊常啟用 E2EE/Letter Sealing，第三方 API 不一定能解密或下載私訊圖片原始檔，可能導致圖片反搜、圖片上傳等功能無法取得圖片。建議主要在群組中使用本 Bot；如果必須在私訊使用，請先確認該聊天室的 E2EE 設定與圖片是否能被 Bot 下載。

## 主要功能

- LINE 登入、收訊與回覆
- 圖片反搜：SauceNAO、Ascii2D、TraceMoe、AnimeTrace、E-Hentai、ExHentai、Copyseeker、Yandex、Iqdb
- LINE Flex Message / LIFF 搜尋結果模板
- X/Twitter、YouTube 下載相關指令
- nHentai、紳士漫畫、禁漫天堂、Pixiv 編號解析模板
- Freeimage.host 圖床上傳
- 黑名單、管理員、標籤資料儲存

## 專案結構

```text
.
├── main.py              # Bot 主程式與指令處理
├── line_api_compat.py   # 將 CHRLINE-Patch 包成舊 linepy 風格的相容層
├── plugins/             # 熱載入外掛與輔助模組
│   ├── image_search.py  # 回覆搜 / 模板搜
│   ├── freeimage_upload.py # #圖片上傳
│   ├── media_tools.py   # X、yt-dlp、標註查詢、小工具
│   ├── wnacg.py         # w: 紳士漫畫解析
│   ├── jmcomic_lookup.py # c: 禁漫天堂解析
│   ├── pixiv_lookup.py  # p: Pixiv 解析
│   ├── nhentai.py       # nHentai 編號解析與 Popular Now
│   └── core/            # 共用工具：Flex 模板、作品模板、Freeimage.host、X 解析
├── CHRLINE/             # CHRLINE-Patch client
├── CHRLINE-Thrift/      # CHRLINE-Thrift definitions
├── json/                # Bot 狀態資料
├── tag/                 # 使用者標籤資料
├── help/                # 舊文字版指令說明
└── Crt/                 # LINE 登入憑證/憑證資料
```

## 安裝

建議使用 Python 3.10 或 3.11。此專案目前也已針對較新的 Python 環境調整 PicImageSearch 依賴。

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

本專案已改用：

- [CHRLINE-Patch](https://github.com/WEDeach/CHRLINE-Patch)
- [CHRLINE-Thrift](https://github.com/DeachSword/CHRLINE-Thrift)
- [PicImageSearch](https://github.com/kitUIN/PicImageSearch)

`main.py` 不直接呼叫 CHRLINE 的原始 dict/list 結構，而是透過 `line_api_compat.py` 保留原本 `cl.sendMessage(...)`、`op.message.text` 等舊寫法，降低遷移成本。

## 設定

複製 `.env.example` 成 `.env`，再填入需要的帳號與 API key。下面每一項都有標註用途：

```env
# [必填] LINE 登入帳號。
LINE_ACCOUNT=

# [必填] LINE 登入密碼。
LINE_PASSWORD=

# [選填] SauceNAO API key。使用「回覆搜1 / 模板搜1」建議填。
SauceNAO_api_key=

# [選填] Freeimage.host API key。使用「#圖片上傳」時必填。
FREEIMAGE_API_KEY=

# [必填] Bot 作者/最高管理員 MID。
Creator=

# [選填] 後台通知聊天室/群組 ID。登入、重啟、錯誤通知會發到這裡。
Dio_GID=

# [選填] PicImageSearch proxy，例如 http://127.0.0.1:7890。一般不用填。
PICSEARCH_PROXIES=

# [選填] PicImageSearch timeout 秒數。網路慢或 ExHentai 常 timeout 可調高。
PICSEARCH_TIMEOUT=60

# [選填] 是否驗證 SSL。一般保持 true。
PICSEARCH_VERIFY_SSL=true

# [選填] Ascii2D 入口清單，逗號分隔。官方站被擋時可加可用代理入口。
ASCII2D_BASE_URLS=https://ascii2d.net

# [選填] E-Hentai cookie。使用「回覆搜4」遇到限制時才需要。
EHENTAI_COOKIES=

# [選填] ExHentai cookie。使用「回覆搜5」通常需要。
EXHENTAI_COOKIES=

# [選填] nHentai cookie。遇到 403 或個人化結果再填。
NHENTAI_COOKIE=

# [選填] yt-dlp cookie 檔案路徑。下載需要登入或年齡限制內容時使用。
YTDLP_COOKIES_FILE=cookies.txt

# [選填] 是否啟用 plugins/ 熱載入。建議保持 true。
HOT_RELOAD_PLUGINS=true

# [不建議改動] LINE 裝置類型。改錯可能導致登入或 sync 失敗。
CHRLINE_DEVICE=DESKTOPWIN

# [不建議改動] LINE app version。留空使用 CHRLINE 預設。
CHRLINE_VERSION=

# [選填] CHRLINE debug log。排查 API 問題時才改 true。
CHRLINE_DEBUG=false

# [不建議改動] 是否使用 Thrift。
CHR_USE_THRIFT=True

# [不建議改動] CHRLINE 內部 TMore 行為。
CHR_TMORE_FORCE=False

# [不建議改動] LINE API domain。除非 LINE endpoint 改版或測試特殊環境，否則不要改。
LINE_HOST_DOMAIN=https://ga2.line.naver.jp
LINE_OBS_DOMAIN=https://obs.line-apps.com
LINE_API_DOMAIN=https://api.line.me
LINE_ACCESS_DOMAIN=https://access.line.me
LINE_BIZ_TIMELINE_DOMAIN=https://ga2.line.naver.jp/mh
```

### Runtime JSON

`json/ban.json`、`json/temp.json` 和 `json/features.json` 是機器運行時資料，已被 `.gitignore` 排除，不建議提交真實 MID、使用次數或個人開關狀態。

格式可以參考：

- `json/ban.example.json`
- `json/temp.example.json`
- `json/features.example.json`

第一次啟動時，如果正式檔案不存在，`main.py` 會自動用預設值建立。需要手動建立時可以複製範例：

```powershell
Copy-Item json\ban.example.json json\ban.json
Copy-Item json\temp.example.json json\temp.json
Copy-Item json\features.example.json json\features.json
```

`tag/*.json` 是使用者標註紀錄，也已被 `.gitignore` 排除；`tag/.gitkeep` 只用來保留空資料夾。

### PicImageSearch 說明

最新 PicImageSearch 仍支援同步語法，例如 `from PicImageSearch.sync import SauceNAO`。本專案目前使用同步版本，並做了這些調整：

- `CopyseekerSync` 改成搭配 `Network` client 使用，符合新版範例。
- `Ascii2D` 的入口清單、SSL 驗證、proxy 改成環境變數；若官方站或代理入口被 Cloudflare 擋住，可用 `ASCII2D_BASE_URLS` 加可用鏡像。
- `EHENTAI_COOKIES` / `EXHENTAI_COOKIES` 改由 `.env` 提供，不再把 cookie 寫死在程式碼。
- `NHENTAI_COOKIE` 可選填；如果 nHentai 首頁被 Cloudflare 擋住，Popular Now 需要填瀏覽器 cookie 才能抓到。
- 反搜結果增加空結果檢查，避免 `resp.raw[0]` 直接炸掉。
- `YTDLP_COOKIES_FILE` 是 yt-dlp 的選填 cookie 檔路徑；檔案存在才會使用。

## 啟動

```powershell
python main.py
```

第一次啟動可能需要完成 LINE 登入流程。`main.py` 是長駐輪詢程式，測試語法時建議使用 `python -m py_compile main.py`，不要直接執行登入流程。

## 熱載入外掛

你可以把新功能寫在 `plugins/` 下面，不需要重啟 bot，也不會重新登入 LINE。Bot 每次收到訊息時會檢查外掛檔案是否有更新，有更新就重新載入。

最小範例：

```python
def handle(ctx):
    if ctx.cmd == "ping":
        ctx.reply("pong")
        return True
    return False
```

`ctx` 常用欄位：

- `ctx.cmd`：小寫後的訊息文字
- `ctx.text`：原始訊息文字
- `ctx.to`：回覆目標
- `ctx.sender`：發訊者 MID
- `ctx.cl`：LINE client
- `ctx.reply("文字")`：回覆目前訊息
- `ctx.is_creator` / `ctx.is_admin`：權限判斷

如果要關閉外掛熱載入，設定 `HOT_RELOAD_PLUGINS=false`。

### 移除不需要的功能

大部分獨立功能都放在 `plugins/` 內。如果你不需要某個功能，可以直接移除或改名對應的外掛檔案，Bot 收到下一則訊息時就不會再載入它。

簡單做法：

1. 先停止 Bot，或確認 `HOT_RELOAD_PLUGINS=true`。
2. 到 `plugins/` 找到對應檔案，例如：
   - `plugins/wnacg.py`：`w:數字`
   - `plugins/jmcomic_lookup.py`：`c:數字`
   - `plugins/pixiv_lookup.py`：`p:數字`
   - `plugins/nhentai.py`：`n:數字` / `n:popular`
   - `plugins/media_tools.py`：隨機圖、R18 圖、X/Twitter、yt-dlp
   - `plugins/freeimage_upload.py`：`#圖片上傳`
   - `plugins/image_draw_template.py`：抽圖模板
3. 不想刪除原始碼時，可以把檔名改成底線開頭，例如 `plugins/_wnacg.py`。PluginManager 會略過底線開頭的檔案。
4. 確認功能不再需要後，再刪除檔案或提交改名。

如果只是暫時不想開放功能，不建議刪檔，建議使用管理員開關。

### 功能開關

管理員可以在 LINE 裡輸入 `功能設定`，用模板按鈕開啟或關閉功能。也可以直接輸入：

```text
功能切換 <key>
```

例如：

```text
功能切換 nhentai
功能切換 media_tools
功能切換 engine_saucenao
功能切換 announcement_notify
```

想查看目前狀態可以輸入 `功能狀態`。功能開關會保存到 `json/features.json`，這個檔案屬於本機 runtime 狀態，預設不提交到 Git。

## 常用指令

實際指令請以 `main.py` 和 `plugins/` 內指令為準。常見功能包含：

- `圖搜說明`
- `功能狀態`
- `回覆搜1` ~ `回覆搜11`
- `模板搜1` ~ `模板搜3`
- `x;URL`
- `#圖片上傳`
- `抽圖`
- `隨機圖`
- `隨機無ai`
- `r18色圖`
- `r18無ai`
- `ytmp4:URL`
- `n:數字`
- `n:popular`
- `w:數字`
- `c:數字`
- `p:數字`
- `xs:關鍵字`
- `lg`
- `pic:about`
- `pic:reb`

## LIFF 設定

目前範例使用的 LIFF ID 來自第三方模板專案 [MISAKA_LIFF](https://github.com/Sakuya0502/MISAKA_LIFF)。如果你不想使用別人的 LIFF，可以自行建立 LINE LIFF App，並把程式內的 LIFF ID 換成自己的。

第一次使用模板功能時，建議先輸入 `Allowliff` 讓帳號授權 LIFF 權限。

## imsearch / Soutubot

`回覆搜10` 預設會嘗試使用 [soutubot.moe](https://soutubot.moe/) 的網頁端點。若網站被 Cloudflare 或其他限制擋住，可以自行部署 [lolishinshi/imsearch](https://github.com/lolishinshi/imsearch)。

```powershell
docker run -it -v ./imsearch:/root/.config/imsearch aloxaf/imsearch:latest --help
```

建立索引並啟動 HTTP server 後，在 `.env` 填：

```env
IMSEARCH_API_URL=http://127.0.0.1:8000
IMSEARCH_TOKEN=
```

`imsearch` 是 GPL-3.0 授權的 Rust 專案，本專案不直接內嵌其源碼，避免授權邊界混亂。

## 第三方項目

本專案使用或相容下列第三方項目，請同時遵守各自授權與使用規範：

- [CHRLINE-Patch](https://github.com/WEDeach/CHRLINE-Patch)
- [CHRLINE-Thrift](https://github.com/DeachSword/CHRLINE-Thrift)
- [PicImageSearch](https://github.com/kitUIN/PicImageSearch)
- [MISAKA_LIFF](https://github.com/Sakuya0502/MISAKA_LIFF)
- [lolishinshi/imsearch](https://github.com/lolishinshi/imsearch)
- [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Freeimage.host API](https://freeimage.host/page/api)

## 許可證與法律資訊

本專案自身新增的程式碼以 MIT License 授權，詳見 `LICENSE`。倉庫內或依賴中的第三方程式碼、API、網站內容與資料來源，仍適用其原作者或服務提供者的授權與條款。

本專案是第三方 LINE Bot，使用非官方 API 可能造成帳號限制、封鎖或其他風險。使用者需自行承擔使用後果，並確認符合所在地法律、LINE 服務條款、第三方網站條款與內容分級要求。若您不同意上述任一條款，請勿直接或間接使用本項目。

## 注意事項

請不要提交敏感資料到 Git：

- `.env`
- `cookies.txt`
- `Crt/`
- `errorLog.txt`
- 下載後產生的影片、圖片暫存檔

這個 Bot 依賴非官方 LINE API，登入、Thrift schema、endpoint 都可能因 LINE 更新而失效。若出現登入或輪詢錯誤，優先檢查 `CHRLINE/`、`CHRLINE-Thrift/` 與 `line_api_compat.py`。
