#!/usr/bin/env python3
import glob,json,pathlib,collections,statistics
rows=[json.load(open(p)) for p in glob.glob("all/*.json") if pathlib.Path(p).name.startswith(("R1-DEV","R2-DEV","R3-DEV"))]
edge={}
for x in rows:
    edge.setdefault(x["candidate"],{})[x["window"]]={
      "baskets":x["baskets"],"pf":x["pf"],"net":x["net"],"expectancy":x["expectancy"],"win_rate_pct":x["win_rate_pct"],
      "max_dd_pct":x["max_dd_pct"],"pattern":x["pattern"],"architecture":x["architecture"]}
pathlib.Path("EDGE_ATTRIBUTION_MATRIX.json").write_text(json.dumps(edge,indent=2))

devb={x["candidate"]:{
  "pf":x["pf"],"net":x["net"],"expectancy":x["expectancy"],"baskets":x["baskets"],"pattern":x["pattern"],
  "admission":x["architecture"].get("pattern_admission",{}),"mean_context":x["architecture"].get("mean_context",0),
  "mean_confirmation":x["architecture"].get("mean_confirmation",0),"mean_mfe_r":x["architecture"].get("mean_mfe_r",0),
  "mean_mae_r":x["architecture"].get("mean_mae_r",0),"top3_loss_pct":x["top3_loss_pct"]
} for x in rows if x["window"]=="DEV-B"}
pathlib.Path("DEV_B_FAILURE_DECOMPOSITION.json").write_text(json.dumps(devb,indent=2))

life={}
for c in ("R1","R2","R3"):
    xs=[x for x in rows if x["candidate"]==c]
    life[c]={
      "lifecycle_samples":sum(x["architecture"].get("lifecycle_count",0) for x in xs),
      "mean_window_mfe_r":statistics.mean([x["architecture"].get("mean_mfe_r",0) for x in xs]) if xs else 0,
      "mean_window_mae_r":statistics.mean([x["architecture"].get("mean_mae_r",0) for x in xs]) if xs else 0,
      "giveback_exits":sum(x["architecture"].get("giveback_exit_count",0) for x in xs),
      "by_window":{x["window"]:x["architecture"].get("lifecycle_by_pattern",{}) for x in xs}
    }
pathlib.Path("LIFECYCLE_MFE_MAE_ANALYSIS.json").write_text(json.dumps(life,indent=2))
