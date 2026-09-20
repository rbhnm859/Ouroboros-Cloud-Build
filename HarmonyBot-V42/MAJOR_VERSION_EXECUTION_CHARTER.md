# HarmonyBot V42 — Canonical Harmonic Geometry & Opportunity Portfolio Engine

V42 is the only active development line. V41/V40/V39/V38/V37/V36 are evidence baselines only.

## Objective
Break the V36 performance champion without increasing basket risk. V42 repairs representation bias before attempting frequency expansion.

V36 evidence benchmark:
- executable baskets/year: 51.33
- Net: +648.58
- Expectancy: +8.42/basket
- PF: 1.2124
- Max DD: 8.77%

## Frozen safety / trading invariants
- H4 macro regime; H1 context/conflict; M15 harmonic thesis/PRZ; M5 execution evidence/follow-through; M1 broker fill granularity only.
- Fibonacci/Harmonic detector remains the sole setup origin.
- Logical Fibonacci Grid levels remain 0/.236/.382/.618 with 3/7,2/7,1/7,1/7 risk weights where the pattern profile permits the depth.
- Whole basket risk <=1%.
- MaxActiveBasket=1.
- Anti-hedge, no duplicate opening, server-side protection, min-volume and margin fail-closed, daily/max-DD locks.
- No Martingale, DCA, Recovery, Loss Averaging.
- Completed-bar discipline / no lookahead.
- Negative-net added cohorts never promote.
- Fresh is never used for tuning.

## V42 registered hypotheses
1. CANONICAL_GEOMETRY: explicit AD/XA vs XD/XA coordinate semantics, canonical Cypher scoring, multi-scale completed-bar pivot graph, canonical setup dedupe, logical-vs-physical Grid anchor.
2. PATTERN_NATIVE: pattern execution archetypes and Pattern x Route prior used for ranking rather than veto.
3. FULL_V42: marginal rescue + opportunity-cost edge + one-M5 pre-fill auction on top of the first two hypotheses.

## Fixed DEV families
- V41_REPLAY: all V42 architecture toggles OFF; V41 legacy control behavior.
- CANONICAL_GEOMETRY: canonical geometry + fixed 2/3/5 pivot graph + canonical setup dedupe + logical harmonic grid ON; pattern-native execution and auction OFF.
- PATTERN_NATIVE: CANONICAL_GEOMETRY + pattern-native M5 execution + follow-through/thesis-failure management.
- FULL_V42: PATTERN_NATIVE + marginal rescue + opportunity-cost model + 5-minute opportunity auction.

No brute-force threshold optimization. No post-hoc retuning from DEV folds. No Fresh tuning.

## Twelve pattern definitions
Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Deep Gartley, Rat, Cypher, Shark, 5-0, AB=CD.

All 12 must possess a live detector -> PRZ -> route -> evidence -> Grid -> execution path. A pattern is never forced to trade merely to satisfy diversity.

## Frequency Admission Gate
Relative to V41_REPLAY, any candidate with additional executions must satisfy:
- added_trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >=1.15
- marginal Net in DEV-A/B/C each >=0

Otherwise FREQUENCY_EXPANSION_REJECTED.

## Alpha Promotion Gate
- DEV-A/B/C each has trades and Net>=0
- aggregate Net>0
- PF>=1.25
- Expectancy>0
- Max DD<=10%
- executable baskets/year>=50
- Frequency Admission Gate PASS
- engineering_clean=true
- actual basket risk violations=0
- margin risk violations=0

## V36 Dominance Gate
A V42 development candidate must also exceed:
- executable baskets/year >51.33
- Net >648.58
- Expectancy >8.42
- PF >1.2124
- Max DD <=8.77%
- DEV-A/B/C Net >=0

Only Alpha Promotion PASS + V36 Dominance PASS may enter capital compatibility.

## Capital / Fresh
Run $100/$150/$200/$300/$500/$1000 in parallel.
$100: baskets>0, Net>0, Expectancy>0, PF>1, DD<=10%, engineering/risk clean.
Only then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair.
Both Fresh runs require positive Net, PF>1, Expectancy>0, DD<=10%, engineering clean.
