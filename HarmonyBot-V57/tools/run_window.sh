#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?manifest path}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; MANIFEST="$6"
CAN=true; FC=true; GRIDV2=true; STOP=true; JOINT=true; CORRIDOR=false
IDENT=false; BOUNDED=false; RESEARCHCONT=false; FAMILYBOOKS=false; SHADOW=false; CALADMIT=false; FAMREP=false; ABCDLIVE=false; V57GRID=true
case "$FAM" in
 V51_CHAMPION_CONTROL)
   ;;
 V57_FAMILY_REP_CONTROL)
   IDENT=true; BOUNDED=true; RESEARCHCONT=true; FAMILYBOOKS=true; SHADOW=true; CALADMIT=false; FAMREP=true; V57GRID=true;;
 V57_CALIBRATED_L0)
   IDENT=true; BOUNDED=true; RESEARCHCONT=true; FAMILYBOOKS=true; SHADOW=true; CALADMIT=true; FAMREP=true; V57GRID=false;;
 V57_CALIBRATED_LEGACY_GRID)
   IDENT=true; BOUNDED=true; RESEARCHCONT=true; FAMILYBOOKS=true; SHADOW=true; CALADMIT=true; FAMREP=true; V57GRID=true;;
 *) echo "unknown V57 variant $FAM"; exit 31;;
esac
CALMAN=""
if [ "$CALADMIT" = true ]; then
  test -s "$MANIFEST" || { echo "[V57-CALIBRATION-MANIFEST-MISSING] $MANIFEST"; exit 41; }
  CALMAN=$(tr -d '\n\r' < "$MANIFEST")
  test -n "$CALMAN" || { echo "[V57-CALIBRATION-MANIFEST-EMPTY]"; exit 42; }
fi
C="$PWD/control"; W="$C/HarmonyBot-V57/window-$FAM-$WIN"; O="$C/HarmonyBot-V57/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V57/dist/HarmonyBot_V57_Regime_Calibrated_Universal_Harmonic_Family_Portfolio_RC.algo" "$W/seal/algo/"
N="V57-$FAM-$WIN-B10000"
test -s "$W/seal/data.snapshot.sha" || { echo "[V57-DATA-SNAPSHOT-MISSING]"; exit 43; }
DATA_SHA=$(tr -d '[:space:]' < "$W/seal/data.snapshot.sha")
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT="$CAN" FAMCONF="$FC" GRIDV2="$GRIDV2" STOPV2="$STOP" JOINT="$JOINT" CORRIDOR="$CORRIDOR" ANCHORFORENSICS=true \
 IDENT="$IDENT" BOUNDED="$BOUNDED" SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true \
 TRADING=true FAMILYBOOKS="$FAMILYBOOKS" SHADOW="$SHADOW" CALADMIT="$CALADMIT" FAMREP="$FAMREP" RESEARCHCONT="$RESEARCHCONT" \
 ABCDLIVE="$ABCDLIVE" V57GRID="$V57GRID" CALMIN=0.0 CALMAN="$CALMAN" \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false BACKTEST_TIMEOUT_SECONDS=1800 \
 "$C/HarmonyBot-V57/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V57/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000 --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
