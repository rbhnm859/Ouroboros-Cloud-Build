#!/usr/bin/env python3
import json,pathlib,re,sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
stages=["raw_paths","identity_pass","prz_pass","temporal_pass","legal_rr","shadow","mfe_positive","baseline_positive","convex_positive","capital_admissible","executed"]
book={f:{s:0 for s in stages} for f in families}
truth=re.compile(r"\[V60-DETECTOR-TRUTH\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
contract=re.compile(r"\[V60-FAMILY-CONTRACT-SUMMARY\]\s+pattern=(.*?)\s+pass=(\d+)")
shadow=re.compile(r"\[V60-SHADOW-CLOSED\].*?pattern=(.*?)\s+route=.*?mfeR=([-0-9.]+).*?realizedR=([-0-9.]+)")
capture=re.compile(r"\[V60-CAPTURE-CLOSED\].*?pattern=(.*?)\s+route=.*?convexR=([-0-9.]+)")
for p in root.rglob("*.log"):
    txt=p.read_text(errors="ignore")
    for m in truth.finditer(txt):
        pat,stage,n=m.group(1).strip(),m.group(2),int(m.group(3))
        if pat not in book: continue
        if stage=="TOPOLOGY_ATTEMPT": book[pat]["raw_paths"]+=n
        elif stage=="RATIO_IDENTITY_PASS": book[pat]["identity_pass"]+=n
    for m in contract.finditer(txt):
        pat=m.group(1).strip()
        if pat in book: book[pat]["temporal_pass"]+=int(m.group(2))
    for m in shadow.finditer(txt):
        pat=m.group(1).strip()
        if pat not in book: continue
        mfe,real=float(m.group(2)),float(m.group(3)); book[pat]["shadow"]+=1
        if mfe>0: book[pat]["mfe_positive"]+=1
        if real>0: book[pat]["baseline_positive"]+=1
    for m in capture.finditer(txt):
        pat=m.group(1).strip()
        if pat in book and float(m.group(2))>0: book[pat]["convex_positive"]+=1
total=sum(v["shadow"] for v in book.values())
report={"version":"HarmonyBot V60","families":book,"total_shadow_opportunities":total,
        "families_with_shadow":sum(v["shadow"]>0 for v in book.values()),
        "research_supply_target_1p5y":200,"supply_target_met":total>=200}
(out/"V60_FAMILY_OPPORTUNITY_DENSITY_REPORT.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
