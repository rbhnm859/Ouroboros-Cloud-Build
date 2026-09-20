# HarmonyBot V42 Evidence Baseline for V43

V42 is frozen as evidence. V43 must not retune V42 thresholds or reinterpret Fresh/OOS.

## V42 completed run
Workflow run: 35507507039.
Engineering: static audit PASS, compile PASS, smoke PASS, 12/12 DEV windows completed.
Capital / freeze / Fresh: correctly skipped. Fresh remained untouched.

## Aggregate DEV frontier
- LEGACY_REPLAY: 14.0 baskets/year; Net +0.74; PF 1.000729; Expectancy +0.0352; Max DD 4.4499%.
- CORE_CONVERSION: 18.0 baskets/year; Net -22.82; PF 0.977903; Expectancy -0.8452; Max DD 4.1724%.
- RESCUE_CONVERSION: 18.0 baskets/year; Net -25.54; PF 0.975334; Expectancy -0.9459; Max DD 4.1724%.
- FULL_V42: 18.0 baskets/year; Net -25.54; PF 0.975334; Expectancy -0.9459; Max DD 4.1724%.

V42 proved that post-admission conversion can create real extra baskets, but the added cohort failed the permanent profitability rule:
- added trades = 6
- marginal Net = -15.48
- marginal Expectancy = -2.58
- marginal PF = 0.944184
- marginal DEV-A Net = +33.31
- marginal DEV-B Net = +61.07
- marginal DEV-C Net = -109.86

Therefore FREQUENCY_EXPANSION_REJECTED.

## Material forensic finding
The six V42 added trades were all AB=CD CORE_ALPHA trades. Rescue did not establish a separate profitable added cohort.

Across FULL_V42 DEV A/B/C, the main funnel was approximately:
- detected 509
- validated 445
- routed 161
- confirming 66
- executable/armed 39
- executed 27

The route/lifetime counterfactual shadow ledger contained large opportunity-loss populations:
- ROUTER_NO_TRADE: 284 resolved shadows; target-hit ratio about 78.5%.
- TTL_EXPIRED: 112 resolved shadows; target-hit ratio about 77.7%.

These shadow outcomes are diagnostic only. They are overlapping counterfactual paths and are not realized P&L, are not broker-executable proof, and must never be used as a substitute for DEV/Fresh profitability evidence.

## V43 research implication
V43 is not allowed to loosen Harmonic/Fibonacci ratio definitions simply to create trades. The detector contains the intended classical pattern profiles and no direct engineering defect was found that removed Gartley/Bat/Butterfly/Crab/Cypher/Shark/5-0/AB=CD families.

V43 therefore targets the downstream structural bottleneck:
1. convert binary NO_TRADE into a structural route-watch state rather than immediate candidate death;
2. replace short fixed wall-clock candidate TTL with thesis/session lifecycle, while expiring candidates once T1 has already consumed the original opportunity;
3. permit pre-touch route refresh as H4/H1/M15 context changes;
4. use pattern-native M5 evidence semantics without brute-force threshold tuning;
5. continue requiring every added cohort to be profitable and every promoted family to beat the V36 champion.
