from pathlib import Path

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# HarmonyBot V29.2 Small Account Fast Execution RC
old='private const string CommercialIteration = "V29.1-Small-Account-Execution-RC";'
if old not in s:
    raise SystemExit('V29.1 marker missing')
s=s.replace(old,'private const string CommercialIteration = "V29.2-Small-Account-Fast-Execution-RC";',1)

# V29.2 counters.
anchor='        private long _v291TacticalExecuted;\n'
if anchor not in s:
    raise SystemExit('V29.1 counter anchor missing')
s=s.replace(anchor, anchor+'''        private long _v292MicroPivotReady;\n        private long _v292CapitalCapReady;\n        private long _v292EarlyTrigger;\n        private long _v292TacticalRejectNoise;\n        private long _v292RrReject;\n        private long _v292TargetTooClose;\n        private long _v292FastStopReady;\n''',1)

# Parameters follow the V29.1 tactical RR parameter.
anchor='''        [Parameter("V29.1 Min Tactical RR", DefaultValue = 2.0, MinValue = 1.0, MaxValue = 5.0)]\n        public double V291MinTacticalRR { get; set; }\n'''
if anchor not in s:
    raise SystemExit('V29.1 parameter anchor missing')
params='''\n        [Parameter("V29.2 Fast Small Account Execution", DefaultValue = true)]\n        public bool V292FastSmallAccountExecution { get; set; }\n\n        [Parameter("V29.2 Micro Pivot Bars", DefaultValue = 2, MinValue = 1, MaxValue = 4)]\n        public int V292MicroPivotBars { get; set; }\n\n        [Parameter("V29.2 Micro Pivot ATR Buffer", DefaultValue = 0.04, MinValue = 0.00, MaxValue = 0.20)]\n        public double V292MicroPivotAtrBuffer { get; set; }\n\n        [Parameter("V29.2 Enable Capital Cap Stop", DefaultValue = true)]\n        public bool V292EnableCapitalCapStop { get; set; }\n\n        [Parameter("V29.2 Early Trigger", DefaultValue = true)]\n        public bool V292EnableEarlyTrigger { get; set; }\n\n        [Parameter("V29.2 Early Trigger Min Quality", DefaultValue = 0.66, MinValue = 0.50, MaxValue = 0.95)]\n        public double V292EarlyTriggerMinQuality { get; set; }\n\n        [Parameter("V29.2 Early Trigger Max PRZ ATR", DefaultValue = 0.95, MinValue = 0.45, MaxValue = 1.50)]\n        public double V292EarlyTriggerMaxPrzAtr { get; set; }\n\n        [Parameter("V29.2 Micro Body Min ATR", DefaultValue = 0.02, MinValue = 0.00, MaxValue = 0.20)]\n        public double V292MicroBodyMinAtr { get; set; }\n\n        [Parameter("V29.2 Wick/Body Confirm Ratio", DefaultValue = 0.25, MinValue = 0.05, MaxValue = 1.50)]\n        public double V292WickBodyConfirmRatio { get; set; }\n'''
s=s.replace(anchor,anchor+params,1)

# Add V29.2 fast confirmation and stop builder before V29.1 trigger helper.
anchor='        private bool V29TryGetTriggeredPending(double atrNow, int currentBarIndex, out Signal signal)\n'
if anchor not in s:
    raise SystemExit('V29 trigger anchor missing')
