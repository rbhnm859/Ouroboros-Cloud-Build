#!/usr/bin/env python3
"""Custody-pinned 2016–2020 R18 closed HCOG family census, NOT a new backtest."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from collections import Counter
from dual_horizon_research import FAMILIES

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def parse_outcome(raw):
    if "[V72-HCOG-OUTCOME]" not in raw:return None
    text=raw.split("[V72-HCOG-OUTCOME]",1)[1]
    m=re.search(r"(?<!\S)family=(\S+)",text)
    n=re.search(r"(?<!\S)setup=(\S+)",text)
    if not m or not n:raise ValueError("malformed family/outcome record")
    fam=m.group(1)
    if fam not in FAMILIES:raise ValueError("unknown source family "+fam)
    return fam,n.group(1)

def report(files,lock):
    artifacts={}
    for path in files:
        with zipfile.ZipFile(path) as z:
            custody=json.loads(z.read("R18_SEMANTIC_CUSTODY.json"))
            year=int(custody["window"][1:])
            if year not in range(2016,2021) or year in artifacts:
                raise ValueError("unapproved/duplicate research year")
            if any(custody.get(k) for k in ("burned_used","validation_used","fresh_used")):
                raise ValueError("protected data contamination")
            digest=sha256(path)
            if digest!=lock["old_source_artifact_hashes"][str(year)]:
                raise ValueError("ZIP custody hash mismatch")
            paths=[p for p in z.namelist() if p.endswith("-R15.log")]
            if len(paths)!=1:raise ValueError("missing/duplicate source log")
            counts=Counter();unique={f:set() for f in FAMILIES}
            with z.open(paths[0]) as f:
                for b in f:
                    rec=parse_outcome(b.decode("utf-8","strict"))
                    if rec:
                        fam,setup=rec;counts[fam]+=1;unique[fam].add(setup)
            artifacts[year]={"year":year,"source_sha256":digest,
                "outcome_rows":sum(counts.values()),
                "family_rows":{f:counts[f] for f in FAMILIES},
                "family_distinct_setups":{f:len(unique[f]) for f in FAMILIES},
                "note":"closed outcomes only: cannot infer all detected signals or performance"}
    if sorted(artifacts)!=list(range(2016,2021)):raise ValueError("missing research year")
    totals={f:sum(artifacts[y]["family_rows"][f] for y in artifacts) for f in FAMILIES}
    total=sum(totals.values())
    return {"schema":"V74_FR1_R18_CLOSED_FAMILY_BASELINE_V1","research_only":True,
        "source_run":37824462498,"burned_used":False,"new_strategy_tested":False,
        "families":FAMILIES,"years":[artifacts[y] for y in sorted(artifacts)],
        "total_closed_outcome_rows":total,"family_closed_outcome_rows":totals,
        "abcd_share":totals["ABCD"]/total if total else None,
        "unobserved_family_does_not_prove_no_detection":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifact-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    lock=json.loads((Path(__file__).parent/"RESEARCH_LOCK.json").read_text())
    files=sorted(a.artifact_dir.glob("*.zip"))
    obj=report(files,lock)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    print("Closed family outcomes",obj["total_closed_outcome_rows"],
          "ABCD",obj["family_closed_outcome_rows"]["ABCD"],
          "Research-only/no new profit claims")
if __name__=="__main__":main()
