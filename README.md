# Bot 實驗室

這個 repository 是 cTrader cBot 的集中實驗與開發工作區，依不同 Bot 專案分類，避免原始碼、編譯成品、回測報告與歷史檔案散落在根目錄。

## Bot 專案

- `FibonacciHarmonicSniperUltimate/`
  - 主線原始碼與專案檔
  - `versions/v0.3.0-fix5/`：目前保留的最新修正版
  - `research-archives/`：研究輸入與封存
  - `reports/`：回測與診斷結果
- `GQ-Session-Scalper-v2/`
  - `src/`：策略原始碼
  - `presets/`：基準參數
  - `reports/`：驗證與候選比較
  - `logs/`：建置紀錄
  - `docs/`：Broker / Symbol 等說明
  - 未保留非 cTrader 原生編譯的假 `.algo` 成品
- `Keltner-Channels-Trader-v2/`
  - `source/`：目前可編譯原始碼
- `Ouroboros/`
  - `builds/`：已編譯 Mobile / Cloud `.algo`
  - `handoff/`：交付封裝與說明

## CI / Backtest

GitHub Actions 位於 `.github/workflows/`，只保留目前仍有用途或仍被編譯鏈依賴的流程。

## Backups

整理前狀態保留在：

- `backup/pre-reorg-2026-09-08`
- `backup/pre-deep-cleanup-2026-09-08`

主分支只保留目前需要的 Bot、原始碼、有效建置流程、回測與必要研究資料。
