import pathlib
s=pathlib.Path("HarmonyBot-V62/src/HarmonyBotV62.cs").read_text()
for x in ["Basket Risk %","MaxValue = 1.0","ActualBasketWorstRisk","WORST_CASE_BASKET_RISK","MinFreeMarginRiskMultiple","FailClosePosition"]:assert x in s,x
print("PASS")
