# K6 Session-Range Sweep Rejection — Corrected IS Stop-Rule Result

## Status

**Classification: C — FAIL**

K6 completed the exact final pre-committed corrected IS run. The environment contract passed, the backtest completed, but the locked commercial strategy gate failed. K6 is not frozen and is not eligible for OOS, FULL, stress, robustness, Monte Carlo, or commercial Mobile/Cloud release.

## Evidence

- Branch: `cds-k6-session-sweep-rejection-final-research`
- Corrected validation run: `34521026064`
- Tested commit: `32052d1a590be70acff044b016c2e29c1cb74383`
- Corrected IS artifact: `CDScalper_K6_SESSION_SWEEP_REJECTION_CORRECTED_IS`
- Artifact ID: `10170039169`
- Artifact digest: `sha256:80bab21366be96de7d05a78c450ed67948501638e8f604930258493b4d7a073b`
- Build/package artifact ID: `10169661039`
- Build/package digest: `sha256:37a2fbad89ab1136a53982dfd86e67c75be22ff1777f3ad399dcb1352fe19a94`

## Corrected IS contract

- EURUSD M1
- Server tick data
- IS: 09/09/2024 00:00 through 08/09/2025 23:59
- Initial balance: USD 30
- Leverage: 1:500
- Fixed spread: 0.43 pip
- Commission: USD 35 per million USD volume
- Environment gate: PASS

## Exact K6 metrics

- Ending balance: USD 27.77
- ROI: **-7.43%** — FAIL
- Net profit: **-$2.23**
- Profit Factor: **0.65** — FAIL
- Trades: **19** — FAIL
- Wins / losses: 5 / 14
- Win rate: **26.32%**
- Post-cost average trade: **-$0.12** — FAIL
- Largest winning trade: $1.27
- Largest losing trade: **-$0.79** — PASS versus >= -$1.00
- Max equity DD: **12.15% / $3.84** — PASS versus <=15%
- Long PF / net: 0.33 / -$2.20
- Short PF / net: 0.99 / -$0.03
- Commissions: -$1.52

## Locked gate result

PASS: environment contract; DD <=15%; largest loss >= -$1.00.

FAIL: ROI >0; PF >=1.15; trades >=50; post-cost expectancy >0.

Overall: **FAIL**.

## Stop rule

Per `k6/PRECOMMIT_SPEC.md`, K6 was the final architecture candidate permitted to use this already-used IS window. Therefore:

- Do not create `k6/FREEZE_MANIFEST.json`.
- Do not run K6 OOS.
- Do not run K6 FULL.
- Do not run 1.25x/1.5x commercial stress promotion tests.
- Do not run robustness or Monte Carlo as promotion evidence.
- Do not create or label any K6 Mobile/Cloud `.algo` as Commercial / Store / Production / Release.
- Do not tune K6 or invent K7/K8 using this same IS window as discovery evidence.
- Preserve the exact K6 source, precommit, workflow and Actions artifacts for auditability.

The campaign must now be sealed as NOT COMMERCIAL-READY.
