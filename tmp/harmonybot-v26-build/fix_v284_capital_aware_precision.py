from pathlib import Path
import re

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# HarmonyBot V28.4 Capital-Aware Precision Entry RC
# Goals:
# - keep all harmonic families, Fibonacci Grid, 1% base RiskPercent and 10% MaxDD contract
# - stop silently reverting SmallAccountMode to the global 100-pip floor after equity rises above threshold
# - preserve the harmonic structural stop; wait for a better PRZ entry instead of compressing it into the risk budget
# - cap only the EXTRA Fibonacci Grid stop extension to the executable risk budget
# - verify actual normalized-volume all-in risk, because broker/API normalization can otherwise round up to min volume
# - support a fixed evaluation start after historical warmup to reduce start-date/state dependency

# -----------------------------------------------------------------------------
# Version + counters
# -----------------------------------------------------------------------------
old='private const string CommercialIteration = "V28.3-Execution-Quality-RC";'
if old not in s: raise SystemExit('V28.3 version marker missing')
s=s.replace(old,'private const string CommercialIteration = "V28.4-Capital-Aware-Precision-RC";',1)

field='        private long _v283GridOrders;\n'
if field not in s: raise SystemExit('V28.3 field anchor missing')
s=s.replace(field,field+'''        private long _v284PrecisionReady;\n        private long _v284PrecisionWait;\n        private long _v284CapitalHardReject;\n        private long _v284NativeRiskReject;\n        private long _v284GridStopCapped;\n        private long _v284WarmupSkipped;\n        private bool _v284EvaluationParsed;\n        private DateTime _v284EvaluationStartUtc;\n''',1)

# -----------------------------------------------------------------------------
# Controls: diagnostic/evaluation and capital-aware PRZ precision execution.
# -----------------------------------------------------------------------------
anchor='''        [Parameter("Min Pivot Quality", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinPivotQuality { get; set; }\n'''
if anchor not in s: raise SystemExit('V28.3 parameter anchor missing')
params='''\n        [Parameter("Capital-Aware Precision Entry", DefaultValue = true)]\n        public bool EnableCapitalAwarePrecisionEntry { get; set; }\n\n        [Parameter("Precision PRZ Max Distance ATR", DefaultValue = 0.45, MinValue = 0.10, MaxValue = 1.50)]\n        public double PrecisionPrzMaxDistanceAtr { get; set; }\n\n        [Parameter("Precision Max Wait ATR", DefaultValue = 1.25, MinValue = 0.10, MaxValue = 4.00)]\n        public double PrecisionMaxWaitAtr { get; set; }\n\n        [Parameter("Capital Safety Headroom", DefaultValue = 0.98, MinValue = 0.80, MaxValue = 1.00)]\n        public double CapitalSafetyHeadroom { get; set; }\n\n        [Parameter("Cap Grid Stop To Risk Budget", DefaultValue = true)]\n        public bool CapGridStopToRiskBudget { get; set; }\n\n        [Parameter("Evaluation Start UTC ISO", DefaultValue = "")]\n        public string EvaluationStartUtcIso { get; set; }\n'''
s=s.replace(anchor,anchor+params,1)

# -----------------------------------------------------------------------------
# Small-account precedence bug fix.
# Previous one-pass validation accepted IsSmallAccountMode() because the helper name
# contains the substring SmallAccountMode, but the helper still applied an equity threshold.
# Explicit SmallAccountMode=true now controls the effective SL/TP floors for the whole run.
# -----------------------------------------------------------------------------
old='''        private double EffectiveMinStopLossPips()\n        {\n            return IsSmallAccountMode() ? Math.Min(MinStopLossPips, SmallAccountMinSLPips) : MinStopLossPips;\n        }\n\n        private double EffectiveMinTakeProfitPips()\n        {\n            return IsSmallAccountMode() ? Math.Min(MinTakeProfitPips, SmallAccountMinTPPips) : MinTakeProfitPips;\n        }\n'''
new='''        private double EffectiveMinStopLossPips()\n        {\n            return SmallAccountMode ? Math.Min(MinStopLossPips, SmallAccountMinSLPips) : MinStopLossPips;\n        }\n\n        private double EffectiveMinTakeProfitPips()\n        {\n            return SmallAccountMode ? Math.Min(MinTakeProfitPips, SmallAccountMinTPPips) : MinTakeProfitPips;\n        }\n'''
if old not in s: raise SystemExit('effective small-account floor methods missing')
s=s.replace(old,new,1)

