# Fibonacci Harmonic cBot 對話工作紀錄

匯出日期：2026-09-07

> 說明：此檔為目前對話的工作紀錄與關鍵內容整理，不是平台逐字匯出的完整原始聊天資料。

## 使用者目標

- 建立以 Fibonacci／Harmonic 圖形為主的 cTrader cBot。
- 圖形成立時，依多頭／空頭結構自動做多或做空。
- 適用 FxPro cTrader Mobile／Cloud。
- 回測 XAUUSD 與 EURUSD；後續先縮短為 XAUUSD 最近30天測試。
- 回報交易數、勝率、淨利、報酬率、最大回撤及 Profit Factor。

## 正確 Bot

- 名稱：Fibonacci Harmonic Sniper Ultimate
- 本次工作不是 Ouroboros V2.2，也不是其他 Bot。
- GitHub repository：`rbhnm859/Ouroboros-Cloud-Build`

## Bot 核心邏輯

- 使用最近五個確認 Pivot：X、A、B、C、D。
- 多頭排列為低／高／低／高／低，符合 Fibonacci/Harmonic 比例時判定做多。
- 空頭排列為高／低／高／低／高，符合比例時判定做空。
- 使用各線段比例與 Pattern Library 評分，而不是單純讀取圖表上的手動畫線物件。
- EMA 預設為 `ScoreOnly` 時只增加評分，不會強制阻擋逆勢交易。
- `Trading Enabled` 原始預設為 false；GitHub 回測流程會在編譯時暫時改成 true。

## 已發現問題

1. `BuildConfirmedPivots()` 在每根 K 棒關閉時重新掃描最多500根歷史 K 棒。
2. `FindBestPattern()` 每根 K 棒都會重複檢查近期 Pivot 與全部 Harmonic Patterns。
3. 沒有 Pivot 快取或增量更新，長期回測效率很低。
4. 策略週期是 H1，但回測使用 `--data-mode=m1`，一年期資料量非常大。
5. ABCD／Reciprocal 等 Pattern 比例範圍較寬，可能接受過於寬鬆的圖形。
6. XAUUSD 若止損距離過大，依風險百分比算出的交易量可能低於 FxPro 最小交易量，造成無交易。
7. 程式未發現明顯無限迴圈、Thread、Sleep 或必然崩潰點。

## 一年期回測紀錄

- Workflow：`.github/workflows/backtest-fibonacci-minimal.yml`
- GitHub Actions Run ID：`34057816779`
- 網址：<https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34057816779>
- 測試商品：XAUUSD、EURUSD
- 週期：H1
- 資料模式：M1
- 初始資金：200 USD
- 原期間：2025-09-07 至 2026-09-07

### 一年期最終結果

- Fibonacci XAUUSD H1：原始碼準備、編譯、登入 cTrader 均成功；Backtest 步驟長時間執行後被取消。
- Fibonacci EURUSD H1：原始碼準備、編譯、登入 cTrader 均成功；Backtest 步驟長時間執行後被取消。
- 沒有產生 JSON、HTML 或 Artifact。
- 目前證據顯示 Bot 能成功編譯並連線，但一年期 M1 資料回測過慢。

## 30天診斷回測設定

- 商品：XAUUSD
- 策略週期：H1
- 回測資料模式：M1
- 初始資金：200 USD
- 測試期間：最近30天
- Timeout：45分鐘
- 報告：XAUUSD-30D.html、XAUUSD-30D.json
- Artifact 名稱：Fibonacci-30D-XAUUSD-Reports
- Workflow 名稱：Fibonacci Harmonic 30D XAUUSD Diagnostic

## 已建立但尚未提交的檔案

- 檔名：`backtest-fibonacci-30d-xauusd.yml`
- GitHub 目的路徑：`.github/workflows/backtest-fibonacci-30d-xauusd.yml`
- 檔案含 `push` 觸發；提交到 main 後會自動啟動回測。

## 目前阻礙

- 嘗試透過目前 GitHub 連線建立 Workflow 時，GitHub 回傳：
  `403 Resource not accessible by integration`
- 使用者已明確同意：提交到 main、使用既有 cTrader Secrets、執行回測並保存報告。
- 但目前連線仍只有讀取能力，無法寫入 repository。
- 雲端瀏覽器操作 GitHub 也曾被環境安全政策封鎖，不能繞過。

## 需要在另一個帳號繼續的工作

1. 重新連接 GitHub，確認可存取 `rbhnm859/Ouroboros-Cloud-Build`。
2. 確保該帳號對 repository 有寫入權限。
3. 建立 `.github/workflows/backtest-fibonacci-30d-xauusd.yml`。
4. 提交到 `main`。
5. 確認 GitHub Actions 自動開始30天 XAUUSD 回測。
6. 監控 Build 與 Backtest 步驟。
7. 下載並分析 JSON/HTML Artifact。
8. 回報交易數、勝率、淨利、報酬率、Profit Factor、最大回撤。
9. 若30天仍卡住，將 `--data-mode=m1` 改為較快模式，或先優化 Pivot 掃描與 Pattern 快取。

## 可直接交給另一個 Codex 的指令

```text
請讀取 GitHub repository rbhnm859/Ouroboros-Cloud-Build。

這次要處理 Fibonacci Harmonic Sniper Ultimate，不是 Ouroboros V2.2。

請建立並提交 .github/workflows/backtest-fibonacci-30d-xauusd.yml：
- XAUUSD
- H1
- 最近30天
- M1資料模式
- 初始資金200 USD
- Timeout 45分鐘
- 使用既有 CTRADER_CTID、CTRADER_PASSWORD、CTRADER_ACCOUNT Secrets
- 產生並保存 HTML/JSON Artifact

提交到 main 後執行回測，並回報交易數、勝率、淨利、報酬率、Profit Factor與最大回撤。
不要改成測試 Ouroboros。
```

## 重要補充

- 分享 ChatGPT 對話不會轉移 GitHub 連線、GitHub 權限、Codex 額度或 cTrader Secrets。
- 另一個帳號必須使用自己的 GitHub 連線與 Codex 額度。
