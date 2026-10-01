#!/usr/bin/env python3
import json,pathlib,sys,math,collections,statistics
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
V=["A_V68_TRUTH_CONTROL","B_EQUAL_VISIBILITY_SHADOW"]
W=["Y2021","Y2022","Y2023","H2024H2","H2025H1","H2025H2"]
DUR={"Y2021":1.0,"Y2022":1.0,"Y2023":1.0,"H2024H2":.5,"H2025H1":.5,"H2025H2":.5}; YEARS=sum(DUR.values())
F=["Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"]
def find(name):
    xs=list(root.rglob(name))
    if len(xs)!=1: raise SystemExit(f"missing-or-duplicate {name}: {len(xs)}")
    return xs[0]
def rd(v,w): return json.load(open(find(f"{v}-{w}.json")))
def sig(d): return [(r.get("direction",""),int(r.get("entry_time") or 0),int(r.get("close_time") or 0),round(float(r.get("net",0)),2),int(r.get("fragments",0))) for r in d.get("basket_outcomes",[])]
def pf_r(xs):
    gp=sum(x for x in xs if x>0); gl=-sum(x for x in xs if x<0)
    return gp/gl if gl else (999 if gp else 0)
wins={(v,w):rd(v,w) for v in V for w in W}
truth={}; truth_ok=True
for w in W:
    a=wins[(V[0],w)]; b=wins[(V[1],w)]
    checks={"baskets":a["baskets"]==b["baskets"],"fragments":a["report_history_fragments"]==b["report_history_fragments"],
      "net":abs(a["net"]-b["net"])<=.05,"pf":abs(a["pf"]-b["pf"])<=.0005,"expectancy":abs(a["expectancy"]-b["expectancy"])<=.01,
      "win_rate":abs(a["win_rate"]-b["win_rate"])<=.0001,"max_dd":abs(a["max_dd_pct"]-b["max_dd_pct"])<=.0005,
      "sequence":sig(a)==sig(b),"engineering_clean":a["engineering_clean"] and b["engineering_clean"],
      "identity_clean":b["identity_clean"],"canonical_coverage":abs(b["canonical_family_coverage"]-1.0)<=1e-12}
    ok=all(checks.values()); truth_ok &= ok; truth[w]={"pass":ok,"checks":checks}

family=[]
for fid in F:
    funnel={k:0 for k in ["topology","geometry_matched","age_rejected","selected","candidates","quality_pass","quality_reject","route_pass","route_reject","prz_touch","confirmation_pass","grid_planned","basket_planned","executed","closed","rejected","expired","invalidated","shadow_started","shadow_resolved"]}
    sh=[]; per_window={}
    for w in W:
        d=wins[(V[1],w)]
        ff=d.get("family_funnel",{}).get(fid,{})
        for k in funnel: funnel[k]+=int(ff.get(k,0))
        sw=[x for x in d.get("shadow_outcomes",[]) if x.get("family_id")==fid]
        sh.extend(sw)
        rr=[x["outcome_r"] for x in sw]
        per_window[w]={"shadow_count":len(rr),"shadow_mean_r":statistics.mean(rr) if rr else None,"shadow_pf_r":pf_r(rr) if rr else None}
    rr=[x["outcome_r"] for x in sh]; positives=[x for x in rr if x>0]
    topology=funnel["topology"]; geom=funnel["geometry_matched"]; exe=funnel["executed"]
    geom_rate=geom/topology if topology else 0; execution_conversion=exe/geom if geom else 0
    shadow_mean=statistics.mean(rr) if rr else None; shadow_pf=pf_r(rr) if rr else None
    positive_windows=sum(1 for w in W if per_window[w]["shadow_count"]>=3 and per_window[w]["shadow_mean_r"] is not None and per_window[w]["shadow_mean_r"]>0)
    research_candidate=len(rr)>=30 and shadow_mean is not None and shadow_mean>0 and shadow_pf is not None and shadow_pf>1.0 and positive_windows>=3
    if geom<20:
        starvation="DETECTOR_OR_GENUINE_SCARCITY_REVIEW"
    elif exe==0 or execution_conversion<.01:
        if funnel["route_reject"]+funnel["quality_reject"] >= max(1,int(.5*geom)): starvation="ADMISSION_STARVATION"
        else: starvation="CONVERSION_STARVATION"
    elif funnel["selected"]>0 and exe/max(funnel["selected"],1)<.05:
        starvation="DOWNSTREAM_CONVERSION_STARVATION"
    else:
        starvation="NO_SEVERE_STARVATION"
    family.append({"family_id":fid,**funnel,"geometry_match_rate":geom_rate,"execution_per_geometry":execution_conversion,
      "shadow_count":len(rr),"shadow_mean_r":shadow_mean,"shadow_pf_r":shadow_pf,"shadow_win_rate":sum(x>0 for x in rr)/len(rr) if rr else None,
      "shadow_mean_mfe_r":statistics.mean([x["mfe_r"] for x in sh]) if sh else None,
      "shadow_mean_mae_r":statistics.mean([x["mae_r"] for x in sh]) if sh else None,
      "positive_shadow_windows":positive_windows,"starvation_class":starvation,"research_expansion_candidate":research_candidate,"windows":per_window})

census_complete=all(any(wins[(V[1],w)].get("family_funnel",{}).get(fid) is not None for w in W) for fid in F)
shadow_no_alpha_leak=truth_ok
decision="CENSUS_READY_FOR_REVIEW" if truth_ok and census_complete else "HOLD_WITH_EVIDENCE"
report={"version":"HarmonyBot V69","stage":"DEV_CENSUS","duration_years":YEARS,"truth_equivalence_gate":truth_ok,"census_complete":census_complete,
 "capital_behavior_changed":False,"shadow_results_used_for_trading":False,"decision":decision,"fresh_used":False,
 "truth_detail":truth,"families":family,
 "research_expansion_candidates":[x["family_id"] for x in family if x["research_expansion_candidate"]]}
(out/"V69_FAMILY_CENSUS.json").write_text(json.dumps(report,indent=2))
(out/"V69_TRUTH_EQUIVALENCE.json").write_text(json.dumps({"pass":truth_ok,"windows":truth},indent=2))
(out/"V69_FINAL_DEV_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V69","decision":decision,"fresh_used":False,"capital_behavior_changed":False},indent=2))
print(json.dumps(report,indent=2))
