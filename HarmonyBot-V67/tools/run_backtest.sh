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
                "HarmonyBot_V67_Family_Native_Throughput_Grid_Commercial_Rebase.algo")
src=src.replace('--MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3',
                '--MicroCapitalThreshold=500 --MaxDrawdownPercent="${MAXDD:-10}" --DailyLossLimitPercent=3')
needle='--EnableFamilyNativeProjectedPrz="$PRJPRZ" --EnableDetectorTruthLedger="$DTRUTH"'
inject=needle + ' --EnableV67FamilyTradeContracts="${V67CONTRACTS:-false}" --EnableV67FamilyDetectorFrontier="${V67FRONTIER:-false}" --EnableV67FamilyNativeGrid="${V67FGRID:-false}" --EnableV67EvidenceRouteGuard="${V67EVIDENCE:-false}" --EnableV67ControlledExpansion="${V67EXPAND:-false}"'
if needle not in src: raise SystemExit("V52 runner injection anchor missing")
src=src.replace(needle,inject)
# The old V52 runner stopped Docker immediately when report JSON became readable.
# Keep broker-history as authoritative and allow stdout telemetry to flush for attribution/right-tail evidence.
flush='then DONE=1; break; fi'
if flush in src:
    src=src.replace(flush,'then DONE=1; sleep "${REPORT_FLUSH_GRACE_SECONDS:-8}"; break; fi',1)
pathlib.Path(sys.argv[2]).write_text(src)
PY
chmod +x "$TMP"
exec "$TMP"
