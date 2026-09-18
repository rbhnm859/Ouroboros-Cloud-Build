#!/usr/bin/env bash
set -euo pipefail
ROOT="$PWD"
CONTROL="$ROOT/control"
WORK="$CONTROL/HarmonyBot-V33/work"
OUT="$CONTROL/HarmonyBot-V33/output"
mkdir -p "$WORK/seal/algo" "$OUT"

write_not_run() {
  local status="$1" reason="$2"
  for n in VALIDATION COMMERCIAL100 OOS WALK_FORWARD SENSITIVITY COST_STRESS MONTE_CARLO FINAL_HOLDOUT; do
    python3 - "$OUT/$n.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
pathlib.Path(p).write_text(json.dumps({"status":status,"reason":reason},indent=2))
PY
  done
}

finalize() {
  local status="$1" reason="$2"
  python3 - "$OUT/FINAL_COMMERCIAL_DECISION.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
x={"version":"HarmonyBot V33.0 — Fibonacci Harmonic Basket Risk & Execution Architecture",
   "final_status":status,"reason":reason,"profit_guarantee":False,
   "commercial_algo_created": status in ("PASS","NEAR_TARGET")}
pathlib.Path(p).write_text(json.dumps(x,indent=2))
pathlib.Path(p).with_suffix(".md").write_text("# HarmonyBot V33.0 Final Decision\n\n**"+status+"**\n\n"+reason+"\n")
print(json.dumps(x,indent=2))
PY
}

echo "== V33 engineering audits =="
cd "$CONTROL"
python3 HarmonyBot-V33/tools/static_audit.py HarmonyBot-V33/src/HarmonyBotV33.cs
python3 HarmonyBot-V33/tools/data_exposure_scan.py
cp STATIC_AUDIT.json TIMEFRAME_AUDIT.json NO_LOOKAHEAD_AUDIT.json SESSION_DST_AUDIT.json GRID_RISK_AUDIT.json EXECUTION_STATE_AUDIT.json DATA_EXPOSURE_LEDGER.json "$OUT/"

echo "== V33 clean build =="
dotnet restore HarmonyBot-V33/HarmonyBotV33.csproj
dotnet build HarmonyBot-V33/HarmonyBotV33.csproj -c Release --no-restore --nologo 2>&1 | tee "$OUT/V33_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$OUT/V33_BUILD.log"

