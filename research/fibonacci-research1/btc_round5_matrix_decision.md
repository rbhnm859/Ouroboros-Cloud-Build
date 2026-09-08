# BTC Round5 Timeframe × Pattern Matrix decision

Run: `34221848491`
Commit: `d636361ec8a43dd06a0de0c1b6827677acda80ca`
Symbol: `BITCOIN`
Risk: 1% equity
Development window: 2026-03-08 through 2026-08-08
Frozen OOS: 2026-08-09 through 2026-09-08
Primary cost: spread 0 + commission 65 / million
Harsh cost: spread 1500 + commission 100 / million

## Development matrix

| Cell | Trades | ROI | PF | Max DD | Decision |
|---|---:|---:|---:|---:|---|
| M1 ABCD | 763 | -92.47% | 0.69 | 93.13% | Reject as standalone engine; H1 execution parameters do not transfer to M1 |
| M5 ABCD | 300 | -61.53% | 0.67 | 62.15% | Reject as standalone engine |
| M15 ABCD | 114 | -37.25% | 0.56 | 43.87% | Reject as standalone engine |
| M15 Reciprocal ABCD | 76 | -35.53% | 0.44 | 36.93% | Reject as standalone engine |
| M30 ABCD | 44 | -8.02% | 0.76 | 20.90% | Reject |
| M30 Reciprocal ABCD | 44 | +16.52% | 1.58 | 5.80% | Advance to frozen validation |
| H1 Reciprocal ABCD | 30 | +22.64% | 2.43 | 4.38% | Anchor / advance |
| H4 Reciprocal ABCD | 7 | +0.17% | 1.04 | 3.71% | Advance only as weak macro-state candidate |
| H4 Gartley | 0 | 0% | 0 | 0% | Too sparse |
| H4 Bat | 0 | 0% | 0 | 0% | Too sparse |
| H4 Crab | 0 | 0% | 0 | 0% | Too sparse |
| D1 Butterfly | 1 | +1.41% | n/a | 0.90% | Too sparse to promote |
| D1 Gartley/Bat/Crab/Deep Crab | 0 | 0% | 0 | 0% | Too sparse |

## Frozen validation

| Cell | FULL6 Trades | FULL6 ROI | FULL6 PF | FULL6 DD | OOS ROI | OOS PF | OOS Harsh ROI | OOS Harsh PF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 Reciprocal ABCD | 37 | +31.82% | 2.68 | 4.40% | +7.74% | 4.17 | +3.30% | 1.75 |
| M30 Reciprocal ABCD | 52 | +15.49% | 1.44 | 5.85% | -0.45% | 0.92 | -5.58% | 0.20 |
| H4 Reciprocal ABCD | 8 | +1.84% | 1.40 | 3.84% | +1.69% | n/a (1 winning trade) | +1.66% | n/a |

Harsh FULL6:
- H1 Reciprocal ABCD: +15.08% ROI, PF 1.63, DD 6.75%.
- M30 Reciprocal ABCD: +8.57% ROI, PF 1.23, DD 7.27%.
- H4 Reciprocal ABCD: +2.02% ROI, PF 1.47, DD 3.59%, but only 8 trades.

## Directional evidence

H1 Reciprocal ABCD FULL6:
- Buy: 16 trades, 13 wins, 81.25% win rate, net +2353.78, PF 6.91.
- Sell: 21 trades, 11 wins, 52.38% win rate, net +828.33, PF 1.55.

M30 Reciprocal ABCD FULL6:
- Buy: 18 trades, 7 wins, 38.89% win rate, net +109.64, PF 1.09.
- Sell: 34 trades, 18 wins, 52.94% win rate, net +1439.68, PF 1.64.

H4 Reciprocal ABCD FULL6:
- Only 8 trades total; sample is too small for a hard gate.

## Decision

1. Keep H1 Reciprocal ABCD as the sole promoted execution engine. It is the only cell with strong development, OOS and harsh-cost robustness.
2. Do not promote M30 Reciprocal ABCD as an independent execution engine. Its positive FULL6 result fails frozen OOS and collapses under OOS harsh costs.
3. Preserve M30 Reciprocal ABCD as a directional research state. Its Sell side is materially stronger than its Buy side and is a plausible confirmation input for H1 Sell trades.
4. H4 Reciprocal ABCD remains a soft / shadow macro-bias state only. Eight FULL6 trades are insufficient for a production hard veto.
5. Do not use full harmonic trade engines on M1/M5/M15 with H1 parameters. Those timeframes should be redesigned as timing/confirmation features rather than independent entries.
6. D1 full harmonics at Score 84 / Pivot 2/2 are too sparse. D1 should use a broader structural regime detector or relaxed state-only geometry if it is retained.

## Next causal hypothesis

Build a narrowly scoped hybrid candidate:
- H1 Reciprocal ABCD remains the entry engine.
- H1 Buy logic remains unchanged.
- H1 Sell is allowed only when a recent valid M30 Reciprocal ABCD state is Sell-aligned (with age decay / structural invalidation).
- H4 is logged as a shadow bias first, not used as a hard gate.
- Max Open Positions remains 1.
- No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging.

Validate the hybrid against the unchanged H1 Growth Champion on development folds, frozen OOS, FULL6 and harsh costs. Do not promote unless Sell PF/DD improve without materially damaging total ROI or OOS robustness.
