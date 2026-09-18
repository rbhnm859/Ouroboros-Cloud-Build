# HarmonyBot Commercial Convergence One-Pass — Codex Execution Command

從目前 **真實 GitHub Evidence** 繼續，不建立新的 Deep Research，不重新研究整個 HarmonyBot，也不要採用「V29.6 → V29.7 → V29.8」逐版本修補模式。

## 0. Source of truth

Repository: `rbhnm859/Ouroboros-Cloud-Build`

Verified starting commit:

`ba8caeab70fc860a68cf72270bcb4d491a90462a`

Verified completed workflow:

`HarmonyBot V29.5 Final Architecture Decision`

Run ID:

`35322359842`

Before modifying anything, re-fetch the run metadata and artifacts and verify that the run head SHA is exactly the SHA above. If the repository has moved forward, DO NOT silently use newer strategy evidence: branch from the verified SHA or explicitly prove that later changes are non-strategy-only.

Consume existing artifacts directly; do not rerun them merely to recreate the same evidence:

- V295-DEV-DEV-A
- V295-DEV-DEV-B
- V295-DEV-DEV-C
- V295-DEVELOPMENT-GATE
- V295-ENGINEERING-REGRESSION

Known verified state to reproduce from artifacts before proceeding:

- Build PASS
- Engineering Regression PASS
- 122 Development baskets total
- DEV-A: 47 baskets, PF ≈ 0.992
- DEV-B: 30 baskets, PF ≈ 0.150
- DEV-C: 45 baskets, PF ≈ 0.866
- Aggregate PF ≈ 0.703
- Aggregate Net ≈ -804.34
- Max DD ≈ 7.16%
- Frequency ≈ 81.33 baskets/year
- Execution errors = 0
- Frequency supply proven; positive expectancy not proven
- Final Holdout untouched

If these do not reproduce, STOP with EVIDENCE_MISMATCH rather than optimizing against a different dataset.

## 1. Permanent engineering freeze

The following are immutable and must be protected by source-diff assertions and regression tests:

- $100 Small Capital Infrastructure
- Risk Sizing
- MinVolume Protection
- Volume Normalization
- Margin / Free-Margin Protection
- Protective SL / server-side protection
- Grid Risk-Cap
- Anti-Hedge
- Duplicate Main Entry Protection
- Fail-Closed behavior
- Execution Integrity
- Broker/API handling
- Capital Protection

Do not improve PF, WR, ROI or frequency by weakening any of these. Do not re-open Direction Gate, Phase-1/2/3, V29.4 preset optimization, or completed V29.5 development.

## 2. Professional bottleneck thesis

Treat the current problem as **edge selection and payoff conversion**, not signal generation.

The 122-basket evidence already shows that increasing raw frequency alone produced negative-expectancy flow. Reproduce and validate the following hypotheses from the existing artifacts:

1. DEV-B is the worst window and its losses are highly concentrated.
2. 13:00 UTC is a DEV-B loss concentration, but because the same hour is not consistently negative in DEV-A/C, hour=13 alone is NOT eligible for a hard block.
3. High-volatility flow is the stronger cross-window structural candidate.
4. In particular, Cypher × high-volatility has repeated negative expectancy across Development windows and is eligible for a simple context-aware admission hypothesis.
5. Existing V29.5 Development executed zero Grid baskets; therefore do not blame executed Grid adds for DEV-B. Preserve thesis-validity protection and instrument future Grid eligibility/add context instead of inventing a Grid root cause.
6. Existing artifacts do not contain trustworthy complete per-basket MFE/MAE/HTF/PRZ/geometry snapshots. Mark unavailable fields UNVERIFIED. Never synthesize them.

The architecture goal is therefore:

**Raw harmonic setup → context classification → context-aware admission → execution → thesis validity → payoff conversion**

not:

**Raw harmonic setup → more filters → fewer trades**.

## 3. Build ONE Commercial Convergence RC, not sequential versions

Create a single isolated branch:

`harmonybot/commercial-convergence-rc`

Create one coherent patch file, for example:

`tmp/harmonybot-v26-build/fix_harmonybot_commercial_convergence_rc.py`

Do not modify the frozen baseline in place.

The RC may add only a small, auditable Context-Aware Edge layer. It must remain deterministic, explainable, causal at decision time and free of future leakage.

### 3.1 Admission architecture

Do NOT create dozens of thresholds.

Use no more than three hypothesis families total:

**Candidate A — Structural Negative Cluster Exclusion**

