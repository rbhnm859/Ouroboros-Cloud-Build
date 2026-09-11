from pathlib import Path
import runpy

# Build on the already-verified V2 runtime patch, then apply the V3 harmonic repair.
runpy.run_path('tools/harmonybotpro_fixed_patch.py', run_name='__main__')
s = Path('fixed/HarmonyBotPro/HarmonyBotPro.cs').read_text()

def rep(old, new, label, expected=1):
    global s
    n = s.count(old)
    if n != expected:
        raise SystemExit(f'{label}: expected {expected}, found {n}')
    s = s.replace(old, new)

# Gate counters in the robot.
rep('        private int _botOpenPositionCount;\n',
    '        private int _botOpenPositionCount;\n        private long _gateBars, _gateSession, _gateSpread, _gateNews, _gateAtr, _gatePattern, _gateMtf, _gateGeometry, _gateVolume, _gateOrders;\n',
    'gate fields')
rep('            try\n            {\n                ResetCalendarStates(false);\n                UpdateRiskLocks();\n',
    '            try\n            {\n                _gateBars++;\n                ResetCalendarStates(false);\n                UpdateRiskLocks();\n',
    'OnBar count')
rep('                if (!IsTradingSession()) return;\n                if (!IsSpreadValid()) return;\n                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;\n',
    '                if (!IsTradingSession()) return;\n                _gateSession++;\n                if (!IsSpreadValid()) return;\n                _gateSpread++;\n                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;\n                _gateNews++;\n',
    'session/spread/news')
rep('                if (atrNow <= 0 || atrNow < MinAtrPrice) return;\n',
    '                if (atrNow <= 0 || atrNow < MinAtrPrice) return;\n                _gateAtr++;\n',
    'ATR gate')
rep('                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, out signal))\n                    return;\n                if (signal == null) return;\n\n                if (!PassMtfFilter(signal.Direction)) return;\n',
    '                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, out signal))\n                    return;\n                if (signal == null) return;\n                _gatePattern++;\n\n                if (!PassMtfFilter(signal.Direction)) return;\n                _gateMtf++;\n',
    'pattern/MTF gates')
rep('                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n\n                double volumeInUnits = CalculateVolumeByRisk(slPips);\n                if (volumeInUnits <= 0) return;\n',
    '                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n                _gateGeometry++;\n\n                double volumeInUnits = CalculateVolumeByRisk(slPips);\n                if (volumeInUnits <= 0) return;\n                _gateVolume++;\n',
    'geometry/volume gates')
rep('                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n',
    '                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n                    _gateOrders++;\n',
    'order count')

# Harmonic detector counters.
rep('        private readonly bool _enableCypher;\n',
    '        private readonly bool _enableCypher;\n\n        public long WindowsChecked { get; private set; }\n        public long DirectionalStructures { get; private set; }\n        public long LegAtrPassed { get; private set; }\n        public long RatioCandidates { get; private set; }\n        public long ConfidencePassed { get; private set; }\n',
    'detector counters')
rep('            if (best == null || best.Score < _minConfidence) return false;\n\n            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;\n',
    '            if (best == null || best.Score < _minConfidence) return false;\n            ConfidencePassed++;\n\n            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;\n',
    'confidence counter')
rep('        private List<Candidate> Evaluate(SwingPoint x, SwingPoint a, SwingPoint b, SwingPoint c, SwingPoint d, double atr, PatternDef[] defs)\n        {\n            var result = new List<Candidate>();\n\n            bool bull =',
    '        private List<Candidate> Evaluate(SwingPoint x, SwingPoint a, SwingPoint b, SwingPoint c, SwingPoint d, double atr, PatternDef[] defs)\n        {\n            WindowsChecked++;\n            var result = new List<Candidate>();\n\n            bool bull =',
    'window counter')
rep('            if (!bull && !bear) return result;\n\n            double xa =',
    '            if (!bull && !bear) return result;\n            DirectionalStructures++;\n\n            double xa =',
    'directional counter')
rep('            if (xa < atr * _minLegAtrRatio || ab < atr * _minLegAtrRatio ||\n                bc < atr * _minLegAtrRatio || cd < atr * _minLegAtrRatio) return result;\n\n            double rXab =',
    '            if (xa < atr * _minLegAtrRatio || ab < atr * _minLegAtrRatio ||\n                bc < atr * _minLegAtrRatio || cd < atr * _minLegAtrRatio) return result;\n            LegAtrPassed++;\n\n            double rXab =',
    'leg ATR counter')

