# K3 Flow-First — Corrected IS Stop-Rule Result

## Status

**Classification: C — FAIL**

This result follows the pre-committed deep-research validation protocol. K3 is **not frozen**, **not promoted to OOS**, and **not eligible for FULL / stress / robustness / Monte Carlo / commercial Mobile release**.

## Evidence source

- Branch: `cds-k3-flow-first-entry-research`
- Corrected validation run: `34481887898`
- Tested source commit: `a66f9d3ad650052f53f854aca9c9fe769fcba439`
- K3 artifact: `CDScalper_K3_CORRECTED_IS_K3_FLOW_FIRST` (artifact `10154347343`)
- K2 control artifact: `CDScalper_K3_CORRECTED_IS_K2_CONTROL` (artifact `10154331018`)

## Corrected test contract

- Symbol: EURUSD
- Timeframe: M1
- Initial balance: USD 30
- Account leverage: 1:500 (confirmed in report)
- Historical data: server tick data (`tickDataFromServer`)
- IS period: 09/09/2024 through 08/09/2025
- CLI spread argument: 0.43 pip
- Commission: 35 USD per million USD volume (confirmed in report metadata)
- Original hard equity/risk protections retained

Note: cTrader 5.9.11 report JSON serializes `main.spread` as null even though the executed CLI command and cBot runtime show `Spread=0.43` and approximately four EURUSD tick-points at signal time. This is a report-metadata limitation and is recorded separately from strategy gate evaluation.

## K3 corrected IS metrics

| Metric | K3 Flow-First | IS research requirement |
|---|---:|---:|
| ROI | -3.10% | > 0 |
| Net profit | -$0.93 | > 0 / positive expectancy |
| Profit Factor | 0.44 | approach 1.15–1.20; promotion gate >=1.15 |
| Trades | 8 | >=50 |
| Win rate | 25.00% | informational |
| Average trade | -$0.12 | >0 |
| Max equity DD | 5.02% | <=15% |
| Largest win | +$0.47 | informational |
| Largest loss | -$0.52 | >=-$1.00 |
| Commission | -$0.64 | realistic cost included |
| Long PF | 0.16 | informational |
| Short PF | 0.00 in report aggregate | informational |

K3 passes only the drawdown and largest-loss risk constraints. It fails ROI, PF, trade-count and post-cost expectancy requirements.

## Same-harness K2 control

| Metric | K2 control | K3 Flow-First |
|---|---:|---:|
| ROI | -4.20% | -3.10% |
| Net | -$1.26 | -$0.93 |
| PF | 0.62 | 0.44 |
| Trades | 14 | 8 |
| Win rate | 35.71% | 25.00% |
| Average trade | -$0.09 | -$0.12 |
| Max equity DD | 8.75% | 5.02% |
| Largest win | +$0.63 | +$0.47 |
| Largest loss | -$0.59 | -$0.52 |
| Commission | -$1.12 | -$0.64 |

Flow-First reduced activity, absolute net loss and drawdown, but did **not** create positive post-cost edge. Profit Factor, win rate, average trade and opportunity count deteriorated relative to K2.

## Protocol decision

The deep-research stop rule stated that if corrected tick-data K3 IS does not at least approach PF 1.15–1.20 with positive expectancy and sufficient trades, the family must be stopped instead of continuing IS parameter search or tuning on OOS.

K3 produced PF 0.44, negative expectancy and only eight trades. This is materially below the stop threshold. Therefore:

- Do not create `FREEZE_MANIFEST.json`.
- Do not run OOS.
- Do not run FULL 2Y as promotion evidence.
- Do not run cost stress / robustness / Monte Carlo as promotion evidence.
- Do not create or label any K3 `.algo` as Commercial / Store / Release.
- Do not retune Delta, ADX, session, weekdays or direction thresholds on this OOS window.
- Preserve Original K, K2 and K3 research artifacts for auditability.

## Engineering follow-up (non-promotion)

Two auditability improvements remain valid engineering work but must not be represented as strategy optimization or commercial rescue:

1. Make the full signal-audit telemetry explicit for every threshold-cross candidate: timestamp, direction, previous/cumulative delta, last-three delta values, price acceptance, HTF EMA, EMA slope, ADX, spread, ATR, estimated cost, decision and skip reason.
2. Review HTF context values for strict closed-bar determinism before any future *new* hypothesis is proposed; current K3 uses live `LastValue` for HTF EMA/ADX context at the M1 OnBar event.

Any future commercial attempt must be a **new pre-committed architecture hypothesis**, not parameter mining of this failed K3.
