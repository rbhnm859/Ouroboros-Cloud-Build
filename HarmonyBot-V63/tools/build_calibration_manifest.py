#!/usr/bin/env python3
import json,pathlib,sys,hashlib,collections,statistics
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);rows=[]
for p in root.rglob("*.json"):
 try:d=json.load(open(p))
 except:continue
 if "basket_outcomes" in d: rows.append(d)
cells=collections.defaultdict(list); fam=collections.defaultdict(list); allr=[]
for d in rows:
 for x in d.get("cell_outcomes",[]):
  k=(x.get("pattern",""),x.get("route",""),x.get("regime",""),x.get("policy","")); cells[k].append(x["r"]); fam[x.get("pattern","")].append(x["r"]); allr.append(x["r"])
global_mean=statistics.mean(allr) if allr else 0
evidence=[]
for k,rs in sorted(cells.items()):
 prior=statistics.mean(fam[k[0]]) if fam[k[0]] else global_mean; n=len(rs); mean=statistics.mean(rs); w=n/(n+8.0); shr=w*mean+(1-w)*prior
 evidence.append({"pattern":k[0],"route":k[1],"regime":k[2],"policy":k[3],"n":n,"mean_r":mean,"family_prior_r":prior,"shrunk_r":shr,"capital_evidence":"ON" if n>=3 and shr>0 else ("SHADOW" if shr>-0.05 else "OFF")})
frozen={"version":"HarmonyBot V63","calibration_period":"2021-2023 burned","source_policy":"preregistered transparent Family×Route×Regime router","hierarchical_shrinkage_k":8.0,"right_tail_min_ratio":.80,"risk":{"basket_risk_pct":1.0,"min_net_rr":2.0},"fresh_used":False}
frozen["config_sha256"]=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
(out/"V63_CALIBRATION_FREEZE.json").write_text(json.dumps({"frozen":frozen,"cell_evidence":evidence,"rows":rows},indent=2));print(json.dumps({"frozen":frozen,"cells":len(evidence)},indent=2))