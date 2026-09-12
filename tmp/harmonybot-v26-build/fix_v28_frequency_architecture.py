from pathlib import Path
import re

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# v28 Commercial Final RC: frequency architecture + candidate ranking + real slippage bound.

# 1) Public commercial-frequency controls after v27's min-volume partial control.
needle = '''        [Parameter("Disable Partial TP At Min Volume", DefaultValue = true)]\n        public bool DisablePartialAtMinVolume { get; set; }\n'''
insert = needle + '''\n        [Parameter("Adaptive Min ATR Factor", DefaultValue = 0.70, MinValue = 0.40, MaxValue = 1.00)]\n        public double AdaptiveMinAtrFactor { get; set; }\n\n        [Parameter("Commercial Swing Depth Reduction", DefaultValue = 1, MinValue = 0, MaxValue = 2)]\n        public int CommercialSwingDepthReduction { get; set; }\n\n        [Parameter("Commercial Pivot Scan Min", DefaultValue = 20, MinValue = 10, MaxValue = 60)]\n        public int CommercialPivotScanMin { get; set; }\n\n        [Parameter("Candidate Max Age Bars", DefaultValue = 48, MinValue = 4, MaxValue = 192)]\n        public int CandidateMaxAgeBars { get; set; }\n\n        [Parameter("Direction Dominance Margin", DefaultValue = 0.04, MinValue = 0.0, MaxValue = 0.20)]\n        public double DirectionDominanceMargin { get; set; }\n\n        [Parameter("Fib Range Boundary Score", DefaultValue = 0.60, MinValue = 0.30, MaxValue = 0.90)]\n        public double FibRangeBoundaryScore { get; set; }\n\n        [Parameter("Reversal Trend Score Floor", DefaultValue = 0.45, MinValue = 0.0, MaxValue = 0.80)]\n        public double ReversalTrendScoreFloor { get; set; }\n'''
if needle not in s:
    raise SystemExit('v28 parameter insertion point missing')
s = s.replace(needle, insert, 1)

# 2) Extra diagnostics.
field = '        private long _diagPartialSkipped;\n'
if field not in s:
    raise SystemExit('v28 diag insertion point missing')
s = s.replace(field, field + '''        private long _diagAtrBlocked;\n        private long _diagBudgetBlocked;\n        private long _diagMtfBlocked;\n        private long _diagGeometryBlocked;\n        private long _diagVolumeBlocked;\n''', 1)

# 3) Adaptive detector depth/scan and new detector controls.
old = '''                double effectiveMinLegAtrRatio = AdaptiveFrequencyRecovery ? Math.Min(MinLegAtrRatio, 0.70) : MinLegAtrRatio;\n                double effectiveFibTolerance = AdaptiveFrequencyRecovery ? Math.Min(0.20, FibTolerance + 0.015) : FibTolerance;\n                double effectiveEntryDeviationAtr = AdaptiveFrequencyRecovery ? Math.Max(MaxEntryDeviationAtr, AdaptiveEntryDeviationFloor) : MaxEntryDeviationAtr;\n\n                _detector = new HarmonicPatternDetector(\n                    SwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,\n                    PivotScanCount, effectiveMinLegAtrRatio, GlobalMinScore, ConsensusBonus,\n                    effectiveFibTolerance, effectiveEntryDeviationAtr,\n                    ClosedBarProvisionalD && AdaptiveFrequencyRecovery, ProvisionalDMinMoveAtr,\n'''
new = '''                double effectiveMinLegAtrRatio = AdaptiveFrequencyRecovery ? Math.Min(MinLegAtrRatio, 0.70) : MinLegAtrRatio;\n                double effectiveFibTolerance = AdaptiveFrequencyRecovery ? Math.Min(0.20, FibTolerance + 0.015) : FibTolerance;\n                double effectiveEntryDeviationAtr = AdaptiveFrequencyRecovery ? Math.Max(MaxEntryDeviationAtr, AdaptiveEntryDeviationFloor) : MaxEntryDeviationAtr;\n                int effectiveSwingDepth = AdaptiveFrequencyRecovery ? Math.Max(3, SwingDepth - Math.Max(0, CommercialSwingDepthReduction)) : SwingDepth;\n                int effectivePivotScan = AdaptiveFrequencyRecovery ? Math.Max(PivotScanCount, CommercialPivotScanMin) : PivotScanCount;\n\n                _detector = new HarmonicPatternDetector(\n                    effectiveSwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,\n                    effectivePivotScan, effectiveMinLegAtrRatio, GlobalMinScore, ConsensusBonus,\n                    effectiveFibTolerance, effectiveEntryDeviationAtr,\n                    ClosedBarProvisionalD && AdaptiveFrequencyRecovery, ProvisionalDMinMoveAtr,\n                    CandidateMaxAgeBars, DirectionDominanceMargin, FibRangeBoundaryScore, ReversalTrendScoreFloor,\n'''
if old not in s:
    raise SystemExit('v28 detector call block missing')
