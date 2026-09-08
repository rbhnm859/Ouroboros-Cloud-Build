# Fibonacci Harmonic Sniper Ultimate — 2026-09-08 diagnostic results

Status: code fixes compiled and backtests completed; strategy NOT approved for live use or profitability claims. Latest candidate: v0.3.0-fix3.

## Scope and results

cTrader CLI 5.9.11, XAUUSD/EURUSD H1, server M1 data, 2026-06-08 to 2026-09-08, initial USD 200, configured risk 1% equity. All results below are from successful jobs and downloaded JSON reports. Fixed spread and commission were both zero; swap charges/credits may still apply. These are diagnostics, not realistic net performance estimates or independent out-of-sample evidence.

| Version | Symbol | Trades | Wins | Net USD | Max equity drawdown |
|---|---|---:|---:|---:|---:|
| fix1 | XAUUSD | 4 | 1 | -27.49 | 37.54% |
| fix1 | EURUSD | 6 | 0 | -9.01 | 5.13% |
| fix2 | XAUUSD | 0 | 0 | 0.00 | 0.00% |
| fix2 | EURUSD | 6 | 0 | -8.60 | 4.92% |
| fix3 | XAUUSD | 0 | 0 | 0.00 | 0.00% |
| fix3 | EURUSD | 6 | 0 | -8.60 | 4.92% |

Zero trades means undefined win rate and insufficient evidence; it is not a profitable or perfect strategy. Six losing EURUSD trades are also far too few to establish stable performance.

## Confirmed repairs

- fix1: EMA Off no longer boosts ranking; aggressive entry checks the D-point side; structural stops use signed distance; rejection counters and independent versioned source added.
- Workflow: added documented `--exit-on-stop`. Without it the completed cBot/report remained inside a running CLI process. Subsequent jobs exited with code 0 and finished normally. Timeouts still count as failures.
- fix2: after sizing/normalization, `Symbol.AmountRisked` must not exceed the configured cash/equity risk budget. The original sizing result could equal the minimum trade volume despite exceeding the risk budget. Gold logs show volume 1, estimated risk USD 16.39–30.25 versus USD 2 budget. Rejecting these trades fixes risk control; it does not improve the entry strategy. This check is an estimate and cannot cap losses from gaps, slippage or fees.
- fix3: entry confirmation now precedes candidate ranking and opposite-direction conflict checks. An unconfirmed high-ranked candidate can no longer mask an otherwise eligible candidate. Gold had 12 risk-rejected entry attempts; no orders were placed. EURUSD performance did not improve.

Risk rejection also returns zero volume, so `risk_budget_exceeded` and `volume_below_min` overlap; do not add these counters as distinct signals. fix3 confirmation counters count candidates, not bars. Strategy thresholds and risk percentage were not tuned to manufacture positive results.

## Reproducibility and artifacts

- fix1 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176003957
- fix2 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176165347
- fix3 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176307277
- fix3 source: ../../Fibonacci-v0.3.0-fix3/FibonacciHarmonicSniperUltimate.cs
- fix3 build project: ../../Fibonacci-v0.3.0-fix3/FibonacciHarmonicSniperUltimate.csproj
- fix3 diagnostic algo ZIP: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176307277/artifacts/10037359332
- fix3 gold HTML/JSON: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176307277/artifacts/10037378042
- fix3 EURUSD HTML/JSON: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176307277/artifacts/10037377245

The compiled diagnostic artifact has TradingEnabled=true because the workflow enables it in its build copy. The checked-in source defaults to false. This artifact is not a production release. Report artifacts expire after 30 days; numeric results.json is checked in permanently. Build artifacts follow repository artifact retention.

Both symbol names were accepted on the connected cTrader account. The report's brokerTitle is blank, so this alone does not establish an FxPro account or universal FxPro symbol compatibility. No live trading was started.

## Remaining work and stopping decision

Do not promote any candidate. Stop repeated fitting on this same three-month window: the risk/entry fixes are verified, but an edge is unproven. Gold's current structural stops, minimum size and USD 200 / 1% risk budget are incompatible for the observed entries. Changing capital or stop geometry changes the strategy assumptions and must be evaluated explicitly, not hidden as optimization.

Before a performance optimization phase, establish broker/account-specific spread, commissions, lot constraints and tick data; define a limited strategy hypothesis and evaluation budget; use separate development data and an untouched later validation period. The entire window above has already been inspected and cannot now be called untouched validation. No background optimization loop or guarantee of near-perfect future returns has been created.
