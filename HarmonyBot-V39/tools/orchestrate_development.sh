#!/usr/bin/env bash
set -euo pipefail

C="$PWD/control"
W="$C/HarmonyBot-V39/work"
O="$C/HarmonyBot-V39/output"
rm -rf "$W" "$O"
mkdir -p "$W/seal/algo" "$O/raw-logs" "$O/algo" "$O/capital" "$O/fresh"
cd "$C"

stage(){ printf '%s [V39-PROGRESS] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$O/RUN_PROGRESS.log"; }
STAGE="BOOT"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then stage "FAILED stage=${STAGE:-unknown} rc=$rc"; fi' EXIT

stage "START V39 regime-conditioned harmonic portfolio program"

STAGE="STATIC_AUDIT"
python3 HarmonyBot-V39/tools/static_audit.py HarmonyBot-V39/src/HarmonyBotV39.cs
cp V39_ARCHITECTURE_AUDIT.json "$O/"

STAGE="BUILD"
dotnet restore HarmonyBot-V39/HarmonyBotV39.csproj
dotnet build HarmonyBot-V39/HarmonyBotV39.csproj -c Release --no-restore --nologo 2>&1 | tee "$O/V39_BUILD.log"
! grep -Eq '(^|[^0-9])error (CS|MSB|NETSDK)[0-9]+' "$O/V39_BUILD.log"
ALGO=$(find HarmonyBot-V39/bin/Release -type f -name '*.algo' | head -1)
test -n "$ALGO" && test -s "$ALGO"
cp "$ALGO" "$W/seal/algo/HarmonyBot_V39_Regime_Conditioned_Harmonic_Portfolio_RC.algo"
cp "$ALGO" "$O/algo/"
sha256sum HarmonyBot-V39/src/HarmonyBotV39.cs "$ALGO" > "$O/SHA256SUMS"
printf '%s\n' "$GITHUB_SHA" > "$O/SOURCE_COMMIT.txt"
stage "BUILD PASS"

run(){
  local fam=$1 suf=$2 st=$3 ev=$4 en=$5 bal=$6 regimesel=$7 routespec=$8 stressq=$9 years=${10}
  local n="V39-${fam}-${suf}-B${bal}"
  STAGE="$n"
  stage "START $n regimeSelector=$regimesel routeSpecialization=$routespec stressQuarantine=$stressq"
  (
    cd "$W"
    RUN_NAME="$n" START_DATE="$st" EVAL_DATE="$ev" END_DATE="$en" BALANCE="$bal" \
    RECALL=true RETENTION=true AGING=true EVIDENCE=true SURVIVAL=true ARBITRATION=true \
    REGIMESEL="$regimesel" ROUTESPEC="$routespec" STRESSQ="$stressq" \
    TTL=8 MAXCAND=12 BACKTEST_TIMEOUT_SECONDS=1800 "$C/HarmonyBot-V39/tools/run_backtest.sh"
  )
  python3 "$C/HarmonyBot-V39/tools/audit_report.py" \
    --report "$W/seal/reports/$n.json" --log "$W/seal/logs/$n.log" --out "$O/$fam-$suf.json" \
    --window "$suf" --family "$fam" --years "$years" --balance "$bal"
  cp "$W/seal/logs/$n.log" "$O/raw-logs/$n.log"
  stage "DONE $n"
}

STAGE="SMOKE"
run FULL_PORTFOLIO SMOKE 04/01/2021 2021-01-11T00:00:00Z 31/01/2021 10000 true true true .075
cp "$O/FULL_PORTFOLIO-SMOKE.json" "$O/V39_SMOKE.json"
python3 - "$O/V39_SMOKE.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))
assert x["summary_present"], "missing V39 summary"
assert x["broker_profile_present"], "missing broker profile"
assert x["execution_errors"]==0
assert x["actual_basket_risk_violations"]==0
assert x["unprotected_survivors"]==0
print("[V39-SMOKE] PASS")
PY
stage "SMOKE PASS"

family(){
  local fam=$1 regimesel=$2 routespec=$3 stressq=$4
  run "$fam" A 04/01/2021 2021-01-11T00:00:00Z 30/06/2021 10000 "$regimesel" "$routespec" "$stressq" .5
  run "$fam" B 01/07/2021 2021-07-08T00:00:00Z 31/12/2021 10000 "$regimesel" "$routespec" "$stressq" .5
  run "$fam" C 03/01/2022 2022-01-10T00:00:00Z 30/06/2022 10000 "$regimesel" "$routespec" "$stressq" .5
}

STAGE="DEV_ABLATION"
family BASELINE_CONTROL false false false
family REGIME_SELECTOR true false true
family ROUTE_SPECIALIZED false true true
family FULL_PORTFOLIO true true true

STAGE="ANALYZE_DEV"
python3 - "$O" <<'PY'
import json,pathlib,sys,re
o=pathlib.Path(sys.argv[1])
fams=["BASELINE_CONTROL","REGIME_SELECTOR","ROUTE_SPECIALIZED","FULL_PORTFOLIO"]
def read(f,w): return json.load(open(o/f"{f}-{w}.json"))
def aggregate(f):
    xs=[read(f,w) for w in "ABC"]
    gp=sum(x["gross_profit"] for x in xs); gl=sum(x["gross_loss"] for x in xs)
    n=sum(x["baskets"] for x in xs); net=sum(x["net"] for x in xs); wins=sum(x["wins"] for x in xs)
    return {
      "baskets":n,"executable_baskets_per_year":n/1.5,
      "pf":gp/gl if gl else (999 if gp else 0),"net":net,"expectancy":net/n if n else 0,
      "win_rate":wins/n if n else 0,
      "positive_windows":sum(x["net"]>0 for x in xs),
      "all_windows_non_negative":all(x["net"]>=0 for x in xs),
      "worst_window_pf":min(x["pf"] for x in xs),
      "max_dd_pct":max(x["max_dd_pct"] for x in xs),
      "engineering_clean":all(x["engineering_clean"] and x["summary_present"] and x["broker_profile_present"] for x in xs),
      "portfolio_evaluated":sum(x.get("portfolio_evaluated",0) for x in xs),
      "portfolio_accepted":sum(x.get("portfolio_accepted",0) for x in xs),
      "portfolio_rejected":sum(x.get("portfolio_rejected",0) for x in xs),
      "route_specialization_rejected":sum(x.get("route_specialization_rejected",0) for x in xs),
      "stress_quarantine_rejected":sum(x.get("stress_quarantine_rejected",0) for x in xs),
      "risk_renormalizations":sum(x.get("risk_renormalizations",0) for x in xs),
      "risk_rejects":sum(x.get("risk_rejects",0) for x in xs),
      "shadow_targets":sum(x.get("shadow_targets",0) for x in xs),
      "shadow_stops":sum(x.get("shadow_stops",0) for x in xs),
      "shadow_unresolved":sum(x.get("shadow_unresolved",0) for x in xs),
      "windows":{w:read(f,w) for w in "ABC"}
    }
a={f:aggregate(f) for f in fams}
for f,v in a.items():
    v["frequency_multiple_vs_v351"]=v["executable_baskets_per_year"]/44.0 if v["executable_baskets_per_year"] else 0
    v["frequency_multiple_vs_v36_structured"]=v["executable_baskets_per_year"]/51.333333333333336 if v["executable_baskets_per_year"] else 0
    v["net_profit_gate"]=v["net"]>0 and v["all_windows_non_negative"]
    v["promotion_floor_pass"]=(v["engineering_clean"] and v["net_profit_gate"] and
       v["executable_baskets_per_year"]>=50 and v["pf"]>=1.10 and v["expectancy"]>0 and
       v["worst_window_pf"]>=0.80 and v["max_dd_pct"]<=10)
    v["major_breakthrough"]=(v["promotion_floor_pass"] and
       (v["executable_baskets_per_year"]>=100 or v["frequency_multiple_vs_v351"]>=2.0))
eligible=[(v["executable_baskets_per_year"],v["pf"],v["net"],f) for f,v in a.items() if v["promotion_floor_pass"]]
eligible.sort(reverse=True)
winner=eligible[0][-1] if eligible else None
frontier={
 "version":"HarmonyBot V39",
 "architecture":"REGIME_CONDITIONED_HARMONIC_PORTFOLIO",
 "evidence_scope":"DEV-A/B/C only; fresh validation untouched",
 "hard_requirement":"aggregate Net Profit > 0 AND each DEV window Net Profit >= 0",
 "external_baselines":{
   "V36_STRUCTURED_RECALL":{"executable_baskets_per_year":51.333333333333336,"pf":1.2124297856312334,"net":648.58,"expectancy":8.423116883116883,"max_dd_pct":8.768267223382058},
   "V38_FULL_EXECUTION":{"executable_baskets_per_year":29.333333333333332,"pf":0.8331543602647733,"net":-416.40,"expectancy":-9.463636363636367,"max_dd_pct":13.397572385793033}
 },
 "families":a,"development_candidate":winner,
 "major_breakthrough":bool(winner and a[winner]["major_breakthrough"]),
 "status":"MAJOR_BREAKTHROUGH" if winner and a[winner]["major_breakthrough"] else ("DEV_CANDIDATE" if winner else "NO_PROMOTABLE_CANDIDATE")
}
(o/"V39_PORTFOLIO_FRONTIER.json").write_text(json.dumps(frontier,indent=2))
decision={
 "version":"HarmonyBot V39","development_candidate":winner,"status":frontier["status"],
 "major_breakthrough":frontier["major_breakthrough"],
 "net_profit_gate":"REQUIRED_AND_NON_NEGOTIABLE",
 "next_stage":"CAPITAL_COMPATIBILITY" if winner else "REASSESS_PATTERN_ROUTE_REGIME_ATTRIBUTION",
 "fresh_validation_used":False,"m1_strategy_dependency":False
}
(o/"V39_PROMOTION_DECISION.json").write_text(json.dumps(decision,indent=2))

funnel={"version":"HarmonyBot V39","scope":"DEV-A/B/C","families":{}}
for f in fams:
    z={"detected":0,"validated":0,"routed":0,"prz":0,"confirming":0,"armed":0,"basket_planned":0,"executed":0,"rejected":0,"expired":0,"invalidated":0}
    for w in "ABC":
        t=(o/"raw-logs"/f"V39-{f}-{w}-B10000.log").read_text(errors="ignore")
        matches=re.findall(r"\[V39-PIPELINE\].*?detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+armed=(\d+)\s+basketPlanned=(\d+).*?executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)",t)
        for m in matches:
            for k,val in zip(["detected","validated","routed","prz","confirming","armed","basket_planned","executed","expired","rejected","invalidated"],map(int,m)):
                z[k]+=val
    funnel["families"][f]=z
(o/"V39_SIGNAL_TRADE_FUNNEL.json").write_text(json.dumps(funnel,indent=2))
print(json.dumps(frontier,indent=2))
print(json.dumps(decision,indent=2))
print(json.dumps(funnel,indent=2))
PY

CAND=$(python3 - "$O/V39_PROMOTION_DECISION.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1])).get("development_candidate") or "")
PY
)

if [ -n "$CAND" ]; then
  STAGE="CAPITAL_COMPATIBILITY"
  case "$CAND" in
    BASELINE_CONTROL) RS=false; RT=false; SQ=false;;
    REGIME_SELECTOR) RS=true; RT=false; SQ=true;;
    ROUTE_SPECIALIZED) RS=false; RT=true; SQ=true;;
    FULL_PORTFOLIO) RS=true; RT=true; SQ=true;;
    *) echo "unknown candidate $CAND"; exit 31;;
  esac
  for BAL in 100 150 200 300 500 1000; do
    run "$CAND" "CAPITAL_$BAL" 04/01/2021 2021-01-11T00:00:00Z 30/06/2022 "$BAL" "$RS" "$RT" "$SQ" 1.5
    cp "$O/$CAND-CAPITAL_$BAL.json" "$O/capital/$BAL.json"
  done
  python3 - "$O" "$CAND" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1]); cand=sys.argv[2]
