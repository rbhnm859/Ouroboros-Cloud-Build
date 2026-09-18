#!/usr/bin/env bash
set -euo pipefail
ROOT="$PWD"; BASE="$ROOT/base"; CONTROL="$ROOT/control"; WORK="$CONTROL/final-freeze-work"; OUT="$CONTROL/final-freeze-output"
mkdir -p "$WORK/seal/algo" "$OUT"

finalize() {
  local status="$1"; local reason="$2"
  python3 - "$OUT/FINAL_COMMERCIAL_FREEZE_DECISION.json" "$status" "$reason" <<'PY'
import json,sys,pathlib
p,status,reason=sys.argv[1:4]
out={"final_commercial_freeze":status,"reason":reason}
pathlib.Path(p).write_text(json.dumps(out,indent=2))
pathlib.Path(p).with_suffix(".md").write_text(f"# HarmonyBot Final Commercial Freeze\n\n**{status}**\n\n{reason}\n")
print(json.dumps(out,indent=2))
PY
}

echo "== Evidence/preregistration lock =="
python3 - <<'PY'
import json
p=json.load(open('control/commercial-freeze-final/PRE_REGISTERED_FINAL_ARCHITECTURE.json'))
assert p['source_evidence']['commercial_convergence_run']==35338325244
assert [x['id'] for x in p['profiles']]==['P1','P2','P3']
assert p['final_holdout']['status'].startswith('UNTOUCHED')
print('FINAL_PREREG_LOCK=PASS')
PY
cp "$CONTROL/commercial-freeze-final/PRE_REGISTERED_FINAL_ARCHITECTURE.json" "$OUT/"

echo "== Reconstruct frozen engineering + final edge architecture =="
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
python3 "$CONTROL/tmp/harmonybot-v26-build/fix_final_commercial_freeze_architecture.py"
for x in 'Final-Commercial-Freeze-Architecture-RC' 'FinalEdgeArchitecture' 'FinalPureStructuralPayoff' '[FINAL-EDGE]' '[FINAL-EDGE-SUMMARY]' 'V29.3 GRID-RISK-CAP-HOTFIX'; do
  grep -Fq "$x" cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs
