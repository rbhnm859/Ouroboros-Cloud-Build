# M3 final repair and independent Engineer diagnosis

## Decision and review scope

The supplied Director export identifies the exact R17/R18 pair at the unchanged formal HEAD. Full source and historical Actions independently confirm a shared-account overlap that the original separate workflow groups did not constrain. This patch closes that pair-specific overlap with a queued, non-canceling shared workflow lock. It does NOT prove that concurrency caused the cTrader Console crash.

Local scoped validation: PASS, 22 tests. Remote CI and its exact final head/run receipt are recorded in PR #28's description and Checks; they must be read rather than presumed successful from this document. Engineer runtime: NOT_VERIFIED, no runtime repair claimed. PR remains Draft and unmerged; formal branch was not updated. No trading/model job was run.

## 1. Source provenance

- Formal repository: rbhnm859/Ouroboros-Cloud-Build
- Formal branch: harmonybot/v73-opportunity-universe
- Latest checked formal HEAD: 7225a8810f8e60eca590eb4ede0dacf54dfdfb82
- Existing PR #28 head before this appended patch: e7eb4f7fa52430eb2a082789fa9eef20ff50b22a
- Existing branch reused: fix/m3-execution-stability-20261015
- Director attachment SHA256: 1a94c7e8a51a7d17905fee38a7483d4004d61593698060c34cd13ba3baa62db8
- Director export report message: 99aa5de5-f585-4a12-adfa-d09c46ea8c3d
- No private conversation body or hidden reasoning was published. See evidence-index.json for the minimal provenance index.

## 2. M3 exact workflow paths and original YAML

| Workflow | Original Git blob SHA | New Git blob SHA |
|---|---|---|
| .github/workflows/harmonybot-v74-r17-research.yml | b73ac3fba2e8af7c63a0cffd09b7b740ae9a6730 | 4d16b4b3245ae05645a35a0af3632dc10d83c774 |
| .github/workflows/harmonybot-v74-r18-semantic.yml | 257f3e7420b3870351bf543676da79d50f98b3cc | 19411287c04106fe64cf9f381d7ee972212e42f1 |

Full original YAML is preserved under baseline/ with matching filenames, copied byte-for-byte from the immutable formal HEAD. Full exact patch is in workflow-change.patch. The attachment's matching blob SHAs establish applicability; source middle sections were independently read in full rather than trusting the truncated Director excerpts.

Original R17:
```yaml
concurrency:
  group: harmonybot-v74-r17-research-${{ github.ref }}
  cancel-in-progress: true
```
Original R18:
```yaml
concurrency:
  group: harmonybot-v74-r18-semantic-${{ github.ref }}
  cancel-in-progress: true
```
Both become:
```yaml
concurrency:
  group: harmonybot-r17-r18-ctrader-research-account-v1
  cancel-in-progress: false
  queue: max
```

Only this concurrency block changes in the two research workflows. Triggers, workflow_dispatch, permissions, needs/if, runners, matrices, steps and evaluation code are identical to the original YAML after removing that block; an explicit golden test enforces this. Neither workflow calls a reusable workflow at job level.

## 3. Root-cause evidence, classification and bounds

A: Shared resource — both universe jobs bind exactly the same repository secret names CTRADER_CTID / CTRADER_ACCOUNT / CTRADER_PASSWORD, with no job environment override. Each has five windows and max-parallel:5. Their independent groups permit a combined upper bound of ten runner jobs using that account. Historical runs at the exact formal HEAD corroborate overlapping jobs:

- R17 run 37862671803: all five matrix jobs began 2026-10-09 00:02:50Z. Y2020 failed at 00:14:34Z; the last job ended 00:22:04Z.
- R18 run 37862671814: matrix jobs began 00:02:45Z–00:02:46Z; Y2017, Y2016 and Y2020 failed by 00:11:28Z; other windows continued until 00:21:38Z.
- Both builds passed; downstream gates were skipped following failures. No new runs of these pipelines were made.