rows={str(b):json.load(open(o/"capital"/f"{b}.json")) for b in [100,150,200,300,500,1000]}
h=rows["100"]
ok=(h["engineering_clean"] and h["baskets"]>0 and h["net"]>0 and h["expectancy"]>0 and
    h["max_dd_pct"]<=10 and h["actual_basket_risk_violations"]==0 and h["margin_risk_violations"]==0)
out={"version":"HarmonyBot V39","candidate":cand,"rows":rows,"hard_100_compatible":ok,
     "net_profit_requirement":"$100 Net Profit > 0","status":"CAPITAL_COMPATIBLE" if ok else "CAPITAL_HOLD"}
(o/"V39_CAPITAL_COMPATIBILITY.json").write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
PY
  CAPOK=$(python3 - "$O/V39_CAPITAL_COMPATIBILITY.json" <<'PY'
import json,sys
print("true" if json.load(open(sys.argv[1]))["hard_100_compatible"] else "false")
PY
)
  if [ "$CAPOK" = true ]; then
    STAGE="FREEZE"
    python3 - "$O" "$CAND" "$GITHUB_SHA" <<'PY'
import json,pathlib,sys,hashlib
o=pathlib.Path(sys.argv[1]); cand=sys.argv[2]; sha=sys.argv[3]
src=pathlib.Path("HarmonyBot-V39/src/HarmonyBotV39.cs"); algo=next((o/"algo").glob("*.algo"))
m={"version":"HarmonyBot V39","candidate":cand,"source_commit":sha,
   "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
   "algo_sha256":hashlib.sha256(algo.read_bytes()).hexdigest(),
   "net_profit_gate":"NON_NEGOTIABLE_POSITIVE",
   "fresh_validation_tuning":False,"status":"ALPHA_AND_CAPITAL_FROZEN"}
