# HarmonyBot V67 — V52 Throughput Family-Native Commercial Rebase

## Parent
Formal parent: HarmonyBot V52 FAMILY_IDENTITY_RECONSTRUCTION, not FULL_V52_COMMERCIAL.

Verified V52 parent evidence:
- 200 baskets / 1.5y
- 133.3333 baskets/year
- Net +2902.27
- PF 1.3754845
- Expectancy +14.51135
- WR 43.5%
- Max DD 9.814999%
- A/B/C all positive
- engineering/risk clean

## Root cause of V52 FULL regression
FULL_V52_COMMERCIAL differs from FAMILY_IDENTITY_RECONSTRUCTION by enabling family-native projected PRZ. The official artifacts show the FULL variant collapses to 117 baskets and aggregate negative Net. V67 therefore keeps projected PRZ disabled in every commercial run.

## Family evidence from burned V52 calibration
- Shark: 21 trades, +1172.47, PF 4.66; trend and exhaustion both positive.
- Rat: 36 trades, +1229.23, PF 2.03; trend +1250.70, exhaustion -21.47. Capital route = trend.
- Cypher: 9 trades, +369.59, PF 2.28. Capital route = trend/exhaustion with family-native completion.
- AB=CD: 127 trades, +295.22, PF 1.05. Exact trend subgroup: 24 trades, +1062.12, PF 2.07. Exhaustion and broad subtype are negative. Standalone capital is restricted to exact/near-1.27 trend; otherwise AB=CD is completion/confluence evidence.
- Gartley/5-0: insufficient/negative historical capital evidence.
- Bat/Alt Bat/Butterfly/Crab/Deep Crab/Deep Gartley: detection exists but prior conversion is weak; V67 gives them explicit family-native route and completion semantics so they can compete without quotas.

## Product rules
1. No family trade quota. Detection remains fair via FamilyDetectionQuota; execution is chosen by current thesis quality.
2. Same underlying geometry can express multiple family hypotheses. Family arbitration selects the best executable hypothesis.
3. Family-native route definitions:
   - retracement: Gartley/Bat/Deep Gartley/Rat -> trend-aligned
   - extension: Alt Bat/Butterfly/Crab/Deep Crab -> exhaustion/transition
   - Shark -> trend/exhaustion
   - Cypher -> trend/exhaustion
   - 5-0 -> exhaustion/transition
   - AB=CD -> exact/near-1.27 trend only
4. Every family has a dedicated M1 completion contract.
5. +DI/-DI/ADX context is telemetry/tie-break only, never a global veto.
6. Whole basket stressed risk <=1%, Min Net RR >=2, MaxActiveBasket=1.
7. No hedge, Martingale, DCA, Recovery, Loss Averaging, stop widening or duplicate thesis.

## Commercial concentration gates
No fixed family allocation is imposed, but the product must demonstrate:
- top-family executed share <=55%
- non-AB=CD Net >0
- at least three families with >=5 trades, positive Net and PF>1
This proves the product is not economically dependent on AB=CD.

## Governance
Risk / Model Validation / Red Team / Data Governance remain fail-closed vetoes.
