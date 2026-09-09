# Round26 — Core Architecture Refactor

Purpose: restructure the proven Round22 BTC engine without changing economics.

## Architecture

The cBot is split into partial-class layers so cTrader still compiles one `.algo` package:

- Signal layer — H1/M30 candidate selection only
- Quality layer — confirmation/quality decisions only
- Regime layer — observational context only in Round26; no veto or resizing
- Risk layer — exact Round22 sizing pass-through
- Execution layer — order routing/protection only

## Frozen trading behavior

Round26 must not change entries, exits, volume, SL/TP, position priority, or risk allocation. Round22 remains the economic anchor.

Frozen constraints:
- MaxOpenPositions=1
- no Grid / Martingale / Hedging / DCA / Recovery / Loss Averaging
- MinPatternScore=84
- MaxPatternAgeBars=16
- MaxEntryDistanceAtr=1.80
- Round22 Balanced risk allocation: H1 Buy 1.15%, H1 Sell 0.80%, M30 Buy 0.40%, M30 Sell 0.50%

## Pre-committed parity gate

The workflow reconstructs and compiles both Round22 and Round26, then runs the same BTC H1 Standard backtests on:

- 2023-09-08 → 2026-09-08
- 2025-09-08 → 2026-09-08

Promotion to a refactor baseline requires normalized trade histories to match exactly for both periods (direction, entry/close time, prices, volume, net, comment), not merely similar headline metrics.

No strategy optimization is allowed until parity passes. Lane-specific H1 Sell / M30 Buy changes belong to the next experiment after this refactor is proven neutral.
