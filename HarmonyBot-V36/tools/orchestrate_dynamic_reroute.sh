#!/usr/bin/env bash
set -euo pipefail
C="$PWD/control"; W="$C/HarmonyBot-V36/work-reroute"; O="$C/HarmonyBot-V36/output-reroute"
rm -rf "$W" "$O"; mkdir -p "$W/seal/algo" "$O/raw-logs"; cd "$C"
python3 HarmonyBot-V36/tools/apply_dynamic_reroute_retention.py
python3 HarmonyBot-V36/tools/static_audit.py HarmonyBot-V36/src/HarmonyBotV36.cs
cp V36_ARCHITECTURE_AUDIT.json "$O/"
dotnet restore HarmonyBot-V36/HarmonyBotV36.csproj
dotnet build HarmonyBot-V36/HarmonyBotV36.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V36_DYNAMIC_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V36_DYNAMIC_BUILD.log"
ALGO=$(find HarmonyBot-V36/bin/Release -type f -name '*.algo' | head -1); test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V36_Dynamic_Reroute_RC.algo"
sha256sum HarmonyBot-V36/src/HarmonyBotV36.cs "$ALGO" > "$O/SHA256SUMS"; printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"
run(){ local w=$1 st=$2 ev=$3 en=$4; local n="V36-DYNAMIC_REROUTE-$w"; (cd "$W"; RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE=10000 BACKTEST_TIMEOUT_SECONDS=2700 "$C/HarmonyBot-V36/tools/run_dynamic_reroute_backtest.sh"); python3 "$C/HarmonyBot-V36/tools/audit_report.py" --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/DYNAMIC_REROUTE-$w.json" --window "$w" --family DYNAMIC_REROUTE --years .5 --balance 10000; cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"; }
run A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021
run B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021
run C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022
python3 - "$O" <<'PY'
import json,pathlib,re,sys
o=pathlib.Path(sys.argv[1]); xs=[json.load(open(o/f'DYNAMIC_REROUTE-{w}.json')) for w in 'ABC']
gp=sum(x['gross_profit'] for x in xs); gl=sum(x['gross_loss'] for x in xs); n=sum(x['baskets'] for x in xs); net=sum(x['net'] for x in xs)
route_deferred=route_recovered=0
for w in 'ABC':
 t=(o/'raw-logs'/f'V36-DYNAMIC_REROUTE-{w}.log').read_text(errors='ignore')
 route_recovered+=len(re.findall(r'\[V36-DYNAMIC-REROUTE\]',t))
 m=re.findall(r'\[V36-FREQUENCY-SUMMARY\].*?routeDeferred=(\d+)\s+routeRecovered=(\d+)',t)
 if m: route_deferred+=int(m[-1][0])
r={'version':'HarmonyBot V36','family':'DYNAMIC_REROUTE','baskets':n,'executable_baskets_per_year':n/1.5,'pf':gp/gl if gl else 999,'net':net,'expectancy':net/n if n else 0,'win_rate':sum(x['wins'] for x in xs)/n if n else 0,'positive_windows':sum(x['net']>0 for x in xs),'worst_window_pf':min(x['pf'] for x in xs),'max_dd_pct':max(x['max_dd_pct'] for x in xs),'engineering_clean':all(x['engineering_clean'] for x in xs),'route_deferred':route_deferred,'route_recovered':route_recovered,'frequency_multiple_vs_v351':(n/1.5)/44.0,'windows':{w:x for w,x in zip('ABC',xs)}}
r['robust_positive_edge']=r['engineering_clean'] and r['net']>0 and r['expectancy']>0 and r['pf']>=1 and r['positive_windows']>=2 and r['worst_window_pf']>=.75 and r['max_dd_pct']<=10
r['major_breakthrough']=r['robust_positive_edge'] and (r['executable_baskets_per_year']>=100 or r['frequency_multiple_vs_v351']>=2)
r['status']='MAJOR_BREAKTHROUGH' if r['major_breakthrough'] else ('RELATIVE_ADVANCE' if r['robust_positive_edge'] and r['executable_baskets_per_year']>=55 else 'NO_PROMOTION')
(o/'V36_DYNAMIC_REROUTE_RESULT.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
PY
