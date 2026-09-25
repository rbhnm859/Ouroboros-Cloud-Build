#!/usr/bin/env python3
import pathlib,re,json,sys
s=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={}
for f in families:
    checks[f+"_profile"]=('"' + f + '"') in s
    checks[f+"_grid"]=(('V67SetGrid("' + f + '"') in s)
checks["abcd_broad_not_capital"]="ABCD_LEGACY_BROAD" in s and "V67AllowBroadAbcdCapital" in s
checks["risk_weights_present"]=all(x in s for x in ["new[] { .40, .30, .20, .10 }","new[] { .72, .28 }","new[] { .55, .30, .15 }"])
checks["grid_cancel_mfe"]="GridCancelMfeR" in s
o={"version":"V67","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 68)
