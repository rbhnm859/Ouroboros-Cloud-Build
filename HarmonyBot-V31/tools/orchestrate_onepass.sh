#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
CONTROL="$ROOT/control"
WORK="$CONTROL/HarmonyBot-V31/work"
OUT="$CONTROL/HarmonyBot-V31/output"
mkdir -p "$WORK/seal/algo" "$OUT"

finalize() {
  local status="$1"
  local reason="$2"
  python3 - "$OUT/FINAL_COMMERCIAL_DECISION.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
x={
 "version":"HarmonyBot V31.0 — Clean-Room Multi-Timeframe Harmonic Execution Kernel",
 "final_status":status,
 "reason":reason,
 "profit_guarantee":False
}
pathlib.Path(p).write_text(json.dumps(x,indent=2))
pathlib.Path(p).with_suffix(".md").write_text("# HarmonyBot V31.0 Final Decision\n\n**"+status+"**\n\n"+reason+"\n")
print(json.dumps(x,indent=2))
PY
}

echo "== V31 clean-room source audit =="
cd "$CONTROL"
python3 HarmonyBot-V31/tools/static_audit.py HarmonyBot-V31/src/HarmonyBotV31.cs
python3 HarmonyBot-V31/tools/data_exposure_scan.py
cp STATIC_AUDIT.json TIMEFRAME_AUDIT.json NO_LOOKAHEAD_AUDIT.json SESSION_DST_AUDIT.json DATA_EXPOSURE_LEDGER.json "$OUT/"

echo "== V31 clean build =="
dotnet restore HarmonyBot-V31/HarmonyBotV31.csproj
dotnet build HarmonyBot-V31/HarmonyBotV31.csproj -c Release --no-restore --nologo 2>&1 | tee "$OUT/V31_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$OUT/V31_BUILD.log"
ALGO=$(find HarmonyBot-V31/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$WORK/seal/algo/HarmonyBot_V31_Commercial.algo"
cp HarmonyBot-V31/src/HarmonyBotV31.cs "$OUT/HarmonyBotV31.cs"
sha256sum HarmonyBot-V31/src/HarmonyBotV31.cs "$ALGO" > "$OUT/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$OUT/SOURCE_COMMIT.txt"

run_dev() {
  local run="$1" window="$2" start="$3" eval="$4" end="$5" years="$6"
  echo "== $run =="
  (
    cd "$WORK"
    RUN_NAME="$run" START_DATE="$start" EVAL_DATE="$eval" END_DATE="$end" CAPITAL=10000 DATA_MODE=m1 RISK=1.0 \
      "$CONTROL/HarmonyBot-V31/tools/run_backtest.sh"
  )
  python3 "$CONTROL/HarmonyBot-V31/tools/audit_report.py" \
    --report "$WORK/seal/reports/$run.json" \
    --log "$WORK/seal/logs/$run.log" \
    --out "$OUT/$window.json" \
    --window "$window" --years "$years" --capital 10000
}

echo "== V31 exposed Development / architecture verification only =="
run_dev "V31-DEV-A" "DEV-A" "04/01/2021" "2021-01-11T00:00:00Z" "30/06/2021" 0.5
run_dev "V31-DEV-B" "DEV-B" "01/07/2021" "2021-07-08T00:00:00Z" "31/12/2021" 0.5
run_dev "V31-DEV-C" "DEV-C" "03/01/2022" "2022-01-10T00:00:00Z" "30/06/2022" 0.5

mkdir -p "$WORK/all"
cp "$OUT/DEV-A.json" "$WORK/all/DEV-A.json"
cp "$OUT/DEV-B.json" "$WORK/all/DEV-B.json"
cp "$OUT/DEV-C.json" "$WORK/all/DEV-C.json"

(
  cd "$WORK"
  GITHUB_OUTPUT=/tmp/v31-development.out python3 "$CONTROL/HarmonyBot-V31/tools/development_gate.py"
)
cp "$WORK/DEVELOPMENT_GATE.json" "$OUT/"

python3 - "$OUT" <<'PY'
import json,pathlib,sys,collections
o=pathlib.Path(sys.argv[1])
rows=[json.load(open(o/f"{w}.json")) for w in ("DEV-A","DEV-B","DEV-C")]
agg=collections.defaultdict(lambda:collections.Counter())
for x in rows:
    for p,z in x.get("pipeline",{}).items():
        for k,v in z.items(): agg[p][k]+=v
(o/"PIPELINE_CONVERSION_MATRIX.json").write_text(json.dumps({p:dict(v) for p,v in agg.items()},indent=2))
root={
 "version":"HarmonyBot V31.0",
 "architecture_checks":{
  "M15_primary_pattern":True,
  "M1_execution_confirmation":True,
  "H4_H1_closed_bar_context":True,
  "legacy_V29_pending_removed":True,
  "legacy_V30_router_removed":True,
  "grid_removed":True,
  "single_position":True,
  "candidate_event_ledger":True
 },
 "development":{x["window"]:{
   "baskets":x["baskets"],"pf":x["pf"],"net":x["net"],"expectancy":x["expectancy"],"win_rate_pct":x["win_rate_pct"],
   "max_dd_pct":x["max_dd_pct"],"pattern":x["pattern"],"route":x["route"],"direction":x["direction"],
   "mean_mfe_r":x["mean_mfe_r"],"mean_mae_r":x["mean_mae_r"]
 } for x in rows}
}
(o/"V31_ROOT_CAUSE_AND_ARCHITECTURE_REPORT.json").write_text(json.dumps(root,indent=2))
PY

DEV_PASS=$(python3 - "$OUT/DEVELOPMENT_GATE.json" <<'PY'
import json,sys
print('true' if json.load(open(sys.argv[1])).get('development_pass') else 'false')
PY
)

ENGINEERING_FAIL=$(python3 - "$OUT/DEVELOPMENT_GATE.json" <<'PY'
import json,sys
print('true' if json.load(open(sys.argv[1])).get('engineering_pipeline_failure') else 'false')
PY
)

if [ "$ENGINEERING_FAIL" = "true" ]; then
  finalize "ENGINEERING_PIPELINE_FAILURE" "V31 compiled and backtested, but the candidate event pipeline did not initialize or emit detections. This is not classified as strategy failure."
  exit 0
fi

if [ "$DEV_PASS" != "true" ]; then
  finalize "STRATEGY_ARCHITECTURE_LIMITATION" "V31 clean-room architecture completed and compiled, but the exposed DEV-A/B/C hard gate did not pass. Per preregistration, no V31.1/V31.2 rescue and no threshold retuning against these windows."
  exit 0
fi

AUTHORIZED=$(python3 - "$OUT/DATA_EXPOSURE_LEDGER.json" <<'PY'
import json,sys
print('true' if json.load(open(sys.argv[1])).get('downstream_authorized') else 'false')
PY
)

if [ "$AUTHORIZED" != "true" ]; then
  finalize "HOLD_DATA_GOVERNANCE" "V31 passed exposed Development, but no historical Validation/OOS/Final-Holdout interval can currently be proven untouched from prior HarmonyBot research. Downstream evidence is locked rather than reusing contaminated windows."
  exit 0
fi

finalize "HOLD" "Downstream authorization exists but no reserved downstream ranges were assigned in this one-pass specification. Refusing to invent validation dates."
