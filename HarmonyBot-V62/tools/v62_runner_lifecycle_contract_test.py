import pathlib
s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
for x in ["ExecuteImmediateRunnerLeg","V62-RUNNER-ASSIGN","V62-RUNNER-SURVIVED-CANONICAL","runnerFilled","runnerClosed"]:assert x in s,x
print("PASS")
