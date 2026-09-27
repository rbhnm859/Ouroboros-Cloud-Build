# HarmonyBot V68 — V67 Failure Forensics and Breakthrough Design

## Evidence source
Recovered from GitHub Actions run **36235505151** (head SHA `14728d02a415a7cb2baac39422f67da490126a3f`).
The V52-vs-V67-A reproduction gate passed before DEV, so the control lineage is valid.
All 24 DEV artifacts (A/B/C/D × six fixed windows) existed even though the downstream DEV frontier artifact was not produced.

## Recovered six-window DEV result (4.5 years total)

| Variant | Baskets | Frequency/y | Net | Normalized Net / 1.5y | PF | Expectancy | WR | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A V52 exact | 516 | 114.67 | +664.30 | +221.43 | 1.0295 | +1.29 | 38.95% | 10.53% |
| B family-native | 204 | 45.33 | -1692.55 | -564.18 | 0.8193 | -8.30 | 37.25% | 8.76% |
| C family-native grid | 122 | 27.11 | -1508.57 | -502.86 | 0.7888 | -12.36 | 36.89% | 8.31% |
| D commercial max | 108 | 24.00 | -1200.93 | -400.31 | 0.8160 | -11.12 | 32.41% | 6.99% |

No V67 B/C/D candidate qualifies for Validation. Fresh remains locked.

## Root cause 1 — family-native became a starvation funnel
V67 did not merely make downstream execution family-aware. It replaced the V52 supply trunk with multiple hard AND gates:
quality -> family route -> family M1 contract -> route-specific M1 veto -> grid feasibility -> scheduler/revalidation.

Recovered pipeline examples:
- AB=CD B: detected 113664, validated 92469, routed 3351, confirming 1176, armed 613, executed 93.
- Rat B: detected 11588, validated 9426, routed 1213, confirming 432, armed 222, executed 34.
- Shark B: detected 7329, validated 5345, routed 1394, confirming 615, armed 277, executed 45.
C and D then reduced execution further.

The failure is therefore primarily downstream admission/conversion, not insufficient detection.

## Root cause 2 — strict M1 conjunctions
Examples in V67 required simultaneous accumulated evidence:
- Rat: rejection + reclaim + BOS + displacement.
- Shark: failed-extension + rejection + BOS.
- 5-0: failed-extension + BOS + retest + directional.
- AB=CD: standalone eligibility + deceleration + failed-extension + directional + BOS.

This turns M1 execution confirmation into a hidden alpha gate and destroys throughput.

## Root cause 3 — AB=CD standalone remains destructive
Recovered A attribution:
- AB=CD aggregate: 234 baskets, Net -1020.38, expectancy -4.36.
- AB=CD exhaustion: 67 baskets, Net -1036.77, expectancy -15.47.

V68 therefore keeps AB=CD as completion/confluence evidence by default. Standalone capital remains off until a preregistered positive marginal cohort proves otherwise.

## Positive cohorts worth preserving, not overfitting
Recovered A:
- Rat trend: 43 baskets, Net +953.84, expectancy +22.18.
- Rat exhaustion: 18 baskets, Net +162.03, expectancy +9.00.
- Shark trend: 23 baskets, Net +401.22, expectancy +17.44, but unstable by window.
- Shark exhaustion: 11 baskets, Net +264.49, expectancy +24.04, mixed by window.
- Cypher trend: 13 baskets, Net +193.58, expectancy +14.89.

Recovered D showed a strong but small Rat-trend pulse (12 baskets, Net +607.14, PF about 3.26, expectancy about +50.59). This is evidence to preserve and test, not a license to hard-code a winner.

## Root cause 4 — Grid can accidentally become an admission gate
C fell from 204 baskets (B) to 122. Family grid geometry and capital allocation were able to make the entire setup fail even when a legal first entry could exist.

V68 rule:
1. Grid remains preplanned before first fill.
2. Whole-basket stressed risk remains <=1%.
3. Deeper legs are optional entry-efficiency improvements.
4. A deeper-leg sizing or target-RR failure may degrade the plan to legal L0-only.
5. Grid may not transform a legal L0 setup into a rejection merely because optional deeper legs are infeasible.
6. No recovery/add-to-loser semantics.

## Root cause 5 — CI/Data Governance cancellation
V67 used one branch-wide concurrency group with `cancel-in-progress: true`.
A later push on the same branch could cancel the frozen SHA after DEV artifacts were already produced and before analysis/final artifacts were uploaded.

V68 uses SHA-isolated concurrency and `cancel-in-progress: false`.
A validation run for one frozen source SHA cannot be cancelled by a later source commit.

## Root cause 6 — prevented risk rejects were mislabeled as engineering violations
V67 `gridRiskViolations` included fail-closed pre-execution rejections while the hard gate is actual post-plan basket-risk violation.
Recovered windows could therefore show `engineering_clean=false` while `actual_basket_risk_violations=0`.

V68 separates:
- `gridRiskPlanRejections`: prevention/telemetry, not an executed violation.
- `actualBasketRiskViolations`: hard FAIL-CLOSED veto.

## V68 architecture
**V52 supply trunk -> family evidence overlay -> explicit negative-cohort veto -> additive family M1 evidence -> non-blocking family grid -> opportunity scheduler.**

Family logic no longer replaces a valid V52 route or legacy confirmation. It can:
- add family-native evidence,
- rescue a valid family setup,
- choose family grid geometry,
- refine ranking and telemetry,
- veto only preregistered cohorts backed by direct negative evidence.

It cannot create HFT alpha, use future MFE/MAE, use trade outcomes at runtime, or relax basket risk/RR.

## Frozen variants
- A: V52 exact control.
- B: Family Evidence Overlay.
- C: B + Family-Native Non-Blocking Grid.
- D: C + opportunity scheduling/revalidation only. Controlled expansion is OFF until positive marginal evidence exists.

## Required decision
Only real DEV artifacts may authorize Validation.
Any failure => `HOLD_WITH_EVIDENCE`.
Only DEV + 2026 Validation + capital compatibility + immutable Fresh 2020H1 may produce `COMMERCIAL_FREEZE_APPROVED`.
