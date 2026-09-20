from pathlib import Path
s=Path("HarmonyBot-V55/src/HarmonyBotV55.cs").read_text(encoding="utf-8")
checks={"identity":"class HarmonyBotV55","rr":"DefaultValue = 2.0","risk":"Basket Risk %","shadow":"RESEARCH_PLANE_NO_CAPITAL_ADMISSION","isolation":"return -1000000.0","no_live_route":"if (false && EnableUniversalHarmonicLiberation"}
bad=[k for k,v in checks.items() if v not in s]
if bad: raise SystemExit("V55 contract FAIL: "+",".join(bad))
print("V55 champion-core/evidence-admission contract PASS")
