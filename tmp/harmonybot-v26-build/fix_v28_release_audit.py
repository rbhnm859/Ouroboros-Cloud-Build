from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# v28 release audit: correct/validate ABCD and prevent repeated entries
# from the same harmonic completion.

# 1) Public dedupe control.
needle = '''        [Parameter("Commission / $1M / side", DefaultValue = 35.0, MinValue = 0.0, MaxValue = 200.0)]\n        public double CommissionPerMillionPerSide { get; set; }\n'''
insert = needle + '''\n        [Parameter("Signal Dedupe Bars", DefaultValue = 96, MinValue = 16, MaxValue = 384)]\n        public int SignalDedupeBars { get; set; }\n'''
if needle not in s:
    raise SystemExit('release audit parameter insertion point missing')
s = s.replace(needle, insert, 1)

# 2) Dedupe state and diagnostics.
needle = '        private long _diagVolumeBlocked;\n'
insert = needle + '''        private long _diagDuplicateBlocked;\n        private readonly Dictionary<string, int> _executedSignalBars = new Dictionary<string, int>();\n'''
if needle not in s:
    raise SystemExit('release audit field insertion point missing')
s = s.replace(needle, insert, 1)

# 3) Stable completion identity on each Signal.
needle = '''        public double Confidence { get; set; }\n        public string PatternName { get; set; }\n'''
insert = '''        public double Confidence { get; set; }\n        public string PatternName { get; set; }\n        public int CompletionIndex { get; set; }\n'''
if needle not in s:
    raise SystemExit('Signal completion field point missing')
s = s.replace(needle, insert, 1)

# 4) Detector exports the chosen completion bar index.
needle = '''                Confidence = finalScore,\n                PatternName = best.PatternName\n            };\n'''
repl = '''                Confidence = finalScore,\n                PatternName = best.PatternName,\n                CompletionIndex = referencePoint.Index\n            };\n'''
if needle not in s:
    raise SystemExit('signal assignment point missing')
s = s.replace(needle, repl, 1)

# 5) CRITICAL: ABCD reversal direction was inverted in legacy code.
# Bullish AB=CD completes after A->B down, B->C up, C->D down and buys at D.
# Bearish is the mirror image and sells at D.
old = '''            else if (isAbcd)\n            {\n                bull = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);\n                bear = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);\n                ab = Math.Abs(b.Price - a.Price);\n                bc = Math.Abs(c.Price - b.Price);\n                cd = Math.Abs(d.Price - c.Price);\n            }\n'''
new = '''            else if (isAbcd)\n            {\n                bull = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);\n                bear = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);\n                ab = Math.Abs(b.Price - a.Price);\n                bc = Math.Abs(c.Price - b.Price);\n                cd = Math.Abs(d.Price - c.Price);\n            }\n'''
if old not in s:
    raise SystemExit('legacy ABCD direction block missing')
s = s.replace(old, new, 1)

# 6) Full AB=CD confluence: C retracement, AB=CD equality and reciprocal BC projection.
# The frequency patch has already replaced the legacy RatioScore call with RangeAwareRatioScore.
old_candidates = [
'''            else if (isAbcd)\n            {\n                double rCD = cd / ab;\n                if (!InFibRange(rCD, def.BIdeal, def.BMin, def.BMax)) return null;\n                geometry = RangeAwareRatioScore(rCD, def.BIdeal, def.BMin, def.BMax);\n            }\n''',
'''            else if (isAbcd)\n            {\n                double rCD = cd / ab;\n                if (!InFibRange(rCD, def.BIdeal, def.BMin, def.BMax)) return null;\n                geometry = RatioScore(rCD, def.BIdeal);\n            }\n'''
]
new = '''            else if (isAbcd)\n            {\n                if (ab <= 0 || bc <= 0 || cd <= 0) return null;\n                double cRetrace = bc / ab;\n                double abcdEquality = cd / ab;\n                double bcProjection = cd / bc;\n\n                if (cRetrace < 0.382 - _fibTolerance || cRetrace > 0.886 + _fibTolerance) return null;\n                if (!InFibRange(abcdEquality, def.BIdeal, def.BMin, def.BMax)) return null;\n                if (bcProjection < 1.13 - _fibTolerance || bcProjection > 2.618 + _fibTolerance) return null;\n\n                double reciprocalIdeal = 1.0 / Math.Max(cRetrace, 0.0001);\n                reciprocalIdeal = Math.Max(1.13, Math.Min(2.618, reciprocalIdeal));\n                double sC = RangeAwareRatioScore(cRetrace, 0.618, 0.382, 0.886);\n                double sEq = RangeAwareRatioScore(abcdEquality, 1.0, 0.90, 1.15);\n                double sProj = RangeAwareRatioScore(bcProjection, reciprocalIdeal, 1.13, 2.618);\n                geometry = sEq * 0.50 + sC * 0.25 + sProj * 0.25;\n            }\n'''
replaced = False
for old_block in old_candidates:
    if old_block in s:
        s = s.replace(old_block, new, 1)
        replaced = True
        break
