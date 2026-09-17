from pathlib import Path
import re

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# HarmonyBot V29.1 Small Account Execution RC
old='private const string CommercialIteration = "V29-Persistent-PRZ-Execution-RC";'
if old not in s: raise SystemExit('V29 marker missing')
s=s.replace(old,'private const string CommercialIteration = "V29.1-Small-Account-Execution-RC";',1)

# Counters after V29 warmup fields.
anchor='        private long _v29WarmupSeeded;\n'
if anchor not in s: raise SystemExit('counter anchor missing')
s=s.replace(anchor, anchor+'''        private long _v291TacticalReady;\n        private long _v291TacticalWait;\n        private long _v291MicroConfirmPass;\n        private long _v291MicroConfirmFail;\n        private long _v291StructuralInvalid;\n        private long _v291TargetMissed;\n        private long _v291CapitalZoneWait;\n''',1)

# Parameters after V29 order attempts parameter.
anchor='''        [Parameter("V29 Max Order Attempts", DefaultValue = 3, MinValue = 1, MaxValue = 10)]\n        public int V29MaxOrderAttemptsPerCandidate { get; set; }\n'''
if anchor not in s: raise SystemExit('V29 parameter anchor missing')
params='''\n        [Parameter("V29.1 Small Account Tactical Execution", DefaultValue = true)]\n        public bool V291SmallAccountTacticalExecution { get; set; }\n\n        [Parameter("V29.1 Tactical Lookback Bars", DefaultValue = 4, MinValue = 2, MaxValue = 12)]\n        public int V291TacticalLookbackBars { get; set; }\n\n        [Parameter("V29.1 Tactical ATR Buffer", DefaultValue = 0.08, MinValue = 0.02, MaxValue = 0.30)]\n        public double V291TacticalAtrBuffer { get; set; }\n\n        [Parameter("V29.1 Tactical Budget Use", DefaultValue = 0.98, MinValue = 0.80, MaxValue = 1.00)]\n        public double V291TacticalBudgetUse { get; set; }\n\n        [Parameter("V29.1 Require Micro Confirmation", DefaultValue = true)]\n        public bool V291RequireMicroConfirmation { get; set; }\n\n        [Parameter("V29.1 Micro Body Min ATR", DefaultValue = 0.05, MinValue = 0.00, MaxValue = 0.30)]\n        public double V291MicroBodyMinAtr { get; set; }\n\n        [Parameter("V29.1 Min Tactical RR", DefaultValue = 2.0, MinValue = 1.0, MaxValue = 5.0)]\n        public double V291MinTacticalRR { get; set; }\n'''
s=s.replace(anchor,anchor+params,1)

# Queue potential: structural-stop distance should not reject a small-account candidate,
# because V29.1 uses a local tactical invalidation after harmonic + PRZ confirmation.
old='''            double structuralStopPips = PriceToPips(Math.Abs(entry - signal.StopLoss));\n            if (structuralStopPips > maxStopPips)\n            {\n                double improveAtr = PipsToPrice(structuralStopPips - maxStopPips) / atrNow;\n                if (improveAtr > Math.Max(0.10, PrecisionMaxWaitAtr) + 1e-9)\n                {\n                    reason = "CAPITAL_TOO_FAR";\n                    return false;\n                }\n            }\n'''
new='''            double structuralStopPips = PriceToPips(Math.Abs(entry - signal.StopLoss));\n            bool tacticalSmallAccount = SmallAccountMode && V291SmallAccountTacticalExecution;\n            if (structuralStopPips > maxStopPips && !tacticalSmallAccount)\n            {\n                double improveAtr = PipsToPrice(structuralStopPips - maxStopPips) / atrNow;\n                if (improveAtr > Math.Max(0.10, PrecisionMaxWaitAtr) + 1e-9)\n                {\n                    reason = "CAPITAL_TOO_FAR";\n                    return false;\n                }\n            }\n'''
if old not in s: raise SystemExit('queue potential block missing')
s=s.replace(old,new,1)

