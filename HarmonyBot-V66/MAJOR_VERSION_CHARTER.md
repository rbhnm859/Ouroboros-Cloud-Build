# HarmonyBot V66 — Harmonic Evidence Accumulator

## Root cause carried forward
V65 proved that requiring thesis proof repairs the worst regimes, but exact event ordering destroyed too much throughput and removed valid winners. The clearest example was a +8.1R H22 AB=CD winner that repeatedly showed route proof but failed the exact sequential stage contract.

## V66 single architecture change
V66 clean-rebases V64 and freezes the V64 execution/risk kernel.

After PRZ touch, V66 accumulates orthogonal M1 evidence for up to six completed bars:
- location: reclaim / inside PRZ / retest
- structure: BOS1 / BOS2 / displacement
- reaction: rejection / failed-extension / sweep / deceleration
- directional / displacement confirmation

Evidence persists across the six-bar window. It does not need to occur on the same candle or in a fixed order.

Family + Route define the minimum evidence set:
- AB=CD: deceleration + location + structure; exhaustion additionally needs failed-extension/sweep.
- Shark / 5-0: location + failed-extension/sweep + structure + retest/directional.
- Cypher: location + rejection + structure.
- Retracement families: location + rejection/failed-extension + structure.
- Extension families: sweep + failed-extension + location + structure.
- Trend route: location + structure + reaction.
- Exhaustion route: location + failed-extension/sweep + rejection/BOS/displacement.
- Transition route: location + BOS2 + rejection.

## Frozen from V64
Harmonic detection, PRZ, H4/H1 context, M15 geometry, route-native execution, conditional Fibonacci re-proof, runner, risk, margin, broker protections, single basket, no hedging/Martingale/DCA/recovery, and small-capital architecture remain unchanged.

## Causal control
V66_V64_CONTROL must reproduce V64_PRODUCT trade-for-trade.
V66_PRODUCT differs only in M1 evidence accumulation.

## Governance
2021/2022 = preservation stress.
2023 = known bad-regime stress, not OOS.
2024H2/2025H1/2025H2 = DEV.
2026 Q1/Q2 = validation only after Alpha breakthrough.
2020H1 = Fresh only after commercial freeze.

No V66.x patch chain. Architecture failure means HOLD and a new major-version decision.
