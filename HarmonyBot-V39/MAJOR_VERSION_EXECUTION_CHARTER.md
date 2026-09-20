# HarmonyBot V39 — Regime-Conditioned Harmonic Portfolio

V39 is a major-version replacement of the V38 execution selector, not a V38.x patch.

## Architecture
- H4: macro regime / structural context.
- H1: harmonic context / MTF conflict.
- M15: harmonic thesis, XABCD geometry, PRZ, structural invalidation, route, canonical targets.
- M5: execution evidence stream only.
- M1: simulation fill granularity only; never a strategy decision timeframe.

## New decision layer
V39 introduces three monotonic, interpretable portfolio controls:
1. Regime Portfolio Selector — combines harmonic robustness, MTF fit, execution evidence, regime score and canonical net RR.
2. Route Specialization — different structural requirements for TREND_ALIGNED, EXHAUSTION and TRANSITION routes.
3. Stress Quarantine — blocks high-stress states without changing risk sizing or weakening protections.

## Registered DEV families
- BASELINE_CONTROL: all V39 portfolio controls disabled.
- REGIME_SELECTOR: regime selector + stress quarantine.
- ROUTE_SPECIALIZED: route specialization + stress quarantine.
- FULL_PORTFOLIO: all three controls.

No brute-force search and no fresh-validation tuning.

## Non-negotiable positive-net gate
A candidate cannot be promoted unless:
- Aggregate DEV Net Profit > 0.
- Every DEV window A/B/C has Net Profit >= 0.
- Expectancy > 0.
- PF >= 1.10.
- Max DD <= 10%.
- Worst-window PF >= 0.80.
- Executable baskets/year >= 50.
- engineering_clean=true.

Negative-net candidates are rejected even if frequency, PF in one window, or win rate looks attractive.

## Frozen safety
Basket risk <=1%; no hedging; no Martingale; no DCA; no Recovery; no Loss Averaging; server-side protection; min-volume fail-closed; margin/free-margin guards; all-in L0 risk normalization; anti-duplicate; completed-bar discipline.

## Promotion sequence
DEV-A/B/C -> positive-net gate -> $100/$150/$200/$300/$500/$1000 compatibility -> source/hash/preset freeze -> exactly one untouched Fresh Validation package -> final regression.