# Add micro-confirmation and tactical-stop helpers before V29TryGetTriggeredPending.
anchor='        private bool V29TryGetTriggeredPending(double atrNow, int currentBarIndex, out Signal signal)\n'
if anchor not in s: raise SystemExit('trigger helper anchor missing')
helper=r'''        private bool V291MicroConfirmed(Signal signal, int currentBarIndex, double atrNow)
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
            bool bodyOk = body + 1e-12 >= atrNow * Math.Max(0.0, V291MicroBodyMinAtr);
            if (!bodyOk) return false;

            if (signal.Direction == TradeDirection.Buy)
            {
                if (close <= open) return false;
                double lowerWick = Math.Max(0.0, Math.Min(open, close) - low);
                bool reclaim = close >= prevClose;
                bool rejection = lowerWick >= body * 0.35;
                return reclaim || rejection;
            }
            else
            {
                if (close >= open) return false;
                double upperWick = Math.Max(0.0, high - Math.Max(open, close));
                bool reclaim = close <= prevClose;
                bool rejection = upperWick >= body * 0.35;
                return reclaim || rejection;
            }
        }

        private bool V291TryBuildTacticalStop(Signal signal, int currentBarIndex, double atrNow, double maxStopPips,
            out double stopPrice, out double stopPips, out double tacticalRr)
        {
            stopPrice = 0;
            stopPips = 0;
            tacticalRr = 0;
            if (!SmallAccountMode || !V291SmallAccountTacticalExecution || signal == null || _symbol == null || _signalBars == null || atrNow <= 0)
                return false;

            double entry = signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            if (entry <= 0 || signal.StopLoss <= 0 || signal.TakeProfit <= 0) return false;

            double floorPips = Math.Max(EffectiveMinStopLossPips(), MinStopDistancePips);
            double capPips = Math.Max(0.0, maxStopPips) * Math.Max(0.80, Math.Min(1.0, V291TacticalBudgetUse));
            if (capPips + 1e-9 < floorPips) return false;

            int i = Math.Min(currentBarIndex, _signalBars.Count - 2);
            int lookback = Math.Max(2, V291TacticalLookbackBars);
            int start = Math.Max(0, i - lookback + 1);
            double localLow = double.MaxValue;
            double localHigh = double.MinValue;
            for (int j = start; j <= i; j++)
            {
                localLow = Math.Min(localLow, _signalBars.LowPrices[j]);
                localHigh = Math.Max(localHigh, _signalBars.HighPrices[j]);
            }
            if (localLow == double.MaxValue || localHigh == double.MinValue) return false;

            double bufferPrice = Math.Max(PipsToPrice(2.0), atrNow * Math.Max(0.02, V291TacticalAtrBuffer));
            if (signal.Direction == TradeDirection.Buy)
            {
                double candidate = localLow - bufferPrice;
                double minimumStop = entry - PipsToPrice(floorPips);
                stopPrice = Math.Min(candidate, minimumStop);
                // Tactical stop must stay inside the original harmonic structural invalidation.
                if (stopPrice <= signal.StopLoss + 1e-12) return false;
                stopPips = PriceToPips(entry - stopPrice);
            }
            else
            {
                double candidate = localHigh + bufferPrice;
                double minimumStop = entry + PipsToPrice(floorPips);
                stopPrice = Math.Max(candidate, minimumStop);
                if (stopPrice >= signal.StopLoss - 1e-12) return false;
                stopPips = PriceToPips(stopPrice - entry);
            }

            if (stopPips + 1e-9 < floorPips || stopPips > capPips + 1e-9) return false;

            double targetPips = PriceToPips(Math.Abs(signal.TakeProfit - entry));
            double costPips = UseCostAdjustedRR
                ? Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid)) + Math.Max(0.0, EstimateRoundTurnCommissionPips())
                : 0.0;
            double netRewardPips = Math.Max(0.0, targetPips - costPips);
            tacticalRr = stopPips > 0 ? netRewardPips / stopPips : 0.0;
            double rrFloor = Math.Max(MinRR, Math.Max(1.0, V291MinTacticalRR));
            if (tacticalRr + 1e-9 < rrFloor) return false;
            return true;
        }

'''
s=s.replace(anchor,helper+anchor,1)

# Replace mixed invalidation and add tactical selection state.
old='''            V29PendingCandidate best = null;\n            double bestRank = double.MinValue;\n'''
new='''            V29PendingCandidate best = null;\n            double bestRank = double.MinValue;\n            double bestTacticalStopPrice = 0;\n            double bestTacticalStopPips = 0;\n            double bestTacticalRr = 0;\n            bool bestUsesTactical = false;\n'''
if old not in s: raise SystemExit('best state anchor missing')
s=s.replace(old,new,1)

