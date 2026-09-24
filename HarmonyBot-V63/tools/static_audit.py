#!/usr/bin/env python3
import pathlib,json,sys
s=pathlib.Path(sys.argv[1]).read_text()
c={"identity":"class HarmonyBotV63" in s and 'BotPrefix = "HB63"' in s,"golden":'V63_GOLDEN_V51_CONTROL' in s,"regimes":all(x in s for x in ["R1_TREND_EXPANSION","R2_TREND_EXHAUSTION","R3_COMPRESSION","R4_TRANSITION"]),"cell":"V63CellKey" in s and "V63PolicyForCell" in s,"conditional":".60,.25,.15,0.0" in s.replace(" ",""),"l3":"V63-L3-SHADOW-ONLY" in s,"risk":"ActualBasketWorstRisk" in s,"no_projected_d":"TryProjectProfile" not in s}
print(json.dumps({"checks":c,"pass":all(c.values())},indent=2)); raise SystemExit(0 if all(c.values()) else 2)