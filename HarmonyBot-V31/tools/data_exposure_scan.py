#!/usr/bin/env python3
import pathlib,re,json
root=pathlib.Path(".")
files=[p for p in root.glob(".github/workflows/*") if p.is_file()]
mentions=[]
for p in files:
    try: t=p.read_text(errors="ignore")
    except: continue
    if "HarmonyBot" not in t and "harmonybot" not in t: continue
    dates=sorted(set(re.findall(r"\b(?:20\d{2})[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b",t)))
    mentions.append({"path":str(p),"dates":dates})
known_runs=[
  {"run_id":35338325244,"purpose":"commercial convergence","status":"EXPOSED"},
  {"run_id":35342318165,"purpose":"architecture redesign","status":"EXPOSED"},
  {"run_id":35345647911,"purpose":"V30 major architecture","status":"EXPOSED"},
  {"run_id":35345623088,"purpose":"V30 duplicate execution","status":"EXPOSED"}
]
ledger={
 "policy":"Any window used for prior HarmonyBot development/validation/backtest or not provably isolated is not called untouched.",
 "workflow_files_scanned":len(mentions),
 "known_runs":known_runs,
 "windows":{
   "DEV-A":{"range":"2021-01-04..2021-06-30","status":"EXPOSED_DEVELOPMENT"},
   "DEV-B":{"range":"2021-07-01..2021-12-31","status":"EXPOSED_DEVELOPMENT"},
   "DEV-C":{"range":"2022-01-03..2022-06-30","status":"EXPOSED_DEVELOPMENT"},
   "2018-H2":{"range":"2018-07-02..2018-12-31","status":"EXPOSED_PREVIOUS_FINAL_HOLDOUT"},
   "2019-H1":{"range":"2019-01-02..2019-06-28","status":"EXPOSED_PREVIOUS_OOS"},
   "2019-H2":{"range":"2019-07-01..2019-12-31","status":"EXPOSED_PREVIOUS_VALIDATION_AND_100_GATE"},
   "VALIDATION_RESERVED":{"range":"UNASSIGNED","status":"RESERVED_NOT_PROVEN"},
   "OOS_RESERVED":{"range":"UNASSIGNED","status":"RESERVED_NOT_PROVEN"},
   "FINAL_HOLDOUT":{"range":"UNASSIGNED","status":"UNTOUCHED_NOT_PROVEN"}
 },
 "workflow_mentions":mentions,
 "downstream_authorized":False,
 "reason":"Repository/workflow scan cannot prove that an unassigned historical market interval has never been inspected in prior deleted/changed runs. Development may run; downstream must remain locked until a genuinely pre-reserved interval is established."
}
pathlib.Path("DATA_EXPOSURE_LEDGER.json").write_text(json.dumps(ledger,indent=2))
print(json.dumps({"workflow_files_scanned":len(mentions),"downstream_authorized":False},indent=2))
