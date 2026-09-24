import pathlib
s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text();a=pathlib.Path("HarmonyBot-V62/tools/audit_report.py").read_text()
for x in ["V62-ECONOMIC-ATTRIBUTION","V62-LEG-ECON","captureRatio","timeToMfe"]:assert x in s,x
for x in ["leg_economics","mean_capture_ratio"]:assert x in a,x
print("PASS")
