from pathlib import Path

PATH = Path('CumulativeDeltaScalper-EURUSD-v1/src/CumulativeDeltaScalper_EURUSD_v1.cs')
text = PATH.read_text(encoding='utf-8')


def replace_method(src: str, signature: str, replacement: str) -> str:
    start = src.find(signature)
    if start < 0:
        raise RuntimeError(f'method not found: {signature}')
    brace = src.find('{', start)
    if brace < 0:
        raise RuntimeError(f'opening brace not found: {signature}')
    depth = 0
    end = None
    for i in range(brace, len(src)):
        ch = src[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise RuntimeError(f'closing brace not found: {signature}')
    return src[:start] + replacement.rstrip() + src[end + 1:]


# 1) Remove O(N history) work from every tick/bar. Daily state is rebuilt once on startup,
#    then maintained incrementally by Positions.Closed.
text = text.replace('            SyncDailyStatsFromHistory();\n', '')

startup_anchor = '''            _accountPeakEquity = Account.Equity;\n            _dayPeakNetPnl = 0;\n\n            Positions.Closed += OnPositionClosed;'''
startup_replacement = '''            _accountPeakEquity = Account.Equity;\n            _dayPeakNetPnl = 0;\n\n            RebuildDailyStateFromHistory();\n            RecoverOpenPositionState();\n\n            Positions.Closed += OnPositionClosed;'''
if startup_anchor not in text:
    raise RuntimeError('OnStart state anchor not found')
text = text.replace(startup_anchor, startup_replacement, 1)

# 2) Use only completed HTF values for deterministic entry filters.
text = replace_method(text, '        private bool CheckHtfEma(int signal)', '''        private bool CheckHtfEma(int signal)\n        {\n            if (!UseHtfEmaFilter) return true;\n            int index = ClosedHtfIndex();\n            if (index < 0 || index >= _htfEma.Result.Count) return false;\n            double ema = _htfEma.Result[index];\n            int mainIndex = Bars.ClosePrices.Count - 2;\n            double referencePrice = mainIndex >= 0 ? Bars.ClosePrices[mainIndex] : Symbol.Bid;\n            if (double.IsNaN(ema) || ema <= 0) return false;\n            return signal > 0 ? referencePrice > ema : referencePrice < ema;\n        }''')

text = replace_method(text, '        private bool CheckEmaSlope(int signal)', '''        private bool CheckEmaSlope(int signal)\n        {\n            if (!UseHtfEmaFilter) return true;\n            int newest = ClosedHtfIndex();\n            int oldest = newest - Math.Max(1, EmaSlopeBars);\n            if (newest < 0 || oldest < 0 || newest >= _htfEma.Result.Count) return false;\n            double a = _htfEma.Result[newest];\n            double b = _htfEma.Result[oldest];\n            if (double.IsNaN(a) || double.IsNaN(b)) return false;\n            return signal > 0 ? a > b : a < b;\n        }\n\n        private int ClosedHtfIndex()\n        {\n            if (_htfBars == null || _htfBars.ClosePrices.Count < 2) return -1;\n            return _htfBars.ClosePrices.Count - 2;\n        }\n\n        private double ClosedHtfAdx()\n        {\n            int index = ClosedHtfIndex();\n            if (index < 0 || index >= _htfDms.ADX.Count) return 0;\n            double value = _htfDms.ADX[index];\n            return double.IsNaN(value) ? 0 : value;\n        }\n\n        private double ClosedAtr()\n        {\n            int index = Bars.ClosePrices.Count - 2;\n            if (index < 0 || index >= _atr.Result.Count) return 0;\n            double value = _atr.Result[index];\n            return double.IsNaN(value) ? 0 : value;\n        }''')

text = replace_method(text, '        private bool CheckAdx()', '''        private bool CheckAdx()\n        {\n            return ClosedHtfAdx() >= AdxThreshold;\n        }''')
text = text.replace('_htfDms.ADX.LastValue < requiredAdx', 'ClosedHtfAdx() < requiredAdx')
text = text.replace('_htfDms.ADX.LastValue < AdxThreshold + Math.Max(0.0, ShortAdxBonus)', 'ClosedHtfAdx() < AdxThreshold + Math.Max(0.0, ShortAdxBonus)')
text = text.replace('double atr = _atr.Result.LastValue;\n            if (atr < MinAtr)', 'double atr = ClosedAtr();\n            if (atr <= 0) { reason = "atr_not_ready"; return false; }\n            if (atr < MinAtr)', 1)
text = text.replace('double slPips = PriceDistanceToPips(_atr.Result.LastValue * SlAtrMultiplier);', 'double slPips = PriceDistanceToPips(ClosedAtr() * SlAtrMultiplier);', 1)
text = text.replace('double tpPips = UseRunnerExit ? slPips * Math.Max(1.0, EmergencyTpR) : PriceDistanceToPips(_atr.Result.LastValue * TpAtrMultiplier);', 'double tpPips = UseRunnerExit ? slPips * Math.Max(1.0, EmergencyTpR) : PriceDistanceToPips(ClosedAtr() * TpAtrMultiplier);', 1)

# 3) Interpret broker minimum protection distance according to MinDistanceType.
text = replace_method(text, '        private bool ValidateStopDistances(double slPips, double tpPips, out string reason)', '''        private bool ValidateStopDistances(double slPips, double tpPips, out string reason)\n        {\n            reason = string.Empty;\n            if (slPips <= 0 || tpPips <= 0) { reason = "invalid_sl_tp_distance"; return false; }\n\n            double referencePrice = Symbol.Bid > 0 ? Symbol.Bid : 1.0;\n            double slPriceDistance = slPips * Symbol.PipSize;\n            double tpPriceDistance = tpPips * Symbol.PipSize;\n            double minSl = BrokerMinDistancePrice(referencePrice, true);\n            double minTp = BrokerMinDistancePrice(referencePrice, false);\n\n            if (minSl > 0 && slPriceDistance + Symbol.TickSize < minSl)\n            {\n                reason = "sl_below_broker_minimum_distance";\n                return false;\n            }\n            if (minTp > 0 && tpPriceDistance + Symbol.TickSize < minTp)\n            {\n                reason = "tp_below_broker_minimum_distance";\n                return false;\n            }\n            return true;\n        }\n\n        private double BrokerMinDistancePrice(double referencePrice, bool stopLoss)\n        {\n            double raw = stopLoss ? Symbol.MinStopLossDistance : Symbol.MinTakeProfitDistance;\n            if (raw <= 0) return 0;\n            if (Symbol.MinDistanceType == SymbolMinDistanceType.Pips)\n                return raw * Symbol.PipSize;\n            return Math.Abs(referencePrice) * raw / 100.0;\n        }''')

# 4) Broker-safe runner / BE stop changes to prevent InvalidRequest loops.
text = replace_method(text, '        private void TryImproveStop(Position position, double newStopLoss, double? takeProfit, string reason)', '''        private void TryImproveStop(Position position, double newStopLoss, double? takeProfit, string reason)\n        {\n            newStopLoss = NormalizeStopForBroker(position.TradeType, newStopLoss);\n\n            if (position.TradeType == TradeType.Buy)\n            {\n                if (newStopLoss >= Symbol.Bid) return;\n                if (position.StopLoss.HasValue && newStopLoss <= position.StopLoss.Value + Symbol.TickSize * 0.25) return;\n            }\n            else\n            {\n                if (newStopLoss <= Symbol.Ask) return;\n                if (position.StopLoss.HasValue && newStopLoss >= position.StopLoss.Value - Symbol.TickSize * 0.25) return;\n            }\n\n            TradeResult result = ModifyPosition(position, newStopLoss, takeProfit);\n            if (result.IsSuccessful)\n            {\n                _breakevenApplied = true;\n                Debug("stop improved: " + reason + " newSL=" + newStopLoss.ToString("F" + Symbol.Digits));\n            }\n            else\n                Debug("stop improve failed " + reason + ": " + result.Error);\n        }\n\n        private double NormalizeStopForBroker(TradeType type, double desired)\n        {\n            double market = type == TradeType.Buy ? Symbol.Bid : Symbol.Ask;\n            double minDistance = BrokerMinDistancePrice(market, true);\n            double adjusted = desired;\n\n            if (type == TradeType.Buy)\n            {\n                double highest = market - minDistance;\n                if (minDistance > 0) adjusted = Math.Min(adjusted, highest);\n                adjusted = Math.Round(adjusted, Symbol.Digits);\n                if (minDistance > 0 && adjusted > highest) adjusted = Math.Round(highest - Symbol.TickSize, Symbol.Digits);\n            }\n            else\n            {\n                double lowest = market + minDistance;\n                if (minDistance > 0) adjusted = Math.Max(adjusted, lowest);\n                adjusted = Math.Round(adjusted, Symbol.Digits);\n                if (minDistance > 0 && adjusted < lowest) adjusted = Math.Round(lowest + Symbol.TickSize, Symbol.Digits);\n            }\n            return adjusted;\n        }''')

# 5) Restore state after Cloud/mobile restart and keep daily accounting event-driven.
text = text.replace('''            if (position == null)\n            {\n                _openTradeDirection = 0;\n                _openTradeTime = DateTime.MinValue;\n                _openInitialRiskPips = 0;\n                return;\n            }\n\n            if (UseHardActualLossCap''', '''            if (position == null)\n            {\n                ClearOpenPositionState();\n                return;\n            }\n\n            if (_openTradeTime == DateTime.MinValue)\n                RecoverOpenPositionState(position);\n\n            if (UseHardActualLossCap''', 1)

text = replace_method(text, '        private void SyncDailyStatsFromHistory()', '''        private void RebuildDailyStateFromHistory()\n        {\n            DateTime dayStart = Server.Time.Date;\n            HistoricalTrade[] closedToday = History\n                .Where(h => h.SymbolName == SymbolName && h.Label == TradeLabel && h.ClosingTime >= dayStart)\n                .OrderBy(h => h.ClosingTime)\n                .ToArray();\n\n            _dailyClosedPnl = closedToday.Sum(h => h.NetProfit);\n            _dailyTradeCount = History.Count(h => h.SymbolName == SymbolName && h.Label == TradeLabel && h.EntryTime >= dayStart)\n                + Positions.Count(p => p.SymbolName == SymbolName && p.Label == TradeLabel && p.EntryTime >= dayStart);\n\n            _consecutiveLosses = 0;\n            _lastLossTime = DateTime.MinValue;\n            foreach (HistoricalTrade h in closedToday)\n            {\n                if (h.NetProfit < 0)\n                {\n                    _consecutiveLosses++;\n                    _lastLossTime = h.ClosingTime;\n                }\n                else if (h.NetProfit > 0)\n                {\n                    _consecutiveLosses = 0;\n                    _lastLossTime = DateTime.MinValue;\n                }\n            }\n\n            _dayStartBalance = Account.Balance - _dailyClosedPnl;\n            _dayHighEquity = Math.Max(Account.Equity, _dayStartBalance);\n            _dayPeakNetPnl = Math.Max(0, _dailyClosedPnl);\n        }''')

text = replace_method(text, '        private void OnPositionClosed(PositionClosedEventArgs args)', '''        private void OnPositionClosed(PositionClosedEventArgs args)\n        {\n            Position p = args.Position;\n            if (p.SymbolName != SymbolName || p.Label != TradeLabel) return;\n\n            if (Server.Time.Date == _currentDay)\n                _dailyClosedPnl += p.NetProfit;\n\n            if (p.NetProfit < 0)\n            {\n                _consecutiveLosses++;\n                _lastLossTime = Server.Time;\n            }\n            else if (p.NetProfit > 0)\n            {\n                _consecutiveLosses = 0;\n                _lastLossTime = DateTime.MinValue;\n            }\n\n            UpdateDailyProfitPeak();\n            ClearOpenPositionState();\n            Debug("position closed pnl=" + p.NetProfit.ToString("F2") + " dayPnl=" + _dailyClosedPnl.ToString("F2") + " consecutiveLosses=" + _consecutiveLosses);\n        }''')

text = replace_method(text, '        private bool HasOpenPosition()', '''        private Position FindOpenPosition()\n        {\n            return Positions.FirstOrDefault(p => p.SymbolName == SymbolName && p.Label == TradeLabel);\n        }\n\n        private bool HasOpenPosition()\n        {\n            return FindOpenPosition() != null;\n        }\n\n        private void RecoverOpenPositionState()\n        {\n            Position position = FindOpenPosition();\n            if (position != null) RecoverOpenPositionState(position);\n        }\n\n        private void RecoverOpenPositionState(Position position)\n        {\n            _openTradeTime = position.EntryTime;\n            _lastTradeTime = position.EntryTime;\n            _openTradeDirection = position.TradeType == TradeType.Buy ? 1 : -1;\n            _openInitialRiskPips = position.StopLoss.HasValue\n                ? Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize\n                : PriceDistanceToPips(ClosedAtr() * SlAtrMultiplier);\n            _breakevenApplied = position.StopLoss.HasValue &&\n                (position.TradeType == TradeType.Buy ? position.StopLoss.Value >= position.EntryPrice : position.StopLoss.Value <= position.EntryPrice);\n        }\n\n        private void ClearOpenPositionState()\n        {\n            _openTradeDirection = 0;\n            _openTradeTime = DateTime.MinValue;\n            _openInitialRiskPips = 0;\n            _breakevenApplied = false;\n        }''')

# Ensure no obsolete full-history scan remains in hot paths.
if 'SyncDailyStatsFromHistory' in text:
    raise RuntimeError('old history-sync method/reference still present')

PATH.write_text(text, encoding='utf-8')
print('Debug refactor applied:', PATH)
print('Length:', len(text), 'chars')