s = s.replace(old, new, 1)

# 4) Adaptive ATR gate, preserving the original configured minimum as baseline.
old = '                if (atrNow <= 0 || atrNow < MinAtrPrice) return;\n'
new = '''                double effectiveMinAtr = AdaptiveFrequencyRecovery\n                    ? Math.Max(0.1, MinAtrPrice * Math.Max(0.40, Math.Min(1.0, AdaptiveMinAtrFactor)))\n                    : MinAtrPrice;\n                if (atrNow <= 0 || atrNow < effectiveMinAtr)\n                {\n                    _diagAtrBlocked++;\n                    return;\n                }\n'''
if old not in s:
    raise SystemExit('v28 ATR gate missing')
s = s.replace(old, new, 1)

# 5) Gate diagnostics for bottleneck accounting.
s = s.replace('''                if (used >= cap)\n                {\n                    Print("[BUDGET] {0} daily cap reached.", signal.PatternName);\n                    return;\n                }\n''', '''                if (used >= cap)\n                {\n                    _diagBudgetBlocked++;\n                    Print("[BUDGET] {0} daily cap reached.", signal.PatternName);\n                    return;\n                }\n''', 1)
s = s.replace('                if (!PassMtfFilter(signal)) return;\n', '''                if (!PassMtfFilter(signal))\n                {\n                    _diagMtfBlocked++;\n                    return;\n                }\n''', 1)
s = s.replace('''                double slPips, tpPips;\n                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n''', '''                double slPips, tpPips;\n                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips))\n                {\n                    _diagGeometryBlocked++;\n                    return;\n                }\n''', 1)
s = s.replace('''                if (volumeInUnits <= 0)\n                {\n                    _pendingPrimaryUseGrid = false;\n                    return;\n                }\n''', '''                if (volumeInUnits <= 0)\n                {\n                    _diagVolumeBlocked++;\n                    _pendingPrimaryUseGrid = false;\n                    return;\n                }\n''', 1)

# 6) Real MaxSlippagePips enforcement and no execution-layer volume upsizing.
start = s.find('        private TradeResult ExecuteRobotMarketOrder(TradeType tt, double volumeInUnits, double? slPips, double? tpPips)\n')
end = s.find('        private double GetCurrentDayDrawdownPercent()\n', start)
if start < 0 or end < 0:
    raise SystemExit('v28 execution block not found')
exec_block = r'''        private TradeResult ExecuteRobotMarketOrder(TradeType tt, double volumeInUnits, double? slPips, double? tpPips)
        {
            if (_symbol == null || volumeInUnits <= 0) return null;

            double vol = _symbol.NormalizeVolumeInUnits(volumeInUnits, RoundingMode.Down);
            if (vol < _symbol.VolumeInUnitsMin || vol > _symbol.VolumeInUnitsMax) return null;

            double basePrice = tt == TradeType.Buy ? _symbol.Ask : _symbol.Bid;
            if (basePrice <= 0) return null;

            if (MaxSlippagePips > 0)
            {
                return ExecuteMarketRangeOrder(tt, SymbolName, vol, MaxSlippagePips, basePrice,
                    BotLabel, slPips, tpPips, "HarmonyBotPro", false, StopTriggerMethod.Trade);
            }

            return ExecuteMarketOrder(tt, SymbolName, vol, BotLabel, slPips, tpPips,
                "HarmonyBotPro", false, StopTriggerMethod.Trade);
        }

'''
s = s[:start] + exec_block + s[end:]

