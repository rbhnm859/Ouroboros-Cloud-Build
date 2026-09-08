# BTC Round4 MTF cross-test decision

Run: `34219381090`
Commit: `8035de5a3a71acbf9423451dee4187c9b2309e80`
Candidate: `Fibonacci-v0.6.0-btc-round4-mtf`
Symbol: `BITCOIN`
Risk: 1% equity
Primary cost: commission 65 / million, spread 0
Harsh cost: spread 1500 + commission 100 / million

## Fixed profiles tested

- `h4_h1_strict`: H1 execution, H4 Reciprocal ABCD must agree for both Buy and Sell.
- `h4_h1_sell_confirm`: H1 execution; only Sell requires H4 Reciprocal ABCD agreement.
- `h1_m30_strict`: M30 execution, H1 Reciprocal ABCD must agree for both Buy and Sell.
- `h1_m30_sell_confirm`: M30 execution; only Sell requires H1 Reciprocal ABCD agreement.

## FULL6 results

| Profile | Trades | ROI | PF | Max DD | Buy | Sell |
|---|---:|---:|---:|---:|---|---|
| h4_h1_sell_confirm | 19 | +18.69% | 3.47 | 2.72% | 19 trades, +1868.82, PF 3.47 | 0 trades |
| h4_h1_strict | 0 | 0.00% | 0.00 | 0.00% | 0 | 0 |
| h1_m30_strict | 14 | -1.10% | 0.90 | 5.29% | 7 trades, +96.90, PF 1.21 | 7 trades, -206.76, PF 0.65 |
| h1_m30_sell_confirm | 28 | -4.31% | 0.80 | 6.24% | 21 trades, -238.44, PF 0.84 | 7 trades, -192.66, PF 0.66 |

## OOS results

| Profile | Trades | ROI | PF | Max DD |
|---|---:|---:|---:|---:|
| h4_h1_sell_confirm | 4 | +4.37% | 4.61 | 2.19% |
| h4_h1_strict | 0 | 0.00% | 0.00 | 0.00% |
| h1_m30_sell_confirm | 6 | -3.95% | 0.30 | 4.66% |
| h1_m30_strict | 4 | -4.61% | 0.00 | 5.27% |

## Harsh-cost observations

- `h4_h1_sell_confirm` FULL6 harsh: +7.74% ROI, PF 1.67, DD 4.11%.
- `h4_h1_sell_confirm` OOS harsh: +0.49% ROI, PF 1.17, DD 4.08%.
- Both H1+M30 profiles remain negative under harsh costs.

## Interpretation

1. Requiring a complete Reciprocal ABCD pattern to be simultaneously active and direction-aligned on H4 and H1 is too restrictive with the current HTF age/pivot geometry. `h4_h1_strict` produced zero trades across FULL3, FULL6 and OOS.
2. `h4_h1_sell_confirm` is the strongest tested profile, but its 19 FULL6 trades are all Buy trades. This means it should be interpreted as a successful Sell rejection / long-only-like filter, not as evidence that strict H4+H1 complete-pattern confluence improves Buy entries.
3. Transplanting the H1 BTC Champion parameters to M30 is not supported. Both H1+M30 profiles lose money in FULL6 and OOS. M30 would require its own geometry/age/pivot/entry calibration before it can be considered again.
4. The next MTF design should use the higher timeframe as a directional state/bias derived from the latest valid HTF structure/pattern, rather than demanding simultaneous completion of a full HTF pattern at the lower-TF entry bar.

## Recommended next design

Keep the H1 Reciprocal ABCD Growth Champion as the execution engine.

Replace strict HTF full-pattern coincidence with an HTF directional-bias state:
- last confirmed HTF harmonic direction,
- bounded validity window,
- structural invalidation to clear the bias,
- optional score decay with age,
- Buy and Sell evaluated separately,
- conflict signals logged as shadow signals,
- Max Open Positions remains 1.

First candidate pair: H4 bias -> H1 execution.

Do not promote H1+M30 at this stage.

No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging was introduced.
