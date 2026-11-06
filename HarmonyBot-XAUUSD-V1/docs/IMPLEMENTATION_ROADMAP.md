# HarmonyBot XAUUSD V1 — engineering implementation contract

Version: V1.1 Cleanroom. This document separates PLANNED implementation from measured evidence.

## Nonnegotiable rules

XAUUSD, cTrader Automate C#, FXPro priority with broker-independent adapters; USD 100 minimum eligibility, not fill guarantee; arbitrary causal timeframes; one open XAUUSD position and basket globally across instances; no hedge, DCA, Martingale, recovery, loss averaging, widen stop, duplicate thesis, unbounded grid or future leakage; planned stressed net RR >=2, active risk <=5%, max drawdown <=10%. Risk + Model Validation + Red Team + Data Governance are independent non-compensatory vetoes. `TradingEnabled` is NOT an available parameter in the prototype.

## Phase 0 — repository, history and authority (DONE for initial scope)

Inputs: V1 source commit, official cTrader API, GitHub Actions logs, safe source snapshot.
Outputs: clean source tree, separate workflow and frozen lineage.
Acceptance: original V74 HEAD unchanged, one new workflow only, zero inherited legacy dirs, no deployment, no order API calls. A clean CI receipt is mandatory.

## Phase 1 — causal Domain Core (PROTOTYPE PASS)

Domain contracts for completed bars, availability timestamps and causally confirmed pivots; alternating pivot construction, no duplicate event identities; price-normalized R, independent broker snapshot + risk-allocation math, one-trade partial-close accounting; UTC, London/New York DST sessions; a gated research-only cBot.

Evidence: prior commit 1ca32dbd; run 42153957669; 54 contract tests and compiled research .algo.
Remaining parity tests: cTrader runtime `OnBarClosed` bar index semantics and bar-close timestamp across weekend/DST, real broker symbol properties, cross-instance uniqueness and persistent reconciliation. Static compilation is insufficient.

## Phase 2 — complete ten-pattern Harmonic engine

Canonical family IDs: Gartley, Bat, Alternate Bat, Butterfly, Crab, Deep Crab, Shark, 5-0, AB=CD, Alternate AB=CD. For each: primary Carney work/volume/edition/page citation (or clearly differentiated independent source), distinct pivot grammar, bullish/bearish symmetry, ratio boundaries and tolerance model, projected PRZ from X/A/B/C, confirmed D, invalidation and expiry, source-lock SHA256, positive/negative fixtures, no common duplicate event counting. Current V71 envelopes are provisional and `TradingApproved=false`; Shark and 5-0 remain specialized and unimplemented, not falsely marked PASS.

Admission gate: only causally available pivots, reproducible pattern fixtures and independent rule review, with no OOF feedback.

## Phase 3 — market intelligence and timeframe selection

Build candidate generator for single/multiple/event-based timeframes; timeline-indexed `event_at/observed_at/available_at/decision_at`; causal as-of joins using ONLY fully completed source bars; data coverage and spread/tick quality audit; regime/indicator alternatives (EMA, adaptive MA, ATR, realized vol, RSI/BAMM, ADX, structure, liquidity sweeps, sessions); incremental information with ablation and uncertainty intervals. Use chronological nested DEV splits with selection freeze, comparing fixed against adaptive timeframe policies.

Admission gate: stable DEV uplift net of costs with permutation and negative controls, no lookahead, no filtering solely to inflate WR.

## Phase 4 — trade decision and candidate ledger

State machine DISCOVER→PROJECT→COMPLETE→EVALUATE→DEFER/REJECT/ENTER→MANAGE→CLOSE. Deterministic trade thesis identity, overlapping-pattern arbitration, price-side and first-passage entry, event lease and no reentry, cost-sensitive stop/target, multi-timeframe regime and valid institutional session. No live action in this phase.

Admission gate: deterministic replay + event ledger tests, risk/duplicate rejects even when alpha score is high.

## Phase 5 — broker, risk and execution

Implement `BrokerSymbolResolver`, `BrokerCapabilityProfile`, `PositionSizer`, `CostEstimator`, `MarginValidator`, `OrderIntentLedger`, `ExposureGuard`, `ExecutionGateway`, `PositionReconciler`, `RecoveryController`. Verify `VolumeInUnits{Min,Max,Step}`, Tick/Pip size, commission, spread, real FX conversion, margin, stop-distance and symbol hours using FXPro demo first and other brokers separately. Persist order intent before submit; on timeout reconcile, never blindly resubmit; enforce single execution lease across instances. Keep real-order method behind an explicit, independently authorized release switch.

Admission gate: mocked reject, network loss, restart, partial fill/close, duplicate and cross-strategy hedge attacks, broker demo only AFTER independent authorization.

## Phase 6 — Virtual Profit Grid

Single-position-only dynamic profit levels, partial close, break-even, ATR trailing, MFE/MAE, trend-extension exit, volatility locks; never open/grid-increase position, never widen stop, never modify original initial-risk denominator. Compare Grid ON/OFF using locked, cost-adjusted OOS and full-lifecycle accounting. Disable if uplift fails.

## Phase 7 — multi-year reproducible tick research

Immutable dataset hash, time/price-side first-passage, realistic spread/slippage/commission/swap, actual symbol lot/volume/margin, no-lookahead; research-only tick backtest, deterministic trade ledger, cost shocks and independent yearly metrics. Execution never equated with shadow.

## Phase 8 — independent OOS and uncertainty

Predeclare annual locked OOS window distinct from already-burned V74 years. Walk-forward on DEV, sealed strategy selection, block bootstrap LCB95 of MeanR with block-length sensitivity and serial dependence, per-year N/MeanR/PF_R/WR/Avg winning R/LCB95. 500 trades / 60% win / 3.30 PF / 0.90 MeanR gates independently every full year. Counterexample tests, negative controls, data governance and red-team vetoes mandatory. Monthly 12% compounding path evaluated separately as aspiration.

## Phase 9 — commercial release

Release artifacts = complete source, verified .algo, cTrader compatibility matrix, FXPro demo evidence, trade/event ledger, source/data/config/cost hashes, reproducible command, net/yearly/LCB report, rollback playbook, independent four-veto acceptance. Stop at NOT VERIFIED/BLOCKED if any required source/artifact is absent; NEVER enable live trading without separate authorization.

## CI economics and cadence

Only dependency-free .NET unit tests and compile on each cleanroom commit. No secrets, no cTrader backtests, no paid optimization and no external AI model charges in automatic workflows. Large evaluations require separate manual, budget-gated workflows. Do not rerun successful unchanged source/algorithm tests.

## Priority next executable engineering task

P2.1: source-lock and independent geometry RuleSet grammar for Gartley and Bat, with strict causal projection/confirmation and adversarial fixtures; then extend individually to remaining eight families. Avoid fake completeness or silent ratio substitutions.

## Acceptance states

Each requirement has exactly PASS (measured), FAIL (counterexample), BLOCKED (prevented by missing authority or dependency), or NOT VERIFIED (untested or insufficient evidence). A compiler success is not a live cTrader behavioral or performance PASS.
