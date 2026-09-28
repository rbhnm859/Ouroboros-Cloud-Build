# HarmonyBot V71 — Protected Champion Core / Incremental Alpha Rebase

Trusted parent: `1b670a0f43ba8ecaa637febfdacf605b1b146f01` (HarmonyBot V51).

## Root-cause finding
Repeated V71 regressions were path-dependent portfolio regressions, not simple indicator failures. MaxActiveBasket=1 means every admission change changes the future opportunity path: a new trade can consume the only slot and delete a later Champion trade. Historical "good cohorts" therefore cannot be promoted safely by turning them into new hard filters or broad admission rules.

## Architectural correction
V71 is rebuilt directly from the trusted V51 source. Expansion is a separate candidate book. With expansion disabled, the V71 core is required by CI to replay the original V51 reference on every burned calibration year. Expansion can execute only when:
1. no V51 core position, pending order or basket exists;
2. no active V51 core thesis exists;
3. the expansion thesis has canonical detector identity, live structure, completed-M1 confirmation and Net RR >= 2;
4. its out-of-fold expected Net-R lower-confidence estimate is positive.

Expansion cannot modify the V51 core admission, confirmation, Grid or exit pipeline.

## Cross-fit model
Burned 2021–2023 is used in three temporal folds: train two years, predict the third. Shadow outcomes are generated only after a candidate reaches PRZ, receives completed-M1 confirmation and has legal RR. Features are pre-entry only: harmonic geometry, PRZ, confidence, time symmetry, pivot quality, M1 confirmation, RR, regime score, efficiency, ATR fit, extension and H4/H1 compatibility. Family/route information is a shrinkage prior, never a hard blacklist.

For DEV, coefficients are frozen from all 2021–2023 data. Validation and Fresh remain locked.

## Variants
A — exact protected V51 core, expansion off.
B — protected core + cross-fit positive-LCB single-leg expansion at 1%.
C — B + post-selection non-blocking Fibonacci Grid at 1%.
D — C + adaptive expansion risk up to the 5% hard ceiling; research only and ineligible for V72 promotion.

## Promotion
Only B or C can promote. Core setup signatures must remain unchanged versus A. Candidate must exceed the immutable V51 floor, remain positive in all burned calibration years, pass cross-fit diagnostics, then pass all three fixed observed DEV windows. Only then may CI create the V72 branch.
