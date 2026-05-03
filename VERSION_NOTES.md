# 2026.05.04.1

- 修正 Instagram 受限貼文或帳號解析失敗時可能 fallback 抓到登入頁 HTML，導致 Bot 傳出奇怪圖片或雜訊提示的問題。
- Instagram 遇到 403、需登入、私人貼文、限制帳號、challenge 或 rate limit 類錯誤時，會直接回覆清楚限制說明，不再改用 fallback 下載。
- 將 Instaloader 取貼文與讀取 sidecar/video URL 的過程完整包住 stdout/stderr，避免 GraphQL retry 訊息露出到執行畫面。
- README 補上 Instagram 受限內容的處理方式與 `INSTALOADER_SESSION_USER` 使用情境。

# 2026.05.03.2

- 移除已不維護的 Threads 下載入口，`回覆搜th` 已從 README、媒體下載模板、功能列表與回覆下載外掛中移除。
- 重新整理 `圖搜說明` 第二頁的媒體下載模板，改成 X/Twitter、影片平台、社群圖片/影片三段，並補上多圖會合併傳送的提示。
- X/Twitter 下載支援一次輸入多個網址，例如 `x:URL URL URL`，解析到多張圖片時會使用 `uploadMultipleImageToTalk` 成組傳送。
- Instagram 下載遇到 GraphQL 403、登入限制或第三方解析被擋時，會壓掉 instaloader 的雜訊輸出，改回覆可讀提示並嘗試 fallback 下載流程。
- Windows Launcher 找不到 Python 時會自動下載 Python 3.11 安裝程式並開啟，安裝完成後可回到 Launcher 繼續建立 `.venv` 與啟動 Bot。
- 新增 `BOT_TIMEZONE` 設定，預設 `Asia/Taipei`，支援 `UTC+8` 這類格式；錯誤紀錄、群組建立時間與標註時間會使用該時區。
- 新增 `AUTO_FRIEND_ADD_CONTACT` 與 `SEND_STARTUP_NOTIFY` 風控開關，預設降低主動加好友與啟動通知，減少帳號被限制的機率。
- README 補上 Python 自動安裝、帳號風控建議、媒體下載整理與新時區設定說明；`.env.example` 補齊相關設定。

# 2026.05.03.1

- 修正 `exec:` 管理指令只執行不回傳的問題，現在會回覆 stdout、stderr 或單行運算結果，輸出過長時會自動截斷。
- 改善 Windows Launcher 在部分電腦下載專案時遇到 SSL 憑證鏈錯誤的情況；一般下載失敗且確認是憑證驗證問題時，會改用備援下載流程。
- 圖搜與模板搜改為背景執行，收到指令後先回覆開始處理，搜尋完成後再回傳結果，避免主收訊流程被 PicImageSearch 或外部 API 卡住。
- 改善 LIFF Flex 模板傳送流程，送出前會整理成合法的 messages 陣列，遇到 token 或 invalid 類錯誤時會重新簽發 LIFF token 再嘗試。
- X/Twitter 下載支援更多轉址網域，新增 `fixvx.com`、`fixupx.com` 以及對應 `www.` 網域。
- 多張圖片傳送改用 `uploadMultipleImageToTalk`，讓 X/Twitter、yt-dlp 共用下載與 Instagram 多圖結果以同一組圖片訊息送出，減少洗版。
- 私訊媒體傳送遇到 E2EE/Letter Sealing plain mode 或 key 缺失時，會回覆更明確的「無法傳送影片」提示；X/Twitter 會補上直接開啟的媒體網址。
- README 補上 douyin.wtf 第三方項目、X 支援網域、多圖傳送、非同步圖搜、LIFF 與 launcher SSL 備援說明。
- `line_api_compat` 文件新增 `uploadMultipleImageToTalk()` 使用說明。

# 2026.04.30.3

- 新增回覆訊息下載指令：`回覆搜yt`、`回覆搜fb`、`回覆搜ph`、`回覆搜ig`、`回覆搜th`。
- 新增管理員工具：`speedtest`、`mid:MID`、`Contact @人`、`pic:about`、`rg`、`data` 等維護指令。
- `ren` 改為 Flex 模板顯示 Bot 運行時間，並納入功能開關與說明模板。
- 新增標註查詢工具：`誰標我`、`清空標註`。
- 整理公開與管理員說明模板，避免公開 help 顯示過多管理員專用項目。
- Windows Launcher 支援自動下載專案、建立 `.env` 與 runtime JSON、建立 `.venv` 並啟動 `main.py`。
- Windows Launcher 會用 `requirements.txt` 的 SHA256 快取依賴安裝狀態，避免每次啟動都重新跑 pip。
- Windows Launcher 打包時會套用 `icon/1.ico` 作為 exe 圖示。

# 2026.04.30.2

- 新增 auth token 登入流程，支援 `LINE_AUTH_TOKEN`、`LINE_AUTHTOKEN`、`BOT_AUTH_TOKEN`。
- 新增媒體下載外掛：`x:URL`、`yt:URL`、`fb:URL`、`ph:URL`、`ig:URL`、`tk:URL`。
- Instagram 下載優先使用 Instaloader，失敗時 fallback 到 yt-dlp。
- TikTok 圖片下載新增 API fallback，預設使用 `DOUYIN_WTF_API_BASE`。
- README 與 help 模板補上媒體下載、功能開關與安裝設定說明。

# 2026.04.30.1

- 整理圖搜說明模板，補齊 SauceNAO、Ascii2D、TraceMoe、Yandex、Iqdb、AnimeTrace、GGJAV 等引擎。
- 新增常用管理員指令與帳號狀態查詢功能。
- 改善 `x:URL` / `回覆搜x` 的 X/Twitter 圖片與影片解析。
- 新增 Freeimage 圖床上傳功能。
- 新增功能開關架構，管理員可透過 `功能設定` / `功能狀態` 管理外掛與搜尋引擎。

# 2026.04.29.3

- 新增群發工具與抽圖標籤功能。
- README 補上 CHRLINE 憑證、token、`.data`、`.e2eekey` 等敏感資料注意事項。
- AnimeTrace 結果模板補上 Trace ID、Box ID 與 AI 判斷資訊。
- 更新啟動與依賴檢查文件。

# 2026.04.29.2

- 新增抽圖與 tag 色圖相關模板。
- LIFF 模板增加文字 fallback，避免 LIFF 發送失敗時只留下 traceback。
- README 補上 Lolicon API 與抽圖指令說明。

# 2026.04.29.1

- 設定預設 LIFF ID：`line://app/2009929108-vOiudUbo`。
- README 補上 chino-liff 專案與 LIFF 設定說明。
- 新增 E2EE 圖片下載說明與回覆圖片圖搜注意事項。
