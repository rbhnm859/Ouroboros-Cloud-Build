# HarmonyBot V45 — Restored Edge & Independent Setup Expansion Engine

V45 is a deliberate hybrid rollback/reconstruction from the exact V36 historical-performance source commit:
448a3fce1ec35b28ce0e8d8e3514e5424d7e007d

It is not a V44 patch.

## Why V45 exists
V36 STRUCTURED_RECALL produced the historical development benchmark:
- 77 baskets / 51.33 per year
- PF 1.2124297856
- Net +648.58 USD
- Expectancy +8.4231 per basket
- Win rate 42.857%
- Max DD 8.7683%

Forensic reconstruction of the raw V36 basket log shows only 55 independent harmonic completions. Twenty-two baskets were repeated re-entries of an already traded setup:
- first execution per unique setup: 55 trades, Net +974.38, PF 1.4265, Expectancy +17.716
- repeated same-setup re-entries: 22 trades, Net -325.80, PF 0.5761, Expectancy -14.809

Therefore V36's first-entry alpha kernel is stronger than the aggregate headline, while duplicate re-entry inflated frequency and reduced profitability.

V44 failed because it replaced too many dimensions simultaneously: signal geometry, D timing, route semantics, execution timeframe and candidate identity. Its Projected-D supply exploded while executable positive alpha collapsed.

## V45 design decision
Restore the V36 confirmed-D + M1 execution kernel and preserve its proven first-entry timing.
Do NOT use Projected-D as the primary alpha engine.
Do NOT replace M1 execution with M5 as the primary alpha gate.

Add only bounded mechanisms with independent rationale:
1. canonical setup identity: one execution maximum per XABCD market setup;
2. corrected AD/XA coordinates for standard harmonic families, switchable so V36 replay remains exact;
3. confirmed-D multi-scale M15 pivot graph for genuinely independent setups;
4. transition proof: TRANSITION requires actual HTF disagreement, not merely a neutral trend sum;
5. M1 rescue lane: candidates that miss the legacy single-bar score may qualify only through stronger route-specific completed-M1 evidence;
6. diversity scheduler: setup-level arbitration, never pattern quotas;
7. AB=CD subtype attribution is observational only and cannot alter the V36 replay.

## Frozen safety core
- XAUUSD / FxPro / UTC / London-open to New-York-close DST-aware.
- H4/H1 context; M15 confirmed harmonic thesis; M1 execution.
- MaxActiveBasket=1.
- basket risk <=1%.
- server-side SL/TP protection.
- broker min-volume/margin/min-distance fail closed.
- max DD/daily loss locks.
- no hedging, Martingale, DCA, Recovery or Loss Averaging.
- Fibonacci staged entry remains preplanned PRZ execution, never loss recovery.
- completed-bar/no-lookahead discipline.

## Fixed DEV experiment
Exactly 12 DEV windows:
- V36_REPLAY x A/B/C
- UNIQUE_SETUP_CORE x A/B/C
- STABLE_ROUTE_CANONICAL x A/B/C
- FULL_V45 x A/B/C

No threshold sweep.

V36_REPLAY must reproduce the historical 77-basket result before any V45 conclusion is accepted.

## Historical all-metric dominance
A candidate must beat every verified V36 benchmark:
- baskets >77
- baskets/year >51.33
- Net >648.58
- PF >1.2124297856
- Expectancy >8.4231
- Win rate >42.857%
- Max DD <8.7683%
- DEV-A/B/C Net each >0
- engineering/risk clean
- no repeated executed setup.

## Clear-breakthrough gate
Because the requirement is to clearly exceed V36, not barely pass:
- >=90 unique executable baskets / 1.5y
- >=60 unique baskets/year
- Net >=800 USD on registered 10k DEV
- PF >=1.35
- Expectancy >=10 USD/basket
- Win rate >=45%
- Max DD <=8.0%
- DEV-A/B/C each positive
- all added unique setups vs V36 independent-setup baseline have positive marginal Net/Expectancy, PF>=1.15 and non-negative A/B/C marginal Net
- engineering/risk clean.

Only a clear-breakthrough candidate may proceed to capital compatibility and Fresh.

## Capital and Fresh governance
After a clear DEV breakthrough only:
$100/$150/$200/$300/$500/$1000 in parallel.
$100 must be genuinely executable and positive-Net with PF>1, Expectancy>0, DD<=10%, no risk/margin violations.
Then freeze source/algo hashes.
Then exactly one untouched Fresh Alpha + one untouched Fresh $100 pair.
Fresh never tunes V45.
