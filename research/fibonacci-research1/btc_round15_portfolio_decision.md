# BTC Round15 — True H1 + M30 Harmonic Portfolio Decision

## Scope
Round15 is the first true single-cBot, single-account portfolio combining the frozen H1 Reciprocal ABCD Growth Champion with the frozen M30 Reciprocal ABCD frequency engine. Both engines remain Harmonic-first. They share equity, 1% risk sizing, MaxOpenPositions=1, daily limits, symbol/label, and protection. H1 has explicit priority at hourly boundaries.

Workflow: `.github/workflows/backtest-fibonacci-btc-round15-portfolio.yml`
Run: `34256743309`
Generator: `tools/create_fibonacci_btc_round15.py`
Version: `v0.13.0-btc-round15-portfolio`

## Recent FULL6 validation (2026-03-08 to 2026-09-08)

### Normal costs
- Trades: 81
- Wins: 48
- Win rate: 59.26%
- Net: +6966.61 USD
- ROI: +69.67%
- PF: 2.31
- Max DD: ~7.83%
- Avg trade: +86.01 USD
- Long PF: 3.51
- Short PF: 1.77
- Return/DD: ~8.90

Engine attribution:
- H1: 35 trades, 22 wins, net +3108.37, PF ~2.47
- M30: 46 trades, 26 wins, net +3858.24, PF ~2.21

### Harsh costs
- Trades: 80
- Wins: 44
- Win rate: 55.00%
- Net: +4436.53 USD
- ROI: +44.37%
- PF: 1.78
- Max DD: ~8.36%

Engine attribution:
- H1: 34 trades, net +1861.36, PF ~1.79
- M30: 46 trades, net +2575.17, PF ~1.77

## Frozen OOS (2026-08-09 to 2026-09-08)

### Normal
- Trades: 15
- Net: +700.40
- ROI: +7.00%
- PF: 1.82
- Max DD: ~4.62%
- H1: 7 trades, +758.30, PF ~4.06
- M30: 8 trades, -57.90, PF ~0.90

### Harsh
- Trades: 15
- Net: +220.67
- ROI: +2.21%
- PF: 1.21
- Max DD: ~4.56%
- H1: 7 trades, +353.80, PF ~1.79
- M30: 8 trades, -133.13, PF ~0.78

The true combined account therefore passes the Round14 aggregate OOS gates, including harsh PF > 1, because the H1 engine stabilizes the portfolio while M30 adds frequency.

## Independent preceding six-month validation (PRE6)
Period: 2025-09-08 to 2026-03-07
Workflow: `.github/workflows/backtest-fibonacci-btc-round15-pre6.yml`
Run: `34257267212`

### PRE6 normal
- Trades: 59
- Wins: 14
- Net: -2439.21
- ROI: -24.39%
- PF: 0.47
- Max DD: ~26.31%
- H1: 14 trades, net -384.52, PF ~0.61
- M30: 45 trades, net -2054.69, PF ~0.42

### PRE6 harsh
- Trades: 59
- Wins: 14
- Net: -2468.36
- ROI: -24.68%
- PF: 0.45
- Max DD: ~26.55%
- H1: 14 trades, net -398.34, PF ~0.60
- M30: 45 trades, net -2070.02, PF ~0.41

## Decision

1. **Frequency objective is technically solved.** A true combined Harmonic-first portfolio produced 80-81 trades in the recent six months, versus 37 for H1-only.
2. **Do not promote Round15 to Production.** Independent PRE6 fails badly and reveals strong regime dependence, especially in the M30 engine.
3. Keep the H1 Growth Champion as the Production Research anchor.
4. Keep Round15 as an Experimental Frequency Portfolio Candidate only.
5. Do not micro-optimize M30 against the already-seen OOS/PRE6 windows.
6. The next research problem is no longer raw frequency. It is **regime qualification for M30**: determine when M30 harmonic frequency is allowed to participate, without replacing Harmonic entry alpha with generic indicators.
7. Any future regime gate must be learned causally from structural/harmonic or broad volatility-state evidence, validated on multiple disjoint periods, and must not be tuned directly to rescue PRE6.
8. No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging changes are introduced.

## Status
- Production Research anchor: H1 Reciprocal ABCD Growth Champion, unchanged.
- Experimental candidate: Round15 H1+M30 true portfolio.
- Frequency: solved in recent regime.
- Cross-regime robustness: failed; next bottleneck.
