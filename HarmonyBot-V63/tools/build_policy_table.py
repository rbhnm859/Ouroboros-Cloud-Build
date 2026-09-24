#!/usr/bin/env python3
import json,pathlib,sys,hashlib,collections,math
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rows=[]
for p in root.rglob("*.json"):
 try:d=json.load(open(p))
 except:continue
 for r in d.get("basket_outcomes",[]): rows.append(r)
cells=collections.defaultdict(list)
for r in rows:
 key=f"{r.get('pattern','UNKNOWN')}|{r.get('route','UNKNOWN')}|CALIBRATION"
 cells[key].append(float(r.get("r",0)))
table={}
for k,v in sorted(cells.items()):
 n=len(v); mean=sum(v)/n; family=k.split("|")[0]; prior=[x for kk,vv in cells.items() if kk.startswith(family+"|") for x in vv]; pm=sum(prior)/len(prior) if prior else 0; w=n/(n+8.0); post=w*mean+(1-w)*pm
 table[k]={"n":n,"mean_r":mean,"family_prior_r":pm,"shrinkage_weight":w,"posterior_expectancy_r":post,"capital_state":"ON" if n>=3 and post>0 else ("OFF" if n>=5 and post<=0 else "SHADOW")}
cfg={"version":"HarmonyBot V63","policy_table":table,"regimes":["R1_TREND_EXPANSION","R2_TREND_EXHAUSTION","R3_COMPRESSION","R4_TRANSITION"],"conditional_grid":[[0,.60],[.236,.25],[.382,.15],[.618,0]],"abcd_standalone_capital":False,"right_tail_min":.80,"whole_basket_risk_max_pct":1.0,"fresh_used":False}
raw=json.dumps(cfg,sort_keys=True,separators=(",",":")).encode(); cfg["sha256"]=hashlib.sha256(raw).hexdigest(); (out/"V63_POLICY_TABLE.json").write_text(json.dumps(cfg,indent=2)); print(json.dumps(cfg,indent=2))