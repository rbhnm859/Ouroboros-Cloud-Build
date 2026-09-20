# EURUSD sanity backtest

Actual performance: **not yet available**. No timeframe is accepted as trading successfully yet.

Four baseline files exist: M1, M5, M15, M30. Each includes every requested metric and safety question; unavailable measurements are JSON null, not zero or pass.

Prepared test: 2026-08-31 00:00 through 2026-09-07 00:00 UTC, starting balance 100 account-currency units, symbol EURUSD, all default strategy parameters, ticks downloaded from the broker. Assumed spread 1 pip and commission 35 per million; not verified broker costs. Account leverage/symbol specification come from the authenticated account and must be checked in the resulting report.

The GitHub Actions workflow `Cumulative Delta EURUSD build and sanity` builds once and tries each timeframe once, six-minute timeout per run, no parameter optimization. It uses existing CTRADER_CTID, CTRADER_ACCOUNT and CTRADER_PASSWORD repository secrets. Missing credentials produce explicit not-run results. Raw JSON, HTML, exit codes and logs are preserved as artifacts if produced. It never executes live `run` commands.

A no-trade outcome is retained as evidence; thresholds are not relaxed merely to produce trades. Tick data are necessary for this uptick/downtick proxy; OHLC/M1 interpolation is not a substitute. No claim of stable profitability or suitability for optimization can be made before measured results and event-level risk checks.

CLI reference: https://help.ctrader.com/ctrader-cli/cbots/
