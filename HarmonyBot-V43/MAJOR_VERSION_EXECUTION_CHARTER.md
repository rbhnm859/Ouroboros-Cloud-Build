# HarmonyBot V43 — Cross-Regime Positive-Alpha Harmonic Portfolio Engine

V43 is a major-version replacement built from the frozen V42 canonical harmonic geometry baseline. It is not a V42 threshold patch.

## Non-negotiable commercial objective
V43 may increase executable frequency only when the added cohort itself is profitable. Net loss is never accepted as the cost of higher trade count.

## Frozen safety core
- XAUUSD / FxPro cTrader, UTC.
- H4 macro structural context, H1 intermediate context, M15 harmonic thesis/PRZ, M5 execution evidence, M1 broker data only.
- Fibonacci/Harmonic geometry remains the entry thesis.
- Logical staged Fibonacci grid remains 0/.236/.382/.618 with intended 3/7,2/7,1/7,1/7 basket weights.
- Whole-basket risk <=1%.
- MaxActiveBasket=1.
- No hedging, Martingale, DCA, Recovery or Loss Averaging.
- Server-side protection, broker min-volume, margin/free-margin, daily risk and max-DD fail-closed behavior remain frozen.
- Completed-bar/no-lookahead discipline remains mandatory.

## V42 evidence carried forward
V42 restored multi-pattern detection but FULL_V42 remained negative. The dominant development observations were:
- substantial detector supply already exists;
- AB=CD was the dominant negative contributor;
- all executed outcomes were effectively MTF-neutral under the old context representation;
- 76 candidates reached armed/executable quality but only 37 executed;
- the old pattern attrition artifact had a parser defect and did not expose terminal reasons;
- fixed-delay opportunity auction can sacrifice entry quality when no competing candidate exists.

These are DEV observations only. Fresh/OOS remains untouched and is not used to set V43 parameters.

## V43 architecture
1. CanonicalSetup + PatternHypothesisSet: one market geometry owns one slot while multiple harmonic labels can remain hypotheses until contextual resolution.
2. Structural Context Vector: H4/H1 direction votes, agreement, ADX state/slope, ATR regime, efficiency and extension become continuous context, not only NEUTRAL/CONFLICT labels.
3. Pattern Temporal State Machine: execution confirmation is sequence-aware, not merely a weighted one-bar score.
4. Cross-Regime Alpha Admission: candidates must pass a preregistered conditional-alpha score; AB=CD trend-aligned setups face a stricter preregistered admission floor because V42 development evidence identified that cohort as the primary negative contributor.
5. Robust Alpha Density: ranking accounts for conservative edge, fill quality, expected R, slot time and capital burden.
6. Event-Driven Opportunity Auction: one eligible candidate executes without an artificial wait; competition is invoked only when multiple legal candidates exist.
7. Opportunity-Loss Ledger: deferred/excluded executable candidates receive counterfactual shadow tracking.
8. The previously disconnected portfolio execution eligibility logic is wired into the executable path.
9. Full pattern/route/regime attrition telemetry is mandatory.

## Fixed DEV ablations
- V42_CONTROL
- CONDITIONAL_ALPHA
- ALPHA_AUCTION
- FULL_V43

Exactly A/B/C for each family = 12 independent DEV windows. No brute-force threshold search.

## Frequency Admission Gate
Relative to V42_CONTROL, any family that adds trades must satisfy:
- added trades > 0
- marginal Net > 0
- marginal Expectancy > 0
- marginal PF >= 1.15
- DEV-A/B/C marginal Net each >= 0

Otherwise FREQUENCY_EXPANSION_REJECTED.

## Absolute positive-net gate
A candidate cannot promote when:
- aggregate Net <= 0, or
- any DEV A/B/C Net < 0.

## V36 historical-dominance gate
A V43 candidate is not considered a historical breakthrough unless all hold:
- executable baskets/year > 51.33
- Net > 648.58 USD on the registered 10k DEV comparison
- Expectancy > 8.42 USD/basket
- PF > 1.2124
- Max DD <= 8.77%
- DEV-A/B/C each Net >= 0
- engineering/risk clean

The stricter alpha-promotion PF floor remains 1.25.

## Frequency staircase after first dominance
>52/year -> 75 -> 100 -> 150 -> maximum robust frequency.
Each additional cohort must independently pass the Frequency Admission Gate.

## Capital and Fresh governance
Only a DEV candidate that passes positive-net, frequency, alpha and V36-dominance gates may run $100/$150/$200/$300/$500/$1000 compatibility. $100 must be genuinely broker-executable and positive-net. Only after source/algo hash freeze may exactly one untouched Fresh Alpha + one Fresh $100 pair run.

Fresh is never used for tuning.