helper=r'''        private bool V292MicroConfirmedFast(Signal signal, int currentBarIndex, double atrNow)
        {
            if (!V291RequireMicroConfirmation) return true;
            if (signal == null || _signalBars == null || atrNow <= 0) return false;
            int i = Math.Min(currentBarIndex, _signalBars.Count - 2);
            if (i < 2) return false;

            double open = _signalBars.OpenPrices[i];
            double close = _signalBars.ClosePrices[i];
            double high = _signalBars.HighPrices[i];
            double low = _signalBars.LowPrices[i];
            double prevClose = _signalBars.ClosePrices[i - 1];
            double body = Math.Abs(close - open);
            double minBody = atrNow * Math.Max(0.0, V292MicroBodyMinAtr);
            bool bodyOk = body + 1e-12 >= minBody;
            if (!bodyOk) return false;

            double safeBody = Math.Max(body, atrNow * 0.005);
            if (signal.Direction == TradeDirection.Buy)
            {
                double lowerWick = Math.Max(0.0, Math.Min(open, close) - low);
                bool directional = close > open;
                bool reclaim = close >= prevClose;
                bool rejection = lowerWick >= safeBody * Math.Max(0.05, V292WickBodyConfirmRatio);
                return (directional && reclaim) || rejection;
            }
            else
            {
                double upperWick = Math.Max(0.0, high - Math.Max(open, close));
                bool directional = close < open;
                bool reclaim = close <= prevClose;
                bool rejection = upperWick >= safeBody * Math.Max(0.05, V292WickBodyConfirmRatio);
                return (directional && reclaim) || rejection;
            }
        }

        private bool V292TryBuildFastStop(Signal signal, int currentBarIndex, double atrNow, double maxStopPips,
            out double stopPrice, out double stopPips, out double tacticalRr, out bool usedCapitalCap)
        {
            stopPrice = 0;
            stopPips = 0;
            tacticalRr = 0;
            usedCapitalCap = false;
            if (!SmallAccountMode || !V291SmallAccountTacticalExecution || !V292FastSmallAccountExecution || signal == null || _symbol == null || _signalBars == null || atrNow <= 0)
                return false;

            double entry = signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            if (entry <= 0 || signal.StopLoss <= 0 || signal.TakeProfit <= 0) return false;

            double floorPips = Math.Max(EffectiveMinStopLossPips(), MinStopDistancePips);
            double capPips = Math.Max(0.0, maxStopPips) * Math.Max(0.80, Math.Min(1.0, V291TacticalBudgetUse));
            if (capPips + 1e-9 < floorPips) return false;

            int i = Math.Min(currentBarIndex, _signalBars.Count - 2);
            if (i < 0) return false;
            int lookback = Math.Max(1, Math.Min(4, V292MicroPivotBars));
            int start = Math.Max(0, i - lookback + 1);
            double localLow = double.MaxValue;
            double localHigh = double.MinValue;
            for (int j = start; j <= i; j++)
            {
                localLow = Math.Min(localLow, _signalBars.LowPrices[j]);
                localHigh = Math.Max(localHigh, _signalBars.HighPrices[j]);
            }
            if (localLow == double.MaxValue || localHigh == double.MinValue) return false;

            double bufferPrice = Math.Max(PipsToPrice(1.0), atrNow * Math.Max(0.0, V292MicroPivotAtrBuffer));
            double pivotStop;
            if (signal.Direction == TradeDirection.Buy)
                pivotStop = localLow - bufferPrice;
            else
                pivotStop = localHigh + bufferPrice;

            double pivotPips = signal.Direction == TradeDirection.Buy
                ? PriceToPips(entry - pivotStop)
                : PriceToPips(pivotStop - entry);

            // Reject nonsensical/noise pivots, but allow the broker/small-account floor to widen a too-tight pivot.
            if (pivotPips <= 0)
            {
                _v292TacticalRejectNoise++;
                return false;
            }

            double chosenPips = Math.Max(floorPips, pivotPips);
            if (chosenPips <= capPips + 1e-9)
            {
                _v292MicroPivotReady++;
            }
            else if (V292EnableCapitalCapStop)
            {
                // Final small-account execution layer: cap actual stop at the all-in 1% budget.
                // The original harmonic stop remains the pattern invalidation boundary.
                chosenPips = capPips;
                usedCapitalCap = true;
                _v292CapitalCapReady++;
            }
            else
                return false;

            if (chosenPips + 1e-9 < floorPips || chosenPips > capPips + 1e-9)
                return false;

            stopPrice = signal.Direction == TradeDirection.Buy
                ? entry - PipsToPrice(chosenPips)
                : entry + PipsToPrice(chosenPips);

            // Tactical stop must remain inside the original harmonic invalidation boundary.
            if (signal.Direction == TradeDirection.Buy)
            {
                if (stopPrice <= signal.StopLoss + 1e-12) return false;
            }
            else
            {
                if (stopPrice >= signal.StopLoss - 1e-12) return false;
            }
            stopPips = chosenPips;

            double targetPips = signal.Direction == TradeDirection.Buy
                ? PriceToPips(signal.TakeProfit - entry)
                : PriceToPips(entry - signal.TakeProfit);
            if (targetPips <= 0)
            {
                _v292TargetTooClose++;
                return false;
            }

            double costPips = UseCostAdjustedRR
                ? Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid)) + Math.Max(0.0, EstimateRoundTurnCommissionPips())
                : 0.0;
            double netRewardPips = Math.Max(0.0, targetPips - costPips);
            tacticalRr = stopPips > 0 ? netRewardPips / stopPips : 0.0;
            double rrFloor = Math.Max(MinRR, Math.Max(1.0, V291MinTacticalRR));
            if (tacticalRr + 1e-9 < rrFloor)
            {
                _v292RrReject++;
                return false;
            }

            _v292FastStopReady++;
            return true;
        }

'''
s=s.replace(anchor,helper+anchor,1)

