# Fibonacci XAUUSD v3.6 — Commercialization Gate

This gate is intentionally evidence-driven. v3.6 must not be promoted on peak ROI alone.

## Product invariants
- XAUUSD specialization remains explicit.
- Fibonacci / Harmonic signal core remains the primary alpha source.
- Single-position only; no hedging.
- No Grid, Martingale, DCA, Recovery, or Loss Averaging.
- Every trade must have broker-valid SL/TP.
- Fixed/risk-bounded sizing must remain enabled.
- Daily loss protection must survive restart and include floating P/L.
- Mobile/Cloud `.algo` packaging is required before release.

## Commercial promotion gates
1. Build/API integrity: zero compile/runtime protection errors in validation.
2. Execution integrity: no duplicate entry, naked position, invalid SL/TP modification, or opposite simultaneous position.
3. Sample sufficiency: report trade count for every window; no promotion based on a tiny sample.
4. Cross-period robustness: evaluate 3M, 6M, 1Y and segmented/OOS windows.
5. Cost robustness: candidate must survive Standard and Harsh transaction-cost assumptions.
6. Risk-adjusted performance: compare ROI, Profit Factor, Max Drawdown, win rate, net profit, and trade count together.
7. Parameter stability: prefer a broad stable parameter region over the single highest-ROI point.
8. OOS requirement: final candidate must remain profitable/acceptable OOS; IS optimization alone is insufficient.
9. Regression protection: v3.5 remains the reference baseline until v3.6 passes all gates.
10. No fabricated metrics: only cTrader/GitHub Actions backtest outputs are admissible.

## v3.6 optimization policy
The exit sweep is treated as a robustness experiment, not a brute-force profit hunt. TP multiplier / breakeven variants are ranked by cross-window consistency and drawdown-adjusted return. A variant with slightly lower ROI can be promoted over the peak-ROI variant when PF, DD, OOS and harsh-cost resilience are materially better.

## Release evidence table
Populate only from completed backtests.

| Candidate | Window | Cost | Trades | Win rate | ROI | PF | Max DD | Net profit | Status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| pending | pending | pending | — | — | — | — | — | — | WAIT |

## Release decision
Current state: **NOT YET PROMOTED**. The active v3.6 validation must complete before any commercial performance claim or Mobile/Cloud release promotion.