- Exclude only clusters that are demonstrably negative in at least two Development windows and have adequate sample support.
- Primary hypothesis: Cypher under objectively defined high-volatility regime.
- Do not hard-block 13:00 merely because DEV-B was bad there.
- Do not create hour-by-hour lookup tables.

**Candidate B — Regime-Adaptive Pattern Admission**

- Pattern × volatility-regime admission.
- Prefer relative/rolling volatility state over a brittle absolute ATR constant when possible.
- The volatility baseline must use only bars available at the signal time.
- Keep low/normal-volatility Cypher supply when evidence does not justify removing it.
- Do not globally raise MinATR, MinGeometryQuality, PRZ, confidence or MTF thresholds to manufacture PF.

**Candidate C — Regime Admission + Payoff/Thesis Conversion**

- Same simple admission architecture as B.
- Preserve V29.5 thesis-validity logic.
- Add only evidence-driven winner-capture / invalidation behavior if MFE/MAE telemetry from the new Development run proves that entry was valid but profit was given back.
- Grid additions remain conditional on thesis validity. Do not force Grid activity.

Candidate A/B/C are the ONLY Development candidates. No brute-force parameter matrix.

## 4. Add causal telemetry BEFORE candidate evaluation

Because the old 122 baskets lack enough causal state, instrument the RC once and have all three candidates emit the same structured telemetry.

At signal/admission time record, without future information:

- candidate
- window
- basket ID
- pattern
- direction
- signal timestamp
- entry timestamp
- entry hour
- session segment
- entry price
- ATR now
- rolling ATR baseline
- ATR/baseline ratio
- volatility regime
- PRZ quality available at that moment
- geometry quality available at that moment
- pattern/composite quality
- HTF state actually available at that moment
- trend/range state if already computable causally
- admission decision
- exact admission reason

During basket life record:

- initial structural risk
- protective SL
- peak favorable price
- peak adverse price
- MFE in R
- MAE in R
- time-to-MFE
- time-to-MAE
- winner giveback in R
- Grid eligible/not eligible
- Grid add timestamp/context if any
- thesis-valid/thesis-invalid state
- exit type/reason
- holding time
- realized pips
- realized money
- realized R/R

Telemetry is observation, not permission to create additional candidate rules after seeing results.

## 5. Candidate parameters must be PRE-REGISTERED

Before running A/B/C, create:

`commercial-convergence/PRE_REGISTERED_CANDIDATES.json`

It must contain the exact logic/thresholds for A/B/C, the evidence supporting each rule, sample counts, windows supporting it, and the rejection criteria.

After the first A/B/C Development run starts, this file is immutable.

No post-hoc threshold adjustment against DEV-A/B/C.

## 6. Development evaluation

Run exactly A/B/C over the same DEV-A/B/C windows used by Run 35322359842.

Use the same broker/cost/data assumptions as the verified Development baseline unless a setting is part of the explicitly preregistered candidate hypothesis.

For every candidate/window calculate basket-level:

- baskets
- annualized frequency
- PF
- net
- expectancy
- WR
- realized RR
- max DD
- average MFE
- average MAE
- median MFE/MAE
- winner giveback
- largest loss
- top-1/top-3/top-5 tail loss contribution
- main vs Grid contribution
- admission-block counts by reason
- execution errors

Also generate:

- EDGE_ATTRIBUTION_MATRIX.csv/json
- DEV_B_LOSS_CONTRIBUTION.csv/json
- CROSS_WINDOW_CLUSTER_VALIDATION.csv/json
- PAYOFF_CONVERSION_ANALYSIS.csv/json
- FREQUENCY_FRONTIER.csv/json

Small-sample clusters remain EXPLORATORY and cannot become hidden hard gates.

## 7. Hard Development Gate

A candidate may advance only if ALL are true:

- 3/3 windows contain trades
- 3/3 PF > 1.0
- 3/3 expectancy > 0
- aggregate net > 0
- aggregate expectancy > 0
- max DD <= 10%
- execution errors = 0
- robust frequency >= 50 actual baskets/year

Selection is not “highest PF”. Build a Pareto/frontier decision using:

- worst-window PF
- aggregate expectancy
- DD
- frequency
- tail-loss concentration
- parameter simplicity

Prefer the candidate with stable worst-window positive expectancy and the highest retained robust frequency.

Target >=75/year, but never add negative-expectancy flow merely to reach it.

If none of A/B/C passes, STOP. Do not create another strategy version. Produce:

`STRATEGY_ARCHITECTURE_LIMITATION.md`

with:

- maximum robust PF observed
- maximum robust frequency compatible with positive expectancy
- maximum robust ROI observed
- worst-window PF
- primary remaining bottleneck
- whether the likely limitation is harmonic edge scarcity, regime instability, payoff conversion, or $100 execution economics

