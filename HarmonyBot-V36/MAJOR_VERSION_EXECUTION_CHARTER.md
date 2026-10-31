# HarmonyBot V36 — High-Frequency Harmonic Portfolio Architecture

## Mandate
This is a MAJOR VERSION program. Do not create V35.2/V35.3/V36.1 patch chains. Work on V36 as one coherent architecture replacement and only stop for a material breakthrough, an unrecoverable engineering/data blocker, or a decision that requires owner authorization.

Parent evidence:
- V35.1 source SHA: 0b2ef01895bfa14a8dae9c298b47a340e93e6f03
- Development winner/control: EXHAUSTION_VETO_ONLY
- Control evidence: 66 baskets; annualized ~44/year; PF 1.16694; net +492.11; expectancy +7.456; max DD 8.04%; 2/3 positive windows; worst-window PF 0.8881; engineering_clean=true.
V35.1 is evidence/control, not a patch base to incrementally tune.

## Primary objective
Increase VALID/EXECUTABLE trade frequency materially without manufacturing count by relaxing risk safety or accepting negative-quality trades.
Target progression: >=50 -> >=100 -> >=150 -> >=200 executable baskets/year where evidence supports it.
If >=200/year is not physically robust under XAUUSD + FxPro + small-capital constraints, report Maximum Robust Executable Trades/year instead of forcing the target.

## Non-negotiables
- Fibonacci/Harmonic remains the entry thesis.
- H4/H1/M15/M1 independent bars; completed-bar/no-lookahead discipline.
- XAUUSD, FxPro/cTrader Mobile/Cloud, UTC0, DST-aware London-to-New-York operating session.
- No duplicate opening; MaxActiveBasket=1; no hedging.
- Basket risk <=1%; server-side protection; max-DD/daily-risk locks; broker volume/margin/min-distance protections; fail-closed.
- No Martingale, DCA, Recovery, Loss Averaging.
- Fibonacci staged entry is permitted only as a pre-planned harmonic PRZ execution structure with total basket risk capped; it must never be loss-recovery sizing.
- Do not increase frequency by raising risk, forcing minimum volume, weakening SL/margin protection, or adding recovery exposure.
- Previously exposed/fresh-validation data may not be used for tuning.

## V36 architecture
H4 Macro Regime
 -> H1 Harmonic Context Portfolio
 -> M15 Multi-Candidate Harmonic Detector
 -> Candidate Quality/Conflict Matrix
 -> Exhaustion Evidence Layer
 -> Transition Quality Score (not blanket hard veto)
 -> M1 Execution Scheduler (timing, not alpha veto)
 -> Frequency-Aware Candidate Arbitration
 -> PRZ Fibonacci Execution Planner
 -> Basket Risk/Capital Feasibility
 -> Server-Protected Execution
 -> Exit/Risk Engine.

### Frequency expansion mechanisms
Investigate frequency only through structural sources:
1. Pattern-family coverage and detector recall across supported harmonic families.
2. Multiple independent M15 candidates per completed bar with deterministic de-duplication.
3. Candidate TTL / PRZ lifecycle efficiency so valid setups are not lost operationally.
4. Route-specific acceptance where V35.1 hard/blanket context rejection destroys positive expectancy.
5. Transition as graded quality/context rather than binary rejection.
6. M1 as execution timing to improve fill/entry quality without deleting a valid HTF/M15 thesis.
7. Session sub-regimes inside the full London-to-US window; never choose hours solely because one DEV slice won.
8. Capital feasibility / minimum-volume diagnostics so $100 execution loss is measured separately from alpha loss.
9. Candidate arbitration: when multiple valid patterns compete, rank rather than discard the entire opportunity set.
10. Pattern-specific PRZ/fib execution profiles that preserve structural invalidation and canonical targets.

## Signal-to-Trade Funnel
For every DEV window record:
Raw Harmonic Signals -> Pattern Qualification -> PRZ -> Direction/Conflict -> Regime -> Exhaustion -> Transition Quality -> Session -> Spread -> M1 Timing -> Candidate Arbitration -> Risk -> MinVolume -> Margin -> Executed Basket.
For every stage output pass/reject/rate and estimated trades lost/year. Where sample size permits, compute rejected-setup PF/expectancy/WR/RR.

Classify every filter:
ESSENTIAL / USEFUL / REDUNDANT / OVER_RESTRICTIVE / REGIME_DEPENDENT / HARMFUL.

## One-pass research protocol
1. Reproduce V35.1 EXHAUSTION control exactly. If reproduction fails, engineering-fix only and re-run; do not tune.
2. Build V36 telemetry-first detector/funnel and loss/opportunity anatomy.
3. Identify the top frequency bottlenecks AND their rejected-setup economics.
4. Construct a bounded set of major V36 architecture families, not patch versions.
5. Run fixed DEV-A/B/C ablation under identical costs/windows.
6. Eliminate any family that gains count by materially degrading expectancy, DD, execution integrity, or cross-window robustness.
7. Select the Pareto candidate with the largest robust executable-frequency advance while preserving positive edge.
8. Freeze alpha.
9. Only then run bounded exit/risk refinement without changing entry alpha.
10. Run $100/$150/$200/$300/$500/$1000 capital compatibility on the frozen candidate.
11. Freeze source/hash/preset/cost model.
12. Reserve and run untouched fresh validation exactly once only after development gates pass.
13. Build commercial .algo/release package only after validation PASS.

## Development gates
Hard engineering:
- compile/build PASS
- executionErrors=0
- engineering_clean=true
- no lookahead/timeframe contamination
- no duplicate/hedge/risk-cap/protection violations.

Performance/robustness:
- DEV-A/B/C all contain executed trades
- aggregate Net > 0 and Expectancy > 0
- Max DD <=10%
- at least 2/3 DEV windows net positive
- candidate must demonstrate relative advance over V35.1 control
- frequency advance must be executable frequency, not raw/projected signals
- report PF/WR/RR/trades/year, but never fabricate a pass to hit aspirational targets.

Commercial target vector (targets, not guaranteed gates):
PF >=2.5; Max DD <=10%; WR >=65%; realized RR >=2:1; >=200 executable trades/year; annual return >=100%; >=10/12 profitable months.
Priority: DD -> PF -> OOS stability -> WR -> return, while this V36 program explicitly seeks the maximum robust frequency frontier.

## Major-breakthrough definition
Only interrupt/report proactively when one of these occurs:
- >=2x V35.1 executable annualized frequency with positive aggregate expectancy, DD<=10%, and no engineering regression;
- first candidate reaches >=100 executable baskets/year while retaining positive edge and cross-window viability;
- a candidate reaches the commercial target neighborhood without evidence contamination;
- a fundamental architecture finding invalidates the current direction;
- an unrecoverable permission/data/runner blocker requires owner action.

Otherwise continue the V36 pipeline without requesting tuning decisions.

## Mandatory outputs
V36_SIGNAL_TRADE_FUNNEL.json/.md
V36_OPPORTUNITY_ANATOMY.json/.md
V36_ARCHITECTURE_ABLATION.json/.md
V36_FREQUENCY_FRONTIER.json/.md
V36_PROMOTION_DECISION.json
V36_EXIT_RISK_ABLATION.json/.md
V36_CAPITAL_COMPATIBILITY.json/.md
V36_FINAL_FREEZE_MANIFEST.json
V36_FRESH_VALIDATION.json/.md
V36_COMMERCIAL_RELEASE_DECISION.json/.md

All result JSON must state source SHA, dataset/window identity, cost assumptions, engineering_clean, executable baskets/year, relative_advance, and evidence limitations.
