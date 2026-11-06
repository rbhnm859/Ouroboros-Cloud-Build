# Codex Instructions — HarmonyBot V74 (staged integration candidate)

Repository: `rbhnm859/Ouroboros-Cloud-Build`.
V74 authoritative source branch: `harmonybot/v73-opportunity-universe`.
This integration branch was forked from `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806`; **fetch live HEAD before coding**. Do not overwrite prior historical work.

## Source and isolation
- This file governs V74 engineering on any branch containing it. The *new XAUUSD cBot* is another project track; never import its Grid feature or different performance gates into V74.
- New-cBot candidate policy is at `docs/codex/NEW_CBOT.md`; it does not grant permission to edit the V74 codebase for the new project.
- Existing LibreChat Production / Railway is frozen for this work. No modifications or added paid services.

## Trading invariants
- XAUUSD, one active basket, min net RR>=2, completed-bar/no lookahead, historical and tick data provenance.
- No hedging, Martingale, DCA, averaging losses, recovery entries, duplicated theses, stop widening, or fee/slippage omissions.
- V74 2021, 2022, 2023 burned OOF each independently require N>=250, MeanR>=0.90, PF_R>=3.30, WR>=70%, AvgRR>=2.30 and LCB95>0; all three years pass. Never weaken a gate, tune against these years or claim gains from old results.
- Risk/Validation/Red Team/Data Governance vetoes are individually fail-closed.

## Codex workflow
1. Start read-only: current source SHA, relevant C# manifests, workflow triggers, jobs/logs/artifacts. Do not re-run valid PASS evidence.
2. Produce explicit objective, exact base SHA and allowed paths; create a fresh reversible task branch before writing code.
3. Implement minimal changes; run only applicable available compilation/tests. cTrader CLI backtest requires actually configured tool, data and genuine run receipts.
4. For evidence: base SHA, changed files/diff, CI run, actual cTrader runtime result (or NOT VERIFIED), hashes of artifacts, rollback path and independent gate status.
5. Maximum two materially distinct root-cause fixes per failure signature; no infinite retry, no unauthorized spend, no secrets in logs, no force push, no auto merge, no production deployment and no live orders.
6. A plugin skill or ChatGPT text cannot create a Codex Cloud task. Report CODEX_STARTED only with actual task ID and status; otherwise CODEX_NOT_STARTED.

Apply supported Codex Cloud environment creation on web/desktop and publish it before invoking a cloud task. This repository configuration alone is not an environment deployment.
