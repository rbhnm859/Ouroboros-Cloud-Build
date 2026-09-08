# Build Log

## 2026-09-08

- Source pulled from `guetaquant-byte/guetaquant-tools`, `main`,
  `ctrader/GQ_Session_Scalper.cs`.
- Independent source created at `src/GQ_Session_Scalper_v2.cs`.
- Python syntax checks passed for the validation harness and the original
  backtest module.
- Original backtest unit tests passed: `3 passed`.
- Static safety checks passed: completed-bar entry path, risk-based volume,
  one-position guard, cost filters, daily risk stop, and forbidden strategy
  terms absent from executable logic.
- Native cTrader compilation was **not available in this workspace** because
  the cTrader Automate/cAlgo SDK and a C# compiler are not installed.
- Therefore `builds/GQ_Session_Scalper_v2.algo` is a portable source package
  with a manifest, not a claim of a cTrader-generated binary. Compile it in
  cTrader Automate and verify the broker-specific symbol mapping before use.
- Validation harness completed with `SIMULATION DATA` and generated IS/OOS
  reports. The gate is `PROFITABILITY VALIDATION FAILED`; no profitable
  candidate label was issued.