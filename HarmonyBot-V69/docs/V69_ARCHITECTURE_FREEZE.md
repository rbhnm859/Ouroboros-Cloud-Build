# HarmonyBot V69 — 12-Family Equal Visibility & Shadow Alpha Census

## Purpose
V69 tests the hypothesis that low capital-trade counts in some harmonic families may be caused by detector, admission, conversion, or portfolio starvation rather than genuine market scarcity.

V69 does **not** impose equal capital allocation or minimum per-family trade quotas. Every family receives equal observability, not equal risk.

## Frozen families
Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Deep Gartley, Rat, Cypher, Shark, 5-0, AB=CD.

## Architecture
For every family V69 records:
Topology attempts -> geometry matches -> age rejects -> selected hypotheses -> candidates -> quality pass/reject -> route pass/reject -> PRZ touch -> confirmation pass -> grid planned -> basket planned -> executed -> closed.

Every terminal candidate also records one terminal reason. Research-only shadow observations are created for terminal candidates only when the same canonical risk/target geometry remains legal and Minimum Net RR >= 2.0.

Shadow outcomes use only future completed M1 bars after the terminal decision. They are prohibited from admission, routing, ranking, grid construction, execution, risk, or scheduler decisions.

## Causal variants
- A_V68_TRUTH_CONTROL: canonical V68 truth control, V69 visibility OFF, V69 shadow OFF.
- B_EQUAL_VISIBILITY_SHADOW: identical capital path, V69 visibility ON, V69 shadow ON.

B must be execution-equivalent to A across all six DEV windows before any census inference is accepted.

## Starvation taxonomy
- Detector / genuine scarcity review: too few canonical geometry matches to infer downstream starvation.
- Admission starvation: geometry exists but quality/route rejection dominates.
- Conversion starvation: candidates survive admission but rarely progress to execution.
- Downstream conversion starvation: selected opportunities exist but execution conversion remains very low.
- No severe starvation: material supply reaches capital execution.

Classification is diagnostic, not a capital rule.

## Governance
DEV: 2021, 2022, 2023, 2024H2, 2025H1, 2025H2.
Validation 2026 remains locked.
Fresh 2020H1 remains locked.
No family may receive capital merely to satisfy a quota.
No shadow result may feed live decisions.
Any future expansion requires a new preregistered causal version.
