from pathlib import Path
import re, base64, gzip

# HarmonyBotPro V3 patch:
# - carries forward V2 runtime/closed-bar/no-hedge fixes
# - repairs harmonic D-point ratio definitions
# - treats Cypher separately (C extension of XA, D retracement of XC)
# - adds gate counters for backtest diagnosis
wf = Path('.github/workflows/build-harmonybotpro-mobile.yml').read_text()
m = re.search(r'payload\s*=\s*"([A-Za-z0-9+/=]+)"', wf)
if not m:
    raise SystemExit('embedded source payload not found')
s = gzip.decompress(base64.b64decode(m.group(1))).decode()

def rep(old, new, label, expected=1):
    global s
    n = s.count(old)
    if n != expected:
        raise SystemExit(f'{label}: expected {expected}, found {n}')
    s = s.replace(old, new)

# ---------------- V2 runtime correctness fixes ----------------
rep('_signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);', '_signalBars = Bars;', 'same-timeframe Bars', 4)
rep('        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();\n',
    '        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();\n        private int _botOpenPositionCount;\n',
    'open count field')
rep('                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback))\n',
    '                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback) + 2)\n',
    'closed bar min bars')
rep('                DateTime barTime = _signalBars.OpenTimes[_signalBars.Count - 1];\n',
    '                int signalIndex = _signalBars.Count - 2;\n                DateTime barTime = _signalBars.OpenTimes[signalIndex];\n',
    'closed signal time')
rep('                int signalIndex = _signalBars.Count - 1;\n                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);\n',
    '                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);\n',
    'remove forming signal index')
rep('                if (!PassMtfFilter(signal.Direction)) return;\n                if (CountOpenPositionsInDirection(signal.Direction) >= MaxSameDirectionTrades) return;\n',
    '                if (!PassMtfFilter(signal.Direction)) return;\n                TradeType desiredType = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n                if (open.Any(p => p.TradeType != desiredType)) return;\n                if (open.Count(p => p.TradeType == desiredType) >= MaxSameDirectionTrades) return;\n',
    'hard no hedge')
rep('                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n',
    '                TradeType tt = desiredType;\n',
    'trade type reuse')
rep('        protected override void OnTick()\n        {\n            try\n            {\n                ResetCalendarStates(false);\n',
    '        protected override void OnTick()\n        {\n            try\n            {\n                if (_botOpenPositionCount <= 0) return;\n                ResetCalendarStates(false);\n',
    'flat tick fast path')
rep('            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            _tp1Done[p.Id] = false;\n',
    '            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            _botOpenPositionCount++;\n            _tp1Done[p.Id] = false;\n',
    'opened count')
rep('            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            double partialVol = _totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0;\n',
    '            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            if (_botOpenPositionCount > 0) _botOpenPositionCount--;\n            double partialVol = _totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0;\n',
    'closed count')
rep('                var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);\n',
    '                var h1 = Bars.TimeFrame == TimeFrame.Hour ? Bars : MarketData.GetBars(TimeFrame.Hour, SymbolName);\n',
    'reuse H1 Bars')
rep('                if (h1 != null && h1.Count >= 220)\n                {\n                    double ema50 = CalculateEma(h1.ClosePrices, 50, h1.Count - 1);\n                    double ema200 = CalculateEma(h1.ClosePrices, 200, h1.Count - 1);\n',
    '                if (h1 != null && h1.Count >= 221)\n                {\n                    int h1Index = h1.Count - 2;\n                    double ema50 = CalculateEma(h1.ClosePrices, 50, h1Index);\n                    double ema200 = CalculateEma(h1.ClosePrices, 200, h1Index);\n',
    'H1 closed MTF')
rep('                if (h4 != null && h4.Count >= 220)\n                {\n                    double ema50 = CalculateEma(h4.ClosePrices, 50, h4.Count - 1);\n                    double ema200 = CalculateEma(h4.ClosePrices, 200, h4.Count - 1);\n',
    '                if (h4 != null && h4.Count >= 221)\n                {\n                    int h4Index = h4.Count - 2;\n                    double ema50 = CalculateEma(h4.ClosePrices, 50, h4Index);\n                    double ema200 = CalculateEma(h4.ClosePrices, 200, h4Index);\n',
    'H4 closed MTF')