ALGO=$(find HarmonyBot-V33/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$WORK/seal/algo/HarmonyBot_V33_Internal.algo"
cp HarmonyBot-V33/src/HarmonyBotV33.cs "$OUT/HarmonyBotV33.cs"
sha256sum HarmonyBot-V33/src/HarmonyBotV33.cs "$ALGO" > "$OUT/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$OUT/SOURCE_COMMIT.txt"

run_dev() {
  local run="$1" window="$2" start="$3" eval="$4" end="$5" years="$6"
  echo "== $run =="
  (
    cd "$WORK"
    RUN_NAME="$run" START_DATE="$start" EVAL_DATE="$eval" END_DATE="$end" CAPITAL=10000 DATA_MODE=m1 RISK=1.0       "$CONTROL/HarmonyBot-V33/tools/run_backtest.sh"
  )
  python3 "$CONTROL/HarmonyBot-V33/tools/audit_report.py"     --report "$WORK/seal/reports/$run.json"     --log "$WORK/seal/logs/$run.log"     --out "$OUT/$window.json"     --window "$window" --years "$years" --capital 10000
}

echo "== V33 EXPOSED architecture verification: one pass only =="
run_dev "V33-DEV-A" "DEV-A" "04/01/2021" "2021-01-11T00:00:00Z" "30/06/2021" 0.5
run_dev "V33-DEV-B" "DEV-B" "01/07/2021" "2021-07-08T00:00:00Z" "31/12/2021" 0.5
run_dev "V33-DEV-C" "DEV-C" "03/01/2022" "2022-01-10T00:00:00Z" "30/06/2022" 0.5

mkdir -p "$WORK/all"
cp "$OUT/DEV-A.json" "$WORK/all/DEV-A.json"
cp "$OUT/DEV-B.json" "$WORK/all/DEV-B.json"
cp "$OUT/DEV-C.json" "$WORK/all/DEV-C.json"

mkdir -p "$OUT/raw-logs"
cp "$WORK/seal/logs/"*.log "$OUT/raw-logs/" 2>/dev/null || true

(
  cd "$WORK"
  GITHUB_OUTPUT=/tmp/v33-development.out python3 "$CONTROL/HarmonyBot-V33/tools/development_gate.py"
)
cp "$WORK/DEVELOPMENT_GATE.json" "$OUT/"

python3 - "$OUT" <<'PY'
import json,pathlib,sys,collections,statistics
o=pathlib.Path(sys.argv[1])
rows=[json.load(open(o/f"{w}.json")) for w in ("DEV-A","DEV-B","DEV-C")]
agg=collections.defaultdict(lambda:collections.Counter())
for x in rows:
    for p,z in x.get("pipeline",{}).items():
        for k,v in z.items(): agg[p][k]+=v
(o/"PIPELINE_CONVERSION_MATRIX.json").write_text(json.dumps({p:dict(v) for p,v in agg.items()},indent=2))
grid={
 "version":"HarmonyBot V33.0",
 "windows":{x["window"]:x.get("grid_attribution",{}) for x in rows},
 "aggregate":{
   "average_filled_legs":statistics.mean([x["grid_attribution"]["average_filled_legs"] for x in rows]) if rows else 0,
   "average_entry_improvement_pips":statistics.mean([x["grid_attribution"]["average_entry_improvement_pips"] for x in rows]) if rows else 0,
   "average_worst_risk_utilization":statistics.mean([x["grid_attribution"]["average_worst_risk_utilization"] for x in rows]) if rows else 0
 }}
(o/"FIBONACCI_GRID_ATTRIBUTION.json").write_text(json.dumps(grid,indent=2))
err=collections.Counter()
for x in rows:
    err.update(x.get("execution_error_reasons",{}))
(o/"EXECUTION_ERROR_LEDGER.json").write_text(json.dumps({"version":"HarmonyBot V33.0","total":sum(err.values()),"reasons":dict(err)},indent=2))
life={
 "version":"HarmonyBot V33.0",
 "windows":{x["window"]:x.get("risk_lifecycle_attribution",{}) for x in rows},
 "aggregate":{
   "admission_risk_rejects":sum(x.get("risk_lifecycle_attribution",{}).get("admission_risk_rejects",0) for x in rows),
   "admission_thesis_rejects":sum(x.get("risk_lifecycle_attribution",{}).get("admission_thesis_rejects",0) for x in rows),
   "admission_passes":sum(x.get("risk_lifecycle_attribution",{}).get("admission_passes",0) for x in rows),
   "frontier_advances":sum(x.get("risk_lifecycle_attribution",{}).get("frontier_advances",0) for x in rows),
   "technical_retries":sum(x.get("risk_lifecycle_attribution",{}).get("technical_retries",0) for x in rows)
 }}
(o/"RISK_LIFECYCLE_ATTRIBUTION.json").write_text(json.dumps(life,indent=2))
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
GRID_NO_EDGE=$(python3 - "$OUT/DEVELOPMENT_GATE.json" <<'PY'
import json,sys
print('true' if json.load(open(sys.argv[1])).get('grid_no_edge') else 'false')
PY
)

if [ "$ENGINEERING_FAIL" = "true" ]; then
  write_not_run "NOT_RUN" "Engineering pipeline did not initialize correctly."
  finalize "ENGINEERING_PIPELINE_FAILURE" "V33 compiled/backtested but the candidate/grid evidence pipeline did not initialize correctly. This is engineering failure, not strategy failure."
  exit 0
fi

if [ "$DEV_PASS" != "true" ]; then
  if [ "$GRID_NO_EDGE" = "true" ]; then
    write_not_run "NOT_RUN" "V33 Development classified FIBONACCI_GRID_NO_EDGE."
    finalize "FIBONACCI_GRID_NO_EDGE" "The pre-registered Fibonacci staged-entry architecture increased drawdown without improving PF, expectancy, MAE efficiency or entry efficiency versus the actual L0 SingleEntryEquivalent. No V33.x rescue is authorized."
  else
    write_not_run "NOT_RUN" "V33 exposed Development hard gate failed."
    finalize "STRATEGY_ARCHITECTURE_LIMITATION" "V33 completed the one-pass exposed DEV-A/B/C architecture verification but failed one or more mandatory Development gates. No threshold/grid/pattern rescue is authorized."
  fi
  exit 0
fi

AUTHORIZED=$(python3 - "$OUT/DATA_EXPOSURE_LEDGER.json" <<'PY'
import json,sys
print('true' if json.load(open(sys.argv[1])).get('downstream_authorized') else 'false')
PY
)

if [ "$AUTHORIZED" != "true" ]; then
  write_not_run "NOT_RUN_DATA_GOVERNANCE" "Fresh pre-reserved Validation/OOS/Final Holdout ranges are not yet proven untouched."
  finalize "HOLD_DATA_GOVERNANCE" "V33 passed exposed Development, but fresh pre-reserved downstream evidence windows are not presently proven untouched. Validation, Commercial100, OOS, walk-forward, sensitivity, cost stress, Monte Carlo and Final Holdout remain locked."
  exit 0
fi

write_not_run "NOT_RUN" "No fresh reserved downstream ranges were assigned; refusing to invent dates."
finalize "HOLD" "Development passed but downstream ranges are unassigned. No Commercial .algo is created."
