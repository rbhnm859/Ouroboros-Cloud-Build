from pathlib import Path
import re, base64, gzip

# Runtime patch v2: preserve strategy parameters while fixing backtest data reuse and execution guards.
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

rep('_signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);', '_signalBars = Bars;', 'same-timeframe Bars', 4)
rep('        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();\n', '        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();\n        private int _botOpenPositionCount;\n', 'open count field')
rep('                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback))\n', '                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback) + 2)\n', 'closed bar min bars')
rep('                DateTime barTime = _signalBars.OpenTimes[_signalBars.Count - 1];\n', '                int signalIndex = _signalBars.Count - 2;\n                DateTime barTime = _signalBars.OpenTimes[signalIndex];\n', 'closed signal time')
rep('                int signalIndex = _signalBars.Count - 1;\n                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);\n', '                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);\n', 'remove forming signal index')
rep('                if (!PassMtfFilter(signal.Direction)) return;\n                if (CountOpenPositionsInDirection(signal.Direction) >= MaxSameDirectionTrades) return;\n', '                if (!PassMtfFilter(signal.Direction)) return;\n                TradeType desiredType = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n                if (open.Any(p => p.TradeType != desiredType)) return;\n                if (open.Count(p => p.TradeType == desiredType) >= MaxSameDirectionTrades) return;\n', 'hard no hedge')
rep('                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n', '                TradeType tt = desiredType;\n', 'trade type reuse')
rep('        protected override void OnTick()\n        {\n            try\n            {\n                ResetCalendarStates(false);\n', '        protected override void OnTick()\n        {\n            try\n            {\n                if (_botOpenPositionCount <= 0) return;\n                ResetCalendarStates(false);\n', 'flat tick fast path')
rep('            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            _tp1Done[p.Id] = false;\n', '            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            _botOpenPositionCount++;\n            _tp1Done[p.Id] = false;\n', 'opened count')
rep('            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            double partialVol = _totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0;\n', '            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;\n\n            if (_botOpenPositionCount > 0) _botOpenPositionCount--;\n            double partialVol = _totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0;\n', 'closed count')
rep('                var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);\n', '                var h1 = Bars.TimeFrame == TimeFrame.Hour ? Bars : MarketData.GetBars(TimeFrame.Hour, SymbolName);\n', 'reuse H1 Bars')
rep('                if (h1 != null && h1.Count >= 220)\n                {\n                    double ema50 = CalculateEma(h1.ClosePrices, 50, h1.Count - 1);\n                    double ema200 = CalculateEma(h1.ClosePrices, 200, h1.Count - 1);\n', '                if (h1 != null && h1.Count >= 221)\n                {\n                    int h1Index = h1.Count - 2;\n                    double ema50 = CalculateEma(h1.ClosePrices, 50, h1Index);\n                    double ema200 = CalculateEma(h1.ClosePrices, 200, h1Index);\n', 'H1 closed MTF')
rep('                if (h4 != null && h4.Count >= 220)\n                {\n                    double ema50 = CalculateEma(h4.ClosePrices, 50, h4.Count - 1);\n                    double ema200 = CalculateEma(h4.ClosePrices, 200, h4.Count - 1);\n', '                if (h4 != null && h4.Count >= 221)\n                {\n                    int h4Index = h4.Count - 2;\n                    double ema50 = CalculateEma(h4.ClosePrices, 50, h4Index);\n                    double ema200 = CalculateEma(h4.ClosePrices, 200, h4Index);\n', 'H4 closed MTF')
rep('        private void RebuildRuntimeStateFromOpenPositions()\n        {\n            var positions = Positions.FindAll(BotLabel, SymbolName);\n', '        private void RebuildRuntimeStateFromOpenPositions()\n        {\n            var positions = Positions.FindAll(BotLabel, SymbolName);\n            _botOpenPositionCount = positions == null ? 0 : positions.Length;\n', 'initial open count')

out = Path('fixed/HarmonyBotPro/HarmonyBotPro.cs')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s)
print('patched source:', out)
print('lines:', len(s.splitlines()))
print('remaining same-TF redundant calls:', s.count('MarketData.GetBars(Bars.TimeFrame, SymbolName)'))
