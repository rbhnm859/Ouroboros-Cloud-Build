# EURUSD M1 30D Candidate A 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_a_guarded_fallback
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_a_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 113.45
- net_profit: 13.45
- return_percent: 13.450000000000003
- profit_factor: 1.3278888347147733
- win_rate: 66.66666666666666
- max_drawdown: 13.864720740948622
- total_trades: 111
- average_trade: 0.12117117117117117
- largest_win: 2.0
- largest_loss: -2.2
- gross_profit: 54.47
- gross_loss: 41.02

## Debug conclusion
Candidate A produced trades with guarded fallback. Compare trade count, profit factor, win rate and drawdown against the loose fallback diagnostic.
