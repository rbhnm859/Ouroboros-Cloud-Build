#!/usr/bin/env python3
import argparse,json,pathlib,math

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--phase",choices=["dev","validation","capital","fresh"],required=True)
ap.add_argument("--out",required=True)
a=ap.parse_args()

def load_rows(root):
    rows=[]
    for p in pathlib.Path(root).rglob("*.json"):
        try:d=json.load(open(p,encoding="utf-8-sig"))
        except Exception:continue
        if isinstance(d,dict) and "basket_outcomes" in d and d.get("version","").startswith("HarmonyBot V66"):
            d["_path"]=str(p); rows.append(d)
    return rows

def pct(v,p):
    v=sorted(v)
    if not v:return 0.0
    q=(len(v)-1)*p; lo=int(q); hi=min(len(v)-1,lo+1)
    return v[lo]+(v[hi]-v[lo])*(q-lo)

def clean_row(x):
    return bool(x.get("engineering_clean")) and all(int(x.get(k,0) or 0)==0 for k in [
        "execution_errors","actual_basket_risk_violations","margin_risk_violations",
        "stop_widening_violations","duplicate_grid_legs","orphan_pending_orders",
        "gap_through_survivors","unprotected_survivors","post_fill_protection_failures",
        "execution_state_violations"
    ])

def agg(xs,years):
    b=[z for x in xs for z in x.get("basket_outcomes",[])]
    vals=[float(z.get("net",0) or 0) for z in b]
    rs=[float(z.get("r",0) or 0) for z in b]
    gp=sum(v for v in vals if v>0); gl=abs(sum(v for v in vals if v<0))
    wins=[r for r in rs if r>0]
    return {
      "baskets":len(b),
      "frequency":len(b)/years if years else 0,
      "net":sum(vals),
      "pf":gp/gl if gl else (999.0 if gp else 0.0),
      "expectancy":sum(vals)/len(vals) if vals else 0.0,
      "win_rate":sum(v>0 for v in vals)/len(vals) if vals else 0.0,
      "max_dd_pct":max([float(x.get("max_dd_pct",0) or 0) for x in xs] or [0]),
      "p95_winner_r":pct(wins,.95),
      "max_winner_r":max(wins) if wins else 0.0,
      "all_positive":bool(xs) and all(float(x.get("net",0) or 0)>0 for x in xs),
      "clean":bool(xs) and all(clean_row(x) for x in xs)
    }

rows=load_rows(a.root)
o={"version":"HarmonyBot V66","phase":a.phase,"source_rows":len(rows)}

if a.phase=="dev":
    by={(x.get("mode"),x.get("window")):x for x in rows}
    wins=["H21","H22","H23","A","B","C"]
    missing=[]
    for mode in ["V66_CONTROL","V66_PRODUCT"]:
        for w in wins:
            if (mode,w) not in by: missing.append(f"{mode}:{w}")
    if missing:
        raise SystemExit("missing dev evidence: "+",".join(missing))
    prod=[by[("V66_PRODUCT",w)] for w in wins]
    ctrl=[by[("V66_CONTROL",w)] for w in wins]
    D=agg([by[("V66_PRODUCT",w)] for w in ["A","B","C"]],1.5)
    H=agg([by[("V66_PRODUCT",w)] for w in ["H21","H22","H23"]],3.0)
    CD=agg([by[("V66_CONTROL",w)] for w in ["A","B","C"]],1.5)
    CH=agg([by[("V66_CONTROL",w)] for w in ["H21","H22","H23"]],3.0)
    rt=D["p95_winner_r"]/CD["p95_winner_r"] if CD["p95_winner_r"]>0 else 1.0
    commercial=(D["baskets"]<=90 and D["frequency"]>=60 and D["net"]>=1800 and D["pf"]>=2 and
                D["expectancy"]>=20 and D["win_rate"]>=.50 and D["max_dd_pct"]<=6 and
                D["all_positive"] and D["clean"] and rt>=.80)
    v51_superiority=(D["frequency"]>38.6667 and D["net"]>2101.66 and D["pf"]>2.1096878432 and
                     D["expectancy"]>36.2355 and D["win_rate"]>=.534483 and D["max_dd_pct"]<=4.49784 and
                     D["all_positive"] and D["clean"])
    historical=(H["all_positive"] and H["clean"])
    bad_regime=(by[("V66_PRODUCT","H23")]["net"]>0 and by[("V66_PRODUCT","C")]["net"]>0)
    control_clean=CD["clean"] and CH["clean"]
    candidate=bool(commercial and v51_superiority and historical and bad_regime and control_clean)
    o.update({
      "product_dev":D,"product_history":H,"control_dev":CD,"control_history":CH,
      "right_tail_preservation":rt,
      "windows":{"product":{w:by[("V66_PRODUCT",w)] for w in wins},"control":{w:by[("V66_CONTROL",w)] for w in wins}},
      "commercial_gate":commercial,"v51_superiority_gate":v51_superiority,
      "historical_stability_gate":historical,"bad_regime_gate":bad_regime,
      "control_clean_gate":control_clean,"candidate":candidate,
      "status":"VALIDATION_CANDIDATE" if candidate else "HOLD_WITH_EVIDENCE"
    })

