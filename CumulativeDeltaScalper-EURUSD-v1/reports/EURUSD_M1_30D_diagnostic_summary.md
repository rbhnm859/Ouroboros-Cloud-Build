# EURUSD M1 30D Diagnostic 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: diagnostic_bar_delta_fallback
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- cTrader CLI date args: 10/08/2026 ~ 09/09/2026 (DD/MM/YYYY)
- Backtest status: completed
- Debug classification: bar_delta_fallback_trades_triggered

## Metrics
- initial_balance: 100.0
- final_balance: 140.7
- net_profit: 40.7
- return_percent: 40.69999999999999
- profit_factor: 1.2065465617863487
- win_rate: 63.06868867082962
- max_drawdown: 9.020618556701006
- total_trades: 1121
- average_trade: 0.03630686886708296
- largest_win: 1.75
- largest_loss: -2.35
- gross_profit: 237.75
- gross_loss: 197.05

## Debug conclusion
Bar-delta fallback produced trades. The previous zero-trade result was caused by tick-delta not accumulating enough under cTrader CLI m1 data mode and/or too-strict filters.
