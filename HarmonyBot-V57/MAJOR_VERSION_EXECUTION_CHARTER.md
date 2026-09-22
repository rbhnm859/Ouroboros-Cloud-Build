# HarmonyBot V57 — Regime-Calibrated Universal Harmonic Family Portfolio Engine

## Architecture authority
V57 is a clean-room major rebuild from the tested V51 execution/risk kernel. V52 contributes only family identity reconstruction, bounded pivot graph, multi-label detection and family quota. V53-V56 contribute evidence-governance lessons only; V56 hand-authored Expected-R and Grid V4 are explicitly not inherited.

## Role allocation
Harmonic/Fibonacci Quant 14%; Math/Geometry/Statistics/Optimization 13%; Commercial System Architecture 11%; Model Validation 10% + veto; Experimental Design 9%; Backtest Forensics 8%; Execution 8%; Risk 8% + veto; Red Team 6% + veto; Data Governance 5% + veto; Portfolio Opportunity Cost 4%; GitHub/CI 2%; SRE 1%; Commercial QA 1%. Veto rights are absolute.

## Non-negotiable safety
- FxPro cTrader / XAUUSD / UTC.
- M15 primary harmonic detection; M1 execution evidence; H1/H4 context.
- MaxActiveBasket=1 for real broker capital.
- Whole-basket risk <=1%.
- MinimumNetRR=2.0.
- No hedging, Martingale, DCA, Recovery, Loss Averaging.
- Completed bars / no lookahead / broker min-volume / margin / SL-TP fail-closed.
- Projected-D never becomes primary alpha.
- Legacy Fibonacci Grid remains the only live Grid control in V57. No new Grid optimizer is promoted in this version.

## Universal family liberation
All 12 families get independent research books:
Gartley, Bat, Alt Bat, Butterfly, Crab, Deep Crab, Deep Gartley, Rat, Cypher, Shark, 5-0, AB=CD.
A family book retains its hypotheses independently of the shared live-capital slot.

## Virtual Parallel Execution
Every candidate that reaches confirmed execution evidence and a legal RR>=2 target receives a virtual L0 shadow trade. Shadow trades run in parallel and are never blocked by MaxActiveBasket=1. They record family, route, regime, MFE, MAE, realized R, holding time and exit reason. This is the primary evidence source for family opportunity economics.

## AB=CD policy
AB=CD remains fully visible as a harmonic primitive and research family. Standalone AB=CD has no real capital authority by default. It can only be enabled in a later preregistered experiment after a calibrated cell demonstrates positive lower-bound expectancy.

## Calibration
Burned historical windows may build a calibration manifest. For each Pattern × Route × Regime cell:
- observed shadow R is aggregated;
- cell mean is hierarchically shrunk toward family and global means;
- uncertainty is penalized;
- only cells with positive conservative lower-bound R and minimum sample support enter the capital manifest.
Capital execution never uses a hand-authored probability or indicator score.

## Regime buckets
TRANSITION, EXHAUSTION_EXTENSION, TREND_EXPANSION, TREND_PULLBACK, VOL_COMPRESSION, MEAN_REVERTING_RANGE, BALANCED.

## Two-stage portfolio arbitration
1. Within-family ranking: at most one representative per family may enter cross-family capital arbitration.
2. Cross-family ranking: compare calibrated lower-bound R per expected slot-hour, then existing V51 rank as a tiebreaker.
This prevents AB=CD population dominance while preserving MaxActiveBasket=1.

## Data plan
Calibration: burned 2021-2023 windows, shadow-only.
DEV3: burned 2024-H2 / 2025-H1 / 2025-H2, used only for development evidence.
Untouched promotion validation: 2026-H1, split into VA/VB and cost-stressed at spread 1.0/1.25/1.5.
Fresh remains untouched until validation + capital + freeze all pass.

## Promotion gate
DEV3 live candidate must meet:
- >=60 trades/year annualized,
- Net >0 and target commercial Net trajectory,
- PF>=2.0,
- Expectancy>=20,
- WR>=50%,
- DD<=6%,
- every DEV3 window positive,
- unique setups=baskets,
- engineering/risk clean,
- added calibrated cohort Net>0,
- GP-2*GL>=0,
- no family population can contribute more than one simultaneous representative,
- shadow coverage exists for all detected families that reach confirmation.
Validation is fail-closed and cannot tune the manifest.
