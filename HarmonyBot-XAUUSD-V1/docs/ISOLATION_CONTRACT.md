# HarmonyBot XAUUSD V1 Cleanroom — isolation contract

## Identity and boundary

- Repository: `rbhnm859/Ouroboros-Cloud-Build` (shared ownership; independent repository not created).
- Independent cleanroom branch: `feat/hbxau-v1-cleanroom-20261106`.
- Source parent (already validated V1 prototype): `1ca32dbd51ecb84d35fee38b9bb5ddcf684af99d`.
- Frozen V74/R18 reference at isolation start: `harmonybot/v73-opportunity-universe` → `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806`.
- Prior V1 source/evidence branch retained unchanged: `feat/harmonybot-xauusd-core-v1-20261106`.
- Cleanroom uses a NEW COMPLETE GIT TREE containing only `HarmonyBot-XAUUSD-V1/` and its own workflow.
- **Commit ancestry is shared by Git design**; only checked-out branch tree, workflow definitions and release gates are separated. Repository-level Actions usage and repository settings remain shared. Do not claim independent repository-level isolation.

## Constitutional invariants

- V74 2021–2023 locked 3/3 gates and its Risk / Validation / Red Team / Data Governance vetoes remain unchanged and cannot be superseded by V1.
- No changes on V74/R18 branch; no cherry-picks from it without source review and provenance.
- No old V74/GitHub workflows, datasets, credentials, configurations or artifacts may be copied into the V1 cleanroom.
- V1 carries its OWN risk constitution (single XAUUSD exposure, maximum 5% active risk, max 10% drawdown, planned net RR >=2, no hedging, Martingale, DCA, stop widening, duplicate thesis, recovery).
- V1 annual OOS target: 500 independent complete trades, MeanR>=.90, PF_R>=3.30, WR>=60%, average winning positive R>=2.30, LCB95>0, each full year separately.
- No live trading, no deployment, no broker tokens, no paid tools and no cTrader backtests unless separately authorized for a later phase.
- C# read-only cBot must not import order APIs: the CI scans source and blocks them.

## Evidence custody / migration

- Source of selected files: `feat/harmonybot-xauusd-core-v1-20261106` at `1ca32dbd51ecb84d35fee38b9bb5ddcf684af99d`, NOT historical V74 source copied on this branch.
- Original CI receipt at source SHA: `42153957669` (54/54 tests, cTrader research .algo).
- New branch must independently pass all tests and publish a new artifact; do NOT claim a previous SHA proves new SHA.
- Keep immutable source/CI/artifact SHA256, transcript of any failed gate, and a clear rollback commit.
- Release promotion is blocked until all four independent vetoes pass.

## Rollback (non-destructive)

If the isolated commit fails, retain the branch and the failure logs, then make a new FIX commit on this branch. Do not force push or delete evidence. The V74 branch and original V1 evidence branch are independent recovery anchors. Moving or deleting refs is never automatic.

## Why this was needed

The prior V1 branch inherited 97 non-V1 workflow files and V74 source directories. Its safe core CI passed, but unrelated legacy workflows reported failures on each push. A clean Git tree ensures the checked-out V1 branch contains neither those workflows nor the V74 development files.

## Full separation later

A distinct repository `rbhnm859/HarmonyBot-XAUUSD-V1` is the preferred long-term boundary when a repository-create action is available. It is **not currently created**. GitHub Actions quota can still be shared at account level, even when code repositories are distinct.
