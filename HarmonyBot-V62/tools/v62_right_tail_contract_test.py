import pathlib
s=pathlib.Path("HarmonyBot-V62/tools/analyze_dev4.py").read_text()
for x in ["right_tail_min_ratio",">=.80","max_winner_preservation_ratio","alpha_preservation_gate"]:assert x in s,x
print("PASS")
