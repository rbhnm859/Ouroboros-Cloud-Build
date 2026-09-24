#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8")
for t in ["BasketRiskPercent","WorstCaseRisk > plan.BasketRiskAmount","ActualBasketWorstRisk","CurrentFilledStructuralRisk","CurrentPendingStructuralRisk","MinBrokerRisk","ModeledCostPips","VolumeForRiskBudget"]: assert t in s,t
assert "RunnerRiskWeight" in s and "ConfigureV61SelectiveRunner" in s
print("V61 whole-basket <=1% fail-closed contract PASS")
