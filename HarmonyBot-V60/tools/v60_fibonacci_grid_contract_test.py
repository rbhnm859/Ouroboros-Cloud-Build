#!/usr/bin/env python3
from pathlib import Path
import re
SRC=Path("HarmonyBot-V60/src/HarmonyBotV60.cs").read_text(encoding="utf-8")
required=[
 "V60ActiveGridRiskWeights","V60GridEnabledForVariant","V60AdaptiveGridForVariant",
 'new[]{.65,.35}','new[]{.50,.30,.20}','new[]{.40,.30,.20,.10}',
 "BasketRiskAmount = Account.Equity * BasketRiskPercent / 100.0",
 "worst > plan.BasketRiskAmount + 1e-8",
 "GridCancelMfeR",
 "fraction > .6180001"
]
for x in required: assert x in SRC, f"missing V60 Grid contract token: {x}"
assert "Martingale" not in SRC
assert "DCA" not in SRC
assert "Recovery" not in SRC
# Static mathematical contract for monotonic weights.
for w in ([.65,.35],[.50,.30,.20],[.40,.30,.20,.10],[3/7,2/7,1/7,1/7]):
    assert abs(sum(w)-1)<1e-12
    assert all(w[i]>=w[i+1] for i in range(len(w)-1))
print("V60 Fibonacci Grid contract PASS")
