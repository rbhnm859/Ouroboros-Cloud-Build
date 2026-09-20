# HarmonyBot V48 — Family-Native Harmonic Portfolio Reform Engine

V48 is a clean major version built from the frozen V47/V46 SCALE evidence. It does not revive Projected-D and it does not use Fresh for tuning.

## Root-cause evidence
V47 FULL showed that dormant harmonic families are not mainly detector-starved:
- Gartley: 468 detected / 15 confirming / 0 armed
- Rat: 838 / 31 / 0
- Bat: 118 / 3 / 0
- Crab: 66 / 6 / 0
- Deep Crab: 50 / 15 / 0
- Deep Gartley: 160 / 7 / 0
while AB=CD, Shark and Cypher did reach Armed/Executed.

Raw event forensics showed large counts of LEGACY_CONFIRMATION_FAILED and FIB_GRID_PLAN_REJECTED for dormant families.

Two architecture defects are preregistered:
1. canonical AD/XA was introduced without synchronizing STANDARD extension invalidation. For Xad>1, the legacy formula used X +/- r*XA, which is one full XA too remote. V48 uses D(r)=A+r(X-A) and places invalidation beyond the deepest legal D.
2. legacy grid minimum span values for retracement families (e.g. Gartley .65XA, Bat .75XA, Deep Gartley .70XA) are inconsistent with the geometric D-to-X distance implied by their AD/XA completion zones. V48 derives the legal grid span envelope from the pattern's own Xad band and structural buffer.

The third issue is common execution semantics: retracement and extension families were forced through a mostly shared M1 rule. V48 adds family-native completed-M1 evidence without lowering the legacy threshold.

## Frozen Alpha core
- XAUUSD / FxPro / UTC
- confirmed-D harmonic thesis
- H4/H1 context
- M15 detection
- M1 execution
- canonical setup identity
- V46 SCALE route admission for the already profitable AB=CD cohort
- staged Fibonacci grid and <=1% basket risk
- MaxActiveBasket=1
- no hedging/Martingale/DCA/Recovery/Loss Averaging
- server-side protection and broker/margin fail closed
- completed-bar / no-lookahead
- existing exit/target policy

AB=CD, Shark and Cypher route semantics are preserved to protect the proven V46 alpha.

## Family taxonomy
RETRACEMENT:
Gartley, Bat, Deep Gartley, Rat

EXTENSION:
Alt Bat, Butterfly, Crab, Deep Crab

TRANSITION:
Shark, 5-0

XC_RETRACE:
Cypher

COMPLETION_SYMMETRY:
AB=CD

## Family route compatibility
- Proven AB=CD/Shark/Cypher routes remain unchanged.
- Retracement family: trend-aligned allowed; transition requires actual transition; exhaustion requires stronger extension plus geometry/PRZ quality.
- Extension family: exhaustion or true transition only; no generic trend-aligned admission.
- 5-0: exhaustion or transition.

## Family-native M1 evidence
Only completed M1 bars.
Retracement requires accumulated reclaim + rejection/failed-extension + micro BOS + directional/displacement evidence.
Extension requires sweep/failed-extension + return-inside-PRZ/reclaim + BOS.
Max 6 M1 bars by preregistration.
No threshold sweep and no tick signal creation.

## Fixed 12-run DEV design
- V46_SCALE_CONTROL x A/B/C
- STRUCTURAL_GEOMETRY_REPAIR x A/B/C
- FAMILY_NATIVE_EXECUTION x A/B/C
- FULL_V48_FAMILY_PORTFOLIO x A/B/C

V46_SCALE_CONTROL must reproduce 39 baskets / 26 per year / Net +1721.72 / PF 2.1833 / Exp +44.15 / WR 51.28% / DD 4.56%.

## Promotion rules
Historical V36 all-metric dominance remains mandatory.
Commercial freeze minimum remains:
- >=90 independent baskets / 1.5y
- >=60/year
- Net >=1800
- PF >=2.0
- Expectancy >=20
- WR >=50%
- DD <=6%
- DEV A/B/C positive
- no duplicate setup
- engineering/risk clean

Added unique cohort vs V46_SCALE_CONTROL must have:
- trades >0
- Net >0
- Expectancy >0
- PF >=1.20
- marginal Net A/B/C >=0

Additionally, every newly activated dormant family with >=3 DEV trades must have aggregate Net>0 and PF>=1.10. A newly activated family may not be hidden by stronger AB=CD performance.

## Data governance
Capital validation only after DEV promotion.
Then $100/$150/$200/$300/$500/$1000.
Then immutable source/.algo hash freeze.
Then exactly one untouched Fresh Alpha + Fresh $100 pair.
Fresh failure means HOLD.
