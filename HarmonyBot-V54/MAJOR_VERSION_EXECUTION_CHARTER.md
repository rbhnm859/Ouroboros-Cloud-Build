# HarmonyBot V54 — Universal Harmonic Liberation & Fibonacci Grid Alpha Core

## Mission
V54 is a clean major-version reconstruction. It must preserve historically proven high-quality Alpha, remove architecture-level suppression of valid harmonic families, admit expansion trades only when the added cohort itself is profitable, and promote Fibonacci Grid from an auxiliary execution feature into a causally tested core execution engine.

## Role-weighted design
Initial decision weights: Harmonic/Fibonacci Quant 14%; Commercial System Architect 12%; Math/Geometry/Statistics 10%; Execution 9%; Risk 8% + veto; Model Validation 8% + veto; Experimental Design 8%; Backtest Forensics 7%; GitHub/cTrader CI 5%; SRE 4%; Adversarial Red Team 6% + veto; Data Governance/OOS 3% + veto; Portfolio Opportunity Cost 3%; Commercial QA 3%. All roles remain active. Risk, Validation, Red Team and OOS/Data Governance vetoes are permanent.

## Frozen non-negotiables
- FxPro / cTrader / XAUUSD / UTC0 / H4-H1-M15-M1.
- Harmonic/Fibonacci is the entry thesis.
- Completed bars only; no lookahead.
- MaxActiveBasket=1; anti-hedge; canonical setup dedupe.
- No Martingale, DCA, Recovery, Loss Averaging, Hedging.
- Whole basket risk <=1%.
- MinimumNetRR=2.0.
- Structural/server-side protection, broker min-volume/min-distance, margin/free-margin and DD locks stay fail-closed.
- V51 execution corridor remains disabled.
- V52 projected-PRZ LIVE path remains disabled.
- Fresh/OOS cannot be used for tuning.

## V54 architecture
### 1. PROVEN_CORE_ALPHA
A preserved lane derived from the legacy high-quality envelope. Core candidates receive execution-slot priority and are not forced through the new expansion confirmation lane.

### 2. HARMONIC_EXPANSION_ALPHA
All mathematically detected family hypotheses are allowed through the liberation identity stage without a generic geometry-floor kill. Family quality is retained as a vector/score and used later.

### 3. Universal Harmonic Liberation
No valid family may be silently zeroed by a generic post-detector quality floor. Family routing is native to retracement, extension, 5-0 transition and AB=CD primitive semantics. Shark/Cypher keep their proven legacy routing.

### 4. Expansion Economic Admission
Expansion candidates must pass MinimumNetRR=2 and a preregistered family-aware economic-quality score. Core candidates are not requalified by this expansion gate.

### 5. Fibonacci Grid Alpha Core
Four causal modes are fixed: L0_ONLY, LEGACY_GRID, FAMILY_NATIVE_GRID, FAMILY_NATIVE_GRID_STATE_AWARE. Legacy Fibonacci levels remain the control. Family-native allocation never exceeds the same 1% basket budget. State-aware mode can cancel deeper pending legs when the thesis is already proved or weakens; it never adds recovery levels.

## Alpha DEV matrix
Fixed variants x DEV-A/B/C:
- V51_QUALITY_CORE_REPLAY
- V52_LIBERATION_CONTROL
- V54_CORE_PLUS_LIBERATION
- V54_FULL_ALPHA

Core Preservation Gate for V54_FULL_ALPHA:
- >=90% of current-run V51 core setup identities retained;
- retained-core Net >=90% of current-run V51 control Net;
- retained-core PF >=90% of current-run V51 control PF.

Marginal Expansion Gate:
- added trades >0;
- added cohort Net >0;
- Expectancy >0;
- PF >=1.25;
- A/B/C added-cohort Net each >=0.

Universal Liberation Gate:
Every family with detected hypotheses must show a liberation/qualification pass; no generic family starvation.

Commercial DEV minimum remains:
>=90 baskets/1.5y; >=60/year; Net>=1800; PF>=2.0; Expectancy>=20; WR>=50%; DD<=6%; A/B/C all positive; unique setups=baskets; engineering/risk clean.

## Grid DEV matrix
With the V54 Full Alpha kernel fixed, compare:
- L0_ONLY
- LEGACY_GRID
- FAMILY_NATIVE_GRID
- FAMILY_NATIVE_GRID_STATE_AWARE
Each x DEV-A/B/C on the exact same immutable data snapshots.

A Grid candidate must:
- beat L0 on Net, PF and Expectancy;
- improve Net in >=2/3 windows;
- DD <=6%;
- engineering/risk clean;
- satisfy the same Commercial DEV gate.
Family-native modes must also improve Net over LEGACY_GRID to replace it. If they do not, Legacy Grid remains the evidence-backed final Grid.

## Governance
Build once, immutable .algo reuse, A/B/C market-data snapshots hashed and reused by every Alpha/Grid variant. Only engineering/YAML/parser/data-artifact defects may be auto-fixed without a new Alpha preregistration. No post-result threshold tuning. Capital -> Freeze -> exactly one Fresh Alpha and one Fresh $100 only after Alpha + Grid DEV gates pass. Formal final decision is only COMMERCIAL_FREEZE_CANDIDATE_PASS or HOLD_WITH_EVIDENCE.
