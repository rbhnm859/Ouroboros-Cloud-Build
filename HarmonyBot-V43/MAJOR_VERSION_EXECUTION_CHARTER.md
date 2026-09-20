# HarmonyBot V43 — Pattern-Native Structural Routing Portfolio

V43 is the only active development line. V42/V41/V40/V39/V38/V37/V36 are evidence baselines only.

## Objective
V43 must increase *executable profitable opportunity*, not merely signal count. It specifically tests whether V42's binary route rejection and short wall-clock candidate lifetime discard structurally valid Harmonic/Fibonacci opportunities that can survive M5 evidence, risk, execution and marginal-profit gates.

## Frozen architecture and safety invariants
- H4 macro regime.
- H1 context/conflict.
- M15 Harmonic/Fibonacci thesis and PRZ.
- M5 execution evidence and follow-through.
- M1 is broker data/fill granularity only.
- Fibonacci/Harmonic detector remains the core thesis engine.
- Logical Fibonacci Grid remains 0/.236/.382/.618.
- Basket risk weights remain 3/7, 2/7, 1/7, 1/7.
- Total basket risk <=1%.
- All-in L0 normalization remains fail-closed.
- MaxActiveBasket=1.
- anti-hedge and duplicate-entry prevention remain mandatory.
- server-side protection remains mandatory.
- broker min-volume, margin and free-margin checks remain fail-closed.
- daily/max-DD locks remain mandatory.
- no Martingale, DCA, Recovery or Loss Averaging.
- completed-bar discipline remains mandatory.
- V42 conversion/replan/fallback safety architecture is retained.

## V43 structural hypotheses
H1 — Structural Route Watch:
A detected and validated pattern that has no instantaneous route is not automatically invalid. It may remain in ROUTE_WATCH until structural invalidation, thesis consumption or session expiry. It may become routable when macro/context state changes.

H2 — Event-Driven Candidate Lifetime:
A Harmonic thesis is not discarded solely because 90–120 wall-clock minutes have elapsed. It remains eligible until structural invalidation, session expiry, or pre-entry canonical T1 consumption. This does not authorize stale entry after the original opportunity has already paid out.

H3 — Cross-Regime Route Refresh:
Before PRZ touch, a live candidate may change its route classification when H4/H1/M15 context materially changes. This is classification refresh, not threshold optimization.

H4 — Pattern-Native M5 Evidence:
Pattern families use fixed, pre-registered M5 evidence semantics:
- extension families emphasize failed extension, rejection and BOS;
- retracement families emphasize reclaim and BOS;
- 5-0 emphasizes BOS and failed extension;
- Cypher emphasizes reclaim;
- AB=CD emphasizes post-completion BOS and displacement.
The existing evidence threshold remains fixed. V43 does not brute-force weights or thresholds.

## Fixed DEV families
Exactly four families:
1. V42_REPLAY — V43 route-watch OFF; event lifetime OFF; pattern-native evidence OFF; route refresh OFF.
2. ROUTE_WATCH — route-watch ON; route refresh ON; event lifetime OFF; pattern-native evidence OFF.
3. STRUCTURAL_LIFETIME — route-watch ON; route refresh ON; event lifetime ON; pattern-native evidence OFF.
4. FULL_V43 — route-watch ON; route refresh ON; event lifetime ON; pattern-native evidence ON.

All four families keep the same V42 FULL stack otherwise: marginal rescue ON, opportunity-cost model ON, follow-through ON, thesis exit ON, conversion/replan/fallback ON. No extra family may be created after seeing DEV.

## Permanent Frequency Admission Gate
Versus V42_REPLAY, every expansion family must satisfy:
- added_trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- DEV-A marginal Net >=0
- DEV-B marginal Net >=0
- DEV-C marginal Net >=0
Otherwise mark FREQUENCY_EXPANSION_REJECTED.

Negative-net added cohorts never promote even if total trade count rises sharply.

## Alpha Promotion Gate
All must pass:
- DEV-A/B/C each baskets >0 and Net >=0
- aggregate Net >0
- PF >=1.25
- Expectancy >0
- Max DD <=10%
- executable baskets/year >=50
- Frequency Admission Gate PASS
- engineering_clean=true
- execution_errors=0
- actual basket risk violations=0
- margin risk violations=0

## V36 Dominance Gate
V36 Structured Recall remains the champion to beat:
- executable baskets/year >51.33
- aggregate Net >648.58
- aggregate Expectancy >8.42/basket
- PF >1.2124
- Max DD <=8.77%
- DEV-A/B/C each Net >=0

A V43 family that merely beats V42 but does not beat V36 does not advance to capital compatibility.

## DEV-only diagnostics
Report:
- Pattern signal-to-execution funnel.
- route-watch admissions and recoveries.
- route refresh count.
- session-lifetime expiries.
- thesis-consumed expiries.
- Pattern-native evidence observations.
- Candidate conversion counts and reasons.
- canonical-key marginal cohort P&L.
- Pattern x Route x Volatility x Efficiency x Lane leave-one-window-out descriptive evidence.
- counterfactual shadow reason matrix, explicitly diagnostic-only.

DEV diagnostics may determine the next major architecture but may not retune current V43.

## Efficiency invariant
- static audit/build once
- one ultra-short smoke
- exactly 12 independent DEV windows in parallel
- immutable compiled .algo reused
- persistent XAUUSD M1 data cache
- immediate per-window artifacts
- workflow concurrency cancels obsolete duplicate V43 runs
- six capital balances in parallel only after DEV promotion
- Fresh Alpha/$100 in parallel only after capital gate and hash freeze

## Capital and Fresh
Only a DEV family passing Alpha + Frequency + V36 Dominance gates may run $100/$150/$200/$300/$500/$1000 compatibility.
$100 must have baskets>0, Net>0, Expectancy>0, PF>1, DD<=10%, engineering/risk clean.
Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair.
Both Fresh runs require positive Net, PF>1, Expectancy>0, DD<=10%, engineering clean.
No tuning after Fresh.
