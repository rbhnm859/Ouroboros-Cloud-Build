#!/usr/bin/env python3
import json,pathlib,sys,collections,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
F=["V51_CHAMPION_CONTROL","V56_CORE_REBASE","V56_EVIDENCE_EXPANSION_L0","V56_EVIDENCE_EXPANSION_LEGACY_GRID","V56_EVIDENCE_EXPANSION_GRID_V4"]
COMM={"baskets":90,"frequency":60.0,"net":1800.0,"pf":2.0,"expectancy":20.0,"win_rate":.50,"max_dd_pct":6.0}
SUPER={"frequency":80.0,"net":3000.0,"pf":2.20,"expectancy":45.0,"win_rate":.55,"max_dd_pct":5.0}
def find(n):
 xs=list(root.rglob(n))
 if not xs: raise SystemExit("missing "+n)
 return xs[0]
def rd(f,w): return json.load(open(find(f"{f}-{w}.json")))
def pf(vals):
 gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 return gp/gl if gl else (999 if gp else 0)
def agg(f):
 xs=[rd(f,w) for w in "ABC"]; rows=[r for x in xs for r in x.get("basket_outcomes",[])]; vals=[r["net"] for r in rows]; n=len(rows)
 ev=[e for x in xs for e in x.get("v56_evidence",[])]
 pipes={}; conv=collections.defaultdict(lambda:collections.Counter()); det=collections.defaultdict(lambda:collections.Counter())
 for x in xs:
  for p,st in x.get("conversion_truth",{}).items(): conv[p].update(st)
  for p,st in x.get("detector_truth",{}).items(): det[p].update(st)
  for p,row in x.get("pattern_pipeline",{}).items():
   q=pipes.setdefault(p,{k:0 for k in row})
   for k,z in row.items(): q[k]+=z
 return {
  "baskets":n,"frequency":n/1.5,"unique_setups":len({r["setup"] for r in rows}),"net":sum(vals),"pf":pf(vals),
  "expectancy":sum(vals)/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,
  "gross_profit":sum(x for x in vals if x>0),"gross_loss":abs(sum(x for x in vals if x<0)),
  "max_dd_pct":max(x["max_dd_pct"] for x in xs),"all_windows_positive":all(x["net"]>0 for x in xs),
  "engineering_clean":all(x["engineering_clean"] for x in xs),
  "risk_clean":all(x.get("actual_basket_risk_violations",0)==0 and x.get("margin_risk_violations",0)==0 for x in xs),
  "windows":{w:rd(f,w) for w in "ABC"},"rows":rows,"pipeline":pipes,
  "conversion_truth":{p:dict(q) for p,q in conv.items()},"detector_truth":{p:dict(q) for p,q in det.items()},
  "evidence":{"observations":len(ev),"admitted":sum(e.get("admitted",False) for e in ev),"core":sum(e.get("core",False) for e in ev),
              "research_only":sum(not e.get("admitted",False) for e in ev),
              "mean_score":sum(e.get("score",0) for e in ev)/len(ev) if ev else 0,
              "mean_expected_r_proxy":sum(e.get("expected_r_proxy",0) for e in ev)/len(ev) if ev else 0}
 }
A={f:agg(f) for f in F}
data_snapshot_valid=True; data_snapshot_by_window={}
for w in "ABC":
 shas={A[f]["windows"][w].get("data_snapshot_sha","") for f in F}; shas.discard("")
 data_snapshot_by_window[w]=sorted(shas)
 if len(shas)!=1:data_snapshot_valid=False
def econ(z):
 g=collections.defaultdict(list)
 for r in z["rows"]:g[r.get("pattern","?")].append(r)
 outp={}
 for p,rows in g.items():
  v=[r["net"] for r in rows]
  outp[p]={"trades":len(v),"net":sum(v),"pf":pf(v),"expectancy":sum(v)/len(v),"win_rate":sum(x>0 for x in v)/len(v)}
 return outp
for z in A.values():
 z["pattern_economics"]=econ(z)
 z["family_detected"]={p:r.get("detected",0) for p,r in z["pipeline"].items()}
 z["family_executed"]={p:r.get("executed",0) for p,r in z["pipeline"].items()}
 z["starved_families"]=[p for p,n in z["family_detected"].items() if n>0 and z["family_executed"].get(p,0)==0]
def parity(a,b):
 sa={r["setup"] for r in a["rows"]}; sb={r["setup"] for r in b["rows"]}
 return {"exact_setup_parity":sa==sb,"missing_from_rebase":sorted(sa-sb),"extra_in_rebase":sorted(sb-sa),
         "delta_baskets":b["baskets"]-a["baskets"],"delta_net":b["net"]-a["net"],"delta_pf":b["pf"]-a["pf"],
         "pass":sa==sb and a["baskets"]==b["baskets"] and abs(a["net"]-b["net"])<=.30 and abs(a["pf"]-b["pf"])<=.006}
core_parity=parity(A["V51_CHAMPION_CONTROL"],A["V56_CORE_REBASE"])
def contribution(f):
 z=A[f]; core=A["V51_CHAMPION_CONTROL"]; core_set={r["setup"] for r in core["rows"]}; zset={r["setup"] for r in z["rows"]}
 added=[r for r in z["rows"] if r["setup"] not in core_set]; removed=[r for r in core["rows"] if r["setup"] not in zset]
 vals=[r["net"] for r in added]; gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0))
 wins={}
 for w in "ABC":
  cw={r["setup"] for r in core["windows"][w].get("basket_outcomes",[])}
  rr=[r for r in z["windows"][w].get("basket_outcomes",[]) if r["setup"] not in cw]
  wins[w]={"trades":len(rr),"net":sum(r["net"] for r in rr),"pf":pf([r["net"] for r in rr])}
 d={"added_trades":len(added),"added_net":sum(vals),"added_pf":pf(vals),"added_expectancy":sum(vals)/len(vals) if vals else 0,
    "added_gp":gp,"added_gl":gl,"commercial_margin_pf2":gp-2*gl,"removed_core_trades":len(removed),
    "removed_core_net":sum(r["net"] for r in removed),"windows":wins}
 d["pass"]=len(added)>0 and d["added_net"]>0 and d["added_expectancy"]>0 and d["commercial_margin_pf2"]>=0 and d["removed_core_trades"]==0 and all(wins[w]["net"]>=0 for w in "ABC")
 return d
