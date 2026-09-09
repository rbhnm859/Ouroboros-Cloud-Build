# EURUSD M1 30D 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- cTrader CLI date args: 10/08/2026 ~ 09/09/2026 (DD/MM/YYYY)
- Backtest status: completed
- Debug classification: completed_zero_trades

## Metrics
- initial_balance: 100.0
- final_balance: 100.0
- net_profit: 0
- return_percent: 0.0
- profit_factor: None
- win_rate: None
- max_drawdown: 0
- total_trades: 0
- average_trade: None
- largest_win: None
- largest_loss: None
- gross_profit: None
- gross_loss: None

## Debug conclusion
cTrader console 已成功執行並產生 report JSON；日期格式、secrets、登入與基本回測流程已排除錯誤。

目前結果是 0 交易，所以它不是盈利結果，也不是虧損結果；它表示目前保守參數在 2026-08-10 ~ 2026-09-09 的 EURUSD M1 回測內沒有任何進場。

因此目前不適合直接做 ROI 最佳化。下一步應先跑 diagnostic preset，用放寬條件確認策略是否能觸發交易。

## Most likely zero-trade causes
1. 策略條件過嚴：Overlap-only session、DeltaThreshold=300、MinConfirmations=5、HTF EMA、EMA slope、ADX、ATR、spread dynamic 同時啟用。
2. M1 data mode 可能沒有提供足夠 tick-level bid movement，導致 tick delta 不容易累積到門檻。
3. OnBar 進場流程必須同時通過 CheckGuards 與 CheckSignal；任一條件失敗都不會開倉。

## Next debug run
建議新增一個獨立 diagnostic run，不覆蓋正式保守版：
- DeltaThreshold: 20~50
- MinConfirmations: 1~2
- UseSessionFilter: false
- UseHtfEmaFilter: false
- MinAtr: 0
- MaxSpreadPoints: 放寬

如果 diagnostic 仍是 0 交易，問題大概率是 tick-delta source 與 cTrader CLI M1 data mode 不匹配，需要改用 tick data 或改寫 delta 來源。
