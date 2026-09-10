# Fibonacci Harmonic Sniper Ultimate v0.4.0 — Pattern Core

## Objective
Make confirmed Fibonacci/Harmonic geometry the only primary signal source. Indicators may confirm, score, or reject a setup, but they never reverse the direction implied by the X/A/B/C/D structure.

## Signal hierarchy
1. Confirm non-repainting pivots.
2. Form alternating X/A/B/C/D windows.
3. Classify bullish/bearish direction from pivot geometry only.
4. Score Fibonacci ratios against the enabled harmonic library.
5. Confirm D/PRZ has not been structurally invalidated.
6. Apply optional candle/EMA/ATR/spread confirmation.
7. Require a valid structure stop and a net reward/risk threshold after execution-cost reserve.
8. Enforce one position per symbol and no opposite exposure.

## Core patterns
- Gartley
- Bat
- Alt Bat
- Butterfly
- Crab
- Deep Crab

Reciprocal ABCD is not an independent trading signal in this version.

## v0.4 engine changes from v0.3.0-fix5
- Incremental confirmed-pivot cache: do not rebuild the full pivot history every closed bar.
- Evaluate only recent XABCD windows after a new confirmed pivot.
- Weighted Fibonacci score with extra emphasis on B and D completion ratios.
- Direction lock: bullish geometry can only Buy; bearish geometry can only Sell.
- D invalidation gate before entry.
- Same-symbol single-position hard gate; no hedging, grid, martingale, DCA, recovery, or loss averaging.
- Static structure SL/TP remains the baseline exit model for clean expectancy measurement before any trailing/breakeven layer is reconsidered.

## Risk model
- Fixed lots, percent-of-equity risk, or fixed cash risk.
- Stop is beyond D plus ATR buffer.
- Broker min/max/step volume normalization.
- Reject trades that exceed the configured maximum stop.
- Reject trades whose Fibonacci target cannot satisfy minimum net R:R after execution-cost reserve.
- Daily loss percent and optional daily loss cash gate.

## Validation gate before calling it a release
A build being profitable on one interval is not enough. The candidate should pass compile, short sanity backtest, standard-cost backtest, harsher-cost backtest, and out-of-sample validation. Optimization should target stability across windows rather than the highest single-window ROI.
