# EURUSD M1 1Y Candidate E 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_e_1y_tail_risk_rr_guard
- Symbol: EURUSD
- Timeframe: M1
- Period: 2025-09-09 ~ 2026-09-09 UTC
- Backtest status: completed
- Debug classification: candidate_e_1y_trades_triggered
- Acceptance gate passed: False

## Metrics
- initial_balance: 100.0
- final_balance: 64.58
- net_profit: -35.42
- return_percent: -35.42
- profit_factor: 0.7919285672325678
- win_rate: 39.08045977011494
- max_drawdown: 48.23794502027934
- total_trades: 261
- average_trade: -0.1357088122605364
- largest_win: 9.45
- largest_loss: -5.07
- gross_profit: 134.81
- gross_loss: 170.23

## Candidate E intent
- Lower fixed money risk and daily loss guard to reduce equity damage from tail losses.
- Reduce SL ATR multiplier and raise TP ATR multiplier to improve payoff structure.
- Keep entry quality filters strict enough to avoid Candidate C overtrading but less destructive than simply filtering everything out.

## Debug conclusion
Candidate E completed the full-year tail-risk/RR test. Compare it to Candidate D by PF, drawdown, return, and trade count before keeping it.
