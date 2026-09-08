# Backtest Summary

## Status

Real cTrader broker-data backtests have not been executed in this ChatGPT/GitHub connector environment.

## Required tests

Run sanity backtests first. Do not brute-force optimize.

| Symbol | Timeframe | Status |
|---|---|---|
| EURUSD | M1 | pending |
| EURUSD | M5 | pending |
| EURUSD | M15 | pending |
| EURUSD | M30 | pending |

## Metrics to record

- Net Profit
- Profit Factor
- Win Rate
- Max Drawdown
- Total Trades
- Average Trade
- Largest Loss
- Largest Win
- Consecutive Losses
- Daily Loss Guard triggered or not
- Duplicate entry detected or not
- Every trade had SL/TP or not
- Broker rejected orders
- InvalidRequest errors
- Volume below broker minimum events

## Decision rule

Only keep a timeframe if it passes safety checks and has enough trades to evaluate. Do not claim profitability unless the actual cTrader report supports it.
