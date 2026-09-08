# BTC Round 3 decision

Run: `34214068752`
Commit: `ed3643f426074ea762dc6115876741b058124cff`
Candidate: `Fibonacci-v0.5.0-btc-round3`
Symbol: `BITCOIN`
Timeframe: `H1`
Backtest data mode: server `M1`
Research balance: USD 10,000
Risk: 1% equity
Primary commission stress used for selection/validation: USD 65 / million, spread 0
Harsh validation: spread 1500 price-points-equivalent CLI setting + USD 100 / million commission

## Decision

Do **not** replace the Round 2 growth champion with a Round 3 sell filter as a universal default. Round 3 did not produce a Pareto improvement in both normal-cost ROI/trade count and drawdown.

Maintain two frozen presets:

1. **Growth Champion — `btc_r3_champion`**
   - Equivalent trading logic to Round 2 `btc_recip_p2_s84`.
   - Reciprocal ABCD only, Pivot 2/2, tolerance 6%, minimum score 84.
   - FULL6: 37 trades, ROI 31.82%, PF 2.68, max equity DD 4.40%, Return/DD 7.24.
   - FULL6 harsh: ROI 15.08%, PF 1.63, max equity DD 6.75%.
   - OOS: 7 trades, ROI 7.74%, PF 4.17, DD 2.83%.
   - OOS harsh: ROI 3.30%, PF 1.75, DD 4.12%.

2. **Robust Challenger — `btc_r3_sell_score88`**
   - Same Buy logic; only Sell minimum pattern score is raised from 84 to 88.
   - FULL6: 34 trades, ROI 30.35%, PF 2.87, max equity DD 3.63%, Return/DD 8.37.
   - FULL6 harsh: ROI 17.56%, PF 1.85, max equity DD 4.16%, Return/DD 4.22.
   - OOS: 7 trades, ROI 7.74%, PF 4.17, DD 2.83%.
   - OOS harsh: ROI 3.30%, PF 1.75, DD 4.12%.
   - FULL6 Sell: 18 trades, net +702.90, PF 1.57.
   - FULL6 harsh Sell: 18 trades, net +570.32, PF 1.46.

## Interpretation

The Sell score-88 gate removes three six-month Sell trades. Normal-cost FULL6 ROI falls by 1.47 percentage points and trade count falls from 37 to 34, but PF rises from 2.68 to 2.87 and max DD falls from 4.40% to 3.63%. Under harsh costs, ROI improves from 15.08% to 17.56%, PF from 1.63 to 1.85, and max DD falls from 6.75% to 4.16%.

Because the project objective prioritizes trade count and ROI while controlling DD, the Growth Champion remains the primary preset. The score-88 profile is retained as the robustness preset rather than replacing the growth preset.

No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging was introduced.
