# xauusd_2 — Predictive Harmonic PRZ Engine

Independent Gold/XAUUSD cTrader cBot architecture. It does not replace xauusd_1 or the frozen BTC branches.

## v2.2 architecture

- Host / execution timeframe: M5.
- Pattern timeframe: M15.
- Context timeframe: H1.
- M15 builds confirmed X-A-B-C pivots and projects D / PRZ before D becomes a confirmed pivot.
- Families: AB=CD, Gartley, Bat, Butterfly, Crab.
- A completed M15 bar touching the PRZ arms one candidate.
- M5 then evaluates four execution rules: engulfing, rejection wick, micro-structure break, and momentum body.
- Default entry requires 2 of 4 M5 rules, while price remains within 0.45 M15 ATR of the PRZ.
- H1 EMA alignment remains a soft score rather than a hard rejection gate.
- Hard execution controls remain: spread/M15-ATR gate, minimum RR, one open position, fixed-risk volume sizing, broker volume normalization, margin check, max trades/day, and max daily realized loss.
- No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging logic.

## Default validation settings

- Symbol: XAUUSD
- Host period: M5
- Backtest data: M1
- Test window: 2026-06-09 to 2026-09-09
- Initial balance: $10,000
- Risk: 0.50% per trade
- Standard cost: spread 17.42, commission 35
- Harsh cost: spread 30, commission 50

## Promotion rule

v2.2 is only worth preserving if the M5 execution layer raises trade quality versus predictive v1 and armed-M15 v2.1 without collapsing back to the 1–2 trade regime. Compare Standard and Harsh results using trades, net profit, ROI, profit factor, max equity drawdown, pattern x direction attribution, and session attribution.
