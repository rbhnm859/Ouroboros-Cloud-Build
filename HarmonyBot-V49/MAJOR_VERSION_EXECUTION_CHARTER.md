# HarmonyBot V49 — Harmonic Family Completion & Confirmation Kernel

## Authority
V49 starts from V48 HOLD_WITH_EVIDENCE at commit `5ba9a6dc005ab8810db67309e388a89a28c99122`. It does not reopen V31–V48 research.

## Preregistered root-cause hypothesis
The dominant bottleneck is Pattern/Route/Scale × Confirming→Armed. V48's "pattern-native" M1 path was still a rigid four-stage ordered FSM constrained to 3–4 completed M1 bars. That experiment therefore did not test an order-independent family-native evidence window.

## Frozen incumbent Alpha
V46 SCALE_CONVERSION remains immutable control. Confirmed-D M15 thesis, H4/H1 context, M1 execution clock, canonical coordinates, route admission, setup dedupe, MaxActiveBasket=1, 0/.236/.382/.618 staged Fibonacci grid, 3/7-2/7-1/7-1/7 basket weights, <=1% basket risk, server-side protection, broker/margin/min-volume fail-closed logic, exits and Fresh/OOS are frozen.

AB=CD and Shark remain on the incumbent confirmation lane. No Projected-D, queue-frequency recovery, repeated same-thesis entries, martingale, DCA, recovery, loss averaging or forced minimum volume is allowed.

## Counterfactual confirmation forensics
At PRZ touch V49 records executable anchor and structural risk. Each completed M1 records legacy score plus first timestamps for directional close, reclaim, BOS1/BOS2, rejection, failed extension, liquidity sweep, displacement and close-back-inside evidence. Shadow outcomes record MFE/MAE, first 1R, 2R, SL, Target1 and Target2 timestamps.

A shadow setup is positive only when 2R is observed on an earlier completed M1 bar than SL. It is negative only when SL is earlier than 2R. Same-bar 2R/SL is ambiguous and never promoted to positive.

### Forensics integrity correction
Counterfactual price-path tracking uses a fixed 180-minute post-PRZ horizon and continues after planner rejection, candidate expiry, or candidate invalidation for candidates that never reach ARMED. Candidate terminal reason/time remains separately recorded. The shadow path stops on structural 1R SL, or after both 2R and canonical Target2 have been observed, or at the fixed horizon. This is instrumentation-only: it cannot create orders, relax the shared grid, alter risk, or change incumbent Alpha. Every CF start must end in exactly one of two mutually exclusive buckets: (a) the setup later reaches ARMED, in which case it is no longer a missed-confirmation counterfactual and receives no CF terminal record; or (b) it never reaches ARMED and must have exactly one terminal CF shadow record. Analyzer integrity therefore requires `CF starts = later-Armed + terminal never-Armed CF records`.

## Order-independent native evidence window
Window is fixed at 12 completed M1 bars; no threshold sweep.

- RETRACEMENT_NATIVE: Gartley, Bat, Deep Gartley, Rat = rejection + reclaim + (BOS1 or displacement), any order.
- EXTENSION_NATIVE: Alt Bat, Butterfly, Crab, Deep Crab = sweep + close-back-inside + failed continuation + (BOS1 or displacement), any order.
- XC_NATIVE: Cypher = rejection + reclaim + (BOS1 or displacement), any order; research lane only in FULL_V49.
- IMPULSE_TRANSITION_NATIVE: 5-0 = sweep + failed continuation + reclaim + (BOS1 or displacement), any order; research lane only in FULL_V49.
- Shark alternate lane is shadow-only; incumbent Shark execution remains unchanged.
- AB=CD execution remains unchanged.

## Fixed DEV — exactly 12
1. V46_SCALE_CONTROL × A/B/C
2. COUNTERFACTUAL_NATIVE_CONFIRM × A/B/C
3. PROVEN_PLUS_NATIVE_LANES × A/B/C
4. FULL_V49_COMMERCIAL × A/B/C

A=2021 H1, B=2021 H2, C=2022 H1. Control must reproduce 39 baskets, +1721.72 net, PF 2.1833, expectancy 44.15, WR 51.28%, DD 4.56% before Alpha analysis.

## Promotion gate
Commercial DEV candidate requires >=90 independent baskets/1.5y, >=60/year, Net>=1800, PF>=2.0, Expectancy>=20, WR>=50%, DD<=6%, A/B/C positive, positive aggregate marginal cohort, each A/B/C marginal cohort net>=0, duplicate setup=0, execution/risk/margin/unprotected violations=0.

Capital, freeze and one-time Fresh pair are conditional on this gate. Fresh is never used for tuning.
