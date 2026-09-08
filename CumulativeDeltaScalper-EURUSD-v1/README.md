# CumulativeDeltaScalper-EURUSD-v1

Independent hardened cTrader/cAlgo build derived from:

- Repository: https://github.com/dhruuvsharma/Trading-Strategies
- Source: platforms/cTrader/CumulativeDeltaScalper/src/CumulativeDeltaScalper.cs

## Scope

This version is prepared as an EURUSD-only scalper baseline for cTrader Automate / cTrader Cloud / cTrader Mobile.

Allowed chart timeframes:

- M1
- M5
- M15
- M30

The bot is intentionally conservative and should be compiled and backtested in cTrader Desktop before any cloud/mobile use.

## Safety rules

- No Grid
- No Martingale
- No DCA
- No Recovery / Loss Averaging
- No Hedging
- One position only
- Entry decision once per completed bar
- Every entry must include SL and TP
- Fixed Money Risk mode included
- Broker min/max/step volume checks included
- Daily loss / profit target / consecutive-loss / cooldown guards included

## Important status

This repository commit contains source and reports only. It does **not** include a confirmed `.algo` artifact because this ChatGPT environment does not have cTrader Automate / cTrader CLI available to compile cBots. Real EURUSD M1/M5/M15/M30 backtests must be run inside cTrader with broker data.
