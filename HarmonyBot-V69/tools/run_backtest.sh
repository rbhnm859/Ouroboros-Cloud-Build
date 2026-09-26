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
                "HarmonyBot_V69_Family_Positive_Cohort_Commercial_Breakthrough.algo")
src=src.replace('--MicroCapitalThreshold=500 --MaxDrawdownPercent=10 --DailyLossLimitPercent=3',
                '--MicroCapitalThreshold=500 --MaxDrawdownPercent="${MAXDD:-10}" --DailyLossLimitPercent=3')
needle='--EnableFamilyNativeProjectedPrz="$PRJPRZ" --EnableDetectorTruthLedger="$DTRUTH"'
inject=needle + ' --EnableV69FamilyTradeContracts="${V69CONTRACTS:-false}" --EnableV69FamilyDetectorFrontier="${V69FRONTIER:-false}" --EnableV69FamilyNativeGrid="${V69FGRID:-false}" --EnableV69EvidenceRouteGuard="${V69EVIDENCE:-false}" --EnableV69ControlledExpansion="${V69EXPAND:-false}" --EnableV69FamilyGridAtlas="${V69ATLAS:-false}" --EnableV69PositiveThroughputExpansion="${V69POSITIVE:-false}" --EnableV69FamilyOpportunityScheduler="${V69SCHED:-false}"'
if needle not in src: raise SystemExit("V52 runner injection anchor missing")
src=src.replace(needle,inject)
flush='then DONE=1; break; fi'
if flush in src:
    src=src.replace(flush,'then DONE=1; sleep "${REPORT_FLUSH_GRACE_SECONDS:-8}"; break; fi',1)
pathlib.Path(sys.argv[2]).write_text(src)
PY
chmod +x "$TMP"
exec "$TMP"
