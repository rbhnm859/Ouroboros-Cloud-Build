#!/usr/bin/env bash
set -euo pipefail
ROOT="${GITHUB_WORKSPACE:-$PWD}"
BASE="$ROOT/control/HarmonyBot-V52/tools/run_backtest.sh"
test -s "$BASE"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 - "$BASE" "$TMP" <<'PY'
import pathlib,sys
src=pathlib.Path(sys.argv[1]).read_text()
src=src.replace("HarmonyBot_V52_Family_Identity_Detection_Graph_Reconstruction_RC.algo",
                "HarmonyBot_V71_Selective_Causal_Alpha_Reconstruction_Grid_Amplifier.algo")
src=src.replace('--BasketRiskPercent=1.0','--BasketRiskPercent="${RISKCAP:-1.0}"')
src=src.replace('--MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3',
                '--MicroCapitalThreshold=500 --MaxDrawdownPercent="${MAXDD:-10}" --DailyLossLimitPercent=3')
needle='--EnableFamilyNativeProjectedPrz="$PRJPRZ" --EnableDetectorTruthLedger="$DTRUTH"'
inject=needle + ' --EnableV67FamilyTradeContracts="${V67CONTRACTS:-false}" --EnableV67FamilyDetectorFrontier="${V67FRONTIER:-false}" --EnableV67FamilyNativeGrid="${V67FGRID:-false}" --EnableV67EvidenceRouteGuard="${V67EVIDENCE:-false}" --EnableV67ControlledExpansion="${V67EXPAND:-false}" --EnableV68CanonicalIdentity="${V68IDENT:-true}" --EnableV68CanonicalIdentityFailClosed="${V68IDFAIL:-false}" --EnableV68EvidencePreservingAdmission="${V68PRESERVE:-false}" --EnableV68FamilyExpansion="${V68EXPAND:-false}" --EnableV68GridChallenger="${V68GRID:-false}" --EnableV69EqualFamilyVisibility="${V69VIS:-true}" --EnableV69ShadowAlphaCensus="${V69SHADOW:-true}" --V69ShadowHorizonM1Bars="${V69HORIZON:-180}" --EnableV70HardVetoRationalization="${V70HARD:-false}" --EnableV70FamilyRouteAdmission="${V70FAM:-false}" --EnableV70OpportunityCostArbitration="${V70ARB:-false}" --EnableV70ProtectedPositiveLanes="${V70PROTECT:-true}" --V70TimingMaxWaitM1Bars="${V70WAIT:-12}" --EnableV71SelectiveLaneSuppression="${V71SUPPRESS:-false}" --EnableV71SelectiveRecall="${V71RECALL:-false}" --EnableV71FamilyNativeGridAmplifier="${V71GRID:-false}" --EnableV71NoBackfillReservation="${V71NOBACKFILL:-false}" --EnableV71RegimeSurvival="${V71REGIME:-false}" --EnableV71SelectiveBackfill="${V71BACKFILL:-false}" --EnableV71AdaptiveRiskScaling="${V71ADAPRISK:-false}"'
if needle not in src: raise SystemExit("V52 runner injection anchor missing")
src=src.replace(needle,inject)
flush='then DONE=1; break; fi'
if flush in src:
    src=src.replace(flush,'then DONE=1; sleep "${REPORT_FLUSH_GRACE_SECONDS:-8}"; break; fi',1)
pathlib.Path(sys.argv[2]).write_text(src)
PY
chmod +x "$TMP"
exec "$TMP"
