from pathlib import Path
import re

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# ============================================================
# v27 Commercial RC: native risk engine + projected budget +
# small-account SL compression + robust protection lifecycle.
# Applied after v26.2 patches.
# ============================================================

# 1) Commercial parameters after Small Account Grid Guard.
needle = '''        [Parameter("Small Account Grid Guard", DefaultValue = true)]\n        public bool SmallAccountGridGuard { get; set; }\n'''
insert = needle + '''\n        [Parameter("Commercial Risk Engine", DefaultValue = true)]\n        public bool CommercialRiskEngine { get; set; }\n\n        [Parameter("Projected Risk Guard", DefaultValue = true)]\n        public bool ProjectedRiskGuard { get; set; }\n\n        [Parameter("Risk Headroom %", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 2.0)]\n        public double RiskHeadroomPercent { get; set; }\n\n        [Parameter("Compress SL To Risk Budget", DefaultValue = true)]\n        public bool CompressStopToRiskBudget { get; set; }\n\n        [Parameter("Max SL Compression Ratio", DefaultValue = 0.90, MinValue = 0.0, MaxValue = 1.0)]\n        public double MaxStopCompressionRatio { get; set; }\n\n        [Parameter("Disable Partial TP At Min Volume", DefaultValue = true)]\n        public bool DisablePartialAtMinVolume { get; set; }\n'''
if needle not in s: raise SystemExit('commercial parameter insertion point missing')
s = s.replace(needle, insert, 1)

# 2) Diagnostics fields.
field = '        private bool _pendingPrimaryUseGrid;\n'
if field not in s: raise SystemExit('diag field point missing')
s = s.replace(field, field + '''        private long _diagSignalsDetected;\n        private long _diagRiskCompressed;\n        private long _diagRiskBlocked;\n        private long _diagOrdersOpened;\n        private long _diagPartialSkipped;\n''', 1)

# 3) Count detected signals right after detector success.
needle = '''                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))\n                    return;\n                if (signal == null) return;\n'''
repl = '''                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))\n                    return;\n                if (signal == null) return;\n                _diagSignalsDetected++;\n'''
if needle not in s: raise SystemExit('signal count point missing')
s = s.replace(needle, repl, 1)

# 4) Commercial geometry hook after normal geometry validation.
needle = '''                double slPips, tpPips;\n                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n\n                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n'''
repl = '''                double slPips, tpPips;\n                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;\n\n                double riskBudgetPct = GetTradeRiskBudgetPercent();\n                if (CommercialRiskEngine && !ApplyCommercialRiskGeometry(ref slPips, ref tpPips, riskBudgetPct))\n                {\n                    _diagRiskBlocked++;\n                    return;\n                }\n\n                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;\n'''
if needle not in s: raise SystemExit('geometry hook missing')
s = s.replace(needle, repl, 1)

# 5) Ensure volume sizing uses the same precomputed budget.
s = s.replace('volumeInUnits = CalculateVolumeByRisk(orderSlPips);', 'volumeInUnits = CalculateVolumeByRisk(orderSlPips, riskBudgetPct);', 1)
s = s.replace('volumeInUnits = CalculateVolumeByRisk(slPips);', 'volumeInUnits = CalculateVolumeByRisk(slPips, riskBudgetPct);', 1)

# 6) Count successful primary orders.
needle = '''                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n'''
if needle not in s: raise SystemExit('order count point missing')
s = s.replace(needle, '''                    _lastTradeTime = Server.Time;\n                    _dailyTradeCount++;\n                    _diagOrdersOpened++;\n''', 1)

