# EURUSD M1 30D Diagnostic 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: diagnostic_relaxed_filters
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- cTrader CLI date args: 10/08/2026 ~ 09/09/2026 (DD/MM/YYYY)
- Backtest status: completed
- Debug classification: diagnostic_zero_trades_possible_delta_source_issue

## Diagnostic parameters
- DeltaThreshold: 30
- MinConfirmations: 1
- UseSessionFilter: false
- UseHtfEmaFilter: false
- MinAtr: 0
- MaxSpreadPoints: 100
- MaxDailyTrades: 50
- MinSecondsBetweenTrades: 0

## Metrics
- initial_balance: 100.0
- final_balance: 100.0
- net_profit: 0.0
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
Relaxed diagnostic parameters still produced zero trades. This points to tick-delta not accumulating under m1 data mode or another non-filter entry gate blocking signals.