# 7) Detector fields for fresh-candidate competition and balanced scoring.
needle = '''        private readonly bool _closedBarProvisionalD;\n        private readonly double _provisionalDMinMoveAtr;\n\n        private readonly Dictionary<string, bool> _enabled'''
repl = '''        private readonly bool _closedBarProvisionalD;\n        private readonly double _provisionalDMinMoveAtr;\n        private readonly int _candidateMaxAgeBars;\n        private readonly double _directionDominanceMargin;\n        private readonly double _rangeBoundaryScore;\n        private readonly double _reversalTrendFloor;\n\n        private readonly Dictionary<string, bool> _enabled'''
if needle not in s:
    raise SystemExit('v28 detector fields missing')
s = s.replace(needle, repl, 1)

# 8) Detector constructor controls.
needle = '''            double fibTolerance, double maxEntryDeviationAtr,\n            bool closedBarProvisionalD, double provisionalDMinMoveAtr,\n            bool gartley, bool bat, bool butterfly, bool crab, bool cypher,'''
repl = '''            double fibTolerance, double maxEntryDeviationAtr,\n            bool closedBarProvisionalD, double provisionalDMinMoveAtr,\n            int candidateMaxAgeBars, double directionDominanceMargin, double rangeBoundaryScore, double reversalTrendFloor,\n            bool gartley, bool bat, bool butterfly, bool crab, bool cypher,'''
if needle not in s:
    raise SystemExit('v28 detector ctor signature missing')
s = s.replace(needle, repl, 1)
needle = '''            _closedBarProvisionalD = closedBarProvisionalD;\n            _provisionalDMinMoveAtr = Math.Max(0.10, Math.Min(1.00, provisionalDMinMoveAtr));\n'''
repl = needle + '''            _candidateMaxAgeBars = Math.Max(4, candidateMaxAgeBars);\n            _directionDominanceMargin = Math.Max(0.0, Math.Min(0.20, directionDominanceMargin));\n            _rangeBoundaryScore = Math.Max(0.30, Math.Min(0.90, rangeBoundaryScore));\n            _reversalTrendFloor = Math.Max(0.0, Math.Min(0.80, reversalTrendFloor));\n'''
if needle not in s:
    raise SystemExit('v28 detector ctor assignment missing')
s = s.replace(needle, repl, 1)

# 9) Replace candidate selection so stale high-score patterns can no longer block fresh lower-score candidates.
method_start = s.find('        public bool TryDetect(Bars bars, int currentIndex, double atrNow, Symbol symbol,\n            double regimeScore, double buyTrend, double sellTrend, out Signal signal)\n')
method_end = s.find('        private bool IsDefEnabled(PatternDef def)\n', method_start)
if method_start < 0 or method_end < 0:
    raise SystemExit('v28 TryDetect method missing')
