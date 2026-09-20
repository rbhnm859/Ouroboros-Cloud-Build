#!/usr/bin/env bash
set -euo pipefail

C="$PWD/control"
W="$C/HarmonyBot-V37/work"
O="$C/HarmonyBot-V37/output"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$O/raw-logs" "$O/algo"
cd "$C"

stage(){ printf '%s [V37-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
STAGE="BOOT"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then stage "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT

stage "START V37 M15 intraday harmonic portfolio program"

STAGE="STATIC_AUDIT"
python3 HarmonyBot-V37/tools/static_audit.py HarmonyBot-V37/src/HarmonyBotV37.cs
cp V37_ARCHITECTURE_AUDIT.json "$O/"

STAGE="BUILD"
dotnet restore HarmonyBot-V37/HarmonyBotV37.csproj
dotnet build HarmonyBot-V37/HarmonyBotV37.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V37_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V37_BUILD.log"
ALGO=$(find HarmonyBot-V37/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V37_M15_Intraday_Harmonic_Portfolio_RC.algo"
cp "$ALGO" "$O/algo/"
sha256sum HarmonyBot-V37/src/HarmonyBotV37.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"
stage "BUILD PASS"

run(){
  local fam=$1 suf=$2 st=$3 ev=$4 en=$5 recall=$6 qreroute=$7 m5refine=$8 ttl=$9 maxc=${10}
  local n="V37-${fam}-${suf}"
  STAGE="$n"
  stage "START $n recall=$recall qreroute=$qreroute m5refine=$m5refine ttl=$ttl maxCandidates=$maxc"
  (
    cd "$W"
    RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE=10000 \
    RECALL="$recall" QREROUTE="$qreroute" M5REFINE="$m5refine" TTL="$ttl" MAXCAND="$maxc" \
    BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V37/tools/run_backtest.sh"
  )
  python3 "$C/HarmonyBot-V37/tools/audit_report.py" \
    --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/$fam-$suf.json" \
    --window "$suf" --family "$fam" --years .5 --balance 10000
  cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
  stage "DONE $n"
}

# Fail-fast smoke: short sample, infrastructure only. It must compile, emit a report and stay engineering clean.
STAGE="SMOKE"
(
  cd "$W"
  RUN_NAME="V37-SMOKE" START_DATE="04/01/2021" EVAL_DATE="2021-01-11T00:00:00Z" END_DATE="31/01/2021" BALANCE=10000 \
  RECALL=true QREROUTE=false M5REFINE=false TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=900 \
  "$C/HarmonyBot-V37/tools/run_backtest.sh"
)
python3 "$C/HarmonyBot-V37/tools/audit_report.py" \
  --report "$W/seal/reports/V37-SMOKE.json" --log "$W/seal/logs/V37-SMOKE.log" --out "$O/V37_SMOKE.json" \
  --window SMOKE --family M15_CORE --years .075 --balance 10000
cp "$W/seal/logs/V37-SMOKE.log" "$O/raw-logs/V37-SMOKE.log"
python3 - "$O/V37_SMOKE.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x["summary_present"], "missing V37 summary"
assert x["broker_profile_present"], "missing broker profile"
assert x["execution_errors"]==0, "execution errors in smoke"
assert x["engineering_clean"], "engineering cleanliness failed"
print("[V37-SMOKE] PASS")
PY
stage "SMOKE PASS"

family(){
  local fam=$1 recall=$2 qreroute=$3 m5refine=$4
  run "$fam" A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 "$recall" "$qreroute" "$m5refine" 8 12
  run "$fam" B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 "$recall" "$qreroute" "$m5refine" 8 12
  run "$fam" C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 "$recall" "$qreroute" "$m5refine" 8 12
}

STAGE="DEV_ABLATION"
family M15_CORE true false false
family M15_QUALIFIED_REROUTE true true false
family M15_M5_REFINEMENT true false true
family M15_COMBINED true true true

STAGE="ANALYZE"
python3 - "$O" <<'PY'
import json,pathlib,sys,re
o=pathlib.Path(sys.argv[1])
fams=["M15_CORE","M15_QUALIFIED_REROUTE","M15_M5_REFINEMENT","M15_COMBINED"]
def read(f,w): return json.load(open(o/f"{f}-{w}.json"))
def aggregate(f):
    xs=[read(f,w) for w in "ABC"]
    gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
    n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs)
    pf=gp/gl if gl else (999 if gp else 0)
    wins=sum(x["wins"] for x in xs)
    return {
      "baskets":n,
      "executable_baskets_per_year":n/1.5,
      "pf":pf,
      "net":net,
      "expectancy":net/n if n else 0,
      "win_rate":wins/n if n else 0,
      "positive_windows":sum(x["net"]>0 for x in xs),
      "worst_window_pf":min(x["pf"] for x in xs),
      "max_dd_pct":max(x["max_dd_pct"] for x in xs),
      "engineering_clean":all(x["engineering_clean"] and x["summary_present"] and x["broker_profile_present"] for x in xs),
      "scheduler_deferred":sum(x.get("scheduler_deferred",0) for x in xs),
      "scheduler_recovered_executions":sum(x.get("scheduler_recovered_executions",0) for x in xs),
      "structured_recall_admitted":sum(x.get("structured_recall_admitted",0) for x in xs),
      "windows":{w:read(f,w) for w in "ABC"}
    }
a={f:aggregate(f) for f in fams}
baseline={
 "V35_1_EXHAUSTION":{"executable_baskets_per_year":44.0,"pf":1.1669391825879287,"net":492.11,"expectancy":7.456212121212121,"max_dd_pct":8.036681195780787,"worst_window_pf":0.8881111299339318},
 "V36_STRUCTURED_RECALL":{"executable_baskets_per_year":51.333333333333336,"pf":1.2124297856312334,"net":648.58,"expectancy":8.423116883116883,"max_dd_pct":8.768267223382058,"worst_window_pf":0.872942356673376}
}
for f,v in a.items():
    v["frequency_multiple_vs_v351"]=v["executable_baskets_per_year"]/44.0 if v["executable_baskets_per_year"] else 0
    v["frequency_multiple_vs_v36_structured"]=v["executable_baskets_per_year"]/51.333333333333336 if v["executable_baskets_per_year"] else 0
    v["quality_floor_pass"]=(v["engineering_clean"] and v["net"]>0 and v["expectancy"]>=5.0 and v["pf"]>=1.10 and
                             v["positive_windows"]>=2 and v["worst_window_pf"]>=0.80 and v["max_dd_pct"]<=10)
    v["major_breakthrough"]=(v["quality_floor_pass"] and
                             (v["executable_baskets_per_year"]>=100 or v["frequency_multiple_vs_v351"]>=2.0))
eligible=[(v["executable_baskets_per_year"],v["pf"],v["expectancy"],f) for f,v in a.items() if v["quality_floor_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None
frontier={
 "version":"HarmonyBot V37",
 "architecture":"M15_INTRADAY_HARMONIC_PORTFOLIO",
 "evidence_scope":"DEV-A/B/C only; fresh validation untouched",
 "external_baselines":baseline,
 "families":a,
 "development_candidate":winner,
 "major_breakthrough":bool(winner and a[winner]["major_breakthrough"]),
 "status":"MAJOR_BREAKTHROUGH" if winner and a[winner]["major_breakthrough"] else ("DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE")
}
(o/"V37_INTRADAY_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={
 "version":"HarmonyBot V37",
 "development_candidate":winner,
 "major_breakthrough":frontier["major_breakthrough"],
 "status":frontier["status"],
 "next_stage":"CAPITAL_COMPATIBILITY_THEN_FRESH_VALIDATION_GOVERNANCE" if winner else "REASSESS_M15_SIGNAL_TO_TRADE_BOTTLENECKS",
 "fresh_validation_used":False,
 "m1_strategy_dependency":False
}
(o/"V37_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))

# Signal-to-trade funnel from final summaries in logs.
funnel={"version":"HarmonyBot V37","scope":"DEV-A/B/C","families":{}}
for f in fams:
    z={"detected":0,"validated":0,"routed":0,"prz":0,"confirming":0,"armed":0,"basket_planned":0,"executed":0,"rejected":0,"expired":0,"invalidated":0}
    for w in "ABC":
        t=(o/"raw-logs"/f"V37-{f}-{w}.log").read_text(errors="ignore")
        matches=re.findall(r"\[V37-PIPELINE\].*?detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+).*?executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)",t)
        for m in matches:
            vals=list(map(int,m))
            for k,val in zip(["detected","validated","routed","prz","confirming","armed","basket_planned","executed","expired","rejected","invalidated"],vals):
                z[k]+=val
    funnel["families"][f]=z
(o/"V37_SIGNAL_TRADE_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
print(json.dumps(frontier,indent=2))
print(json.dumps(decision,indent=2))
print(json.dumps(funnel,indent=2))
PY

stage "COMPLETE V37 M15 intraday DEV program"
