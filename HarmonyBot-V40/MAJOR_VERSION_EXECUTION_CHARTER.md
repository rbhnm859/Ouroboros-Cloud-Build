# HarmonyBot V40 — Attribution-Driven Harmonic Portfolio & Follow-Through Engine

V40 is a major-version replacement of V39's veto-heavy selection layer.

## Thesis
V36/V38/V39 evidence shows Harmonic opportunities are not scarce, but realized P&L deteriorates because candidate selection and follow-through discrimination are weak. V40 therefore changes from filter-first to rank-first execution.

## Frozen architecture
- H4 macro regime/context.
- H1 intermediate harmonic context/conflict.
- M15 primary harmonic thesis, PRZ, structural invalidation, canonical targets.
- M5 execution evidence and follow-through measurement.
- M1 is backtest fill-resolution only, never a strategy timeframe.
- Fibonacci/Harmonic detector, broker realism and risk kernel remain core.
- Max active basket = 1.
- Total basket risk <=1%.
- No hedging, Martingale, DCA, Recovery or Loss Averaging.

## New V40 modules
1. Candidate Attribution Ledger: records pattern, route, regime, geometry, PRZ, symmetry, pivot quality, evidence, follow-through, MFE/MAE and realized P&L.
2. Rank-First Portfolio: evidence/regime/route features become continuous ranking inputs rather than hard vetoes.
3. M5 Follow-Through Engine: distinguishes temporary PRZ reaction from sustained reversal.
4. Thesis-Failure Management: server SL remains intact, but a basket may close earlier when follow-through persistently fails after sufficient evidence.

## Fixed DEV ablations
- LEGACY_CONTROL: rank-first OFF, follow-through OFF, thesis-failure OFF.
- RANK_ONLY: rank-first ON, follow-through OFF, thesis-failure OFF.
- RANK_FOLLOWTHROUGH: rank-first ON, follow-through ON, thesis-failure OFF.
- FULL_V40: rank-first ON, follow-through ON, thesis-failure ON.

No brute-force optimization and no Fresh tuning.

## First-stage promotion gate
A candidate must satisfy all:
- DEV-A/B/C all have trades.
- DEV-A/B/C each Net Profit >= 0.
- Aggregate Net Profit > 0.
- Aggregate PF >= 1.15.
- Aggregate Expectancy > 0.
- Max DD <= 10%.
- Executable baskets/year >= 50.
- engineering_clean = true.
- Actual basket risk violations = 0.
- Margin risk violations = 0.

Negative-net candidates are never promoted.

## Promotion sequence
12-way DEV -> attribution matrix -> positive-net promotion gate -> parallel $100/$150/$200/$300/$500/$1000 compatibility -> frozen source/algo manifest -> exactly one untouched Fresh Alpha and Fresh $100 pair -> commercial decision.

Fresh remains untouched until DEV and $100 compatibility pass.
