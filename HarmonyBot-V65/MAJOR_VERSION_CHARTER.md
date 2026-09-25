# HarmonyBot V65 — Harmonic Thesis Completion Engine

## Purpose
V65 changes only the Alpha Engine confirmation layer. V64 execution and risk are frozen.

The failure signature behind V65 is specific: 2023 and 2025H2 losses were concentrated in harmonic trades that produced almost no favorable excursion before adverse excursion, especially trend-aligned AB=CD and Shark setups. That is an entry-thesis failure, not a target/grid/runner failure.

## Frozen from V64
- Harmonic/Fibonacci geometry and PRZ construction.
- H4/H1 context construction and M15 pattern detection.
- V64 route-native execution:
  - Trend aligned: conditional Fibonacci + independent runner.
  - Exhaustion: two-leg conditional Fibonacci.
  - Transition: single entry.
- Conditional .236/.382 staged-entry re-proof.
- .618 shadow only.
- Whole-basket stressed risk <= 1%.
- Broker/min-volume/margin/server-SL protections.
- No duplicate thesis, hedging, Martingale, DCA, recovery/loss averaging, or stop widening.
- $100 small-capital architecture.

## Single V65 alpha change
After PRZ touch, a setup may not become executable from a generic one-bar M1 score.

It must complete a pattern-native harmonic thesis sequence within six completed M1 bars.

For families already covered by the family-completion contract, V65 preserves their native completion semantics. For AB=CD, Shark and Cypher, V65 uses the existing pattern-native microstructure state machine instead of the legacy generic threshold.

A completed native sequence must also satisfy the route-specific M1 proof on the completion bar:
- Trend aligned: reclaim plus break/failure evidence.
- Exhaustion: reclaim + rejection + failed-extension/BOS evidence.
- Transition: reclaim + deeper break + rejection.

No rescue lane is allowed in V65_PRODUCT. If the sequence is incomplete after six bars, the candidate is rejected.

## Causal control
V65_V64_CONTROL must reproduce V64_PRODUCT trade-for-trade. It uses the identical V64 execution/risk path and legacy confirmation behavior.

V65_PRODUCT differs from control only by the thesis-completion state machine.

## Evidence governance
- 2021/2022: preservation stress.
- 2023: known failure-regime stress test; not called OOS.
- 2024H2/2025H1/2025H2: DEV evidence.
- 2026 Q1/Q2: validation only after DEV candidate.
- 2020H1: untouched Fresh only after commercial freeze.

No V65.x patch chain. If the preregistered thesis engine fails, report HOLD and make the next major-version decision from evidence.
