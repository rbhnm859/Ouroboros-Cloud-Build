#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"
C="$PWD/control"; W="$C/HarmonyBot-V71/reference-window-$WIN"; O="$C/HarmonyBot-V71/reference-output-$WIN"
rm -rf "$O" "$W"; mkdir -p "$W/seal/algo" "$W/seal/data" "$O/raw-logs"
cp "$C/HarmonyBot-V71/reference/HarmonyBot_V51_Family_Native_Math_Geometry_Economic_Conversion_RC.algo" "$W/seal/algo/"
N="V51-REFERENCE-$WIN-B10000"
(
 cd "$W"
 RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
 FAMNATIVE=false FAMOBS=true CANCONTRACT=true FAMCONF=true GRIDV2=true STOPV2=true JOINT=true CORRIDOR=true ANCHORFORENSICS=true \
 PQUEUE=false HANDOFF=false NATIVE=false NATIVEBARS=4 DECAY=false HARDLIFE=180 REVALIDATE=false \
 ALGO="seal/algo/HarmonyBot_V51_Family_Native_Math_Geometry_Economic_Conversion_RC.algo" \
 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V51/tools/run_backtest.sh"
)
test -s "$W/seal/logs/$N.log"; test -s "$W/seal/reports/$N.json"
DATA_FILES=$(find "$W/seal/data" -type f | wc -l | tr -d " ")
test "$DATA_FILES" -gt 0 || { echo "[V71-DATA-SEED-FAIL] window=$WIN reason=EMPTY_DATA_CACHE"; exit 41; }
DATA_HASH=$(cd "$W/seal/data" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
printf "%s\n" "$DATA_HASH" > "$O/DATA_SNAPSHOT_SHA256.txt"
printf "%s\n" "$DATA_FILES" > "$O/DATA_SNAPSHOT_FILE_COUNT.txt"
echo "[V71-DATA-SEED] window=$WIN files=$DATA_FILES sha256=$DATA_HASH"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"; cp "$W/seal/reports/$N.json" "$O/raw-report.json"
python3 "$C/HarmonyBot-V71/tools/audit_report.py" --report "$W/seal/reports/$N.json" --log "$W/seal/logs/$N.log"  --out "$O/V51_REFERENCE-$WIN.json" --window "$WIN" --variant "V51_REFERENCE" --years "$YEARS" --balance 10000 --data-snapshot "$O/DATA_SNAPSHOT_SHA256.txt"
