#!/usr/bin/env python3
import argparse,json,pathlib,statistics
ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--phase",required=True,choices=["calibration","dev","validation","capital","fresh"]); ap.add_argument("--out",required=True)
a=ap.parse_args()

def load():
    rows=[]
    for p in pathlib.Path(a.root).rglob("*.json"):
        try:d=json.load(open(p))
        except:continue
        if isinstance(d,dict) and d.get("version")=="HarmonyBot V67" and "basket_outcomes" in d: rows.append(d)
    return rows

def agg(xs,years):
    b=[z for x in xs for z in x["basket_outcomes"]]; v=[z["net"] for z in b]; gp=sum(x for x in v if x>0); gl=abs(sum(x for x in v if x<0))
    fam={}
    for x in b:
        fam.setdefault(x["pattern"],[]).append(x["net"])
    famsum={k:{"baskets":len(q),"net":sum(q)} for k,q in fam.items()}
    return {"baskets":len(b),"frequency":len(b)/years if years else 0,"net":sum(v),"pf":gp/gl if gl else (999 if gp else 0),
            "expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,
            "max_dd_pct":max([x["max_dd_pct"] for x in xs] or [0]),"all_positive":bool(xs) and all(x["net"]>0 for x in xs),
            "clean":bool(xs) and all(x["engineering_clean"] and x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0 for x in xs),
            "family":famsum,"max_family_share":max([len(q)/len(b) for q in fam.values()] or [0]),
            "positive_family_count":sum(sum(q)>0 for q in fam.values()),"non_abcd_net":sum(x["net"] for x in b if x["pattern"]!="AB=CD")}

rows=load(); o={"version":"HarmonyBot V67","phase":a.phase,"rows":len(rows)}

if a.phase=="calibration":
    by={(x["mode"],x["window"],x["family_grid"]):x for x in rows}
    req=["A","B","C"]
    ctrl=[by[("V67_CONTROL",w,False)] if ("V67_CONTROL",w,False) in by else by[("V67_CONTROL",w,True)] for w in req]
    prod=[by[("V67_PRODUCT",w,True)] for w in req]
    C=agg(ctrl,1.5); P=agg(prod,1.5)
    reproduction=(C["baskets"]==200 and abs(C["net"]-2902.27)<=0.05 and abs(C["pf"]-1.3754845136750589)<=1e-4 and abs(C["expectancy"]-14.51135)<=1e-3 and abs(C["win_rate"]-.435)<=1e-6 and abs(C["max_dd_pct"]-9.814998648020353)<=.05 and C["clean"])
    o.update({"control":C,"product":P,"control_reproduction":reproduction,"candidate":reproduction,"status":"DEV_UNLOCKED" if reproduction else "HOLD_CONTROL_MISMATCH"})

