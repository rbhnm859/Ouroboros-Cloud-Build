# HarmonyBot V71 — Minimal-Gate Signal Preservation Rebase

This iteration removes stacked Alpha-supply vetoes while retaining canonical harmonic identity, structural validity, minimum Net RR, session/spread legality, MaxActiveBasket=1, and whole-basket risk/margin protection.

All 12 canonical harmonic families remain eligible for the candidate pool after a common global geometry/PRZ integrity check. H4/H1 conflict, regime, confirmation strength, family history, age and spread quality are ranking inputs rather than admission vetoes.

Execution order: canonical detection -> minimal integrity -> soft contextual route -> PRZ touch -> minimal completed-M1 execution confirmation -> Alpha-only RR -> signal-preserving arbitration -> winner frozen -> Fibonacci Grid -> risk -> execution.

Grid is non-blocking. If the family-native Grid cannot be built legally, the already-selected harmonic winner falls back to one legal L0 market leg instead of losing the signal.

Variants:
- A: exact V70 truth control.
- B: prior Final Structural Rebase control.
- C: minimal-gate all-family, signal-preserving queue/arbitration, forced single-leg, 1% risk.
- D: C plus non-blocking post-selection family-native Fibonacci Grid, 1% risk.
- E: D plus adaptive risk up to 5%, research-only and ineligible for V72 promotion.

Supply capacity for C/D/E: PortfolioMaxCandidates 24, FamilyDetectionQuota 8, Candidate TTL 16 M15 bars, persistent serial queueing. These are capacity controls, not outcome-derived filters.

Only C or D may promote, and only if they beat the immutable V51 floor, remain positive in all burned 2021/2022/2023 calibration windows, reach at least 60 trades/year, DD <=4.49784%, and remain engineering/risk/identity clean. Validation and Fresh remain locked.
