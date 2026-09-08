# BTC Round8 MFE/MAE + Breakeven Exit Decision

Excursion run: `34238032957`
Breakeven A/B run: `34238809899`
Symbol: `BITCOIN`
Execution timeframe: H1
Risk: 1% equity
Primary cost: spread 0 + commission 65 / million
Harsh cost: spread 1500 + commission 100 / million

## Stage 1 — unchanged Champion excursion instrumentation

The instrumentation reproduced the existing Growth Champion exactly on the recent six months:
- 37 trades
- 24 wins
- ROI +31.82%
- PF 2.68
- Max DD 4.40%

FULL12 (2025-09-08 through 2026-09-08):
- 54 trades
- 30 wins
- ROI +30.85%
- PF 2.03
- Max DD 5.92%

### MFE / MAE evidence

FULL12 losers: 24 total.
- 10 losers (41.7%) reached +0.50R before eventually losing.
- 8 losers (33.3%) reached +0.75R before eventually losing.
- 4 losers (16.7%) reached +1.00R before eventually losing.
- 2 losers (8.3%) reached +1.25R before eventually losing.

Direction split at +0.75R:
- Buy: 5 of 10 losing Buy trades reached +0.75R then later lost.
- Sell: 3 of 14 losing Sell trades reached +0.75R then later lost.

This justified direct Breakeven A/B rather than assuming MFE implies a profitable stop-management rule.

## Stage 2 — direct Breakeven A/B

| Profile | FULL12 ROI | FULL12 PF | FULL12 DD | FULL6 ROI | FULL6 PF | FULL6 Harsh ROI | PRE6 ROI | PRE6 Harsh ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Control | **+30.85%** | **2.03** | 5.92% | **+31.82%** | **2.68** | +15.08% | -7.27% | -10.58% |
| BE 0.50R all | +13.88% | 1.62 | **4.33%** | +11.00% | 1.71 | +2.27% | -3.34% | -5.02% |
| BE 0.75R all | +21.32% | 1.84 | 4.41% | +17.99% | 1.98 | +7.91% | **-2.63%** | -5.38% |
| BE 1.00R all | +24.99% | 1.91 | 4.40% | +25.92% | 2.45 | **+21.49%** | -6.16% | -8.09% |
| BE 0.75R Buy-only | +24.38% | 1.88 | 6.49% | +23.72% | 2.34 | +9.88% | -3.60% | -7.25% |
| BE 0.75R Sell-only | +25.27% | 1.90 | 4.68% | +27.86% | 2.53 | +14.34% | -6.46% | -8.81% |

## Interpretation

1. No tested Breakeven profile beats the Control on normal-cost Growth performance across FULL12 and FULL6.
2. 0.50R is too early and destroys a large portion of the strategy edge.
3. Buy-only 0.75R is also rejected despite the MFE observation; the actual price-path ordering causes profitable trades to be cut too often.
4. Sell-only 0.75R reduces drawdown slightly but still lowers normal ROI.
5. 1.00R all-direction Breakeven is the strongest high-cost defensive variant: recent FULL6 harsh improves from +15.08% / PF 1.63 to +21.49% / PF 2.26, with lower DD. However normal FULL6 ROI falls from +31.82% to +25.92%, so it is not a Growth replacement.
6. PRE6 remains negative for every profile, showing that exit management alone does not repair weak historical regimes.

## Partial TP screening

Using the recorded MFE path, a simple path-consistent approximation of taking 25–50% partial profit at 0.75R or 1.00R reduces total realized R in both FULL12 and FULL6. This is not a substitute for a full partial-close backtest, but it is strong enough evidence not to prioritize Partial TP next.

## Decision

**Keep the Production Research Growth Champion unchanged.**

Default:
- H1 Reciprocal ABCD Growth Champion
- Breakeven OFF
- M30 inverse-veto OFF in production research anchor
- Risk 1%
- Max Open Positions 1

Experimental defensive exit challenger:
- Breakeven trigger = 1.00R
- Apply Buy = true
- Apply Sell = true
- Use only as a research / harsh-cost defensive candidate, not the default.

Do not promote:
- BE 0.50R all
- BE 0.75R all
- BE 0.75R Buy-only
- BE 0.75R Sell-only

## Recommended next exit research

Do not micro-optimize Breakeven thresholds around 0.9/1.0/1.1R.

Next priority: **post-exit shadow continuation research** on unchanged Champion winners. After the original TP closes a trade, continue observing the same directional move without opening a real position and measure whether price reaches 2.0R / 2.2R / 2.5R within fixed horizons. This is necessary before testing wider TP because in-position MFE is censored by the existing TP.

No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging.
