# xauusd_1 — Fibonacci XAUUSD Gold Round1

Independent Gold branch for Fibonacci Harmonic Sniper Ultimate. BTC Round17/Round18 files are not modified.

## Architecture

1. Signal Engine — H1 confirmed pivots X-A-B-C-D, pattern family, Bullish/Buy or Bearish/Sell direction.
2. Quality Engine — ratio quality, PRZ concentration, AB=CD symmetry, reciprocal BC/CD relationship, freshness, EMA context, M30 confirmation, spread/ATR cost score.
3. Risk & Execution — structural stop, Fibonacci AD target, minimum RR rejection, fixed-percent equity risk, broker volume/risk validation, margin gate, max one open position and daily loss gate.

## Core patterns

- Gartley
- Bat
- Butterfly
- Crab
- Deep Crab
- ABCD (Reciprocal ABCD is scored as ABCD ratio consistency, not duplicated as a second trade signal)

## Round1 research defaults

- Primary timeframe: H1
- Confirmation timeframe: M30
- Pivot: 3/3
- Ratio tolerance: 5%
- Minimum final quality: 84
- M30: at least 2 of 3 confirmation rules
- Risk: 0.50% equity
- Max daily loss: 3%
- Max open positions: 1
- Minimum RR: 1.50
- Target: 0.618 of AD
- No Grid, Martingale, DCA, Recovery, Loss Averaging, or Hedging logic

## Reproducibility

`source.gz.b64` contains the exact gzip+base64 source. The GitHub Actions workflow decodes it to `src/FibonacciXAUUSD1.cs`, builds with official cTrader CLI 5.9.11, and packages source, `.algo`, hashes and reports together.
