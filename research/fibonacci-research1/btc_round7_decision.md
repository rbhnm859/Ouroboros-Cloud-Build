# BTC Round7 M30 Sell Inverse Veto Decision

Primary A/B run: `34226137393`
Untouched prior-6m validation run: `34227038850`
Round7 build commit: `3a14aceac0057e563ec5b2e86217897afc72c77b`
Symbol: `BITCOIN`
Execution timeframe: H1
Risk: 1% equity
Primary cost: spread 0 + commission 65 / million
Harsh cost: spread 1500 + commission 100 / million

## Hypothesis

Keep the H1 Reciprocal ABCD Growth Champion unchanged for Buy. For H1 Sell, reject the entry when a recent valid, structurally non-invalidated M30 Reciprocal ABCD state is also Sell. Test M30 state ages 4, 8 and 12 against the unchanged Champion.

## Studied 6-month A/B: 2026-03-08 through 2026-09-08

| Profile | Trades | ROI | PF | Max DD | OOS ROI | FULL6 Harsh ROI | FULL6 Harsh PF |
|---|---:|---:|---:|---:|---:|---:|---:|
| Champion | 37 | +31.82% | 2.68 | 4.40% | +7.74% | +15.08% | 1.63 |
| Inverse Age4 | 35 | **+35.88%** | **3.29** | 4.40% | +7.74% | **+18.83%** | **1.90** |
| Inverse Age8 | 34 | +32.93% | 3.08 | 5.90% | +7.71% | +19.97% | 2.01 |
| Inverse Age12 | 33 | +34.82% | **3.37** | 4.53% | +7.71% | **+21.16%** | **2.12** |

### Directional detail

Champion FULL6 Sell:
- 21 trades
- PF 1.55
- net about +$828.33

Inverse Age4 FULL6 Sell:
- 19 trades
- PF **2.02**
- net about **+$1,190.78**

Inverse Age4 FULL6 harsh Sell:
- PF **1.56**
- net about **+$698.68**

Inverse Age12 FULL6 Sell:
- 17 trades
- PF 2.02
- net about +$1,091.70

Inverse Age12 FULL6 harsh Sell:
- PF 1.87
- net about +$911.56

Age4 improves normal-cost ROI by +4.06 percentage points versus Champion while removing only two trades and keeping the same reported max drawdown. Age12 is the strongest harsh-cost variant but has slightly higher normal max drawdown and fewer trades.

## Untouched prior six months: 2025-09-08 through 2026-03-07

This period was not used to form the inverse-veto hypothesis.

| Profile | Trades | ROI | PF | Max DD | Harsh ROI | Harsh PF |
|---|---:|---:|---:|---:|---:|---:|
| Champion | 17 | -0.88% | 0.92 | 5.90% | -1.14% | 0.90 |
| Inverse Age4 | 17 | -0.88% | 0.92 | 5.90% | -1.14% | 0.90 |
| Inverse Age12 | 17 | -1.10% | 0.90 | 6.19% | -1.39% | 0.88 |

Age4 is exactly identical to the Champion over this untouched period. Therefore the prior-six-month test does **not** independently confirm the inverse-veto edge; the age-4 veto did not materially change the executed trade path in that period. Age12 is slightly worse and is not preferred.

## Final decision

**Do not replace the Production Research Growth Champion yet.**

Promote `Inverse Age4` only to **Experimental Challenger** status.

Rationale:
1. Age4 materially improves the studied 2026-03 to 2026-09 period: ROI, PF, Sell PF and harsh-cost performance improve without increasing reported max DD.
2. However, the inverse-veto hypothesis was discovered from analysis of the same studied six-month period in Round6. Therefore that improvement is not fully independent evidence.
3. The untouched preceding six months neither confirms nor falsifies Age4 because its executed trades are identical to the Champion there.
4. Age12 is not promoted because it is slightly worse than Champion in the untouched prior-six-month period.
5. The improvement in Age4 is currently driven by a very small number of vetoed Sell events; more independent events are required before production promotion.

## Current status

Production research anchor:
- H1 Reciprocal ABCD Growth Champion
- M30 inverse-veto OFF

Experimental challenger:
- H1 Reciprocal ABCD
- Buy unchanged
- Reject H1 Sell when a valid M30 Reciprocal ABCD Sell state exists
- M30 state max age = 4 bars
- Risk = 1%
- Max Open Positions = 1

No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging.

## Recommended next research

Stop tuning M30 age. Do not optimize 3/4/5/6 bars around the observed winner.

Next priority should be one of:
1. extend untouched historical / forward validation until enough independent M30-veto Sell events exist; and/or
2. begin MFE/MAE exit research on the unchanged H1 Growth Champion, because entry-side M30 filtering now has too few independent events to justify more parameter tuning.
