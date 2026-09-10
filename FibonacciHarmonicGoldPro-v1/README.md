# Fibonacci Harmonic Gold Pro v1.0.0

A new XAUUSD-specialised cTrader cBot built around harmonic-pattern completion as the **only entry signal family**.

## Core architecture

- Fixed execution engine: M15 entry scan with H1/H4 harmonic-only confluence.
- Confirmed right-side swing pivots to reduce repainting.
- Pattern set: Gartley, Bat, Alternate Bat, Butterfly, Crab, Deep Crab, Cypher, Shark (mapped as O-X-A-B-C), AB=CD, 5-0.
- No EMA/RSI/MACD trend filter is used for entry.
- Blocks duplicate entries and blocks a new trade whenever an existing position on the same symbol is present.
- Default session: 07:00-21:00 UTC, with configurable open/close freeze windows.
- Optional manual UTC blackout windows, e.g. `12:25-12:40;13:55-14:10`.
- Risk-percent or fixed-lot sizing, with optional month-start equity compounding anchor.
- Broker volume normalization and estimated-margin gate.
- Spread/commission cost-to-risk gate.
- Market entry by default, or optional expiring Fibonacci CD pullback limit entry.
- Pattern-derived invalidation stop.
- Fibonacci target ladder based on CD: TP1=0.382, TP2=0.618, Final=1.272.
- Minimum final R:R gate defaults to 3.0.
- Partial exits, break-even, and M15 price-structure trailing.
- Daily loss, weekly loss, maximum equity drawdown, consecutive-loss and cooldown circuit breakers.
- `AccessRights.None`; no external DLLs.

## Safety / execution semantics

The bot blocks rather than forces a trade when M15 has no qualified harmonic completion, H1/H4 conflict, confluence is insufficient, final target cannot satisfy the minimum R:R, transaction costs are excessive, margin is insufficient, or session/risk/duplicate-position gates fail.

## XAUUSD symbol names

`XAUUSD Only=true` accepts symbol names containing `XAUUSD` or `GOLD`, including common broker suffix/prefix variants. The actual broker symbol must still be selected in cTrader.

## Cloud / Mobile

The project compiles to `.algo` through GitHub Actions. Once imported into cTrader, it can be started as a Cloud instance and controlled from supported cTrader clients, including Mobile.

## Important validation rule

No profitability number is hard-coded or claimed. Before commercial release, run tick-data backtests and forward/OOS validation for recent 1 month, 1 year and 3 years, reporting trades, net profit, ROI, drawdown, win rate, average R:R, Sharpe, Sortino and profit factor.

The default parameters are an engineering baseline, not a guarantee of profit.
