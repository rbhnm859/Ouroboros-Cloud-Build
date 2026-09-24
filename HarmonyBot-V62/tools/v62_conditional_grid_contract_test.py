import pathlib
s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
for x in ["new[] { .60, .25, .15 }","V62-L3-SHADOW","TryArmNextConditionalLeg","RouteSpecificM1EvidencePass","targetBasis = V62ConditionalGridEnabled() ? anchor"]:assert x in s,x
print("PASS")