# -----------------------------------------------------------------------------
# Carry the actual harmonic D/C reference price into the execution layer.
# -----------------------------------------------------------------------------
anchor='        public double PivotQuality { get; set; }\n'
if anchor not in s: raise SystemExit('Signal quality field anchor missing')
s=s.replace(anchor,anchor+'        public double ReferencePrice { get; set; }\n',1)

anchor='''                PivotQuality = best.PivotQuality\n            };'''
if anchor not in s: raise SystemExit('signal construction anchor missing')
s=s.replace(anchor,'''                PivotQuality = best.PivotQuality,\n                ReferencePrice = referencePoint.Price\n            };''',1)

# -----------------------------------------------------------------------------
# Fixed evaluation window after warmup. Historical bars may be loaded before the
# evaluation start, while no live orders are allowed until the requested UTC time.
# -----------------------------------------------------------------------------
helper='''        private bool V284EvaluationWindowOpen()\n        {\n            if (string.IsNullOrWhiteSpace(EvaluationStartUtcIso)) return true;\n            if (!_v284EvaluationParsed)\n            {\n                _v284EvaluationParsed = true;\n                DateTimeOffset dto;\n                if (DateTimeOffset.TryParse(EvaluationStartUtcIso, out dto))\n                    _v284EvaluationStartUtc = dto.UtcDateTime;\n                else\n                {\n                    _v284EvaluationStartUtc = DateTime.MinValue;\n                    Print("[V284-WARMUP] Invalid EvaluationStartUtcIso={0}; evaluation gate disabled.", EvaluationStartUtcIso);\n                }\n            }\n            if (_v284EvaluationStartUtc == DateTime.MinValue) return true;\n            if (Server.Time < _v284EvaluationStartUtc)\n            {\n                _v284WarmupSkipped++;\n                return false;\n            }\n            return true;\n        }\n\n        private double V284MaxExecutableStopPips(double riskBudgetPct)\n        {\n            if (_symbol == null || Account.Equity <= 0 || riskBudgetPct <= 0 || _symbol.VolumeInUnitsMin <= 0) return 0;\n            try\n            {\n                double riskMoney = Account.Equity * riskBudgetPct / 100.0;\n                double raw = _symbol.PipsForFixedRisk(riskMoney, _symbol.VolumeInUnitsMin) - EstimateExecutionReservePips();\n                if (double.IsNaN(raw) || double.IsInfinity(raw)) return 0;\n                return Math.Max(0.0, raw * Math.Max(0.80, Math.Min(1.0, CapitalSafetyHeadroom)));\n            }\n            catch { return 0; }\n        }\n\n        private bool V284PrecisionEntryReady(Signal signal, double atrNow, double riskBudgetPct, out double maxStopPips)\n        {\n            maxStopPips = V284MaxExecutableStopPips(riskBudgetPct);\n            if (!EnableCapitalAwarePrecisionEntry) return true;\n            if (signal == null || _symbol == null || atrNow <= 0 || maxStopPips <= 0)\n            {\n                _v284CapitalHardReject++;\n                return false;\n            }\n\n            double entry = signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;\n            if (entry <= 0 || signal.StopLoss <= 0)\n            {\n                _v284CapitalHardReject++;\n                return false;\n            }\n\n            double floorPips = Math.Max(EffectiveMinStopLossPips(), MinStopDistancePips);\n            if (maxStopPips + 1e-9 < floorPips)\n            {\n                _v284CapitalHardReject++;\n                Print("[V284-CAPITAL-HARD] pattern={0} maxStop={1:F1} floor={2:F1} equity={3:F2} budget={4:F2}%",\n                    signal.PatternName ?? "NA", maxStopPips, floorPips, Account.Equity, riskBudgetPct);\n                return false;\n            }\n\n            double structuralStopPips = PriceToPips(Math.Abs(entry - signal.StopLoss));\n            double referenceDistanceAtr = signal.ReferencePrice > 0 ? Math.Abs(entry - signal.ReferencePrice) / atrNow : 0.0;\n\n            if (referenceDistanceAtr > Math.Max(0.10, PrecisionPrzMaxDistanceAtr))\n            {\n                _v284PrecisionWait++;\n                Print("[V284-PRECISION-WAIT] pattern={0} reason=PRZ_DISTANCE distAtr={1:F3} limit={2:F3}",\n                    signal.PatternName ?? "NA", referenceDistanceAtr, PrecisionPrzMaxDistanceAtr);\n                return false;\n            }\n\n            if (structuralStopPips > maxStopPips + 1e-9)\n            {\n                double improvePips = structuralStopPips - maxStopPips;\n                double improveAtr = PipsToPrice(improvePips) / atrNow;\n                if (improveAtr <= Math.Max(0.10, PrecisionMaxWaitAtr))\n                {\n                    _v284PrecisionWait++;\n                    Print("[V284-PRECISION-WAIT] pattern={0} reason=CAPITAL structuralSL={1:F1} maxStop={2:F1} improveAtr={3:F3}",\n                        signal.PatternName ?? "NA", structuralStopPips, maxStopPips, improveAtr);\n                }\n                else\n                {\n                    _v284CapitalHardReject++;\n                    Print("[V284-CAPITAL-HARD] pattern={0} structuralSL={1:F1} maxStop={2:F1} improveAtr={3:F3} limit={4:F3}",\n                        signal.PatternName ?? "NA", structuralStopPips, maxStopPips, improveAtr, PrecisionMaxWaitAtr);\n                }\n                return false;\n            }\n\n            _v284PrecisionReady++;\n            Print("[V284-PRECISION-READY] pattern={0} structuralSL={1:F1} maxStop={2:F1} przDistAtr={3:F3}",\n                signal.PatternName ?? "NA", structuralStopPips, maxStopPips, referenceDistanceAtr);\n            return true;\n        }\n\n'''
onbar='        protected override void OnBar()\n'
if onbar not in s: raise SystemExit('OnBar anchor missing')
s=s.replace(onbar,helper+onbar,1)

