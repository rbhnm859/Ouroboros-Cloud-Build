# cTrader cBot Workspace

此 repository 依 Bot 專案分類，避免原始碼、編譯成品、回測報告與歷史檔案散落在根目錄。

## Bot 專案

- `FibonacciHarmonicSniperUltimate/`
  - 主線原始碼與專案檔
  - `versions/v0.3.0-fix5/`：目前保留的最新修正版
  - `research-archives/`：研究輸入/封存
  - `docs/`：開發與工作紀錄
  - `reports/`：回測/診斷結果
- `GQ-Session-Scalper-v2/`
  - `src/`、`presets/`、`reports/`、`logs/`、`docs/` 與已編譯 `.algo`
- `Keltner-Channels-Trader-v2/`
  - `source/`：可編譯原始碼
- `Ouroboros/`
  - `builds/`：已編譯 Mobile/Cloud `.algo`
  - `handoff/`：交付封裝與說明

## CI / Backtest

GitHub Actions 位於 `.github/workflows/`。

## Cleanup

2026-09-08 整理時，主分支移除 Fibonacci `fix1`～`fix4` 舊工作副本與對應過時 workflow，並移除 Keltner 已解壓後的重複 source ZIP。整理前完整狀態保存在分支：

`backup/pre-reorg-2026-09-08`

此次整理僅調整檔案結構與移除重複/過時工作副本，不修改任何 cBot 交易邏輯。
