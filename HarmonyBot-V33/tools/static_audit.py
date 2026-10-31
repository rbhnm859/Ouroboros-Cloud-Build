#!/usr/bin/env python3
import pathlib,json,sys,re
s=pathlib.Path(sys.argv[1]).read_text()
checks={
"v33_class":"class HarmonyBotV33" in s,
"frozen_fib":"new[] { 0.0, .236, .382, .618 }" in s,
"frozen_weights":"3.0 / 7.0" in s and "2.0 / 7.0" in s,
"basket_risk_one":'[Parameter("Basket Risk %", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 1.0)]' in s,
"protection_frontier":"AdvanceBasketProtectionFrontier" in s and "ProtectionFrontier" in s,
"no_old_stop_manager":"ImproveBasketStops(" not in s,
"live_risk_reconcile":"CurrentFilledStructuralRisk" in s and "CurrentPendingStructuralRisk" in s and "LIVE_FILLED_RISK_REJECT" in s,
"deeper_thesis_gate":"DeeperLegThesisEligible" in s,
"broker_safe_stop":"BrokerSafeStop" in s,
"completed_m1":"LastClosedIndex(_m1Bars)" in s,
"no_recovery":not re.search(r"\bMartingale\b|\bDCA\b|Loss Averaging|Recovery Grid",s,re.I),
"no_v32_telemetry":"[V32-" not in s
}
status="PASS" if all(checks.values()) else "FAIL"
pathlib.Path("V33_ARCHITECTURE_AUDIT.json").write_text(json.dumps({"status":status,"checks":checks},indent=2))
print(json.dumps({"status":status,"checks":checks},indent=2))
raise SystemExit(0 if status=="PASS" else 2)
