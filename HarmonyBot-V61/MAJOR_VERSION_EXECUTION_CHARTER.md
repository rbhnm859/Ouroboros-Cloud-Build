# HarmonyBot V61 — Champion-Core Fibonacci Grid Commercial Rebase
V61 is rebased from immutable V51 SHA `1b670a0f43ba8ecaa637febfdacf605b1b146f01`. Variant A must dynamically reproduce the V51 historical champion before promotion.

Fixed variants: V61_V51_EXACT_CONTROL; V61_CHAMPION_FIB_GRID; V61_GRID_REGIME_SURVIVAL; V61_COMMERCIAL_MAX.
Grid: Trend 0/.236/.382/.618 at .40/.30/.20/.10; Exhaustion 0/.236 at .65/.35; Transition 0/.236/.382 at .50/.30/.20. Whole-basket stressed risk remains <=1%; runner reuses an existing leg and cannot add volume/risk. Standalone AB=CD Capital is OFF outside exact V51 control.

Calibration: 2021-2023 burned. DEV4: 2024H2/2025H1/2025H2. Validation: untouched 2026Q1/Q2 at spread 1.0/1.25/1.5, no tuning. Fresh: 2020H1 exactly once after Freeze.

V51 reproduction gate: 58 baskets, Net 2101.66, PF 2.1096878432, Expectancy 36.2355, WR 53.4483%, Max DD 4.49784%. B-A requires Delta Net>0, PF/expectancy non-decreasing, P95 winner R>0, max winner not worse, >=2/3 positive Delta Net windows, and zero execution/risk/margin violations. Gates are fail-closed.