anchor='''                ResetCalendarStates(false);\n                PruneStateDictionaries();\n                UpdateRiskLocks();\n\n                if (IsEquityUnsafe()) return;\n'''
if anchor not in s: raise SystemExit('OnBar warmup insertion anchor missing')
s=s.replace(anchor,'''                ResetCalendarStates(false);\n                PruneStateDictionaries();\n                UpdateRiskLocks();\n\n                if (!V284EvaluationWindowOpen()) return;\n                if (IsEquityUnsafe()) return;\n''',1)

# -----------------------------------------------------------------------------
# Capital-aware entry preflight BEFORE legacy stop compression.
# This preserves the harmonic structural stop: if current price cannot support it,
# the bot waits for a better PRZ price rather than shortening the invalidation level.
# -----------------------------------------------------------------------------
anchor='''                double riskBudgetPct = GetTradeRiskBudgetPercent();\n                if (CommercialRiskEngine && !ApplyCommercialRiskGeometry(ref slPips, ref tpPips, riskBudgetPct))\n'''
if anchor not in s: raise SystemExit('risk preflight anchor missing')
s=s.replace(anchor,'''                double riskBudgetPct = GetTradeRiskBudgetPercent();\n                double v284MaxStopPips = 0;\n                if (CommercialRiskEngine && !V284PrecisionEntryReady(signal, atrNow, riskBudgetPct, out v284MaxStopPips))\n                    return;\n\n                if (CommercialRiskEngine && !ApplyCommercialRiskGeometry(ref slPips, ref tpPips, riskBudgetPct))\n''',1)

# -----------------------------------------------------------------------------
# Fibonacci Grid remains enabled. Only the extra stop extension beyond the harmonic
# structural stop may be capped to the executable all-in risk budget.
# -----------------------------------------------------------------------------
old='''                if (useGridForThisTrade)\n                {\n                    orderSlPips = slPips * GridStopFib;\n                    orderTpPips = null;\n                    _lastPrimaryRiskPips = slPips;\n                    volumeInUnits = CalculateVolumeByRisk(orderSlPips, riskBudgetPct);\n                }\n'''
new='''                if (useGridForThisTrade)\n                {\n                    double desiredGridStop = slPips * GridStopFib;\n                    orderSlPips = desiredGridStop;\n                    if (CommercialRiskEngine && CapGridStopToRiskBudget && v284MaxStopPips > 0 && orderSlPips > v284MaxStopPips)\n                    {\n                        // Never cap below the actual harmonic structural stop. We only remove excess Grid extension.\n                        orderSlPips = Math.Max(slPips, v284MaxStopPips);\n                        _v284GridStopCapped++;\n                        Print("[V284-GRID-CAP] baseSL={0:F1} desiredGridSL={1:F1} cappedGridSL={2:F1}",\n                            slPips, desiredGridStop, orderSlPips);\n                    }\n                    orderTpPips = null;\n                    _lastPrimaryRiskPips = slPips;\n                    volumeInUnits = CalculateVolumeByRisk(orderSlPips, riskBudgetPct);\n                }\n'''
if old not in s: raise SystemExit('grid primary sizing block missing')
s=s.replace(old,new,1)

