#!/usr/bin/env bash
set -euo pipefail
: "${1:?variant}"; : "${2:?window}"; : "${3:?start}"; : "${4:?eval}"; : "${5:?end}"; : "${6:?manifest}"
FAM="$1"; WIN="$2"; START="$3"; EVAL="$4"; END="$5"; MANIFEST="$6"
GRID=true; CAPLIVE=false; CALADMIT=false
case "$FAM" in
 V59_MANIFOLD_BASELINE_L0) GRID=false; CAPLIVE=false; CALADMIT=true;;
 V59_MANIFOLD_CAPTURE_L0) GRID=false; CAPLIVE=true; CALADMIT=true;;
 V59_MANIFOLD_CAPTURE_LEGACY_GRID) GRID=true; CAPLIVE=true; CALADMIT=true;;
 *) echo "unknown V59 variant $FAM"; exit 31;;
esac
test -s "$MANIFEST" || { echo "[V59-MANIFEST-MISSING]"; exit 41; }
CALMAN=$(tr -d '\n\r' < "$MANIFEST"); test -n "$CALMAN" || { echo "[V59-MANIFEST-EMPTY]"; exit 42; }
C="$PWD/control"; W="$C/HarmonyBot-V59/window-$FAM-$WIN"; O="$C/HarmonyBot-V59/output-$FAM-$WIN"
rm -rf "$O"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V59/dist/HarmonyBot_V59_Canonical_Harmonic_Manifold_Excursion_Capture_RC.algo" "$W/seal/algo/"
N="V59-$FAM-$WIN-B10000"
test -s "$W/seal/data.snapshot.sha" || { echo "[V59-DATA-SNAPSHOT-MISSING]"; exit 43; }
DATA_SHA=$(tr -d '[:space:]' < "$W/seal/data.snapshot.sha")
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=false ANCHORFORENSICS=true \
 IDENT=true BOUNDED=true SKIPS=2 FQUOTA=4 PRJPRZ=false DTRUTH=true TRADING=true FAMILYBOOKS=true SHADOW=true CALADMIT="$CALADMIT" FAMREP=true RESEARCHCONT=true \
 ABCDLIVE=false V59GRID="$GRID" CALMIN=0.0 CALMAN="$CALMAN" MANIFOLD=true PUREPRZ=true DAG=true CAPRESEARCH=true CAPLIVE="$CAPLIVE" MATCHED=true PROJERR=.55 MSIG=1.0 \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false BACKTEST_TIMEOUT_SECONDS=1800 \
 "$C/HarmonyBot-V59/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V59/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log" --out "$O/$FAM-$WIN.json" --window "$WIN" --family "$FAM" --years .5 --balance 10000 --data-sha "$DATA_SHA"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
