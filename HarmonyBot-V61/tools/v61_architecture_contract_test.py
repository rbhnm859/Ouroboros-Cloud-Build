#!/usr/bin/env python3
from pathlib import Path
s=Path("HarmonyBot-V61/src/HarmonyBotV61.cs").read_text(encoding="utf-8")
checks={"variants":all(x in s for x in ["V61_V51_EXACT_CONTROL","V61_DAG_CAPITAL_CONTROL","V61_CHAMPION_FIB_GRID","V61_GRID_REGIME_SURVIVAL","V61_COMMERCIAL_MAX"]),"grid":"V61RouteGridContract" in s and ".40, .30, .20, .10" in s and ".65, .35" in s and ".50, .30, .20" in s,"veto_only":"V61RegimeSurvivalPass" in s and "V61_REGIME_SURVIVAL_VETO" in s,"rat_only":'sig.PatternName != "Rat"' in s and "V61RatMinGeometry" in s and "V61RatMinPrz" in s and "V61RatMinConfidence" in s,"runner":"RunnerTarget" in s and "RunnerEligible" in s and "ConfigureV61SelectiveRunner" in s,"abcd_off":"V61_ABCD_STANDALONE_CAPITAL_OFF" in s,"dag":"UpdateV61StageAwareFamilyCompletionEvidence" in s and "i > c.V61DagAnchorBar" in s,"grid_cancel":"basket.PeakR >= GridCancelMfeR" in s and '"MFE_GRID_CANCEL"' in s,"risk":"ActualBasketWorstRisk" in s and "basket.InitialBasketRisk + 1e-8" in s}
bad=[k for k,v in checks.items() if not v]; print({"version":"HarmonyBot V61","checks":checks,"pass":not bad})
if bad: raise SystemExit("V61 architecture contract FAIL: "+",".join(bad))
