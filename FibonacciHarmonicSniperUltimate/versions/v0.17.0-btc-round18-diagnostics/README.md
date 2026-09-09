# Fibonacci BTC Round18 Diagnostics

This is a logic-neutral instrumentation fork of the frozen Round17 M30-half-risk source.

## Frozen baseline
- Source version: `v0.16.0-btc-round17-m30-half-risk`
- H1 risk: 1.0% equity
- M30 risk: 0.50% equity
- MaxOpenPositions: 1
- MaxTradesPerDay: 6
- H1 health gate: >=2 wins in the last 3 closed H1 trades
- H1 pattern score: 84
- Ratio tolerance: 6%
- Max pattern age: 16 bars
- Max entry distance: 1.80 ATR
- Cooldown: 2 H1 bars / 4 M30 bars in M30 engine

## Round18 diagnostics change
- Detects an actual M30 Reciprocal ABCD candidate before the Round16 health/shared-limit execution gates.
- Does **not** change the original execution gate order or risk sizing.
- Logs candidate direction, score, D age, EMA alignment, confirmation, H1 health sample/win counts, nearest same-direction H1 state age, open-position state, day-limit state and final gate.
- H1 trade comments are tagged `H1|...`; M30 comments already use `M30|...` for direct attribution.
- The exact source is stored as gzip+base64 payload parts and reconstructed during CI; SHA-256 is verified before build.

## Acceptance test for diagnostics-only build
The Round18 diagnostics run should reproduce Round17 economics on the same 2025-09-08 to 2026-09-08 test window:
- Standard baseline: 94 trades, ROI +38.48%, PF 1.85, max equity DD 5.92%
- Harsh baseline: 92 trades, ROI +19.25%, PF 1.40, max equity DD 7.67%

Any material divergence means the diagnostics patch is not logic-neutral and must be fixed before directional expansion.