# Critical ratio repair: AD/XA for Gartley/Bat/Butterfly/Crab; Cypher uses XC.
rep('            double cd = Math.Abs(d.Price - c.Price);\n            double xd = Math.Abs(d.Price - x.Price);\n',
    '            double cd = Math.Abs(d.Price - c.Price);\n            double ad = Math.Abs(d.Price - a.Price);\n            double xc = Math.Abs(c.Price - x.Price);\n',
    'distances')
rep('            double rXab = ab / xa;\n            double rAbc = bc / ab;\n            double rBcd = cd / bc;\n            double rXad = xd / xa;\n',
    '            double rXab = ab / xa;\n            double rAbc = bc / ab;\n            double rBcd = cd / bc;\n            double rAdXa = ad / xa;\n            double rCxXa = xc / xa;\n            double rCdXc = xc > 0 ? cd / xc : 0;\n',
    'ratios')

old = '''            foreach (var def in defs)\n            {\n                if (!InRange(rXab, def.ABMin, def.ABMax)) continue;\n                if (!InRange(rAbc, def.BCMin, def.BCMax)) continue;\n                if (!InRange(rBcd, def.CDMin, def.CDMax)) continue;\n                if (!InRange(rXad, def.XDMin, def.XDMax)) continue;\n\n                double s1 = RatioScore(rXab, def.ABIdeal);\n                double s2 = RatioScore(rAbc, def.BCIdeal);\n                double s3 = RatioScore(rBcd, def.CDIdeal);\n                double s4 = RatioScore(rXad, def.XDIdeal);\n\n                double score = ((s1 + s2 + s3 + s4) / 4.0) * 0.8 + ts * 0.2;\n                score *= def.Weight;\n\n                result.Add(new Candidate\n                {\n                    X = x,\n                    A = a,\n                    B = b,\n                    C = c,\n                    D = d,\n                    IsBullish = bull,\n                    Score = score,\n                    PatternName = def.Name\n                });\n            }'''
new = '''            foreach (var def in defs)\n            {\n                double ratioScore;\n                if (def.Name == "Cypher")\n                {\n                    if (!InRange(rXab, 0.382, 0.618)) continue;\n                    if (!InRange(rCxXa, 1.13, 1.414)) continue;\n                    if (!InRange(rCdXc, 0.70, 0.90)) continue;\n                    double s1 = RatioScore(rXab, 0.50);\n                    double s2 = RatioScore(rCxXa, 1.272);\n                    double s3 = RatioScore(rCdXc, 0.786);\n                    ratioScore = (s1 + s2 + s3) / 3.0;\n                }\n                else\n                {\n                    if (!InRange(rXab, def.ABMin, def.ABMax)) continue;\n                    if (!InRange(rAbc, def.BCMin, def.BCMax)) continue;\n                    if (!InRange(rBcd, def.CDMin, def.CDMax)) continue;\n                    if (!InRange(rAdXa, def.XDMin, def.XDMax)) continue;\n                    double s1 = RatioScore(rXab, def.ABIdeal);\n                    double s2 = RatioScore(rAbc, def.BCIdeal);\n                    double s3 = RatioScore(rBcd, def.CDIdeal);\n                    double s4 = RatioScore(rAdXa, def.XDIdeal);\n                    ratioScore = (s1 + s2 + s3 + s4) / 4.0;\n                }\n\n                RatioCandidates++;\n                double score = ratioScore * 0.8 + ts * 0.2;\n                score *= def.Weight;\n                result.Add(new Candidate\n                {\n                    X = x, A = a, B = b, C = c, D = d, IsBullish = bull,\n                    Score = score, PatternName = def.Name\n                });\n            }'''
rep(old, new, 'harmonic loop')

rep('            if (_tracker != null)\n                _tracker.PrintReport(Account.Equity);\n',
    '            if (_tracker != null)\n                _tracker.PrintReport(Account.Equity);\n\n            Print("[GATES] bars={0} session={1} spread={2} news={3} atr={4} pattern={5} mtf={6} geometry={7} volume={8} orders={9}", _gateBars, _gateSession, _gateSpread, _gateNews, _gateAtr, _gatePattern, _gateMtf, _gateGeometry, _gateVolume, _gateOrders);\n            if (_detector != null) Print("[HARMONIC] windows={0} directional={1} legAtr={2} ratioCandidates={3} confidencePassed={4}", _detector.WindowsChecked, _detector.DirectionalStructures, _detector.LegAtrPassed, _detector.RatioCandidates, _detector.ConfidencePassed);\n',
    'OnStop diagnostics')

out = Path('fixed-v3/HarmonyBotPro/HarmonyBotPro.cs')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)
print('V3 patched:', out)
print('legacy rXad refs:', s.count('rXad'))
