from pathlib import Path
import re
p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

def once(pattern,repl,label,flags=0):
    global s
    s,n=re.subn(pattern,repl,s,count=1,flags=flags)
    if n!=1: raise SystemExit(label+' missing')

# Public controls + Signal payload.
once(r'(\s*\[Parameter\("Signal Dedupe Bars"[^\n]*\)\]\s*\n\s*public int SignalDedupeBars \{ get; set; \}\s*\n)',r'\1\n        [Parameter("Geometry Quality Engine", DefaultValue = true)]\n        public bool EnableGeometryQualityEngine { get; set; }\n\n        [Parameter("Min Geometry Quality", DefaultValue = 0.52, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinGeometryQuality { get; set; }\n','geometry parameters')
once(r'(\s*public int CompletionIndex \{ get; set; \}\s*\n)',r'\1        public double GeometryQuality { get; set; }\n        public double PrzConfluence { get; set; }\n        public double TimeSymmetry { get; set; }\n        public double PivotQuality { get; set; }\n','signal geometry fields')
once(r'(\s*private long _diagDuplicateBlocked;\s*\n)',r'\1        private long _diagGeometryValidated;\n        private long _diagGeometryRejectedQuality;\n','geometry counters')

# Candidate layout has changed across hardening passes. Anchor only on the unique class declaration.
once(r'((?:private|internal|public)?\s*(?:sealed\s+)?class\s+Candidate\s*\{)',r'\1\n            public double GeometryQuality;\n            public double PrzConfluence;\n            public double TimeSymmetry;\n            public double PivotQuality;','Candidate class',re.S)

# Calculate geometry while Match locals are alive. Preserve the actual X initializer emitted by the hardened detector
# instead of assuming a specific Shark/5-0/ABCD expression.
once(r'(\s*)return new Candidate\s*\{\s*\n(\s*)X\s*=\s*([^,\n]+),',r'\1double geometryQuality = GeometryQualityScore(\n\1    x, a, b, c, d, atr, geometry,\n\1    out double przScore, out double timeScore, out double pivotScore);\n\n\1return new Candidate\n\1{\n\2GeometryQuality = geometryQuality,\n\2PrzConfluence = przScore,\n\2TimeSymmetry = timeScore,\n\2PivotQuality = pivotScore,\n\2X = \3,','Candidate construction',re.S)

once(r'(Confidence\s*=\s*finalScore,\s*\n\s*PatternName\s*=\s*best\.PatternName,\s*\n\s*CompletionIndex\s*=\s*referencePoint\.Index)(\s*\n\s*\};)',r'\1,\n                GeometryQuality = best.GeometryQuality,\n                PrzConfluence = best.PrzConfluence,\n                TimeSymmetry = best.TimeSymmetry,\n                PivotQuality = best.PivotQuality\2','signal geometry assignment')

helper='''        private double GeometryQualityScore(SwingPoint x, SwingPoint a, SwingPoint b, SwingPoint c, SwingPoint d, double atrPrice, double ratioScore, out double prz, out double time, out double pivot)\n        {\n            const double eps = 1e-9;\n            if (a == null || b == null || c == null || d == null) { prz=0; time=0; pivot=0; return 0; }\n            if (x == null) x=a;\n            double xa=Math.Abs(a.Price-x.Price), ab=Math.Abs(b.Price-a.Price), cd=Math.Abs(d.Price-c.Price);\n            double vol=Math.Max(Math.Abs(atrPrice),eps);\n            double projectionGap=Math.Min(Math.Abs(d.Price-x.Price),Math.Abs(d.Price-a.Price));\n            prz=1.0/(1.0+projectionGap/vol);\n            double tXA=Math.Max(1.0,a.Index-x.Index), tAB=Math.Max(1.0,b.Index-a.Index);\n            double tBC=Math.Max(1.0,c.Index-b.Index), tCD=Math.Max(1.0,d.Index-c.Index);\n            double timeErr=(Math.Abs(tXA-tCD)/Math.Max(tXA,tCD)+Math.Abs(tAB-tBC)/Math.Max(tAB,tBC))*0.5;\n            time=Math.Max(0.0,Math.Min(1.0,1.0-timeErr));\n            pivot=Math.Max(0.0,Math.Min(1.0,Math.Min(xa,Math.Min(ab,cd))/Math.Max(vol*2.0,eps)));\n            double fib=Math.Max(0.0,Math.Min(1.0,ratioScore));\n            return Math.Max(0.0,Math.Min(1.0,fib*0.45+prz*0.25+time*0.15+pivot*0.15));\n        }\n\n'''
# Insert the helper immediately before the already-discovered Candidate nested class. This is a stable
# structural boundary inside HarmonicPatternDetector and does not depend on mutable section comments.
once(r'(\s*(?:private|internal|public)?\s*(?:sealed\s+)?class\s+Candidate\s*\{)',helper+r'\1','geometry helper',re.S)

once(r'(\s*_diagSignalsDetected\+\+;\s*\n)(\s*PruneExecutedSignalKeys\(signalIndex\);)',r'\1                if (EnableGeometryQualityEngine)\n                {\n                    if (signal.GeometryQuality < MinGeometryQuality) { _diagGeometryRejectedQuality++; _diagGeometryBlocked++; return; }\n                    _diagGeometryValidated++;\n                }\n\n\2','geometry funnel')

old=r'Print\("\[COMMERCIAL-DIAG\] signals=\{0\} orders=\{1\} compressed=\{2\} riskBlocked=\{3\} partialSkipped=\{4\} atrBlocked=\{5\} budgetBlocked=\{6\} mtfBlocked=\{7\} geometryBlocked=\{8\} volumeBlocked=\{9\} duplicateBlocked=\{10\} capitalInfeasible=\{11\}"\s*,\s*\n\s*_diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\s*\n\s*_diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible\);'
new='''Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10} capitalInfeasible={11} geometryValid={12} geometryQualityRejected={13}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,\n                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible, _diagGeometryValidated, _diagGeometryRejectedQuality);'''
once(old,new,'commercial diagnostic',re.S)

for token in ['Geometry Quality Engine','GeometryQualityScore(SwingPoint','PrzConfluence','TimeSymmetry','PivotQuality','_diagGeometryValidated','geometryValid={12}','GeometryQuality = best.GeometryQuality','class Candidate']:
    if token not in s: raise SystemExit('geometry engine missing token: '+token)
if 'PatternMatch' in s or 'GeometryQualityScore(Pivot ' in s: raise SystemExit('obsolete geometry dependency remains')
p.write_text(s,encoding='utf-8')
print('Applied V28.1 Geometry Quality Engine with structural helper anchor')
