#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8"); b=s.split("private bool UpdateV61StageAwareFamilyCompletionEvidence",1)[1].split("private bool SelectCanonicalBasketTarget",1)[0]
for bad in ["[i + 1]","[i+1]","[i + 2]","[i+2]"]: assert bad not in b,bad
assert "i > c.V61DagAnchorBar" in b
print("V61 completed-bar/no-lookahead DAG contract PASS")
