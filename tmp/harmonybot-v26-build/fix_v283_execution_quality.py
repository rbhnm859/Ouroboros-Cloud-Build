from pathlib import Path
import re

p=Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s=p.read_text(encoding='utf-8')

# V28.3: wire the previously diagnostic V28.2 layer into the real execution funnel.
# RiskPercent, MaxDrawdown, broker minimum volume, structural SL, Fibonacci Grid and all 12 patterns remain intact.

# Version/counters. Keep V28.2 helpers for compatibility, but expose a real V28.3 execution ledger.
s=s.replace('private const string CommercialIteration = "V28.2-Strategy-Quality-RC";', 'private const string CommercialIteration = "V28.3-Execution-Quality-RC";', 1)
field='        private long _v282GridAttributed;\n'
if field not in s: raise SystemExit('V28.2 field anchor missing')
s=s.replace(field, field+'        private long _v283QualityAccepted;\n        private long _v283QualityRejected;\n        private long _v283CapitalRejected;\n        private long _v283GridOrders;\n',1)

# Add component-quality controls next to the existing Geometry Engine controls.
anchor='        public double MinGeometryQuality { get; set; }\n'
if anchor not in s: raise SystemExit('MinGeometryQuality anchor missing')
params='''\n\n        [Parameter("Min PRZ Confluence", DefaultValue = 0.55, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinPrzConfluence { get; set; }\n\n        [Parameter("Min Time Symmetry", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinTimeSymmetry { get; set; }\n\n        [Parameter("Min Pivot Quality", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 1.0)]\n        public double MinPivotQuality { get; set; }\n'''
s=s.replace(anchor,anchor+params,1)

# Replace the actual V28.1 geometry decision block. This is the real Pattern -> Geometry -> Entry funnel.
old='''                if (EnableGeometryQualityEngine)\n                {\n                    if (signal.GeometryQuality < MinGeometryQuality) { _diagGeometryRejectedQuality++; _diagGeometryBlocked++; return; }\n                    _diagGeometryValidated++;\n                }\n'''
new='''                if (EnableGeometryQualityEngine)\n                {\n                    bool geometryPass = signal.GeometryQuality >= MinGeometryQuality\n                        && signal.PrzConfluence >= MinPrzConfluence\n                        && signal.TimeSymmetry >= MinTimeSymmetry\n                        && signal.PivotQuality >= MinPivotQuality;\n                    if (!geometryPass)\n                    {\n                        _diagGeometryRejectedQuality++;\n                        _diagGeometryBlocked++;\n                        _v283QualityRejected++;\n                        Print("[V283-QUALITY-REJECT] pattern={0} q={1:F3} prz={2:F3} time={3:F3} pivot={4:F3}",\n                            signal.PatternName ?? "NA", signal.GeometryQuality, signal.PrzConfluence, signal.TimeSymmetry, signal.PivotQuality);\n                        return;\n                    }\n                    _diagGeometryValidated++;\n                    _v283QualityAccepted++;\n                    Print("[V283-QUALITY-ACCEPT] pattern={0} q={1:F3} prz={2:F3} time={3:F3} pivot={4:F3}",\n                        signal.PatternName ?? "NA", signal.GeometryQuality, signal.PrzConfluence, signal.TimeSymmetry, signal.PivotQuality);\n                }\n'''
if old not in s: raise SystemExit('real geometry funnel anchor missing')
s=s.replace(old,new,1)

# Wire capital infeasibility into the V28.3 ledger at every existing capital-rejection point.
# Do not alter the rejection itself and do not increase allowed risk.
n=s.count('_diagCapitalInfeasible++;')
if n < 2: raise SystemExit('expected capital rejection points missing')
s=s.replace('_diagCapitalInfeasible++;','_diagCapitalInfeasible++; _v283CapitalRejected++;')

# Attribute actual opened orders while Fibonacci Grid is enabled. This is deliberately an execution count,
# not a claim that Grid caused PnL; outcome attribution remains in the existing pattern ledger/history accounting.
order='_diagOrdersOpened++;'
if order not in s: raise SystemExit('order-open counter anchor missing')
s=s.replace(order,order+'\n                if (EnableFibGrid) _v283GridOrders++;',1)

# Replace V28.2 stop summary with a V28.3 execution-pipeline summary.
oldsum='Print("[V282-SUMMARY] iteration={0} geometryAccepted={1} capitalRejected={2} gridAttributed={3}", CommercialIteration, _v282GeometryAccepted, _v282CapitalRejected, _v282GridAttributed);'
if oldsum not in s: raise SystemExit('V28.2 summary anchor missing')
newsum='Print("[V283-SUMMARY] iteration={0} qualityAccepted={1} qualityRejected={2} capitalRejected={3} gridOrders={4}", CommercialIteration, _v283QualityAccepted, _v283QualityRejected, _v283CapitalRejected, _v283GridOrders);'
s=s.replace(oldsum,newsum,1)

required=['V28.3-Execution-Quality-RC','MinPrzConfluence','MinTimeSymmetry','MinPivotQuality','[V283-QUALITY-ACCEPT]','[V283-QUALITY-REJECT]','_v283CapitalRejected','_v283GridOrders','[V283-SUMMARY]','EnableFibGrid','GeometryQualityScore','SmallAccountMinSLPips','RiskPercent','capitalInfeasible','MinRR','Gartley','Bat','Butterfly','Crab','Cypher','Shark','FiveZero']
missing=[x for x in required if x not in s]
if missing: raise SystemExit('V28.3 integrity missing: '+','.join(missing))

p.write_text(s,encoding='utf-8')
print('Applied V28.3 real execution-quality funnel')
print('Wired geometry component gates, capital rejection ledger and Fibonacci Grid order attribution')
print('RiskPercent/MaxDrawdown/structural SL/broker minimum volume unchanged')