if not replaced:
    raise SystemExit('ABCD geometry block missing')

# 7) Reject a pattern only after it has ACTUALLY produced a successful order.
needle = '''                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))\n                    return;\n                if (signal == null) return;\n                _diagSignalsDetected++;\n'''
repl = '''                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))\n                    return;\n                if (signal == null) return;\n                _diagSignalsDetected++;\n\n                PruneExecutedSignalKeys(signalIndex);\n                string signalKey = BuildSignalKey(signal);\n                int priorSignalBar;\n                if (_executedSignalBars.TryGetValue(signalKey, out priorSignalBar) &&\n                    signalIndex - priorSignalBar <= Math.Max(16, SignalDedupeBars))\n                {\n                    _diagDuplicateBlocked++;\n                    return;\n                }\n'''
if needle not in s:
    raise SystemExit('detector success point missing')
s = s.replace(needle, repl, 1)

# 8) Mark the harmonic completion only after broker accepted the order.
needle = '''                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n                    _diagOrdersOpened++;\n'''
repl = '''                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n                    _diagOrdersOpened++;\n                    _executedSignalBars[signalKey] = signalIndex;\n'''
if needle not in s:
    raise SystemExit('successful order mark point missing')
s = s.replace(needle, repl, 1)

# 9) Small bounded helper set; completion bar + pattern + direction defines one setup.
marker = '''        private bool PassMtfFilter(Signal signal)\n'''
helpers = '''        private string BuildSignalKey(Signal signal)\n        {\n            if (signal == null) return "";\n            return string.Format("{0}|{1}|{2}", signal.PatternName ?? "?", signal.Direction, signal.CompletionIndex);\n        }\n\n        private void PruneExecutedSignalKeys(int currentBarIndex)\n        {\n            int keep = Math.Max(16, SignalDedupeBars);\n            var stale = _executedSignalBars\n                .Where(kv => currentBarIndex - kv.Value > keep)\n                .Select(kv => kv.Key)\n                .ToList();\n            foreach (string key in stale)\n                _executedSignalBars.Remove(key);\n        }\n\n'''
if marker not in s:
    raise SystemExit('dedupe helper marker missing')
s = s.replace(marker, helpers + marker, 1)

# 10) Add dedupe count to commercial diagnostics.
old = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked);\n'''
new = '''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked);\n'''
if old not in s:
    raise SystemExit('commercial diagnostic point missing')
s = s.replace(old, new, 1)

for token in ['Signal Dedupe Bars', 'CompletionIndex', '_diagDuplicateBlocked', 'BuildSignalKey', 'reciprocalIdeal']:
    if token not in s:
        raise SystemExit('release audit missing token: ' + token)
# Make inversion fix auditable and fail the build chain if the old ABCD direction remains.
if 'bull = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);' in s:
    raise SystemExit('legacy inverted ABCD bullish direction still present')

p.write_text(s, encoding='utf-8')
print('Applied v28 full ABCD confluence, direction fix, signal dedupe and release audit hardening')
