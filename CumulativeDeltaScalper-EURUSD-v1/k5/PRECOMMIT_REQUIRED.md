# K5 Research Gate — PRECOMMIT REQUIRED

This branch exists only as a placeholder for a future, separately pre-committed architecture hypothesis after K4 was formally classified C-FAIL.

No K5 source, preset, backtest workflow, optimization, OOS, FULL, stress, robustness, Monte Carlo, or commercial `.algo` is valid until a new architecture specification is committed **before** the first corrected IS run.

The precommit must fix, before testing:
- primary entry event / market-structure hypothesis;
- confirmation hierarchy;
- completed-bar / no-lookahead rules;
- session and weekday rules;
- SL/TP and maximum holding logic;
- single-position and no-hedging enforcement;
- volume normalization and broker stop-distance handling;
- realistic cost model: EURUSD M1, server ticks, spread 0.43 pip, commission 35 USD per million USD volume, initial balance USD 30, leverage 1:500;
- IS window and all hard gates;
- Freeze rule;
- OOS/FULL/stress/robustness/Monte Carlo sequence;
- stop rule;
- prohibited post-hoc tuning actions.

K4 results must not be used to choose K5 parameters or direction-specific settings. K5 must be a genuinely new hypothesis, not a renamed K4 parameter adjustment.

Until a complete precommit specification exists, this branch is **RESEARCH PLACEHOLDER ONLY** and must not produce a Commercial / Store / Production / Release artifact.
