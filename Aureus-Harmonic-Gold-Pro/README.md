# Aureus Harmonic Gold Pro

A new, isolated XAUUSD cTrader cBot research project built for commercial validation.

## Strategy contract

- Primary entry source: confirmed Fibonacci harmonic X-A-B-C-D structures only.
- Entry timeframe: XAUUSD M15.
- Higher-timeframe filter: H1/H4 harmonic agreement/conflict only; no EMA/RSI replacement entry logic.
- Supported core patterns: Gartley, Bat, Butterfly, Crab, Deep Crab.
- Anti-repaint: pivots require both left and right confirmation bars before they can be used.
- No duplicate exposure: any existing XAUUSD position or pending order blocks a new entry.
- No hedging: opposite exposure on the same symbol is never created.
- Trading session: London open through New York close with UK/US DST rules.
- Risk sizing: percentage of equity and broker volume normalization; no arbitrary fixed maximum-lot parameter.
- Protection: structural X/D invalidation stop, Fibonacci D-to-A 0.618 target, minimum net R:R gate, breakeven and ATR trailing.
- Risk governor: daily, weekly, monthly loss gates and peak-equity drawdown kill switch.
- Execution filters: spread ceiling, minimum ATR, ATR shock filter, optional manual UTC news blackout windows.

## Commercial-validation rule

No result is considered commercial-grade from a single in-sample backtest. The CI workflow runs 1Y and 3Y XAUUSD M15 tests from cTrader CLI with M1 source data, then produces a scorecard. A pass is only a research gate, not a guarantee of future profitability.

Default internal research gates:

- Net profit > 0
- Profit factor >= 1.50
- Maximum equity drawdown <= 15%
- 1Y ROI >= 20%
- 3Y CAGR >= 15%
- Minimum trade count: 40 (1Y), 120 (3Y)
- Return / max-drawdown >= 1.50

A later release candidate must also pass OOS/walk-forward, Monte Carlo trade-order reshuffling, cost/slippage stress, parameter-neighbourhood stability, demo forward testing, and a code/restart/recovery checklist before a commercial claim is made.

## Backtest baseline

- Broker/data source: connected cTrader account used by GitHub Actions secrets
- Symbol: XAUUSD
- Chart period: M15
- Data mode: M1
- Starting balance: USD 10,000
- 1Y window: 11/09/2025 to 10/09/2026
- 3Y window: 11/09/2023 to 10/09/2026

## Disclaimer

Backtests are historical simulations. They do not guarantee future returns. Commercial acceptance thresholds in this repository are internal engineering gates, not official cTrader Store profitability requirements.
