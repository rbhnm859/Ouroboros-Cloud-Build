# V74 R19 — Research-only causal architecture and feasibility

**Status:** research only. No Alpha Gate, OOF promotion, broker execution or order API.

## Source-locked zero-model feasibility

The five sealed R18 semantic-year ZIP artifacts were downloaded via an authorized GitHub connection and their ZIP SHA256 values verified. Research-only R18 action outcomes were recalculated and checked against the original R18 filtering contract. Results below are upper bounds for the **existing fixed R18 action set**, not a claim about the new R19 templates.

| Year | Unique eligible event upper bound | Perfect-foresight positive-event upper bound | Required independent events/winners |
|---|---:|---:|---|
| 2016 | 196 | 44 | 250 / 175 — FAIL |
| 2017 | 247 | 50 | 250 / 175 — FAIL |
| 2018 | 273 | 57 | 250 / 175 — FAIL |
| 2019 | 273 | 49 | 250 / 175 — FAIL |
| 2020 | 188 | 34 | 250 / 175 — FAIL |

An interval-scheduling DP further constrains overlap, but **relaxes unique event identity** and is deliberately an optimistic upper bound, **not** an exact joint colored-interval optimum. See R19_R18_VERIFIED_BOUNDS.json. Existing R18 fixed actions fail the necessary counting test even under perfect hindsight. New R19 actions require separate outcome evidence; this result must not be generalized to all Harmonic Trading.

## Authorized reproduction

1. Download unchanged ZIP artifacts from GitHub Actions run 37824462498, naming them v74-r18-semantic-Y2016.zip through Y2020.zip.
2. Verify against the SHA256 values in RESEARCH_LOCK.json and the original ../r18/feasibility_certificate.py.
3. Execute: python3 HarmonyBot-V74/r19/r19_achievability.py --artifact-dir PATH --out R19_FEASIBILITY.json
4. Execute: python3 -m unittest discover -s HarmonyBot-V74/r19 -p 'test_r19_*.py' -v
5. Compare counts to R19_R18_VERIFIED_BOUNDS.json. If differing, fail closed; do not overwrite the certificate.

## Engineering boundary and next blockers

- The four R19 action templates are DESIGN ONLY; no response surface has been evaluated. Preserve family-native pattern definitions and actual bid/ask and risk economics.
- r19_event_state.py is a Python research reference for causal timestamp, stable event identity, monotone state transitions and simulated ENTER; it is **not** a live cTrader policy.
- A later phase must build native Harmonic action outcomes on pinned causal ticks, then test temporal availability, calibration, coverage constraints, event/block bootstrap, negative controls and C# runtime parity.
- Four independent vetoes (Risk / Model Validation / Red Team / Data Governance) and the fixed 2021–2023 annual gates remain mandatory.
- Never access burned / Validation / Fresh to tune R19. New XAUUSD V1, LibreChat and Railway are outside scope. No paid or live operations.
