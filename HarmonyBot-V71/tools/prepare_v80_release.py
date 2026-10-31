#!/usr/bin/env python3
import pathlib,sys,json
mode=sys.argv[1].upper(); risk=float(sys.argv[2]); root=pathlib.Path(sys.argv[3])
if mode not in ("SINGLE","GRID"): raise SystemExit("mode must be SINGLE or GRID")
if risk not in (1.0,2.0,3.0,5.0): raise SystemExit("risk must be preregistered 1/2/3/5")
p=root/"src/Architecture/HarmonyBotV71.V73OpportunityUniverse.cs"
s=p.read_text()
old='[Parameter("Enable V74 Embedded Frozen Policy", DefaultValue = false)]'
if old not in s: raise SystemExit("embedded default anchor missing")
s=s.replace(old,'[Parameter("Enable V74 Embedded Frozen Policy", DefaultValue = true)]')
p.write_text(s)
p=root/"src/HarmonyBotV71.cs"
s=p.read_text()
a='[Parameter("V71 Expansion Execution", DefaultValue = false)]'
b='[Parameter("V71 Expansion Grid", DefaultValue = false)]'
c='[Parameter("V71 Expansion Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0)]'
for x in (a,b,c):
    if x not in s: raise SystemExit("commercial default anchor missing: "+x)
s=s.replace(a,'[Parameter("V71 Expansion Execution", DefaultValue = true)]')
s=s.replace(b,f'[Parameter("V71 Expansion Grid", DefaultValue = {str(mode=="GRID").lower()})]')
rv=str(int(risk)) if risk.is_integer() else str(risk)
s=s.replace(c,f'[Parameter("V71 Expansion Risk %", DefaultValue = {rv}, MinValue = 0.1, MaxValue = 5.0)]')
p.write_text(s)
print(json.dumps({"mode":mode,"risk_pct":risk,"embedded_policy_default":True,"expansion_execution_default":True},indent=2))
