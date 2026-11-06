# V1 baseline and evidence custody — observed before isolation patch

Snapshot: 2026-11-06, readonly GitHub branch/run API and prior complete CI.

| Evidence | Observed state |
|---|---|
| Official V74 branch | `harmonybot/v73-opportunity-universe` at `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806` |
| V1 existing branch | `feat/harmonybot-xauusd-core-v1-20261106` at `1ca32dbd51ecb84d35fee38b9bb5ddcf684af99d` before this isolation change |
| V1 C# safety tests | 54/54 PASS, Run [42153957669](https://github.com/rbhnm859/Ouroboros-Cloud-Build/actions/runs/42153957669) |
| V1 read-only .algo build | PASS, same run `42153957669` |
| V1 artifact custody | ID `13474002047`, binary and source hashes retained |
| V1 trading | HARD_DISABLED (no order API in research adapter, no demo/live runtime verified) |
| V74 R18 metric gate | FAIL / research-only; V1 does not inherit its result |
| V1 harmonic source verification | NOT VERIFIED, 10 profiles currently research-only |
| Broker-specific sizing and margin | NOT VERIFIED; no broker data tested |
| V1 multi-year tick/OOS | NOT RUN |
| V1 live deployment | NOT AUTHORIZED |
| Branch protection | NOT VERIFIED as enforced; API showed `protected=false` |
| Three unrelated historical workflows | Failed workflow records on V1 pushes, no jobs; not a V1 CI gate |

### Scope of this patch
Introduce one machine-enforced CI diff scope, negative tests and permanently versioned engineering/segregation plan. It does not alter original V74 files, change existing older workflow triggers, dispatch protected gates or enable trading. Exact newer commit/run/artifact identifiers must be obtained from CI after writing.