new_try = r'''        public bool TryDetect(Bars bars, int currentIndex, double atrNow, Symbol symbol,
            double regimeScore, double buyTrend, double sellTrend, out Signal signal)
        {
            signal = null;
            if (bars == null || symbol == null || currentIndex < _depth * 4 || currentIndex >= bars.Count || atrNow <= 0)
                return false;

            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);
            if (_closedBarProvisionalD)
                AppendClosedBarProvisionalPivot(pivots, bars, currentIndex, atrNow, _provisionalDMinMoveAtr);
            if (pivots.Count < 4) return false;

            int start = Math.Max(0, pivots.Count - _scanCount);
            var all = new List<Candidate>();

            for (int i = start; i <= pivots.Count - 4; i++)
            {
                foreach (var def in _defs)
                {
                    if (!IsDefEnabled(def)) continue;
                    Candidate c = Match(bars, pivots, i, def, atrNow, regimeScore, buyTrend, sellTrend, currentIndex);
                    if (c == null) continue;

                    SwingPoint reference = c.Family == PatternFamily.Shark ? c.C : c.D;
                    if (reference == null) continue;
                    if (_candidateMaxAgeBars > 0 && currentIndex - reference.Index > _candidateMaxAgeBars) continue;

                    double candidateEntry = c.IsBullish ? symbol.Ask : symbol.Bid;
                    if (candidateEntry <= 0) continue;
                    if (Math.Abs(candidateEntry - reference.Price) > atrNow * _maxEntryDeviationAtr) continue;

                    all.Add(c);
                }
            }

            if (all.Count == 0) return false;

            var groups = new Dictionary<int, List<Candidate>>();
            foreach (Candidate c in all)
            {
                int key = c.X != null ? c.X.Index : c.A.Index;
                List<Candidate> slot;
                if (!groups.TryGetValue(key, out slot))
                {
                    slot = new List<Candidate>();
                    groups[key] = slot;
                }
                slot.Add(c);
            }

            Candidate best = null;
            double bestScore = -1;

            foreach (var kv in groups)
            {
                List<Candidate> slot = kv.Value;
                double bestBuy = -1, bestSell = -1;
                int buyCount = 0, sellCount = 0;
                for (int i = 0; i < slot.Count; i++)
                {
                    Candidate c = slot[i];
                    if (c.IsBullish) { buyCount++; if (c.Score > bestBuy) bestBuy = c.Score; }
                    else { sellCount++; if (c.Score > bestSell) bestSell = c.Score; }
                }

                bool? dominantBull = null;
                if (buyCount > 0 && sellCount > 0)
                {
                    if (Math.Abs(bestBuy - bestSell) < _directionDominanceMargin) continue;
                    dominantBull = bestBuy > bestSell;
                }

                Candidate slotBest = null;
                double slotScore = -1;
                int dominantCount = dominantBull.HasValue ? (dominantBull.Value ? buyCount : sellCount) : slot.Count;

                for (int i = 0; i < slot.Count; i++)
                {
                    Candidate c = slot[i];
                    if (dominantBull.HasValue && c.IsBullish != dominantBull.Value) continue;
                    double sc = c.Score;
                    if (dominantCount >= 2) sc *= _consensusBonus;
                    if (sc > slotScore) { slotScore = sc; slotBest = c; }
                }

                if (slotBest != null && slotScore > bestScore)
                {
                    best = slotBest;
                    bestScore = slotScore;
                }
            }

            if (best == null) return false;

            double finalScore = Math.Min(1.0, bestScore);
            if (finalScore < best.Threshold || finalScore < _globalMinScore || finalScore < _minConfidence)
                return false;

            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;
            double entry = dir == TradeDirection.Buy ? symbol.Ask : symbol.Bid;
            SwingPoint referencePoint = best.Family == PatternFamily.Shark ? best.C : best.D;
            if (referencePoint == null) return false;

            double stop, tpDist;
            stop = dir == TradeDirection.Buy
                ? referencePoint.Price - atrNow * _slAtrMult
                : referencePoint.Price + atrNow * _slAtrMult;

            if (best.Family == PatternFamily.Shark || best.Family == PatternFamily.FiveZero)
            {
                double bc = Math.Abs(best.B.Price - best.C.Price);
                tpDist = Math.Max(bc * 0.5, atrNow * 1.2);
            }
            else
            {
                double cd = best.C != null && best.D != null ? Math.Abs(best.C.Price - best.D.Price) : atrNow;
                tpDist = Math.Max(cd * _tpCdMult, atrNow * 1.2);
            }

            double tp = dir == TradeDirection.Buy ? entry + tpDist : entry - tpDist;
            if (dir == TradeDirection.Buy && !(stop < entry && entry < tp)) return false;
            if (dir == TradeDirection.Sell && !(tp < entry && entry < stop)) return false;

            signal = new Signal
            {
                Direction = dir,
                EntryPrice = entry,
                StopLoss = stop,
                TakeProfit = tp,
                Confidence = finalScore,
                PatternName = best.PatternName
            };
            return true;
        }

'''
s = s[:method_start] + new_try + s[method_end:]

