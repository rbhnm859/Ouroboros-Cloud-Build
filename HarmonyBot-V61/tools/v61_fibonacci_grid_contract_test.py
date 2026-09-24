#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8")
for t in ["new[] { 0.0, .236, .382, .618 }","new[] { .40, .30, .20, .10 }","new[] { 0.0, .236 }","new[] { .65, .35 }","new[] { 0.0, .236, .382 }","new[] { .50, .30, .20 }"]: assert t in s,t
print("V61 Fibonacci Grid contract PASS")
