# HarmonyBot V35.1 — Alpha Root-Cause Attribution

Source evidence: completed V35 Development Run 35381369459, EXPOSED DEV-A/B/C only. No 2020-H1 Fresh Validation result is used for tuning.

Observed architecture behavior:
- BASE_V34: 73 baskets, aggregate PF 1.082, Net +266.64, expectancy +3.65, max DD 8.33%.
- QUALITY_ONLY: identical executed metrics to BASE_V34 despite 25 quality rejections. Quality removals did not alter realized baskets.
- REGIME_ONLY: 73 baskets, PF 0.990, Net -33.38. The V35 router was not a pure filter; it relaxed V34 eligibility and changed the executable set.
- CONFIRM_ONLY: 72 baskets, PF 0.933, Net -219.03. Enhanced confirmation replaced legacy confirmation and used different pass rules.
- FULL_V35: 68 baskets, PF 0.855, Net -444.90.
- Parsed FULL_V35 transition telemetry: 5 completed baskets, 0 winners, approximately -422.62 net.

Structural root causes:
1. Non-monotonic regime router: a context module could create trades V34 would reject.
2. Non-monotonic confirmation: enhanced confirmation could replace rather than supplement legacy confirmation.
3. Transition semantic ambiguity: a neutral trend state could be treated as transition without actual H4/H1 state disagreement.
4. Quality attribution failure: rejected candidates that never execute do not prove realized Alpha improvement.
5. Capital feasibility confound: capital compatibility must be studied separately from Normal-capital Alpha.

V35.1 design:
- V34 RouteSignal is evaluated first.
- Transition and Exhaustion modules can only veto a V34-approved route.
- Legacy M1 confirmation is mandatory first.
- Route-specific M1 evidence can only veto after legacy confirmation passes.
- Scheduler rank remains the V34 formula.
- Harmonic robustness is observation-only in this ablation.
- Capital feasibility is disabled in Normal Alpha ablation and studied separately after an Alpha candidate exists.
- No threshold sweep is authorized.
