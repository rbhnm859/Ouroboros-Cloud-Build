# K3 Flow-First — Corrected IS Stop-Rule Result

## Status

**Classification: C — FAIL**

This result follows the pre-committed deep-research validation protocol. K3 is **not frozen**, **not promoted to OOS**, and **not eligible for FULL / stress / robustness / Monte Carlo / commercial Mobile release**.

## Evidence source

- Branch: `cds-k3-flow-first-entry-research`
- Corrected validation run: `34481887898`
- Tested source commit: `a66f9d3ad650052f53f854aca9c9fe769fcba439`
- Original K artifact: `CDScalper_K3_CORRECTED_IS_ORIGINAL_K` (artifact `10154474294`)
- K2 control artifact: `CDScalper_K3_CORRECTED_IS_K2_CONTROL` (artifact `10154331018`)
- K3 artifact: `CDScalper_K3_CORRECTED_IS_K3_FLOW_FIRST` (artifact `10154347343`)

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

cTrader Console 5.9.11 serializes `main.spread` as null in these JSON reports even though the executed CLI command records `--spread=0.43`, the runtime parameter table records `Spread=0.43`, and K3 runtime signal logs show approximately four EURUSD tick-points at execution checks. Therefore this is recorded as a report-metadata limitation rather than evidence that spread was omitted.

## Three-way corrected IS comparison

| Metric | Original K | K2 control | K3 Flow-First | K3 IS requirement |
|---|---:|---:|---:|---:|
| ROI | -6.03% | -4.20% | -3.10% | >0 |
| Net profit | -$1.81 | -$1.26 | -$0.93 | positive |
| Profit Factor | 0.31 | 0.62 | 0.44 | >=1.15 for research promotion |
| Trades | 20 | 14 | 8 | >=50 |
| Win rate | 40.00% | 35.71% | 25.00% | informational |
| Average trade | -$0.09 | -$0.09 | -$0.12 | >0 |
| Max equity DD | 6.83% | 8.75% | 5.02% | <=15% |
| Largest win | +$0.20 | +$0.63 | +$0.47 | informational |
| Largest loss | -$0.57 | -$0.59 | -$0.52 | >=-$1.00 |
| Commission | -$1.60 | -$1.12 | -$0.64 | realistic cost included |

### K3 directional metrics

- Long PF: 0.16
- Long net: -$1.40
- Short aggregate PF: 0.00 as serialized by the report
- Short net: +$0.47

The eight-trade sample is too small to justify direction-specific threshold tuning. Disabling one side would be parameter mining and is not permitted under the pre-committed protocol.

## Interpretation

K2 improves on Original K in the corrected tick-data environment, but it remains materially unprofitable. K3 Flow-First reduces activity, absolute net loss, commission paid and drawdown versus both earlier controls, but it does **not** create a positive post-cost trading edge. Compared with K2, K3 has lower PF, lower win rate, worse average trade and fewer opportunities.

The K3 result is not near the research threshold: PF is 0.44, average trade is negative, ROI is negative, and only eight trades occurred versus the required minimum of 50.

## Protocol decision

The deep-research stop rule requires the family to stop if corrected tick-data K3 IS does not at least approach PF 1.15–1.20 with positive expectancy and sufficient trades. K3 fails this condition materially.

Therefore:

- Do **not** create `FREEZE_MANIFEST.json`.
- Do **not** run OOS.
- Do **not** run FULL 2Y as promotion evidence.
- Do **not** run cost stress / robustness / Monte Carlo as promotion evidence.
- Do **not** create or label any K3 `.algo` as Commercial / Store / Release.
- Do **not** retune Delta, ADX, session, weekdays, long/short thresholds or other entry parameters using this OOS window.
- Preserve Original K, K2 and K3 sources, workflows, reports and artifacts for auditability.

## Engineering follow-up allowed by the report

The following may be done only as engineering/auditability work, not as an attempt to rescue this failed K3 through parameter fitting:

1. Add full threshold-cross signal telemetry: timestamp, direction, previous/cumulative delta, last-three delta values, price acceptance, HTF EMA, EMA slope, ADX, spread, ATR, estimated cost, decision and skip reason.
2. Review HTF context for strict closed-bar determinism; current K3 uses live `LastValue` values for HTF EMA/ADX at the M1 `OnBar` event.
3. Correct the report parser so cTrader 5.9.11's missing `main.spread` field does not create a false environment failure when CLI/runtime evidence confirms the locked spread setting.

Any later commercial attempt must be a **new, separately pre-committed architecture hypothesis**. It must restart at corrected IS and may not be justified by OOS tuning of this failed K3.
