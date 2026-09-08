# BTC Round14 — H1 + M30 Harmonic Portfolio / Signal Overlap Decision

## Scope

Round14 changes no strategy parameters. It compares the frozen H1 Reciprocal ABCD Growth Champion with the frozen Round13 M30 Reciprocal ABCD frequency candidate.

Workflow: `.github/workflows/backtest-fibonacci-btc-round14-overlap.yml`
Run: `34255133036`

## Frozen engines

### H1 Growth Champion
- Pattern: Reciprocal ABCD
- Pivot: 2 / 2
- Ratio tolerance: 6%
- Minimum score: 84
- Max age: 16 H1 bars
- Max entry distance: 1.80 ATR
- Confirmation move: 0.05 ATR
- Candle confirmation: On
- Cooldown: 2 H1 bars
- Risk: 1%

### M30 frequency candidate
- Pattern: Reciprocal ABCD
- Pivot: 2 / 2
- Ratio tolerance: 6%
- Minimum score: 84
- Max age: 32 M30 bars
- Max entry distance: 1.80 ATR
- Confirmation move: 0.05 ATR
- Candle confirmation: On
- Cooldown: 4 M30 bars
- Risk: 1%

## FULL6 overlap findings

- H1: 37 trades, +3182.11 net, PF 2.68.
- M30: 57 trades, +1836.00 net, PF 1.47.
- 12 M30 trades occurred while an H1 position was already open.
- Those 12 overlapping M30 trades were poor: 25.0% win rate, -483.75 net, PF 0.56.
- The 45 M30 trades occurring while H1 was flat were materially stronger: 53.3% win rate, +2319.75 net, PF 1.83.
- H1-flat M30 Sell was strongest: 30 trades, +1611.71 net, PF 1.88.
- H1-flat M30 Buy: 15 trades, +708.04 net, PF 1.74.

This indicates that a shared MaxOpenPositions=1 portfolio naturally removes a disproportionately weak M30 subset.

## FULL6 harsh

- H1: 37 trades, +1508.26 net, PF 1.63.
- M30: 56 trades, +994.92 net, PF 1.24.
- M30 during H1 position: 11 trades, -669.08 net, PF 0.38.
- M30 while H1 flat: 45 trades, +1664.00 net, PF 1.55.
- H1-flat M30 Sell: PF 1.68.
- H1-flat M30 Buy: PF 1.32.

The same overlap effect persists under harsh costs.

## OOS findings

Normal OOS:
- H1: 7 trades, +774.36 net, PF 4.17.
- M30: 10 trades, +23.97 net, PF 1.03.
- M30 while H1 flat: 8 trades, -80.88 net, PF 0.86.
- First-come one-position approximation: 14 trades, +810.27 net, PF 2.11.

Harsh OOS:
- H1: 7 trades, +329.64 net, PF 1.75.
- M30: 9 trades, -484.49 net, PF 0.39.
- M30 while H1 flat: 8 trades, -377.19 net, PF 0.45.
- First-come one-position approximation: 13 trades, -98.41 net, PF 0.90.

## Frequency conclusion

The frequency problem is no longer the main bottleneck.

A causal first-come one-position approximation retains roughly:
- FULL6: 75 trades (29 H1 + 46 M30), PF 2.18 on standalone-net approximation.
- FULL6 harsh: 74 trades (29 H1 + 45 M30), PF 1.60 on standalone-net approximation.

This is well above the original H1-only 37 trades and demonstrates that 50+ trades per six months is structurally achievable without adding non-harmonic entry alpha.

## Robustness conclusion

Do **not** promote raw H1+M30 to Production yet.

Reason:
- Normal FULL6 portfolio overlap looks strong.
- FULL6 harsh also remains positive.
- Normal OOS remains positive.
- Harsh OOS first-come approximation is PF 0.90 and negative net.

Also, first-come portfolio metrics are based on standalone trade histories with separate equity/risk compounding. They are not a substitute for a true combined-account backtest.

## Decision

1. Keep H1 Growth Champion as the Production Research anchor.
2. Keep M30 as a Frequency Engine candidate, not standalone Production.
3. Frequency objective is considered technically solved: 50+ opportunities are available.
4. Next research must test a **true combined-account H1 + M30 Harmonic Portfolio** with shared equity, shared MaxOpenPositions=1, shared daily controls, and explicit engine tagging.
5. Do not add RSI/MACD/ADX or non-harmonic alpha to solve frequency.
6. Do not lower H1 quality gates to chase count.
7. The next combined test must preserve Harmonic-first logic and compare normal/OOS/harsh against H1 Champion.

## Promotion gate for the true combined portfolio

- FULL6 trades >= 50
- FULL6 PF >= 1.7 preferred, >= 1.5 absolute minimum
- Max DD <= 8% preferred, <= 10% absolute maximum
- OOS PF > 1
- OOS harsh PF > 1
- Return/DD not materially worse than H1 Champion
- H1 trades must not be disproportionately displaced by lower-quality M30 positions
