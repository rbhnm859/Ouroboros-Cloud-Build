# xauusd_3 — Harmonic Hybrid Engine

Independent XAUUSD cTrader cBot architecture. It does not overwrite xauusd_2.

## Architecture

- Host timeframe: M5.
- H1: market regime / trend context, scored rather than used as a blanket hard gate.
- M15: impulse structure and Fibonacci 0.50–0.786 retracement zone.
- Harmonic geometry is optional confluence, not the sole source of trades.
- M5: engulfing, rejection wick, micro-structure break and momentum confirmation.
- Final signal score = H1 regime (20) + Fibonacci (20) + M15 structure (15) + Harmonic confluence (25) + M5 execution (20).

## Hard gates retained

- Minimum RR.
- Spread / ATR.
- Fixed-money risk sizing through cTrader symbol risk APIs.
- Margin check.
- Daily loss cap.
- Account-wide same-symbol position lock.
- Account-wide same-symbol pending-order lock.
- Entry mutex and broker-send recheck.
- No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging.

## Initial validation target

XAUUSD M5, M1 backtest data, 2026-06-09 to 2026-09-09, $10,000 balance, 0.5% risk.

First acceptance goal: materially increase trade count versus xauusd_2 v2.3 while preserving positive or near-positive expectancy under both Standard and Harsh cost assumptions.
