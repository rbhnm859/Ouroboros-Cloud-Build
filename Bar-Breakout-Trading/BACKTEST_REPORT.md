# BACKTEST REPORT

## 最新狀態

- Bar Breakout Trading 本地 build 成功並已產出 `.algo`。
- 針對雲端回測鏈路，已完成 Keltner smoke 的失敗/修復對照驗證：
  - 失敗 run: `34188549640`
  - 修復後成功 run: `34189167177`

## 失敗根因摘要（Run 34188549640）

- 並非帳密或 symbol/timeframe 無效；log 顯示已連線並成功登入。
- 在 `Progress | Backtesting | 0.00 % |` 後，CLI 先輸出損壞統計片段（例如 `"Equity":,`、`"NetProfit":-,`），接著才拋出：
  - `System.InvalidOperationException: Message expected`
  - `BacktestReportSavingStateStrategy.DoEnter()`
- 根因類型：**cTrader CLI + report/output 階段訊息協定異常**（非 cBot 策略邏輯錯誤）。

## 已驗證 workaround（Run 34189167177）

相較失敗參數，改為：
- 固定 image：`ghcr.io/spotware/ctrader-console:5.9.11`（不使用 latest）
- 加入 `--exit-on-stop`
- 改用 `--data-mode=m1 --data-dir=/work/cache`
- 明確輸出 `--report` 與 `--report-json`

結果：
- `CTRADER_EXIT_CODE=0`
- 回測進度由 0% 正常推進至 98%+
- 產生 report 並上傳 artifact（3 檔）

## 下一步

- 以同一組穩定 backtest 參數套用到 Bar Breakout Trading sanity / 篩選流程，再填入統計欄位。
