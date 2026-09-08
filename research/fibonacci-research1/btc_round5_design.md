# BTC Round5 — Hierarchical Multi-Timeframe State + Pattern Matrix

Version: `v0.7.0-btc-round5-state-matrix`
Build run: `34221399180`
Build commit: `8c84b994bbd379c936707cdeae789f1dcebeabfd`
Symbol focus: `BITCOIN`
Execution core: H1 Reciprocal ABCD Growth Champion defaults

## Architecture

Round5 does not require every timeframe to show a simultaneous harmonic pattern. The timeframes are hierarchical:

- Macro regime: D1, H4
- Direction/setup: H1, M30
- Confirmation: M15, M5
- Timing: M1

The default decision mode is `MacroVeto`.

A lower-timeframe H1 setup is vetoed only when both valid D1 and H4 states agree in the opposite direction. M30/M15/M5/M1 are recorded as confluence/timing states and do not veto by default. This avoids the zero-trade failure mode observed in Round4 strict H4+H1 coincidence testing.

## Initial pattern mapping

- D1: Gartley, Bat, Butterfly, Crab, Deep Crab
- H4: Gartley, Bat, Crab, Reciprocal ABCD
- H1: Reciprocal ABCD
- M30: Reciprocal ABCD, ABCD
- M15: ABCD, Reciprocal ABCD
- M5: ABCD
- M1: ABCD

These mappings are research defaults, not promoted final parameters. They must be validated by Timeframe × Pattern Matrix backtests.

## State lifecycle

Each timeframe state includes:

- pattern name
- direction
- geometry score
- age in bars
- age-decayed confidence
- structural invalidation price

A state is discarded if it exceeds its timeframe-specific age window or if current price crosses its structural invalidation level.

## Decision modes

- `ObserveOnly`: log the matrix; do not use Round5 states to reject trades.
- `MacroVeto`: D1+H4 opposite-direction agreement can reject an H1 setup. This is the default.
- `WeightedGate`: optional research mode using hierarchical weights. It is not a flat vote and is not the default production decision.

## Diagnostics

Round5 logs deduplicated `[R5 MATRIX]` state changes and `[R5 SNAPSHOT]` confluence snapshots. Rejected macro conflicts are logged as `[R5 SHADOW]` so rejected signals can later be measured instead of silently discarded.

## Risk constraints retained

- Max Open Positions remains controlled by the existing engine (default 1).
- No Grid.
- No Martingale.
- No DCA.
- No Recovery / Loss Averaging.
- No Hedging logic was introduced.

## Next validation

Do not promote Round5 over the Round2 Growth Champion from compilation alone. The next step is a fixed Timeframe × Pattern Matrix and hierarchical cross-test on 3M / 6M / OOS / harsh-cost data, with Buy and Sell statistics separated.