# 10) Range-aware geometry scoring: valid harmonic ranges remain valid, while ideal ratios still score highest.
repls = {
    'RatioScore(rAB, def.BIdeal)': 'RangeAwareRatioScore(rAB, def.BIdeal, def.BMin, def.BMax)',
    'RatioScore(rBC, def.CIdeal)': 'RangeAwareRatioScore(rBC, def.CIdeal, def.CMin, def.CMax)',
    'RatioScore(rCD, def.XDIdeal)': 'RangeAwareRatioScore(rCD, def.XDIdeal, def.XDMin, def.XDMax)',
    'RatioScore(rCD, def.BIdeal)': 'RangeAwareRatioScore(rCD, def.BIdeal, def.BMin, def.BMax)',
    'RatioScore(rC, def.CIdeal)': 'RangeAwareRatioScore(rC, def.CIdeal, def.CMin, def.CMax)',
    'RatioScore(rD, def.XDIdeal)': 'RangeAwareRatioScore(rD, def.XDIdeal, def.XDMin, def.XDMax)',
    'RatioScore(rB, def.BIdeal)': 'RangeAwareRatioScore(rB, def.BIdeal, def.BMin, def.BMax)',
    'RatioScore(rD, def.DIdeal)': 'RangeAwareRatioScore(rD, def.DIdeal, def.DMin, def.DMax)',
    'RatioScore(rXD, def.XDIdeal)': 'RangeAwareRatioScore(rXD, def.XDIdeal, def.XDMin, def.XDMax)',
}
for a,b in repls.items():
    s = s.replace(a,b)

old = '''        private double RatioScore(double ratio, double ideal)\n        {\n            if (ideal <= 0) return 0;\n            double dev = Math.Abs(ratio - ideal) / ideal;\n            double score = 1.0 - dev / Math.Max(_fibTolerance, 0.001);\n            return Clamp01(score);\n        }\n'''
new = '''        private double RangeAwareRatioScore(double ratio, double ideal, double min, double max)\n        {\n            if (ideal <= 0) return _rangeBoundaryScore;\n            double lo = max > 0 ? min - _fibTolerance : min;\n            double hi = max > 0 ? max + _fibTolerance : max;\n            if (max > 0 && (ratio < lo || ratio > hi)) return 0;\n\n            double span;\n            if (ratio <= ideal) span = Math.Max(ideal - lo, 0.0001);\n            else span = Math.Max(hi - ideal, 0.0001);\n\n            double normalized = Math.Min(1.0, Math.Abs(ratio - ideal) / span);\n            double score = 1.0 - (1.0 - _rangeBoundaryScore) * normalized;\n            return Clamp01(score);\n        }\n'''
if old not in s:
    raise SystemExit('v28 old RatioScore block missing')
s = s.replace(old,new,1)

# 11) Reversal patterns should not be penalized twice for being counter-trend; final MTF gate still controls execution.
needle = '            double trendScore = bull ? buyTrend : sellTrend;\n'
repl = '''            double trendScore = bull ? buyTrend : sellTrend;\n            if (def.Family == PatternFamily.Reversal)\n                trendScore = Math.Max(trendScore, _reversalTrendFloor);\n'''
if needle not in s:
    raise SystemExit('v28 trend score point missing')
s = s.replace(needle,repl,1)

# 12) Extend final commercial diagnostics.
old = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped);\n'''
new = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked);\n'''
if old not in s:
    raise SystemExit('v28 commercial diag point missing')
s = s.replace(old,new,1)

required = [
    'VolumeForFixedRisk', 'AmountRisked', 'PipsForFixedRisk', 'ExecuteMarketRangeOrder',
    'RangeAwareRatioScore', 'Candidate Max Age Bars', 'Adaptive Min ATR Factor',
    '[COMMERCIAL-DIAG]'
]
for token in required:
    if token not in s:
        raise SystemExit('v28 missing required token: ' + token)
if 'MarketOrderParameters' in s:
    raise SystemExit('MarketOrderParameters unexpectedly remains')

p.write_text(s, encoding='utf-8')
print('Applied v28 Commercial Final RC frequency architecture')
