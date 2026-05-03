# Chino LINE Image Search Bot

這是一個 Python LINE Bot，主要提供 LINE 群組/聊天室內的圖片反搜、影片下載、標籤管理與 Flex Message 回覆功能。

## 風險提醒

本專案是第三方 LINE Bot，並非 LINE 官方工具。使用非官方 API、自動化登入或長時間自動化操作，都可能違反服務條款或觸發風控機制，導致帳號被限制、登出或封鎖。請自行評估風險，建議使用專門的測試帳號，不要使用重要主帳號運行。

## 主要功能

- LINE 登入、收訊與回覆
- 圖片反搜：SauceNAO、Ascii2D、TraceMoe、AnimeTrace、Yandex、Iqdb、GGJAV，圖搜會在背景執行，避免卡住其他訊息
- LINE Flex Message / LIFF 搜尋結果模板，支援回覆私訊 E2EE 圖片進行圖搜
- LIFF 模板傳送失敗時會重新簽發 token，並保留文字 fallback
- 抽圖功能使用 [Lolicon API](https://docs.api.lolicon.app/#/setu) 取得隨機圖與標籤圖
- X/Twitter、YouTube、Facebook、Pornhub、Instagram、TikTok 下載相關指令
- 多張圖片會透過 `uploadMultipleImageToTalk` 成組傳送，減少逐張洗版
- nHentai、紳士漫畫、禁漫天堂、Pixiv 編號解析模板
- Freeimage.host 圖床上傳
- 管理員、使用次數、標籤資料儲存

## 專案結構

```text
.
├── main.py              # Bot 主程式與指令處理
├── line_api_compat.py   # 將 CHRLINE-Patch 包成舊 linepy 風格的相容層
├── plugins/             # 熱載入外掛與輔助模組
│   ├── __init__.py
│   ├── broadcast.py     # 管理員群發文字、圖片、影片
│   ├── example.py       # 熱載入外掛範例
│   ├── admin_profile_tools.py # speedtest / mid:MID / Contact @人
│   ├── freeimage_upload.py # #圖片上傳
│   ├── facebook_download.py # fb: Facebook 影片下載
│   ├── image_draw_template.py # 抽圖 / 標籤抽圖模板與 Lolicon API
│   ├── image_search.py  # 回覆搜 / 模板搜
│   ├── instagram_download.py # ig: Instagram 圖片 / 影片下載
│   ├── jmcomic_lookup.py # c: 禁漫天堂解析
│   ├── mention_tools.py # 誰標我 / 清空標註
│   ├── nhentai.py       # nHentai 編號解析與 Popular Now
│   ├── pixiv_lookup.py  # p: Pixiv 解析
│   ├── pornhub_download.py # ph: Pornhub 影片下載
│   ├── reply_media_download.py # 回覆搜yt/fb/ph/ig
│   ├── runtime_tools.py # ren 運行時間模板
│   ├── tiktok_download.py # tk: TikTok 圖片 / 影片下載
│   ├── wnacg.py         # w: 紳士漫畫解析
│   ├── x_download.py    # x:URL / 回覆搜x
│   ├── ytdlp_download.py # yt:URL 與 yt-dlp 共用下載工具
│   └── core/            # 共用工具
│       ├── __init__.py
│       ├── cooldown.py  # 抽圖冷卻
│       ├── features.py  # 功能開關定義
│       ├── freeimage.py # Freeimage.host API
│       ├── gallery_template.py # 作品解析 Flex 模板
│       ├── help_template.py # 說明 / 狀態 / 版本模板
│       ├── template.py  # 圖搜結果 Flex 模板
│       ├── text_convert.py # 繁簡轉換
│       └── web_image_search.py # GGJAV 等網頁圖搜輔助
├── CHRLINE/             # CHRLINE-Patch client
├── CHRLINE-Thrift/      # CHRLINE-Thrift definitions
├── docs/                # 開發文件與 line_api_compat API 參考
├── icon/                # Windows launcher 圖示
├── json/                # Bot 狀態資料
├── scripts/             # Windows / Linux 啟動與打包輔助腳本
├── tag/                 # 使用者標籤資料
└── help/                # 舊文字版指令說明
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

如果需要自己寫插件或直接參考相容層 API，可以查看 [docs/](docs/README.md)。裡面已把 `line_api_compat.py` 拆成登入與輪詢、好友與群組、訊息與媒體、E2EE 圖片下載、資料結構等多份文件。

## 設定

複製 `.env.example` 成 `.env`，再填入需要的帳號與 API key。下面每一項都有標註用途：

```env
# 登入優先順序：LINE_AUTH_TOKEN -> LINE_ACCOUNT / LINE_PASSWORD -> SQR 掃碼。

# [選填] LINE auth token。也相容 LINE_AUTHTOKEN / BOT_AUTH_TOKEN。
LINE_AUTH_TOKEN=

# [選填] LINE 登入帳號。沒填 auth token 時才會使用。
LINE_ACCOUNT=

# [選填] LINE 登入密碼。需與 LINE_ACCOUNT 一起填寫。
LINE_PASSWORD=

# [選填] SauceNAO API key。使用「回覆搜1 / 模板搜1」建議填。
SauceNAO_api_key=

# [選填] Freeimage.host API key。使用「#圖片上傳」時必填。
FREEIMAGE_API_KEY=

# [必填] Bot 作者/最高管理員 MID。
Creator=

# [選填] 後台通知聊天室/群組 ID。登入、重啟、錯誤通知會發到這裡。
Dio_GID=

# [選填] Bot 顯示時間使用的時區。預設台灣時間，可填 Asia/Taipei、UTC+8、UTC-5。
BOT_TIMEZONE=Asia/Taipei
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

CHRLINE 會在 `CHRLINE/` 內產生 `.data`、`.e2eekey`、token 與登入憑證類資料。這些資料夾通常是隱藏檔案，需要開啟顯示隱藏檔才看得到。請妥善保管，不要外流，也不要在提供 API、壓縮專案或分享檔案時順手把這些憑證資料一起給出去。

### 帳號風控建議

LINE 非官方登入與自動化操作本身就有風控風險，`blocked user code:35` 通常代表對方封鎖、不可送訊息，或帳號被 LINE 限制。程式已把容易觸發風控的主動行為做成開關：

- `AUTO_FRIEND_ADD_CONTACT=false`：預設不在加好友事件主動加對方好友。
- `SEND_STARTUP_NOTIFY=false`：預設不在每次啟動時主動傳背景通知。

若帳號容易被限制，建議維持以上預設、降低群發頻率、避免短時間大量加好友或私訊，並使用專門測試帳號運行。

### PicImageSearch 說明

最新 PicImageSearch 仍支援同步語法，例如 `from PicImageSearch.sync import SauceNAO`。本專案目前使用同步版本，但圖搜指令會丟到背景 thread 執行，因此搜尋期間不會阻塞主收訊流程。本專案另外做了這些調整：

- `Ascii2D` 的入口清單、SSL 驗證、proxy 改成環境變數；若官方站或代理入口被 Cloudflare 擋住，可用 `ASCII2D_BASE_URLS` 加可用鏡像。
- 反搜結果增加空結果檢查，避免 `resp.raw[0]` 直接炸掉。

### 作品解析設定

- `NHENTAI_COOKIE` 可選填；如果 nHentai 首頁被 Cloudflare 擋住，Popular Now 需要填瀏覽器 cookie 才能抓到。

### 媒體下載設定

- `YTDLP_COOKIES_FILE` 是 yt-dlp 的選填 cookie 檔路徑；檔案存在才會使用。
- `YTDLP_COOKIES_FROM_BROWSER` 可讓 yt-dlp 讀取瀏覽器 cookie，例如 `chrome`、`edge`、`firefox`。下載需要登入或年齡限制內容時建議先填這個。
- `YTDLP_COOKIE` 可直接貼 cookie 字串，IG / TikTok 圖片 fallback 解析時會帶上。
- `INSTALOADER_SESSION_USER` 可讓 Instagram 下載使用本機 Instaloader session；需要先用 `instaloader -l 使用者名稱` 建立。
- `DOUYIN_WTF_API_BASE` 是 TikTok 圖片解析 API，預設使用 `https://douyin.wtf`，也可以改成自己部署的服務。

Instagram 貼文如果來自受限帳號、私人帳號、需要登入或被 Instagram 暫時擋第三方解析，Bot 會直接回覆限制提示，不會再 fallback 抓登入頁 HTML，避免傳出奇怪圖片或解析雜訊。

### 媒體下載說明

媒體下載已拆成多個獨立外掛，可以在 `功能設定` 中單獨開關：

- X / Twitter：`x:URL` 可下載單一貼文圖片或影片，也可以一次貼多個 X 網址；`回覆搜x` 可回覆含 URL 的訊息後下載。支援 `x.com`、`twitter.com`、`vxtwitter.com`、`fxtwitter.com`、`fixvx.com`、`fixupx.com` 等網址。
- 影片平台：`yt:URL` / `回覆搜yt` 使用 yt-dlp 下載 YouTube 或 yt-dlp 支援的影片網址；`fb:URL` / `回覆搜fb` 下載 Facebook 影片；`ph:URL` / `回覆搜ph` 下載 Pornhub 影片。
- 社群圖片 / 影片：`ig:URL` / `回覆搜ig` 下載 Instagram 媒體；`tk:URL` 下載 TikTok 圖片或影片。

下載結果如果包含多張圖片，Bot 會優先用 `uploadMultipleImageToTalk` 成組傳送；影片仍依 LINE API 限制逐個檔案傳送。私訊遇到 E2EE/Letter Sealing plain mode 或金鑰缺失時，媒體可能無法傳送，Bot 會回覆提示；X/Twitter 下載會補上可直接開啟的媒體網址。

## 啟動

### Windows 原始碼啟動

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python main.py
```

### Windows Launcher

Releases 會提供 `ChinoBotLauncher.exe`。可以把 exe 放在專案根目錄執行；如果只把 exe 放到空資料夾，它會自動下載 `chino-line-image-bot` 到同一個資料夾後再啟動。

Launcher 會自動處理：

- 建立 `.env`、`json/ban.json`、`json/temp.json`、`json/features.json`
- 建立 `.venv`
- 安裝 `requirements.txt`
- 啟動 `main.py`

第一次啟動會比較久，因為需要下載專案與安裝依賴。安裝成功後會把 `requirements.txt` 的 hash 記錄到 `.venv\.requirements.sha256`，之後只要依賴沒有變更，就會跳過 pip 安裝檢查。若更新版本後 `requirements.txt` 有變更，Launcher 會自動重新安裝依賴。

如果某些 Windows 電腦缺少可用的根憑證，下載 GitHub zip 時可能出現 `CERTIFICATE_VERIFY_FAILED`。Launcher 會先照正常 SSL 驗證下載；確認是憑證鏈問題後，會改用備援下載流程，避免第一次自動安裝直接中斷。

如果電腦找不到 Python，Launcher 會自動下載 Python 3.11 Windows 安裝程式並開啟安裝視窗。安裝時請勾選 `Add python.exe to PATH`，完成後回到 Launcher 視窗按 Enter，Launcher 會繼續建立 `.venv` 與啟動 Bot。

檢查 launcher 是否能找到專案與 Python：

```powershell
.\ChinoBotLauncher.exe --check
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

也可以直接使用腳本建立環境：

```bash
bash scripts/linux_install.sh
```

### 打包 Windows Launcher

想做成 Releases 可放的 Windows exe，可以先安裝 PyInstaller 後執行：

```powershell
python -m pip install pyinstaller
powershell -ExecutionPolicy Bypass -File scripts\build_windows_launcher.ps1
```

產生的 `dist\ChinoBotLauncher.exe` 是啟動器；如果 `icon\1.ico` 存在，打包時會自動套用為 exe 圖示。

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
   - `plugins/mention_tools.py`：`誰標我` / `清空標註`
   - `plugins/freeimage_upload.py`：`#圖片上傳`
   - `plugins/image_draw_template.py`：抽圖模板、隨機圖、R18 圖、tag 色圖
   - `plugins/x_download.py`：`x:URL` / `回覆搜x`
   - `plugins/reply_media_download.py`：`回覆搜yt` / `回覆搜fb` / `回覆搜ph` / `回覆搜ig`
   - `plugins/ytdlp_download.py`：`yt:URL`
   - `plugins/facebook_download.py`：`fb:URL`
   - `plugins/pornhub_download.py`：`ph:URL`
   - `plugins/instagram_download.py`：`ig:URL`
   - `plugins/tiktok_download.py`：`tk:URL`
   - `plugins/admin_profile_tools.py`：`speedtest` / `mid:MID` / `Contact @人`
   - `plugins/runtime_tools.py`：`ren`
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
功能切換 x_download
功能切換 engine_saucenao
功能切換 announcement_notify
```

想查看目前狀態可以輸入 `功能狀態`。功能開關會保存到 `json/features.json`，這個檔案屬於本機 runtime 狀態，預設不提交到 Git。

## 常用指令

實際指令請以 `main.py` 和 `plugins/` 內指令為準。常見功能包含：

- `圖搜說明`：顯示圖搜、媒體下載與常用功能模板。
- `功能狀態`：管理員查看目前功能開關狀態。
- `版本檢查`：管理員查看本機版本、遠端版本與更新內容。
- `版本更新`：管理員從 GitHub 拉取新版，必要時更新依賴並重啟 Bot。
- `圖搜api版本檢查`：管理員檢查 PicImageSearch 版本是否有更新。
- `更新圖搜api`：管理員更新 PicImageSearch 依賴。
- `pic:about`：管理員查看 Bot 帳號與執行資訊。
- `rg` / `群組資訊`：管理員查看目前群組資訊。
- `mymid`：管理員查看自己的 MID。
- `gid`：管理員查看目前群組 GID。
- `mid @人`：管理員查看被標註者的 MID。
- `data`：管理員回覆訊息後查看該訊息原始資料。
- `回覆搜1` ~ `回覆搜7`：回覆圖片後使用不同圖搜引擎搜尋圖片來源或相似結果。
- `模板搜1` ~ `模板搜3`：BotCreator 回覆圖片後輸出指定圖搜引擎的模板結果。
- `x:URL`：下載 X/Twitter 貼文內的圖片或影片。
- `回覆搜x`：回覆含 X/Twitter URL 的訊息後下載其中圖片或影片。
- `yt:URL`：下載 YouTube 或 yt-dlp 支援的影片。
- `回覆搜yt`：回覆影片 URL 後下載。
- `fb:URL`：下載 Facebook 影片。
- `回覆搜fb`：回覆 Facebook URL 後下載。
- `ph:URL`：下載 Pornhub 影片。
- `回覆搜ph`：回覆 Pornhub URL 後下載。
- `ig:URL`：下載 Instagram 圖片或影片。
- `回覆搜ig`：回覆 Instagram URL 後下載。
- `tk:URL`：下載 TikTok 圖片或影片。
- `speedtest`：管理員執行測速並回傳結果圖片。
- `mid:MID`：管理員查詢指定 MID 的好友資料。
- `Contact @人`：管理員用模板查看被標註者資料。
- `ren`：以模板顯示 Bot 運行時間。
- `誰標我`：查看目前聊天室最近標註你的人。
- `清空標註`：清空目前聊天室的標註紀錄。
- `#圖片上傳`：回覆圖片後上傳到 Freeimage.host，並回傳圖片網址。
- `抽圖`：顯示抽圖模板。
- `隨機圖`：取得一般隨機圖。
- `隨機無ai`：取得排除 AI 標籤的隨機圖。
- `r18色圖`：取得 R18 隨機圖。
- `r18無ai`：取得排除 AI 標籤的 R18 隨機圖。
- `tag色圖 標籤`：依指定標籤抽圖，會自動處理繁簡轉換。
- `群發 內容`：管理員建立群發預覽。
- `確認群發` / `取消群發` / `群發狀態`：管理員確認、取消或查看群發進度。
- `n:數字`：解析 nHentai 作品資訊。
- `n:popular`：顯示 nHentai Popular Now。
- `w:數字`：解析紳士漫畫作品。
- `c:數字`：解析禁漫天堂作品。
- `p:數字`：解析 Pixiv 作品。
- `lg`：管理員觸發登入/狀態相關工具。
- `pic:reb`：管理員重啟 Bot。

## 版本檢查與更新

專案根目錄有 `VERSION` 檔案，用來判斷目前版本；`VERSION_NOTES.md` 用來顯示版本更新內容。每次合併 PR 或發布更新時，請同步更新這兩個檔案。

- `版本檢查`：讀取本機與 GitHub `master` 的 `VERSION` / `VERSION_NOTES.md`，若有新版會顯示最近合併 PR 與版本更新內容。
- `版本更新`：管理員限定，會執行 `git fetch` 與 `git pull --ff-only origin master`。更新後如果 `requirements.txt` 有變更，會先更新依賴，再自動重啟 Bot 套用新程式。

若本機檔案和遠端更新真的衝突，`git pull` 會回傳錯誤並停止。

## LIFF 設定

目前預設使用本專案搭配的 LIFF：`line://app/2009929108-vOiudUbo`。

LIFF 專案網址：[chino-liff](https://github.com/talkouki89/chino-liff)。可以直接使用這個 LIFF，也可以自行 clone 後建立自己的 LINE LIFF App，再把程式內的 LIFF ID 換成自己的。

Bot 送 Flex 模板時會先整理成合法的 LINE messages 陣列。若 LIFF token 開太久失效，會重新簽發 token 再送一次；仍失敗時會改傳模板內文字與 `allowliff` 授權連結。

## 第三方項目

本專案使用或相容下列第三方項目，請同時遵守各自授權與使用規範：

- [CHRLINE-Patch](https://github.com/WEDeach/CHRLINE-Patch)
- [CHRLINE-Thrift](https://github.com/DeachSword/CHRLINE-Thrift)
- [PicImageSearch](https://github.com/kitUIN/PicImageSearch)
- [Lolicon API](https://docs.api.lolicon.app/#/setu)
- [chino-liff](https://github.com/talkouki89/chino-liff)
- [jmcomic](https://github.com/hect0x7/JMComic-Crawler-Python)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [douyin.wtf](https://douyin.wtf)
- [Freeimage.host API](https://freeimage.host/page/api)

## 許可證與法律資訊

本專案自身新增的程式碼以 MIT License 授權，詳見 `LICENSE`。倉庫內或依賴中的第三方程式碼、API、網站內容與資料來源，仍適用其原作者或服務提供者的授權與條款。

本專案是第三方 LINE Bot，使用非官方 API 可能造成帳號限制、封鎖或其他風險。使用者需自行承擔使用後果，並確認符合所在地法律、LINE 服務條款、第三方網站條款與內容分級要求。若您不同意上述任一條款，請勿直接或間接使用本項目。

## 注意事項

請不要提交敏感資料到 Git：

- `.env`
- `cookies.txt`
- `CHRLINE/` 內的 `.data`、`.e2eekey`、token 與登入憑證資料
- `errorLog.txt`
- 下載後產生的影片、圖片暫存檔

這個 Bot 依賴非官方 LINE API，登入、Thrift schema、endpoint 都可能因 LINE 更新而失效。若出現登入或輪詢錯誤，優先檢查 `CHRLINE/`、`CHRLINE-Thrift/` 與 `line_api_compat.py`。