# 7) Replace risk sizing with cTrader native risk APIs.
start = s.find('        private double CalculateVolumeByRisk(double slPips)\n')
end = s.find('        private bool CheckNotionalLimit(double volume)\n', start)
if start < 0 or end < 0: raise SystemExit('risk sizing block missing')
new_risk = r'''        private double GetCurrentDayDrawdownPercent()
        {
            if (_dayStartEquity <= 0) return 0;
            return Math.Max(0.0, (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0);
        }

        private double GetCurrentWeekDrawdownPercent()
        {
            if (_weekStartEquity <= 0) return 0;
            return Math.Max(0.0, (_weekStartEquity - Account.Equity) / _weekStartEquity * 100.0);
        }

        private double GetCurrentPeakDrawdownPercent()
        {
            if (_equityPeak <= 0) return 0;
            return Math.Max(0.0, (_equityPeak - Account.Equity) / _equityPeak * 100.0);
        }

        private double GetTradeRiskBudgetPercent()
        {
            double pct = RiskPercent * GetDynamicRiskFactor();
            if (!CommercialRiskEngine) return Math.Max(0.0, pct);
            if (pct <= 0 || Account.Equity <= 0) return 0;

            if (ProjectedRiskGuard)
            {
                double headroom = Math.Max(0.0, RiskHeadroomPercent);
                if (DailyLossLimitPercent > 0)
                    pct = Math.Min(pct, Math.Max(0.0, DailyLossLimitPercent - GetCurrentDayDrawdownPercent() - headroom));
                if (WeeklyLossLimitPercent > 0)
                    pct = Math.Min(pct, Math.Max(0.0, WeeklyLossLimitPercent - GetCurrentWeekDrawdownPercent() - headroom));
                if (MaxDrawdown > 0)
                    pct = Math.Min(pct, Math.Max(0.0, MaxDrawdown - GetCurrentPeakDrawdownPercent() - headroom));
            }

            return Math.Max(0.0, pct);
        }

        private bool ApplyCommercialRiskGeometry(ref double slPips, ref double tpPips, double riskBudgetPct)
        {
            if (!CommercialRiskEngine) return true;
            if (_symbol == null || Account.Equity <= 0 || riskBudgetPct <= 0) return false;

            double minVol = _symbol.VolumeInUnitsMin;
            if (minVol <= 0) return false;

            double riskAmount = Account.Equity * riskBudgetPct / 100.0;
            double maxPips;
            try { maxPips = _symbol.PipsForFixedRisk(riskAmount, minVol); }
            catch { return false; }

            double floorPips = Math.Max(EffectiveMinStopLossPips(), MinStopDistancePips);
            if (double.IsNaN(maxPips) || double.IsInfinity(maxPips) || maxPips < floorPips)
            {
                if ((Server.Time - _lastVolumeWarnTime).TotalMinutes >= 5)
                {
                    Print("[RISK-BLOCK] minVol={0} riskBudget={1:F2}% cannot support minSL={2:F1} pips (max={3:F1}).",
                        minVol, riskBudgetPct, floorPips, maxPips);
                    _lastVolumeWarnTime = Server.Time;
                }
                return false;
            }

            if (slPips > maxPips)
            {
                if (!CompressStopToRiskBudget) return false;
                double compression = 1.0 - (maxPips / Math.Max(slPips, 0.0001));
                if (compression > Math.Max(0.0, Math.Min(1.0, MaxStopCompressionRatio)))
                {
                    Print("[RISK-BLOCK] SL compression {0:P1} exceeds limit {1:P1}; original={2:F1} max={3:F1}.",
                        compression, MaxStopCompressionRatio, slPips, maxPips);
                    return false;
                }

                double original = slPips;
                slPips = Math.Max(floorPips, maxPips);
                double spreadPips = Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid));
                double rrFloor = slPips * MinRR + (UseCostAdjustedRR ? spreadPips : 0.0);
                tpPips = Math.Max(tpPips, Math.Max(EffectiveMinTakeProfitPips(), rrFloor));
                _diagRiskCompressed++;
                Print("[RISK-COMPRESS] SL {0:F1}->{1:F1} pips, TP={2:F1}, budget={3:F2}%.",
                    original, slPips, tpPips, riskBudgetPct);
            }
            return true;
        }

        private double CalculateVolumeByRisk(double slPips, double riskBudgetPct)
        {
            if (slPips <= 0 || slPips < EffectiveMinStopLossPips() || _symbol == null) return 0;
            double equity = Account.Equity;
            if (equity <= 0) return 0;

            double pct = CommercialRiskEngine ? riskBudgetPct : RiskPercent * GetDynamicRiskFactor();
            if (!CommercialRiskEngine && DailyLossLimitPercent > 0)
                pct = Math.Min(pct, DailyLossLimitPercent);
            if (pct <= 0) return 0;

            double riskAmount = equity * pct / 100.0;
            double vol;
            try { vol = _symbol.VolumeForFixedRisk(riskAmount, slPips, RoundingMode.Down); }
            catch { return 0; }
            if (double.IsNaN(vol) || double.IsInfinity(vol) || vol <= 0) return 0;

            vol = _symbol.NormalizeVolumeInUnits(vol, RoundingMode.Down);
            if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;

            if (vol >= _symbol.VolumeInUnitsMin)
                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;

            if (!AllowMinVolumeFallback) return 0;

            double minVol = _symbol.VolumeInUnitsMin;
            double minRisk;
            try { minRisk = _symbol.AmountRisked(minVol, slPips); }
            catch { return 0; }
            double minRiskPct = equity > 0 ? minRisk / equity * 100.0 : double.MaxValue;

            double capPct = CommercialRiskEngine
                ? pct
                : (IsSmallAccountMode() ? MicroMinVolumeRiskCapPercent : MinVolumeRiskCapPercent);
            if (!CommercialRiskEngine && DailyLossLimitPercent > 0)
                capPct = Math.Min(capPct, DailyLossLimitPercent);

            if (minRiskPct > capPct + 1e-6)
            {
                if ((Server.Time - _lastVolumeWarnTime).TotalMinutes >= 5)
                {
                    Print("[VOLUME] Native min-volume risk {0:F2}% > cap {1:F2}%; trade skipped.", minRiskPct, capPct);
                    _lastVolumeWarnTime = Server.Time;
                }
                return 0;
            }

            Print("[VOLUME] Native min-volume fallback {0}, risk={1:F2}%.", minVol, minRiskPct);
            return (CheckNotionalLimit(minVol) && CheckMarginLimit(minVol)) ? minVol : 0;
        }

'''
s = s[:start] + new_risk + s[end:]

