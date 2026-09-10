# CumulativeDeltaScalper EURUSD K2 — Engineering Audit

## Lineage

- Original Candidate K source commit: `ca6d78774eb7f772d32e19e537a9584a5cfc5400`
- Reproducible K workflow commit: `5e78965d273a6c07a6a0db00a09fc26a18d14e41`
- Cost decomposition commit: `d019ed2395c8a714294dffac96cc41779649df19`
- Latest one-pass commercial validation commit: `20f3e3b24c07f956ce4ea3789ae1affcebebdc9b`
- Latest one-pass run: `34468926999` (completed successfully at workflow level)

Original K remains preserved and unmodified. K2 is isolated under `CumulativeDeltaScalper-EURUSD-v1/k2/`.

## Original K engineering findings

- `AccessRights.None` present.
- Uses `ExecuteMarketOrder` with SL/TP supplied at entry.
- Uses `ModifyPosition` for breakeven.
- Uses `VolumeForFixedRisk` and `NormalizeVolumeInUnits` with broker min/max checks.
- Uses `Symbol.MinStopLossDistance` / `Symbol.MinTakeProfitDistance` checks.
- Entry processing is driven from `OnBar`; fallback delta uses `Bars.ClosePrices.Count - 2`, so it references the just-closed bar rather than a future bar.
- One-position protection is label+symbol based.
- Spread points conversion in Original K is `Symbol.Spread / Symbol.TickSize`.
- Daily P/L and trade count are reconstructed from history, but several runtime-only fields in Original K are not fully reconstructed after restart.
- Original K initializes `_accountPeakEquity` from current equity on restart, therefore account-wide peak DD continuity cannot be fully reconstructed from broker history alone. K2 preserves the guard but this restart limitation is explicitly documented.

## K2 allowed structural changes only

1. Cost-aware trade gate. The expected move is the ATR-based TP distance. Estimated round-trip cost includes live spread, commission-equivalent pips, and a small execution buffer. Entry is blocked when `ExpectedMove / EstimatedTotalCost < 2.0`.
2. ATR-based breakeven. Trigger defaults to `0.5 ATR` instead of a fixed 1-pip trigger. A small positive buffer is allowed to reduce commission-negative breakevens.
3. Adverse-delta exit moved to completed-bar confirmation. It requires adverse cumulative delta and an adverse closed candle that has moved beyond entry in the wrong direction.

No new technical indicator, strategy module, averaging, hedging, grid, martingale, DCA, recovery, loss averaging, Fibonacci, RSI, MACD, Bollinger or ML logic is introduced.

## Cost-model verification requirement

The GitHub Actions workflow captures `ctrader-console backtest --help` output for `spread`, `commission`, and `leverage`, and backtest JSON metadata must be checked before promotion.

`--spread=0.43` and `--commission=35` must not be treated as commercially valid until the generated report confirms the intended interpretation. If the CLI unit differs from the assumed unit, only the test harness may be corrected; strategy parameters must not be altered to compensate.

K2's internal commission estimate is parameterized separately as `CommissionUsdPerMillion=35`. The estimate converts EURUSD notional to USD using current mid price and converts commission money to pips using `Symbol.PipValue * volume`.

## Commercial validation discipline

- IS: 2024-09-09 through 2025-09-08
- OOS: 2025-09-09 through 2026-09-09
- Full: 2024-09-09 through 2026-09-09
- EURUSD M1, USD 30, leverage 1:500
- Baseline spread CLI value: 0.43
- Commission CLI value: 35 USD per million USD volume, subject to metadata verification
- No OOS retuning
- No zero-cost promotion evidence
- No DD-guard disabling

Promotion is prohibited unless OOS, Full, cost stress, robustness, and Monte Carlo gates all pass.
