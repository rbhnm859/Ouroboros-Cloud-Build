import pathlib
s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
assert "LastClosedIndex" in s and "allCompletedBars=true" in s and "projectedD=false" in s
print("PASS")
