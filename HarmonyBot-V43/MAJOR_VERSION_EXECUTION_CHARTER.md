# HarmonyBot V43 — Multiscale Harmonic Discovery & Positive-Alpha Execution Portfolio

V43 is the only active development line. V42/V41/V40/V39/V38/V37/V36 are evidence baselines only.

## Frozen architecture and risk invariants
- H4 macro regime; H1 context/conflict; M15 Harmonic/Fibonacci thesis and PRZ; M5 completed-bar execution evidence/follow-through; M1 broker fill granularity only.
- Harmonic ratios remain canonical; V43 does not widen ratio thresholds from DEV evidence.
- Supported pattern contracts: Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Deep Gartley, Rat, Cypher, Shark, 5-0, AB=CD.
- Logical staged Fibonacci Grid is 0/.236/.382/.618 with 3/7,2/7,1/7,1/7 basket-risk weights.
- <=1% total basket risk; all-in risk normalization; MaxActiveBasket=1; anti-hedge; no duplicate opening; server-side protection.
- Min-volume and margin fail closed; daily/max-DD locks; no Martingale/DCA/Recovery/Loss Averaging; completed-bar discipline.
- No brute-force thresholds. Fresh/OOS is never used for tuning.

## V42 evidence that determines V43
V42 FULL: 21 baskets, 14/year, PF 1.0938, Net +78.34, Expectancy +3.73, DD 4.15%.
Grid planning: 128 attempts / 32 passes / 96 fails. Of failures, 71 were legacy SPAN_XA and 23 were NO_LEGAL_L0.
Only 5/12 pattern families were detected in DEV and only Shark, 5-0, AB=CD executed.
Opportunity Queue had slotBlocked=0; therefore basket occupancy was not the limiting bottleneck.

## Pre-registered V43 hypotheses
1. MULTISCALE_DISCOVERY: run the unchanged harmonic matcher on deterministic completed-bar pivot depths 2/3/5 for M15, while H1/H4 remain their existing context behavior.
2. PATTERN_DIVERSITY_ADMISSION: before filling remaining candidate capacity, preserve the strongest valid candidate from each detected pattern family. This changes discovery opportunity, not harmonic validity.
3. STRUCTURAL_GRID_ELIGIBILITY: the legacy SPAN_XA execution heuristic cannot veto an already-valid harmonic thesis when enabled; structural stop, canonical target, RR, PRZ legality, <=1% all-in risk, min-volume and margin checks remain mandatory.
4. PRZ_SYNCHRONOUS_EVIDENCE: the completed M5 bar that touches PRZ may be the first evidence observation. No intrabar data and no lookahead are introduced.

## Fixed DEV families — exactly 12 independent windows
- V42_REPLAY: V42 full behavior; all four V43 hypotheses OFF.
- DISCOVERY_ONLY: MULTISCALE_DISCOVERY + PATTERN_DIVERSITY_ADMISSION ON; execution-recovery hypotheses OFF.
- EXECUTION_RECOVERY: discovery hypotheses OFF; STRUCTURAL_GRID_ELIGIBILITY + PRZ_SYNCHRONOUS_EVIDENCE ON.
- FULL_V43: all four V43 hypotheses ON.
Each family runs DEV-A/B/C independently in parallel using one immutable compiled .algo.

## Frequency Admission Gate
Compared with V42_REPLAY:
- added_trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- DEV-A/B/C marginal Net each >= 0
Otherwise FREQUENCY_EXPANSION_REJECTED.

## New-pattern profitability gate
Any pattern that gains executed trades versus V42_REPLAY is treated as a marginal cohort.
A new pattern cohort may contribute to promotion only when:
- aggregate cohort Net > 0
- aggregate cohort Expectancy > 0
- aggregate cohort PF >= 1.15
- every DEV window in which that cohort traded has Net >= 0
No pattern is forced to trade to satisfy a coverage target.

## Pattern utilization contract
- Static executable-path coverage must be 12/12.
- DEV must report raw matches, selected candidates, armed candidates and executed baskets by pattern.
- Commercial full-pattern completion target is 12/12 patterns executed with positive marginal cohorts.
- Absence of a valid historical setup must never be solved by inventing signals or widening ratios post hoc.

## Alpha Promotion Gate
- DEV-A/B/C each has trades and Net >= 0
- aggregate Net > 0
- PF >= 1.25
- Expectancy > 0
- Max DD <= 10%
- executable baskets/year >= 50
- Frequency Admission Gate PASS
- New-pattern profitability gate PASS for every added pattern cohort
- engineering_clean=true
- actual basket-risk violations=0
- margin-risk violations=0
Negative-net candidates never promote.

## V36 Dominance Gate
- executable baskets/year > 51.33
- Net > +648.58
- Expectancy > +8.42/basket
- PF > 1.2124
- Max DD <= 8.77%
- DEV-A/B/C Net each >= 0

## Post-DEV sequence
Only a family passing Alpha Promotion + V36 Dominance proceeds to parallel $100/$150/$200/$300/$500/$1000 compatibility.
$100 requires baskets>0, Net>0, Expectancy>0, PF>1, DD<=10%, engineering/risk clean.
Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha + Fresh $100 pair.
Both Fresh runs require positive Net, PF>1, Expectancy>0, DD<=10% and engineering clean.
