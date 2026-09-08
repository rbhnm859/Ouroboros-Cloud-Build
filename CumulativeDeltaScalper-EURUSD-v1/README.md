# CumulativeDeltaScalper-EURUSD-v1

EURUSD-only hardened cTrader Automate/cAlgo cBot baseline promoted to the cds-eurusd-v1 branch.

## Source and scope

- Source: src/CumulativeDeltaScalper_EURUSD_v1.cs
- Provenance pointer: original/CumulativeDeltaScalper.original.cs
- Allowed symbol: EURUSD and broker suffixes beginning with EURUSD
- Allowed chart timeframes: M1, M5, M15, M30
- Sanity-test parameter preset: presets/eurusd_m1_conservative.json

## Safety rules retained

- No grid, martingale, DCA, recovery, loss averaging, or hedging
- One position only, guarded by symbol and label
- Entry decision once per completed bar
- Every market order includes SL and TP
- Fixed-money-risk mode is the default; broker volume min/max/step checks are applied
- Daily trade/loss/profit limits, consecutive-loss stop, and cooldown guards are applied

## Verification status

The source was reviewed in this task and its delimiter balance is valid. The Replit sandbox has no cTrader Desktop/Automate or cTrader CLI runtime, so no genuine .algo artifact or broker-data backtest is claimed. See reports/build_result.md and reports/EURUSD_M1_backtest_summary.md.
