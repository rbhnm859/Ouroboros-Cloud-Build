# EURUSD M1 Candidate H 2Y 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_h_2y_core_overlap_threshold130
- Symbol: EURUSD
- Timeframe: M1
- Period: 2024-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_h_2y_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 128.97
- net_profit: 28.97
- return_percent: 28.970000000000002
- profit_factor: 1.124645039153257
- win_rate: 58.333333333333336
- max_drawdown: 20.26776040860547
- total_trades: 384
- average_trade: 0.07544270833333333
- largest_win: 11.8
- largest_loss: -4.08
- gross_profit: 261.39
- gross_loss: 232.42

## Candidate H intent
- Keep Candidate G session and risk structure.
- Raise DeltaThreshold from 125 to 130 to remove marginal weak signals.
- Avoid adding day-of-week filtering before testing a minimal robustness adjustment.

## Debug conclusion
Candidate H completed the two-year threshold-130 validation. Keep it only if it beats Candidate G without reducing trades below the 2Y gate.
