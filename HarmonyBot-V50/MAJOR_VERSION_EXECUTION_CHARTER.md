# HarmonyBot V50 — Pattern-Native Structural Risk & Grid Contract Engine

## Evidence basis
V49 reproduced V46 SCALE_CONTROL exactly: 39 independent baskets / 1.5y, Net +1721.72, PF 2.1833, Expectancy +44.15, WR 51.28%, Max DD 4.56%, A/B/C positive.

V49 FAMILY_COMPLETION_ONLY proved dormant families can pass pattern-native completion:
Gartley 14, Bat 3, Alt Bat 3, Butterfly 4, Crab 6, Deep Crab 10, Deep Gartley 6, Rat 29, 5-0 1.
Yet all standard dormant-family passes were immediately rejected by FIB_GRID_PLAN_REJECTED and produced 0 Armed / 0 Executed.

## Root cause
The legacy grid gate mixes incompatible coordinate semantics:
- Retracement families such as Gartley/Bat have D-to-X structural risk distances around 0.1–0.25 XA, while legacy MinimumGridSpanXa values are 0.65–0.75, making acceptance mathematically impossible.
- Extension families use AD/XA but legacy structural invalidation converts it as X ± XadMax*XA. Correct X-space conversion is X ± (1-XadMax)*XA. The legacy formula displaces the stop by roughly one full XA, then the grid max-span gate rejects the candidate.
Thus the system can detect and confirm those patterns yet still structurally block execution.

## Frozen
Confirmed-D, M15 thesis, M1 execution, H4/H1 context, V46 scale-route admission, V49 family completion evidence, exits, Fibonacci grid fractions 0/.236/.382/.618, 3/7-2/7-1/7-1/7 weights, <=1% basket risk, MaxActiveBasket=1, setup dedupe, no hedging/Martingale/DCA/Recovery/Loss Averaging, server-side protection, broker min-volume/margin fail-closed, no lookahead.

## V50 reforms
1. Grid Span Semantic V2: legacy XA minimum/maximum span is not applied to structural stop distance. PRZ legality, physical risk, broker feasibility and remaining RR remain hard gates.
2. Structural Invalidation V2 for extension families: convert AD/XA completion to the correct X-space coordinate using X + (1-r)*XA for bullish and X - (1-r)*XA for bearish before buffer.
3. Explicit grid rejection telemetry for PROFILE, STOP_DISTANCE, LEGACY_XA_SPAN, ROUTE_LEGS, NO_LEGAL_L0_IN_PRZ, CAPITAL_EXECUTION, NO_PHYSICAL_L0, TARGET_RR.
4. No risk increase, no SL removal, no threshold sweep.

## Fixed DEV
Exactly 12:
- V46_SCALE_CONTROL × A/B/C
- FAMILY_COMPLETION_ONLY × A/B/C
- GRID_SEMANTIC_V2 × A/B/C
- FULL_V50_COMMERCIAL × A/B/C

## Commercial gate
Baseline must reproduce.
Candidate requires >=90 independent baskets /1.5y, >=60/year, Net>=1800, PF>=2.0, Expectancy>=20, WR>=50%, MaxDD<=6%, A/B/C positive, engineering/risk clean, duplicate setup=0, added cohort vs control Net/Expectancy positive, PF>=1.20, and marginal Net A/B/C each >=0.

Only after DEV pass: actual $100/$150/$200/$300/$500/$1000 validation -> immutable hashes -> exactly one untouched Fresh Alpha + one Fresh $100.

Execution registration: V50 fixed structural-grid workflow armed.