contrib={f:contribution(f) for f in F if f.startswith("V56_EVIDENCE_EXPANSION_")}
def grid_delta(a,b):
 x,y=A[a],A[b]
 wins={w:{"delta_net":x["windows"][w]["net"]-y["windows"][w]["net"]} for w in "ABC"}
 return {"candidate":a,"control":b,"delta_net":x["net"]-y["net"],"delta_pf":x["pf"]-y["pf"],"delta_expectancy":x["expectancy"]-y["expectancy"],
         "delta_dd":x["max_dd_pct"]-y["max_dd_pct"],"positive_delta_windows":sum(v["delta_net"]>0 for v in wins.values()),"windows":wins,
         "pass":x["net"]>y["net"] and x["pf"]>=y["pf"] and x["expectancy"]>=y["expectancy"] and sum(v["delta_net"]>0 for v in wins.values())>=2 and x["max_dd_pct"]<=COMM["max_dd_pct"] and x["engineering_clean"] and x["risk_clean"]}
grid={"LEGACY_VS_L0":grid_delta("V56_EVIDENCE_EXPANSION_LEGACY_GRID","V56_EVIDENCE_EXPANSION_L0"),
      "GRID_V4_VS_LEGACY":grid_delta("V56_EVIDENCE_EXPANSION_GRID_V4","V56_EVIDENCE_EXPANSION_LEGACY_GRID")}
def commercial(z):
 return z["baskets"]>=COMM["baskets"] and z["frequency"]>=COMM["frequency"] and z["net"]>=COMM["net"] and z["pf"]>=COMM["pf"] and z["expectancy"]>=COMM["expectancy"] and z["win_rate"]>=COMM["win_rate"] and z["max_dd_pct"]<=COMM["max_dd_pct"] and z["all_windows_positive"] and z["engineering_clean"] and z["risk_clean"] and z["unique_setups"]==z["baskets"]
def superiority(z):
 return z["frequency"]>=SUPER["frequency"] and z["net"]>SUPER["net"] and z["pf"]>SUPER["pf"] and z["expectancy"]>SUPER["expectancy"] and z["win_rate"]>=SUPER["win_rate"] and z["max_dd_pct"]<=SUPER["max_dd_pct"] and z["all_windows_positive"]
for f,z in A.items():
 z["commercial_gate"]=commercial(z) if f.startswith("V56_EVIDENCE_EXPANSION_") else False
 z["superiority_gate"]=superiority(z) if f.startswith("V56_EVIDENCE_EXPANSION_") else False
 z["core_preservation_gate"]=core_parity["pass"] if f=="V56_CORE_REBASE" else (contrib.get(f,{}).get("removed_core_trades",1)==0 if f in contrib else False)
 z.pop("rows",None)
eligible=[]
for f in ["V56_EVIDENCE_EXPANSION_LEGACY_GRID","V56_EVIDENCE_EXPANSION_GRID_V4"]:
 gridok=True if f.endswith("LEGACY_GRID") else grid["GRID_V4_VS_LEGACY"]["pass"]
 if A[f]["commercial_gate"] and A[f]["superiority_gate"] and contrib[f]["pass"] and core_parity["pass"] and gridok:
  eligible.append(f)
winner=max(eligible,key=lambda f:(A[f]["net"],A[f]["pf"],A[f]["frequency"])) if eligible else None
front={"version":"HarmonyBot V56","architecture":"UNIVERSAL_HARMONIC_HIGH_FREQUENCY_ALPHA_PURIFICATION_CORE_PROTECTED",
"commercial_minimum":COMM,"superiority_target":SUPER,"data_snapshot_valid":data_snapshot_valid,"data_snapshot_by_window":data_snapshot_by_window,
"core_rebase_parity":core_parity,"families":A,"expansion_contribution":contrib,"grid_causal_attribution":grid,
"development_candidate":winner,"status":"DEV2_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False,
"next_stage":"UNTOUCHED_VALIDATION" if winner else "STOP_DEV2_HOLD"}
(out/"V56_PERFORMANCE_FRONTIER.json").write_text(json.dumps(front,indent=2))
(out/"V56_EVIDENCE_ADMISSION_REPORT.json").write_text(json.dumps({f:A[f]["evidence"] for f in F},indent=2))
(out/"V56_FAMILY_ECONOMICS.json").write_text(json.dumps({f:{"pattern_economics":A[f]["pattern_economics"],"pipeline":A[f]["pipeline"],"starved_families":A[f]["starved_families"]} for f in F},indent=2))
(out/"V56_GRID_CAUSAL_ATTRIBUTION.json").write_text(json.dumps(grid,indent=2))
(out/"candidate.txt").write_text(winner or "")
(out/"V56_FINAL_DEV2_DECISION.json").write_text(json.dumps({"version":"HarmonyBot V56","decision":"DEV2_SUPERIORITY_PASS" if winner else "HOLD_WITH_EVIDENCE","fresh_used":False},indent=2))
print(json.dumps(front,indent=2))
