# 2026.04.30.3

- 新增 `回覆搜yt`、`回覆搜fb`、`回覆搜ph`、`回覆搜ig`、`回覆搜th`，可回覆含網址的訊息後直接下載對應媒體。
- 新增管理員工具：`speedtest` 回傳測速結果圖片、`mid:MID` 查詢指定 MID 資料、`Contact @人` 以模板顯示好友資料。
- `ren` 改成 Flex 模板顯示 Bot 運行時間，並加入功能開關與管理員模板。
- 優化 `誰標我` / `清空標註`，改為只處理目前聊天室的標註紀錄，並加入公開 help 模板與 README 常用指令。
- 整理 BotCreator / 管理員指令名稱與模板，補上圖搜權限、次數、備份、登入狀態、收回與加好友等常用入口。
- 新增 Windows `ChinoBotLauncher.exe` 打包流程，支援自動下載專案、建立 `.env` 與 runtime JSON、建立虛擬環境、安裝依賴並啟動 Bot。
- Windows launcher 會使用 `requirements.txt` hash 快取依賴狀態，第二次啟動若依賴沒有變更會跳過 pip 安裝檢查。
- Windows launcher 支援 `icon/1.ico` 作為 exe 圖示，並補上 Linux 簡易安裝腳本。

# 2026.04.30.2

- 新增 auth token 登入流程；有填 `LINE_AUTH_TOKEN` 時優先使用 token，未填才依序使用帳號密碼或 SQR 掃碼登入。
- 拆分媒體下載功能：`x:URL`、`yt:URL`、`fb:URL`、`ph:URL`、`ig:URL`、`tk:URL` 分別放到獨立外掛，方便單獨開關與維護。
- Instagram 圖片下載改用 Instaloader 優先處理，影片仍保留 yt-dlp fallback；可用 `INSTALOADER_SESSION_USER` 指定本機 session。
- TikTok 圖片下載保留 API fallback，並支援 `DOUYIN_WTF_API_BASE` 改成自架解析服務。
- help 模板改成媒體下載固定第二頁；管理員看到的管理員功能固定放最後一頁。
- 移除無法穩定使用的舊下載入口，並清理相關功能開關、README、help 與依賴設定。
- 更新 README 的專案結構、環境變數、媒體下載與敏感資料保管說明。

# 2026.04.30.1

- 調整圖搜說明與搜尋引擎編號，移除目前不可用的回覆搜項目，保留可用的 SauceNAO、Ascii2D、TraceMoe、Yandex、Iqdb、AnimeTrace、GGJAV。
- 新增與整理管理員工具：`pic:about`、`rg` / `群組資訊`、`mymid`、`gid`、`mid @人`、`data`，並把 `bottoken` / `botauthtoken` 放到 BotCreator 專用區。
- 優化 `pic:about`，避免部分 LINE API 回 500 時整個指令失敗，無法取得的帳號設定欄位不再顯示。
- 優化 `x:URL` / `回覆搜x`，支援更多 X/Twitter 網域並改善網址解析、傳送結果與錯誤提示。
- 修正 `yt:URL` 的 yt-dlp 下載流程，優先選擇不需要 ffmpeg 合併的單檔影片，並改用暫存資料夾追蹤實際下載檔案。
- 調整抽圖標籤模板與 tag 指令，新增標籤分類與繁簡處理，並修正搜尋不到時的提示文字。
- 新增 Freeimage 直接圖片 URL 回傳，並補上圖片回覆 API 文件。
- 拆分標註查詢工具到獨立外掛，更新功能開關、README 專案結構與常用指令說明。
- 移除不可用或已棄用的功能入口，包括 XSList 舊關鍵字查詢、imsearch / Soutubot、E-Hentai / ExHentai / Copyseeker 與移除 E2EE 金鑰指令。
- 更新圖搜 API 版本檢查與更新指令，並整理管理員 help 模板第二頁。

# 2026.04.29.3

- 新增管理員群發功能，可先預覽文字、圖片或影片，確認後背景每秒向一個群組發送，避免一次大量發送。
- `tag色圖` 會自動將用戶輸入的繁體標籤轉成簡體送給 API，回覆顯示則維持繁體，降低繁體標籤搜尋不到的機率。
- 抽圖模板新增遊戲、其他與人物標籤，包含蔚藍檔案、絕區零、鳴潮、Shadowverse、JC、泳衣與多個角色標籤。
- README 移除專案結構中的 `Crt/`，補充 CHRLINE 憑證、token、`.data`、`.e2eekey` 等隱藏資料的保管提醒。
- AnimeTrace 圖搜結果移除 Trace ID、BoxID 與座標，AI 判斷改成顯示「是 / 否」。
- 版本更新成功後會檢查 `requirements.txt` 是否變更；若有變更會先更新依賴，成功後再重啟 Bot。

# 2026.04.29.2

- 管理員使用抽圖指令不再套用 10 秒冷卻，方便測試。
- 新增 `tag色圖 標籤` 指令，未輸入標籤時會提示範例。
- 標籤抽圖找不到資料時，改用更清楚的繁體提示並建議嘗試簡體標籤。
- 抽圖模板改為三頁 carousel，新增 Tag 色圖按鈕，並分頁整理遊戲與其他標籤。
- README 補上抽圖使用的 Lolicon API 來源與 `tag色圖 標籤` 指令。
- LIFF 模板發送失敗時改為文字 fallback，避免未授權 LIFF 時插件直接拋出 traceback。

# 2026.04.29.1

- 預設 LIFF 改為 `line://app/2009929108-vOiudUbo`。
- README 改為介紹 chino-liff 專案，移除舊 LIFF 說明。
- 移除私訊 E2EE 圖片無法下載的舊說明，文件改為標示支援回覆私訊 E2EE 圖片進行圖搜。
- 自動加好友訊息改為說明私訊與群組都可回覆圖片使用圖搜。
