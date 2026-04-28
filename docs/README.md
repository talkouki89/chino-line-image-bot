# 文件目錄

這個資料夾放本專案的開發文件，方便想自己寫插件或直接呼叫 bot API 的使用者參考。

## line_api_compat.py

`line_api_compat.py` 是本專案包在 CHRLINE-Patch 上方的相容層，讓程式可以用接近舊 linepy 的方式操作 LINE API。

建議閱讀順序：

1. [line_api_compat 總覽](line-api-compat-overview.md)
2. [登入、個人資料與輪詢](line-api-compat-auth-polling.md)
3. [好友、群組與聊天室](line-api-compat-chats-contacts.md)
4. [訊息、LIFF 與媒體傳送](line-api-compat-messages-media.md)
5. [圖片下載與 E2EE 圖片](line-api-compat-e2ee-images.md)
6. [資料結構與 AttrProxy](line-api-compat-data-model.md)
