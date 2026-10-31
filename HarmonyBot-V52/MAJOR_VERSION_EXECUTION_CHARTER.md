# HarmonyBot V52 — Harmonic Family Identity & Detection Graph Reconstruction Kernel

## Root-cause hypothesis
V51 Math improved quality to 58 independent baskets / 1.5y, Net +2101.66, PF 2.1097, DD 4.50%, yet its detector showed severe family suppression: AB=CD dominated while multiple standard families disappeared despite existing in V50 on the same DEV windows. V52 treats this as a detector/identity architecture problem before treating it as an economic problem.

## Frozen safety and Alpha controls
- V46 SCALE_CONTROL must reproduce 39 / +1721.72 / PF 2.1833 / DD 4.56%.
- V51_MATH_CONTROL must reproduce 58 / +2101.66 / PF 2.1097 / DD 4.50%.
- M15 confirmed-D thesis; M1 completed-bar execution; H4/H1 context.
- MinimumNetRR=2.0, whole-basket risk <=1%, server-side SL/TP, broker min-volume/min-distance/margin fail-closed.
- MaxActiveBasket=1, no hedging, no duplicate underlying setup execution, no Martingale/DCA/Recovery/Loss Averaging.
- Fibonacci staged entries remain 0/.236/.382/.618 with 3/7,2/7,1/7,1/7.
- V51 D-to-invalidation execution-corridor experiment remains disabled because it degraded performance.
- Fresh/OOS remains sealed until DEV + capital + freeze hashes pass.

## V52 causal reconstruction
1. Split UnderlyingGeometryId from FamilyHypothesisId. Multiple families may coexist as hypotheses on one geometry; only one underlying setup may execute.
2. Replace mandatory consecutive-five-pivot enumeration with a bounded pivot graph on M15, allowing at most two total skipped micro pivots.
3. Apply a per-family detection quota before global execution arbitration to prevent AB=CD supply from starving other families.
4. Move standard-family AB=CD compatibility from hard pre-detection deletion to a shadow mathematical component under the reconstructed detector; joint geometry still penalizes mismatch.
5. Replace the universal 0.45 ATR leg floor with preregistered family structural noise floors only in the reconstructed detector.
6. Add family-native terminal topology handling for Shark / 5-0 without changing the immutable controls.
7. FULL_V52 adds a multi-projection Fibonacci PRZ center using XA terminal, BC projection, AB=CD completion and observed D as confluence inputs. ATR is tolerance, not PRZ identity.
8. Every detector stage emits a Detector Truth Ledger. Silent disappearance is not acceptable evidence.

## Fixed DEV — exactly 12
- V46_SCALE_CONTROL × A/B/C
- V51_MATH_CONTROL × A/B/C
- FAMILY_IDENTITY_RECONSTRUCTION × A/B/C
- FULL_V52_COMMERCIAL × A/B/C

No threshold sweep and no Fresh use for tuning.

## Detector gate
Build must pass architecture, geometry and detector-contract tests. The source must expose all supported families, multi-label family identity, bounded-pivot graph, underlying execution dedupe, family quota and truth-ledger stages.

## Commercial DEV gate
Controls reproduce first. Candidate requires >=90 independent baskets / 1.5y, >=60/year, Net>=1800, PF>=2.0, Expectancy>=20, WR>=50%, MaxDD<=6%, A/B/C positive, unique setups=baskets, engineering/risk clean, aggregate marginal Net/Expectancy positive, marginal PF>=1.20 and marginal A/B/C Net each >=0.

Only after DEV pass: actual $100/$150/$200/$300/$500/$1000 -> immutable source/.algo hashes -> one untouched Fresh Alpha + one untouched Fresh $100.

Formal outcome is only COMMERCIAL_FREEZE_CANDIDATE_PASS or HOLD_WITH_EVIDENCE.

Execution registration: V52 detector-reconstruction workflow armed.
