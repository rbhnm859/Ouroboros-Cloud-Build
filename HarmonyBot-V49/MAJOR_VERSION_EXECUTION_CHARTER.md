# HarmonyBot V49 — Pattern-Native Completion Contract Engine

## Evidence basis
V48 proved the V46 SCALE_CONTROL still reproduces 39 independent baskets / 1.5y, Net +1721.72, PF 2.1833, Expectancy +44.15, WR 51.28%, Max DD 4.56%, A/B/C positive.

V48 FULL funnel showed dormant-family Confirming counts without executions: 5-0 8, Alt Bat 3, Butterfly 4, Crab 9, Deep Crab 16, Deep Gartley 7, Gartley 15, Rat 31, Bat 3. Total = 96 Confirming opportunities. V48 PatternNativeTemporalPass was zero for every family.

## Root-cause hypothesis
1. Pattern identity contracts are too broad for several canonical families; e.g. legacy Bat permits BC 1.13 even though canonical Bat requires >=1.618.
2. Completion confirmation is structurally biased: a family-agnostic single-M1 score is the primary gate.
3. The prior native FSM was effectively over-constrained: four ordered stages in at most four completed M1 bars, one state transition per bar. It produced zero native passes.
4. Therefore zero executions in dormant families cannot yet be interpreted as zero market alpha.

## Frozen proven lane
AB=CD, Shark and Cypher keep the V46 legacy completion lane in V49. Confirmed-D, M15 thesis, M1 execution, H4/H1 context, scale-route admission, exits, grid, <=1% basket risk, MaxActiveBasket=1, no duplicate execution, no hedging/Martingale/DCA/Recovery/Loss Averaging, server protection, min-volume/margin fail-closed and completed-bar/no-lookahead are frozen.

## V49 reform
- Canonical family identity contracts for Gartley/Bat/Alt Bat/Butterfly/Crab/Deep Crab.
- Deep Gartley and Rat remain project-specific experimental families but their pipeline stays operational and attributable.
- Standard-family AB=CD compatibility becomes family-specific.
- Dormant families use a six-completed-M1 evidence accumulator, not a one-bar universal score and not a four-bars/four-stages exact sequence.
- Compatible evidence may coexist on one completed bar; this is not lookahead.
- No threshold sweep.

## Fixed DEV
Exactly 12:
- V46_SCALE_CONTROL × A/B/C
- FAMILY_COMPLETION_ONLY × A/B/C
- CANONICAL_IDENTITY_ONLY × A/B/C
- FULL_V49_COMMERCIAL × A/B/C

## Commercial gate
Baseline must reproduce.
Candidate requires >=90 independent baskets /1.5y, >=60/year, Net >=1800, PF >=2.0, Expectancy >=20, WR >=50%, MaxDD <=6%, A/B/C positive, engineering/risk clean, no duplicate setup, and added cohort vs control Net/Expectancy positive, PF>=1.20, with marginal Net A/B/C each >=0.
Family plumbing must be explicit: canonical-family Confirming opportunities cannot disappear silently; each evaluated family must produce contract-pass or explicit contract-window-reject telemetry.

Only after DEV gate passes: $100/$150/$200/$300/$500/$1000 actual executable validation -> immutable hashes -> exactly one untouched Fresh Alpha + one Fresh $100.