rep('        private void RebuildRuntimeStateFromOpenPositions()\n        {\n            var positions = Positions.FindAll(BotLabel, SymbolName);\n',
    '        private void RebuildRuntimeStateFromOpenPositions()\n        {\n            var positions = Positions.FindAll(BotLabel, SymbolName);\n            _botOpenPositionCount = positions == null ? 0 : positions.Length;\n',
    'initial open count')

# ---------------- Gate counters ----------------
rep('        private int _botOpenPositionCount;\n',
    '        private int _botOpenPositionCount;\n        private long _gateBars, _gateSession, _gateSpread, _gateNews, _gateAtr, _gatePattern, _gateMtf, _gateGeometry, _gateVolume, _gateOrders;\n',
    'gate counter fields')
rep('            try\n            {\n                ResetCalendarStates(false);\n                UpdateRiskLocks();\n',
    '            try\n            {\n                _gateBars++;\n                ResetCalendarStates(false);\n                UpdateRiskLocks();\n',
    'OnBar counter')
rep('                if (!IsTradingSession()) return;\n                if (!IsSpreadValid()) return;\n                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;\n',
    '                if (!IsTradingSession()) return;\n                _gateSession++;\n                if (!IsSpreadValid()) return;\n                _gateSpread++;\n                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;\n                _gateNews++;\n',
    'session spread news gates')
rep('                if (atrNow <= 0 || atrNow < MinAtrPrice) return;\n',
    '                if (atrNow <= 0 || atrNow < MinAtrPrice) return;\n                _gateAtr++;\n',
    'ATR gate')
rep('                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, out signal))\n                    return;\n                if (signal == null) return;\n\n                if (!PassMtfFilter(signal.Direction)) return;\n',
    '                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, out signal))\n                    return;\n                if (signal == null) return;\n                _gatePattern++;\n\n                if (!PassMtfFilter(signal.Direction)) return;\n                _gateMtf++;\n',
    'pattern and MTF gates')
rep('                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n\n                double volumeInUnits = CalculateVolumeByRisk(slPips);\n                if (volumeInUnits <= 0) return;\n',
    '                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n                _gateGeometry++;\n\n                double volumeInUnits = CalculateVolumeByRisk(slPips);\n                if (volumeInUnits <= 0) return;\n                _gateVolume++;\n',
    'geometry and volume gates')
rep('                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n',
    '                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n                    _gateOrders++;\n',
    'order counter')
rep('            if (_tracker != null)\n                _tracker.PrintReport(Account.Equity);\n',
    '            if (_tracker != null)\n                _tracker.PrintReport(Account.Equity);\n\n            Print("[GATES] bars={0} session={1} spread={2} news={3} atr={4} pattern={5} mtf={6} geometry={7} volume={8} orders={9}",\n                _gateBars, _gateSession, _gateSpread, _gateNews, _gateAtr, _gatePattern, _gateMtf, _gateGeometry, _gateVolume, _gateOrders);\n            if (_detector != null)\n                Print("[HARMONIC] windows={0} directional={1} legAtr={2} ratioCandidates={3} confidencePassed={4}",\n                    _detector.WindowsChecked, _detector.DirectionalStructures, _detector.LegAtrPassed, _detector.RatioCandidates, _detector.ConfidencePassed);\n',
    'OnStop diagnostics')

# ---------------- Harmonic detector diagnostics ----------------
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

# ---------------- Critical harmonic ratio repair ----------------
rep('            double cd = Math.Abs(d.Price - c.Price);\n            double xd = Math.Abs(d.Price - x.Price);\n',
    '            double cd = Math.Abs(d.Price - c.Price);\n            double ad = Math.Abs(d.Price - a.Price);\n            double xc = Math.Abs(c.Price - x.Price);\n',
    'replace XD with AD/XC distances')
