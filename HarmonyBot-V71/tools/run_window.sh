#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
EXPSHADOW=false; EXPEXEC=false; EXPGRID=false; EXPADAPRISK=false; EXPRISK=1.0
case "$VAR" in
 SHADOW_PREPASS) EXPSHADOW=true;;
 A_V51_PROTECTED_CORE) ;;
 B_PROTECTED_XFIT_SINGLE) EXPSHADOW=true; EXPEXEC=true;;
 C_PROTECTED_XFIT_GRID) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true;;
 D_PROTECTED_XFIT_GRID_RISK5) EXPSHADOW=true; EXPEXEC=true; EXPGRID=true; EXPADAPRISK=true; EXPRISK=5.0;;
 *) echo "unknown V71 variant $VAR"; exit 31;;
esac

C="$PWD/control"; W="$C/HarmonyBot-V71/window-$VAR-$WIN"; O="$C/HarmonyBot-V71/output-$VAR-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V71/dist/HarmonyBot_V71_Protected_Champion_Core_Incremental_Alpha.algo" "$W/seal/algo/"
N="V71-$VAR-$WIN-B10000"

EDGE_MODEL_SPEC=""; EDGE_PRIOR_SPEC=""; EDGE_LCB_MARGIN=0; EDGE_MODEL_ID="NONE"
if [ "$EXPEXEC" = true ]; then
 MODEL_DIR="${MODEL_DIR:-$C/HarmonyBot-V71/model}"
 MF="$MODEL_DIR/$WIN.json"
 case "$WIN" in H2024H2|H2025H1|H2025H2) MF="$MODEL_DIR/FULL.json";; esac
 test -s "$MF"
 eval "$(python3 - "$MF" <<'PY'
import json,shlex,sys
m=json.load(open(sys.argv[1]))
for k,v in [("EDGE_MODEL_SPEC",m["spec"]),("EDGE_PRIOR_SPEC",m["family_prior_spec"]),("EDGE_LCB_MARGIN",str(m["lcb_margin"])),("EDGE_MODEL_ID",m["model_id"])]:
 print(k+"="+shlex.quote(v))
PY
 )"
fi

(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  EXPSHADOW="$EXPSHADOW" EXPEXEC="$EXPEXEC" EXPGRID="$EXPGRID" EXPADAPRISK="$EXPADAPRISK" EXPRISK="$EXPRISK"  EDGE_MODEL_SPEC="$EDGE_MODEL_SPEC" EDGE_PRIOR_SPEC="$EDGE_PRIOR_SPEC" EDGE_LCB_MARGIN="$EDGE_LCB_MARGIN" EDGE_MODEL_ID="$EDGE_MODEL_ID"  BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V71/tools/run_backtest.sh"
)
test -s "$W/seal/logs/$N.log"; test -s "$W/seal/reports/$N.json"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"; cp "$W/seal/reports/$N.json" "$O/raw-report.json"
python3 "$C/HarmonyBot-V71/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/$VAR-$WIN.json" --window "$WIN" --variant "$VAR" --years "$YEARS" --balance 10000
