# HarmonyBot Performance Execution Specification

Status: **HIGHEST PRIORITY EXECUTION / VALIDATION / COMMERCIAL FREEZE SPECIFICATION**  
Engineering baseline: **HarmonyBot V29.3 Grid Risk-Cap Hotfix RC**  
Stable historical baseline: **HarmonyBot V29.2**  
Engineering Freeze: **PASS / protected**  
Performance Freeze: **FAIL_STAGE1 / active recovery execution**  
Final Commercial Freeze: **HOLD until all gates pass**

## 1. Non-negotiable constraints

The V29.3 Engineering Freeze is immutable unless a verified engineering regression is discovered. Performance work must not weaken Small Capital Mode, broker minimum-volume protection, volume-step normalization, position sizing, margin/free-margin protection, protective SL, Basket Risk-Cap, Grid exposure control, anti-hedging, duplicate-main-entry protection, or fail-closed execution.

All candidate ranking is lexicographic. No weighted composite score is permitted.

1. Max Drawdown <= 10% (hard reject above 10%).
2. Robust Profit Factor, ultimate target >= 2.5.
3. OOS stability: Net > 0, Expectancy > 0, DD <= 10%, no single-winner dependency.
4. Win Rate >= 65% without collapsing realized RR/PF.
5. Annual Return >= 100% only after priorities 1-4 hold.
6. Then assess Trades >= 200/year, realized Basket RR >= 2:1, profitable months >= 10/12, and Net Profit >= 100% initial capital.

Initial performance recovery gate is intentionally weaker than the final commercial target: DD <= 10%, PF > 1, Net > 0, Expectancy > 0. PF floor is then raised in stages: >1.3 -> >1.5 -> >2.0 -> >=2.5 while preserving prior gates.

## 2. Evidence baseline

The frozen 1.618/1.618 payoff preset was positive only in the development M1 sample. Independent historical robustness then failed in both IS and OOS. IS recorded 54 baskets, PF about 0.307, Net about -$606.42, negative expectancy and DD about 6.47%. OOS recorded 19 baskets, PF about 0.680, Net about -$111.86, negative expectancy and DD about 2.10%.

OOS had zero Grid-child baskets and still lost; therefore Grid additions are not the sole root cause. IS also remained materially negative outside the small set of Grid-child baskets. Cypher was the strongest negative contributor in the exposed IS sample, but no pattern is disabled commercially from that sample alone.

No verified source logic bug, execution bug, risk-cap failure, broker-protection failure, margin cascade or unexpected hedge has been established. Accordingly, V29.4 is **not authorized at the start of this specification**.

## 3. Performance Action Matrix