rep('            double rXab = ab / xa;\n            double rAbc = bc / ab;\n            double rBcd = cd / bc;\n            double rXad = xd / xa;\n',
    '            double rXab = ab / xa;\n            double rAbc = bc / ab;\n            double rBcd = cd / bc;\n            double rAdXa = ad / xa;\n            double rCxXa = xc / xa;\n            double rCdXc = xc > 0 ? cd / xc : 0;\n',
    'ratio definitions')

old_loop = '''            foreach (var def in defs)\n            {\n                if (!InRange(rXab, def.ABMin, def.ABMax)) continue;\n                if (!InRange(rAbc, def.BCMin, def.BCMax)) continue;\n                if (!InRange(rBcd, def.CDMin, def.CDMax)) continue;\n                if (!InRange(rXad, def.XDMin, def.XDMax)) continue;\n\n                double s1 = RatioScore(rXab, def.ABIdeal);\n                double s2 = RatioScore(rAbc, def.BCIdeal);\n                double s3 = RatioScore(rBcd, def.CDIdeal);\n                double s4 = RatioScore(rXad, def.XDIdeal);\n\n                double score = ((s1 + s2 + s3 + s4) / 4.0) * 0.8 + ts * 0.2;\n                score *= def.Weight;\n\n                result.Add(new Candidate\n                {\n                    X = x,\n                    A = a,\n                    B = b,\n                    C = c,\n                    D = d,\n                    IsBullish = bull,\n                    Score = score,\n                    PatternName = def.Name\n                });\n            }'''
new_loop = '''            foreach (var def in defs)\n            {\n                double ratioScore;\n\n                if (def.Name == "Cypher")\n                {\n                    // Cypher is structurally different: B retraces XA, C extends XA,\n                    // and D is a 0.786 retracement of XC. Do not reuse AD/XA.\n                    if (!InRange(rXab, 0.382, 0.618)) continue;\n                    if (!InRange(rCxXa, 1.13, 1.414)) continue;\n                    if (!InRange(rCdXc, 0.70, 0.90)) continue;\n\n                    double s1 = RatioScore(rXab, 0.50);\n                    double s2 = RatioScore(rCxXa, 1.272);\n                    double s3 = RatioScore(rCdXc, 0.786);\n                    ratioScore = (s1 + s2 + s3) / 3.0;\n                }\n                else\n                {\n                    // Gartley/Bat/Butterfly/Crab define D from the XA leg by AD/XA\n                    // (retracement for Gartley/Bat; extension for Butterfly/Crab).\n                    if (!InRange(rXab, def.ABMin, def.ABMax)) continue;\n                    if (!InRange(rAbc, def.BCMin, def.BCMax)) continue;\n                    if (!InRange(rBcd, def.CDMin, def.CDMax)) continue;\n                    if (!InRange(rAdXa, def.XDMin, def.XDMax)) continue;\n\n                    double s1 = RatioScore(rXab, def.ABIdeal);\n                    double s2 = RatioScore(rAbc, def.BCIdeal);\n                    double s3 = RatioScore(rBcd, def.CDIdeal);\n                    double s4 = RatioScore(rAdXa, def.XDIdeal);\n                    ratioScore = (s1 + s2 + s3 + s4) / 4.0;\n                }\n\n                RatioCandidates++;\n                double score = ratioScore * 0.8 + ts * 0.2;\n                score *= def.Weight;\n\n                result.Add(new Candidate\n                {\n                    X = x,\n                    A = a,\n                    B = b,\n                    C = c,\n                    D = d,\n                    IsBullish = bull,\n                    Score = score,\n                    PatternName = def.Name\n                });\n            }'''
rep(old_loop, new_loop, 'harmonic evaluation loop')

out = Path('fixed-v3/HarmonyBotPro/HarmonyBotPro.cs')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)
print('patched source:', out)
print('lines:', len(s.splitlines()))
print('remaining same-TF redundant calls:', s.count('MarketData.GetBars(Bars.TimeFrame, SymbolName)'))
print('remaining legacy XD ratio refs:', s.count('rXad'))
