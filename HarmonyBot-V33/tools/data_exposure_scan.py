#!/usr/bin/env python3
import pathlib,re,json
root=pathlib.Path(".")
mentions=[]
for p in root.glob(".github/workflows/*"):
    if not p.is_file(): continue
    try:t=p.read_text(errors="ignore")
    except:continue
    if "HarmonyBot" not in t and "harmonybot" not in t: continue
    dates=sorted(set(re.findall(r"\b(?:20\d{2})[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b",t)))
    mentions.append({"path":str(p),"dates":dates})
ledger={
 "policy":"Any period previously used or not provably pre-reserved is not described as untouched.",
 "workflow_files_scanned":len(mentions),
 "known_exposure":[
  {"run_id":35338325244,"version":"pre-V31","status":"EXPOSED"},
  {"run_id":35342318165,"version":"pre-V31","status":"EXPOSED"},
  {"run_id":35345647911,"version":"V30","status":"EXPOSED"},
  {"run_id":35359904930,"version":"V31","status":"EXPOSED_DEVELOPMENT"},
  {"run_id":35363039611,"version":"V32","status":"EXPOSED_DEVELOPMENT"},
  {"run_id":35364331428,"version":"V32","status":"EXPOSED_DEVELOPMENT"}
 ],
 "windows":{
  "DEV-A":{"range":"2021-01-04..2021-06-30","status":"EXPOSED_ARCHITECTURE_VERIFICATION"},
  "DEV-B":{"range":"2021-07-01..2021-12-31","status":"EXPOSED_ARCHITECTURE_VERIFICATION"},
  "DEV-C":{"range":"2022-01-03..2022-06-30","status":"EXPOSED_ARCHITECTURE_VERIFICATION"},
  "2018-H2":{"range":"2018-07-02..2018-12-31","status":"EXPOSED_PREVIOUS_FINAL_HOLDOUT"},
  "2019-H1":{"range":"2019-01-02..2019-06-28","status":"EXPOSED_PREVIOUS_OOS"},
  "2019-H2":{"range":"2019-07-01..2019-12-31","status":"EXPOSED_PREVIOUS_VALIDATION_AND_100_GATE"},
  "VALIDATION_RESERVED":{"range":"UNASSIGNED","status":"RESERVED_NOT_PROVEN"},
  "OOS_RESERVED":{"range":"UNASSIGNED","status":"RESERVED_NOT_PROVEN"},
  "FINAL_HOLDOUT":{"range":"UNASSIGNED","status":"UNTOUCHED_NOT_PROVEN"}
 },
 "workflow_mentions":mentions,
 "downstream_authorized":False,
 "reason":"No genuinely pre-reserved fresh Validation/OOS/Final Holdout range is presently proven untouched."
}
pathlib.Path("DATA_EXPOSURE_LEDGER.json").write_text(json.dumps(ledger,indent=2))
print(json.dumps({"workflow_files_scanned":len(mentions),"downstream_authorized":False},indent=2))