# -----------------------------------------------------------------------------
# Verify actual normalized volume risk. Some broker/API paths can return/normalize
# to min volume even when that min volume exceeds the requested risk budget.
# -----------------------------------------------------------------------------
old='''            if (vol >= _symbol.VolumeInUnitsMin)\n                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;\n'''
new='''            if (vol >= _symbol.VolumeInUnitsMin)\n            {\n                double nativeRiskMoney;\n                try { nativeRiskMoney = _symbol.AmountRisked(vol, allInRiskPips); }\n                catch { return 0; }\n                double nativeRiskPct = equity > 0 ? nativeRiskMoney / equity * 100.0 : double.MaxValue;\n                if (nativeRiskPct > pct + 1e-6)\n                {\n                    _v284NativeRiskReject++;\n                    Print("[V284-NATIVE-RISK-REJECT] vol={0} allInPips={1:F1} risk={2:F3}% budget={3:F3}%",\n                        vol, allInRiskPips, nativeRiskPct, pct);\n                    return 0;\n                }\n                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;\n            }\n'''
if old not in s: raise SystemExit('native normalized volume return block missing')
s=s.replace(old,new,1)

# Grid basket additions must not expand the basket risk cap above the configured base RiskPercent.
old='''            double allowedRiskPct = maxRiskPct;\n            if (GridGoldenRiskConvergence)\n                allowedRiskPct = FibonacciMathCore.GoldenRiskBudgetCumulative(nextLevel, maxRiskPct);\n'''
new='''            double allowedRiskPct = maxRiskPct;\n            if (GridGoldenRiskConvergence)\n                allowedRiskPct = FibonacciMathCore.GoldenRiskBudgetCumulative(nextLevel, maxRiskPct);\n            if (CommercialRiskEngine)\n                allowedRiskPct = Math.Min(allowedRiskPct, Math.Max(0.0, RiskPercent));\n'''
if old not in s: raise SystemExit('grid risk budget block missing')
s=s.replace(old,new,1)

# -----------------------------------------------------------------------------
# V28.4 stop summary.
# -----------------------------------------------------------------------------
old='Print("[V283-SUMMARY] iteration={0} qualityAccepted={1} qualityRejected={2} capitalRejected={3} gridOrders={4}", CommercialIteration, _v283QualityAccepted, _v283QualityRejected, _v283CapitalRejected, _v283GridOrders);'
if old not in s: raise SystemExit('V28.3 summary missing')
new='Print("[V284-SUMMARY] iteration={0} qualityAccepted={1} qualityRejected={2} legacyCapitalRejected={3} gridOrders={4} precisionReady={5} precisionWait={6} capitalHardReject={7} nativeRiskReject={8} gridStopCapped={9} warmupSkipped={10} effectiveMinSL={11:F1}", CommercialIteration, _v283QualityAccepted, _v283QualityRejected, _v283CapitalRejected, _v283GridOrders, _v284PrecisionReady, _v284PrecisionWait, _v284CapitalHardReject, _v284NativeRiskReject, _v284GridStopCapped, _v284WarmupSkipped, EffectiveMinStopLossPips());'
s=s.replace(old,new,1)

required=[
    'V28.4-Capital-Aware-Precision-RC','EnableCapitalAwarePrecisionEntry','PrecisionPrzMaxDistanceAtr',
    'PrecisionMaxWaitAtr','CapitalSafetyHeadroom','CapGridStopToRiskBudget','EvaluationStartUtcIso',
    'ReferencePrice','V284PrecisionEntryReady','[V284-PRECISION-WAIT]','[V284-PRECISION-READY]',
    '[V284-NATIVE-RISK-REJECT]','[V284-GRID-CAP]','[V284-SUMMARY]','EnableFibGrid','GeometryQualityScore',
    'SmallAccountMinSLPips','RiskPercent','capitalInfeasible','MinRR','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero'
]
missing=[x for x in required if x not in s]
if missing: raise SystemExit('V28.4 integrity missing: '+','.join(missing))

# Strong safety regressions: explicit small-account floor and true-risk audit must exist.
if 'return SmallAccountMode ? Math.Min(MinStopLossPips, SmallAccountMinSLPips)' not in s:
    raise SystemExit('V28.4 explicit SmallAccountMode floor precedence missing')
if 'nativeRiskPct > pct + 1e-6' not in s:
    raise SystemExit('V28.4 actual normalized-volume risk guard missing')

p.write_text(s,encoding='utf-8')
print('Applied HarmonyBot V28.4 Capital-Aware Precision Entry RC')
print('Fixed explicit SmallAccountMode floor precedence bug')
print('Added warmup/evaluation gate, PRZ precision wait, structural-stop capital preflight, Grid extension cap and normalized-volume true-risk verification')
print('RiskPercent, MaxDrawdown, anti-hedge, 12 harmonic families and Fibonacci Grid retained')
