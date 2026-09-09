# Round25 — Causal Lane Quality

Round25 tests whether causal, lane-specific risk adaptation can improve the 3-year robustness of the Round22 Standard Champion without changing signal logic or increasing MaxOpenPositions.

## Why

Round24 exposed strong regime dependence over 2023-09-08 to 2026-09-08: 256 trades, 26.55% ROI, PF 1.22, max equity DD 21.89%. The latest year was much stronger than the middle year, and lane attribution changed by regime.

Round25 therefore keeps all entries/exits frozen and adapts risk only from each lane's own already-closed trades:

- H1_BUY
- H1_SELL
- M30_BUY
- M30_SELL

The Round21 bypass lane remains frozen and is excluded from lane-quality state.

## Causal rule

Each closed trade contributes its realized R multiple, clipped to [-1R, +2R], to that lane's rolling queue. No future data, calendar-year labels, or hindsight regime labels are used.

If samples are below the profile minimum, multiplier = 1.00.
If rolling mean R <= weak threshold, risk is reduced.
If rolling mean R >= strong threshold, risk is increased only slightly.
Otherwise multiplier = 1.00.

Signal selection, SL/TP geometry, MaxOpenPositions=1, Round21 bypass logic, score=84, age=16 and entry-distance=1.80 ATR remain frozen.

## Pre-committed profiles

1. Stable: window 6, min samples 4, weak <= -0.10R => 0.70x, strong >= +0.30R => 1.05x.
2. Balanced: window 6, min samples 4, weak <= -0.05R => 0.60x, strong >= +0.25R => 1.08x.
3. Responsive: window 4, min samples 3, weak <= -0.05R => 0.60x, strong >= +0.20R => 1.10x.

## 3Y control

Round22 frozen baseline, 2023-09-08 to 2026-09-08, Standard costs:

- Trades: 256
- ROI: 26.55%
- PF: 1.22
- Max equity DD: 21.89%

Round25 3Y gate:

- trades >= 250
- ROI > 26.55%
- PF > 1.22
- max equity DD < 21.89%

## Recent-1Y no-regression gate

Selected 3Y profile is re-run on 2025-09-08 to 2026-09-08.

Target versus Round22:

- trades >= 95
- ROI >= 39.93%
- PF >= 1.90
- max equity DD <= 5.65%

Harsh validation uses commission=100 and spread=1500; it must not materially regress Round22 Harsh (95 trades / 18.12% ROI / PF 1.39 / 6.48% DD).

Round22 remains Champion unless Round25 clears the validation gates. Round25 does not add the Round24 1.8–2.0 ATR expansion; that remains research-only until sample size is sufficient.
