# BTC Monthly Growth v3 — Quality Recovery

Status: RESEARCH CANDIDATE — NOT CHAMPION

Base branch commit: `05768c84d6a6cf73e048fb00f6d80604b1a730f4`
Champion remains: Round22 Standard.
Round26 remains the exact-parity modular baseline.
Growth2 is rejected and must not be promoted.

## Growth2 rejection evidence

- 3Y aggregate: 260 trades, ROI +38.01%, PF 1.33, Max Equity DD 15.65%.
- Recent aggregate: 101 trades, ROI +34.73%, PF 1.92, DD 5.65%.
- Growth2 attribution 3Y: 62 trades, net -54.55, PF 0.8032.
- Growth2 attribution recent: 22 trades, net -74.47, PF 0.4299.
- Fixed yearly segment Y2: ROI -7.32%, PF 0.78.
- Harsh 3Y: PF 1.08, DD 18.94%.
- Harsh recent: PF 1.40, DD 6.30%.

Promotion: REJECTED.

## v3 design constraint

Do not alter Round22 or Round26. Do not increase risk to manufacture return. Preserve the shared Store portfolio risk/execution layer, hard single-position/no-hedging rule, mandatory SL/TP, equity-percentage risk and emergency protection close.

The v3 candidate will replace only the rejected Growth2 alpha entry logic. It must keep independent attribution and use the hierarchy H4/H1 trend -> M30 pullback -> momentum recovery -> entry. The first optimization target is signal quality, especially eliminating the negative Growth2 entry family, before seeking more trade count.

## Frozen promotion gates

- 3Y trades >= 250; target >= 300 after new alpha.
- 3Y PF >= 1.40.
- 3Y Max DD <= 15–18%.
- Recent 1Y PF >= 1.80.
- Recent 1Y DD <= 6%.
- Harsh recent PF >= 1.35.
- At least two positive fixed yearly segments.
- No catastrophic worst year.
- Independent alpha attribution must be positive and cannot be explained by increased risk.

No candidate may replace Champion unless all frozen gates pass.