This proves workflow/job overlap, not ten simultaneously authenticated CLI sessions or a broker-enforced concurrency ceiling. The crash's causal attribution remains NOT_VERIFIED. The repair is deliberate conservative isolation of the identified pair's shared external resource.

B: Independent work — build/evaluation/artifacts inside each protocol remain unchanged. The workflow-wide lock conservatively queues the entire second protocol, including its build, to avoid separate matrix-job locks replacing pending windows. Unrelated workflow group strings remain unchanged; no unrelated workflow is admitted into the new shared group.

C: Cancellation risk — simply copying one old group while retaining cancel-in-progress:true would let R17 cancel R18 (or vice versa). Merely setting false without queue:max could still replace a pending protocol. The patch therefore uses false plus queue:max, per current GitHub.com documentation. Queuing is bounded by the platform to 100 pending members; it is not infinite and does not guarantee dispatch-order execution.

The group intentionally omits ref: both protocols still reference the same secret tuple on manual runs of other refs. This lock is scoped to these two workflows, NOT a repository-wide lock for every cTrader consumer. Other legacy/Rapid/Full consumers are not silently changed.

Documentation checked:
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/reference/workflows-and-actions/contexts

## 4. Tests and free CI

- Preserve the original 13 regression responsibilities. The previous R17/R18 isolation assertion is intentionally updated: the evidenced pair now shares the account lock, while all unrelated pipelines must remain isolated.
- Add prevention of cross-protocol cancellation, pending replacement, ref-split locks and unrelated membership.
- Compare all non-concurrency fields of both real workflows against their immutable original full YAML.
- Add four negative/positive receipt-verifier tests; total local tests: 22 PASS.
- Guard: 11 scoped contracts PASS; duplicate YAML keys, semantic booleans, group/cancellation/trigger/permission/job changes remain checked.
- New synthetic GitHub job probes: three same-group producers plus one independent producer, using no secrets and no trading/model imports. The verifier requires all four receipts and non-overlapping shared-group work intervals. It deliberately does not require unrelated jobs to start in parallel, since runner allocation is not guaranteed.
- The synthetic group includes run_id, so it never acquires the actual account lock. Synthetic job-level scheduling is evidence of the GitHub scheduling policy, not a live test of the two broker workflows.
- Remove the guard's duplicate push trigger. The existing PR's synchronize trigger provides one corresponding CI run for the patch; workflow_dispatch remains available.
- All CI jobs have contents:read; checkout does not persist credentials. No Actions write, database, deployment or model credentials are requested.

Reproduce offline:
```sh
python -m pip install PyYAML==6.0.2
python engineering/m3/workflow_guard.py
python -m unittest discover -s engineering/m3 -p 'test_*.py' -v
```

## 5. Three old failures, not ignored

All three original run records are completed/failure at e7eb4f7fa52430eb2a082789fa9eef20ff50b22a, event push, with zero jobs. Their immutable source blockers were reproduced without rerunning them:

| Run | Exact workflow path | Reproduced source blocker |
|---|---|---|
| 38703364446 | .github/workflows/build-ctrader-cumulative-delta-scalper.yml | line 36 jobs.backtest.if directly references secrets, an unsupported context at job-level if; YAML itself parses |
| 38703363162 | .github/workflows/harmonybot-commercial-convergence-abc.yml | line 24 unquoted expression inside flow mapping: `with: { ref: ${{ env.BASE_COMMIT }} }`; YAML parser rejects it |
| 38703361961 | .github/workflows/cdscalper-eurusd-v1-build-from-main.yml | unindented heredoc content escapes the run block; YAML parser fails at line 56 (`- Status: success`) |

These are verified source-level load/validation blockers, consistent with the zero-job failed runs. Exact GitHub failure annotations could not be read: the connector rejected the check-suites endpoint as outside its allowed endpoints. Therefore the precise platform annotation wording is NOT_VERIFIED. A skipped trigger/job should not be equated with these source validation failures; neither concurrency cancellation nor runner permission failure is evidenced in these zero-job records.

