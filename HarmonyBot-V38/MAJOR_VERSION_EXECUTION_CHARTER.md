# HarmonyBot V38 — M15 Thesis / M5 Evidence Execution

V38 is a major architecture replacement, not a V37.x patch.

## Architecture contract
- H4: macro regime and structure.
- H1: harmonic context and conflict.
- M15: harmonic thesis, XABCD geometry, PRZ, invalidation, canonical targets, route and candidate creation.
- M5: execution evidence only. M5 is not a second alpha engine.
- M1: broker data granularity only; never a mandatory strategy timeframe.

## Fixed hypotheses
1. SINGLE_BAR_CONTROL — completed M5 single-bar evidence with candidate survival, no accumulated evidence, no opportunity arbitration.
2. EVIDENCE_ONLY — bounded 2–4 bar M5 evidence accumulation; reject after the evidence minimum if threshold is not met.
3. EVIDENCE_SURVIVAL — evidence accumulation plus keep-alive until TTL/structural invalidation.
4. FULL_EXECUTION — evidence accumulation + survival + opportunity-cost candidate arbitration.

No brute-force threshold search is permitted in this phase.

## Evidence model
M5 evidence combines reclaim, micro-BOS, rejection, failed extension, displacement and directional close behavior. Evidence is accumulated over completed bars only.

## Counterfactual ledger
Every pre-execution terminal candidate can enter a bounded shadow ledger. Record subsequent target/stop/unresolved outcome, MFE and MAE without affecting trading. Shadow evidence is diagnostic only and cannot be used as hidden OOS tuning.

## Risk normalization
Before L0 market execution, recompute all-in risk from the actual market entry, including modeled cost. Renormalize L0 volume downward within the remaining basket risk budget. Never force broker minimum volume. Total basket risk remains <=1%.

## Promotion floor
A DEV candidate must have:
- >=50 executable baskets/year
- PF >=1.10
- expectancy >0
- Max DD <=10%
- >=2/3 positive DEV windows
- worst-window PF >=0.80
- engineering_clean=true

Major breakthrough remains >=2x V35.1 frequency with positive edge and clean risk, or first robust >=100 executable baskets/year.

## Post-promotion
Only a promoted DEV candidate proceeds to $100/$150/$200/$300/$500/$1000 compatibility. Only a $100-compatible frozen candidate may consume the predeclared untouched 2020-H1 validation package. No tuning after fresh validation.