# 8) Replace custom margin estimate with broker-native GetEstimatedMargin.
start = s.find('        private bool CheckMarginLimit(double volume)\n')
end = s.find('        private bool IsSmallAccountMode()\n', start)
if start < 0 or end < 0: raise SystemExit('margin block missing')
new_margin = r'''        private bool CheckMarginLimit(double volume)
        {
            if (_symbol == null || volume <= 0) return false;
            double freeMargin = Account.FreeMargin;
            if (freeMargin <= 0) return false;

            double margin;
            try { margin = _symbol.GetEstimatedMargin(TradeType.Buy, volume); }
            catch { return false; }
            if (double.IsNaN(margin) || double.IsInfinity(margin) || margin < 0) return false;

            double maxMargin = freeMargin * Math.Max(0.0, 1.0 - MarginBufferPercent / 100.0);
            if (margin > maxMargin)
            {
                if ((Server.Time - _lastMarginWarnTime).TotalMinutes >= 5)
                {
                    Print("[MARGIN] vol={0} native est.margin={1:F2} > {2:F2} (free={3:F2}, buffer={4:F0}%). Skip.",
                        volume, margin, maxMargin, freeMargin, MarginBufferPercent);
                    _lastMarginWarnTime = Server.Time;
                }
                return false;
            }
            return true;
        }

'''
s = s[:start] + new_margin + s[end:]

# 9) Fix small account boundary robustly (v26.2 already <=; keep commercial explicit).
s = s.replace('return SmallAccountMode && Account.Equity <= SmallAccountThreshold;',
              'return SmallAccountMode && Account.Equity <= SmallAccountThreshold + 1e-9;', 1)

# 10) Replace R calculation with cTrader native AmountRisked.
old = '''        private double ComputeR(double money, double riskPips, double initVol, double pips)\n        {\n            if (initVol > 0 && _symbol != null && _symbol.PipValue > 0)\n            {\n                double riskMoney = riskPips * _symbol.PipValue * initVol;\n                if (riskMoney > 0) return money / riskMoney;\n            }\n            return pips / Math.Max(riskPips, 0.0001);\n        }\n'''
new = '''        private double ComputeR(double money, double riskPips, double initVol, double pips)\n        {\n            if (initVol > 0 && _symbol != null && riskPips > 0)\n            {\n                try\n                {\n                    double riskMoney = _symbol.AmountRisked(initVol, riskPips);\n                    if (riskMoney > 0) return money / riskMoney;\n                }\n                catch { }\n            }\n            return pips / Math.Max(riskPips, 0.0001);\n        }\n'''
if old not in s: raise SystemExit('ComputeR block missing')
s = s.replace(old, new, 1)

