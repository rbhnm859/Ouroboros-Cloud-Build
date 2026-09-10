using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBot : Robot
    {
        [Parameter("SymbolName", DefaultValue = "XAUUSD")]
        public string SymbolName { get; set; }

        [Parameter("RiskPercent", DefaultValue = 1.5, MinValue = 0.1, MaxValue = 5.0)]
        public double RiskPercent { get; set; }

        [Parameter("MaxDrawdown(%)", DefaultValue = 20.0, MinValue = 1.0, MaxValue = 80.0)]
        public double MaxDrawdown { get; set; }

        [Parameter("DailyLossLimit(%)", DefaultValue = 5.0, MinValue = 0.5, MaxValue = 30.0)]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Close All On Daily Lock", DefaultValue = false)]
        public bool CloseAllOnDailyLock { get; set; }

        [Parameter("Auto Re-Protect On Start", DefaultValue = true)]
        public bool AutoReprotectOnStart { get; set; }

        [Parameter("Emergency SL ATR Mult", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0)]
        public double EmergencySlAtrMult { get; set; }

        [Parameter("Emergency TP RR", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 10.0)]
        public double EmergencyTpRR { get; set; }

        [Parameter("SessionStart(GMT)", DefaultValue = 8, MinValue = 0, MaxValue = 23)]
        public int SessionStart { get; set; }

        [Parameter("SessionEnd(GMT)", DefaultValue = 22, MinValue = 0, MaxValue = 23)]
        public int SessionEnd { get; set; }

        [Parameter("MTF Enabled", DefaultValue = true)]
        public bool MTFEnabled { get; set; }

        [Parameter("PatternConfidence", DefaultValue = 0.75, MinValue = 0.5, MaxValue = 0.99)]
        public double PatternConfidence { get; set; }

        [Parameter("Max Concurrent Trades", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int MaxConcurrentTrades { get; set; }

        [Parameter("Max Same Direction Trades", DefaultValue = 1, MinValue = 1, MaxValue = 10)]
        public int MaxSameDirectionTrades { get; set; }

        [Parameter("Cooldown Minutes", DefaultValue = 15, MinValue = 1, MaxValue = 240)]
        public int CooldownMinutes { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 5, MaxValue = 100)]
        public int AtrPeriod { get; set; }

        [Parameter("SL ATR Mult", DefaultValue = 1.3, MinValue = 0.5, MaxValue = 10.0)]
        public double SlAtrMult { get; set; }

        [Parameter("TP CD Mult", DefaultValue = 0.618, MinValue = 0.2, MaxValue = 3.0)]
        public double TpCdMult { get; set; }

        [Parameter("Min RR", DefaultValue = 1.2, MinValue = 0.5, MaxValue = 10.0)]
        public double MinRR { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 40.0, MinValue = 1.0, MaxValue = 300.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Min SL (pips)", DefaultValue = 30.0, MinValue = 1.0, MaxValue = 1000.0)]
        public double MinStopLossPips { get; set; }

        [Parameter("Min TP (pips)", DefaultValue = 30.0, MinValue = 1.0, MaxValue = 2000.0)]
        public double MinTakeProfitPips { get; set; }

        [Parameter("Min Stop Distance (pips)", DefaultValue = 10.0, MinValue = 0.0, MaxValue = 500.0)]
        public double MinStopDistancePips { get; set; }

        [Parameter("SL Update Step (pips)", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 50.0)]
        public double SlUpdateStepPips { get; set; }

        [Parameter("SL Update Cooldown (sec)", DefaultValue = 5, MinValue = 1, MaxValue = 120)]
        public int SlUpdateCooldownSec { get; set; }

        [Parameter("Swing Depth", DefaultValue = 5, MinValue = 2, MaxValue = 20)]
        public int SwingDepth { get; set; }

        [Parameter("Swing Lookback", DefaultValue = 180, MinValue = 50, MaxValue = 1000)]
        public int SwingLookback { get; set; }

        [Parameter("Pivot Scan Count", DefaultValue = 12, MinValue = 5, MaxValue = 60)]
        public int PivotScanCount { get; set; }

        [Parameter("Min Leg ATR Ratio", DefaultValue = 0.8, MinValue = 0.1, MaxValue = 10.0)]
        public double MinLegAtrRatio { get; set; }

        [Parameter("BreakEven Trigger (pips)", DefaultValue = 120.0, MinValue = 5.0, MaxValue = 1000.0)]
        public double BreakEvenTriggerPips { get; set; }

        [Parameter("BreakEven Offset (pips)", DefaultValue = 10.0, MinValue = 0.0, MaxValue = 200.0)]
        public double BreakEvenOffsetPips { get; set; }

        [Parameter("Trailing Trigger (pips)", DefaultValue = 180.0, MinValue = 10.0, MaxValue = 2000.0)]
        public double TrailingTriggerPips { get; set; }

        [Parameter("Trailing Distance (pips)", DefaultValue = 90.0, MinValue = 5.0, MaxValue = 1000.0)]
        public double TrailingDistancePips { get; set; }

        [Parameter("Enable Partial TP", DefaultValue = true)]
        public bool EnablePartialTP { get; set; }

        [Parameter("TP1 at RR", DefaultValue = 1.0, MinValue = 0.3, MaxValue = 10.0)]
        public double Tp1RR { get; set; }

        [Parameter("TP1 Close %", DefaultValue = 50.0, MinValue = 5.0, MaxValue = 95.0)]
        public double Tp1ClosePercent { get; set; }

        [Parameter("Block News Window", DefaultValue = true)]
        public bool BlockNewsWindow { get; set; }

        [Parameter("Blocked Windows GMT", DefaultValue = "12:25-12:45;14:25-14:45")]
        public string BlockedWindowsGMT { get; set; }

        private const string BotLabel = "HarmonyBot";

        private Symbol _symbol;
        private Bars _signalBars;

        private double _initialEquity;
        private double _equityPeak;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastProcessedSignalBarTime = DateTime.MinValue;

        private DateTime _currentDay;
        private double _dayStartEquity;
        private bool _dailyLocked;

        private HarmonicPatternDetector _detector;

        private readonly Dictionary<long, bool> _tp1Done = new Dictionary<long, bool>();
        private readonly Dictionary<long, double> _initialRiskPips = new Dictionary<long, double>();
        private readonly HashSet<long> _partialClosing = new HashSet<long>();
        private readonly Dictionary<long, DateTime> _lastSlModifyTime = new Dictionary<long, DateTime>();

        protected override void OnStart()
        {
            _symbol = Symbols.GetSymbol(SymbolName);
            if (_symbol == null)
            {
                Print("[ERROR] Symbol not found: {0}", SymbolName);
                Stop();
                return;
            }

            _signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);
            if (_signalBars == null || _signalBars.Count < 20)
            {
                Print("[ERROR] Unable to load bars for symbol={0}", SymbolName);
                Stop();
                return;
            }

            _detector = new HarmonicPatternDetector(
                SwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult, PivotScanCount, MinLegAtrRatio);

            _initialEquity = Account.Equity;
            _equityPeak = Account.Equity;

            ResetDailyStateIfNeeded(true);
            RebuildRuntimeStateFromOpenPositions();

            if (AutoReprotectOnStart)
                ReProtectExistingPositions();

            Positions.Opened += OnPositionOpened;
            Positions.Closed += OnPositionClosed;

            Print("HarmonyBot latest started | Symbol={0} | TF={1} | Equity={2:F2}",
                SymbolName, Bars.TimeFrame, _initialEquity);
        }

        protected override void OnStop()
        {
            Positions.Opened -= OnPositionOpened;
            Positions.Closed -= OnPositionClosed;

            EnsureServerSideProtectionBeforeStop();
        }

        protected override void OnBar()
        {
            try
            {
                ResetDailyStateIfNeeded(false);
                UpdateRiskLocks();

                if (_dailyLocked)
                {
                    if (CloseAllOnDailyLock)
                        CloseAllBotPositions("DailyLock");
                    return;
                }

                if (IsPeakDrawdownExceeded()) return;
                if (!IsTradingSession()) return;
                if (!IsSpreadValid()) return;
                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;

                var open = Positions.FindAll(BotLabel, SymbolName);
                if (open.Length >= MaxConcurrentTrades) return;
                if ((Server.Time - _lastTradeTime).TotalMinutes < CooldownMinutes) return;

                if (_signalBars == null)
                    _signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);

                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback))
                    return;

                DateTime barTime = _signalBars.OpenTimes[_signalBars.Count - 1];
                if (barTime <= _lastProcessedSignalBarTime) return;
                _lastProcessedSignalBarTime = barTime;

                int signalIndex = _signalBars.Count - 1;
                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                if (atrNow <= 0) return;

                Signal signal;
                bool found = _detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, out signal);
                if (!found || signal == null) return;

                if (!PassMtfFilter(signal.Direction)) return;
                if (CountOpenPositionsInDirection(signal.Direction) >= MaxSameDirectionTrades) return;

                double slPips, tpPips;
                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;

                double volumeInUnits = CalculateVolumeByRisk(slPips);
                if (volumeInUnits <= 0) return;

                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
                var tr = ExecuteMarketOrder(tt, SymbolName, volumeInUnits, BotLabel, slPips, tpPips);

                if (tr != null && tr.IsSuccessful)
                {
                    _lastTradeTime = Server.Time;
                    Print("[TRADE] {0} vol={1} sl={2:F1} tp={3:F1} conf={4:F2}",
                        tt, volumeInUnits, slPips, tpPips, signal.Confidence);
                }
                else
                {
                    Print("[ORDER ERROR] {0}", tr == null ? "null result" : tr.Error.ToString());
                }
            }
            catch (Exception ex)
            {
                Print("[EXCEPTION-OnBar] {0}", ex.Message);
            }
        }

        protected override void OnTick()
        {
            try
            {
                ResetDailyStateIfNeeded(false);
                UpdateRiskLocks();
                ManageOpenPositions();
            }
            catch (Exception ex)
            {
                Print("[EXCEPTION-OnTick] {0}", ex.Message);
            }
        }

        private void OnPositionOpened(PositionOpenedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;

            _tp1Done[p.Id] = false;
            _partialClosing.Remove(p.Id);

            double rp = p.StopLoss.HasValue
                ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                : 0.0001;

            _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
            _lastSlModifyTime[p.Id] = DateTime.MinValue;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;

            _tp1Done.Remove(p.Id);
            _initialRiskPips.Remove(p.Id);
            _partialClosing.Remove(p.Id);
            _lastSlModifyTime.Remove(p.Id);
        }

        private void ManageOpenPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);

            foreach (var p in positions)
            {
                double profitPips = p.Pips;

                if (!_tp1Done.ContainsKey(p.Id)) _tp1Done[p.Id] = false;
                if (!_initialRiskPips.ContainsKey(p.Id))
                {
                    double rp = p.StopLoss.HasValue ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value)) : 0.0001;
                    _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
                }
                if (!_lastSlModifyTime.ContainsKey(p.Id)) _lastSlModifyTime[p.Id] = DateTime.MinValue;

                if (EnablePartialTP && !_tp1Done[p.Id] && !_partialClosing.Contains(p.Id))
                {
                    double rr = profitPips / _initialRiskPips[p.Id];
                    if (rr >= Tp1RR)
                    {
                        _partialClosing.Add(p.Id);
                        bool ok = TryPartialClose(p);
                        _partialClosing.Remove(p.Id);

                        if (ok)
                        {
                            _tp1Done[p.Id] = true;
                            double be = p.TradeType == TradeType.Buy
                                ? p.EntryPrice + PipsToPrice(BreakEvenOffsetPips)
                                : p.EntryPrice - PipsToPrice(BreakEvenOffsetPips);

                            TryModifyStopLoss(p, be);
                        }
                    }
                }

                if (profitPips >= BreakEvenTriggerPips)
                {
                    double be = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + PipsToPrice(BreakEvenOffsetPips)
                        : p.EntryPrice - PipsToPrice(BreakEvenOffsetPips);

                    TryModifyStopLoss(p, be);
                }

                if (profitPips >= TrailingTriggerPips)
                {
                    double trail = p.TradeType == TradeType.Buy
                        ? _symbol.Bid - PipsToPrice(TrailingDistancePips)
                        : _symbol.Ask + PipsToPrice(TrailingDistancePips);

                    TryModifyStopLoss(p, trail);
                }
            }
        }

        private bool TryModifyStopLoss(Position p, double newSl)
        {
            if (!CanImproveStopLoss(p, newSl)) return false;

            DateTime last = _lastSlModifyTime.ContainsKey(p.Id) ? _lastSlModifyTime[p.Id] : DateTime.MinValue;
            if ((Server.Time - last).TotalSeconds < SlUpdateCooldownSec) return false;

            var mr = ModifyPosition(p, newSl, p.TakeProfit);
            if (mr != null && mr.IsSuccessful)
            {
                _lastSlModifyTime[p.Id] = Server.Time;
                return true;
            }

            if (mr != null)
                Print("[SL MODIFY ERROR] PosId={0} | {1}", p.Id, mr.Error);
            return false;
        }

        private bool CanImproveStopLoss(Position p, double newSl)
        {
            if (!HasMinDistanceFromMarket(p.TradeType, newSl, MinStopDistancePips))
                return false;

            if (p.StopLoss.HasValue)
            {
                double deltaPips = PriceToPips(Math.Abs(newSl - p.StopLoss.Value));
                if (deltaPips < SlUpdateStepPips) return false;
            }

            if (p.TradeType == TradeType.Buy)
            {
                if (newSl >= _symbol.Bid) return false;
                return !p.StopLoss.HasValue || newSl > p.StopLoss.Value;
            }
            else
            {
                if (newSl <= _symbol.Ask) return false;
                return !p.StopLoss.HasValue || newSl < p.StopLoss.Value;
            }
        }

        private bool TryPartialClose(Position p)
        {
            try
            {
                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);
                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);
                long closeUnits = (long)Math.Floor(norm);
                if (closeUnits <= 0) return false;

                double remain = p.VolumeInUnits - closeUnits;
                if (closeUnits < _symbol.VolumeInUnitsMin) return false;
                if (remain > 0 && remain < _symbol.VolumeInUnitsMin) return false;

                var tr = ClosePosition(p, closeUnits);
                if (tr != null && tr.IsSuccessful)
                {
                    Print("[TP1] Partial close | PosId={0} closed={1} remain={2}",
                        p.Id, closeUnits, Math.Max(0, remain));
                    return true;
                }

                Print("[TP1 ERROR] PosId={0} | {1}", p.Id, tr == null ? "null result" : tr.Error.ToString());
                return false;
            }
            catch (Exception ex)
            {
                Print("[TP1 EXCEPTION] PosId={0} | {1}", p.Id, ex.Message);
                return false;
            }
        }

        private void UpdateRiskLocks()
        {
            if (Account.Equity > _equityPeak)
                _equityPeak = Account.Equity;

            if (_dayStartEquity > 0)
            {
                double ddDay = (_dayStartEquity - Account.Equity) / _dayStartEquity * 100.0;
                if (ddDay >= DailyLossLimitPercent)
                {
                    if (!_dailyLocked)
                        Print("[DAILY LOCK] DD={0:F2}% >= {1:F2}%", ddDay, DailyLossLimitPercent);
                    _dailyLocked = true;
                }
            }
        }

        private bool IsPeakDrawdownExceeded()
        {
            if (_equityPeak <= 0) return false;
            double dd = (_equityPeak - Account.Equity) / _equityPeak * 100.0;
            if (dd >= MaxDrawdown)
            {
                Print("[RISK] Peak DD={0:F2}% >= {1:F2}%", dd, MaxDrawdown);
                return true;
            }
            return false;
        }

        private void ResetDailyStateIfNeeded(bool force)
        {
            DateTime today = Server.Time.Date;
            if (force || today != _currentDay)
            {
                _currentDay = today;
                _dayStartEquity = Account.Equity;
                _dailyLocked = false;
                Print("[DAILY RESET] {0:yyyy-MM-dd} StartEquity={1:F2}", _currentDay, _dayStartEquity);
            }
        }

        private void CloseAllBotPositions(string reason)
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            foreach (var p in positions)
            {
                var tr = ClosePosition(p);
                if (tr != null && tr.IsSuccessful)
                    Print("[FORCE CLOSE] PosId={0} by {1}", p.Id, reason);
            }
        }

        private void ReProtectExistingPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            if (positions == null || positions.Length == 0) return;

            if (_signalBars == null)
                _signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);

            int idx = _signalBars != null ? _signalBars.Count - 1 : -1;
            double atrNow = (idx > AtrPeriod) ? CalculateAtr(_signalBars, AtrPeriod, idx) : 0;

            foreach (var p in positions)
            {
                if (!_tp1Done.ContainsKey(p.Id))
                    _tp1Done[p.Id] = true;

                if (!_initialRiskPips.ContainsKey(p.Id))
                {
                    double rp = p.StopLoss.HasValue
                        ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                        : Math.Max(MinStopLossPips, atrNow > 0 ? PriceToPips(atrNow * SlAtrMult) : MinStopLossPips);

                    _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
                }

                if (!_lastSlModifyTime.ContainsKey(p.Id))
                    _lastSlModifyTime[p.Id] = DateTime.MinValue;

                if (!p.StopLoss.HasValue || !p.TakeProfit.HasValue)
                {
                    if (atrNow <= 0) continue;

                    double slDistPrice = Math.Max(PipsToPrice(MinStopLossPips), atrNow * EmergencySlAtrMult);
                    double tpDistPrice = Math.Max(PipsToPrice(MinTakeProfitPips), slDistPrice * EmergencyTpRR);

                    double sl = p.TradeType == TradeType.Buy
                        ? p.EntryPrice - slDistPrice
                        : p.EntryPrice + slDistPrice;

                    double tp = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + tpDistPrice
                        : p.EntryPrice - tpDistPrice;

                    if (HasMinDistanceFromMarket(p.TradeType, sl, MinStopDistancePips))
                    {
                        var mr = ModifyPosition(p, sl, tp);
                        if (mr != null && mr.IsSuccessful)
                            Print("[RE-PROTECT] PosId={0} SL/TP restored.", p.Id);
                        else
                            Print("[RE-PROTECT ERROR] PosId={0} {1}", p.Id, mr == null ? "null" : mr.Error.ToString());
                    }
                }
            }
        }

        private void EnsureServerSideProtectionBeforeStop()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            if (positions == null || positions.Length == 0) return;

            if (_signalBars == null)
                _signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);

            int idx = _signalBars != null ? _signalBars.Count - 1 : -1;
            double atrNow = (idx > AtrPeriod) ? CalculateAtr(_signalBars, AtrPeriod, idx) : 0;
            if (atrNow <= 0) return;

            foreach (var p in positions)
            {
                if (p.StopLoss.HasValue && p.TakeProfit.HasValue) continue;

                double slDistPrice = Math.Max(PipsToPrice(MinStopLossPips), atrNow * EmergencySlAtrMult);
                double tpDistPrice = Math.Max(PipsToPrice(MinTakeProfitPips), slDistPrice * EmergencyTpRR);

                double sl = p.TradeType == TradeType.Buy
                    ? p.EntryPrice - slDistPrice
                    : p.EntryPrice + slDistPrice;

                double tp = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + tpDistPrice
                    : p.EntryPrice - tpDistPrice;

                if (!HasMinDistanceFromMarket(p.TradeType, sl, MinStopDistancePips))
                    continue;

                var mr = ModifyPosition(p, sl, tp);
                if (mr != null && mr.IsSuccessful)
                    Print("[STOP-PROTECT] PosId={0} protected before bot stop.", p.Id);
            }
        }

        private bool ValidateOrderGeometryAndReprice(Signal signal, out double slPips, out double tpPips)
        {
            slPips = 0;
            tpPips = 0;
            if (signal == null) return false;

            double entry = signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double sl = signal.StopLoss;
            double tp = signal.TakeProfit;

            if (entry <= 0 || sl <= 0 || tp <= 0) return false;

            if (signal.Direction == TradeDirection.Buy)
            {
                if (!(sl < entry && entry < tp)) return false;
            }
            else
            {
                if (!(tp < entry && entry < sl)) return false;
            }

            slPips = PriceToPips(Math.Abs(entry - sl));
            tpPips = PriceToPips(Math.Abs(tp - entry));

            if (slPips < MinStopLossPips) return false;
            if (tpPips < MinTakeProfitPips) return false;

            double rr = tpPips / slPips;
            if (rr < MinRR) return false;

            TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            if (!HasMinDistanceFromMarket(tt, sl, MinStopDistancePips)) return false;

            return true;
        }

        private bool HasMinDistanceFromMarket(TradeType tradeType, double stopPrice, double minDistancePips)
        {
            double dist = PipsToPrice(minDistancePips);
            if (tradeType == TradeType.Buy)
                return (_symbol.Bid - stopPrice) >= dist;
            return (stopPrice - _symbol.Ask) >= dist;
        }

        private int CountOpenPositionsInDirection(TradeDirection direction)
        {
            int count = 0;
            var positions = Positions.FindAll(BotLabel, SymbolName);
            foreach (var p in positions)
            {
                if (direction == TradeDirection.Buy && p.TradeType == TradeType.Buy) count++;
                if (direction == TradeDirection.Sell && p.TradeType == TradeType.Sell) count++;
            }
            return count;
        }

        private bool IsTradingSession()
        {
            int h = Server.Time.Hour;
            if (SessionStart == SessionEnd) return true;
            if (SessionStart < SessionEnd) return h >= SessionStart && h < SessionEnd;
            return h >= SessionStart || h < SessionEnd;
        }

        private bool IsSpreadValid()
        {
            double spreadPips = (_symbol.Ask - _symbol.Bid) / _symbol.PipSize;
            if (spreadPips > MaxSpreadPips)
            {
                Print("[SKIP] Spread {0:F1} > {1:F1} pips", spreadPips, MaxSpreadPips);
                return false;
            }
            return true;
        }

        private bool IsInBlockedNewsWindow(DateTime serverTime)
        {
            if (string.IsNullOrWhiteSpace(BlockedWindowsGMT))
                return false;

            TimeSpan now = serverTime.TimeOfDay;
            string[] windows = BlockedWindowsGMT.Split(new[] { ';' }, StringSplitOptions.RemoveEmptyEntries);

            foreach (string w in windows)
            {
                string[] se = w.Trim().Split('-');
                if (se.Length != 2) continue;

                TimeSpan s, e;
                bool okS = TimeSpan.TryParseExact(se[0].Trim(), @"hh\:mm", CultureInfo.InvariantCulture, out s) ||
                           TimeSpan.TryParseExact(se[0].Trim(), @"h\:mm", CultureInfo.InvariantCulture, out s);
                bool okE = TimeSpan.TryParseExact(se[1].Trim(), @"hh\:mm", CultureInfo.InvariantCulture, out e) ||
                           TimeSpan.TryParseExact(se[1].Trim(), @"h\:mm", CultureInfo.InvariantCulture, out e);

                if (!okS || !okE) continue;

                bool inWin = s <= e ? (now >= s && now <= e) : (now >= s || now <= e);
                if (inWin)
                {
                    Print("[NEWS BLOCK] {0}", w.Trim());
                    return true;
                }
            }
            return false;
        }

        private bool PassMtfFilter(TradeDirection direction)
        {
            if (!MTFEnabled) return true;

            var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            if (h1 == null || h1.Count < 220) return false;

            double ema50 = CalculateEma(h1.ClosePrices, 50, h1.Count - 1);
            double ema200 = CalculateEma(h1.ClosePrices, 200, h1.Count - 1);

            return direction == TradeDirection.Buy ? ema50 > ema200 : ema50 < ema200;
        }

        private double CalculateEma(DataSeries series, int period, int endIndex)
        {
            if (series == null || period <= 0 || endIndex <= 0 || endIndex >= series.Count) return 0;

            int start = Math.Max(0, endIndex - period * 6);
            double k = 2.0 / (period + 1.0);
            double ema = series[start];

            for (int i = start + 1; i <= endIndex; i++)
                ema = series[i] * k + ema * (1.0 - k);

            return ema;
        }

        private double CalculateAtr(Bars bars, int period, int endIndex)
        {
            if (bars == null || period <= 1 || endIndex <= 0 || endIndex >= bars.Count) return 0;
            if (endIndex - period < 1) return 0;

            double sum = 0;
            int start = endIndex - period + 1;

            for (int i = start; i <= endIndex; i++)
            {
                double high = bars.HighPrices[i];
                double low = bars.LowPrices[i];
                double prevClose = bars.ClosePrices[i - 1];

                double tr1 = high - low;
                double tr2 = Math.Abs(high - prevClose);
                double tr3 = Math.Abs(low - prevClose);

                sum += Math.Max(tr1, Math.Max(tr2, tr3));
            }

            return sum / period;
        }

        private double CalculateVolumeByRisk(double slPips)
        {
            if (slPips <= 0 || slPips < MinStopLossPips || _symbol.PipValue <= 0) return 0;

            double riskAmount = Account.Equity * (RiskPercent / 100.0);
            double raw = riskAmount / (slPips * _symbol.PipValue);

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;

            double vol = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (vol < _symbol.VolumeInUnitsMin) return 0;
            if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;

            return vol;
        }

        private double PriceToPips(double d)
        {
            if (_symbol.PipSize <= 0) return 0;
            return d / _symbol.PipSize;
        }

        private double PipsToPrice(double pips)
        {
            return pips * _symbol.PipSize;
        }

        private void RebuildRuntimeStateFromOpenPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            foreach (var p in positions)
            {
                if (!_tp1Done.ContainsKey(p.Id))
                    _tp1Done[p.Id] = false;

                if (!_initialRiskPips.ContainsKey(p.Id))
                {
                    double rp = p.StopLoss.HasValue ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value)) : 0.0001;
                    _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
                }

                if (!_lastSlModifyTime.ContainsKey(p.Id))
                    _lastSlModifyTime[p.Id] = DateTime.MinValue;
            }
        }
    }

    public enum TradeDirection
    {
        Buy,
        Sell
    }

    public class Signal
    {
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public double StopLoss { get; set; }
        public double TakeProfit { get; set; }
        public double Confidence { get; set; }
        public string PatternName { get; set; }
    }

    public class SwingPoint
    {
        public int Index { get; set; }
        public double Price { get; set; }
        public bool IsHigh { get; set; }
    }

    public class HarmonicPatternDetector
    {
        private readonly int _depth;
        private readonly int _lookback;
        private readonly double _minConfidence;
        private readonly double _slAtrMult;
        private readonly double _tpCdMult;
        private readonly int _scanCount;
        private readonly double _minLegAtrRatio;

        public HarmonicPatternDetector(int depth, int lookback, double minConfidence, double slAtrMult, double tpCdMult, int scanCount, double minLegAtrRatio)
        {
            _depth = Math.Max(2, depth);
            _lookback = Math.Max(50, lookback);
            _minConfidence = minConfidence;
            _slAtrMult = slAtrMult;
            _tpCdMult = tpCdMult;
            _scanCount = Math.Max(5, scanCount);
            _minLegAtrRatio = Math.Max(0.1, minLegAtrRatio);
        }

        public bool TryDetect(Bars bars, int currentIndex, double atrNow, Symbol symbol, out Signal signal)
        {
            signal = null;
            if (bars == null || symbol == null || currentIndex < _depth * 3 || currentIndex >= bars.Count || atrNow <= 0)
                return false;

            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);
            if (pivots.Count < 5) return false;

            int start = Math.Max(0, pivots.Count - _scanCount);
            Candidate best = null;
            double bestScore = -1;

            for (int i = start; i <= pivots.Count - 5; i++)
            {
                var c = Evaluate(pivots[i], pivots[i + 1], pivots[i + 2], pivots[i + 3], pivots[i + 4], atrNow);
                if (c != null && c.Score > bestScore)
                {
                    best = c;
                    bestScore = c.Score;
                }
            }

            if (best == null || best.Score < _minConfidence) return false;

            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;
            double entry = dir == TradeDirection.Buy ? symbol.Ask : symbol.Bid;
            double stop = dir == TradeDirection.Buy ? best.D.Price - atrNow * _slAtrMult : best.D.Price + atrNow * _slAtrMult;
            double cdRange = Math.Abs(best.C.Price - best.D.Price);
            double tpDist = Math.Max(cdRange * _tpCdMult, atrNow * 1.2);
            double tp = dir == TradeDirection.Buy ? entry + tpDist : entry - tpDist;

            if (dir == TradeDirection.Buy && !(stop < entry && entry < tp)) return false;
            if (dir == TradeDirection.Sell && !(tp < entry && entry < stop)) return false;

            signal = new Signal
            {
                Direction = dir,
                EntryPrice = entry,
                StopLoss = stop,
                TakeProfit = tp,
                Confidence = best.Score,
                PatternName = "Gartley"
            };
            return true;
        }

        private Candidate Evaluate(SwingPoint x, SwingPoint a, SwingPoint b, SwingPoint c, SwingPoint d, double atr)
        {
            bool bull = (a.Price > x.Price) && (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);
            bool bear = (a.Price < x.Price) && (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);
            if (!bull && !bear) return null;

            double xa = Math.Abs(a.Price - x.Price);
            double ab = Math.Abs(b.Price - a.Price);
            double bc = Math.Abs(c.Price - b.Price);
            double cd = Math.Abs(d.Price - c.Price);
            double xd = Math.Abs(d.Price - x.Price);

            if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0) return null;
            if (xa < atr * _minLegAtrRatio || ab < atr * _minLegAtrRatio || bc < atr * _minLegAtrRatio || cd < atr * _minLegAtrRatio) return null;

            double rXab = ab / xa;
            double rAbc = bc / ab;
            double rBcd = cd / bc;
            double rXad = xd / xa;

            bool valid =
                InRange(rXab, 0.55, 0.72) &&
                InRange(rAbc, 0.382, 0.886) &&
                InRange(rBcd, 1.13, 1.80) &&
                InRange(rXad, 0.70, 0.90);

            if (!valid) return null;

            double s1 = RatioScore(rXab, 0.618);
            double s2 = RatioScore(rAbc, 0.618);
            double s3 = RatioScore(rBcd, 1.272);
            double s4 = RatioScore(rXad, 0.786);

            int tXA = Math.Max(1, a.Index - x.Index);
            int tAB = Math.Max(1, b.Index - a.Index);
            int tBC = Math.Max(1, c.Index - b.Index);
            int tCD = Math.Max(1, d.Index - c.Index);

            double ts = (SymmetryScore(tXA, tAB) + SymmetryScore(tAB, tBC) + SymmetryScore(tBC, tCD)) / 3.0;
            double score = ((s1 + s2 + s3 + s4) / 4.0) * 0.8 + ts * 0.2;

            return new Candidate
            {
                X = x,
                A = a,
                B = b,
                C = c,
                D = d,
                IsBullish = bull,
                Score = score
            };
        }

        private List<SwingPoint> BuildSwingPoints(Bars bars, int endIndex, int lookback, int depth)
        {
            var pivots = new List<SwingPoint>();
            int start = Math.Max(depth, endIndex - lookback);

            for (int i = start; i <= endIndex - depth; i++)
            {
                bool isHigh = true;
                bool isLow = true;

                double hi = bars.HighPrices[i];
                double lo = bars.LowPrices[i];

                for (int j = i - depth; j <= i + depth; j++)
                {
                    if (j < 0 || j >= bars.Count || j == i) continue;
                    if (bars.HighPrices[j] > hi) isHigh = false;
                    if (bars.LowPrices[j] < lo) isLow = false;
                    if (!isHigh && !isLow) break;
                }

                if (isHigh && !isLow)
                    pivots.Add(new SwingPoint { Index = i, Price = hi, IsHigh = true });
                else if (isLow && !isHigh)
                    pivots.Add(new SwingPoint { Index = i, Price = lo, IsHigh = false });
                else if (isHigh && isLow)
                {
                    if (pivots.Count == 0 || pivots[pivots.Count - 1].IsHigh)
                        pivots.Add(new SwingPoint { Index = i, Price = lo, IsHigh = false });
                    else
                        pivots.Add(new SwingPoint { Index = i, Price = hi, IsHigh = true });
                }
            }

            pivots = pivots.OrderBy(p => p.Index).ToList();
            if (pivots.Count == 0) return pivots;

            var compressed = new List<SwingPoint> { pivots[0] };
            for (int i = 1; i < pivots.Count; i++)
            {
                SwingPoint last = compressed[compressed.Count - 1];
                SwingPoint cur = pivots[i];

                if (cur.IsHigh == last.IsHigh)
                {
                    if (cur.IsHigh)
                    {
                        if (cur.Price >= last.Price) compressed[compressed.Count - 1] = cur;
                    }
                    else
                    {
                        if (cur.Price <= last.Price) compressed[compressed.Count - 1] = cur;
                    }
                }
                else
                {
                    compressed.Add(cur);
                }
            }

            return compressed;
        }

        private bool InRange(double v, double min, double max) { return v >= min && v <= max; }

        private double RatioScore(double value, double ideal)
        {
            if (ideal <= 0) return 0;
            double err = Math.Abs(value - ideal) / ideal;
            double score = 1.0 - err;
            if (score < 0) return 0;
            if (score > 1) return 1;
            return score;
        }

        private double SymmetryScore(double a, double b)
        {
            double ratio = a > b ? a / b : b / a;
            return Math.Max(0, Math.Min(1, 1.0 / ratio));
        }

        private class Candidate
        {
            public SwingPoint X;
            public SwingPoint A;
            public SwingPoint B;
            public SwingPoint C;
            public SwingPoint D;
            public bool IsBullish;
            public double Score;
        }
    }
}
