# K5 Impulse-Pullback-Reclaim — Corrected IS Stop-Rule Result

## Status

**Classification: C — FAIL**

K5 completed the exact pre-committed corrected IS run, but the commercial IS gate failed. In accordance with the locked commercial validation protocol, K5 is **not frozen**, **not promoted to OOS**, and **not eligible for FULL / stress / robustness / Monte Carlo / commercial Mobile/Cloud release**.

## Evidence source

- Branch: `cds-k5-impulse-pullback-reclaim-research`
- Corrected validation run: `34495064771`
- Tested source/workflow commit: `ab80b09b7b5be241ac4ffe0f29477cf07d1ac2bb`
- Commit message: `Enforce symbol-wide single-position no-hedge guard`
- Corrected IS evidence artifact: `CDScalper_K5_IMPULSE_PULLBACK_RECLAIM_CORRECTED_IS`
- Corrected IS artifact ID: `10159930988`
- Corrected IS artifact digest: `sha256:e545f50b85c79df7aaefd0f276d1c335482cf862c6f3ea8d0c271587cb954d90`
- Build/package artifact: `CDScalper_K5_IMPULSE_PULLBACK_RECLAIM_IS_PACKAGE`
- Build/package artifact ID: `10159441339`
- Build/package digest: `sha256:bfe32fd6956a56d81d8bba538408ccea9146d8b091cdcb0b39fc4f5914ed4669`

## Corrected test contract

- EURUSD M1
- Initial balance: USD 30
- Expected leverage: 1:500
- Historical mode: server tick data
- IS: 09/09/2024 00:00 through 08/09/2025 23:59
- Fixed spread: 0.43 pip
- Commission: 35 USD per million USD volume
- Exact precommitted K5 architecture retained
- Symbol-wide single-position / no-hedge guard retained

## Commercial IS gate

The locked gate requires all of the following:

- ROI > 0
- Profit Factor >= 1.15
- Trades >= 50
- Max equity drawdown <= 15%
- Largest losing trade >= -$1.00
- Post-cost average trade / expectancy > 0
- Correct environment contract must pass in full

GitHub Actions job `corrected_is` completed the exact corrected IS backtest successfully, then failed specifically at **Apply corrected K5 IS gate**. Therefore the overall K5 commercial IS gate is failed.

## Engineering checks that passed before the strategy gate

The audit/build job passed all required preconditions before corrected IS execution, including:

- K4 stop-rule enforcement
- K5 precommit ordering
- Fixed K5 architecture invariants
- `AccessRights.None`
- net6.0 target
- M5/M15 closed-bar context usage
- broker stop-distance handling
- risk-based normalized volume handling
- leverage/account guard logic
- single-position protection
- absence of uncommitted RSI/MACD/Bollinger/Fibonacci/ML modules
- absence of Grid/Martingale/DCA/Recovery/Loss Averaging/Hedging logic
- exact K5 `.algo` build

Therefore this run is treated as a **strategy/commercial gate failure**, not a compile failure.

## Protocol decision

Because the first corrected IS promotion gate failed:

- Do **not** create `k5/FREEZE_MANIFEST.json`.
- Do **not** run K5 OOS.
- Do **not** run K5 FULL 2Y as promotion evidence.
- Do **not** run K5 1.25x / 1.5x stress as promotion evidence.
- Do **not** run K5 robustness / walk-forward as promotion evidence.
- Do **not** run K5 Monte Carlo as promotion evidence.
- Do **not** label the K5 `.algo` Commercial / Store / Production / Release.
- Do **not** retune K5 against this IS window or any reserved OOS window.
- Preserve K5 source, precommit spec, workflow, reports and Action artifacts unchanged for auditability.

## Allowed next commercial step

K5 is closed as a failed hypothesis. The only allowed next commercial-development action is to define a **new, separately pre-committed architecture hypothesis** before viewing any new validation result. The new candidate must:

1. document the economic/market hypothesis before source implementation;
2. lock its architecture, parameters, validation window and hard gates before the first corrected IS run;
3. use the same realistic-cost commercial harness;
4. undergo exactly one first corrected IS promotion decision;
5. stop immediately as C-FAIL if any hard IS gate fails;
6. proceed to Freeze -> OOS -> FULL -> 1.25x/1.5x stress -> robustness -> Monte Carlo -> Mobile/Cloud `.algo` only if every preceding gate passes.

No iterative same-window tuning is permitted.
