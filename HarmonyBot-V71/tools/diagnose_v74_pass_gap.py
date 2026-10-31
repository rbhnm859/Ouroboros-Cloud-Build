#!/usr/bin/env python3
"""V74 exact pass-gap decomposition. Diagnostic only; never trains or promotes."""
import json,math,pathlib,sys
from collections import Counter,defaultdict
from v74_model_lib import load_rows,metrics,SEQUENTIAL_KEYS,LATE_AUCTION_KEYS,SURVIVAL_FRESH_KEYS

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
YEARS=["Y2021","Y2022","Y2023"]; MIN_N=250; MIN_MEAN=.90; MIN_PF=3.30; MIN_WR=.70; MIN_RR=2.30
EARLY=[k for k in SEQUENTIAL_KEYS if k.startswith("M15_") and k.endswith("_F00")]
LATE=[k for k in LATE_AUCTION_KEYS if k.endswith("_F30")]
KEYS={"EARLY":EARLY,"LATE":LATE,"SURVIVAL":SURVIVAL_FRESH_KEYS}
rows=load_rows(root,YEARS)

def eid(s):
 p=(s or "").split("|"); return "|".join((p[0],p[1],p[-1])) if len(p)>=7 else (s or "")
def outcome(r,k,src):
 om=r.get("sequential",{}) if src=="EARLY" else r.get("late_auction",{}) if src=="LATE" else r.get("survival_fresh",{})
 rm=r.get("sequential_rr",{}) if src=="EARLY" else r.get("late_auction_rr",{}) if src=="LATE" else r.get("survival_fresh_rr",{})
 v,rr=om.get(k),rm.get(k)
 try:v=float(v);rr=float(rr)
 except:return None
 if not math.isfinite(v) or not math.isfinite(rr) or rr+1e-9<MIN_RR:return None
 return {"r":v,"rr":rr,"src":src,"key":k,"family":r.get("family",""),"action":r.get("action",""),"setup":r.get("setup","")}
def oracle(year):
 d=defaultdict(list)
 for r in rows:
  if r["window"]!=year:continue
  e=eid(r.get("setup",""))
  for src,ks in KEYS.items():
   for k in ks:
    z=outcome(r,k,src)
    if z is not None:d[e].append(z)
 best=[]
 for e,zs in d.items():
  z=max(zs,key=lambda q:(q["r"],q["rr"],q["src"]+"|"+q["key"])); z=dict(z,event=e); best.append(z)
 return sorted(best,key=lambda q:(q["r"],q["rr"],q["event"]),reverse=True)

def req(m):
 n=m["n"]; wins=round(m["win_rate"]*n)
 return {"wins_now":wins,"wins_required":math.ceil(MIN_WR*n-1e-12),"minimum_loss_to_win_conversions_for_wr":max(0,math.ceil(MIN_WR*n-1e-12)-wins),
         "mean_r_gap":max(0.0,MIN_MEAN-m["mean_r"]),"pf_gap":max(0.0,MIN_PF-m["pf_r"]),"avg_rr_gap":max(0.0,MIN_RR-m["average_rr"])}

report={"type":"V74_EXACT_PASS_GAP_DIAGNOSTIC_ONLY","used_for_training":False,"gate_unchanged":True,"years":{}}
for y in YEARS:
 b=oracle(y); top=b[:MIN_N]
 fake=[dict(r,r=q["r"],bars=1) for q,r in [(z,z) for z in top]]
 m=metrics(fake)
 losers=[z for z in top if z["r"]<=0]
 report["years"][y]={"available_events":len(b),"top250_metrics":m,"requirements":req(m),
  "top250_positive":sum(z["r"]>0 for z in top),"top250_nonpositive":len(losers),
  "losers_by_family":dict(Counter(z["family"] for z in losers).most_common()),
  "losers_by_action":dict(Counter(z["action"] for z in losers).most_common()),
  "losers_by_source":dict(Counter(z["src"] for z in losers).most_common()),
  "losers_by_route":dict(Counter(z["src"]+"|"+z["key"] for z in losers).most_common(20)),
  "interpretation":"ORACLE_LOSER_MEANS_ACTION_SPACE_MISSING_A_PROFITABLE_LEGAL_ROUTE_FOR_THIS_EVENT"}
(out/"V74_PASS_GAP.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
