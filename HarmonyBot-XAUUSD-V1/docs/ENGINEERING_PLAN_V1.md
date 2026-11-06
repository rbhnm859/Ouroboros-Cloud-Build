# HarmonyBot XAUUSD V1 — Engineering Plan and Acceptance Matrix

**Date** 2026-11-06. This is an independent new strategy, not a rewrite or revalidation of V74/R18.

## Constitutional controls
- MaxActivePosition=1 and MaxActiveBasket=1; reject any XAUUSD existing/pending position from another strategy when execution is someday enabled.
- No hedge, Martingale, DCA, averaging down, loss recovery, duplicate thesis, widened stops, future observations or risk override.
- Initial portfolio/basket risk hard cap 5%, minimum planned net RR 2, peak drawdown acceptance <=10%. A minimum USD100 balance does not imply minimum lot feasibility.
- All critical broker capabilities and order reconciliation must be verified or the trade is rejected; at V1 prototype stage no trade placement exists.
- All empirical research must use completed-bar/forward-tick causal observations with event_at, observed_at, available_at, decision_at and original approved monetary risk denominator.
- Each new V1 complete OOS year separately requires N>=500, MeanR>=0.90, PF_R>=3.30, WR>=60%, AvgWinningR>=2.30, LCB95>0. The independent monthly compounded 12% target is not a guarantee and does not replace these gates.
- V74 2021–2023 frozen gates remain independent and unchanged (N>=250, MeanR>=0.90, PF_R>=3.30, WR>=70%, AvgRR>=2.30, LCB95>0 every year).

## Detailed phases

| Phase | Deliverable and entry preconditions | Definition of Done / separate evidence |
|---|---|---|
| 0 — Isolation / API | Verify source HEAD, baseline SHA, cTrader package version, data lineage, reusable V71 code, and branch custody. | V74 HEAD unchanged; only V1 paths changed; exact source diff, allowed controls, CI receipt. |
| 1 — Domain Core | Bar/pivot timestamps, event identity, price tick normalization, financial R and ratio structures, decision state, BTC-free C# DLL; no production API calls. | Domain tests, deterministic fixtures, cTrader .algo build and SHA256 custody PASS. |
| 2 — Harmonic | Document 10 separate RuleSets: Gartley, Bat, Alternate Bat, Butterfly, Crab, Deep Crab, Shark, 5-0, AB=CD, Alternate AB=CD. Independent source pin (author, volume, edition, pages), tolerances, pivot grammar, PRZ, completion, invalidation, bullish/bearish witnesses; no projected D treated as completed. | Primary literature license/source integrity; positive, negative, symmetry, geometric boundary, no-lookahead fixtures; reject disputed source. |
| 3 — Timeframe / Regime | Enumerate supported TF and event modes from historical data, causal multi-timeframe joins, opportunity supply analysis, ATR/volatility/EMA/RSI/ADX/swing/sweep/session/spread features and incremental-value ablations. | Fixed vs adaptive TF DEV comparison, stationary and drift checks, data-quality and timestamp/cost evidence. |
| 4 — Decision | Event-native grouping, unique ThesisId and intent, PRZ/swing/indicator confirmation, hard defer/reject, cost-adjusted net-R. | Deterministic replay, no duplicate theses, no conflicting positions, no invalid decision-time features. |
| 5 — Broker & Execution | FXPro broker adapter, exact VolumeInUnits, tick/pip currency conversion, commissions, swap, leverage/margin, position reconciliation, atomic/fenced singleton execution, timeout status reconciliation and recovery. | Read-only capabilities followed by DEMO-ONLY tests; crash/restart, rejects, disconnects, partial fills; no real trading. |
| 6 — Virtual Grid | One-position exits: partial profits, BE tightening, ATR trail, MFE/MAE research exit and adaptive profit locks; **never add position**. | Grid vs grid-off paired OOS comparison; no stop widening / exposure growth; disable if incremental improvement not statistically robust. |
| 7 — Backtest | Pinned multi-year XAUUSD tick data, stress spread/slippage/swaps, executions and complete trade-identity ledger, TF search nested within DEV. | SHA256 dataset/config/cost-model manifest, exact command/container, yearly and monthly metrics, counterexample report. |
| 8 — Independent OOS | Pre-registered blocked/walk-forward tests, purge/embargo on overlapping labels, block bootstrap with length sensitivity, confidence bounds and independent year Gates. | All complete OOS years independently satisfy every Gate; separate four-veto acceptance. |
| 9 — Commercial | Reproducible cTrader build, compatibility matrix per FXPro/other broker, operational incident plan, artifact signing/hashes and rollback proof. | Demo runtime evidence and human-authorized release; live trading forbidden by default. |

## Planned work immediately after isolation Gate
1. P2 reference registry: canonical source receipts (exact page/revision) and rule-level `source_verified` with source-locked SHA. Internal V71 ratios are hypotheses only, never the authority.
2. P2 specialized shape grammars for Shark and 5-0; positive/negative bidirectional unit vectors; projected PRZ from XABC before completed D is distinct from D confirmation; Native Tick geometry sensitivity.
3. P3 feature/store time availability and no-lookahead multi-timeframe contract, then standalone TF/indicator research harness (DEV, not locked V74 OOF).
4. P5 demo-first broker-adapter capability resolution without a live order path. Only after phase and explicit separate deployment approval may an order gateway be considered.

## Cost / release controls
Use only existing GitHub Actions within user-authorized free allotment, isolated branch/path triggers and exact reproducible tests. Do not automatically run full historical cTrader CLI, touch Railway/LibreChat, migrate protected data, or call paid APIs. Keep `AlgoPublish=false` and `TradingApproved=false`.

## Recovery checkpoints
Every stage must record BASE SHA, HEAD SHA, workflow run, audit and compiler result, artifact digest, tests executed, factual limits and the first unresolved prerequisite. Failed jobs remain evidence, never overwritten by manually claimed PASS.
