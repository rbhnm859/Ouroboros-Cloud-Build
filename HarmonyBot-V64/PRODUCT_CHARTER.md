# HarmonyBot V64 — XAUUSD Harmonic Product Convergence

V64 returns HarmonyBot to the original commercial product goal.

## Product definition
- XAUUSD only, FxPro cTrader / Mobile / Cloud.
- Harmonic/Fibonacci geometry is the sole trade thesis origin.
- H4 = macro context, H1 = intermediate context, M15 = pattern/PRZ, M1 = execution confirmation.
- London open through New York close, DST-aware.
- One active basket, no hedging, Martingale, DCA, recovery/loss averaging, duplicate thesis, stop widening, or projected-D alpha.
- Whole-basket stressed risk <= 1%.
- Minimum net RR = 2.0.
- $100 small-capital compatibility remains mandatory.

## Three-layer architecture
1. Alpha Engine — detect/qualify harmonic pattern + PRZ + HTF context.
2. Execution Engine — route-native SINGLE / CONDITIONAL_FIBONACCI / INDEPENDENT_RUNNER only.
3. Risk & Commercial Engine — sizing, broker legality, margin, server protection, drawdown/daily protection, single-basket enforcement.

## Deliberate removals
V64 does not contain DAG research selection, Bayesian cell routing, rejected-cohort recovery, occupancy governor, frozen cell policy maps, or post-hoc DEV tuning.

## Execution contract
- Trend-aligned harmonic reversal: Conditional Fibonacci execution plus a 15% independent runner.
- Exhaustion reversal: front-loaded two-leg conditional Fibonacci execution.
- Transition reversal: single entry only.
- Deeper .236/.382 capital is permitted only after thesis re-proof.
- .618 remains shadow-only.
- Runner exists only to preserve right-tail winners; it never rescues losing positions.

## Commercial governance
No feature is retained merely because it is theoretically attractive. A production feature must either create positive alpha or preserve existing alpha without violating risk.

Promotion requires:
- DEV A/B/C all positive.
- Net > 0 and no frequency expansion with non-positive delta Net.
- PF >= 2.0, expectancy >= $20/trade, WR >= 50%, DD <= 6%.
- >= 60 trades/year and <= 90 baskets / 1.5 years under current governance.
- zero execution, actual basket-risk, and margin violations.
- right-tail preservation >= 0.80 against the V51 baseline.
- validation, small-capital, freeze, then untouched Fresh only.

Fresh failure means HOLD and a new major-version decision; no V64.x patch chain.
