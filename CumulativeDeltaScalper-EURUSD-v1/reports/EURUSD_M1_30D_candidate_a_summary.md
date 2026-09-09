# EURUSD M1 30D Candidate A 回測摘要

- Bot: CumulativeDeltaScalper-EURUSD-v1
- Run type: candidate_a_guarded_fallback
- Symbol: EURUSD
- Timeframe: M1
- Period: 2026-08-10 ~ 2026-09-09 UTC
- cTrader CLI date args: 10/08/2026 ~ 09/09/2026 (DD/MM/YYYY)
- Backtest status: failed_no_report_json
- Debug classification: candidate_a_execution_failed
- Acceptance gate passed: False

## Candidate A Parameters
- DeltaThreshold: 85
- MinConfirmations: 2
- UseBarDeltaFallback: true
- FallbackBelowTickDelta: 3
- BarDeltaPointMultiplier: 2.0
- UseSessionFilter / OverlapOnly: true / true
- HTF EMA filter: true
- ADX Threshold: 12.0
- Min ATR / Max ATR: 0.00005 / 0.00150
- MaxSpreadPoints: 25
- MaxDailyTrades: 12

## Metrics
- initial_balance: 100.0
- final_balance: None
- net_profit: None
- return_percent: None
- profit_factor: None
- win_rate: None
- max_drawdown: None
- total_trades: None
- average_trade: None
- largest_win: None
- largest_loss: None
- gross_profit: None
- gross_loss: None

## Debug conclusion
Candidate A backtest did not complete with a usable JSON report. Inspect console markers before changing strategy logic again.

## Errors / limitations
- cTrader console did not produce backtest/reports/EURUSD-M1-30D-candidate-a.json
