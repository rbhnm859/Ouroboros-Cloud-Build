# HarmonyBot V71 — Unified Harmonic Auction Rebase

## Root cause addressed
V71 evidence shows both filter stacking and indiscriminate all-family release fail for opposite reasons. The remaining bottleneck is MaxActiveBasket=1 winner selection: a weaker opportunity can consume the only slot before a stronger harmonic thesis becomes executable.

## Architecture
Detection keeps all 12 canonical families visible. Hard vetoes remain restricted to canonical identity/integrity, completed-bar structure, structural invalidation, minimum Net RR >= 2, institutional session/spread, unique thesis, single-basket, broker margin/protection and whole-basket risk legality.

Family/route context is reconstructed family-native first. If both family-native and legacy routes return NO_TRADE, a pre-entry soft fallback route is assigned from transition/conflict/extension state; this preserves previously rejected but positive calibration supply without weakening safety.

Capital ranking uses one Unified Harmonic Opportunity Score:
- geometry and PRZ precision,
- confidence, time symmetry and pivot quality,
- completed-M1 execution confirmation,
- net RR,
- H4/H1 compatibility as a soft score,
- regime efficiency/ATR/extension/trend as a soft score,
- AB=CD completion confluence,
- bounded calibration-only family/route prior,
- age, spread and expected slot-duration opportunity-cost penalties.

No future MFE/MAE, realized outcome, future bar or Fresh/Validation data can enter the score.

## Real-time auction
When the slot is free, newly armed candidates receive a 1-minute minimum comparison window. If multiple candidates are close, the auction may wait up to 4 minutes. A dominant score lead can execute earlier. This is real-time waiting, not lookahead.

## Supply fixes
PortfolioMaxCandidates legal ceiling is widened from 12 to 32, enabling the intended 24-candidate research pool. ParkedHardLifetimeMinutes is widened from the fixed 180-minute contract to 120–360 so the preregistered 240-minute queue is actually legal.

## Variants
A: exact truth control.
B: previous best Structural Rebase control.
C: Unified Score + family-native-first soft route + all-family candidate pool + single-leg, 1% risk.
D: C + real-time auction, single-leg, 1% risk.
E: D + non-blocking post-selection family-native Fibonacci Grid, 1% risk.
F: E + adaptive risk up to 5%, research-only and never eligible for V72 promotion.

Only C/D/E may promote, and only after beating the immutable V51 floor with all three 2021–2023 calibration years positive. A frozen winner then proceeds to the already-observed DEV stress windows. Validation and Fresh stay locked.
