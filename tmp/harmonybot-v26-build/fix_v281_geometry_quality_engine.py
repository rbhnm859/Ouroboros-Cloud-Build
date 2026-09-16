from pathlib import Path
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

needle='''        [Parameter("Signal Dedupe Bars", DefaultValue = 96, MinValue = 16, MaxValue = 384)]\n        public int SignalDedupeBars { get; set; }\n'''
insert=needle+'''\n        [Parameter("Geometry Quality Engine", DefaultValue = true)]\n        public bool EnableGeometryQualityEngine { get; set; }\n\n        [Parameter("Min Geometry Quality", DefaultValue = 0.52, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinGeometryQuality { get; set; }\n'''
if needle not in s: raise SystemExit('geometry parameter insertion point missing')
s=s.replace(needle,insert,1)

needle='''        public int CompletionIndex { get; set; }\n'''
insert=needle+'''        public double GeometryQuality { get; set; }\n        public double PrzConfluence { get; set; }\n        public double TimeSymmetry { get; set; }\n        public double PivotQuality { get; set; }\n'''
if needle not in s: raise SystemExit('geometry signal fields point missing')
s=s.replace(needle,insert,1)

needle='''        private long _diagDuplicateBlocked;\n'''
insert=needle+'''        private long _diagGeometryValidated;\n        private long _diagGeometryRejectedQuality;\n'''
if needle not in s: raise SystemExit('geometry diag fields point missing')
s=s.replace(needle,insert,1)

needle='''                Confidence = finalScore,\n                PatternName = best.PatternName,\n                CompletionIndex = referencePoint.Index\n            };\n'''
repl='''                Confidence = finalScore,\n                PatternName = best.PatternName,\n                CompletionIndex = referencePoint.Index,\n                GeometryQuality = GeometryQualityScore(x, a, b, c, d, atrPrice, geometry, out double przScore, out double timeScore, out double pivotScore),\n                PrzConfluence = przScore,\n                TimeSymmetry = timeScore,\n                PivotQuality = pivotScore\n            };\n'''
if needle not in s: raise SystemExit('geometry signal assignment point missing')
s=s.replace(needle,repl,1)

# Detector uses SwingPoint as its pivot model. Keep the geometry helper bound to
# that real source type so the generated source compiles without introducing a
# fictitious Pivot dependency.
helper='''        private double GeometryQualityScore(SwingPoint x, SwingPoint a, SwingPoint b, SwingPoint c, SwingPoint d, double atrPrice, double ratioScore, out double prz, out double time, out double pivot)\n        {\n            double eps = 1e-9;\n            double xa = Math.Abs(a.Price - x.Price);\n            double ab = Math.Abs(b.Price - a.Price);\n            double cd = Math.Abs(d.Price - c.Price);\n            double vol = Math.Max(Math.Abs(atrPrice), eps);\n            double dFromX = Math.Abs(d.Price - x.Price);\n            double dFromA = Math.Abs(d.Price - a.Price);\n            double projectionGap = Math.Min(dFromX, dFromA);\n            prz = 1.0 / (1.0 + projectionGap / Math.Max(vol, eps));\n            double tXA = Math.Max(1.0, a.Index - x.Index);\n            double tAB = Math.Max(1.0, b.Index - a.Index);\n            double tBC = Math.Max(1.0, c.Index - b.Index);\n            double tCD = Math.Max(1.0, d.Index - c.Index);\n            double timeErr = (Math.Abs(tXA - tCD) / Math.Max(tXA, tCD) + Math.Abs(tAB - tBC) / Math.Max(tAB, tBC)) * 0.5;\n            time = Math.Max(0.0, Math.Min(1.0, 1.0 - timeErr));\n            double minLeg = Math.Min(xa, Math.Min(ab, cd));\n            pivot = Math.Max(0.0, Math.Min(1.0, minLeg / Math.Max(vol * 2.0, eps)));\n            double fib = Math.Max(0.0, Math.Min(1.0, ratioScore));\n            return Math.Max(0.0, Math.Min(1.0, fib * 0.45 + prz * 0.25 + time * 0.15 + pivot * 0.15));\n        }\n\n'''
det=s.find('class HarmonicPatternDetector')
if det < 0: raise SystemExit('HarmonicPatternDetector class missing')
next_class=s.find('\n    public class ', det+1)
if next_class < 0: next_class=s.find('\n    internal class ', det+1)
if next_class < 0: raise SystemExit('geometry detector boundary missing')
close=s.rfind('    }', det, next_class)
if close < 0: raise SystemExit('geometry detector closing brace missing')
s=s[:close]+helper+s[close:]

needle='''                _diagSignalsDetected++;\n\n                PruneExecutedSignalKeys(signalIndex);\n'''
repl='''                _diagSignalsDetected++;\n                if (EnableGeometryQualityEngine)\n                {\n                    if (signal.GeometryQuality < MinGeometryQuality)\n                    {\n                        _diagGeometryRejectedQuality++;\n                        _diagGeometryBlocked++;\n                        return;\n                    }\n                    _diagGeometryValidated++;\n                }\n\n                PruneExecutedSignalKeys(signalIndex);\n'''
if needle not in s: raise SystemExit('geometry funnel insertion point missing')
s=s.replace(needle,repl,1)

old='''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10} capitalInfeasible={11}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible);\n'''
new='''                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10} capitalInfeasible={11} geometryValid={12} geometryQualityRejected={13}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible, _diagGeometryValidated, _diagGeometryRejectedQuality);\n'''
if old not in s: raise SystemExit('geometry commercial diagnostic block missing')
s=s.replace(old,new,1)

for token in ['Geometry Quality Engine','GeometryQualityScore(SwingPoint','PrzConfluence','TimeSymmetry','PivotQuality','_diagGeometryValidated','_diagGeometryRejectedQuality','EnableFibGrid','capitalInfeasible={11}','geometryValid={12}','geometryQualityRejected={13}']:
    if token not in s: raise SystemExit('geometry engine missing token: '+token)
if 'GeometryQualityScore(Pivot ' in s: raise SystemExit('obsolete Pivot geometry signature remains')

p.write_text(s,encoding='utf-8')
print('Applied V28.1 independent Harmonic Geometry Quality Engine')