# 11) Robust min-volume partial TP + fresh position after partial close.
start = s.find('        private void ManageOpenPositions()\n')
end = s.find('        private bool TryPartialClose(Position p)\n', start)
if start < 0 or end < 0: raise SystemExit('ManageOpenPositions block missing')
new_manage = r'''        private void ManageOpenPositions()
        {
            var snapshots = Positions.FindAll(BotLabel, SymbolName);

            foreach (var snapshot in snapshots)
            {
                if (snapshot == null) continue;
                Position p = Positions.FindById((int)snapshot.Id) ?? snapshot;
                if (EnableFibGrid && _positionToBasket.ContainsKey(p.Id)) continue;

                EnsureRuntimeState(p);
                double profitPips = p.Pips;
                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);

                if (EnablePartialTP && !_tp1Done[p.Id] && !_partialClosing.Contains(p.Id))
                {
                    double rr = profitPips / Math.Max(_initialRiskPips[p.Id], 0.0001);
                    if (rr >= Tp1RR)
                    {
                        double minVol = _symbol.VolumeInUnitsMin;
                        bool canSplit = !DisablePartialAtMinVolume || p.VolumeInUnits >= minVol * 2.0 - 1e-9;
                        if (!canSplit)
                        {
                            _tp1Done[p.Id] = true;
                            _diagPartialSkipped++;
                            Print("[TP1-SKIP] PosId={0} volume={1} cannot be safely split at broker min={2}; keep full position.",
                                p.Id, p.VolumeInUnits, minVol);
                        }
                        else
                        {
                            _partialClosing.Add(p.Id);
                            bool ok = TryPartialClose(p);
                            _partialClosing.Remove(p.Id);

                            if (ok)
                            {
                                _tp1Done[p.Id] = true;
                                Position fresh = Positions.FindById((int)p.Id);
                                if (fresh == null) continue;
                                p = fresh;
                                profitPips = p.Pips;

                                double be = p.TradeType == TradeType.Buy
                                    ? p.EntryPrice + PipsToPrice(beOffsetPips)
                                    : p.EntryPrice - PipsToPrice(beOffsetPips);
                                TryModifyStopLoss(p, be);
                            }
                        }
                    }
                }

                Position current = Positions.FindById((int)p.Id);
                if (current == null) continue;
                p = current;
                profitPips = p.Pips;

                if (profitPips >= BreakEvenTriggerPips)
                {
                    double be = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + PipsToPrice(beOffsetPips)
                        : p.EntryPrice - PipsToPrice(beOffsetPips);
                    TryModifyStopLoss(p, be);
                }

                current = Positions.FindById((int)p.Id);
                if (current == null) continue;
                p = current;
                profitPips = p.Pips;

                if (profitPips >= TrailingTriggerPips)
                {
                    double trail = p.TradeType == TradeType.Buy
                        ? _symbol.Bid - PipsToPrice(TrailingDistancePips)
                        : _symbol.Ask + PipsToPrice(TrailingDistancePips);
                    TryModifyStopLoss(p, trail);
                }
            }
        }

'''
s = s[:start] + new_manage + s[end:]

# 12) TryPartialClose: never accidentally turn a partial TP into full close.
needle = '''                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);\n                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);\n                long closeUnits = (long)Math.Floor(norm);\n                if (closeUnits <= 0) return false;\n\n                double remain = p.VolumeInUnits - closeUnits;\n                if (closeUnits < _symbol.VolumeInUnitsMin) return false;\n                if (remain > 0 && remain < _symbol.VolumeInUnitsMin) return false;\n'''
repl = '''                double minVol = _symbol.VolumeInUnitsMin;\n                if (p.VolumeInUnits < minVol * 2.0 - 1e-9) return false;\n\n                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);\n                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);\n                double closeUnits = norm;\n                if (closeUnits < minVol) return false;\n\n                double remain = p.VolumeInUnits - closeUnits;\n                if (remain < minVol) return false;\n'''
if needle not in s: raise SystemExit('partial units block missing')
s = s.replace(needle, repl, 1)

# 13) Partial realized estimate uses native risk conversion rather than raw PipValue arithmetic.
old = '                    double partialMoney = signedPips * _symbol.PipValue * closeUnits;\n'
new = '''                    double partialMoney = 0;\n                    try\n                    {\n                        double absMoney = _symbol.AmountRisked(closeUnits, Math.Abs(signedPips));\n                        partialMoney = signedPips >= 0 ? absMoney : -absMoney;\n                    }\n                    catch { partialMoney = 0; }\n'''
if old not in s: raise SystemExit('partial money line missing')
s = s.replace(old, new, 1)

