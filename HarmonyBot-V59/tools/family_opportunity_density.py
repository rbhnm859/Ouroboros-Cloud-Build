#!/usr/bin/env python3
import json, pathlib, re, sys

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
stages=["raw_paths","identity_pass","prz_pass","temporal_pass","legal_rr","shadow","mfe_positive","baseline_positive","capture_positive","capital_admissible","executed"]
book={f:{s:0 for s in stages} for f in families}

truth_rx=re.compile(r"\[V59-DETECTOR-TRUTH\]\s+pattern=(.*?)\s+stage=(\S+)\s+count=(\d+)")
pipe_rx=re.compile(r"\[V59-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+).*?basketPlanned=(\d+).*?executed=(\d+)")
shadow_rx=re.compile(r"\[V59-SHADOW-CLOSED\].*?pattern=(.*?)\s+route=.*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)")
capture_rx=re.compile(r"\[V59-CAPTURE-CLOSED\].*?pattern=(.*?)\s+route=.*?hybridR=([-0-9.]+)")
admit_rx=re.compile(r"\[V59-CALIBRATED-ADMISSION\].*?pattern=(.*?)\s+")

for p in root.rglob("*.log"):
    txt=p.read_text(errors="ignore")
    for m in truth_rx.finditer(txt):
        pat,stage,n=m.group(1).strip(),m.group(2),int(m.group(3))
        if pat not in book: continue
        if stage=="TOPOLOGY_ATTEMPT": book[pat]["raw_paths"]+=n
        elif stage=="RATIO_IDENTITY_PASS": book[pat]["identity_pass"]+=n
    for m in pipe_rx.finditer(txt):
        pat=m.group(1).strip()
        if pat not in book: continue
        book[pat]["prz_pass"]+=int(m.group(5))
        book[pat]["temporal_pass"]+=int(m.group(7))
        book[pat]["legal_rr"]+=int(m.group(8))
        book[pat]["executed"]+=int(m.group(9))
    for m in shadow_rx.finditer(txt):
        pat=m.group(1).strip()
        if pat not in book: continue
        mfe=float(m.group(2)); realized=float(m.group(4))
        book[pat]["shadow"]+=1
        if mfe>0: book[pat]["mfe_positive"]+=1
        if realized>0: book[pat]["baseline_positive"]+=1
    for m in capture_rx.finditer(txt):
        pat=m.group(1).strip()
        if pat in book and float(m.group(2))>0: book[pat]["capture_positive"]+=1
    for m in admit_rx.finditer(txt):
        pat=m.group(1).strip()
        if pat in book: book[pat]["capital_admissible"]+=1

total_shadow=sum(x["shadow"] for x in book.values())
active_families=sum(1 for x in book.values() if x["shadow"]>0)
report={
    "version":"HarmonyBot V59",
    "families":book,
    "total_shadow_opportunities":total_shadow,
    "families_with_shadow":active_families,
    "research_supply_target_1p5y":200,
    "supply_target_met":total_shadow>=200,
    "all_12_families_observed_in_shadow":active_families==12,
}
(out/"V59_FAMILY_OPPORTUNITY_DENSITY_REPORT.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