## 8. One untouched Validation only after Development PASS

Predeclare a Validation interval that has not been used for candidate construction, threshold choice or earlier HarmonyBot tuning. Prove its non-overlap in an exposure ledger.

Run the selected candidate exactly once.

Required:

- PF >1
- expectancy >0
- net >0
- DD <=10%
- errors=0
- frequency does not collapse

Validation failure = candidate rejected. Do not change parameters and reuse that Validation.

## 9. Real $100 FxPro Commercial Gate

Only after Validation PASS.

Use:

- Initial balance: $100
- Broker: FxPro demo matching existing account evidence
- XAUUSD
- leverage 1:500
- Small Capital Mode ON
- realistic commission/spread/slippage settings already used by the commercial workflow
- no $10,000 proportional inference

Audit the full lifecycle:

Pattern → Signal → Pending → Trigger → Main Entry → Grid Eligibility → Grid Add if valid → Protective SL → Management → BE → Trailing → Exit → Basket Close → Risk Reset → Next Trade.

Report:

- RawSignals
- EligibleSignals
- ExecutedMainEntries
- ExecutedBaskets
- SkippedByMinVolume
- SkippedByRisk
- SkippedByMargin
- SkippedBySpread
- SkippedByCost
- MaximumMarginUsage
- MinimumFreeMargin
- MaximumActualRisk
- MaximumBasketRisk
- invalid volume
- unprotected position
- hedge
- duplicate entry
- execution errors
- $100 actual executable baskets/year

$100 DD must remain <=10%.

Commercial frequency is the $100 executable frequency, not the $10,000 frequency.

## 10. Robustness sequence — only after Development + Validation + $100 PASS

Run in this order, with no parameter tuning between them:

1. OOS
2. Walk-Forward
3. parameter sensitivity around the frozen selected values: ±5%, ±10%, ±20%
4. spread stress
5. commission stress
6. slippage stress
7. combined cost stress
8. basket-level Monte Carlo

Reject exact-point-only success.

Record median and worst-window PF, expectancy, DD, frequency and $100 survival characteristics.

## 11. Commercial targets vs gates

Do not curve-fit to these. They are post-robustness targets:

- PF target >=2.5
- WR target >=65%
- realized RR target >=2:1
- annual ROI target >=100%
- profitable months target >=10/12
- actual executable trades/year long-term target >=200
- DD <=10%

A commercially credible RC may be labelled NEAR_TARGET rather than falsely failed if it passes every robustness gate but does not hit every aspirational KPI.

Create a target-gap table showing achieved value, target, gap and whether closing the gap would require unsafe/unsupported optimization.

Never claim guarantees.

## 12. Final Holdout

Keep Final Holdout UNTOUCHED until:

Engineering PASS
→ Development PASS
→ Validation PASS
→ $100 PASS
→ OOS PASS
→ Robustness PASS.

Then and only then run the Final Holdout once.

No tuning after Holdout.

## 13. Commercial Freeze decision

Create one final artifact:

`commercial-convergence/FINAL_COMMERCIAL_DECISION.md`

Allowed conclusions only:

- FINAL COMMERCIAL FREEZE = PASS
- FINAL COMMERCIAL FREEZE = NEAR_TARGET
- FINAL COMMERCIAL FREEZE = HOLD
- STRATEGY ARCHITECTURE LIMITATION

PASS requires every mandatory gate, not merely attractive PF.

NEAR_TARGET requires every mandatory safety/robustness gate to pass while aspirational commercial KPI(s) remain below target; list the exact gaps.

HOLD if mandatory evidence is incomplete.

## 14. GitHub execution behavior

Commit the RC architecture, preregistration, workflow and reporting scripts to the isolated branch.

Open a PR to main, but do NOT merge automatically.

Trigger only the new consolidated Commercial Convergence workflow.

The workflow itself must enforce gate order and automatically stop downstream jobs when an upstream gate fails.

Do not wait for the user to type “continue”. Run through all automatically authorized gates. If a gate fails, stop there and publish the evidence instead of starting another optimization cycle.

Upload artifacts for every completed gate, including the final compiled .algo only if the candidate reaches the appropriate commercial freeze stage.

At the end report:

- branch
- commit SHA
- PR
- workflow Run ID
- exact candidate selected
- DEV-A/B/C metrics
- Validation metrics if authorized
- $100 metrics if authorized
- robustness metrics if authorized
- final commercial status
- exact remaining KPI gaps
- confirmation that Final Holdout remained untouched unless legally reached by the gate chain.
