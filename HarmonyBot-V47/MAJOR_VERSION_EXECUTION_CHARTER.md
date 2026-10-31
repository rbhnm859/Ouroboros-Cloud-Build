# HarmonyBot V47 — Alpha-Preserving Throughput & Serial Opportunity Engine

## Frozen Alpha baseline
V47 inherits V46 SCALE_CONVERSION and must reproduce:
- 39 independent baskets / 1.5y
- 26.00/year
- Net +1721.72 USD
- PF 2.1833
- Expectancy +44.15 USD
- Win Rate 51.28%
- Max DD 4.56%
- DEV A/B/C Net all positive
- duplicate executed setup = 0
- engineering/risk clean

If V46_SCALE_CONTROL does not reproduce this within rounding tolerance, stop Alpha interpretation and repair experiment isolation only.

## Alpha kernel frozen
No performance-driven changes to:
- confirmed-D harmonic thesis
- H4/H1 context
- M15 harmonic detection
- M1 execution clock
- canonical standard AD/XA coordinates
- V46 secondary-scale route admission
- staged Fibonacci grid 0/.236/.382/.618
- 3/7,2/7,1/7,1/7 intended basket weights
- <=1% basket risk
- MaxActiveBasket=1
- no hedging, same-setup re-entry, Martingale, DCA, Recovery or Loss Averaging
- server protection, min-volume, margin/free-margin, daily risk, max-DD, completed-bar/no-lookahead
- current exit/target policy

Projected-D is prohibited as primary architecture. M5 may not replace M1 as the primary execution clock.

## V47 throughput mechanisms
1. Persistent Armed Opportunity Queue:
   ARMED -> SLOT_BLOCKED -> PARKED -> REVALIDATING -> EXECUTABLE -> EXECUTED
   or terminal fail-closed states.
   Parked candidates create no broker pending order and reserve no risk or margin.
2. Hard thesis validity + fixed 180-minute maximum parked lifetime.
3. Event-driven serial handoff immediately after a basket fully closes.
4. Mandatory current-quote grid/risk/RR/broker revalidation before delayed execution.
5. Pattern-native finite-state completed-M1 confirmation across max 4 bars.
6. Opportunity decay ranking with deterministic structural/evidence/freshness penalties; no Fresh-trained weights.
7. Shadow opportunity ledger and slot-occupancy telemetry.

## Fixed DEV design
Exactly 12 DEV jobs:
- V46_SCALE_CONTROL x A/B/C
- QUEUE_RECOVERY x A/B/C
- NATIVE_M1_EXPANSION x A/B/C
- FULL_V47_COMMERCIAL x A/B/C

No threshold sweep.

## Historical all-metric dominance
Candidate must beat V36 in every verified metric:
- baskets >77
- >51.33/year
- Net >648.58
- PF >1.2124297856
- Expectancy >8.4231
- WR >42.857%
- DD <8.7683%
- A/B/C positive
- duplicate setup = 0
- engineering/risk clean

## Commercial Freeze Candidate
- >=90 independent baskets / 1.5y
- >=60/year
- Net >=1800
- PF >=2.0
- Expectancy >=20
- WR >=50%
- DD <=6%
- A/B/C positive
- zero execution/risk/margin/unprotected violations
- no repeated executed setup
- FULL candidate added cohort vs V46_SCALE_CONTROL: trades>0, Net>0, Expectancy>0, PF>=1.20, marginal Net A/B/C >=0

## Stretch reporting
Report >=120 baskets /1.5y, >=80/year, Net>=2500, PF>=2.2, Exp>=20, WR>=50%, DD<=6%, plus progress to 200/year, PF2.5, WR65%, realized RR>=2, annual return>=100%, 10/12 profitable months. Stretch goals never override risk or data governance.

## Capital/Fresh
Only Commercial Freeze Candidate PASS may run $100/$150/$200/$300/$500/$1000.
$100 must be actually executable and positive with PF>1, Exp>0, DD<=10%, risk/margin clean and no forced min-volume risk expansion.
Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair.
Fresh never tunes V47.
Final outcomes: COMMERCIAL_FREEZE_CANDIDATE_PASS or HOLD_WITH_EVIDENCE.
