# HarmonyBot V60 — Harmonic Alpha Conversion, Fibonacci Grid & Convex Profit-Capture Engine

V60 rebases verified V59 and treats conversion—not raw signal count—as the bottleneck. Immutable: whole-basket stressed risk <=1%, MinimumNetRR>=2.0, MaxActiveBasket=1, no hedge/Martingale/DCA/Recovery/Loss Averaging, broker/min-volume/margin/server-protection fail closed, completed-bar/no-lookahead, Validation no tuning, Fresh 2020-H1 sealed.

## Core
- Cluster-aware evidence keyed by UnderlyingGeometryId; FamilyHypothesisId and CapitalThesisId remain distinct.
- V59 family-native minimal-coordinate manifold, pure X/A/B/C projected PRZ, AB=CD subtype algebra and terminality retained.
- Continuous pre-entry Alpha features may rank research but cannot grant capital without burned-calibration evidence.
- Family/Route-native Convex Capture and bounded Runner are research counterfactuals using prior-bar MFE only.
- Fibonacci Grid is a core execution Alpha layer, never recovery.

## Fibonacci Grid
Fractions capped at 0/.236/.382/.618. Legacy control: 3/7,2/7,1/7,1/7. Adaptive challenger is monotonic:
Trend .40/.30/.20/.10 (max 4); Exhaustion .65/.35 (max 2); Transition .50/.30/.20 (max 2-3).
Whole-basket risk includes filled+pending+spread+commission+slippage stress and remains <=1%. Minimum volume may skip legs, never expand risk. Deeper pending legs cancel once MFE>=+0.50R or thesis/risk/session validity ends.

## Fixed causal variants
A V60_CORE_L0_BASELINE
B V60_CORE_L0_FAMILY_CAPTURE
C V60_LEGACY_FIB_GRID_CAPTURE
D V60_ADAPTIVE_FIB_GRID_CAPTURE

## Validation order
Gate0 evidence integrity -> Gate1 mathematical/grid/capture contracts -> burned C1/C2/C3 temporal cross-validation -> paired same-geometry counterfactual -> DEV 2024H2/2025H1/2025H2 (4x3 jobs) -> stress -> 2026H1 untouched validation -> $100/$150/$200/$300/$500/$1000 -> freeze -> one Fresh 2020H1 pair.

AB=CD standalone capital remains OFF. Grid/Runner/Continuous Alpha cannot be promoted by lowering thresholds.

Research leap objectives, not guarantees: >=100 robust trades/year if physically supported, Net >=2x V51 step-change target, PF>=2.5, expectancy >= V51, WR 60-65% stretch, DD <=4.49784% and preferably <=3.5%, P95 winner and max winner improved without OOS degradation.
