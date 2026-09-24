#!/usr/bin/env python3
from pathlib import Path
a=Path("HarmonyBot-V61/tools/analyze_dev4.py").read_text(encoding="utf-8"); c=Path("HarmonyBot-V61/tools/cluster_evidence.py").read_text(encoding="utf-8")
for t in ["p95_winner_r","max_winner_r","delta_net","delta_pf","delta_expectancy","delta_dd","delta_frequency","right_tail_preserved"]: assert t in a,t
for t in ["setup","pattern","route","window","unique_geometries"]: assert t in c,t
print("V61 evidence integrity contract PASS")