elif a.phase=="dev":
    control=[x for x in rows if x["mode"]=="V67_CONTROL" and x["window"] in ["H23","A","B","C"]]
    product=[x for x in rows if x["mode"]=="V67_PRODUCT" and x["family_grid"] and x["window"] in ["H23","A","B","C"]]
    nogrid=[x for x in rows if x["mode"]=="V67_PRODUCT" and not x["family_grid"] and x["window"] in ["H23","A","B","C"]]
    if len(control)!=4 or len(product)!=4 or len(nogrid)!=4: raise SystemExit("missing dev evidence")
    C=agg(control,2.5); P=agg(product,2.5); N=agg(nogrid,2.5)
    control_dev=[x for x in control if x["window"] in ["A","B","C"]]; CD=agg(control_dev,1.5)
    dev_prod=[x for x in product if x["window"] in ["A","B","C"]]; D=agg(dev_prod,1.5)
    dev_nogrid=[x for x in nogrid if x["window"] in ["A","B","C"]]; G=agg(dev_nogrid,1.5)
    grid_delta=P["net"]-N["net"]; grid_delta_dev=D["net"]-G["net"]
    grid_multiplier=(D["net"]/G["net"] if G["net"]>0 else None)
    family_gate=(D["max_family_share"]<=.55 and D["positive_family_count"]>=3 and D["non_abcd_net"]>0 and len(D["family"])>=4)
    throughput=(D["frequency"]>=60 and D["frequency"]>=.70*max(1,CD["frequency"]))
    family_alpha_gate=(G["net"]>CD["net"] and G["pf"]>=CD["pf"] and G["expectancy"]>=CD["expectancy"] and
                       G["frequency"]>=.70*max(1,CD["frequency"]) and G["non_abcd_net"]>0 and
                       G["positive_family_count"]>=3 and G["max_family_share"]<=.55 and G["clean"])
    commercial=(D["net"]>=1800 and D["pf"]>=2 and D["expectancy"]>=20 and D["win_rate"]>=.50 and D["max_dd_pct"]<=6 and D["all_positive"] and D["clean"] and throughput and family_gate)
    historical_grid=next(x for x in product if x["window"]=="H23")
    historical_nogrid=next(x for x in nogrid if x["window"]=="H23")
    historical=historical_grid["net"]>0
    grid_gate=(grid_delta>0 and grid_delta_dev>0 and P["pf"]>=N["pf"] and P["expectancy"]>=N["expectancy"] and
               D["pf"]>=G["pf"] and D["expectancy"]>=G["expectancy"] and
               P["max_dd_pct"]<=N["max_dd_pct"]+1e-9 and D["max_dd_pct"]<=G["max_dd_pct"]+1e-9 and
               P["frequency"]>=.90*max(1,N["frequency"]) and D["frequency"]>=.90*max(1,G["frequency"]) and
               historical_grid["net"]>=historical_nogrid["net"] and P["clean"])
    candidate=bool(commercial and historical and family_alpha_gate and grid_gate)
    o.update({"control":C,"control_dev_1_5y":CD,"product":P,"product_dev_1_5y":D,"product_no_family_grid":N,"no_grid_dev_1_5y":G,
              "grid_delta_net":grid_delta,"grid_delta_dev_net":grid_delta_dev,"grid_net_multiplier":grid_multiplier,
              "grid_stretch_double_net":bool(grid_multiplier is not None and grid_multiplier>=2),
              "family_alpha_gate":family_alpha_gate,"family_diversification_gate":family_gate,"throughput_gate":throughput,
              "commercial_gate":commercial,"historical_2023_gate":historical,"grid_gate":grid_gate,"candidate":candidate,
              "status":"VALIDATION_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE"})

elif a.phase=="validation":
    q=[x for x in rows if x["mode"]=="V67_PRODUCT" and str(x["window"]).startswith("VAL_")]
    base=[x for x in q if abs(float(x["spread"])-1.0)<1e-9]
    A=agg(base,.5)
    stress=bool(q) and all(x["net"]>0 and x["engineering_clean"] for x in q)
    candidate=(len(base)==2 and A["all_positive"] and A["clean"] and A["pf"]>=2 and A["expectancy"]>=20 and A["win_rate"]>=.50 and A["max_dd_pct"]<=6 and stress)
    o.update({"base":A,"stress_all_positive":stress,"candidate":bool(candidate),"status":"CAPITAL_CANDIDATE" if candidate else "HOLD_VALIDATION"})

elif a.phase=="capital":
    q=[x for x in rows if str(x["window"]).startswith("CAPITAL_")]
    expected={100,150,200,300,500,1000,10000}; got={int(round(x["starting_balance"])) for x in q}
    per=[]
    for x in sorted(q,key=lambda z:z["starting_balance"]):
        ok=x["baskets"]>0 and x["net"]>0 and x["expectancy"]>0 and x["pf"]>1 and x["max_dd_pct"]<=6 and x["engineering_clean"] and x["actual_basket_risk_violations"]==0 and x["margin_risk_violations"]==0
        per.append({"balance":x["starting_balance"],"baskets":x["baskets"],"net":x["net"],"pf":x["pf"],"expectancy":x["expectancy"],"dd":x["max_dd_pct"],"pass":ok})
    candidate=(got==expected and all(x["pass"] for x in per))
    o.update({"balances":per,"candidate":bool(candidate),"status":"PRE_FRESH_FREEZE" if candidate else "HOLD_CAPITAL"})

elif a.phase=="fresh":
    q=[x for x in rows if str(x["window"]).startswith("FRESH_")]
    if len(q)!=1: raise SystemExit("fresh evidence count mismatch")
    x=q[0]; candidate=x["baskets"]>0 and x["net"]>0 and x["pf"]>1 and x["expectancy"]>0 and x["max_dd_pct"]<=6 and x["engineering_clean"]
    o.update({"fresh":x,"candidate":bool(candidate),"status":"COMMERCIAL_FREEZE_APPROVED" if candidate else "HOLD_FRESH"})

pathlib.Path(a.out).write_text(json.dumps(o,indent=2)); print(json.dumps(o,indent=2))
