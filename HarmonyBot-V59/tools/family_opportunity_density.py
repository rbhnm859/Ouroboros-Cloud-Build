#!/usr/bin/env python3
import json, pathlib, re, sys
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
stages=["raw_paths","identity_pass","prz_pass","temporal_pass","legal_rr","shadow","mfe_positive","baseline_positive","capture_positive","capital_admissible","executed"]
book={f:{s:0 for s in stages} for f in families}

for p in root.rglob("*.log"):
    for line in p.read_text(errors="ignore").splitlines():
        m=re.search(r"pattern=(.*?)\s+(?:route=|pass=|detected=)",line)
        pattern=m.group(1).strip() if m else None
        if pattern not in book: continue
        if "TOPOLOGY_ATTEMPT" in line: book[pattern]["raw_paths"]+=1
        if "PATTERN_DETECTED" in line: book[pattern]["identity_pass"]+=1
        if "PRZ_" in line and ("WAIT" in line or "PASS" in line or "ENTER" in line): book[pattern]["prz_pass"]+=1
        if "NATIVE_TEMPORAL_PASS" in line or "FAMILY-CONTRACT-SUMMARY" in line: book[pattern]["temporal_pass"]+=1
        if "TARGET_RR" not in line and "BASKET_PLANNED" in line: book[pattern]["legal_rr"]+=1
        if "[V59-SHADOW-CLOSED]" in line:
            book[pattern]["shadow"]+=1
            mm=re.search(r"mfeR=([-0-9.]+).*realizedR=([-0-9.]+)",line)
            if mm:
                if float(mm.group(1))>0: book[pattern]["mfe_positive"]+=1
                if float(mm.group(2))>0: book[pattern]["baseline_positive"]+=1
        if "[V59-CAPTURE-CLOSED]" in line:
            mm=re.search(r"hybridR=([-0-9.]+)",line)
            if mm and float(mm.group(1))>0: book[pattern]["capture_positive"]+=1
        if "CALIBRATED_CAPITAL_ADMIT" in line: book[pattern]["capital_admissible"]+=1
        if "EXECUTED" in line and "[V59-PIPELINE]" not in line: book[pattern]["executed"]+=1

total_shadow=sum(x["shadow"] for x in book.values())
report={"version":"HarmonyBot V59","families":book,"total_shadow_opportunities":total_shadow,
        "research_supply_target_1p5y":200,"supply_target_met":total_shadow>=200}
(out/"V59_FAMILY_OPPORTUNITY_DENSITY_REPORT.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
