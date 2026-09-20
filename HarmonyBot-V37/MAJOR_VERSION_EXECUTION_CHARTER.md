# HarmonyBot V37 — M15 Intraday Harmonic Portfolio Architecture

## Major-version mandate
V37 is a major architecture replacement. Do not create V36.x or V37.x patch chains for alpha research.

## Timeframe contract
- H4: macro regime and structural context.
- H1: intermediate harmonic context and conflict classification.
- M15: primary harmonic detection, PRZ lifecycle, confirmation, candidate arbitration and default execution decisions.
- M5: optional execution refinement only; it must be proven by DEV ablation.
- M1: not a strategy timeframe and not a mandatory confirmation layer. Broker backtest data may still use M1 granularity for fill realism.

## Alpha/frequency architecture
- Fibonacci/Harmonic remains the core alpha thesis.
- Structured Recall is retained as the best V36 frequency/edge mechanism.
- Broad Dynamic Reroute is not promoted because it increased frequency while diluting PF/expectancy.
- V37 tests only qualified reroute candidates that retain strong geometry, PRZ, confidence, time symmetry, pivot quality, non-conflict MTF state and healthy regime conditions.
- Deferred candidate retention and frequency-aware arbitration remain available.
- No frequency gain may come from higher risk, forced minimum volume, weaker protection, Martingale, DCA, Recovery, Loss Averaging or Hedging.

## Risk contract
- Total basket risk <= 1%.
- Max DD protection remains active.
- Daily loss protection remains active.
- Server-side protection remains mandatory.
- Anti-hedge and duplicate-entry protection remain mandatory.
- Broker minimum volume, margin and free-margin feasibility are fail-closed.
- $100 remains the minimum supported-capital target; capital compatibility is tested only after a DEV alpha/frequency candidate exists.

## Validation contract
1. Static architecture audit.
2. Compile with zero errors.
3. Short smoke backtest.
4. DEV-A/B/C fixed ablation:
   - M15_CORE
   - M15_QUALIFIED_REROUTE
   - M15_M5_REFINEMENT
   - M15_COMBINED
5. Select only a robust positive-edge candidate.
6. Capital compatibility.
7. Freeze.
8. One untouched fresh validation.
9. Commercial release decision.

## Breakthrough definition
Major breakthrough requires either:
- >= 2x V35.1 executable annualized frequency while positive expectancy, DD <= 10%, engineering clean and cross-window viability remain; or
- first robust candidate >= 100 executable baskets/year.