done
mkdir -p seal/{build,algo}
cp cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs seal/build/HarmonyBotPro.cs
cat > seal/build/HarmonyBotPro.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net6.0</TargetFramework><ImplicitUsings>disable</ImplicitUsings><Nullable>disable</Nullable><AlgoName>HarmonyBotPro_final_commercial_freeze</AlgoName><AlgoBuild>true</AlgoBuild><AlgoPublish>false</AlgoPublish><IncludeSource>false</IncludeSource></PropertyGroup><ItemGroup><PackageReference Include="cTrader.Automate" Version="1.0.19" /></ItemGroup></Project>
EOF
dotnet restore seal/build/HarmonyBotPro.csproj
dotnet build seal/build/HarmonyBotPro.csproj -c Release --no-restore --nologo 2>&1 | tee seal/build.log
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' seal/build.log
ALGO=$(find seal/build/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" seal/algo/HarmonyBotPro_final_commercial_freeze.algo
sha256sum seal/build/HarmonyBotPro.cs seal/algo/HarmonyBotPro_final_commercial_freeze.algo > seal/SHA256SUMS.txt
cp seal/algo/HarmonyBotPro_final_commercial_freeze.algo "$WORK/seal/algo/"
cp seal/SHA256SUMS.txt "$OUT/"; cp seal/build/HarmonyBotPro.cs "$OUT/HarmonyBotPro_final_commercial_freeze.cs"
cd "$ROOT"

run_one() {
  local profile="$1" run="$2" window="$3" start="$4" eval="$5" end="$6" capital="$7" datamode="$8" small="$9"
  shift 9
  local years="$1" qscale="${2:-1.0}" spread="${3:-1}" commission="${4:-35}" slippage="${5:-30}"
  echo "== $run =="
  (
    cd "$WORK"
    PROFILE="$profile" RUN_NAME="$run" START_DATE="$start" EVAL_DATE="$eval" END_DATE="$end" CAPITAL="$capital" DATA_MODE="$datamode" SMALL="$small"       QUALITY_SCALE="$qscale" SPREAD="$spread" COMMISSION="$commission" SLIPPAGE="$slippage" "$CONTROL/commercial-freeze-final/run_final_backtest.sh"
  )
  python3 "$CONTROL/commercial-freeze-final/audit_final.py" --report "$WORK/seal/reports/$run.json" --log "$WORK/seal/logs/$run.log" --out "$OUT/$run.json"     --profile "$profile" --window "$window" --years "$years" --capital "$capital" --data-mode "$datamode"
}

stage_ok() {
  python3 - "$1" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
ok=bool(x.get('baskets',0)>0 and x.get('pf',0)>1 and x.get('expectancy',0)>0 and x.get('net',0)>0 and x.get('max_dd_pct',999)<=10 and x.get('execution_errors',999)==0)
raise SystemExit(0 if ok else 1)
PY
}

echo "== Final profiles P1/P2/P3 x DEV-A/B/C =="
for P in P1 P2 P3; do
  run_one "$P" "$P-DEV-A" "DEV-A" "04/01/2021" "2021-01-11T00:00:00Z" "30/06/2021" 10000 m1 false 0.5
  run_one "$P" "$P-DEV-B" "DEV-B" "01/07/2021" "2021-07-08T00:00:00Z" "31/12/2021" 10000 m1 false 0.5
  run_one "$P" "$P-DEV-C" "DEV-C" "03/01/2022" "2022-01-10T00:00:00Z" "30/06/2022" 10000 m1 false 0.5
done
rm -rf "$WORK/all"; mkdir -p "$WORK/all"; cp "$OUT"/P?-DEV-*.json "$WORK/all/"
(
 cd "$WORK"; GITHUB_OUTPUT=/tmp/final-dev-gate.out python3 "$CONTROL/commercial-freeze-final/development_gate_final.py"
)
cp "$WORK/FINAL_DEVELOPMENT_GATE.json" "$OUT/"
test ! -f "$WORK/FINAL_STRATEGY_ARCHITECTURE_LIMITATION.md" || cp "$WORK/FINAL_STRATEGY_ARCHITECTURE_LIMITATION.md" "$OUT/"
WINNER=$(python3 - <<'PY'
import json
print(json.load(open('control/final-freeze-output/FINAL_DEVELOPMENT_GATE.json')).get('winner',''))
PY
)
if [ -z "$WINNER" ]; then
  finalize "STRATEGY_ARCHITECTURE_LIMITATION" "No preregistered final architecture profile passed 3/3 Development PF>1, positive expectancy/net, DD<=10%, zero errors and >=50 baskets/year. Final Holdout remains untouched."
  exit 0
fi
echo "SELECTED_FINAL_PROFILE=$WINNER"

run_one "$WINNER" "VALIDATION-$WINNER" "VALIDATION" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 10000 m1 false 0.5
cp "$OUT/VALIDATION-$WINNER.json" "$OUT/VALIDATION.json"
if ! stage_ok "$OUT/VALIDATION.json"; then finalize "HOLD" "Winner failed untouched Validation; no retuning or reuse."; exit 0; fi

run_one "$WINNER" "COMMERCIAL100-$WINNER" "COMMERCIAL100" "01/07/2019" "2019-07-08T00:00:00Z" "31/12/2019" 100 ticks true 0.5
cp "$OUT/COMMERCIAL100-$WINNER.json" "$OUT/COMMERCIAL100.json"
if ! stage_ok "$OUT/COMMERCIAL100.json"; then finalize "HOLD" "Winner failed real $100 FxPro XAUUSD 1:500 tick gate."; exit 0; fi

run_one "$WINNER" "OOS-$WINNER" "OOS" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5
cp "$OUT/OOS-$WINNER.json" "$OUT/OOS.json"
if ! stage_ok "$OUT/OOS.json"; then finalize "HOLD" "Winner failed untouched OOS; Final Holdout remains untouched."; exit 0; fi

echo "== Historical walk-forward stress (2020 exposed period, not holdout) =="
run_one "$WINNER" "WF-2020-H1" "WF_2020_H1" "02/01/2020" "2020-01-09T00:00:00Z" "30/06/2020" 10000 m1 false 0.5
run_one "$WINNER" "WF-2020-H2" "WF_2020_H2" "01/07/2020" "2020-07-08T00:00:00Z" "31/12/2020" 10000 m1 false 0.5
python3 - <<'PY'
import json,pathlib
xs=[json.load(open('control/final-freeze-output/WF-2020-H1.json')),json.load(open('control/final-freeze-output/WF-2020-H2.json'))]
gp=sum(x['gross_profit'] for x in xs); gl=sum(x['gross_loss'] for x in xs); net=sum(x['net'] for x in xs); n=sum(x['baskets'] for x in xs)
out={'rows':xs,'aggregate_pf':gp/gl if gl else (999 if gp else 0),'aggregate_net':net,'aggregate_expectancy':net/n if n else 0,
     'max_dd_pct':max(x['max_dd_pct'] for x in xs),'walk_forward_pass':all(x['execution_errors']==0 and x['max_dd_pct']<=10 for x in xs) and net>0 and (gp/gl if gl else 0)>1}
pathlib.Path('control/final-freeze-output/WALK_FORWARD_GATE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
PY
WF_OK=$(python3 - <<'PY'
import json
print('true' if json.load(open('control/final-freeze-output/WALK_FORWARD_GATE.json')).get('walk_forward_pass') else 'false')
PY
)
if [ "$WF_OK" != "true" ]; then finalize "HOLD" "Winner failed 2020 historical walk-forward stress."; exit 0; fi

echo "== Quality sensitivity + cost robustness =="
run_one "$WINNER" "ROBUST-BASE" "BASE" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_080" "QUALITY_080" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.80 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_090" "QUALITY_090" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.90 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_095" "QUALITY_095" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 0.95 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_105" "QUALITY_105" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.05 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_110" "QUALITY_110" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.10 1 35 30
run_one "$WINNER" "ROBUST-QUALITY_120" "QUALITY_120" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.20 1 35 30
run_one "$WINNER" "ROBUST-SPREAD_150" "SPREAD_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1.5 35 30
run_one "$WINNER" "ROBUST-COMMISSION_150" "COMMISSION_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 52.5 30
run_one "$WINNER" "ROBUST-SLIPPAGE_150" "SLIPPAGE_150" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1 35 45
run_one "$WINNER" "ROBUST-COMBINED_COST" "COMBINED_COST" "02/01/2019" "2019-01-09T00:00:00Z" "28/06/2019" 10000 m1 false 0.5 1.0 1.5 52.5 45
python3 "$CONTROL/commercial-freeze-final/robustness_final.py" --dir "$OUT" --out "$OUT/FINAL_ROBUSTNESS_GATE.json"
ROBUST_OK=$(python3 - <<'PY'
import json
print('true' if json.load(open('control/final-freeze-output/FINAL_ROBUSTNESS_GATE.json')).get('robustness_pass') else 'false')
PY
)
if [ "$ROBUST_OK" != "true" ]; then finalize "HOLD" "Winner failed sensitivity/cost/Monte-Carlo robustness; Final Holdout remains untouched."; exit 0; fi

run_one "$WINNER" "FINAL-HOLDOUT-$WINNER" "FINAL_HOLDOUT" "02/07/2018" "2018-07-09T00:00:00Z" "31/12/2018" 10000 m1 false 0.5
cp "$OUT/FINAL-HOLDOUT-$WINNER.json" "$OUT/FINAL_HOLDOUT.json"
if ! stage_ok "$OUT/FINAL_HOLDOUT.json"; then finalize "HOLD" "Final Holdout used once and failed. No post-holdout tuning."; exit 0; fi

python3 - "$WINNER" <<'PY'
import json,sys,pathlib
p=sys.argv[1]; o=pathlib.Path('control/final-freeze-output')
h=json.load(open(o/'FINAL_HOLDOUT.json')); c=json.load(open(o/'COMMERCIAL100.json')); v=json.load(open(o/'VALIDATION.json')); z=json.load(open(o/'OOS.json')); r=json.load(open(o/'FINAL_ROBUSTNESS_GATE.json'))
annual_roi=h['net']/h['initial_capital']/0.5*100 if h['initial_capital'] else 0
months={}; months.update(v.get('monthly_net',{})); months.update(z.get('monthly_net',{}))
metrics={'pf':h['pf'],'win_rate_pct':h['win_rate_pct'],'realized_rr':h.get('realized_rr') or 0,'annualized_roi_pct':annual_roi,
         'profitable_months_2019':sum(1 for x in months.values() if x>0),'observed_months_2019':len(months),
         'commercial_100_baskets_per_year':c['annualized_frequency'],'max_dd_pct':h['max_dd_pct']}
target={'pf':2.5,'win_rate_pct':65,'realized_rr':2.0,'annualized_roi_pct':100,'profitable_months_2019':10,'commercial_100_baskets_per_year':200,'max_dd_pct':10}
ach={'pf':metrics['pf']>=2.5,'win_rate_pct':metrics['win_rate_pct']>=65,'realized_rr':metrics['realized_rr']>=2,
     'annualized_roi_pct':metrics['annualized_roi_pct']>=100,'profitable_months_2019':metrics['profitable_months_2019']>=10,
     'commercial_100_baskets_per_year':metrics['commercial_100_baskets_per_year']>=200,'max_dd_pct':metrics['max_dd_pct']<=10}
near=metrics['pf']>=1.5 and metrics['realized_rr']>=1.5 and metrics['annualized_roi_pct']>=30 and metrics['commercial_100_baskets_per_year']>=75 and metrics['max_dd_pct']<=10
status='PASS' if all(ach.values()) else ('NEAR_TARGET' if near else 'HOLD')
out={'final_commercial_freeze':status,'selected_profile':p,'mandatory_gates':{'development':'PASS','validation':'PASS','$100':'PASS','oos':'PASS','walk_forward':'PASS','robustness':'PASS','final_holdout':'PASS'},
     'metrics':metrics,'targets':target,'target_achieved':ach,'robustness':{'mc_95pct_max_dd':r['mc_95pct_max_dd'],'mc_risk_of_ruin':r['mc_risk_of_ruin']}}
(o/'FINAL_COMMERCIAL_FREEZE_DECISION.json').write_text(json.dumps(out,indent=2))
gaps=[k for k,vv in ach.items() if not vv]
(o/'FINAL_COMMERCIAL_FREEZE_DECISION.md').write_text('# HarmonyBot Final Commercial Freeze\n\n**'+status+'**\n\nSelected profile: '+p+'\n\nRemaining target gaps: '+(', '.join(gaps) if gaps else 'none')+'\n')
print(json.dumps(out,indent=2))
PY
STATUS=$(python3 - <<'PY'
import json
print(json.load(open('control/final-freeze-output/FINAL_COMMERCIAL_FREEZE_DECISION.json')).get('final_commercial_freeze','HOLD'))
PY
)
if [ "$STATUS" = "PASS" ] || [ "$STATUS" = "NEAR_TARGET" ]; then
  cp "$BASE/seal/algo/HarmonyBotPro_final_commercial_freeze.algo" "$OUT/HarmonyBotPro_FINAL_COMMERCIAL_FREEZE.algo"
fi
echo "FINAL_ONE_PASS_COMPLETE status=$STATUS"
