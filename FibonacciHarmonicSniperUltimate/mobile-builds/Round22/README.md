# Fibonacci Harmonic Sniper Ultimate — BTC Round22 Mobile

## Status

- Standard Champion: Round22 Balanced
- Harsh-cost defensive benchmark: Round17
- Target platform: cTrader Mobile / Cloud
- Primary symbol / timeframe: BITCOIN / H1

## Mobile build

- File: `FibonacciHarmonicSniperUltimate-BTC-Round22-Mobile.algo`
- Framework: .NET 6
- cTrader.Automate: 1.0.19
- File size: 61,341 bytes
- SHA-256: `7910579d4d2437928efedc46bd41406a4dc96159084cb2140a70763ddef29921`

## Recommended BTC H1 Balanced settings

Use `BTC-H1-Balanced.parameters.json` as the exact reference for the tested Round22 Balanced configuration.

Key risk allocation:

- H1 Buy risk: 1.15%
- H1 Sell risk: 0.80%
- M30 Buy risk: 0.40%
- M30 Sell risk: 0.50%
- Selective M30 health-bypass risk: 0.10%
- Max open positions: 1
- Max trades/day: 6
- Max daily loss: 5%

Core signal settings:

- Pattern: Reciprocal ABCD
- Min pattern score: 84
- Pivot Left / Right: 2 / 2
- Ratio tolerance: 6%
- Max pattern age: 16 bars
- Max entry distance: 1.80 ATR
- Candle confirmation: enabled
- Confirmation move: 0.05 ATR
- Cooldown: 2 bars
- Minimum R:R: 1.50
- Fallback R:R: 1.80
- M30 engine: enabled
- H1 health gate: enabled

Round21 selective bypass settings retained in Round22:

- Selective health bypass: enabled
- Bypass minimum score: 93
- Same-direction H1 max age: 2 hours
- Reserve H1 at hour boundary: enabled

## Validation snapshot

1Y Standard, BITCOIN H1, 2025-09-08 to 2026-09-08, initial balance 10,000:

- Trades: 95
- ROI: 39.93%
- Profit Factor: 1.95
- Max equity drawdown: 5.65%

1Y Harsh-cost validation:

- Trades: 95
- ROI: 18.12%
- Profit Factor: 1.39
- Max equity drawdown: 6.48%

True 6+6 split validation also showed Round22 improving Standard performance and drawdown versus Round17, while Round17 remained slightly stronger on Harsh ROI in the second half.

## Deployment notes

1. Download the `.algo` file from this folder.
2. Add/import it into the cTrader environment that supports cBot `.algo` packages, then run it in cTrader Cloud/Mobile.
3. Use BITCOIN on H1 for the validated configuration.
4. Match the values in `BTC-H1-Balanced.parameters.json` before comparing live/demo behavior with the published backtest results.
5. Broker symbol names, spreads, commissions, execution and crypto contract specifications can change real results.

`BTC-H1-Balanced.parameters.json` is a reference parameter file; it is not claimed to be a native cTrader preset import file.
