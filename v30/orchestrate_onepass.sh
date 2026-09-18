#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
BASE="$ROOT/base"
CONTROL="$ROOT/control"
WORK="$CONTROL/v30-work"
OUT="$CONTROL/v30-output"
mkdir -p "$WORK/seal/algo" "$OUT"

finalize() {
  local status="$1"; local reason="$2"
  python3 - "$OUT/FINAL_COMMERCIAL_DECISION.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
x={"version":"HarmonyBot V30.0 Regime-Routed Harmonic Portfolio Engine","final_commercial_freeze":status,"reason":reason}
pathlib.Path(p).write_text(json.dumps(x,indent=2))
pathlib.Path(p).with_suffix(".md").write_text("# HarmonyBot V30.0 Final Commercial Decision\n\n**"+status+"**\n\n"+reason+"\n")
print(json.dumps(x,indent=2))
PY
}

echo "== V30 evidence lock =="
test -f "$CONTROL/v30/V30_ARCHITECTURE_FREEZE.md"
cp "$CONTROL/v30/V30_ARCHITECTURE_FREEZE.md" "$OUT/"
printf '%s\n' '35342318165' > "$OUT/PARENT_EVIDENCE_RUN.txt"

echo "== Reconstruct frozen engineering lineage + V30 major architecture =="
cd "$BASE"
python3 tmp/harmonybot-v26-build/build_v261_frequency.py
python3 tmp/harmonybot-v26-build/fix_v261_mtf_overload.py
python3 tmp/harmonybot-v26-build/fix_v262_frequency_safe.py
python3 tmp/harmonybot-v26-build/fix_v262_grid_guard_band.py
python3 tmp/harmonybot-v26-build/fix_v27_commercial_rc.py
python3 tmp/harmonybot-v26-build/fix_v28_frequency_architecture.py
python3 tmp/harmonybot-v26-build/fix_v28_cost_rr.py
python3 tmp/harmonybot-v26-build/fix_v281_geometry_quality_engine.py
python3 tmp/harmonybot-v26-build/fix_v281_commercial_onepass.py
python3 tmp/harmonybot-v26-build/fix_v282_strategy_quality_rc.py
python3 tmp/harmonybot-v26-build/fix_v283_execution_quality.py
python3 tmp/harmonybot-v26-build/fix_v284_capital_aware_precision.py
python3 tmp/harmonybot-v26-build/fix_v29_persistent_prz_execution.py
python3 tmp/harmonybot-v26-build/fix_v291_small_account_execution.py
python3 tmp/harmonybot-v26-build/fix_v292_small_account_fast_execution.py
python3 tmp/harmonybot-v26-build/fix_v292_grid_lifecycle_hotfix.py
python3 tmp/harmonybot-v26-build/fix_v293_grid_risk_cap_hotfix.py
python3 "$CONTROL/tmp/harmonybot-v26-build/fix_v294_edge_context_gate.py"
python3 "$CONTROL/tmp/harmonybot-v26-build/fix_v295_thesis_validity_minimum.py"
python3 "$CONTROL/tmp/harmonybot-v26-build/fix_harmonybot_v30_commercial_architecture.py"
for x in 'V30.0-Regime-Routed-Harmonic-Portfolio-RC' 'TryDetectPortfolio' 'V30SelectPortfolioSignal' '[V30-SUMMARY]' 'V29.3 GRID-RISK-CAP-HOTFIX'; do
  grep -Fq "$x" cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs
done