Source hashes, line numbers and parser diagnostics are recorded in legacy-diagnostics.json. The three legacy workflows are unchanged; the request required diagnosis, not revival of unrelated old trading pipelines. They remain inherited failures and do not become PASS because the M3 guard passes.

## 6. Engineer independent evidence

The attachment contains 104 unique outer tool records; ten subagent calls have no output field and no completion/error status. Five historical outer search_code calls exist, but they do NOT expose the failed Engineer's internal execution. The recursion error appears in reported discussion, not in any recorded tool output. This corrects any earlier unsupported claim of an observed Engineer search loop.

Configuration source and deployment were matched read-only:
- Repository: rbhnm859/LibreChat-Railway-Config-Repos
- Deployment source commit: 13f53b983281d3ee34d50f268d23e296df5d8ab3
- Railway live deployment at inspection: aa8c1712-acb9-44c8-aeff-6e4e8310c069, SUCCESS, created 2026-10-15T06:58:55.271Z
- hb-agent-provision.cjs blob: 7d7f6f663d55b2be5a657c67ea9f890a9d161d21
- Source-managed profiles: Director 16, Quant 10, Engineer 14; Engineer and Quant cannot spawn subagents, Director may invoke those two. Bootstrap verifies recursion_limit against the desired profile before reporting success.
- Engineer writes are explicitly frozen; model-facing allowlist and runtime deny policy exclude remote write/trigger operations. Work's independent GitHub connection can write PR #28; that does not grant Engineer permission.

Source value 14 is NOT proof of the failed invocation's effective value. Bounded Railway log reads did not return the bootstrap profile receipt or a GraphRecursionError trace for the failed run. Startup logs contained MCP transport errors at a different time; these are not attributed to the recursion incident. No current persisted Agent document or per-run graph configuration was queried or changed.

The native execution graph is supplied by the pinned LibreChat runtime image, not the trading repository. Configuration Dockerfile pins ghcr.io/danny-avila/librechat-dev@sha256:b278c620834c5653801030091072cad1974b47d0fc15a5009ed1a7d6e4c4f0d7; native patch anchors include /app/packages/api/dist/index.cjs and /app/api/server/controllers/agents/resume.js. These anchors do not identify the exact inner graph loop or a 12-step override. The actual inner controller/override is therefore still NOT_VERIFIED.

No production runtime changes were made. Search deduplication, bounded retries, terminal permission-error handling, partial-result preservation and subagent error propagation are NOT claimed implemented in the live Engineer. No limit was increased. No disconnected helper was added and represented as a runtime fix.

## 7. Unverified items and Draft decision

- Engineer's effective per-run limit, source of 12 versus 14, inner tool sequence, graph/checkpoint state and error propagation: NOT_VERIFIED.
- Engineer deduplication/retry/budget/runtime regression: NOT_RUN, blocked by missing inner trace and runtime integration access.
- Causal link from broker concurrency to Console crash: NOT_VERIFIED.
- Live execution of the actual repaired R17/R18 pipelines: NOT_RUN, because it would execute prohibited backtests.
- Exact annotations on the three old failed runs: unavailable through current connector; verified source blockers are recorded separately.
- Other account-consuming workflows: outside the two-workflow repair scope, unchanged.

M3 source repair can be reviewed after the corresponding static/synthetic CI passes. The combined M3 + Engineer final-acceptance claim is not ready; keep PR #28 Draft and do not auto-merge. Known inherited legacy failures remain explicit.

The single necessary human evidence action is to export the ALREADY FAILED Engineer invocation's server-side trace/configuration (not another Director conversation export and not a new model run): effective recursionLimit, node/step sequence, sanitized tool arguments/results, final error/stack and completion status. If no trace was retained, say unavailable; historical root cause cannot be recovered from this attachment alone. Do not share PAT/OAuth/passwords, cookies, database URIs or private message bodies.

All changes are on the existing PR branch. Formal branch, strategy, V74/Alpha gates, Agent IDs, Skills/Model Specs, MongoDB, credentials, production deployment and archived research evidence are unchanged.