| Issue | Evidence | Affected Segment | Root Cause | Parameter / Logic / Source | Proposed Fix | Expected KPI Impact | Regression Risk | Required Validation | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| M1 positive but IS/OOS both negative | M1 PF >1/Net >0; IS PF ~0.307; OOS PF ~0.680 | Full strategy | Parameter robustness / regime instability | Preset first | Stop using 1.618/1.618 as commercial preset; re-screen on clean Development data | Raises PF floor if true edge exists | Low engineering, high model-selection risk | Multi-window Development -> Validation | High |
| Grid cannot explain all losses | OOS negative with zero Grid children; IS mostly non-grid loss | Grid + Non-Grid | Strategy edge failure beyond Grid | Preset/selection | Keep Grid; evaluate Grid separately from main baskets | Prevents false Grid-only optimization | Low | Grid vs Non-Grid basket matrix | High |
| Non-Grid negative expectancy | IS non-grid materially negative; OOS all non-grid and negative | Non-Grid | Pattern/entry/regime/exit mix | Preset first | Decompose by pattern, alignment, session, volatility, exit | PF/expectancy improvement | Medium | Clean Development segmentation + Validation | High |
| Cypher instability | Exposed IS Cypher PF ~0.164 and large negative net; OOS still <1 | Cypher | Pattern/regime dependency hypothesis | Existing pattern toggle initially | Candidate family: Cypher restriction/disable; accept only if clean data confirms | PF floor / tail loss | Frequency loss; selection bias | Development subwindows + Validation | Medium-High |
| 5-0 not proven stable | IS near break-even but OOS small sample negative | 5-0 | Uncertain edge | No change initially | Retain until new clean data proves persistent negative edge | Avoid premature over-filtering | Low | Development/Validation pattern matrix | Medium |
| Winner too small | Realized RR ~0.47-0.76 in exposed windows; frequent scale-outs/partial exits | Winners / exits | Winner capture truncation hypothesis | Existing exit parameters | Test partial-exit simplification before new logic | Avg winner, RR, PF | Lower WR / larger giveback | Development + Validation + MFE capture audit | Medium-High |
| Losers too large / tail concentration | OOS top-3 losses ~88% gross loss | Tail losses | Structural stop / regime / invalidation delay | Preset first; logic only if needed | Test existing stop/regime controls; only then consider MAE/time/invalidation logic | DD, PF floor | Stop-out frequency | Multi-window tail attribution | High |
| Counter-trend / alignment instability | Soft MTF reversal exists; exposed failure spans regimes | MTF / regime | Weak alignment hypothesis | Existing parameters | Strict H1/H4 alignment candidate family | PF floor / tail reduction | Trade-frequency reduction | Development/Validation regime matrix | Medium |
| Partial-close fragments corrupt raw KPIs | cTrader history splits underlying positions | Audit | Measurement issue | Workflow/audit | Basket-level aggregation is official KPI | Correct PF/WR/RR measurement | None | Every validation report | High |
| Session edge unknown | Existing London-to-NY gate but no stable segment proof | Session | Unverified | Workflow/audit first | Segment London / overlap / NY before changing hours | OOS stability | Over-filtering | Development segment matrix | Low-Medium |
| Volatility edge unknown | No cross-window segment proof yet | Volatility | Unverified | Workflow/audit first | Bucket volatility and test only after attribution | PF / DD stability | Curve fitting | Development segmentation then fixed Validation | Low-Medium |
| PRZ / geometry quality edge unknown | Source exposes geometry/PRZ/time/pivot thresholds | Entry quality | Unverified threshold stability | Existing parameters | Keep fixed in first family screen; optimize only after segment evidence | PF / signal quality | Parameter explosion | Nested Validation | Medium |
| $100 frequency may be constrained by min volume | Small-cap engineering passes but annual signal feasibility not yet measured on clean long sample | $100 execution | Broker min-volume / risk budget | Audit + existing protections | Count Eligible, MinVolume/Risk/Margin skips and executed baskets; never force min lot | Frequency feasibility | None if audit-only | $100 long-window validation | Medium-High |
| 200/year may conflict with PF floor | Full-account frequency can be adequate but quality is currently negative | Frequency | Edge scarcity hypothesis | Preset/selection | Defer frequency expansion until PF/OOS stable | Avoid low-quality trades | Lower volume of trades | Annualized Validation/WF | High |
| RR >=2 may conflict with high WR | Current realized RR far below 2 despite nominal MinRR | Exit distribution | Structural KPI conflict possible | Exit architecture | Optimize realized payoff, not nominal TP:SL | RR/PF | WR degradation | Basket distribution + sensitivity | High |
| Need MAE/time/invalidation kill-switch | Existing source has no general time exit / MAE kill-switch | Tail losses | Hypothesis, not yet proven necessary | Potential Source | Do not patch until preset families fail and clean data shows repeated conditional tail pattern | DD/PF | Source regression | Cross-development evidence first | Medium |

## 4. Data Governance

### 4.1 EXPOSED DATA

All data previously used for HarmonyBot development, tuning, backtests, M1, payoff repair, IS/OOS, root-cause analysis or parameter adjustment is permanently marked **EXPOSED**.

Auditable repository evidence shows historical HarmonyBot 3-year runs beginning around 10-11 September 2023 and ending in September 2026. Therefore the conservative exposed union for current governance is:

- **2023-09-10 through 2026-09-16: EXPOSED**.
- The known V29 M1 / D7 / IS / OOS subsets inside this union remain EXPOSED and can be used only as historical diagnostic evidence, never as Final Holdout.

No HarmonyBot workflow exposure was found in the repository search for 2021 or 2022. Those older periods are therefore classified **AUDITABLY UNEXPOSED** rather than assumed perfect OOS. Any off-repository prior use would invalidate that classification.

### 4.2 New clean partitions

These partitions are frozen before the new candidate search starts:

**Development Set** — may be used for family discovery and local search only:
- DEV-A: start 2021-01-04, evaluation start 2021-01-11, end 2021-06-30
- DEV-B: start 2021-07-01, evaluation start 2021-07-08, end 2021-12-31
- DEV-C: start 2022-01-03, evaluation start 2022-01-10, end 2022-06-30

**Validation Set** — PASS/FAIL only, never parameter optimization:
- VAL: start 2022-07-01, evaluation start 2022-07-08, end 2022-12-30

**Untouched Final Holdout** — must not be executed until candidate, parameters, gates and workflow are frozen:
- HOLDOUT: start 2023-01-02, evaluation start 2023-01-09, end 2023-08-31

