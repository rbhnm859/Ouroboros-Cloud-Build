# HarmonyBot V35.1 — Fresh Validation Data Governance Lock

This file is committed before any new fresh/forward performance is observed.

## Frozen candidate

- Candidate: `EXHAUSTION_VETO_ONLY`
- V35.1 source commit used by the successful development run: `0b2ef01895bfa14a8dae9c298b47a340e93e6f03`
- Source SHA256: `1474574432ac785d667089516327fe34bbcee1ff6bfeead068951e0472065b94`
- V34 execution/risk kernel remains frozen.
- No Alpha, Harmonic/Fibonacci ratios, structural stop, grid weights, risk percentage, scheduler ranking or validation gate may be changed from validation results.

## Capital compatibility evidence

Capital Compatibility Run: `35389301971`

- Minimum Technical Equity among tested points: **USD 100**
- Recommended Operating Equity under the precommitted engineering criteria: **USD 1000**
- These are engineering conclusions from exposed DEV data, not profitability validation.
- USD 100 remains a technical/micro capability point and is **not** promoted as the recommended operating capital.

## Historical exposure decision

The project does **not** currently have another historical interval that can be described as auditably untouched without spending the protected Final Holdout.

Known exposure includes:

- 2018-07-02..2018-12-31 — previous final-holdout use
- 2019-01-02..2019-06-28 — previous OOS use
- 2019-07-01..2019-12-31 — previous validation / USD100 gate use
- 2020-01-02..2020-06-30 — consumed by V34 Fresh Validation Run `35379490879`; now `EXPOSED_VALIDATION_FAILED`
- 2020-07-01..2020-12-31 — exposed by repository workflows
- 2021-01-04..2022-06-30 — exposed development data, including V35/V35.1 and the Capital Compatibility Study
- 2022-07-01..2022-12-30 — exposed retired validation
- 2023-09-10..2026-09-16 — exposed prior HarmonyBot research

Intervals outside the list above are **not automatically fresh**. Existing governance says unknown prior exposure invalidates an untouched claim. Therefore pre-2018/unassigned gaps are not promoted into Fresh Validation by absence from the present workflow list.

## Protected Final Holdout

`2023-01-02 .. 2023-08-31` remains:

**RESERVED_UNTOUCHED_NOT_AUTHORIZED**

It must not be used now. It remains single-use evidence for the final stage after the preceding validation, OOS/walk-forward, parameter sensitivity and execution-cost stress program is fully frozen.

## New forward reservation

Because no additional historical interval is provably untouched, the next evidence source is pre-reserved forward data.

- Reservation ID: `V351-FORWARD-VAL-1`
- Start: **2026-09-21T00:00:00Z**
- Evaluation start: **2026-09-28T00:00:00Z**
- End: **2027-03-31T23:59:59Z**
- Broker: **FxPro**
- Symbol: **XAUUSD**
- Leverage: **1:500**
- Bot timezone: **UTC**
- Candidate: **EXHAUSTION_VETO_ONLY**
- Status: **RESERVED_BEFORE_DATA_EXISTS**

### Tracks

Track A — Normal Capital:

- Starting balance: **USD 10,000**
- Metrics and equity curve are evaluated independently.

Track B — Recommended Operating Capital:

- Starting balance: **USD 1,000**
- Metrics and equity curve are evaluated independently.

USD 100 may continue to be reported as engineering/micro-capability evidence, but it is not pooled with either promotion track and is not the recommended-capital validation track.

## Frozen pass/fail gate

The existing V34 Stage-1 validation gate is retained rather than changed after seeing V35.1 DEV results. Each validation track must independently satisfy:

- at least 10 completed baskets; otherwise `INSUFFICIENT_SAMPLE`
- PF > 1.0
- Net > 0
- Expectancy > 0
- Max Equity DD <= 10%
- Engineering Clean = true
- broker profile present
- V35.1 summary present
- basket activity present
- zero execution/risk safety violations required by the frozen V34 kernel

No pooled PF, Net, Expectancy or DD across tracks.

## Anti-contamination rule

No observation from `V351-FORWARD-VAL-1` may be used to:

- retune Alpha;
- blacklist losing Harmonic patterns;
- alter Fibonacci ratios;
- alter structural stops;
- change Fibonacci grid weights or depth to fit the interval;
- increase Basket Risk;
- force minimum volume;
- change the pass/fail gate after results are known.

If the forward interval is incomplete or broker data are unavailable, record `INSUFFICIENT_FORWARD_DATA` or `DATA_UNAVAILABLE`. Do not substitute an exposed historical interval and do not spend the protected 2023 Final Holdout early.
