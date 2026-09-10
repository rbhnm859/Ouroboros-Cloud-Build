# BTC Harmonic Guard Commercial RC1

Status: **RESEARCH RELEASE CANDIDATE — NOT CHAMPION UNTIL ALL GATES PASS**

Base lineage: Round22 Champion -> Round26 parity core -> Store v1 safety -> Growth3 v3.1 -> Commercial RC1.

## Structural changes

- One centralized `ExecuteMarketOrder` boundary for H1, M30 and Growth3.
- One shared equity-percent risk sizing engine with broker min/max/step and estimated-risk validation.
- Shared multi-timeframe regime snapshot (H4/H1/M30 volatility).
- Lane-aware Portfolio Gate before legacy H1/M30 execution.
- Restart-safe directional health circuit breaker reconstructed from cTrader History.
- Growth3 confidence can only reject signals; it cannot increase risk.
- Max one position, no hedging, mandatory SL/TP and checked emergency close remain mandatory.
- No Grid, Martingale, DCA, Recovery or Loss Averaging.
- No date-specific filters and no risk increase to manufacture ROI.

## Frozen commercial promotion gates

RC1 can be promoted only when the actual GitHub Actions artifact proves all of the following on the unchanged validation windows:

- 3Y trades >= 250 (target >= 300, not mandatory).
- 3Y Profit Factor >= 1.40.
- 3Y Max Equity Drawdown <= 18%.
- Recent 1Y Profit Factor >= 1.80.
- Recent 1Y Max Equity Drawdown <= 6%.
- At least 2 positive yearly segments.
- Worst yearly PF >= 0.90 and worst yearly ROI >= -3%.
- Harsh 3Y ROI >= 0 and PF >= 1.00.
- Harsh Recent PF >= 1.35 and Max DD <= 6.8%.
- Growth3 independent attribution must have positive net and PF > 1.00 in both 3Y and Recent if the lane trades.
- Build must compile with 0 errors and generated project must contain exactly one direct `ExecuteMarketOrder` call.

If any gate fails, Round22 remains Champion and RC1 is REJECTED. No candidate may overwrite the Champion by partial success.