Holdout state at specification creation: **UNTOUCHED / NOT AUTHORIZED FOR RUNNING YET**.

If FxPro/cTrader server history is unavailable for a partition, the workflow must mark `INSUFFICIENT_TRUE_HOLDOUT_DATA` or `DATA_UNAVAILABLE`; it must not silently substitute exposed data.

## 5. Segment / Edge Matrix specification

All official performance measurements are basket-level. Raw cTrader history items are execution fragments only.

For every clean window, emit at minimum:

- Pattern Type
- Direction
- Grid-child present vs Non-Grid
- Session bucket: London, London/NY overlap, New York
- Trend context / MTF alignment when auditable
- Volatility bucket when auditable
- PRZ / geometry quality bucket when auditable
- Exit type

Metrics: Basket Count, PF, Win Rate, Net, Expectancy, Average Winner, Average Loser, Median Winner, Median Loser, Realized RR, Max DD, Largest Loss, Top-1/3/5 loss contribution, holding time; MFE/MAE only when tick/bar evidence can be reconstructed without changing trading logic. Missing context must be labeled `UNVERIFIED`, never inferred.

## 6. Candidate Families — Phase 1

V29.3 source remains unchanged. The initial search is deliberately low-dimensional.

**BASE — Frozen V29.3 reference**
- GridProfitFib=1.618
- GridStopFib=1.618
- Existing V29.3 Full Bot settings unchanged.

**A — Pattern Selection / Cypher restriction probe**
- BASE + `EnableCypher=false`.
- Purpose: test whether exposed Cypher weakness persists in clean periods.
- This is a family probe, not a commercial decision.

**B — Winner Capture probe**
- BASE + `EnablePartialTP=false`.
- Purpose: determine whether partial-close truncation is suppressing realized winners.
- Grid scale-out remains unchanged to isolate the factor.

**C — Tail / Stop Geometry probe**
- BASE + `SlAtrMult=1.0` (from 1.2 default), no risk-percent increase.
- Purpose: determine whether modest structural stop contraction improves loss distribution without collapsing WR.

**D — Regime / HTF alignment probe**
- BASE + `H4FilterEnabled=true` + `SoftMtfReversalGate=false`.
- Purpose: test strict H1/H4 directional alignment.

**E — Combination candidate**
- Not pre-defined. It may be created only from components that independently improve Development PF floor and do not violate DD/frequency integrity. This prevents interaction overfitting.

No candidate in Phase 1 changes RiskPercent, Small Capital engineering, MaxDrawdown, Grid risk-cap, minimum-volume behavior, broker protection or leverage.

## 7. Development gate and family selection

Each Phase-1 candidate is tested across DEV-A, DEV-B and DEV-C. A family is rejected immediately if any reliable Development window exceeds 10% DD.

A family may advance to VAL only when:
- aggregate Development Net > 0;
- aggregate Development Expectancy > 0;
- aggregate Development PF > 1;
- no Development window has DD > 10%;
- improvement is not caused by a single extreme winner;
- at least two of three Development windows are non-negative or the negative window is statistically small and does not show clear structural collapse.

Among survivors, rank by:
1. Worst-window PF;
2. Median-window PF;
3. cross-window positive-expectancy stability;
4. Win Rate;
5. Return;
6. frequency/RR.

## 8. Validation gate

VAL is strictly PASS/FAIL. No parameter may be changed in response to VAL.

Minimum Stage-1 VAL gate:
- Max DD <= 10%;
- PF > 1;
- Net > 0;
- Expectancy > 0;
- no single winner contributes an unacceptable share of gross profit;
- execution errors = 0.

Failure retires the family or returns the project to Development with a new hypothesis. The failed VAL results must not be used as optimization targets.

## 9. Robustness sequence after Validation PASS

Only a candidate that passes VAL may continue:

1. Rolling/anchored Walk-Forward: output median and worst window PF, DD, WR, RR, expectancy, tail loss, Grid/Non-Grid split.
2. Sensitivity around surviving parameters: +/-5%, +/-10%, +/-20%. Exact-point-only success = curve-fit reject.
3. Cost Stress: Spread x1.25, Spread x1.5, higher commission, moderate slippage; cost-fragile candidate = reject.
4. Freeze design and parameter values.
5. Run the untouched Final Holdout **once**.
6. Basket-level Monte Carlo if feasible: median return, 5th-percentile return, 95th-percentile DD, worst DD, risk of ruin, $100 survival rate.
7. $100 Final Validation including EligibleSignals, SkippedByMinVolume, SkippedByRisk, SkippedByMargin, ExecutedTrades, max margin usage, min free margin, max open risk, max basket risk.
8. Full Bot Final Validation.
9. Commercial KPI matrix and freeze decision.

