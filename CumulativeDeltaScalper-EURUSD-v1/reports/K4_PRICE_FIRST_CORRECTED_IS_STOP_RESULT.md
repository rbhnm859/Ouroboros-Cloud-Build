# K4 Price-First Breakout — Corrected IS Stop-Rule Result

## Status

**Classification: C — FAIL**

This result follows the pre-committed commercial validation protocol. K4 is **not frozen**, **not promoted to OOS**, and **not eligible for FULL / stress / robustness / Monte Carlo / commercial Mobile release**.

## Evidence source

- Branch: `cds-k4-price-first-breakout-research`
- Corrected validation run: `34485464338`
- Tested source/workflow commit: `6b71671afc4a6a1d5e601a01c9c9dcd7a5ff7cab`
- Evidence artifact: `CDScalper_K4_PRICE_FIRST_CORRECTED_IS`
- Artifact ID: `10155864421`
- Artifact digest: `sha256:ade28bdefd818394ae649e666cfa29bd385305bed8f1e86e38faf1912cb9dfce`

## Corrected test contract

- EURUSD M1
- Initial balance: USD 30
- Leverage: 1:500
- Historical mode: server tick data (`tickDataFromServer`)
- IS: 09/09/2024 through 08/09/2025
- Spread CLI argument: 0.43 pip
- Commission: 35 USD per million USD volume
- K4 precommit architecture and hard account/risk guards retained

The report parser confirmed the full environment contract. cTrader Console serialized `main.spread` as null, so the locked 0.43 pip setting was validated from the execution log fallback as designed by the engineering audit.

## Corrected IS metrics

| Metric | K4 result | First-IS requirement | Pass? |
|---|---:|---:|---|
| ROI | -10.47% | >0 | FAIL |
| Net profit | -$3.14 | positive | FAIL |
| Profit Factor | 0.51 | >=1.15 | FAIL |
| Trades | 32 | >=50 | FAIL |
| Win rate | 40.63% | informational | — |
| Average trade | -$0.10 | >0 | FAIL |
| Max equity DD | 12.05% | <=15% | PASS |
| Largest win | +$0.36 | informational | — |
| Largest loss | -$0.44 | >=-$1.00 | PASS |
| Commission | -$3.76 | realistic cost included | — |

Directional diagnostics:
- Long PF: 0.62; long net: -$0.75
- Short PF: 0.45; short net: -$2.39

The sample is not sufficient to justify direction-specific mining, and the precommit explicitly forbids using this result to retune long/short thresholds, breakout lookback, close-location percentile, ADX, delta vote count, session, weekday set, TP or SL on the same IS window.

## Protocol decision

K4 materially fails the pre-committed first-IS promotion gate. Therefore:

- Do **not** create a K4 `FREEZE_MANIFEST.json`.
- Do **not** run K4 OOS.
- Do **not** run K4 FULL 2Y as promotion evidence.
- Do **not** run K4 stress / robustness / Monte Carlo as promotion evidence.
- Do **not** label the K4 `.algo` Commercial / Store / Production / Release.
- Do **not** retune K4 using this IS or any OOS window.
- Preserve K4 source, precommit spec, workflow, reports and artifacts for auditability.

## Allowed next commercial step

A further attempt must be a **new separately pre-committed architecture hypothesis**. It must be defined before its first corrected IS run, use the same locked realistic-cost validation contract, and restart at IS without OOS tuning. K4 itself is closed as a failed hypothesis.
