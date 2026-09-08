# Ouroboros V2.2 GitHub 交接專案

此專案包以 GitHub `main` 最新狀態重新建立，用於保存目前程式、回測資料與對話脈絡。

## 基準版本

- Repository：`rbhnm859/Ouroboros-Cloud-Build`
- 打包時 HEAD：`3b1e94fa6eb2a3dc5134813f5e0bfe41586add0f`
- Commit：`Align FX and metals session with London liquidity`

## 內容

- `repository/`：上述 HEAD 的完整 Git 追蹤檔案，不含 `.git` 與認證。
- `conversation/`：本次對話與執行紀錄。
- `compiled/`：先前 workflow 成功編譯並完成三品種回測的 `.algo`。
- `reports/`：XAUUSD、EURUSD、BITCOIN 30 天 M1 HTML／JSON 報告。
- `CONTINUE_PROMPT.md`：交給另一個 AI 接手的指令。

## 注意

`compiled/` 內是上一個已驗證 artifact，不一定對應打包時最新 HEAD。若要使用最新程式，必須在 GitHub Actions 重新編譯並下載新 artifact。

本包不包含 cTrader 密碼、GitHub Token、API Key、`accounts.txt`、`.pwd` 或 `.git` 認證資料。

