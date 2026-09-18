# HarmonyBot V35.2 — One-Pass Commercial Finalization Protocol

## Authority / frozen baseline
- Repository: rbhnm859/Ouroboros-Cloud-Build
- Parent branch: harmonybot/v35.1-monotonic-alpha-veto
- Development baseline: BASE_V34
- Current advancement candidate: EXHAUSTION_VETO_ONLY
- Do not re-research V31–V35 history.
- Fibonacci / Harmonic Pattern remains the core entry thesis.
- XAUUSD, FxPro cTrader Mobile/Cloud, UTC0, H4/H1/M15/M1.
- No duplicate positions and no hedging.
- No Grid, Martingale, DCA, Recovery or Loss Averaging.
- 2020-H1 Fresh Validation is quarantined: never use it for tuning, thresholds, feature selection, candidate selection, or debugging strategy behavior.

## Goal
Execute one controlled sequence:
V35.1 freeze -> DEV loss anatomy -> evidence-based V35.2 alpha refinement -> fixed ablation -> promotion gate -> exit/risk refinement -> capital compatibility -> final freeze -> untouched fresh validation -> commercial release.

Do not loop until profitable. Do not tune against fresh validation. Do not promote a family that merely matches baseline.

## Stage 1 — Reproduce and freeze V35.1
Reproduce BASE_V34 and EXHAUSTION_VETO_ONLY over the exact existing DEV-A/B/C windows and cost assumptions.
Verify source hash, parameters, symbol mapping, session, risk settings and engineering_clean.
If reproduction materially differs from the recorded V35.1 evidence, STOP with engineering/reproducibility failure.

## Stage 2 — DEV loss anatomy
Export basket/trade-level evidence for DEV-A/B/C, with special focus on DEV-C.
At minimum classify:
pattern family; direction; H4/H1 regime; M15 harmonic setup; session; volatility/ATR regime; transition state; exhaustion state; M1 state; spread/cost; intended RR; realized R; MAE; MFE; holding time; exit reason.
Produce aggregate slices only where sample size is reported. Identify candidate structural loss clusters that recur beyond one isolated window.
Do not change strategy during this stage.

## Stage 3 — V35.2 hypotheses
EXHAUSTION_VETO remains active.
M1_VETO must not be a hard alpha veto; M1 may only be tested as execution timing/microstructure context.
TRANSITION_VETO must not be copied as a hard veto; it may only become a quality penalty/confirmation requirement if Stage 2 evidence supports it.
Create at most three evidence-based incremental hypotheses plus the unchanged V35.1 exhaustion control.
Do not alter Fibonacci/Harmonic ratios, SL/TP, breakeven, trailing, or risk sizing in this alpha stage unless an engineering bug requires a behavior-preserving fix.

## Stage 4 — Fixed alpha ablation
Run all candidates on identical DEV-A/B/C windows and identical costs.
Required metrics per family and per window:
baskets, annualized trades, PF, net, expectancy, max DD, win rate, average win, average loss, realized RR, positive windows, worst-window PF, MAE/MFE summaries, transition/exhaustion/M1 counts, engineering_clean, relative_advance.

## Stage 5 — Promotion gate
Compare every candidate directly with EXHAUSTION_VETO_ONLY and BASE_V34.
A candidate must show genuine incremental evidence, not equality.
Reject if improvement is produced mainly by severe trade suppression or a single DEV window.
Promotion requires all of:
- engineering_clean=true;
- aggregate PF > EXHAUSTION control;
- aggregate expectancy > EXHAUSTION control;
- worst-window PF > EXHAUSTION control;
- max DD no materially worse than EXHAUSTION control;
- no pathological collapse in basket count / annualized trade frequency;
- improvement not isolated to one DEV window.
If no V35.2 candidate passes, freeze EXHAUSTION_VETO_ONLY as alpha winner. Do not invent another tuning round.

## Stage 6 — Exit/risk refinement
Only after alpha winner is frozen, perform one bounded ablation of exit/risk behavior.
Keep entry alpha frozen.
Test only defensible variants of SL/TP, breakeven, trailing/time exit and sizing/risk controls.
Select using expectancy, PF, DD, left-tail behavior and robustness, not maximum net profit alone.
If no variant genuinely advances, retain original exit/risk behavior.

## Stage 7 — Capital compatibility
Run the final frozen strategy at starting balances:
USD 100, 150, 200, 300, 500, 1000.
Use FxPro-compatible symbol/volume normalization and realistic costs.
Report requested risk vs realized risk, minimum/normalized volume effects, margin feasibility, rejected/skipped trades, baskets, PF, net, expectancy and max DD.
Declare separately:
1. technical minimum runnable capital;
2. reasonable commercial operating capital.
Do not change alpha parameters per balance.

## Stage 8 — Final freeze
Record immutable:
source SHA/hash, parameter preset, symbol mapping, timeframe stack, UTC0 session, cost model, risk model, build/runtime versions, and selected candidate lineage.
Create a machine-readable FINAL_FREEZE_MANIFEST.json.
After this point, no strategy changes may be made using fresh-validation information.

## Stage 9 — Untouched fresh validation
Use only a genuinely untouched reserved period that has never influenced V35/V35.1/V35.2 tuning or selection.
2020-H1 remains prohibited for tuning and must not be repurposed if it has already been observed in the research process.
Run the frozen candidate once.
Classify result as PASS / MARGINAL / FAIL using predeclared validation gates.
Never tune from this result. MARGINAL remains a research candidate; FAIL returns the project to research only after quarantining the validation period from future claims of freshness.

## Stage 10 — Commercial release
Only after validation PASS:
- Release build and .algo artifact
- cTrader/FxPro compatibility checks
- Mobile/Cloud compatibility checks
- duplicate-entry and anti-hedge tests
- runtime safeguards
- parameter/preset documentation
- development + fresh-validation evidence report
- release version, commit SHA and hashes
- GitHub release-ready package

## Mandatory outputs
Generate machine-readable and human-readable artifacts:
- V352_LOSS_ANATOMY.json / .md
- V352_ALPHA_ABLATION.json / .md
- V352_PROMOTION_DECISION.json
- V352_EXIT_RISK_ABLATION.json / .md
- V352_CAPITAL_COMPATIBILITY.json / .md
- FINAL_FREEZE_MANIFEST.json
- FRESH_VALIDATION_RESULT.json / .md
- COMMERCIAL_RELEASE_DECISION.json / .md

Every decision JSON must include engineering_clean, baseline comparison, relative_advance, evidence limitations and exact reason for PASS/REJECT/STOP.

## Stop conditions
STOP rather than tuning around:
- non-reproducible V35.1 baseline;
- compile/runtime/data-integrity failure;
- missing cost assumptions;
- accidental access/use of quarantined fresh data during tuning;
- insufficient evidence for a new alpha hypothesis.
Engineering-only fixes are allowed only when behavior preserving and documented; they must not silently change the alpha hypotheses or promotion gate.

## Final principle
This is a one-pass evidence-constrained finalization pipeline, not an optimization-until-profitable loop. Preserve causal attribution, reject overfit improvements, and retain the older candidate whenever the new family does not demonstrate real relative advance.
