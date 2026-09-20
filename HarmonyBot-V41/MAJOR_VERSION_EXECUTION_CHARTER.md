# HarmonyBot V41 — Cross-Validated Marginal Alpha Admission & Pattern Portfolio Engine

V41 replaces V40's broad rank-first frequency expansion with a dual-lane admission architecture.

## Non-negotiable invariant
Increasing executable trade count is permitted only when the added cohort itself has positive historical DEV economics. No version may promote if aggregate Net <= 0, any DEV window Net < 0, or frequency expansion adds a negative marginal cohort.

## Frozen core
- H4 macro regime, H1 context/conflict, M15 harmonic thesis/PRZ, M5 evidence/follow-through.
- M1 remains broker fill-resolution only.
- Fibonacci/Harmonic detector remains core.
- Fibonacci staged grid remains 0/.236/.382/.618 with 3/7,2/7,1/7,1/7 weights.
- Whole basket risk <=1%.
- MaxActiveBasket=1.
- No hedging, Martingale, DCA, Recovery or Loss Averaging.
- V40 thesis-failure management retained.
- Broker realism, min-volume, margin, post-fill, server protection, daily/max-DD locks remain frozen.

## V41 dual lanes
1. CORE_ALPHA: evidence-pass candidate; retains the stricter main path.
2. MARGINAL_RESCUE: evidence-failed candidate may survive only if pre-registered M5 follow-through, evidence, route-fit, stress and marginal edge conditions pass.

## Canonical pairing
Every M15 setup receives CanonicalCandidateKey = Pattern + Direction + CompletionTime + X/A/B/C prices. Cross-family paired analysis uses this key. Duplicate canonical candidates are not re-created.

## Fixed DEV ablations
- LEGACY_REPLAY: rescue OFF, opportunity-cost model OFF, thesis exit OFF.
- CORE_THESIS: rescue OFF, opportunity-cost model OFF, thesis exit ON.
- EDGE_RESCUE: rescue ON, opportunity-cost model OFF, thesis exit ON.
- FULL_V41: rescue ON, opportunity-cost model ON, thesis exit ON.

No brute-force optimization and no Fresh tuning.

## Frequency Admission Gate
For any family that increases trades relative to LEGACY_REPLAY:
- added trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- marginal Net in DEV-A/B/C each >= 0
Otherwise FREQUENCY_EXPANSION_REJECTED.

## Alpha Promotion Gate
- DEV-A/B/C each has trades and Net >=0
- aggregate Net >0
- PF >=1.25
- Expectancy >0
- Max DD <=10%
- executable baskets/year >=50
- Frequency Admission Gate PASS
- engineering/risk clean

Only then: parallel $100/$150/$200/$300/$500/$1000 -> freeze hashes -> exactly one untouched Fresh Alpha + Fresh $100 -> final commercial decision.
