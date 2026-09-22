#!/usr/bin/env python3
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
rows=[]
for w in "ABC":
 xs=list(root.rglob(f"FAMILY_NATIVE_MATH_GEOMETRY-{w}.json"))
 if not xs: raise SystemExit("missing V51 replay "+w)
 rows.append(json.load(open(xs[0])))
b=[x for r in rows for x in r.get("basket_outcomes",[])]
vals=[x["net"] for x in b]
gp=sum(x for x in vals if x>0); gl=abs(sum(x for x in vals if x<0)); pf=gp/gl if gl else 999
n=len(b); net=sum(vals); exp=net/n if n else 0; wr=sum(x>0 for x in vals)/n if n else 0; dd=max(r["max_dd_pct"] for r in rows)
expected={"baskets":58,"net":2101.66,"pf":2.1096878432,"expectancy":36.2355,"win_rate":.534483,"max_dd_pct":4.49784}
checks={
"baskets":n==58,
"net":abs(net-expected["net"])<=.30,
"pf":abs(pf-expected["pf"])<=.006,
"expectancy":abs(exp-expected["expectancy"])<=.08,
"win_rate":abs(wr-expected["win_rate"])<=.002,
"max_dd":abs(dd-expected["max_dd_pct"])<=.02,
"windows_positive":all(r["net"]>0 for r in rows),
"engineering":all(r["engineering_clean"] for r in rows),
"risk":all(r.get("actual_basket_risk_violations",0)==0 and r.get("margin_risk_violations",0)==0 for r in rows)
}
ok=all(checks.values())
report={"version":"HarmonyBot V51 historical replay inside V58","actual":{"baskets":n,"net":net,"pf":pf,"expectancy":exp,"win_rate":wr,"max_dd_pct":dd},"expected":expected,"checks":checks,"pass":ok}
(out/"V58_V51_HISTORICAL_REPLAY.json").write_text(json.dumps(report,indent=2))
(out/"replay.out").write_text("true" if ok else "false")
print(json.dumps(report,indent=2))
if not ok: raise SystemExit("V51 historical replay mismatch")
