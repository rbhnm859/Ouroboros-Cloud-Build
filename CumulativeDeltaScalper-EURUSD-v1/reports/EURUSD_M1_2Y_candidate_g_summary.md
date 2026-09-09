# EURUSD M1 Candidate G 2Y 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_g_2y_core_overlap_hour
- Symbol: EURUSD
- Timeframe: M1
- Period: 2024-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_g_2y_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 132.57
- net_profit: 32.57
- return_percent: 32.56999999999999
- profit_factor: 1.1494516587895196
- win_rate: 59.22330097087378
- max_drawdown: 17.6720351390923
- total_trades: 412
- average_trade: 0.07905339805825243
- largest_win: 9.44
- largest_loss: -4.08
- gross_profit: 250.5
- gross_loss: 217.93

## Candidate G intent
- Keep Candidate F parameters except the trading session.
- Trade only the strongest common 14:00-15:00 UTC core overlap window.
- Validate across two full years instead of only one OOS segment.

## Debug conclusion
Candidate G completed the two-year core-overlap validation. Keep it only if the 2Y gate passes and it improves prior-year OOS versus Candidate F.
