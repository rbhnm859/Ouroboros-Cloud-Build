# HarmonyBot XAUUSD V1 — isolated research branch

**Status: engineering prototype / execution hard-disabled.** This is a new strategy development lane. It does not change V74/R18, their year gates, the existing broker deployment or any live account.

## Verified starting evidence
- Source repo: rbhnm859/Ouroboros-Cloud-Build
- Parent: c3283e6f61741a5a9a3d2fc7ea31a066b64f7806
- Source reuse: V71 Domain/Safety architecture, `HarmonyBot-V71/tools/harmonic_precision_contract.py` (internal ratio envelopes, NOT primary-source certification), original V74 research kept untouched.
- cTrader Automate package: 1.0.19 (same package as legacy V71). Compile and actual .algo output are **not verified** until CI completes.
- Official API reference: https://help.ctrader.com/ctrader-algo/references/General/Robot/
- Official volume normalization: https://help.ctrader.com/ctrader-algo/references/MarketData/Symbols/Symbol/NormalizeVolumeInUnits/
- API is not thread safe: https://help.ctrader.com/ctrader-algo/documentation/migration-from-net-framework/

## Current deliverables
- `src/HarmonyBot.XauUsd.Core/`: immutable completed-bar/pivot contracts, causal confirmation lag, deduplicated event ID, research geometry registry, PRZ intersection, feature-availability gate, independent broker/risk snapshots, NetRR and margin-constrained volume, no-stop-widening Virtual Grid primitives, DST-aware session gate, hard-disabled trading decision.
- `tests/HarmonyBot.XauUsd.Tests/`: dependency-free executable C# contract tests.
- `src/HarmonyBot.XauUsd.cBot/`: cTrader read-only observation adapter with **no order API calls**.
- `.github/workflows/harmonybot-xauusd-v1-domain.yml`: branch-scoped CI; does not use broker credentials, cTrader CLI backtests or any paid service.

## Explicit limitations and fail-closed guards
1. Ten families are **declared research profiles**, not ten primary-literature-verified and production-approved detectors. XABCD and AB=CD families use transcribed internal V71 research envelopes. Shark/5-0 need distinct native pivot grammars and intentionally return no matches. All `TradingApproved=false`.
2. The research allocation math requires audited currency conversion, margin, stop-distance, current spread/slippage/commission and FXPro/other-broker symbol specifications. These are not observed by this static library.
3. ResearchIntentLedger is an in-process deduplication test primitive; NOT durable and not a distributed lease. Runtime broker reconciliation, persistent orders, swap accounting, partial fills and live recovery are NOT implemented.
4. Timezone conversion requires system IANA/Windows timezone data; holiday/trading-hour confirmation is provided externally and must be true. No market calendar is inferred.
5. Rolling multi-timeframe selection, indicator incremental-value testing, independent OOS, tick backtests, empirical strategy gates and V1 commercial acceptance are NOT RUN.
6. Virtual Grid only permits decreasing exposure or tightening protective stops. It never creates additional orders.
7. RiskGate.Evaluate returns a **research sizing result**, never an order authorization. Every trading decision is rejected by the Phase 1 adapter. No trade API calls exist.
8. USD 100 means **minimum balance eligibility**, not guaranteed tradeability. Minimum volume may be unaffordable. All metric targets are research gates, not expectations or guarantees.

## Reproducible test commands (from repository root)
```bash
dotnet run --project HarmonyBot-XAUUSD-V1/tests/HarmonyBot.XauUsd.Tests/HarmonyBot.XauUsd.Tests.csproj -c Release
dotnet build HarmonyBot-XAUUSD-V1/src/HarmonyBot.XauUsd.cBot/HarmonyBot.XauUsd.cBot.csproj -c Release -p:AlgoPublish=false
```

## Forward gates
- P1: genuine .NET tests and cTrader API compile on exact commit.
- P2: certify every ratio/pivot grammar against pinned original volume/page/edition; tests for positive and negative counterexamples.
- P3: broker adapter with live-query-only inspection, demo execution reconciliation, singleton lease, broker risk conversion, no unknown outcomes.
- P4: version-locked research-only tick data and DEV walk-forward, then independent OOS without tuning to burned V74 years.
- P5: four independent vetoes (Risk, Model Validation, Red Team, Data Governance). Until all pass, trading remains hard-disabled.

Rollback: delete the isolated feature branch only **after** explicit approval, or simply leave it idle. No original source files modified.

## Phase 1 extension
- `CausalPatternAssembler` receives confirmed pivots and emits research-only completed-D events after five alternating pivots. Broker orders remain impossible.
- `CommercialResearchGate` implements the new V1 annual threshold checklist but is not independent validation; synthetic test inputs never count as measured results.
- `WholeTradeAccounting` records partial-close cash flows as one completed lifecycle, maintaining the original initial-risk denominator.
