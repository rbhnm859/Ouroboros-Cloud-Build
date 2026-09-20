# HarmonyBot V42 — Opportunity Conversion & Positive-Marginal Portfolio

V42 is the only active development line. V41/V40/V39/V38/V37/V36 are evidence baselines only.

## Purpose
V41 proved that marginal-rescue candidates can pass admission yet fail to create added executable baskets. V42 therefore moves the research target downstream: convert already-admitted positive-alpha opportunities into legal executable baskets without increasing basket risk, concurrent exposure, or using negative-alpha frequency expansion.

## Frozen architecture
- H4 macro regime.
- H1 context/conflict.
- M15 Harmonic/Fibonacci thesis and PRZ.
- M5 execution evidence and follow-through.
- M1 is broker data/fill granularity only.
- Fibonacci/Harmonic detector remains core.
- Logical Fibonacci Grid remains 0/.236/.382/.618.
- Basket risk weights remain 3/7, 2/7, 1/7, 1/7.
- Total basket risk <=1%.
- MaxActiveBasket=1.
- All-in L0 risk normalization stays fail-closed.
- Server-side protection, min-volume, margin/free-margin protection, daily lock and max-DD lock stay frozen.
- No hedging, duplicate opening, Martingale, DCA, Recovery or Loss Averaging.
- Completed-bar discipline is mandatory.

## V42 structural change
V42 adds an explicit conversion state:
DETECTED -> VALIDATED -> ROUTED -> WAIT_PRZ -> PRZ_TOUCHED -> EVIDENCE_BUILDING -> ADMITTED -> EXECUTABLE -> EXECUTED.

An admitted candidate is not silently discarded merely because one instantaneous Grid/capital feasibility attempt fails. While the thesis remains valid, TTL remains alive, risk limits remain clean and MaxActiveBasket is free, V42 may re-attempt legal conversion on later completed execution bars.

V42 also adds a ranked scheduler fallback cascade. Before any basket is active, if the highest-ranked candidate fails a legal execution/risk check and leaves no live position/pending order/basket, the next ranked executable candidate may be attempted. The cascade stops immediately when any basket exposure exists.

Neither mechanism may force broker minimum volume, widen risk, weaken SL protection, create a hedge, or exceed one active basket.

## Fixed DEV families
Exactly four families are allowed:
1. LEGACY_REPLAY — rescue off, opportunity-cost off, follow-through off, thesis exit off, conversion/replan/fallback off.
2. CORE_CONVERSION — rescue off, opportunity-cost off, follow-through on, thesis exit on, conversion/replan/fallback on.
3. RESCUE_CONVERSION — rescue on, opportunity-cost off, follow-through on, thesis exit on, conversion/replan/fallback on.
4. FULL_V42 — rescue on, opportunity-cost on, follow-through on, thesis exit on, conversion/replan/fallback on.

No threshold brute force. No post-hoc DEV retuning. Fresh is never tuning data.

## Frequency Admission Gate
Relative to LEGACY_REPLAY, an expansion family may count as frequency improvement only when:
- added_trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- DEV-A/B/C marginal Net each >= 0

Otherwise: FREQUENCY_EXPANSION_REJECTED.

## Alpha Promotion Gate
All must pass:
- DEV-A/B/C each has baskets >0 and Net >=0
- aggregate Net >0
- PF >=1.25
- Expectancy >0
- Max DD <=10%
- executable baskets/year >=50
- Frequency Admission Gate PASS
- engineering_clean=true
- actual basket risk violations=0
- margin risk violations=0

Negative-net candidates never promote.

## V36 Dominance Gate
V36 Structured Recall is the performance champion baseline to beat. V42 promotion to capital compatibility additionally requires:
- executable baskets/year >51.33
- aggregate Net >648.58
- aggregate Expectancy >8.42/basket
- PF >1.2124
- Max DD <=8.77%
- DEV-A/B/C Net each >=0

This gate is deliberately stricter than merely recovering from V41.

## Diagnostics
DEV-only reporting must include:
- Pattern signal-to-execution funnel.
- ADMITTED -> Grid feasible -> Capital feasible -> Executable -> Scheduler competition -> Executed conversion counts.
- conversion defer reasons.
- Pattern x Route x Volatility x Efficiency x Lane attribution.
- leave-one-window-out descriptive diagnostics.
These diagnostics may determine the next major architecture but may not retune the current V42 run.

## Efficiency invariant
- build/static audit once
- ultra-short smoke once
- exactly 12 independent DEV windows in parallel
- immutable compiled .algo reused
- persistent XAUUSD M1 cache
- per-window artifacts uploaded immediately
- duplicate V42 runs cancelled by workflow concurrency
- capital balances in parallel
- Fresh Alpha/$100 in parallel

## Capital and Fresh
Only a DEV family passing every gate may run $100/$150/$200/$300/$500/$1000 compatibility.
$100 requires baskets>0, Net>0, Expectancy>0, PF>1, DD<=10%, engineering/risk clean.
Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair.
Both Fresh runs require positive Net, PF>1, Expectancy>0, DD<=10%, engineering clean.
No tuning after Fresh.

## Commercial rule
Trade count is never purchased with negative marginal expectancy. V42 is successful only if additional executable opportunity is itself profitable and the resulting portfolio surpasses the V36 champion evidence under the registered gates.
