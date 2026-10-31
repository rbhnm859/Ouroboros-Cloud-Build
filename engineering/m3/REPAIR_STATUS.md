> Historical initial audit. Superseded by [FINAL_REPAIR_REPORT.md](FINAL_REPAIR_REPORT.md) after the supplied Director export identified the M3 pair. Statements below describe the earlier evidence-blocked state.

# M3 execution stability evidence — 2026-10-15

## Acceptance
- Overall M3 repair: BLOCKED (Director's two VERIFIED workflow identities and raw comparison are unavailable).
- GitHub connection: branch creation PASS under rbhnm859 engineering connection.
- Static prevention: local PASS (11 scoped contracts, 13 tests); remote CI receipt belongs in PR checks.
- Engineer recursion root cause and runtime correction: NOT_VERIFIED.
- Live cross-workflow exclusion/cancellation: NOT_VERIFIED; static isolation checks only.
- No existing workflow concurrency settings have been changed. No claim that M3 is fixed.

## Exact source provenance
Trading branch: harmonybot/v73-opportunity-universe
HEAD: 7225a8810f8e60eca590eb4ede0dacf54dfdfb82
Tree: 7480bc512ece05313c81666c7f06b45e7066b5b6
Configuration repository: rbhnm859/LibreChat-Railway-Config-Repos
Configuration main HEAD: 13f53b983281d3ee34d50f268d23e296df5d8ab3
Configuration repository was read only. Production deployment parity was not inspected.

The target tree (560 entries, not truncated), repository issue/PR listing, and local tracked text searches did not supply an identifiable M3 Director receipt. Prior conversation retrieval confirmed that VERIFIED had been reported without the two paths or exact diff; this is not a substitute for source evidence. The LibreChat web UI presented a login form, so raw private conversation/tool results could not be read.

## Workflows and resource ownership
The manifest records exact observed concurrency, triggers (including workflow_dispatch), permissions and job-level control fields for all ten V73/V74 workflows, plus the new guard. Baseline Git blob SHAs accompany each entry. The baseline is an observation, not proof that every policy is correct.

Two current examples inspected in full, NOT identified as the Director M3 pair:
1. .github/workflows/harmonybot-v74-r17-research.yml
   blob b73ac3fba2e8af7c63a0cffd09b7b740ae9a6730
   group harmonybot-v74-r17-research-${{ github.ref }}; cancel true
   permissions contents:read, actions:read
   jobs r17_build, r17_tick_universe, r17_research_gate
2. .github/workflows/harmonybot-v74-r18-semantic.yml
   blob 257f3e7420b3870351bf543676da79d50f98b3cc
   group harmonybot-v74-r18-semantic-${{ github.ref }}; cancel true
   permissions contents:read, actions:read
   jobs r18_build, r18_semantic_universe, r18_semantic_gate

These use separate hosted runners and run-scoped artifacts with separate R17/R18 names. Shared source filenames and broker secret names do not alone establish an exclusive runtime resource. Broker-side limits are unknown. Therefore their distinct groups were preserved, not forcibly unified.
The R18 oracle has cancel-in-progress:false intentionally in the observed baseline; the guard preserves that distinction.

Observed broader risk: the Full evidence workflow uses a repository-wide constant group (harmonybot-v73-v80-autonomous-evidence-g2), unlike the branch-qualified Rapid/Fast groups. This can couple manual runs across refs, but without Director intent/resource ownership evidence it is not designated M3 or altered here.

Two unrelated legacy YAML files fail local YAML parsing: .github/workflows/cdscalper-eurusd-v1-build-from-main.yml and .github/workflows/harmonybot-commercial-convergence-abc.yml. They are outside the scoped V73/V74 check and unchanged. This PR does not certify repository-wide YAML validity.

## Existing Actions read, never rerun
At trading HEAD:
- 37862672823 Full evidence: success
- 37862672820 V72 legacy: skipped
- 37862671803 R17 research: failure
- 37862671814 R18 semantics: failure
- 37862669905 legacy commercial convergence: failure
These conclusions do not establish M3 success or strategy acceptance. No research/backtest workflow was dispatched or rerun.

## Engineer independent diagnosis
Source evidence in configuration repository:
- hb-agent-provision.cjs blob 7d7f6f663d55b2be5a657c67ea9f890a9d161d21:
  ENGINEER_WRITES_FROZEN=true; ENGINEER_TOOLS contains read-only methods plus search_code/search_repositories; Engineer profile steps=14; desired recursion_limit=p.steps; Engineer subagents disabled.
- librechat-full-auto.yaml blob 6e7186e4c8be8934ba0b22b6277804740577534e:
  runtime deny includes remote GitHub writes/Actions trigger; deny overrides ask.
- tests/librechat-engineer-hitl-scope-v1.cjs blob 4ee8c2981f299e007952a9b324bbe2b9489885d0:
  asserts the read-only lock and write-tool exclusions.
- Dockerfile blob 24cf36075ec7a143348df62c540752bc38fdee31:
  native LibreChat framework is supplied by ghcr.io/danny-avila/librechat-dev@sha256:b278c620834c5653801030091072cad1974b47d0fc15a5009ed1a7d6e4c4f0d7.
  Runtime patch input is /app/packages/api/dist/index.cjs; resume integration uses /app/api/server/controllers/agents/resume.js.
The actual graph/tool execution loop is not source-controlled in the trading repository. Configuration access proved reads only; no configuration write or deployment was attempted.

Thus the explicit write freeze is a verified SOURCE-level reason Engineer cannot execute those write methods; it is not proof of the cause of the observed recursion failure. Work's separate connection successfully created this PR branch, so Engineer's lock must not be conflated with Work's rights.

The error 'Recursion limit of 12 reached' differs from the desired source profile value 14. Without the persisted per-run configuration, conversation ID, tool arguments/results and graph transitions, stale state, overridden runtime options, repeated search and framework step accounting remain competing hypotheses. No limit was raised and no paid model was called.

Runtime safeguards (identical-call deduplication; terminal permission/not-found errors; bounded transient retries; reserved final-summary budget) are NOT IMPLEMENTED in the live Engineer by this PR. Adding an unused helper to the trading repository would not fix the real runtime and is deliberately not represented as a repair.
Tests for live deduplication, terminal errors and exhausted runtime budget: NOT_RUN / BLOCKED on the missing runtime trace and source integration.

## Exact change scope and verification
Only new files:
- .github/workflows/harmonybot-m3-static-guard.yml: read-only contents permission, isolated PR/ref group, 5 minute hosted Linux job; runs no trading/model/database/deployment commands.
- engineering/m3/workflow-contract.json: observed contracts and baseline blob hashes.
- engineering/m3/workflow_guard.py: YAML 1.2-style boolean handling for 'on', duplicate-key rejection, exact control-field comparisons and case-insensitive shared-group detection.
- engineering/m3/test_workflow_guard.py: 13 baseline/negative tests.
- this report.

Reproduce:
```sh
python -m pip install PyYAML==6.0.2
python engineering/m3/workflow_guard.py
python -m unittest discover -s engineering/m3 -p 'test_*.py' -v
```

The guard detects changes against a reviewable baseline; it does not simulate GitHub's scheduler, establish a resource lock, or verify framework behavior. Contract updates must follow evidence review. Existing write permissions are preserved, not falsely described as minimized; only the new guard is contents:read.

## Single necessary evidence handoff
Provide one redacted export of the existing LibreChat M3 conversation, including Director's two full workflow paths, original comparison/tool results and Engineer's failed tool-call trace (arguments, outcomes, ordering, effective recursion limit). Do not include OAuth/PAT/password values. This unlocks correct pair selection and runtime root-cause diagnosis without rerunning models or research.
Do not merge this draft as completed M3 repair before those unresolved acceptance criteria are satisfied.

No V74 thresholds, strategies, risk logic, Agent IDs, Skills, Model Specs, Railway, MongoDB, OAuth/PAT or archived evidence were modified.

