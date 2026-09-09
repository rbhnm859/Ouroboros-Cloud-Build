# EURUSD M1 1Y Candidate F 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_f_1y_session_trim_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2025-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_f_1y_trades_triggered
- Acceptance gate passed: True

## Metrics
- initial_balance: 100.0
- final_balance: 125.33
- net_profit: 25.33
- return_percent: 25.33
- profit_factor: 1.1857719105243858
- win_rate: 56.540084388185655
- max_drawdown: 15.414196442877733
- total_trades: 237
- average_trade: 0.10687763713080169
- largest_win: 9.45
- largest_loss: -2.88
- gross_profit: 161.68
- gross_loss: 136.35

## Candidate F intent
- Return to Candidate D risk/RR structure.
- Trim the negative 15:00-15:30 UTC segment observed in Candidate D trade diagnostics.
- Avoid Candidate E aggressive RR settings that collapsed win rate.

## Debug conclusion
Candidate F completed the full-year session-trim test. It should beat Candidate D on PF and drawdown by removing the negative 15 UTC segment.
