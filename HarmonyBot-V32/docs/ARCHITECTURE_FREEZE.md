# HarmonyBot V32.0 — Fibonacci Harmonic Grid Portfolio Execution Engine

## Major-version policy
- V31 remains frozen. No V31.1, V31.2 or V31 Grid Patch.
- Final source is `HarmonyBot-V32/src/HarmonyBotV32.cs`.
- V32 does not restore V29 Persistent PRZ Queue, V29 GridBasket, V30 Router, Recovery Grid, Martingale, DCA or Loss Averaging.

## Timeframes
- H4: macro regime + active harmonic context.
- H1: intermediate regime + harmonic conflict context.
- M15: only primary harmonic setup generator.
- M1: execution confirmation only.
- Analytical reads use completed bars.

## Fibonacci staged entry
- The grid is a pre-planned staged-entry mechanism, never recovery logic.
- L0=0.000, L1=0.236, L2=0.382, L3=0.618 of anchor-to-structural-stop distance.
- No 0.786/1.000/1.272/1.618 recovery levels.
- Grid plan is frozen before L0 executes.
- L1-L3 are server-side limit orders with expiration and absolute structural protection.
- Whole-basket Development risk cap is 1.0%.
- Default risk weights are 3/7, 2/7, 1/7, 1/7; unused risk is not redistributed.
- Broker minimum volume may cause a leg to be skipped; risk is never increased to force a fill.

## Pattern-specific design
Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Cypher, Shark, 5-0, AB=CD, Deep Gartley and Rat each have explicit grid profiles. Structural invalidation is Fibonacci/pattern geometry based; ATR may describe regime/PRZ width but does not define the stop.

## Routes
- TREND_ALIGNED_REVERSAL: up to 4 legs.
- EXHAUSTION_REVERSAL: up to 2 legs.
- TRANSITION_REVERSAL: up to 2–3 legs causally.
- NO_TRADE / hard conflict: no basket.

## Basket lifecycle
PLANNED -> LEG0_EXECUTED -> GRID_PENDING / PARTIALLY_FILLED -> BASKET_ACTIVE -> BASKET_PROTECTED -> CLOSED, with CANCELLED / EXPIRED / INVALIDATED / RISK_REJECTED / MARGIN_REJECTED / SESSION_EXPIRED terminal paths.
One active basket maximum; no hedge or duplicate leg.

## Pending cancellation
Pending legs are cancelled on TTL expiry, structural invalidation, hard MTF conflict, daily/max-DD lock, institutional-session end, or basket MFE >= +0.50R.

## Winner management
- No-MFE exit only after age >=3m, basket peak <0.15R and basket current <=-0.80R.
- No break-even before 1.0R.
- >=1.0R may protect +0.10R.
- >=1.5R may trail using causal M1 structure and 38.2% Fibonacci retracement.
- Stops may never be widened.

## Development governance
DEV-A/B/C are exposed architecture-verification windows only. Fibonacci levels, pattern availability and thresholds may not be retuned from these results. V32 has one formal candidate; no V32.x rescue.

## Hard gate
3/3 traded, 3/3 PF>1, 3/3 expectancy>0, 3/3 net>0, aggregate positive, DD<=10%, execution errors=0, frequency>=50/year, grid-risk violations=0, duplicate legs=0, orphan pending orders=0, structural-stop widening=0.

Grid-specific comparison uses the actual L0 trades as SingleEntryEquivalent against the actual basket result. If grid increases DD without improving PF/expectancy/MAE efficiency, classify FIBONACCI_GRID_NO_EDGE.

Commercial targets remain targets, not guarantees.
