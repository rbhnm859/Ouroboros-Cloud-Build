# HarmonyBot V67 — V52 Throughput Core Family-Native Grid Commercial Rebase

## Mission
Rebase commercial development directly on V52 throughput, not V66. Preserve opportunity supply while replacing shared-family routing with family-native thesis, completion, arbitration and staged Fibonacci Grid execution.

## Calibration evidence
Formal V52 FULL_V52_COMMERCIAL (run 35531304357):
- AB=CD: 66 trades, net -518.02, PF 0.864.
- Shark: 13 trades, net +148.59.
- Cypher: 6 trades, net +32.59.
- Rat: 26 trades, net +28.27.
- Shark x Trend-Aligned: 10 trades, net +346.10, PF 2.56.
- Shark x Exhaustion: net -197.51.
- AB=CD x Exhaustion: net -517.04.

This calibration evidence may guide V67 architecture. Later DEV (2024H2, 2025H1, 2025H2), Validation and Fresh may not tune V67.

## Family-native capital architecture
- Shark: Trend-Aligned lane only in V67 Product.
- Cypher: Trend-Aligned primary, Transition only under family-native confirmation.
- Rat / Gartley / Bat / Deep Gartley: retracement-family Trend-Aligned / Transition contracts.
- 5-0: Exhaustion / Transition only.
- Alt Bat / Butterfly / Crab / Deep Crab: extension-family Exhaustion / Transition only.
- AB=CD standalone capital OFF by default. It remains completion/confluence evidence and cannot dominate supply.

## Fibonacci Grid
Grid is pre-designed staged entry, never recovery.
- Whole-basket stressed risk <=1%.
- 0 / .236 / .382 / .618 are family-aware and route-aware, not four independent trades.
- No Martingale, DCA, Recovery, Loss Averaging or stop widening.
- Deeper legs are cancelled after basket MFE >= +0.50R or thesis invalidation/session/spread/margin/risk lock.

## Indicator decision
No new production indicator gate is added in the first V67 Candidate. Existing EMA/ATR/ADX remain context-only. This deliberately avoids repeating V61-V66 over-filtering. Directional Movement (+DI/-DI) is deferred to shadow telemetry only if later-DEV shows a specific family-direction failure.

## Commercial gates
- Control must reproduce V52 FULL_V52_COMMERCIAL calibration windows.
- DEV A/B/C all positive.
- Frequency >=60/year and <=90 baskets/1.5y.
- Net >=1800 / 1.5y.
- PF >=2.0.
- Expectancy >=20/trade.
- WR >=50%.
- Max DD <=6%.
- Minimum Net RR >=2.
- Actual basket risk violations =0; margin violations =0; execution errors =0.
- At least 3 non-AB=CD families must have positive contribution with >=3 trades each.
- AB=CD share <=25%; no single non-ABCD family >55% of product DEV trades.
- New frequency is allowed only if Delta Net >0 versus control.

Risk, Model Validation, Red Team and Data Governance are fail-closed vetoes.
Fresh remains locked until DEV, Validation and Capital all pass.
