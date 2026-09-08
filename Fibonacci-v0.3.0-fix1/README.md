# Fibonacci v0.3.0-fix1
Candidate source, not a compiled or profitability-validated release.

Changes: aggressive D-side validation; signed structural stop distance; EMA Off no ranking bonus; enabled pattern list cached at startup; rejection counters printed at stop.
Full pivot cache deliberately deferred: current baseline calculation completes quickly.
3-month diagnostic: 2026-06-08 00:00 UTC through 2026-09-08 00:00 UTC, XAUUSD/EURUSD H1, M1 data, $200.
Workflow uploads the diagnostic algo before backtest. This diagnostic binary has TradingEnabled=true; source default remains false.
Timeout is now 10 minutes for the process and 20 minutes for the job. Timeout remains a failure, reports are retained for inspection.
Summary reads the actual nested report schema; zero trades has undefined win rate.
Spread/commission still use original defaults (zero): this first run is only for signal diagnostics. No profitability claim.
Next: investigate counters, confirm broker costs, use Jun 8-Aug 8 for development and Aug 8-Sep 8 as untouched validation. Do not tune repeatedly on the validation month.
No new backtest results exist until the workflow runs.
