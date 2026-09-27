#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
case "$VAR" in
 A_V69_CONTROL)
   V70HARD=false; V70FAM=false; V70ARB=false;;
 B_HARD_VETO_RATIONALIZED)
   V70HARD=true; V70FAM=false; V70ARB=false;;
 C_FAMILY_ROUTE_RECONSTRUCTED)
   V70HARD=true; V70FAM=true; V70ARB=false;;
 D_OPPORTUNITY_COST)
   V70HARD=true; V70FAM=true; V70ARB=true;;
 *) echo "unknown V70 variant $VAR"; exit 31;;
esac

C="$PWD/control"
W="$C/HarmonyBot-V70/window-$VAR-$WIN"
O="$C/HarmonyBot-V70/output-$VAR-$WIN"
rm -rf "$O" "$W"
mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V70/dist/HarmonyBot_V70_Causal_Admission_Reconstruction_Alpha_Recall_Recovery.algo" "$W/seal/algo/"
N="V70-$VAR-$WIN-B10000"

(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000  FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true  IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true  PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false  V67CONTRACTS=false V67FRONTIER=false V67FGRID=false V67EVIDENCE=false V67EXPAND=false  V68IDENT=true V68IDFAIL=false V68PRESERVE=false V68EXPAND=false V68GRID=false  V69VIS=true V69SHADOW=true V69HORIZON=180  V70HARD="$V70HARD" V70FAM="$V70FAM" V70ARB="$V70ARB" V70PROTECT=true V70WAIT=12  MAXDD=10 BACKTEST_TIMEOUT_SECONDS=1800  "$C/HarmonyBot-V70/tools/run_backtest.sh"
)

python3 "$C/HarmonyBot-V70/tools/audit_report.py"  --report "$W/seal/reports/$N.json"  --log "$W/seal/logs/$N.log"  --out "$O/$VAR-$WIN.json"  --window "$WIN" --family "$VAR" --years "$YEARS" --balance 10000

cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"
