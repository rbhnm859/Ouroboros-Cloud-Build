# v0.3.0-fix4 research candidate

Not a profitable release. Based on fix3; preserves all prior source and results. Rejects invalidated D pivots, nonfinite ATR, opposite same-symbol positions/pending orders, and insufficient remaining Fibonacci reward before ranking. Explicit RiskReward mode retains fixed RR targets. Risk remains 1% of USD 200; no forced minimum volume.

Six predefined diagnostic cases compare cost-bearing fix3 H1, fix4 H1/M15, and M15 EMA confirmation. Period 2026-06-08 to 2026-09-08 has already been observed; not independent validation. Assumed spread EURUSD 1 pip, XAUUSD 30 pips; CLI commission 35 USD/million. These are cost scenarios, not verified FxPro quotes. M1 data, not tick accuracy. Preserve all failures and zero-trade results. No increase in capital/risk to force gold trades. Compiled workflow artifacts have TradingEnabled=true for diagnostics only; checked-in default is false. Compilation and backtests pending at creation.
