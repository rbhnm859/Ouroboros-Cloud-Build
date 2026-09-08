# BTC Round16 — H1 Harmonic Health Regime Gate Decision

## Scope
Round16 keeps both entry engines Harmonic-first. H1 Reciprocal ABCD remains the primary engine and always trades normally. M30 Reciprocal ABCD is permitted only after at least 2 of the last 3 closed H1 trades were profitable. Before three H1 samples exist, M30 remains disabled.

No RSI, MACD, ADX, Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging is introduced.

Workflow: `.github/workflows/backtest-fibonacci-btc-round16-h1-health.yml`
Run: `34261572906`
Version: `v0.15.0-btc-round16-h1-health`

## PRE6 — 2025-09-08 to 2026-03-07

### Normal
- Trades: 21
- Wins: 8
- Net: -52.26 USD
- ROI: -0.52%
- PF: 0.96
- Max DD: ~5.72%
- H1: 17 trades, -94.44, PF ~0.92
- M30 admitted: 4 trades, +42.18, PF ~1.14

### Harsh
- Trades: 21
- Net: -97.92 USD
- ROI: -0.98%
- PF: 0.93
- Max DD: ~5.85%
- H1: 17 trades, -121.74, PF ~0.89
- M30 admitted: 4 trades, +23.82, PF ~1.08

Compared with raw Round15 PRE6 (-24.39%, PF 0.47, DD 26.31%), the adaptive H1 health gate removes most of the historical M30 damage.

## FULL6 — 2026-03-08 to 2026-09-08

### Normal
- Trades: 71
- Wins: 40
- Net: +4998.12 USD
- ROI: +49.98%
- PF: 2.06
- Max DD: ~7.80%
- H1: 36 trades, +3054.11, PF ~2.54
- M30 admitted: 35 trades, +1944.01, PF ~1.71

### Harsh
- Trades: 69
- Wins: 35
- Net: +2468.52 USD
- ROI: +24.69%
- PF: 1.50
- Max DD: ~10.39%
- H1: 35 trades, +1506.33, PF ~1.66
- M30 admitted: 34 trades, +962.19, PF ~1.36

Frequency remains materially above the H1-only 37-trade baseline.

## Frozen OOS — 2026-08-09 to 2026-09-08

### Normal
- Trades: 14
- Net: +517.89 USD
- ROI: +5.18%
- PF: 1.61
- Max DD: ~2.54%
- H1: 7 trades, +744.14, PF ~4.03
- M30: 7 trades, -226.25, PF ~0.63

### Harsh
- Trades: 12
- Net: +42.12 USD
- ROI: +0.42%
- PF: 1.05
- Max DD: ~2.90%
- H1: 7 trades, +329.64, PF ~1.75
- M30: 5 trades, -287.52, PF ~0.37

## Decision
1. H1 Health Gate is a meaningful cross-regime improvement and remains a strong research challenger.
2. It is **not promoted to Production yet** because FULL6 harsh Max DD (~10.39%) is slightly above the 10% hard gate, and admitted M30 trades remain weak in frozen OOS.
3. H1 Growth Champion remains the Production Research anchor.
4. Frequency is still solved: recent FULL6 retains 69-71 trades, far above H1-only 37.
5. Do not tune the 2-of-3 health rule against these already-seen windows.
6. Next single-variable risk hypothesis: keep H1 at 1% risk and reduce M30 risk to 0.5%. This changes portfolio risk contribution, not entry alpha or trade frequency.
