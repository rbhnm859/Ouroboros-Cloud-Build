# HarmonyBot V46 — Restored Alpha Execution Conversion Engine

V46 follows V45 DEV evidence and keeps Fresh untouched.

## Evidence basis
V45 proved:
- exact V36 replay: 77 baskets, Net +648.58, PF 1.21243, Expectancy +8.423, WR 42.857%, DD 8.768%.
- V36 contained 22 repeated same-setup reentries with Net -325.80 / PF 0.576.
- first unique V36 executions: 55, Net +974.38 / PF 1.4265 / Expectancy +17.716.
- V45 STABLE_ROUTE_CANONICAL: 38 unique baskets, Net +1000.38, PF 1.6853, Expectancy +26.326, DD 4.635%, DEV A/B/C all positive.
- V45 FULL: 77 unique baskets, Net +871.73, PF 1.28695, Expectancy +11.321, DD 6.827%; C remained -72.90 and frequency did not exceed V36.
- FULL had 143 armed candidates but only 77 executions; raw ledger showed 31 candidates expired after reaching ARMED.
- secondary-scale added AB=CD EXHAUSTION cohort was positive in A/B/C, while secondary-scale trend-aligned AB=CD was negative overall.

## Architectural decision
V46 preserves the confirmed-D + M1 restored kernel and the V45 stable core.
It does not introduce Projected-D and does not use M5 as the primary alpha gate.

Frequency may increase only through:
1. Cross-window-supported scale-route admission:
   secondary-scale AB=CD is live only for EXHAUSTION_REVERSAL.
2. M1 temporal evidence:
   route-native confirmation evidence may accumulate across at most 3 completed M1 bars; no threshold sweep.
3. Armed execution grace:
   an already confirmed/armed setup may receive a bounded 90-minute execution opportunity extension.
4. Mandatory pre-execution revalidation:
   after any wait, grid/PRZ/structural SL/broker feasibility/remaining RR are rebuilt at the live quote; failure is fail-closed.
5. MaxActiveBasket remains 1 and setup identity remains one execution maximum.

## Fixed DEV ablations
Exactly 12:
- V36_REPLAY x A/B/C
- STABLE_CORE x A/B/C
- SCALE_CONVERSION x A/B/C
- FULL_V46 x A/B/C

No brute-force search.

## Gates
V36_REPLAY must reproduce the registered 77-basket benchmark.

Historical all-metric dominance:
- baskets >77
- frequency >51.33/year
- Net >648.58
- PF >1.2124297856
- Expectancy >8.4231
- WR >42.857%
- DD <8.7683%
- DEV-A/B/C all positive
- duplicate executed setup = 0
- engineering/risk clean

Clear breakthrough:
- >=90 unique baskets /1.5y
- >=60/year
- Net >=800
- PF >=1.35
- Expectancy >=10
- WR >=45%
- DD <=8%
- A/B/C all positive
- incremental unique cohort versus STABLE_CORE: trades>0, Net>0, Expectancy>0, PF>=1.15, marginal Net A/B/C each >=0
- engineering/risk clean.

Only a clear-breakthrough candidate may enter $100/$150/$200/$300/$500/$1000 capital validation, immutable hash freeze, and exactly one untouched Fresh Alpha + Fresh $100 pair.
