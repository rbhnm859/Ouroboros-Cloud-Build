#!/usr/bin/env python3
from pathlib import Path
SRC=Path("HarmonyBot-V60/src/HarmonyBotV60.cs").read_text(encoding="utf-8")
for x in [
 "EnableV60ConvexCaptureResearch","EnableV60RunnerResearch","V60RunnerFraction",
 "V60ConvexPolicy","double prevMfe=x.MfeR","prevMfe>=protectTrigger",
 "prevMfe>=trailTrigger","RunnerArmed","ConvexCoreR","ConvexR"
]:
    assert x in SRC, f"missing V60 convex capture token: {x}"
# Guard against same-bar optimistic use: policy decisions must be made from prevMfe,
# while x.MfeR is updated only later in the loop.
p=SRC.index("double prevMfe=x.MfeR")
decision=SRC.index("if(EnableV60ConvexCaptureResearch",p)
update=SRC.index("x.MfeR=Math.Max",decision)
assert decision < update
assert "prevMfe>=protectTrigger" in SRC[decision:update]
assert "prevMfe>=trailTrigger" in SRC[decision:update]
print("V60 Convex Capture / Runner prior-bar contract PASS")