## 10. Source-version rule

Current decision: **NO V29.4**.

Preset/workflow/audit changes do not increment the bot source version. V29.4 Development Candidate is permitted only if clean Development evidence establishes that V29.3 cannot express a required performance rule, such as a repeated cross-window MAE/time-based invalidation or pattern-specific threshold that cannot be represented by existing parameters.

Any future source patch must be the minimum necessary performance patch and must preserve V29.3 as the technically stable baseline. Only gates affected by the source change are rerun, but compile, risk regression, $100 viability, execution integrity and Full Bot integrity must remain demonstrably intact where applicable.

## 11. Stop rules

Stop a candidate family when any of the following occurs:
- IS/Development improvement is accompanied by Validation deterioration.
- Return improvement pushes DD above 10%.
- WR improvement collapses PF or realized RR.
- Frequency improvement materially lowers PF.
- only one window succeeds.
- only one exact parameter value succeeds.
- cost stress immediately turns the strategy negative.
- tail reduction depends on rules hand-crafted around previously known individual losses.

## 12. Current execution state after Phase-1 / Phase-1.1

Research is closed. This document is now the controlling execution specification.

Completed evidence:
- Phase-1 preset probes did not produce a Validation-qualified candidate.
- Phase-1.1 ATR-coverage probes restored trade count but failed cross-regime expectancy.
- F_ATR_FACTOR_040: DEV-A PF 0.409, DEV-B PF 0.658, DEV-C PF 0.646; all Net negative.
- G_MIN_ATR_1_0: 217 total baskets across three Development windows; worst PF 0.337; total Net -2372.88; zero positive windows.
- H_MIN_ATR_0_5: 225 total baskets; PF 0.461 / 0.433 / 1.167; total Net -1402.98; DEV-C DD 10.008% breaches the hard 10% ceiling.
- Therefore simple ATR relaxation is RETIRED and must not be retuned.
- Pattern attribution under relaxed ATR was dominated by Cypher and 5-0. Neither pattern showed stable positive expectancy across all three Development windows.
- VAL-2 (2020-H2) was not executed because no Development winner existed and remains reserved pending the next qualified candidate.

Active execution priority:
1. $100 Small-Capital performance feasibility.
2. Signal-funnel attribution using existing V29.3 telemetry plus controlled ablation.
3. Minimal Effective Filter Stack: MTF, geometry/quality, pattern coverage, non-grid isolation.
4. Cross-regime positive expectancy before any exit/payoff expansion.
5. Only after positive entry edge exists: winner capture, tail control, PF ladder, OOS/WF/sensitivity/cost stress/final holdout.

V29.4 remains NOT AUTHORIZED. Any source patch requires proof that a necessary adaptive rule cannot be represented by V29.3 parameters.

## 13. Phase-2 architecture ablation gate

Phase-2 runs on the already-exposed Development windows only and fixes Initial Capital at $100 with the proven V29.3 Small Capital execution stack enabled. The family set is deliberately small:

- BASE100: frozen V29.3 small-cap reference.
- MTF_OFF100: remove the H1 MTF directional gate only.
- GEOM_OFF100: diagnostic removal of the geometry-quality engine only.
- PATTERN_TOL100: modest FibTolerance expansion (0.07) to test pattern coverage without lowering all quality thresholds.
- NON_GRID100: disable Grid only to isolate Non-Grid expectancy; diagnostic, not an instruction to remove Grid commercially.
- ATR15_QUALITY60: one high-evidence combination; moderate ATR coverage recovery (MinAtrPrice 1.5) paired with stricter geometry/PRZ quality (0.60/0.60). This tests whether frequency can be recovered without admitting the low-quality tail observed in Phase-1.1.

Development advancement requires all three Development windows active, no window DD >10%, every window PF >1, total Net >0, total expectancy >0, and no execution-integrity error. Any family failing those conditions is retired. Validation remains PASS/FAIL only and cannot be used for retuning.

## 12. Freeze states

- **Engineering Freeze:** PASS and protected.
- **Performance Freeze:** cannot pass until clean Validation, WF, sensitivity, cost stress, Final Holdout and final account checks pass.
- **Final Commercial Freeze:** PASS only when Engineering Freeze = PASS and Performance Freeze = PASS.

Until then the commercial state remains **TECHNICALLY STABLE / PERFORMANCE DEVELOPMENT**.