(o/"V39_FREEZE_MANIFEST.json").write_text(json.dumps(m,indent=2)); print(json.dumps(m,indent=2))
PY
    STAGE="FRESH_VALIDATION"
    run "$CAND" FRESH_ALPHA 02/01/2020 2020-01-09T00:00:00Z 30/06/2020 10000 "$RS" "$RT" "$SQ" .5
    run "$CAND" FRESH_100 02/01/2020 2020-01-09T00:00:00Z 30/06/2020 100 "$RS" "$RT" "$SQ" .5
    cp "$O/$CAND-FRESH_ALPHA.json" "$O/fresh/alpha.json"
    cp "$O/$CAND-FRESH_100.json" "$O/fresh/100.json"
    python3 - "$O" "$CAND" <<'PY'
import json,pathlib,sys
o=pathlib.Path(sys.argv[1]); cand=sys.argv[2]
a=json.load(open(o/"fresh"/"alpha.json")); m=json.load(open(o/"fresh"/"100.json"))
ok=(a["engineering_clean"] and a["baskets"]>0 and a["net"]>0 and a["expectancy"]>0 and a["pf"]>1 and a["max_dd_pct"]<=10 and
    m["engineering_clean"] and m["baskets"]>0 and m["net"]>0 and m["expectancy"]>0 and m["pf"]>1 and m["max_dd_pct"]<=10)
out={"version":"HarmonyBot V39","candidate":cand,"fresh_alpha":a,"fresh_100":m,
     "fresh_validation_pass":ok,"net_profit_requirement":"positive in both fresh runs",
     "commercial_release_decision":"PASS_TO_FINAL_REGRESSION" if ok else "HOLD"}
(o/"V39_FRESH_VALIDATION.json").write_text(json.dumps(out,indent=2))
(o/"V39_COMMERCIAL_RELEASE_DECISION.json").write_text(json.dumps({
 "version":"HarmonyBot V39","candidate":cand,"decision":out["commercial_release_decision"],
 "reason":"frozen DEV + positive-net $100 compatibility + untouched positive-net fresh validation"
},indent=2))
print(json.dumps(out,indent=2))
PY
  fi
fi

stage "COMPLETE V39 program"
