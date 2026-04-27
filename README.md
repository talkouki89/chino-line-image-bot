# Chino LINE Image Search Bot

這是一個 Python LINE Bot，主要提供 LINE 群組/聊天室內的圖片反搜、影片下載、標籤管理與 Flex Message 回覆功能。

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
├── line_api_compat.py   # 將 CHRLINE-Patch 包成舊 AKANEPY 風格的相容層
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
├── help/                # 指令說明文字
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

複製 `.env.example` 成 `.env`，再填入需要的帳號與 API key。

```env
LINE_ACCOUNT=
LINE_PASSWORD=
SauceNAO_api_key=
FREEIMAGE_API_KEY=
Creator=
Dio_GID=

# PicImageSearch optional settings
PICSEARCH_PROXIES=
PICSEARCH_TIMEOUT=60
PICSEARCH_VERIFY_SSL=true
ASCII2D_BASE_URLS=https://ascii2d.net
EHENTAI_COOKIES=
EXHENTAI_COOKIES=
NHENTAI_COOKIE=
YTDLP_COOKIES_FILE=cookies.txt
HOT_RELOAD_PLUGINS=true

# CHRLINE-Patch optional settings
CHRLINE_DEVICE=DESKTOPWIN
CHRLINE_VERSION=
CHRLINE_DEBUG=false
CHR_USE_THRIFT=True
CHR_TMORE_FORCE=False
LINE_HOST_DOMAIN=https://ga2.line.naver.jp
LINE_OBS_DOMAIN=https://obs.line-apps.com
LINE_API_DOMAIN=https://api.line.me
LINE_ACCESS_DOMAIN=https://access.line.me
LINE_BIZ_TIMELINE_DOMAIN=https://ga2.line.naver.jp/mh
```

### Runtime JSON

`json/ban.json` 和 `json/temp.json` 是機器運行時資料，已被 `.gitignore` 排除，不建議提交真實 MID 或使用次數。

格式可以參考：

- `json/ban.example.json`
- `json/temp.example.json`

第一次啟動時，如果正式檔案不存在，`main.py` 會自動用預設值建立。需要手動建立時可以複製範例：

```powershell
Copy-Item json\ban.example.json json\ban.json
Copy-Item json\temp.example.json json\temp.json
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

## 常用指令

完整指令請看 `help/help.txt`、`help/help0.txt`、`help/help1.txt`、`main.py` 與 `plugins/` 內的指令分支。常見功能包含：

- `回覆搜1` ~ `回覆搜9`
- `模板搜1` ~ `模板搜3`
- `x;URL`
- `回覆搜x`
- `#圖片上傳`
- `隨機圖`
- `r18色圖`
- `tag色圖 標籤`
- `ytmp4:URL`
- `n:數字`
- `n:popular`
- `w:數字`
- `c:數字`
- `p:數字`
- `pic:about`
- `pic:reb`

## 注意事項

請不要提交敏感資料到 Git：

- `.env`
- `cookies.txt`
- `Crt/`
- `errorLog.txt`
- 下載後產生的影片、圖片暫存檔

這個 Bot 依賴非官方 LINE API，登入、Thrift schema、endpoint 都可能因 LINE 更新而失效。若出現登入或輪詢錯誤，優先檢查 `CHRLINE/`、`CHRLINE-Thrift/` 與 `line_api_compat.py`。