mkdir -p seal/{build,algo}
cp cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs seal/build/HarmonyBotPro.cs
cat > seal/build/HarmonyBotPro.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><AlgoName>HarmonyBotPro_V30_Commercial_RC</AlgoName><AlgoBuild>true</AlgoBuild><AlgoPublish>false</AlgoPublish><IncludeSource>false</IncludeSource></PropertyGroup><ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup></Project>
EOF
dotnet restore seal/build/HarmonyBotPro.csproj
dotnet build seal/build/HarmonyBotPro.csproj -c Release --no-restore --nologo 2>&1 | tee seal/build.log
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' seal/build.log
ALGO=$(find seal/build/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" seal/algo/HarmonyBotPro_V30_Commercial_RC.algo
sha256sum seal/build/HarmonyBotPro.cs seal/algo/HarmonyBotPro_V30_Commercial_RC.algo > seal/SHA256SUMS.txt
cp seal/algo/HarmonyBotPro_V30_Commercial_RC.algo "$WORK/seal/algo/"
cp seal/SHA256SUMS.txt "$OUT/"
cp seal/build/HarmonyBotPro.cs "$OUT/HarmonyBotPro_V30_Commercial_RC.cs"
cp seal/build.log "$OUT/V30_BUILD.log"
cd "$ROOT"

run_one() {
  local run="$1" window="$2" start="$3" eval="$4" end="$5" capital="$6" datamode="$7" small="$8" years="$9"
  shift 9
  local scale="${1:-1.0}" spread="${2:-1}" commission="${3:-35}" slippage="${4:-30}"
  echo "== $run =="
  (
    cd "$WORK"
    CANDIDATE=V30 RUN_NAME="$run" START_DATE="$start" EVAL_DATE="$eval" END_DATE="$end" \
      CAPITAL="$capital" DATA_MODE="$datamode" SMALL="$small" THRESH_SCALE="$scale" SPREAD="$spread" COMMISSION="$commission" SLIPPAGE="$slippage" \
      "$CONTROL/v30/run_backtest.sh"
  )
  python3 "$CONTROL/v30/audit_report.py" --report "$WORK/seal/reports/$run.json" --log "$WORK/seal/logs/$run.log" \
    --out "$OUT/$run.json" --window "$window" --years "$years" --capital "$capital" --data-mode "$datamode"
}

stage_ok() {
  python3 - "$1" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
ok=bool(x.get("baskets",0)>0 and x.get("pf",0)>1 and x.get("expectancy",0)>0 and x.get("net",0)>0 and x.get("max_dd_pct",999)<=10 and x.get("execution_errors",999)==0)
raise SystemExit(0 if ok else 1)
PY
}

echo "== V30 Development =="
run_one "V30-DEV-A" "DEV-A" "04/01/2021" "2021-01-11T00:00:00Z" "30/06/2021" 10000 m1 false 0.5
run_one "V30-DEV-B" "DEV-B" "01/07/2021" "2021-07-08T00:00:00Z" "31/12/2021" 10000 m1 false 0.5
run_one "V30-DEV-C" "DEV-C" "03/01/2022" "2022-01-10T00:00:00Z" "30/06/2022" 10000 m1 false 0.5

rm -rf "$WORK/all"; mkdir -p "$WORK/all"
cp "$OUT"/V30-DEV-*.json "$WORK/all/"
(
  cd "$WORK"
  GITHUB_OUTPUT=/tmp/v30-gate.out python3 "$CONTROL/v30/development_gate.py"
)
cp "$WORK/V30_DEVELOPMENT_GATE.json" "$OUT/"
test ! -f "$WORK/V30_ARCHITECTURE_LIMITATION.md" || cp "$WORK/V30_ARCHITECTURE_LIMITATION.md" "$OUT/"

python3 - <<'PY'
import json,pathlib
o=pathlib.Path('control/v30-output')
xs=[json.load(open(o/f'V30-DEV-{w}.json')) for w in ('A','B','C')]
report={
 "version":"HarmonyBot V30.0",
 "root_causes_addressed":["sell_only_direction_lock","single_best_candidate_loss","legacy_mtf_double_gate","grid_primary_payoff_compression","path_dependent_pattern_auto_disable"],
 "windows":{x["window"]:{
   "pf":x["pf"],"net":x["net"],"expectancy":x["expectancy"],"win_rate_pct":x["win_rate_pct"],"realized_rr":x["realized_rr"],
   "direction":x["direction"],"pattern":x["pattern"],"v30":x["v30"]} for x in xs}
}
(o/'V30_ROOT_CAUSE_REPORT.json').write_text(json.dumps(report,indent=2))
PY

DEV_PASS=$(python3 - <<'PY'
import json
print('true' if json.load(open('control/v30-output/V30_DEVELOPMENT_GATE.json')).get('development_pass') else 'false')
PY
)
if [ "$DEV_PASS" != "true" ]; then
  finalize "STRATEGY ARCHITECTURE LIMITATION" "HarmonyBot V30.0 major architecture reset failed the hard 3-window Development gate. No post-hoc threshold tuning against DEV-A/B/C is authorised."
  exit 0
fi

echo "== One-use Validation =="
run_one "VALIDATION-V30" "VALIDATION" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 10000 m1 false 0.5
cp "$OUT/VALIDATION-V30.json" "$OUT/VALIDATION.json"
if ! stage_ok "$OUT/VALIDATION.json"; then
  finalize "HOLD" "V30.0 failed the predeclared one-use Validation. No retuning or Validation reuse."
  exit 0
fi

echo "== Real $100 FxPro execution gate (same validation market interval; execution-feasibility evidence, not independent performance evidence) =="
run_one "COMMERCIAL100-V30" "COMMERCIAL100" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 100 ticks true 0.5
cp "$OUT/COMMERCIAL100-V30.json" "$OUT/COMMERCIAL100.json"
if ! stage_ok "$OUT/COMMERCIAL100.json"; then
  finalize "HOLD" "V30.0 failed the real $100 FxPro XAUUSD 1:500 tick execution gate."
  exit 0
fi

echo "== OOS =="
run_one "OOS-V30" "OOS" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5
cp "$OUT/OOS-V30.json" "$OUT/OOS.json"
if ! stage_ok "$OUT/OOS.json"; then
  finalize "HOLD" "V30.0 failed predeclared OOS. Robustness and Final Holdout were not run."
  exit 0
fi

echo "== Walk-forward =="
run_one "WF-1" "WF1" "02/01/2019" "2019-01-09T00:00:00Z" "28/02/2019" 10000 m1 false 0.16
run_one "WF-2" "WF2" "01/03/2019" "2019-03-08T00:00:00Z" "30/04/2019" 10000 m1 false 0.17
run_one "WF-3" "WF3" "01/05/2019" "2019-05-08T00:00:00Z" "28/06/2019" 10000 m1 false 0.17

echo "== Sensitivity ±5/10/20 =="
run_one "SENS-BASE" "BASE" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.00
run_one "SENS-M20" "M20" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.80
run_one "SENS-M10" "M10" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.90
run_one "SENS-M5" "M5" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.95
run_one "SENS-P5" "P5" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.05
run_one "SENS-P10" "P10" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.10
run_one "SENS-P20" "P20" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.20

echo "== Cost stress =="
run_one "COST-SPREAD" "SPREAD150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.00 1.5 35 30
run_one "COST-COMMISSION" "COMMISSION150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.00 1 52.5 30
run_one "COST-SLIPPAGE" "SLIPPAGE150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.00 1 35 45
run_one "COST-COMBINED" "COMBINED" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.00 1.5 52.5 45

python3 "$CONTROL/v30/robustness_gate.py" --dir "$OUT" --out "$OUT/ROBUSTNESS_GATE.json"
ROBUST=$(python3 - <<'PY'
import json
print('true' if json.load(open('control/v30-output/ROBUSTNESS_GATE.json')).get('robustness_pass') else 'false')
PY
)
if [ "$ROBUST" != "true" ]; then
  finalize "HOLD" "V30.0 failed walk-forward/sensitivity/cost/Monte-Carlo robustness. Final Holdout remains untouched."
  exit 0
fi

echo "== Final Holdout once =="
run_one "FINAL-HOLDOUT-V30" "FINAL_HOLDOUT" "02/07/2018" "2018-07-09T00:00:00Z" "31/12/2018" 10000 m1 false 0.5
cp "$OUT/FINAL-HOLDOUT-V30.json" "$OUT/FINAL_HOLDOUT.json"
if ! stage_ok "$OUT/FINAL_HOLDOUT.json"; then
  finalize "HOLD" "V30.0 Final Holdout was used once and failed. No post-holdout tuning."
  exit 0
fi

python3 - <<'PY'
import json,pathlib
o=pathlib.Path('control/v30-output')
h=json.load(open(o/'FINAL_HOLDOUT.json')); c=json.load(open(o/'COMMERCIAL100.json')); v=json.load(open(o/'VALIDATION.json')); os=json.load(open(o/'OOS.json')); r=json.load(open(o/'ROBUSTNESS_GATE.json'))
months={}; months.update(v.get('monthly_net',{})); months.update(os.get('monthly_net',{}))
metrics={
 "pf":h["pf"],"win_rate_pct":h["win_rate_pct"],"realized_rr":h.get("realized_rr") or 0,
 "annualized_roi_pct":h["net"]/h["initial_capital"]/0.5*100 if h["initial_capital"] else 0,
 "profitable_months":sum(x>0 for x in months.values()),"observed_months":len(months),
 "commercial100_frequency":c["annualized_frequency"],"max_dd_pct":h["max_dd_pct"]
}
targets={"pf":2.5,"win_rate_pct":65,"realized_rr":2.0,"annualized_roi_pct":100,"profitable_months":10,"commercial100_frequency":200,"max_dd_pct":10}
achieved={
 "pf":metrics["pf"]>=2.5,"win_rate_pct":metrics["win_rate_pct"]>=65,"realized_rr":metrics["realized_rr"]>=2,
 "annualized_roi_pct":metrics["annualized_roi_pct"]>=100,"profitable_months":metrics["profitable_months"]>=10,
 "commercial100_frequency":metrics["commercial100_frequency"]>=200,"max_dd_pct":metrics["max_dd_pct"]<=10
}
status="PASS" if all(achieved.values()) else "NEAR_TARGET"
decision={"version":"HarmonyBot V30.0 Regime-Routed Harmonic Portfolio Engine","final_commercial_freeze":status,
 "mandatory_gates":{"development":"PASS","validation":"PASS","commercial100":"PASS","oos":"PASS","robustness":"PASS","final_holdout":"PASS"},
 "metrics":metrics,"targets":targets,"target_achieved":achieved,
 "robustness":{"mc_95pct_max_dd":r["mc_95pct_max_dd"],"mc_risk_of_ruin":r["mc_risk_of_ruin"]}}
(o/'FINAL_COMMERCIAL_DECISION.json').write_text(json.dumps(decision,indent=2))
gaps=[k for k,vv in achieved.items() if not vv]
(o/'FINAL_COMMERCIAL_DECISION.md').write_text("# HarmonyBot V30.0 Final Commercial Decision\n\n**"+status+"**\n\nRemaining target gaps: "+(", ".join(gaps) if gaps else "none")+"\n")
print(json.dumps(decision,indent=2))
PY

STATUS=$(python3 - <<'PY'
import json
print(json.load(open('control/v30-output/FINAL_COMMERCIAL_DECISION.json')).get('final_commercial_freeze','HOLD'))
PY
)
if [ "$STATUS" = "PASS" ] || [ "$STATUS" = "NEAR_TARGET" ]; then
  cp "$BASE/seal/algo/HarmonyBotPro_V30_Commercial_RC.algo" "$OUT/HarmonyBotPro_V30_Commercial_RC.algo"
fi
echo "V30_ONEPASS_COMPLETE status=$STATUS"
