# EURUSD M1 1Y Candidate D 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_d_1y_drawdown_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2025-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_d_1y_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 116.46000000000001
- net_profit: 16.46
- return_percent: 16.460000000000008
- profit_factor: 1.0957923529069429
- win_rate: 56.55172413793104
- max_drawdown: 25.591551532475766
- total_trades: 290
- average_trade: 0.05675862068965516
- largest_win: 9.45
- largest_loss: -5.07
- gross_profit: 188.29
- gross_loss: 171.83

## Debug conclusion
Candidate D completed the full-year drawdown-guard test. Prefer it over Candidate C only if drawdown improves materially while PF stays above 1.15.
