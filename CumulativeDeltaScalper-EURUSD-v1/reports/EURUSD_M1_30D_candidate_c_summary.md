# EURUSD M1 30D Candidate C 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_c_balanced_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_c_trades_triggered
- Acceptance gate passed: True

## Metrics
- initial_balance: 100.0
- final_balance: 116.45
- net_profit: 16.45
- return_percent: 16.450000000000003
- profit_factor: 1.5070900123304563
- win_rate: 68.08510638297872
- max_drawdown: 5.742994100294965
- total_trades: 94
- average_trade: 0.175
- largest_win: 2.0
- largest_loss: -2.2
- gross_profit: 48.89
- gross_loss: 32.44

## Debug conclusion
Candidate C produced trades with balanced controls. Prefer it over A or B only if it passes both the profit-factor and drawdown gates.
