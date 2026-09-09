# EURUSD M1 Candidate J 2Y ROI Guard 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_j_roi_session_guard_2y_100
- Symbol: EURUSD
- Timeframe: M1
- Period: 2024-09-09 ~ 2026-09-09 UTC
- Starting balance: 100
- Backtest status: completed
- Debug classification: candidate_j_2y_trades_triggered
- Promotion gate passed: True

## Metrics
- initial_balance: 100.0
- final_balance: 173.42000000000002
- net_profit: 73.42
- return_percent: 73.42000000000002
- profit_factor: 1.4423158021567564
- win_rate: 63.97306397306397
- max_drawdown: 9.731634589319611
- total_trades: 297
- average_trade: 0.2472053872053872
- largest_win: 8.25
- largest_loss: -3.65
- gross_profit: 239.41
- gross_loss: 165.99
- return_to_drawdown: 7.544467409470744

## Candidate J intent
- Keep Candidate I base-code guards.
- Trim negative final minutes: 14:54-14:59 UTC.
- Maximize return-to-drawdown without increasing leverage or using recovery logic.
