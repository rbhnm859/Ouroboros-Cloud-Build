#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); mode=sys.argv[3]; out.mkdir(parents=True,exist_ok=True)
F=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
reports=[]
for p in root.rglob("*.json"):
 try:
  d=json.load(open(p))
  if "basket_outcomes" in d: reports.append(d)
 except: pass
rows=sum((d.get("basket_outcomes",[]) for d in reports),[]); vals=[float(r["net"]) for r in rows]; n=len(vals)
gp=sum(x for x in vals if x>0); gl=-sum(x for x in vals if x<0); pf=gp/gl if gl else (999 if gp else 0); net=sum(vals)
fam={f:sum(float(r["net"]) for r in rows if r.get("pattern")==f) for f in F}; cnt={f:sum(r.get("pattern")==f for r in rows) for f in F}
zero=("execution_errors","grid_risk_violations","actual_basket_risk_violations","margin_risk_violations","stop_widening_violations","duplicate_grid_legs","orphan_pending_orders","unprotected_survivors","post_fill_protection_failures","execution_state_violations")
z={"mode":mode,"baskets":n,"net":net,"pf":pf,"expectancy":net/n if n else 0,"win_rate":sum(x>0 for x in vals)/n if n else 0,"max_dd_pct":max((float(d.get("max_dd_pct",0)) for d in reports),default=0),"all_windows_positive":all(float(d.get("net",0))>0 for d in reports),"all_12_families_positive":all(cnt[f]>0 and fam[f]>0 for f in F),"family_net":fam,"family_count":cnt,"risk_clean":all(all(int(d.get(k,0) or 0)==0 for k in zero) for d in reports),"engineering_clean":all(bool(d.get("engineering_clean",False)) for d in reports)}
z["pass"]=n>0 and z["net"]>0 and z["pf"]>=2 and z["expectancy"]>=20 and z["win_rate"]>=.50 and z["max_dd_pct"]<=6 and z["all_windows_positive"] and z["all_12_families_positive"] and z["risk_clean"] and z["engineering_clean"]
(out/f"V69_{mode}_GATE.json").write_text(json.dumps(z,indent=2)); (out/"pass.txt").write_text("true" if z["pass"] else "false"); print(json.dumps(z,indent=2))