# 14) Modern protection overload and live-position guard.
old = '''        private bool TryModifyStopLoss(Position p, double newSl)\n        {\n            if (!CanImproveStopLoss(p, newSl)) return false;\n\n            DateTime last = _lastSlModifyTime.ContainsKey(p.Id) ? _lastSlModifyTime[p.Id] : DateTime.MinValue;\n            if ((Server.Time - last).TotalSeconds < SlUpdateCooldownSec) return false;\n\n            var mr = ModifyPosition(p, newSl, p.TakeProfit);\n'''
new = '''        private bool TryModifyStopLoss(Position p, double newSl)\n        {\n            if (p == null) return false;\n            Position live = Positions.FindById((int)p.Id);\n            if (live == null) return false;\n            p = live;\n            if (!CanImproveStopLoss(p, newSl)) return false;\n\n            DateTime last = _lastSlModifyTime.ContainsKey(p.Id) ? _lastSlModifyTime[p.Id] : DateTime.MinValue;\n            if ((Server.Time - last).TotalSeconds < SlUpdateCooldownSec) return false;\n\n            var mr = ModifyPosition(p, newSl, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade);\n'''
if old not in s: raise SystemExit('TryModifyStopLoss block missing')
s = s.replace(old, new, 1)

# 15) Grid projected basket risk uses native AmountRisked per leg.
start = s.find('        private double ProjectedBasketLoss(GridBasket b, double addVolume, double addEntry, Position[] positions)\n')
end = s.find('        private double BasketR(GridBasket b, double cur)\n', start)
if start < 0 or end < 0: raise SystemExit('ProjectedBasketLoss block missing')
new_grid_risk = r'''        private double ProjectedBasketLoss(GridBasket b, double addVolume, double addEntry, Position[] positions)
        {
            if (_symbol == null) return double.MaxValue;
            double loss = 0;
            try
            {
                foreach (var p in positions)
                {
                    if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != b.Id) continue;
                    double pips = PriceToPips(Math.Abs(p.EntryPrice - b.StopPrice));
                    loss += _symbol.AmountRisked(p.VolumeInUnits, pips);
                }
                double addPips = PriceToPips(Math.Abs(addEntry - b.StopPrice));
                loss += _symbol.AmountRisked(addVolume, addPips);
            }
            catch { return double.MaxValue; }
            return Math.Max(0, loss);
        }

'''
s = s[:start] + new_grid_risk + s[end:]

# 16) Do not force min-volume grid add without exact risk validation.
needle = '''            if (addVolume < _symbol.VolumeInUnitsMin)\n            {\n                if (!AllowMinVolumeFallback) return;\n                addVolume = _symbol.VolumeInUnitsMin;\n            }\n'''
repl = '''            if (addVolume < _symbol.VolumeInUnitsMin)\n            {\n                if (!AllowMinVolumeFallback) return;\n                addVolume = _symbol.VolumeInUnitsMin;\n                double addStopPips = PriceToPips(Math.Abs(cur - b.StopPrice));\n                double addRisk;\n                try { addRisk = _symbol.AmountRisked(addVolume, addStopPips); }\n                catch { return; }\n                double addRiskPct = Account.Equity > 0 ? addRisk / Account.Equity * 100.0 : double.MaxValue;\n                if (addRiskPct > Math.Max(0.1, GridMaxTotalRiskPercent)) return;\n            }\n'''
if needle not in s: raise SystemExit('grid fallback block missing')
s = s.replace(needle, repl, 1)

# 17) Modernize basket stop modify overload.
s = s.replace('var mr = ModifyPosition(p, b.StopPrice, p.TakeProfit);',
              'var mr = ModifyPosition(p, b.StopPrice, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade);')

# 18) OnStop diagnostics.
needle = '''                PrintPatternLedger();\n                PrintGridReport();\n'''
repl = '''                PrintPatternLedger();\n                PrintGridReport();\n                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4}",\n                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped);\n'''
if needle not in s: raise SystemExit('OnStop diagnostics point missing')
s = s.replace(needle, repl, 1)

p.write_text(s, encoding='utf-8')
print('Applied v27 Commercial RC architecture fixes')
