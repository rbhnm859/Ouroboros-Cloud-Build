#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"

C="$PWD/control"
W="$C/HarmonyBot-V71/window-R17-TICK-$WIN"
O="$C/HarmonyBot-V71/output-R17-TICK-$WIN"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$W/seal/data" "$W/seal/reports" "$W/seal/logs" "$O/raw-logs"

A=$(find "$C/HarmonyBot-V71/dist" -type f -name 'HarmonyBot_V71_Protected_Champion_Core_Incremental_Alpha.algo' | head -1)
test -s "$A"
cp "$A" "$W/seal/algo/"

N="V71-R17-TICK-$WIN-B10000"
(
  cd "$W"
  RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
  EXPSHADOW=false EXPEXEC=false EXPGRID=false EXPADAPRISK=false EXPRISK=1.0 \
  V72BIFURCATION=false V72FAMILYNATIVE=false V72FAILUREAUCTION=false V72HCOG=false V72HCAP=false \
  V73UNIVERSE=true V74R17TICK=true V74EXTERNAL=false V74EMBEDDED=false \
  BACKTEST_DATA_MODE=ticks IMMUTABLE_DATA=false BACKTEST_TIMEOUT_SECONDS=3600 \
  "$C/HarmonyBot-V71/tools/run_backtest.sh"
)

test -s "$W/seal/logs/$N.log"
test -s "$W/seal/logs/$N-R15.log"
test -s "$W/seal/reports/$N.json"

DATA_FILES=$(find "$W/seal/data" -type f | wc -l | tr -d ' ')
test "$DATA_FILES" -gt 0 || { echo "[R17-TICK-CUSTODY-FAIL] window=$WIN reason=EMPTY_TICK_CACHE"; exit 61; }
DATA_HASH=$(cd "$W/seal/data" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
printf "%s\n" "$DATA_HASH" > "$O/DATA_SNAPSHOT_SHA256.txt"
printf "%s\n" "$DATA_HASH" > "$O/R17_TICK_DATA_SHA256.txt"
printf "%s\n" "$DATA_FILES" > "$O/R17_TICK_DATA_FILE_COUNT.txt"
cat > "$O/R17_TICK_CUSTODY.json" <<JSON
{
  "schema": "V74_R17_TICK_CUSTODY_V1",
  "window": "$WIN",
  "data_mode": "ticks",
  "source": "ctrader_server_tick_cache",
  "sha256": "$DATA_HASH",
  "file_count": $DATA_FILES,
  "validation_used": false,
  "fresh_used": false,
  "burned_used": false
}
JSON

cp "$W/seal/logs/$N-R15.log" "$O/raw-logs/$N-R15.log"
sha256sum "$O/raw-logs/$N-R15.log" > "$O/R17_EVIDENCE_SHA256-$WIN.txt"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"

python3 "$C/HarmonyBot-V71/tools/audit_report.py" \
  --report "$W/seal/reports/$N.json" \
  --log "$W/seal/logs/$N.log" \
  --out "$O/R_V73_OPPORTUNITY_UNIVERSE-$WIN.json" \
  --window "$WIN" --variant R_V73_OPPORTUNITY_UNIVERSE \
  --years "$YEARS" --balance 10000 --data-snapshot "$O/DATA_SNAPSHOT_SHA256.txt"

echo "[R17-TICK-CUSTODY] window=$WIN files=$DATA_FILES sha256=$DATA_HASH"
