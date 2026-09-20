# HarmonyBot V42 — Marginal Alpha Opportunity Portfolio & Pattern-Native Execution Engine

V42 is the only active development line. V41/V40/V39/V38/V37/V36 are evidence baselines only.

## Frozen invariants
- H4 macro regime; H1 context/conflict; M15 Harmonic/Fibonacci thesis and PRZ; M5 completed-bar execution evidence/follow-through; M1 broker fill granularity only.
- Fibonacci/Harmonic detector remains the only setup generator.
- Supported profiles: Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Deep Gartley, Rat, Cypher, Shark, 5-0, AB=CD.
- Logical staged Fibonacci Grid is always 0/.236/.382/.618 with 3/7,2/7,1/7,1/7 risk weights. Physical depth may be reduced only by route, broker min-volume, margin and <=1% all-in basket-risk feasibility.
- <=1% total basket risk; MaxActiveBasket=1; anti-hedge; no duplicate opening; server-side protection; daily/max-DD locks; fail-closed min-volume/margin behavior.
- No Martingale, DCA, Recovery, Loss Averaging or forced minimum volume.
- Completed-bar discipline and CanonicalCandidateKey dedupe are mandatory.

## Pre-registered V42 hypotheses
1. PHYSICAL_GRID_REALIZATION: every supported pattern exposes the same four logical Fibonacci levels; executable physical depth is capital/route normalized rather than deleting the entire thesis.
2. OPPORTUNITY_QUEUE: an already admitted executable candidate that loses the single basket slot may remain eligible for one bounded hold interval, but structural invalidation still kills it immediately.
3. PATTERN_NATIVE_COMPETITION: admission thresholds are unchanged. After admission, candidates compete using pattern-native structural evidence so AB=CD does not receive an implicit universal execution-model advantage.
4. OPPORTUNITY_CONVERSION_LEDGER: admission -> grid feasibility -> slot competition -> execution attrition is measured explicitly.

No threshold brute force. No Fresh tuning. DEV diagnostics cannot retune the current V42 run post hoc.

## Fixed DEV families — exactly 12 windows
- LEGACY_REPLAY: V41 legacy lane behavior; all V42 hypotheses off.
- V41_FULL_REPLAY: V41 full dual-lane/follow-through/opportunity-cost behavior; all V42 hypotheses off.
- OPPORTUNITY_GRID: V41 full + four-level physical grid realization + opportunity queue; pattern-native competition off.
- FULL_V42: all registered V42 hypotheses on.
Each family runs DEV-A/B/C independently and in parallel from one immutable compiled .algo.

## Permanent Frequency Admission Gate
Relative to LEGACY_REPLAY, any family with more trades must have:
- added_trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- marginal Net in DEV-A/B/C each >= 0
Otherwise FREQUENCY_EXPANSION_REJECTED.

## Alpha Promotion Gate
- DEV-A/B/C each has trades and Net >= 0
- aggregate Net > 0
- PF >= 1.25
- Expectancy > 0
- Max DD <= 10%
- executable baskets/year >= 50
- Frequency Admission Gate PASS
- engineering_clean=true
- actual basket-risk violations=0
- margin-risk violations=0
- negative-net candidates never promote

## V36 Dominance Gate
The promoted V42 family must also exceed the frozen V36 performance champion:
- executable baskets/year > 51.33
- Net > +648.58
- Expectancy > +8.42/basket
- PF > 1.2124
- Max DD <= 8.77%
- DEV-A/B/C Net each >= 0

## Post-DEV sequence
Only a family that passes both Alpha Promotion and V36 Dominance proceeds to parallel $100/$150/$200/$300/$500/$1000 compatibility. $100 requires baskets>0, Net>0, Expectancy>0, PF>1, DD<=10%, engineering/risk clean. Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair. Both Fresh runs require positive Net, PF>1, Expectancy>0, DD<=10% and engineering clean.
