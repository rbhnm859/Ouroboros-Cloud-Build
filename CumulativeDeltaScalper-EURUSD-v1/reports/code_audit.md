# Code Audit - CumulativeDeltaScalper-EURUSD-v1

## Upstream source

- Repository: https://github.com/dhruuvsharma/Trading-Strategies
- Path: platforms/cTrader/CumulativeDeltaScalper/src/CumulativeDeltaScalper.cs
- Observed blob SHA: 6434e67cce1b9c269775beac8efbca02eb90ab84

## Original design observed

The upstream cTrader source identifies itself as a cTrader/cAlgo port of CumulativeDeltaScalper. The header describes:

- Tick-level uptick/downtick cumulative delta
- Sliding window of N candles
- Cumulative-delta threshold crossover
- Confirmation stack: momentum, M15 EMA, EMA slope, M15 ADX, spread check
- ATR anchored SL/TP
- Session filter, cooldown, daily caps, adverse-delta exit, optional breakeven

## Main issues hardened in this branch

1. OnTick entries were replaced by completed-bar entry decisions. OnTick only counts ticks and manages open positions.
2. EURUSD prefix validation was added. EURUSD, EURUSD.c, EURUSD.raw, EURUSD.r style symbols are allowed by prefix.
3. Timeframe validation was added. M1, M5, M15, M30 are allowed when their toggle is true.
4. One-position-only guard was kept and tightened by label and symbol.
5. Grid, Martingale, DCA, Recovery, Loss Averaging and Hedging are not implemented.
6. Fixed Money Risk mode was added as the default.
7. Broker volume checks were added using min/max and normalization.
8. Daily loss money, daily loss percent, profit target, consecutive-loss and cooldown checks were added.
9. SL/TP are calculated before order send and passed directly into ExecuteMarketOrder.

## Compile caveat

This repository update was created with GitHub connector tools, not inside cTrader Automate. It must be compiled in cTrader Desktop Automate before Cloud/Mobile use.

## Backtest caveat

No real EURUSD broker-data backtest was executed in this ChatGPT environment. Run cTrader backtests for M1/M5/M15/M30 and record results under `backtests/`.
