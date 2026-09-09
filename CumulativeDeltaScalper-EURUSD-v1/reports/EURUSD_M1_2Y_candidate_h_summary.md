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
- final_balance: 127.57
- net_profit: 27.57
- return_percent: 27.569999999999993
- profit_factor: 1.1352863241572206
- win_rate: 58.2901554404145
- max_drawdown: 17.128581466156607
- total_trades: 386
- average_trade: 0.07142487046632123
- largest_win: 9.44
- largest_loss: -4.08
- gross_profit: 231.35999999999999
- gross_loss: 203.79

## Candidate H intent
- Keep Candidate G session and risk structure.
- Raise DeltaThreshold from 125 to 130 to remove marginal weak signals.
- Avoid adding day-of-week filtering before testing a minimal robustness adjustment.

## Debug conclusion
Candidate H completed the two-year threshold-130 validation. Keep it only if it beats Candidate G without reducing trades below the 2Y gate.
