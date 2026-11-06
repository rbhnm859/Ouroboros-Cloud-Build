# HarmonyBot XAUUSD V1 — Isolation Charter

**Scope: development-only.** This charter applies to branch `feat/harmonybot-xauusd-core-v1-20261106`; it does not supersede any V74/R18 rule or grant authority to trade.

## Immutable anchor
| Property | Value |
|---|---|
| Repository | rbhnm859/Ouroboros-Cloud-Build |
| Original V74 branch | `harmonybot/v73-opportunity-universe` |
| V74 reference SHA at separation | `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806` |
| New V1 branch | `feat/harmonybot-xauusd-core-v1-20261106` |
| V1 allowed source prefix | `HarmonyBot-XAUUSD-V1/` |
| V1 allowed CI control-plane file | `.github/workflows/harmonybot-xauusd-v1-domain.yml` |
| Live trading | HARD DISABLED |
| Paid jobs and cTrader CLI backtests | NOT AUTHORIZED |
| LibreChat / Railway | FROZEN |

The V74 reference SHA is a **branch-fork baseline**. The official V74 branch may evolve independently; this V1 branch must not merge those changes automatically.

## Change custody and CI boundary
1. V1 commits may change **only** the allowed directory and its sole V1 CI YAML file. `tools/audit_isolation.py` verifies ancestry from the pinned V74 fork commit, computes a changed-path SHA256, denies any other changed path, checks project references and reviews CI permissions/credentials. Its negative cases are independently tested.
2. Do not edit any historical `HarmonyBot-V*`, `Fibonacci*`, `tmp/`, shared workflow, data snapshot or protected V74 gate in this branch. **Read-only inspection** of historical sources is allowed for engineering context; do not silently import their unverified outcomes or labels.
3. The CI must run only on V1 branch changes, without broker secrets, live account access, paid model calls, remote deployments, or use of production credentials. Its artifacts are named `HBXAU-V1-RESEARCH-ONLY-<SHA>`, with source, test and binary SHA256.
4. V74 and V1 must maintain independent source SHA, datasets, event ledgers, cost-model versions, timestamps, forecasts, research logs and governance decisions. Historical V74 2021–2023 burned OOF cannot become V1 tuning or model selection data through a new name.
5. The V1 project remains no-trade: zero order placement, cancellation, position modification and closing calls. Research-only risk sizing is NOT broker execution authority. Any promotion needs four distinct veto checks — Risk, Validation, Red Team, Data Governance — and separate explicit user approval.
6. No V1 pull request targeting the V74 branch, main or any production release should be merged without an independently reviewed cross-project migration and explicit approval. An `.algo` compile pass does not approve deployment.

## Limits to isolation
**Branch segregation is logical, not a separate GitHub security boundary.** Repository administrator permissions, GitHub Action billing, legacy workflows, settings, runner quotas and branch protections are shared. As checked on 2026-11-06, the two branch API records had `protected=false`; CI checks cannot stop an administrator from bypassing CI. The three inherited legacy workflows have been surfacing immediate failed workflow records on V1 pushes, despite being manual-only and having zero jobs; these records are not V1 tests and not evidence of a cTrader run. No changes to those inherited workflows are authorized by this isolation patch.

A separate Repository with independent Actions policy is an optional later migration, requiring a distinct migration/permission review, not an implicit step of this V1 work.

## Recovery
- If V1 isolation check fails: STOP, do not modify V74, identify offending paths and create a **new V1-only revert commit**. Do not force-push or delete protected history.
- If V1 CI fails: repair the smallest V1-only change; leave the V74 baseline unchanged.
- If proof is unavailable, report NOT VERIFIED and keep execution disabled.
- Safest rollback is to stop using the feature branch. Deleting the branch or deploying an artifact requires separate authorization.

## Evidence labels
PASS = observed evidence of a precisely stated check; FAIL = measured violation; BLOCKED = missing prerequisite/authority; NOT VERIFIED = insufficient evidence. A green CI job is not a commercial strategy Gate pass.