# Expand best-candidate state for V29.2 telemetry.
old='''            bool bestUsesTactical = false;\n'''
new='''            bool bestUsesTactical = false;\n            bool bestUsedCapitalCap = false;\n            bool bestEarlyTrigger = false;\n'''
if old not in s:
    raise SystemExit('best tactical state missing')
s=s.replace(old,new,1)

# Replace the V29.1 eligibility block with faster small-account execution logic.
old='''                double structuralStopPips = PriceToPips(Math.Abs(entry - c.Signal.StopLoss));\n                double refDistAtr = c.Signal.ReferencePrice > 0 ? Math.Abs(entry - c.Signal.ReferencePrice) / atrNow : 0.0;\n                double przLimit = V29EffectivePrzLimit(c.Signal);\n                if (refDistAtr > przLimit + 1e-9) continue;\n\n                bool structuralCapitalReady = structuralStopPips <= maxStopPips + 1e-9;\n                double tacticalStopPrice = 0;\n                double tacticalStopPips = 0;\n                double tacticalRr = 0;\n                bool tacticalReady = false;\n                if (!structuralCapitalReady && SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    tacticalReady = V291TryBuildTacticalStop(c.Signal, currentBarIndex, atrNow, maxStopPips, out tacticalStopPrice, out tacticalStopPips, out tacticalRr);\n                    if (!tacticalReady)\n                    {\n                        _v291CapitalZoneWait++;\n                        continue;\n                    }\n                }\n                else if (!structuralCapitalReady)\n                    continue;\n\n                if (SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    if (!V291MicroConfirmed(c.Signal, currentBarIndex, atrNow))\n                    {\n                        _v291MicroConfirmFail++;\n                        continue;\n                    }\n                    _v291MicroConfirmPass++;\n                }\n\n                double effectiveStopPips = tacticalReady ? tacticalStopPips : structuralStopPips;\n                double capitalEfficiency = maxStopPips > 0 ? 1.0 - Math.Min(1.0, effectiveStopPips / maxStopPips) : 0.0;\n                double freshness = 1.0 - Math.Min(1.0, (double)age / Math.Max(5, V29PendingMaxBars));\n                double rank = c.CompositeScore + 0.05 * capitalEfficiency + 0.02 * freshness + (tacticalReady ? 0.02 * Math.Min(2.0, tacticalRr / Math.Max(1.0, MinRR)) : 0.0);\n                if (rank > bestRank)\n                {\n                    bestRank = rank;\n                    best = c;\n                    bestUsesTactical = tacticalReady;\n                    bestTacticalStopPrice = tacticalStopPrice;\n                    bestTacticalStopPips = tacticalStopPips;\n                    bestTacticalRr = tacticalRr;\n                }\n'''
new='''                double structuralStopPips = PriceToPips(Math.Abs(entry - c.Signal.StopLoss));\n                double refDistAtr = c.Signal.ReferencePrice > 0 ? Math.Abs(entry - c.Signal.ReferencePrice) / atrNow : 0.0;\n                double przLimit = V29EffectivePrzLimit(c.Signal);\n                bool insideNormalPrz = refDistAtr <= przLimit + 1e-9;\n                bool earlyEligible = V292EnableEarlyTrigger && c.CompositeScore + 1e-9 >= V292EarlyTriggerMinQuality\n                    && refDistAtr <= Math.Max(przLimit, V292EarlyTriggerMaxPrzAtr) + 1e-9;\n                if (!insideNormalPrz && !earlyEligible) continue;\n\n                if (SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    bool microOk = V292FastSmallAccountExecution\n                        ? V292MicroConfirmedFast(c.Signal, currentBarIndex, atrNow)\n                        : V291MicroConfirmed(c.Signal, currentBarIndex, atrNow);\n                    if (!microOk)\n                    {\n                        _v291MicroConfirmFail++;\n                        continue;\n                    }\n                    _v291MicroConfirmPass++;\n                }\n\n                bool structuralCapitalReady = structuralStopPips <= maxStopPips + 1e-9;\n                double tacticalStopPrice = 0;\n                double tacticalStopPips = 0;\n                double tacticalRr = 0;\n                bool tacticalReady = false;\n                bool usedCapitalCap = false;\n                if (!structuralCapitalReady && SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    tacticalReady = V292FastSmallAccountExecution\n                        ? V292TryBuildFastStop(c.Signal, currentBarIndex, atrNow, maxStopPips, out tacticalStopPrice, out tacticalStopPips, out tacticalRr, out usedCapitalCap)\n                        : V291TryBuildTacticalStop(c.Signal, currentBarIndex, atrNow, maxStopPips, out tacticalStopPrice, out tacticalStopPips, out tacticalRr);\n                    if (!tacticalReady)\n                    {\n                        _v291CapitalZoneWait++;\n                        _v291TacticalWait++;\n                        continue;\n                    }\n                }\n                else if (!structuralCapitalReady)\n                    continue;\n\n                double effectiveStopPips = tacticalReady ? tacticalStopPips : structuralStopPips;\n                double capitalEfficiency = maxStopPips > 0 ? 1.0 - Math.Min(1.0, effectiveStopPips / maxStopPips) : 0.0;\n                double freshness = 1.0 - Math.Min(1.0, (double)age / Math.Max(5, V29PendingMaxBars));\n                double rank = c.CompositeScore + 0.05 * capitalEfficiency + 0.02 * freshness\n                    + (tacticalReady ? 0.02 * Math.Min(2.0, tacticalRr / Math.Max(1.0, MinRR)) : 0.0)\n                    + ((!insideNormalPrz && earlyEligible) ? 0.01 : 0.0);\n                if (rank > bestRank)\n                {\n                    bestRank = rank;\n                    best = c;\n                    bestUsesTactical = tacticalReady;\n                    bestUsedCapitalCap = usedCapitalCap;\n                    bestEarlyTrigger = !insideNormalPrz && earlyEligible;\n                    bestTacticalStopPrice = tacticalStopPrice;\n                    bestTacticalStopPips = tacticalStopPips;\n                    bestTacticalRr = tacticalRr;\n                }\n'''
if old not in s:
    raise SystemExit('V29.1 trigger eligibility block missing')
