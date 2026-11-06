# HBXAU V1.3 — One-shot core refactor audit and acceptance

## Evidence source

Branch: `feat/hbxau-v1-cleanroom-20261106`.
Base/rollback anchor: `7566a6a682acb3e7a13d8baedbc985555287e16a`.
Previous successful CI: `42231525111` (62/62, compiled research .algo).
V74 official branch unchanged at preflight: `c3283e6f61741a5a9a3d2fc7ea31a066b64f7806`.
Current-commit CI must be independently verified; this text is NOT a run receipt.

## Deficiency analysis / implemented root fixes

| ID | Verified initial deficiency | Root-cause fix | Acceptance |
|---|---|---|---|
| A01 | One outside candle can be both strict pivot High and Low; the assembler rejects shared source index as if the market were out of order | Reject dual-center OHLC ambiguity without inventing intrabar order; record cumulative count in research log | New ambiguity and non-repeat tests |
| A02 | ResearchIntentLedger HashSet grows without upper bound; eviction would re-allow duplicate theses | Introduce capacity 8192 and fail-closed saturation; no evictions | Capacity, oversized ID, duplicate tests |
| A03 | 5% per-trade cap does not budget remaining loss room to 10% peak-equity drawdown | Maximum planned initial loss = min(5% equity, equity - 0.90*peak); all fees/slippage estimated; no guarantee against gaps | Cushion sizing and minimum-unit rejection tests |
| A04 | Risk Gate treats negative exposure counts as zero and non-enum direction as Sell | Explicit invalid count / invalid direction gates | Negative exposure, invalid direction tests |
| A05 | Trade prices can be off broker tick grid | Fail closed; do not silently round stop into risk increase | Off-grid test |
| A06 | Empty feature collection vacuously passes all-causal predicate | Explicit nonempty requirement | Empty and single-valid feature tests |
| A07 | Harmonic match checks AFTER D but has no independent XABC-only PRZ construction | New `CausalPrzProjector` with XABC-only typed API, current research BCD/XAD/CDAB projected range intersection, legal tick clipping | Positive, negative, mirror, no D and causal-timestamp tests |
| A08 | Price ratio match could be mislabeled a pre-D signal even if C not confirmed until after D started | Explicit `PrzProjectedBeforeD` metadata, trading remains disabled | Retrospective-vs-causal tests |
| A09 | CI status document still showed 54-case source while last accepted evidence was 62 | Update snapshot of prior verified source and make current-HEAD status explicitly CI-derived | GitHub SHA/Run must be inspected |

## Unresolved by code changes (hard BLOCKED / NOT VERIFIED)

- **Primary source**: provisional V71-derived ratio envelopes for Gartley/Bat/AlternateBat/Butterfly/Crab/DeepCrab/ABCD/AlternateABCD are NOT independent Carney-certified rules. Shark and FiveZero remain special structures NOT IMPLEMENTED. Source-verified canonical grammars must precede actual promotion.
- **cTrader behavior**: OnBar semantics source-backed, but real FXPro Runtime, weekend tick timestamp, multi-timeframe closed-bar parity, symbol suffix and cTrader broker metadata NOT VERIFIED.
- **Execution**: broker order API intentionally absent; persistent cross-instance execution lease, broker reconciliation, margin/commission and FX currency conversions not implemented. No demo orders.
- **Quant**: multi-year native Bid/Ask tick dataset unavailable; annual 500 / MeanR .9 / PF_R 3.3 / WR .6 / AvgWinR 2.3 / LCB95 >0 NOT VERIFIED. 12% monthly compound never a promise.
- **Regime & backtests**: P3/P7/P8/P9 remain NOT VERIFIED/BLOCKED. Backtest cannot be inferred from synthetic unit data.
- **Protective stops**: planned max-risk DD cushion does not bound extreme gap loss. Peak-equity drawdown max 10% and active risk 5% are policy limits, not a mathematical guarantee.

## Required CI scope

- Single cleanroom branch (no V74 CI); only one new commit for this grouped refactor.
- Existing 62 cases must remain PASS; add >= 20 causality/risk/geometry adversarial tests; compile research cBot; static no-order API scan; source and artifact SHA256.
- Rollback: parent `7566a6a682acb3e7a13d8baedbc985555287e16a` retained, forward fix only; no force push or delete.
- The V74 2021–2023 3/3 locked Gate and four independent vetoes remain UNTOUCHED.
- Never declare V1 "finished" without actual broker runtime, canonical sources, independent OOS and promotion authorization.

## Independent veto evaluation

Risk: no observed new unsafe trade method; live risk unverified.
Validation: no source certification or OOS; promotion BLOCKED.
Red Team: added adversarial tests, runtime unavailable; promotion BLOCKED.
Data Governance: tested isolated source and provenance, OOS custody not available; promotion BLOCKED.

Official cTrader bar-event contract: https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-bar-events/
Official HarmonicTrader Shark and 5-0 distinction:
https://harmonictrader.com/harmonic-patterns/shark-pattern/
https://harmonictrader.com/harmonic-patterns/5-0/
