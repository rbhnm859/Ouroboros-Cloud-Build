# EURUSD M1 1Y Candidate C 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_c_1y
- Symbol: EURUSD
- Timeframe: M1
- Period: 2025-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_c_1y_trades_triggered
- Acceptance gate passed: False

## Candidate C Parameters
- DeltaThreshold: 90
- MinConfirmations: 2
- UseBarDeltaFallback: true
- FallbackBelowTickDelta: 3
- BarDeltaPointMultiplier: 2.0
- UseSessionFilter / OverlapOnly: true / true
- HTF EMA filter: true
- ADX Threshold: 13.0
- Min ATR / Max ATR: 0.00005 / 0.00135
- MaxSpreadPoints: 23
- MaxDailyTrades: 9

## Metrics
- initial_balance: 100.0
- final_balance: 124.65
- net_profit: 24.65
- return_percent: 24.650000000000006
- profit_factor: 1.0336408548734886
- win_rate: 58.87913571910871
- max_drawdown: 42.069140823589414
- total_trades: 1481
- average_trade: 0.01664415935178933
- largest_win: 9.45
- largest_loss: -16.6
- gross_profit: 757.39
- gross_loss: 732.74

## Debug conclusion
Candidate C completed a full-year backtest. Use the acceptance gate and monthly/window checks before treating it as a deployable live candidate.
