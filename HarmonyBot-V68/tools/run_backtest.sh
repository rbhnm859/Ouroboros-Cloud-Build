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
                "HarmonyBot_V68_Harmonic_Family_Grid_Atlas_Positive_Throughput_Rebase.algo")
src=src.replace('--MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3',
                '--MicroCapitalThreshold=500 --MaxDrawdownPercent="${MAXDD:-10}" --DailyLossLimitPercent=3')
needle='--EnableFamilyNativeProjectedPrz="$PRJPRZ" --EnableDetectorTruthLedger="$DTRUTH"'
inject=needle + ' --EnableV68FamilyTradeContracts="${V68CONTRACTS:-false}" --EnableV68FamilyDetectorFrontier="${V68FRONTIER:-false}" --EnableV68FamilyNativeGrid="${V68FGRID:-false}" --EnableV68EvidenceRouteGuard="${V68EVIDENCE:-false}" --EnableV68ControlledExpansion="${V68EXPAND:-false}" --EnableV68FamilyGridAtlas="${V68ATLAS:-false}" --EnableV68PositiveThroughputExpansion="${V68POSITIVE:-false}" --EnableV68FamilyOpportunityScheduler="${V68SCHED:-false}"'
if needle not in src: raise SystemExit("V52 runner injection anchor missing")
src=src.replace(needle,inject)
flush='then DONE=1; break; fi'
if flush in src:
    src=src.replace(flush,'then DONE=1; sleep "${REPORT_FLUSH_GRACE_SECONDS:-8}"; break; fi',1)
pathlib.Path(sys.argv[2]).write_text(src)
PY
chmod +x "$TMP"
exec "$TMP"
