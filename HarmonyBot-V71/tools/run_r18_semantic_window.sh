#!/usr/bin/env bash
set -euo pipefail
: "${1:?window}"; : "${2:?start}"; : "${3:?eval}"; : "${4:?end}"; : "${5:?years}"
WIN="$1"; START="$2"; EVAL="$3"; END="$4"; YEARS="$5"

C="$PWD/control"
W="$C/HarmonyBot-V71/window-R18-SEMANTIC-$WIN"
O="$C/HarmonyBot-V71/output-R18-SEMANTIC-$WIN"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$W/seal/data" "$W/seal/reports" "$W/seal/logs" "$O/raw-logs"

A=$(find "$C/HarmonyBot-V71/dist" -type f -name 'HarmonyBot_V71_Protected_Champion_Core_Incremental_Alpha.algo' | head -1)
test -s "$A"
cp "$A" "$W/seal/algo/"

N="V71-R18-SEMANTIC-$WIN-B10000"

capture_failure() {
  rc=$?
  if [[ "$rc" -ne 0 ]]; then
    mkdir -p "$O/failure"
    test ! -s "$W/seal/logs/$N.log" || cp "$W/seal/logs/$N.log" "$O/failure/$N.log"
    test ! -s "$W/seal/logs/$N-R15.log" || cp "$W/seal/logs/$N-R15.log" "$O/failure/$N-R15.log"
    test ! -s "$W/seal/reports/$N.json" || cp "$W/seal/reports/$N.json" "$O/failure/$N.json"
    printf '%s\n' "$rc" > "$O/failure/exit_code.txt"
  fi
  exit "$rc"
}
trap capture_failure ERR

(
  cd "$W"
  RUN_NAME="$N" START_DATE="$START" EVAL_DATE="$EVAL" END_DATE="$END" BALANCE=10000 \
  EXPSHADOW=false EXPEXEC=false EXPGRID=false EXPADAPRISK=false EXPRISK=1.0 \
  V72BIFURCATION=false V72FAMILYNATIVE=false V72FAILUREAUCTION=false V72HCOG=false V72HCAP=false \
  V73UNIVERSE=true V74R17TICK=true V74R18OUTCOME=true V74EXTERNAL=false V74EMBEDDED=false \
  BACKTEST_DATA_MODE=ticks IMMUTABLE_DATA=false BACKTEST_TIMEOUT_SECONDS="${R18_BACKTEST_TIMEOUT_SECONDS:-4500}" \
  "$C/HarmonyBot-V71/tools/run_backtest.sh"
)

test -s "$W/seal/logs/$N.log"
test -s "$W/seal/logs/$N-R15.log"
test -s "$W/seal/reports/$N.json"
grep -q '^\[V74-R18-SUMMARY\] schema=V74_R18_OUTCOME_V1 ' "$W/seal/logs/$N-R15.log"
grep -q '^\[V74-R18-OUTCOME\] schema=V74_R18_OUTCOME_V1 ' "$W/seal/logs/$N-R15.log"
# Causal truth gate: the sealed telemetry must carry the corrected forward-time
# tick fingerprint. A legacy newest-to-oldest frame is never acceptable here.
grep -q '^\[V74-R17-FRAME\] schema=V74_R17_TICK_V4 ' "$W/seal/logs/$N-R15.log"
if grep -q 'schema=V74_R17_TICK_V2 ' "$W/seal/logs/$N-R15.log"; then
  echo "[R18-TICK-TRUTH-FAIL] window=$WIN reason=LEGACY_REVERSED_TICK_FRAME"
  exit 72
fi

DATA_FILES=$(find "$W/seal/data" -type f | wc -l | tr -d ' ')
test "$DATA_FILES" -gt 0 || { echo "[R18-CUSTODY-FAIL] window=$WIN reason=EMPTY_TICK_CACHE"; exit 71; }
DATA_HASH=$(cd "$W/seal/data" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)
EVIDENCE_HASH=$(sha256sum "$W/seal/logs/$N-R15.log" | cut -d' ' -f1)

cp "$W/seal/logs/$N-R15.log" "$O/raw-logs/$N-R15.log"
cp "$W/seal/logs/$N.log" "$O/raw-logs/$N.log"
cp "$W/seal/reports/$N.json" "$O/raw-report.json"
printf '%s\n' "$DATA_HASH" > "$O/DATA_SNAPSHOT_SHA256.txt"
printf '%s  %s\n' "$EVIDENCE_HASH" "raw-logs/$N-R15.log" > "$O/R18_EVIDENCE_SHA256-$WIN.txt"

cat > "$O/R18_SEMANTIC_CUSTODY.json" <<JSON
{
  "schema": "V74_R18_SEMANTIC_CUSTODY_V1",
  "window": "$WIN",
  "data_mode": "ticks",
  "source": "ctrader_server_tick_cache",
  "tick_sha256": "$DATA_HASH",
  "evidence_sha256": "$EVIDENCE_HASH",
  "file_count": $DATA_FILES,
  "tick_time_semantics": "FORWARD",
  "validation_used": false,
  "fresh_used": false,
  "burned_used": false
}
JSON

python3 "$C/HarmonyBot-V71/tools/audit_report.py" \
  --report "$W/seal/reports/$N.json" \
  --log "$W/seal/logs/$N.log" \
  --out "$O/R_V73_OPPORTUNITY_UNIVERSE-$WIN.json" \
  --window "$WIN" --variant R_V73_OPPORTUNITY_UNIVERSE \
  --years "$YEARS" --balance 10000 --data-snapshot "$O/DATA_SNAPSHOT_SHA256.txt"

echo "[R18-SEMANTIC-CUSTODY] window=$WIN files=$DATA_FILES tick_sha256=$DATA_HASH evidence_sha256=$EVIDENCE_HASH tick_time_semantics=FORWARD"
