# BTC Round6 H1 + M30 Sell Confirmation A/B Decision

Run: `34225018349`
Commit: `8f6a0fa1cf4d7c5ff9e7bfc433760fa39c1f34d9`
Symbol: `BITCOIN`
Execution timeframe: H1
Risk: 1% equity
FULL6: 2026-03-08 through 2026-09-08
Frozen OOS: 2026-08-09 through 2026-09-08
Primary cost: spread 0 + commission 65 / million
Harsh cost: spread 1500 + commission 100 / million

## Hypothesis

Keep the H1 Reciprocal ABCD Growth Champion Buy path unchanged. Allow an H1 Sell only when a recent valid, structurally non-invalidated M30 Reciprocal ABCD state is also Sell. Test M30 state max ages 4, 8 and 12 bars against the unchanged Champion control.

## Results

| Profile | FULL6 Trades | FULL6 ROI | PF | Max DD | OOS ROI | OOS PF | OOS Harsh ROI | FULL6 Harsh ROI | FULL6 Harsh PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Champion control | 37 | +31.82% | 2.68 | 4.40% | +7.74% | 4.17 | +3.30% | +15.08% | 1.63 |
| Hybrid age 4 | 21 | +15.35% | 2.44 | 3.73% | +4.37% | 4.61 | +0.49% | +4.42% | 1.30 |
| Hybrid age 8 | 25 | +13.88% | 1.99 | 4.57% | +3.27% | 2.44 | -0.66% | -0.14% | 0.99 |
| Hybrid age 12 | 25 | +13.88% | 1.99 | 4.57% | +3.27% | 2.44 | -0.66% | -0.14% | 0.99 |

## Sell-side evidence

Champion FULL6 Sell:
- 21 trades
- PF 1.55
- net about +$828.33

Hybrid age 4 Sell:
- 2 trades
- 0 winners
- both losing

Hybrid age 8 / 12 Sell:
- 6 trades
- 1 winner
- Sell PF about 0.29 in normal FULL6

Trade-by-trade intersection against the Champion is especially important:
- The 6 Champion Sell trades that also satisfy the age-8/12 M30 Sell-alignment condition sum to about **-$515.85**.
- The remaining 15 Champion Sell trades that do **not** satisfy that M30 Sell-alignment condition sum to about **+$1,344.18**, with an approximate standalone PF of **2.70**.
- For age 4, the 2 aligned Champion Sell trades sum to about **-$339.19**; the other 19 Champion Sell trades sum to about **+$1,167.52**, approximate PF **2.01**.

This means the simple same-direction M30 confirmation selects a materially worse subset of H1 Sell trades in this sample.

## Decision

**REJECT Round6 as a promotion candidate.**

Do not replace the current H1 Reciprocal ABCD Growth Champion. The hypothesis `H1 Sell + recent M30 Sell alignment = higher-quality Sell` is falsified by this six-month A/B test and frozen OOS/cost stress.

Keep:
- H1 Reciprocal ABCD Growth Champion as the production research anchor.
- H1 Buy logic unchanged.
- Max Open Positions = 1.
- No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging.

## Next causal hypothesis

The data supports testing the **opposite use** of M30 state:

- H1 Buy remains unchanged.
- H1 Sell remains allowed by default.
- A recent valid M30 Reciprocal ABCD **Sell** state becomes a veto / risk warning rather than a confirmation.
- Compare `reject H1 Sell when M30 is Sell-aligned` vs Champion.
- Optionally test a softer version that reduces Sell risk instead of fully vetoing it.
- H4 remains shadow-only until its sample is larger.

This inverse-veto hypothesis must be backtested directly because portfolio occupancy changes can create additional H1 opportunities; the trade-intersection arithmetic above is evidence, not a substitute for a full backtest.
