#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?years}"
VAR="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; YEARS="$6"
case "$VAR" in
 A_V70_TRUTH_CONTROL)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=false; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=false; V71SPINE=false; V71POSTGRID=false; V71COREARB=false; V71CHALLENGER=false; V71SURVIVAL2=false; RISKCAP=1.0;;
 B_CANONICAL_CORE_SPINE)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=false; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=false; V71SPINE=true; V71POSTGRID=true; V71COREARB=true; V71CHALLENGER=false; V71SURVIVAL2=false; RISKCAP=1.0;;
 C_CORE_REGIME_SURVIVAL)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=false; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=false; V71SPINE=true; V71POSTGRID=true; V71COREARB=true; V71CHALLENGER=false; V71SURVIVAL2=true; RISKCAP=1.0;;
 D_CHALLENGER_RESERVE)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=false; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=false; V71SPINE=true; V71POSTGRID=true; V71COREARB=true; V71CHALLENGER=true; V71SURVIVAL2=true; RISKCAP=1.0;;
 E_POST_SELECTION_GRID)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=true; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=false; V71SPINE=true; V71POSTGRID=true; V71COREARB=true; V71CHALLENGER=true; V71SURVIVAL2=true; RISKCAP=1.0;;
 F_ADAPTIVE_RISK_CAPACITY)
   V71SUPPRESS=false; V71RECALL=false; V71GRID=true; V71NOBACKFILL=false; V71REGIME=false; V71BACKFILL=false; V71ADAPRISK=true; V71SPINE=true; V71POSTGRID=true; V71COREARB=true; V71CHALLENGER=true; V71SURVIVAL2=true; RISKCAP=5.0;;
 *) echo "unknown V71 variant $VAR"; exit 31;;
esac

C="$PWD/control"
W="$C/HarmonyBot-V71/window-$VAR-$WIN"
O="$C/HarmonyBot-V71/output-$VAR-$WIN"
rm -rf "$O" "$W"
mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V71/dist/HarmonyBot_V71_Selective_Causal_Alpha_Reconstruction_Grid_Amplifier.algo" "$W/seal/algo/"
N="V71-$VAR-$WIN-B10000"

(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 V67CONTRACTS=false V67FRONTIER=false V67FGRID=false V67EVIDENCE=false V67EXPAND=false \
 V68IDENT=true V68IDFAIL=false V68PRESERVE=false V68EXPAND=false V68GRID=false \
 V69VIS=true V69SHADOW=true V69HORIZON=180 \
 V70HARD=false V70FAM=false V70ARB=false V70PROTECT=true V70WAIT=12 \
 V71SUPPRESS="$V71SUPPRESS" V71RECALL="$V71RECALL" V71GRID="$V71GRID" V71NOBACKFILL="$V71NOBACKFILL" V71REGIME="$V71REGIME" V71BACKFILL="$V71BACKFILL" V71ADAPRISK="$V71ADAPRISK" V71SPINE="$V71SPINE" V71POSTGRID="$V71POSTGRID" V71COREARB="$V71COREARB" V71CHALLENGER="$V71CHALLENGER" V71SURVIVAL2="$V71SURVIVAL2" RISKCAP="$RISKCAP" \
 MAXDD=10 BACKTEST_TIMEOUT_SECONDS=1800 \
 "$C/HarmonyBot-V71/tools/run_backtest.sh"
)

test -s "$W/seal/logs/$N.log"
test -s "$W/seal/reports/$N.json"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"

python3 "$C/HarmonyBot-V71/tools/audit_report.py" \
 --report "$W/seal/reports/$N.json" \
 --log "$W/seal/logs/$N.log" \
 --out "$O/$VAR-$WIN.json" \
 --window "$WIN" --family "$VAR" --years "$YEARS" --balance 10000
