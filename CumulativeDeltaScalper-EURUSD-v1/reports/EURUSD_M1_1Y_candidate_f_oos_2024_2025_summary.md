# EURUSD M1 Candidate F OOS 2024-2025 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_f_oos_2024_2025_session_trim_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2024-09-09 ~ 2025-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_f_oos_2024_2025_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 112.76
- net_profit: 12.76
- return_percent: 12.760000000000005
- profit_factor: 1.0518425222443424
- win_rate: 57.279236276849645
- max_drawdown: 22.335933586202074
- total_trades: 419
- average_trade: 0.030453460620525064
- largest_win: 10.77
- largest_loss: -15.6
- gross_profit: 258.89
- gross_loss: 246.13

## Candidate F OOS intent
- Validate the Candidate F session-trim guard on the previous full year.
- Do not change SL/TP, delta threshold, or risk structure during this OOS check.
- Reject if PF, drawdown, win rate, return, or trade count fail the gate.

## Debug conclusion
Candidate F completed the prior-year OOS test. Keep it only if the prior-year OOS gate also passes.
