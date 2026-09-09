# xauusd_2 — Predictive Harmonic PRZ Engine

Independent Gold/XAUUSD cTrader cBot architecture. It does not replace or overwrite xauusd_1.

## Objective

Fix the low-frequency / late-entry problem observed in xauusd_1 by projecting harmonic completion zones from X-A-B-C before D becomes a fully confirmed pivot.

## Architecture

- Primary execution timeframe: M15.
- H1 is context only; EMA alignment contributes to confidence instead of acting as a hard reject gate.
- X-A-B-C uses fast confirmed pivots (default 2-left / 1-right).
- D and PRZ are projected before a D pivot exists.
- Families in v2.0 baseline: AB=CD, Gartley, Bat, Butterfly, Crab.
- Entry requires price interaction with PRZ plus an M15 reversal score.
- Confidence combines pattern shape, PRZ convergence, M15 reversal and H1 trend context.
- Hard execution gates remain: minimum RR, spread/ATR, one open position, risk sizing, margin check and daily loss cap.
- No Grid, Martingale, DCA, Recovery, Loss Averaging or Hedging logic.

## Baseline test target

First validation uses XAUUSD M15 with M1 backtest data for 2026-06-09 to 2026-09-09, $10,000 balance and 0.5% risk per trade.

Promotion target for the new architecture is not a specific win rate. The first goal is to materially improve unique trade count over xauusd_1 while preserving positive expectancy under both Standard and Harsh cost assumptions.
