# Round25 Results — Causal Lane Quality

GitHub Actions run: 34344146868

## 3-year Standard screen (2023-09-08 to 2026-09-08)

Frozen Round22 control:
- Trades: 256
- ROI: 26.55%
- Net: +2655.20
- PF: 1.22
- Max equity DD: 21.8930%

Profiles:

### Responsive — selected
- window=4
- min samples=3
- weak mean R <= -0.05 => 0.60x risk
- strong mean R >= +0.20 => 1.10x risk
- Trades: 256
- ROI: 28.09%
- Net: +2809.26
- PF: 1.26
- Max equity DD: 17.5507%
- Passed all four 3Y gates.

### Balanced
- Trades: 256
- ROI: 26.55%
- Net: +2654.56
- PF: 1.23
- Max equity DD: 18.2276%
- Failed ROI improvement gate.

### Stable
- Trades: 255
- ROI: 23.93%
- Net: +2392.78
- PF: 1.20
- Max equity DD: 21.7312%
- Failed ROI/PF gates.

## Recent 1-year validation of Responsive

Standard:
- Trades: 95
- ROI: 36.18%
- Net: +3617.57
- PF: 1.87
- Max equity DD: 4.9295%

Round22 comparison:
- 95 trades / 39.93% ROI / PF 1.95 / DD 5.6463%

Responsive reduced DD but failed recent ROI and PF no-regression gates.

Harsh:
- Trades: 95
- ROI: 11.98%
- Net: +1198.43
- PF: 1.27
- Max equity DD: 5.6010%

Round22 Harsh comparison:
- 95 trades / 18.12% ROI / PF 1.39 / DD 6.4833%

Responsive again reduced DD but materially regressed ROI/PF.

## Lane attribution

3Y Responsive minus Round22 control net contribution:
- H1 Buy: +304.67
- H1 Sell: -167.32
- M30 Buy: -45.48
- M30 Sell: +62.85
- R21 bypass lanes: essentially unchanged/frozen

Recent 1Y Responsive minus Round22:
- H1 Buy: +64.67
- H1 Sell: -315.95
- M30 Buy: -75.46
- M30 Sell: -48.73
- R21M30 Buy: unchanged

This shows the same rolling mean-R rule is not suitable for every lane. It helps H1 Buy over both horizons and helps M30 Sell over 3Y, but it suppresses H1 Sell recovery and hurts M30 Buy.

## Decision

`promotion_eligible = false`.

Round22 remains the Standard Champion. No Round25 Mobile release should replace it.

## Next evidence-based experiment

Do not retune all thresholds globally. The next controlled experiment should make lane adaptation selective:

1. Apply causal lane-quality adaptation to H1 Buy only, or H1 Buy + M30 Sell.
2. Keep H1 Sell and M30 Buy at Round22 fixed risk until a separate fast-recovery rule is validated.
3. Preserve MaxOpenPositions=1 and all existing entry/exit gates.
4. Do not enable the 1.8–2.0 ATR expansion yet.

The objective is to retain Round25's 3Y H1 Buy gain and DD reduction while restoring Round22's recent-year H1 Sell/M30 contribution.