s=s.replace(old,new,1)

# Upgrade trigger telemetry and count early/capital-cap triggers only when selected.
old='''            if (bestUsesTactical)\n            {\n                signal.StopLoss = bestTacticalStopPrice;\n                _v291TacticalReady++;\n                Print("[V291-TACTICAL-READY] pattern={0} stopPips={1:F1} maxStop={2:F1} RR={3:F2} structuralStop={4:F1}",\n                    signal.PatternName ?? "NA", bestTacticalStopPips, maxStopPips, bestTacticalRr,\n                    PriceToPips(Math.Abs((signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - best.Signal.StopLoss)));\n            }\n'''
new='''            if (bestUsesTactical)\n            {\n                signal.StopLoss = bestTacticalStopPrice;\n                _v291TacticalReady++;\n                if (bestUsedCapitalCap) _v292CapitalCapReady++;\n                if (bestEarlyTrigger) _v292EarlyTrigger++;\n                Print("[V292-FAST-READY] pattern={0} stopPips={1:F1} maxStop={2:F1} RR={3:F2} structuralStop={4:F1} capitalCap={5} early={6}",\n                    signal.PatternName ?? "NA", bestTacticalStopPips, maxStopPips, bestTacticalRr,\n                    PriceToPips(Math.Abs((signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - best.Signal.StopLoss)),\n                    bestUsedCapitalCap, bestEarlyTrigger);\n            }\n'''
if old not in s:
    raise SystemExit('V29.1 ready block missing')
s=s.replace(old,new,1)

# Do not double-count capital cap readiness inside helper; count selected candidates above.
s=s.replace('                _v292CapitalCapReady++;\n','',1)

# Add V29.2 summary immediately after V29.1 execution telemetry.
anchor='''            Print("[V291-EXECUTION] tacticalExecuted={0}", _v291TacticalExecuted);\n'''
if anchor not in s:
    raise SystemExit('V29.1 execution summary anchor missing')
summary='''            Print("[V292-SUMMARY] fastStopReady={0} microPivotReady={1} capitalCapReady={2} earlyTrigger={3} rejectNoise={4} rrReject={5} targetTooClose={6}",\n                _v292FastStopReady, _v292MicroPivotReady, _v292CapitalCapReady, _v292EarlyTrigger, _v292TacticalRejectNoise, _v292RrReject, _v292TargetTooClose);\n'''
s=s.replace(anchor,anchor+summary,1)

# Integrity checks.
for marker in [
    'V29.2-Small-Account-Fast-Execution-RC','V292FastSmallAccountExecution','V292TryBuildFastStop',
    'V292MicroConfirmedFast','[V292-FAST-READY]','[V292-SUMMARY]','STRUCTURAL_STOP_BREACH','TARGET_ALREADY_REACHED',
    'EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','RiskPercent','MinRR']:
    if marker not in s:
        raise SystemExit('missing V29.2 marker: '+marker)

p.write_text(s,encoding='utf-8')
print('Applied HarmonyBot V29.2 Small Account Fast Execution RC')
print('Adaptive 1-2 bar micro-pivot stop, 1% capital-cap fallback and early PRZ trigger enabled')
print('Geometry/RR/anti-hedge/Fibonacci Grid/12 harmonic families retained; RiskPercent and MaxDrawdown unchanged')
