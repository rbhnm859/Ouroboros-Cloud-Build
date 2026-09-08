# Fibonacci Harmonic Sniper Ultimate — 2026-09-08 diagnostic results

Status: code fixes compiled and backtests completed; strategy NOT approved for live use or profitability claims. Latest candidate: v0.3.0-fix5.

## Scope and results

cTrader CLI 5.9.11, server M1 data, 2026-06-08 to 2026-09-08, initial USD 200, configured risk 1% equity. All results below are from successful jobs and downloaded JSON reports. fix1–fix3 H1 runs used zero spread and zero commission assumptions. Later fix4/fix5 diagnostics used modeled cost scenarios via CLI: EURUSD spread 1 pip, XAUUSD spread 30 pips, commission 35 USD/million, plus M15 and trend-filter variants where noted. These are diagnostics, not realistic net performance estimates or independent out-of-sample evidence.

| Version | Case | Symbol | Period | Trades | Wins | Net USD | Max equity drawdown |
|---|---|---|---|---:|---:|---:|---:|
| fix1 | default | XAUUSD | H1 | 4 | 1 | -27.49 | 37.54% |
| fix1 | default | EURUSD | H1 | 6 | 0 | -9.01 | 5.13% |
| fix2 | default | XAUUSD | H1 | 0 | 0 | 0.00 | 0.00% |
| fix2 | default | EURUSD | H1 | 6 | 0 | -8.60 | 4.92% |
| fix3 | default | XAUUSD | H1 | 0 | 0 | 0.00 | 0.00% |
| fix3 | default | EURUSD | H1 | 6 | 0 | -8.60 | 4.92% |
| fix3 | eur-h1-baseline | EURUSD | H1 | 6 | 0 | -9.36 | 5.22% |
| fix4 | eur-h1-fix4 | EURUSD | H1 | 1 | 0 | -1.30 | 4.05% |
| fix4 | eur-m15-fix4 | EURUSD | M15 | 7 | 1 | -12.27 | 6.39% |
| fix4 | eur-m15-trend | EURUSD | M15 | 1 | 0 | -2.73 | 2.22% |
| fix4 | xau-h1-fix4 | XAUUSD | H1 | 0 | 0 | 0.00 | 0.00% |
| fix4 | xau-m15-fix4 | XAUUSD | M15 | 0 | 0 | 0.00 | 0.00% |
| fix5 | eur-h1-fix5 | EURUSD | H1 | 1 | 0 | -1.30 | 4.05% |
| fix5 | eur-m15-fix5 | EURUSD | M15 | 3 | 0 | -3.96 | 2.14% |
| fix5 | xau-m15-fix5 | XAUUSD | M15 | 0 | 0 | 0.00 | 0.00% |

Zero trades means undefined win rate and insufficient evidence; it is not a profitable or perfect strategy. Small trade counts are still too limited to establish a stable edge, even where losses became smaller.

## Confirmed repairs

- fix1: EMA Off no longer boosts ranking; aggressive entry checks the D-point side; structural stops use signed distance; rejection counters and independent versioned source added.
- Workflow: added documented `--exit-on-stop`. Without it the completed cBot/report remained inside a running CLI process. Subsequent jobs exited with code 0 and finished normally. Timeouts still count as failures.
- fix2: after sizing/normalization, `Symbol.AmountRisked` must not exceed the configured cash/equity risk budget. The original sizing result could equal the minimum trade volume despite exceeding the risk budget. Gold logs show volume 1, estimated risk USD 16.39–30.25 versus USD 2 budget. Rejecting these trades fixes risk control; it does not improve the entry strategy. This check is an estimate and cannot cap losses from gaps, slippage or fees.
- fix3: entry confirmation now precedes candidate ranking and opposite-direction conflict checks. An unconfirmed high-ranked candidate can no longer mask an otherwise eligible candidate. Gold had 12 risk-rejected entry attempts; no orders were placed. EURUSD performance did not improve.
- fix4: rejects invalidated D pivots before ranking, blocks nonfinite ATR sizing, avoids opposite same-symbol exposure, and rejects insufficient remaining Fibonacci reward. Under modeled EURUSD costs, H1 shrank from the cost-bearing fix3 baseline of -9.36 USD over 6 trades to -1.30 USD over 1 trade; M15 ScoreOnly still lost -12.27 USD over 7 trades, while M15 ConfirmOnly lost -2.73 USD over 1 trade. Gold H1 and M15 still placed 0 trades.
- fix5: reserves execution costs in sizing and minimum net reward/risk, and rejects reused or older same-direction D pivots. Under the same modeled costs, EURUSD H1 matched fix4 H1 at -1.30 USD over 1 trade, while EURUSD M15 improved from fix4's -12.27 USD over 7 trades to -3.96 USD over 3 trades. Gold M15 still placed 0 trades, with `risk_budget_exceeded` and `volume_below_min` continuing to block entries.

Risk rejection also returns zero volume, so `risk_budget_exceeded` and `volume_below_min` overlap; do not add these counters as distinct signals. fix3 confirmation counters count candidates, not bars. Strategy thresholds and risk percentage were not tuned to manufacture positive results.

## Reproducibility and artifacts

- fix1 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176003957
- fix2 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176165347
- fix3 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34176307277
- fix4 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186235715
- fix5 successful run: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014
- latest source: ../../Fibonacci-v0.3.0-fix5/FibonacciHarmonicSniperUltimate.cs
- latest build project: ../../Fibonacci-v0.3.0-fix5/FibonacciHarmonicSniperUltimate.csproj
- fix5 diagnostic algo ZIPs: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040670879, https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040672291, https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040698883
- fix5 report ZIPs: https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040689351, https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040693720, https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/34186495014/artifacts/10040717599

The compiled diagnostic artifact has TradingEnabled=true because the workflow enables it in its build copy. The checked-in source defaults to false. This artifact is not a production release. Report artifacts expire after 30 days; numeric results.json is checked in permanently. Build artifacts follow repository artifact retention.

Both symbol names were accepted on the connected cTrader account. The report's brokerTitle is blank, so this alone does not establish an FxPro account or universal FxPro symbol compatibility. No live trading was started.

## Remaining work and stopping decision

Do not promote any candidate. Stop repeated fitting on this same three-month window: the risk/entry fixes are verified, but an edge is unproven. Gold's current structural stops, minimum size and USD 200 / 1% risk budget are incompatible for the observed entries. Changing capital or stop geometry changes the strategy assumptions and must be evaluated explicitly, not hidden as optimization.

Before a performance optimization phase, establish broker/account-specific spread, commissions, lot constraints and tick data; define a limited strategy hypothesis and evaluation budget; use separate development data and an untouched later validation period. The entire window above has already been inspected and cannot now be called untouched validation. No background optimization loop or guarantee of near-perfect future returns has been created.