old='''                double bid = _symbol.Bid;\n                double ask = _symbol.Ask;\n                bool invalid = c.Signal.Direction == TradeDirection.Buy\n                    ? (bid <= c.Signal.StopLoss || (c.Signal.TakeProfit > 0 && ask >= c.Signal.TakeProfit))\n                    : (ask >= c.Signal.StopLoss || (c.Signal.TakeProfit > 0 && bid <= c.Signal.TakeProfit));\n                if (invalid)\n                {\n                    _v29PendingCandidates.Remove(c.Key);\n                    _v29PendingInvalidated++;\n                    V29PatternStat(c.Signal.PatternName).Invalidated++;\n                    Print("[V29-PENDING-INVALID] pattern={0} reason=STRUCTURE_OR_TARGET ageBars={1}", c.Signal.PatternName ?? "NA", age);\n                    continue;\n                }\n'''
new='''                double bid = _symbol.Bid;\n                double ask = _symbol.Ask;\n                bool structuralBreach = c.Signal.Direction == TradeDirection.Buy ? bid <= c.Signal.StopLoss : ask >= c.Signal.StopLoss;\n                bool targetReached = c.Signal.TakeProfit > 0 && (c.Signal.Direction == TradeDirection.Buy ? ask >= c.Signal.TakeProfit : bid <= c.Signal.TakeProfit);\n                if (structuralBreach)\n                {\n                    _v29PendingCandidates.Remove(c.Key);\n                    _v29PendingInvalidated++;\n                    _v291StructuralInvalid++;\n                    V29PatternStat(c.Signal.PatternName).Invalidated++;\n                    Print("[V291-PENDING-INVALID] pattern={0} reason=STRUCTURAL_STOP_BREACH ageBars={1}", c.Signal.PatternName ?? "NA", age);\n                    continue;\n                }\n                if (targetReached)\n                {\n                    _v29PendingCandidates.Remove(c.Key);\n                    _v29PendingInvalidated++;\n                    _v291TargetMissed++;\n                    V29PatternStat(c.Signal.PatternName).Invalidated++;\n                    Print("[V291-PENDING-INVALID] pattern={0} reason=TARGET_ALREADY_REACHED ageBars={1}", c.Signal.PatternName ?? "NA", age);\n                    continue;\n                }\n'''
if old not in s: raise SystemExit('invalidation block missing')
s=s.replace(old,new,1)

old='''                double structuralStopPips = PriceToPips(Math.Abs(entry - c.Signal.StopLoss));\n                double refDistAtr = c.Signal.ReferencePrice > 0 ? Math.Abs(entry - c.Signal.ReferencePrice) / atrNow : 0.0;\n                double przLimit = V29EffectivePrzLimit(c.Signal);\n                if (structuralStopPips > maxStopPips + 1e-9 || refDistAtr > przLimit + 1e-9) continue;\n\n                double capitalEfficiency = maxStopPips > 0 ? 1.0 - Math.Min(1.0, structuralStopPips / maxStopPips) : 0.0;\n                double freshness = 1.0 - Math.Min(1.0, (double)age / Math.Max(5, V29PendingMaxBars));\n                double rank = c.CompositeScore + 0.05 * capitalEfficiency + 0.02 * freshness;\n                if (rank > bestRank)\n                {\n                    bestRank = rank;\n                    best = c;\n                }\n'''
new='''                double structuralStopPips = PriceToPips(Math.Abs(entry - c.Signal.StopLoss));\n                double refDistAtr = c.Signal.ReferencePrice > 0 ? Math.Abs(entry - c.Signal.ReferencePrice) / atrNow : 0.0;\n                double przLimit = V29EffectivePrzLimit(c.Signal);\n                if (refDistAtr > przLimit + 1e-9) continue;\n\n                bool structuralCapitalReady = structuralStopPips <= maxStopPips + 1e-9;\n                double tacticalStopPrice = 0;\n                double tacticalStopPips = 0;\n                double tacticalRr = 0;\n                bool tacticalReady = false;\n                if (!structuralCapitalReady && SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    tacticalReady = V291TryBuildTacticalStop(c.Signal, currentBarIndex, atrNow, maxStopPips, out tacticalStopPrice, out tacticalStopPips, out tacticalRr);\n                    if (!tacticalReady)\n                    {\n                        _v291CapitalZoneWait++;\n                        continue;\n                    }\n                }\n                else if (!structuralCapitalReady)\n                    continue;\n\n                if (SmallAccountMode && V291SmallAccountTacticalExecution)\n                {\n                    if (!V291MicroConfirmed(c.Signal, currentBarIndex, atrNow))\n                    {\n                        _v291MicroConfirmFail++;\n                        continue;\n                    }\n                    _v291MicroConfirmPass++;\n                }\n\n                double effectiveStopPips = tacticalReady ? tacticalStopPips : structuralStopPips;\n                double capitalEfficiency = maxStopPips > 0 ? 1.0 - Math.Min(1.0, effectiveStopPips / maxStopPips) : 0.0;\n                double freshness = 1.0 - Math.Min(1.0, (double)age / Math.Max(5, V29PendingMaxBars));\n                double rank = c.CompositeScore + 0.05 * capitalEfficiency + 0.02 * freshness + (tacticalReady ? 0.02 * Math.Min(2.0, tacticalRr / Math.Max(1.0, MinRR)) : 0.0);\n                if (rank > bestRank)\n                {\n                    bestRank = rank;\n                    best = c;\n                    bestUsesTactical = tacticalReady;\n                    bestTacticalStopPrice = tacticalStopPrice;\n                    bestTacticalStopPips = tacticalStopPips;\n                    bestTacticalRr = tacticalRr;\n                }\n'''
if old not in s: raise SystemExit('trigger eligibility block missing')
s=s.replace(old,new,1)

