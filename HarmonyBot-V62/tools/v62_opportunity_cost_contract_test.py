import pathlib
a=pathlib.Path("HarmonyBot-V62/tools/audit_report.py").read_text();s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
for x in ["rejected_cohort_quality","gate_telemetry","mean_shadow_mfe_r"]:assert x in a,x
for x in ["V62-GATE-REJECT","V62-GATE-PASS","V51-ENTRY-ANCHOR-FORENSICS"]:assert x in s,x
print("PASS")
