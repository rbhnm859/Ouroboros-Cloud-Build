#!/usr/bin/env bash
set -euo pipefail

ROOT="$PWD"
BASE="$ROOT/base"
CONTROL="$ROOT/control"
WORK="$CONTROL/work"
OUT="$CONTROL/commercial-convergence-output"
mkdir -p "$WORK/seal/algo" "$OUT"

finalize() {
  local status="$1"; local reason="$2"
  python3 - "$OUT/FINAL_COMMERCIAL_DECISION.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
out={"final_commercial_freeze":status,"reason":reason}
pathlib.Path(p).write_text(json.dumps(out,indent=2))
pathlib.Path(p).with_suffix(".md").write_text(f"# HarmonyBot Final Commercial Decision\n\n**{status}**\n\n{reason}\n")
print(json.dumps(out,indent=2))
PY
}

echo "== Evidence lock =="
python3 - <<'PY'
import json
p=json.load(open('control/commercial-convergence/PRE_REGISTERED_CANDIDATES.json'))
assert p['baseline']['run_id']==35322359842
assert p['baseline']['head_sha']=='ba8caeab70fc860a68cf72270bcb4d491a90462a'
assert [x['id'] for x in p['candidates']]==['A','B','C']
assert p['final_holdout']['status'].startswith('UNTOUCHED')
print('EVIDENCE_LOCK=PASS')
PY
cp "$CONTROL/commercial-convergence/PRE_REGISTERED_CANDIDATES.json" "$OUT/"

echo "== Reconstruct frozen V29.5 + one-pass RC =="
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
python3 "$CONTROL/tmp/harmonybot-v26-build/fix_harmonybot_commercial_convergence_rc.py"
for x in 'Commercial-Convergence-One-Pass-RC' 'CommercialConvergenceMode' '[COMM-ADMISSION]' '[COMM-CONVERGENCE-SUMMARY]' 'V295ThesisGuard' 'V29.3 GRID-RISK-CAP-HOTFIX'; do
  grep -Fq "$x" cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs
done
mkdir -p seal/{build,algo}
cp cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs seal/build/HarmonyBotPro.cs
cat > seal/build/HarmonyBotPro.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><AlgoName>HarmonyBotPro_commercial_convergence_rc</AlgoName><AlgoBuild>true</AlgoBuild><AlgoPublish>false</AlgoPublish><IncludeSource>false</IncludeSource></PropertyGroup><ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup></Project>
EOF
dotnet restore seal/build/HarmonyBotPro.csproj
dotnet build seal/build/HarmonyBotPro.csproj -c Release --no-restore --nologo 2>&1 | tee seal/build.log
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' seal/build.log
ALGO=$(find seal/build/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" seal/algo/HarmonyBotPro_commercial_convergence_rc.algo
sha256sum seal/build/HarmonyBotPro.cs seal/algo/HarmonyBotPro_commercial_convergence_rc.algo > seal/SHA256SUMS.txt
cp seal/algo/HarmonyBotPro_commercial_convergence_rc.algo "$WORK/seal/algo/"
cp seal/SHA256SUMS.txt "$OUT/"
cp seal/build/HarmonyBotPro.cs "$OUT/HarmonyBotPro_commercial_convergence_rc.cs"
cd "$ROOT"

run_one() {
  local cand="$1" run="$2" window="$3" start="$4" eval="$5" end="$6" capital="$7" datamode="$8" small="$9"
  shift 9
  local years="$1" scale="${2:-1.0}" spread="${3:-1}" commission="${4:-35}" slippage="${5:-30}"
  echo "== $run =="
  (
    cd "$WORK"
    CANDIDATE="$cand" RUN_NAME="$run" START_DATE="$start" EVAL_DATE="$eval" END_DATE="$end"     CAPITAL="$capital" DATA_MODE="$datamode" SMALL="$small" THRESH_SCALE="$scale" SPREAD="$spread" COMMISSION="$commission" SLIPPAGE="$slippage"     "$CONTROL/commercial-convergence/run_backtest.sh"
  )
  python3 "$CONTROL/commercial-convergence/audit_report.py"     --report "$WORK/seal/reports/$run.json" --log "$WORK/seal/logs/$run.log" --out "$OUT/$run.json"     --candidate "$cand" --window "$window" --years "$years" --capital "$capital" --data-mode "$datamode"
}

stage_ok() {
  python3 - "$1" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
ok=bool(x.get('baskets',0)>0 and x.get('pf',0)>1 and x.get('expectancy',0)>0 and x.get('net',0)>0 and x.get('max_dd_pct',999)<=10 and x.get('execution_errors',999)==0)
raise SystemExit(0 if ok else 1)
PY
}

echo "== Development A/B/C x DEV-A/B/C =="
for C in A B C; do
  run_one "$C" "$C-DEV-A" "DEV-A" "04/01/2021" "2021-01-11T00:00:00Z" "30/06/2021" 10000 m1 false 0.5
  run_one "$C" "$C-DEV-B" "DEV-B" "01/07/2021" "2021-07-08T00:00:00Z" "31/12/2021" 10000 m1 false 0.5
  run_one "$C" "$C-DEV-C" "DEV-C" "03/01/2022" "2022-01-10T00:00:00Z" "30/06/2022" 10000 m1 false 0.5
done

rm -rf "$WORK/all"; mkdir -p "$WORK/all"
cp "$OUT"/A-DEV-*.json "$OUT"/B-DEV-*.json "$OUT"/C-DEV-*.json "$WORK/all/"
(
  cd "$WORK"
  GITHUB_OUTPUT=/tmp/commercial-dev-gate.out python3 "$CONTROL/commercial-convergence/development_gate.py"
)
cp "$WORK/DEVELOPMENT_GATE.json" "$OUT/"
test ! -f "$WORK/STRATEGY_ARCHITECTURE_LIMITATION.md" || cp "$WORK/STRATEGY_ARCHITECTURE_LIMITATION.md" "$OUT/"
WINNER=$(python3 - <<'PY'
import json
print(json.load(open('control/commercial-convergence-output/DEVELOPMENT_GATE.json')).get('winner',''))
PY
)
if [ -z "$WINNER" ]; then
  finalize "STRATEGY ARCHITECTURE LIMITATION" "None of preregistered A/B/C passed 3/3 Development PF>1, expectancy>0, DD<=10%, zero errors and >=50 baskets/year. Stop rule enforced; no further version tuning."
  exit 0
fi
echo "SELECTED_CANDIDATE=$WINNER"

run_one "$WINNER" "VALIDATION-$WINNER" "VALIDATION" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 10000 m1 false 0.5
cp "$OUT/VALIDATION-$WINNER.json" "$OUT/VALIDATION.json"
if ! stage_ok "$OUT/VALIDATION.json"; then
  finalize "HOLD" "Selected candidate failed the single predeclared Validation. No retuning or Validation reuse permitted."
  exit 0
fi

run_one "$WINNER" "COMMERCIAL100-$WINNER" "COMMERCIAL100" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 100 ticks true 0.5
cp "$OUT/COMMERCIAL100-$WINNER.json" "$OUT/COMMERCIAL100.json"
if ! stage_ok "$OUT/COMMERCIAL100.json"; then
  finalize "HOLD" "Selected candidate failed the real $100 FxPro commercial gate (positive expectancy/net, PF>1, DD<=10%, zero execution errors required)."
  exit 0
fi

run_one "$WINNER" "OOS-$WINNER" "OOS" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5
cp "$OUT/OOS-$WINNER.json" "$OUT/OOS.json"
if ! stage_ok "$OUT/OOS.json"; then
  finalize "HOLD" "Selected candidate failed predeclared OOS. No downstream robustness or Final Holdout was run."
  exit 0
fi

echo "== Sensitivity and cost robustness =="
run_one "$WINNER" "ROBUST-BASE" "BASE" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 35 30
run_one "$WINNER" "ROBUST-THRESH_MINUS10" "THRESH_MINUS10" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.9 1 35 30
run_one "$WINNER" "ROBUST-THRESH_PLUS10" "THRESH_PLUS10" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.1 1 35 30
run_one "$WINNER" "ROBUST-SPREAD_150" "SPREAD_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1.5 35 30
run_one "$WINNER" "ROBUST-COMMISSION_150" "COMMISSION_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 52.5 30
run_one "$WINNER" "ROBUST-SLIPPAGE_150" "SLIPPAGE_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 35 45
run_one "$WINNER" "ROBUST-COMBINED_COST" "COMBINED_COST" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1.5 52.5 45
python3 "$CONTROL/commercial-convergence/robustness_gate.py" --dir "$OUT" --out "$OUT/ROBUSTNESS_GATE.json"
ROBUST_OK=$(python3 - <<'PY'
import json
print('true' if json.load(open('control/commercial-convergence-output/ROBUSTNESS_GATE.json')).get('robustness_pass') else 'false')
PY
)
if [ "$ROBUST_OK" != "true" ]; then
  finalize "HOLD" "Selected candidate failed preregistered sensitivity/cost/Monte-Carlo robustness. Final Holdout remained untouched."
  exit 0
fi

run_one "$WINNER" "FINAL-HOLDOUT-$WINNER" "FINAL_HOLDOUT" "02/07/2018" "2018-07-09T00:00:00Z" "31/12/2018" 10000 m1 false 0.5
cp "$OUT/FINAL-HOLDOUT-$WINNER.json" "$OUT/FINAL_HOLDOUT.json"
if ! stage_ok "$OUT/FINAL_HOLDOUT.json"; then
  finalize "HOLD" "Final Holdout was used once and failed. No tuning after Holdout."
  exit 0
fi

python3 - "$WINNER" <<'PY'
import json,sys,pathlib
w=sys.argv[1]
outdir=pathlib.Path('control/commercial-convergence-output')
h=json.load(open(outdir/'FINAL_HOLDOUT.json')); c=json.load(open(outdir/'COMMERCIAL100.json'))
v=json.load(open(outdir/'VALIDATION.json')); o=json.load(open(outdir/'OOS.json')); r=json.load(open(outdir/'ROBUSTNESS_GATE.json'))
annual_roi=h['net']/h['initial_capital']/0.5*100 if h['initial_capital'] else 0
months={}
for src in (v,o):
    months.update(src.get('monthly_net',{}))
prof=sum(1 for x in months.values() if x>0); obs=len(months)
metrics={
  'pf':h['pf'],'win_rate_pct':h['win_rate_pct'],'realized_rr':h.get('realized_rr') or 0,'annualized_roi_pct':annual_roi,
  'profitable_months_2019':prof,'observed_months_2019':obs,'commercial_100_baskets_per_year':c['annualized_frequency'],'max_dd_pct':h['max_dd_pct']
}
targets={'pf':2.5,'win_rate_pct':65,'realized_rr':2.0,'annualized_roi_pct':100,'profitable_months_2019':10,'commercial_100_baskets_per_year':200,'max_dd_pct':10}
achieved={
 'pf':metrics['pf']>=2.5,'win_rate_pct':metrics['win_rate_pct']>=65,'realized_rr':metrics['realized_rr']>=2,
 'annualized_roi_pct':metrics['annualized_roi_pct']>=100,'profitable_months_2019':metrics['profitable_months_2019']>=10,
 'commercial_100_baskets_per_year':metrics['commercial_100_baskets_per_year']>=200,'max_dd_pct':metrics['max_dd_pct']<=10
}
status='PASS' if all(achieved.values()) else 'NEAR_TARGET'
decision={'final_commercial_freeze':status,'selected_candidate':w,'mandatory_gates':{'development':'PASS','validation':'PASS','$100':'PASS','oos':'PASS','robustness':'PASS','final_holdout':'PASS'},
          'metrics':metrics,'targets':targets,'target_achieved':achieved,'robustness':{'mc_95pct_max_dd':r['mc_95pct_max_dd'],'mc_risk_of_ruin':r['mc_risk_of_ruin']}}
(outdir/'FINAL_COMMERCIAL_DECISION.json').write_text(json.dumps(decision,indent=2))
gaps=[k for k,vv in achieved.items() if not vv]
(outdir/'FINAL_COMMERCIAL_DECISION.md').write_text('# HarmonyBot Final Commercial Decision\n\n**'+status+'**\n\nSelected candidate: '+w+'\n\nRemaining target gaps: '+(', '.join(gaps) if gaps else 'none')+'\n')
print(json.dumps(decision,indent=2))
PY

echo "ONE_PASS_COMPLETE"