old='''            signal = V29CloneSignal(best.Signal);\n            Print("[V29-PENDING-TRIGGER] pattern={0} key={1} score={2:F3} rank={3:F3} ageBars={4}",\n                signal.PatternName ?? "NA", best.Key, best.CompositeScore, bestRank, Math.Max(0, currentBarIndex - best.CreatedBarIndex));\n            return true;\n'''
new='''            signal = V29CloneSignal(best.Signal);\n            if (bestUsesTactical)\n            {\n                signal.StopLoss = bestTacticalStopPrice;\n                _v291TacticalReady++;\n                Print("[V291-TACTICAL-READY] pattern={0} stopPips={1:F1} maxStop={2:F1} RR={3:F2} structuralStop={4:F1}",\n                    signal.PatternName ?? "NA", bestTacticalStopPips, maxStopPips, bestTacticalRr,\n                    PriceToPips(Math.Abs((signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid) - best.Signal.StopLoss)));\n            }\n            Print("[V29-PENDING-TRIGGER] pattern={0} key={1} score={2:F3} rank={3:F3} ageBars={4} tactical={5}",\n                signal.PatternName ?? "NA", best.Key, best.CompositeScore, bestRank, Math.Max(0, currentBarIndex - best.CreatedBarIndex), bestUsesTactical);\n            return true;\n'''
if old not in s: raise SystemExit('trigger return block missing')
s=s.replace(old,new,1)

# Summary: append V29.1 diagnostic line before V29 pattern stats.
anchor='''            foreach (var kv in _v29PatternPendingStats.OrderBy(k => k.Key))\n'''
if anchor not in s: raise SystemExit('summary pattern loop anchor missing')
summary='''            Print("[V291-SUMMARY] tacticalReady={0} tacticalWait={1} microPass={2} microFail={3} structuralInvalid={4} targetMissed={5} capitalZoneWait={6}",\n                _v291TacticalReady, _v291TacticalWait, _v291MicroConfirmPass, _v291MicroConfirmFail, _v291StructuralInvalid, _v291TargetMissed, _v291CapitalZoneWait);\n\n'''
s=s.replace(anchor,summary+anchor,1)

# Ensure tactical orders are visible in successful execution telemetry.
old='''                    if (v29FromPending) V29RemovePending(signal, "EXECUTED", true);\n'''
new='''                    if (v29FromPending)\n                    {\n                        if (SmallAccountMode && V291SmallAccountTacticalExecution) _v291TacticalExecuted++;\n                        V29RemovePending(signal, "EXECUTED", true);\n                    }\n'''
# Add missing field if this anchor is used.
if old in s:
    s=s.replace('        private long _v291CapitalZoneWait;\n','        private long _v291CapitalZoneWait;\n        private long _v291TacticalExecuted;\n',1)
    s=s.replace(old,new,1)
    s=s.replace('_v291CapitalZoneWait);','_v291CapitalZoneWait);\n            Print("[V291-EXECUTION] tacticalExecuted={0}", _v291TacticalExecuted);',1)

# Integrity checks.
for marker in [
    'V29.1-Small-Account-Execution-RC','V291SmallAccountTacticalExecution','V291TryBuildTacticalStop',
    'STRUCTURAL_STOP_BREACH','TARGET_ALREADY_REACHED','[V291-TACTICAL-READY]','[V291-SUMMARY]',
    'EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','RiskPercent','MinRR']:
    if marker not in s: raise SystemExit('missing V29.1 marker: '+marker)

p.write_text(s,encoding='utf-8')
print('Applied HarmonyBot V29.1 Small Account Execution RC')
print('Added capital-compatible tactical stop, micro confirmation, split invalidation telemetry and wider persistent candidate eligibility')
print('RiskPercent/MaxDrawdown/anti-hedge/Fibonacci Grid/12 harmonic families preserved')
