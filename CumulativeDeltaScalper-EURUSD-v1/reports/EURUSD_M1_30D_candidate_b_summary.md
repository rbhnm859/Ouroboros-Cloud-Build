# EURUSD M1 30D Candidate B 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_b_drawdown_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_b_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 105.02
- net_profit: 5.02
- return_percent: 5.019999999999996
- profit_factor: 1.1766983456529392
- win_rate: 61.111111111111114
- max_drawdown: 6.620347394540945
- total_trades: 72
- average_trade: 0.06972222222222221
- largest_win: 2.0
- largest_loss: -1.88
- gross_profit: 33.43
- gross_loss: 28.41

## Debug conclusion
Candidate B produced trades with tighter drawdown controls. Use it if it reduces drawdown versus Candidate A while keeping positive return and PF above the gate.
