# Round28 Results — Continuous Quality Risk

GitHub Actions run: 34404822994

## 3Y Standard control
- Trades: 256
- ROI: 26.55%
- Net: +2655.20
- PF: 1.22
- Max equity DD: 21.8930%

## Selected profile: h1-protect
Config: H1 Sell min scale 0.35 / gamma 1.25; M30 Buy min scale 0.80 / gamma 0.85.
- Trades: 256
- ROI: 24.39%
- Net: +2439.29
- PF: 1.23
- Max equity DD: 20.0630%
- 3Y promotion gates: only trade-count gate passed; ROI/PF/DD gates failed.

Other 3Y profiles:
- balanced: 256 trades / ROI 24.54% / PF 1.22 / DD 20.42%
- m30-protect: 256 trades / ROI 23.38% / PF 1.21 / DD 20.84%

## Fixed annual validation for h1-protect
- 2023-09-08 to 2024-09-08: 90 trades / ROI -0.77% / PF 0.98 / DD 11.85%
- 2024-09-08 to 2025-09-08: 60 trades / ROI -5.82% / PF 0.80 / DD 10.83%
- 2025-09-08 to 2026-09-08: 95 trades / ROI +37.90% / PF 2.04 / DD 4.78%

## Harsh
- Full 3Y: 246 trades / ROI -2.87% / PF 0.97 / DD 23.92%
- Recent 1Y: 95 trades / ROI +17.43% / PF 1.43 / DD 4.98%

## Decision
`promotion_eligible = false`.

Round28 is not promoted. It improved the weak 2024-2025 slice and recent-year PF/DD, but reduced full-3Y ROI and did not solve long-horizon Harsh profitability. The next experiment should restore M30 Buy to Round22 fixed risk and use macro-asymmetric H1 Sell sizing only when a closed D1 regime is clearly bullish.