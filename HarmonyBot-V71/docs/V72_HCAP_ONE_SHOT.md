# HarmonyBot V72 Candidate — HCAP One-Shot Specification

## Status
This branch is the single one-shot candidate for the Harmonic Counterfactual Action Policy (HCAP).
It starts from the V71 terminal baseline and does not modify the frozen harmonic detector or trusted V51 mother binary.

## Frozen strategy contract
- XAUUSD, FxPro demo USD, 1:500, UTC.
- H4/H1/M15 state; completed M1 execution evidence only.
- Frozen 12-family harmonic detector.
- V51 Protected Core has first capital-slot priority.
- MaxActiveBasket = 1.
- Alpha qualification risk = 1%.
- Minimum Net RR = 2.
- Grid OFF for Alpha qualification. Grid remains a post-Alpha profit amplifier only.
- No hedging, Martingale, DCA, recovery, loss averaging or stop widening.

## HCAP action space
For every causally eligible harmonic action:
- NO_TRADE
- REVERSAL
- CONTINUATION

HCAP does not use year identity. It uses only contemporaneous pre-entry observables:
geometry quality, PRZ confluence, confidence, time symmetry, pivot quality, Net-RR,
efficiency, ATR fit, extension, trend strength, ADX slope context and MTF conflict context.

## Fixed model
The model family is preregistered and not searched:
- action-specific linear ridge value model;
- fixed continuous ridge = 8;
- fixed family shrinkage ridge = 24;
- intercept ridge = 0.01;
- canonical family one-hot partial pooling;
- one-sided LCB z = 1.645;
- NO_TRADE whenever Q <= 0 or LCB <= 0.

No hyperparameter search, year classifier, PnL threshold tuning or post-result selector is permitted.

## Burned temporal OOF
Exactly three folds:
- Train 2021+2022 -> Test 2023
- Train 2021+2023 -> Test 2022
- Train 2022+2023 -> Test 2021

Each test year must independently satisfy:
- selected opportunities >= 60/year
- Mean R > 0
- PF_R > 1
- one-sided 95% LCB of Mean R > 0

Failure eliminates HCAP. No HCAP.1 threshold rescue is allowed.

## Capital conversion
If OOF Alpha passes, each burned year is rerun in cTrader using its own OOF model.
V51 Core remains first priority and Core displacement must be zero.
The existing commercial Pareto gate remains unchanged and requires a material breakthrough.

## Fixed DEV
Only a frozen all-calibration model may run:
- 2024 H2
- 2025 H1
- 2025 H2

## Locked Validation and Fresh
Only after DEV PASS:
- Validation: 2026 Q1 and 2026 Q2
- Fresh: 2026 Q3 (2026-07-01 through 2026-09-30)

Fresh cannot execute unless Validation passes.
Validation/Fresh never feed model fitting or threshold changes.

## Final promotion
Only the complete chain can promote:
V51 exact replay -> temporal OOF Alpha -> OOF capital conversion -> fixed DEV ->
2026 Q1/Q2 Validation -> 2026 Q3 Fresh.

PASS creates the final branch:
`harmonybot/v72-harmonic-counterfactual-action-policy`

FAIL at any strategy gate terminates HCAP without threshold/filter/risk rescue.
Engineering-only compile/API/parser/CI repairs are permitted without changing the preregistered strategy contract.