elif a.phase=="validation":
    q=[x for x in rows if str(x.get("window","")).startswith("VAL_")]
    base=[x for x in q if abs(float(x.get("spread",0))-1.0)<1e-9]
    baseagg=agg(base,.5)
    quarters={str(x.get("window","")).split("_")[1] for x in base}
    stress_positive=bool(q) and all(float(x.get("net",0) or 0)>0 and clean_row(x) for x in q)
    candidate=(quarters=={"Q1","Q2"} and baseagg["all_positive"] and baseagg["clean"] and
               baseagg["pf"]>=2 and baseagg["expectancy"]>=20 and baseagg["win_rate"]>=.50 and
               baseagg["max_dd_pct"]<=6 and stress_positive)
    o.update({"base_spread":baseagg,"stress_rows":q,"stress_all_positive_clean":stress_positive,
              "candidate":bool(candidate),"status":"CAPITAL_CANDIDATE" if candidate else "HOLD_VALIDATION"})

elif a.phase=="capital":
    caps=[x for x in rows if str(x.get("window","")).startswith("CAPITAL_B")]
    expected={100,150,200,300,500,1000,10000}
    got={int(round(float(x.get("starting_balance",0)))) for x in caps}
    per=[]
    for x in sorted(caps,key=lambda z:float(z.get("starting_balance",0))):
        ok=(x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and
            float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and clean_row(x))
        per.append({"balance":x.get("starting_balance"),"baskets":x.get("baskets"),"net":x.get("net"),
                    "pf":x.get("pf"),"expectancy":x.get("expectancy"),"max_dd_pct":x.get("max_dd_pct"),
                    "clean":clean_row(x),"pass":ok})
    candidate=(got==expected and all(x["pass"] for x in per))
    o.update({"balances":per,"candidate":bool(candidate),"status":"PRE_FRESH_FREEZE_CANDIDATE" if candidate else "HOLD_CAPITAL"})

elif a.phase=="fresh":
    q=[x for x in rows if str(x.get("window","")).startswith("FRESH_")]
    if len(q)!=1: raise SystemExit(f"expected one fresh row, got {len(q)}")
    x=q[0]
    candidate=(x.get("baskets",0)>0 and float(x.get("net",0) or 0)>0 and float(x.get("pf",0) or 0)>1 and
               float(x.get("expectancy",0) or 0)>0 and float(x.get("max_dd_pct",0) or 0)<=6 and clean_row(x))
    o.update({"fresh":x,"candidate":bool(candidate),"status":"COMMERCIAL_FREEZE_APPROVED" if candidate else "HOLD_FRESH"})

pathlib.Path(a.out).write_text(json.dumps(o,indent=2),encoding="utf-8")
print(json.dumps(o,indent=2))
