# HarmonyBot V44 — Canonical Harmonic Commercial Convergence Engine

V44 is a clean major-version commercial-freeze candidate built from the frozen V43 evidence baseline. It is not a V43 threshold patch and it must not use Fresh/OOS for tuning.

## Commercial objective
V44 must attempt historical dominance in one preregistered architecture:
- all-in basket risk <=1%;
- engineering/risk violations = 0;
- aggregate and DEV-A/B/C Net >0;
- added frequency cohort itself profitable;
- historical V36 metrics all exceeded;
- commercial-candidate minimum: >=75 executable baskets/year, >=113 baskets/1.5y, Net >=800 USD on registered 10k DEV comparison, PF >=1.35, Expectancy >=10 USD/basket, Max DD <=8.0%;
- final stretch targets remain PF>=2.5, WR>=65%, realized RR>=2, 200+/year, DD<=10%, annual return>=100%, >=10/12 profitable months. Stretch targets are reported, never fabricated.

## Frozen safety core
- FxPro cTrader / XAUUSD / UTC.
- H4 macro structural context, H1 intermediate context, M15 harmonic thesis, M5 execution evidence, M1 broker data only.
- MaxActiveBasket=1.
- no hedging, Martingale, DCA, Recovery or Loss Averaging.
- logical Fibonacci grid 0/.236/.382/.618 with intended 3/7,2/7,1/7,1/7 basket weights.
- basket risk <=1%, server-side protection, broker min-volume, margin/free-margin, daily-risk and max-DD fail-closed behavior.
- completed-bar / no-lookahead discipline.

## V44 harmonic contract
1. Canonical ratio coordinates are dimensionless and independent of account size or ATR.
2. ATR may provide execution tolerance only; it may not redefine pattern identity.
3. Standard/alternate AB=CD are separated:
   - AB=CD Exact: CD/AB around 1.0.
   - AB=CD Alt 1.27.
   - AB=CD Alt 1.618.
4. Standard patterns use canonical XA/AB/BC/CD relationships.
5. Cypher uses XC-specific coordinates.
6. Shark and 5-0 retain native confirmed-completion schemas rather than being forced into the standard Gartley/Bat coordinate meaning.
7. Rat remains experimental and receives a stricter statistical guard.
8. Canonical PRZ is a Fibonacci projection cluster, not merely D +/- ATR.

## Projected-D engine
Confirmed XABC may create a forward D/PRZ hypothesis without consuming future bars. State flow:
XABC_CONFIRMED -> D_PROJECTED -> WAIT_PRZ -> TERMINAL_PRICE_BAR -> M5_NATIVE_CONFIRM -> ARMED -> EXECUTED.
Projected-D is enabled only for patterns whose D can be expressed from known XABC ratios. No lookahead is permitted.

## Route semantics
- CONTINUATION_PULLBACK: pattern direction agrees with HTF trend; execution must prove trend resumption after the harmonic pullback.
- COUNTERTREND_EXHAUSTION: pattern direction opposes HTF trend; requires extension/exhaustion evidence.
- STRUCTURAL_TRANSITION: H4/H1 disagreement or structural transition; requires micro structure flip/retest evidence.
Persistent-trend AB=CD is not blacklisted; it carries a preregistered persistence hazard and stricter temporal/evidence admission.

## Fixed DEV ablations
Exactly 12 independent windows:
- V43_CONTROL x A/B/C
- CANONICAL_PROJECTED_D x A/B/C
- REGIME_NATIVE_EXECUTION x A/B/C
- FULL_V44_COMMERCIAL x A/B/C

No threshold sweep and no post-hoc window tuning.

## Frequency admission
Relative to V43_CONTROL, an expanded family must have:
- added trades >0;
- marginal Net >0;
- marginal Expectancy >0;
- marginal PF >=1.15;
- DEV-A/B/C marginal Net each >=0.

## Historical dominance and commercial-candidate gates
Historical V36 dominance requires all:
- baskets >77 over registered 1.5y;
- executable baskets/year >51.33;
- Net >648.58 USD;
- Expectancy >8.42 USD/basket;
- PF >1.2124;
- Max DD <8.77%;
- DEV-A/B/C Net >0;
- engineering/risk clean.

Commercial-candidate gate is stricter:
- >=113 baskets / 1.5y and >=75/year;
- Net >=800 USD;
- PF >=1.35;
- Expectancy >=10 USD/basket;
- Max DD <=8.0%;
- all DEV windows positive;
- frequency admission PASS;
- leave-one-window-out robustness not negative;
- engineering/risk clean.

## Capital and Fresh governance
Only a commercial DEV candidate may run $100/$150/$200/$300/$500/$1000 compatibility.
$100 must be actually executable, positive-Net, PF>1, Expectancy>0, DD<=10%, risk/margin clean.
Then freeze source/algo hashes and consume exactly one untouched Fresh Alpha plus one untouched Fresh $100 pair.
Fresh never tunes V44. Fresh failure means HOLD, not a V44 threshold patch.
