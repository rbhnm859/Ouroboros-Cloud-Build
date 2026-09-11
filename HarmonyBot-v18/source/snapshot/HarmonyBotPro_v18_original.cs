using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class HarmonyBotPro : Robot
    {
        // ============================================================
        //  1. Risk / Capital
        // ============================================================
        [Parameter("Symbol", DefaultValue = "XAUUSD")]
        public string SymbolName { get; set; }

        [Parameter("Risk % / trade", DefaultValue = 1.5, MinValue = 0.1, MaxValue = 5.0)]
        public double RiskPercent { get; set; }

        [Parameter("Max DD %", DefaultValue = 10.0, MinValue = 1.0, MaxValue = 50.0)]
        public double MaxDrawdown { get; set; }

        [Parameter("Daily Loss Limit %", DefaultValue = 4.0, MinValue = 0.5, MaxValue = 30.0)]
        public double DailyLossLimitPercent { get; set; }

        [Parameter("Weekly Loss Limit %", DefaultValue = 8.0, MinValue = 1.0, MaxValue = 40.0)]
        public double WeeklyLossLimitPercent { get; set; }

        [Parameter("Monthly Target %", DefaultValue = 12.0, MinValue = 2.0, MaxValue = 60.0)]
        public double MonthlyTargetPercent { get; set; }

        [Parameter("Risk Cut After Monthly Target", DefaultValue = 0.5, MinValue = 0.1, MaxValue = 1.0)]
        public double RiskAfterMonthlyTarget { get; set; }

        [Parameter("Close All On Daily Lock", DefaultValue = false)]
        public bool CloseAllOnDailyLock { get; set; }

        [Parameter("Auto Re-Protect On Start", DefaultValue = true)]
        public bool AutoReprotectOnStart { get; set; }

        [Parameter("Emergency SL ATR Mult", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0)]
        public double EmergencySlAtrMult { get; set; }

        [Parameter("Emergency TP RR", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0)]
        public double EmergencyTpRR { get; set; }

        // ============================================================
        //  2. Session / Filters
        // ============================================================
        [Parameter("Session Start (GMT)", DefaultValue = 8, MinValue = 0, MaxValue = 23)]
        public int SessionStart { get; set; }

        [Parameter("Session End (GMT)", DefaultValue = 22, MinValue = 0, MaxValue = 23)]
        public int SessionEnd { get; set; }

        [Parameter("H1 MTF Trend Filter", DefaultValue = true)]
        public bool MTFEnabled { get; set; }

        [Parameter("H4 Trend Filter", DefaultValue = false)]
        public bool H4FilterEnabled { get; set; }

        [Parameter("Pattern Confidence", DefaultValue = 0.72, MinValue = 0.5, MaxValue = 0.99)]
        public double PatternConfidence { get; set; }

        [Parameter("Max Concurrent Trades", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int MaxConcurrentTrades { get; set; }

        [Parameter("Max Same Direction Trades", DefaultValue = 1, MinValue = 1, MaxValue = 10)]
        public int MaxSameDirectionTrades { get; set; }

        [Parameter("Max Trades / Day", DefaultValue = 4, MinValue = 1, MaxValue = 20)]
        public int MaxTradesPerDay { get; set; }

        [Parameter("Cooldown Minutes", DefaultValue = 10, MinValue = 1, MaxValue = 240)]
        public int CooldownMinutes { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, MinValue = 5, MaxValue = 100)]
        public int AtrPeriod { get; set; }

        [Parameter("SL ATR Mult", DefaultValue = 1.2, MinValue = 0.5, MaxValue = 10.0)]
        public double SlAtrMult { get; set; }

        [Parameter("TP CD Mult", DefaultValue = 1.0, MinValue = 0.2, MaxValue = 3.0)]
        public double TpCdMult { get; set; }

        [Parameter("Min RR", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 10.0)]
        public double MinRR { get; set; }

        [Parameter("Max Spread (pips)", DefaultValue = 35.0, MinValue = 1.0, MaxValue = 300.0)]
        public double MaxSpreadPips { get; set; }

        [Parameter("Min SL (pips)", DefaultValue = 100.0, MinValue = 1.0, MaxValue = 1000.0)]
        public double MinStopLossPips { get; set; }

        [Parameter("Min TP (pips)", DefaultValue = 200.0, MinValue = 1.0, MaxValue = 2000.0)]
        public double MinTakeProfitPips { get; set; }

        [Parameter("Min Stop Distance (pips)", DefaultValue = 15.0, MinValue = 0.0, MaxValue = 500.0)]
        public double MinStopDistancePips { get; set; }

        [Parameter("Min ATR (price)", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 50.0)]
        public double MinAtrPrice { get; set; }

        // ============================================================
        //  3. Swing / Pivot
        // ============================================================
        [Parameter("Swing Depth", DefaultValue = 5, MinValue = 2, MaxValue = 20)]
        public int SwingDepth { get; set; }

        [Parameter("Swing Lookback", DefaultValue = 200, MinValue = 50, MaxValue = 1000)]
        public int SwingLookback { get; set; }

        [Parameter("Pivot Scan Count", DefaultValue = 14, MinValue = 5, MaxValue = 60)]
        public int PivotScanCount { get; set; }

        [Parameter("Min Leg ATR Ratio", DefaultValue = 0.8, MinValue = 0.1, MaxValue = 10.0)]
        public double MinLegAtrRatio { get; set; }

        // ============================================================
        //  4. Pattern Family (12)
        // ============================================================
        [Parameter("Enable Gartley", DefaultValue = true)]
        public bool EnableGartley { get; set; }

        [Parameter("Enable Bat", DefaultValue = true)]
        public bool EnableBat { get; set; }

        [Parameter("Enable Butterfly", DefaultValue = true)]
        public bool EnableButterfly { get; set; }

        [Parameter("Enable Crab", DefaultValue = true)]
        public bool EnableCrab { get; set; }

        [Parameter("Enable Cypher", DefaultValue = true)]
        public bool EnableCypher { get; set; }

        [Parameter("Enable Rat", DefaultValue = true)]
        public bool EnableRat { get; set; }

        [Parameter("Enable Deep Gartley", DefaultValue = true)]
        public bool EnableDeepGartley { get; set; }

        [Parameter("Enable Alt Bat", DefaultValue = false)]
        public bool EnableAltBat { get; set; }

        [Parameter("Enable Deep Crab", DefaultValue = true)]
        public bool EnableDeepCrab { get; set; }

        [Parameter("Enable ABCD", DefaultValue = true)]
        public bool EnableABCD { get; set; }

        [Parameter("Enable Shark", DefaultValue = true)]
        public bool EnableShark { get; set; }

        [Parameter("Enable 5-0", DefaultValue = false)]
        public bool EnableFiveZero { get; set; }

        // ============================================================
        //  5. Pattern Scoring / Precision
        // ============================================================
        [Parameter("Global Min Score", DefaultValue = 0.55, MinValue = 0.3, MaxValue = 0.9)]
        public double GlobalMinScore { get; set; }

        [Parameter("Consensus Bonus", DefaultValue = 1.12, MinValue = 1.0, MaxValue = 1.3)]
        public double ConsensusBonus { get; set; }

        [Parameter("Fib Tolerance", DefaultValue = 0.05, MinValue = 0.01, MaxValue = 0.20)]
        public double FibTolerance { get; set; }

        [Parameter("Max Entry Dev (ATR)", DefaultValue = 0.5, MinValue = 0.1, MaxValue = 2.0)]
        public double MaxEntryDeviationAtr { get; set; }

        [Parameter("Max Trades Per Pattern %", DefaultValue = 50, MinValue = 10, MaxValue = 100)]
        public int MaxTradesPerPatternPercent { get; set; }

        [Parameter("Auto-Disable Lose Patterns", DefaultValue = true)]
        public bool AutoDisableLosing { get; set; }

        [Parameter("Auto-Disable WinRate %", DefaultValue = 50.0, MinValue = 30.0, MaxValue = 70.0)]
        public double AutoDisableWinRate { get; set; }

        // ============================================================
        //  6. Trade Management
        // ============================================================
        [Parameter("SL Update Step (pips)", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 50.0)]
        public double SlUpdateStepPips { get; set; }

        [Parameter("SL Update Cooldown (sec)", DefaultValue = 5, MinValue = 1, MaxValue = 120)]
        public int SlUpdateCooldownSec { get; set; }

        [Parameter("BreakEven Trigger (pips)", DefaultValue = 100.0, MinValue = 5.0, MaxValue = 1000.0)]
        public double BreakEvenTriggerPips { get; set; }

        [Parameter("BreakEven Offset (pips)", DefaultValue = 10.0, MinValue = 0.0, MaxValue = 200.0)]
        public double BreakEvenOffsetPips { get; set; }

        [Parameter("Trailing Trigger (pips)", DefaultValue = 150.0, MinValue = 10.0, MaxValue = 2000.0)]
        public double TrailingTriggerPips { get; set; }

        [Parameter("Trailing Distance (pips)", DefaultValue = 90.0, MinValue = 5.0, MaxValue = 1000.0)]
        public double TrailingDistancePips { get; set; }

        [Parameter("Enable Partial TP", DefaultValue = true)]
        public bool EnablePartialTP { get; set; }

        [Parameter("TP1 at RR", DefaultValue = 1.0, MinValue = 0.3, MaxValue = 10.0)]
        public double Tp1RR { get; set; }

        [Parameter("TP1 Close %", DefaultValue = 60.0, MinValue = 5.0, MaxValue = 95.0)]
        public double Tp1ClosePercent { get; set; }

        [Parameter("Block News Window", DefaultValue = true)]
        public bool BlockNewsWindow { get; set; }

        [Parameter("Blocked Windows GMT", DefaultValue = "12:25-12:45;14:25-14:45")]
        public string BlockedWindowsGMT { get; set; }

        // ============================================================
        //  State
        // ============================================================
        private const string BotLabel = "HarmonyBotPro";

        private Symbol _symbol;
        private Bars _signalBars;

        private double _initialEquity;
        private double _equityPeak;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastProcessedSignalBarTime = DateTime.MinValue;
        private bool _ddClosedFlag;
        private DateTime _lastSpreadPrintTime = DateTime.MinValue;
        private DateTime _lastNewsPrintTime = DateTime.MinValue;
        private string _lastOpenedPattern = "";

        private DateTime _currentDay;
        private double _dayStartEquity;
        private bool _dailyLocked;
        private int _dailyTradeCount;

        private DateTime _currentWeekStart;
        private double _weekStartEquity;
        private bool _weeklyLocked;

        private DateTime _currentMonthStart;
        private double _monthStartEquity;

        private HarmonicPatternDetector _detector;
        private PerformanceTracker _tracker;

        private readonly Dictionary<long, string> _patternByPosition = new Dictionary<long, string>();
        private readonly Dictionary<string, int> _patternDailyCount = new Dictionary<string, int>();
        private readonly Dictionary<string, PatternStat> _ledger = new Dictionary<string, PatternStat>();

        private readonly Dictionary<long, bool> _tp1Done = new Dictionary<long, bool>();
        private readonly Dictionary<long, double> _initialRiskPips = new Dictionary<long, double>();
        private readonly HashSet<long> _partialClosing = new HashSet<long>();
        private readonly Dictionary<long, DateTime> _lastSlModifyTime = new Dictionary<long, DateTime>();
        private readonly Dictionary<long, double> _sumPriceVol = new Dictionary<long, double>();
        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();

        // EMA cache (per-bar)
        private DateTime _emaCacheBar = DateTime.MinValue;
        private double _cacheH1Ema50, _cacheH1Ema200;
        private double _cacheH4Ema50, _cacheH4Ema200;

        // Auto-disable throttle
        private DateTime _lastAutoDisableDate = DateTime.MinValue;

        // ============================================================
        //  Lifecycle
        // ============================================================
        protected override void OnStart()
        {
            try
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
                    Print("[ERROR] No bars for {0}", SymbolName);
                    Stop();
                    return;
                }

                _detector = new HarmonicPatternDetector(
                    SwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,
                    PivotScanCount, MinLegAtrRatio, GlobalMinScore, ConsensusBonus,
                    FibTolerance, MaxEntryDeviationAtr,
                    EnableGartley, EnableBat, EnableButterfly, EnableCrab, EnableCypher,
                    EnableRat, EnableDeepGartley, EnableAltBat, EnableDeepCrab, EnableABCD,
                    EnableShark, EnableFiveZero);

                _tracker = new PerformanceTracker(this);

                _initialEquity = Account.Equity;
                _equityPeak = Account.Equity;
                _tracker.InitialEquity = _initialEquity;

                ResetCalendarStates(true);
                RebuildRuntimeStateFromOpenPositions();

                if (AutoReprotectOnStart)
                    ReProtectExistingPositions();

                Positions.Opened += OnPositionOpened;
                Positions.Closed += OnPositionClosed;

                Print("HarmonyBotPro vAllPatterns-OPT started | {0} | TF={1} | Equity={2:F2}",
                    SymbolName, Bars.TimeFrame, _initialEquity);
            }
            catch (Exception ex)
            {
                Print("[EXCEPTION-OnStart] {0}", ex.Message);
                Stop();
            }
        }

        protected override void OnStop()
        {
            try
            {
                Positions.Opened -= OnPositionOpened;
                Positions.Closed -= OnPositionClosed;

                EnsureServerSideProtectionBeforeStop();

                if (_tracker != null)
                    _tracker.PrintReport(Account.Equity);
                PrintPatternLedger();
            }
            catch (Exception ex)
            {
                Print("[EXCEPTION-OnStop] {0}", ex.Message);
            }
        }

        protected override void OnBar()
        {
            try
            {
                ResetCalendarStates(false);
                UpdateRiskLocks();

                if (IsPeakDrawdownExceeded())
                {
                    if (!_ddClosedFlag)
                    {
                        _ddClosedFlag = true;
                        CloseAllBotPositions("MaxDD");
                        Print("[RISK] Max drawdown guard tripped - trading halted.");
                    }
                    return;
                }

                if (_dailyLocked)
                {
                    if (CloseAllOnDailyLock)
                        CloseAllBotPositions("DailyLock");
                    return;
                }
                if (_weeklyLocked) return;

                if (!IsTradingSession()) return;
                if (!IsSpreadValid()) return;
                if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;

                RefreshEmaCache();

                var open = Positions.FindAll(BotLabel, SymbolName);
                if (open.Length >= MaxConcurrentTrades) return;
                if (_dailyTradeCount >= MaxTradesPerDay) return;
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
                if (atrNow <= 0 || atrNow < MinAtrPrice) return;

                double regimeScore = CalculateRegimeScore(atrNow);
                double buyTrend = CalculateTrendScore(TradeDirection.Buy);
                double sellTrend = CalculateTrendScore(TradeDirection.Sell);

                Signal signal;
                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))
                    return;
                if (signal == null) return;

                // Per-pattern daily budget
                int cap = Math.Min(MaxTradesPerDay, Math.Max(1, (int)Math.Ceiling(MaxTradesPerDay * (MaxTradesPerPatternPercent / 100.0))));
                int used = _patternDailyCount.ContainsKey(signal.PatternName) ? _patternDailyCount[signal.PatternName] : 0;
                if (used >= cap)
                {
                    Print("[BUDGET] {0} daily cap reached.", signal.PatternName);
                    return;
                }

                if (!PassMtfFilter(signal.Direction)) return;
                if (CountOpenPositionsInDirection(signal.Direction, open) >= MaxSameDirectionTrades) return;

                double slPips, tpPips;
                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips)) return;

                double volumeInUnits = CalculateVolumeByRisk(slPips);
                if (volumeInUnits <= 0) return;

                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;

                // Set pattern BEFORE order so the Opened event maps the position correctly.
                _lastOpenedPattern = signal.PatternName;

                var tr = ExecuteMarketOrder(tt, SymbolName, volumeInUnits, BotLabel, slPips, tpPips);

                if (tr != null && tr.IsSuccessful)
                {
                    _lastTradeTime = Server.Time;
                    _dailyTradeCount++;
                    _patternDailyCount[signal.PatternName] = used + 1;

                    // Direct, race-free mapping (event handler remains as fallback).
                    if (tr.Position != null)
                        _patternByPosition[tr.Position.Id] = signal.PatternName;

                    Print("[TRADE] {0} {1} vol={2} sl={3:F1} tp={4:F1} conf={5:F3}",
                        signal.PatternName, tt, volumeInUnits, slPips, tpPips, signal.Confidence);
                }
                else
                {
                    _lastOpenedPattern = "";
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
                ResetCalendarStates(false);
                UpdateRiskLocks();

                // Intra-bar MaxDD guard (bar 之間也保護).
                if (IsPeakDrawdownExceeded())
                {
                    if (!_ddClosedFlag)
                    {
                        _ddClosedFlag = true;
                        CloseAllBotPositions("MaxDD");
                        Print("[RISK] Max drawdown guard tripped (intra-bar) - trading halted.");
                    }
                    return;
                }

                ManageOpenPositions();
            }
            catch (Exception ex)
            {
                Print("[EXCEPTION-OnTick] {0}", ex.Message);
            }
        }

        // ============================================================
        //  Position Events
        // ============================================================
        private void OnPositionOpened(PositionOpenedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;

            if (!_patternByPosition.ContainsKey(p.Id))
                _patternByPosition[p.Id] = _lastOpenedPattern;

            _tp1Done[p.Id] = false;
            _partialClosing.Remove(p.Id);
            _sumPriceVol[p.Id] = 0;
            _totalClosedUnits[p.Id] = 0;

            double rp = p.StopLoss.HasValue
                ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                : EstimateRiskPips(CurrentAtr());

            _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
            _lastSlModifyTime[p.Id] = DateTime.MinValue;
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.Label != BotLabel || p.SymbolName != SymbolName) return;

            double partialVol = _totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0;
            double finalVol = p.VolumeInUnits;
            double totalUnits = partialVol + finalVol;

            double px = p.ClosePrice > 0 ? p.ClosePrice : (p.TradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask);
            double signed = p.TradeType == TradeType.Buy ? (px - p.EntryPrice) : (p.EntryPrice - px);

            double sumPV = (_sumPriceVol.ContainsKey(p.Id) ? _sumPriceVol[p.Id] : 0) + signed * finalVol;
            double avgPips = totalUnits > 0 ? (sumPV / totalUnits) / _symbol.PipSize : 0;
            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;
            double r = avgPips / Math.Max(riskPips, 0.0001);

            if (_tracker != null)
                _tracker.AddTrade(Server.Time, r, sumPV, avgPips);

            string pat = _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "Unknown";
            AddToLedger(pat, r, sumPV);

            _patternByPosition.Remove(p.Id);
            _tp1Done.Remove(p.Id);
            _initialRiskPips.Remove(p.Id);
            _partialClosing.Remove(p.Id);
            _lastSlModifyTime.Remove(p.Id);
            _sumPriceVol.Remove(p.Id);
            _totalClosedUnits.Remove(p.Id);
        }

        // ============================================================
        //  Ledger / Auto-disable
        // ============================================================
        private void AddToLedger(string pattern, double r, double moneyPnl)
        {
            if (!_ledger.ContainsKey(pattern))
                _ledger[pattern] = new PatternStat();

            PatternStat s = _ledger[pattern];
            s.Trades++;
            s.SumR += r;
            s.Pnl += moneyPnl;
            if (moneyPnl >= 0) { s.Wins++; s.SumWinR += r; }
            else { s.Losses++; s.SumLossR += -r; }
        }

        private void PrintPatternLedger()
        {
            Print("");
            Print("================================================================");
            Print("           PATTERN-WISE LEDGER (12 PATTERNS)");
            Print("================================================================");
            Print("  PATTERN        TRADES  WIN%    AVGR    PF      STATUS  DISABLED-REASON");
            Print("  ------------------------------------------------------------");

            foreach (var kv in _ledger)
            {
                PatternStat s = kv.Value;
                double winRate = s.Trades > 0 ? (double)s.Wins / s.Trades * 100.0 : 0;
                double avgR = s.Trades > 0 ? s.SumR / s.Trades : 0;
                double avgWinR = s.Wins > 0 ? s.SumWinR / s.Wins : 0;
                double avgLossR = s.Losses > 0 ? s.SumLossR / s.Losses : 0;
                double pf = avgLossR > 0 ? avgWinR / avgLossR : (avgWinR > 0 ? 99.0 : 0);
                bool disabled = _detector != null && _detector.IsPatternDisabled(kv.Key);
                string reason = _detector != null ? _detector.GetDisableReason(kv.Key) : "";
                Print("  {0,-12} {1,6} {2,7:F1} {3,7:F2} {4,6:F2}  {5,-9} {6}",
                    kv.Key, s.Trades, winRate, avgR, pf, disabled ? "OFF" : "ACTIVE", reason);
            }
            Print("================================================================");
            Print("");
        }

        private void AutoDisableWeakPatterns()
        {
            if (!AutoDisableLosing || _detector == null) return;

            DateTime today = Server.Time.Date;
            if (_lastAutoDisableDate == today) return;
            _lastAutoDisableDate = today;

            foreach (var kv in _ledger)
            {
                PatternStat s = kv.Value;
                if (s.Trades < 30) continue;
                if (_detector.IsPatternDisabled(kv.Key)) continue;

                double winRate = (double)s.Wins / s.Trades * 100.0;
                if (winRate < AutoDisableWinRate)
                {
                    _detector.DisablePattern(kv.Key, string.Format("WR {0:F1}%", winRate));
                    Print("[AUTO-DISABLE] {0} winRate={1:F1}% < {2:F1}% -> disabled.", kv.Key, winRate, AutoDisableWinRate);
                }
            }
        }

        // ============================================================
        //  Trade Management
        // ============================================================
        private void ManageOpenPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);

            foreach (var p in positions)
            {
                EnsureRuntimeState(p);
                double profitPips = p.Pips;

                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);

                if (EnablePartialTP && !_tp1Done[p.Id] && !_partialClosing.Contains(p.Id))
                {
                    double rr = profitPips / Math.Max(_initialRiskPips[p.Id], 0.0001);
                    if (rr >= Tp1RR)
                    {
                        _partialClosing.Add(p.Id);
                        bool ok = TryPartialClose(p);
                        _partialClosing.Remove(p.Id);

                        if (ok)
                        {
                            _tp1Done[p.Id] = true;
                            double be = p.TradeType == TradeType.Buy
                                ? p.EntryPrice + PipsToPrice(beOffsetPips)
                                : p.EntryPrice - PipsToPrice(beOffsetPips);

                            TryModifyStopLoss(p, be);
                        }
                    }
                }

                if (profitPips >= BreakEvenTriggerPips)
                {
                    double be = p.TradeType == TradeType.Buy
                        ? p.EntryPrice + PipsToPrice(beOffsetPips)
                        : p.EntryPrice - PipsToPrice(beOffsetPips);

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
                    double px = p.ClosePrice > 0 ? p.ClosePrice : (p.TradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask);
                    double signed = p.TradeType == TradeType.Buy ? (px - p.EntryPrice) : (p.EntryPrice - px);
                    _sumPriceVol[p.Id] = (_sumPriceVol.ContainsKey(p.Id) ? _sumPriceVol[p.Id] : 0) + signed * closeUnits;
                    _totalClosedUnits[p.Id] = (_totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0) + closeUnits;

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

        private void EnsureRuntimeState(Position p)
        {
            if (!_tp1Done.ContainsKey(p.Id)) _tp1Done[p.Id] = false;
            if (!_patternByPosition.ContainsKey(p.Id)) _patternByPosition[p.Id] = "Unknown";
            if (!_initialRiskPips.ContainsKey(p.Id))
            {
                double rp = p.StopLoss.HasValue
                    ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                    : EstimateRiskPips(CurrentAtr());
                _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
            }
            if (!_sumPriceVol.ContainsKey(p.Id)) _sumPriceVol[p.Id] = 0;
            if (!_totalClosedUnits.ContainsKey(p.Id)) _totalClosedUnits[p.Id] = 0;
            if (!_lastSlModifyTime.ContainsKey(p.Id)) _lastSlModifyTime[p.Id] = DateTime.MinValue;
        }

        // ============================================================
        //  Risk Calendar
        // ============================================================
        private void ResetCalendarStates(bool force)
        {
            DateTime today = Server.Time.Date;

            if (force || today != _currentDay)
            {
                _currentDay = today;
                _dayStartEquity = Account.Equity;
                _dailyLocked = false;
                _dailyTradeCount = 0;
                _patternDailyCount.Clear();
                Print("[DAY RESET] {0:yyyy-MM-dd} StartEquity={1:F2}", _currentDay, _dayStartEquity);
            }

            DateTime weekStart = today.AddDays(-(((int)today.DayOfWeek + 6) % 7));
            if (force || weekStart != _currentWeekStart)
            {
                _currentWeekStart = weekStart;
                _weekStartEquity = Account.Equity;
                _weeklyLocked = false;
                Print("[WEEK RESET] Week of {0:yyyy-MM-dd}", _currentWeekStart);
            }

            DateTime monthStart = new DateTime(today.Year, today.Month, 1);
            if (force || monthStart != _currentMonthStart)
            {
                _currentMonthStart = monthStart;
                _monthStartEquity = Account.Equity;
                Print("[MONTH RESET] {0:yyyy-MM}", _currentMonthStart);
            }
        }

        private void UpdateRiskLocks()
        {
            double eq = Account.Equity;
            if (eq > _equityPeak)
                _equityPeak = eq;

            if (_dayStartEquity > 0 && !_dailyLocked)
            {
                double ddDay = (_dayStartEquity - eq) / _dayStartEquity * 100.0;
                if (ddDay >= DailyLossLimitPercent)
                {
                    _dailyLocked = true;
                    Print("[DAILY LOCK] DD={0:F2}% >= {1:F2}%", ddDay, DailyLossLimitPercent);
                }
            }

            if (_weekStartEquity > 0 && !_weeklyLocked)
            {
                double ddWeek = (_weekStartEquity - eq) / _weekStartEquity * 100.0;
                if (ddWeek >= WeeklyLossLimitPercent)
                {
                    _weeklyLocked = true;
                    Print("[WEEKLY LOCK] DD={0:F2}% >= {1:F2}%", ddWeek, WeeklyLossLimitPercent);
                }
            }

            AutoDisableWeakPatterns();
        }

        private bool IsPeakDrawdownExceeded()
        {
            if (_equityPeak <= 0) return false;
            double dd = (_equityPeak - Account.Equity) / _equityPeak * 100.0;
            return dd >= MaxDrawdown;
        }

        private double GetDynamicRiskFactor()
        {
            double dd = _equityPeak > 0 ? (_equityPeak - Account.Equity) / _equityPeak * 100.0 : 0;

            double ddFactor = 1.0;
            if (dd >= MaxDrawdown) ddFactor = 0.0;
            else if (dd >= MaxDrawdown * 0.7) ddFactor = 0.30;
            else if (dd >= MaxDrawdown * 0.5) ddFactor = 0.50;
            else if (dd >= MaxDrawdown * 0.3) ddFactor = 0.75;
            else if (dd >= MaxDrawdown * 0.15) ddFactor = 0.90;

            double monthFactor = 1.0;
            if (MonthlyTargetPercent > 0 && _monthStartEquity > 0)
            {
                double mr = (Account.Equity - _monthStartEquity) / _monthStartEquity * 100.0;
                if (mr >= MonthlyTargetPercent)
                    monthFactor = Math.Max(0.1, RiskAfterMonthlyTarget);
            }

            double f = Math.Min(ddFactor, monthFactor);
            return Math.Max(0.0, Math.Min(1.0, f));
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

        private double CalculateVolumeByRisk(double slPips)
        {
            if (slPips <= 0 || slPips < MinStopLossPips || _symbol.PipValue <= 0) return 0;

            double riskPct = RiskPercent * GetDynamicRiskFactor();
            if (riskPct <= 0) return 0;

            double riskAmount = Account.Equity * (riskPct / 100.0);
            double raw = riskAmount / (slPips * _symbol.PipValue);

            if (double.IsNaN(raw) || double.IsInfinity(raw) || raw <= 0) return 0;

            double vol = _symbol.NormalizeVolumeInUnits(raw, RoundingMode.Down);
            if (vol < _symbol.VolumeInUnitsMin) return 0;
            if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;

            return vol;
        }

        // ============================================================
        //  Regime / Trend
        // ============================================================
        private void RefreshEmaCache()
        {
            DateTime barTime = _signalBars != null && _signalBars.Count > 0
                ? _signalBars.OpenTimes[_signalBars.Count - 1]
                : DateTime.MinValue;

            if (_emaCacheBar == barTime) return;
            _emaCacheBar = barTime;

            _cacheH1Ema50 = _cacheH1Ema200 = 0;
            _cacheH4Ema50 = _cacheH4Ema200 = 0;

            var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            if (h1 != null && h1.Count >= 220)
            {
                _cacheH1Ema50 = CalculateEma(h1.ClosePrices, 50, h1.Count - 1);
                _cacheH1Ema200 = CalculateEma(h1.ClosePrices, 200, h1.Count - 1);
            }

            var h4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            if (h4 != null && h4.Count >= 220)
            {
                _cacheH4Ema50 = CalculateEma(h4.ClosePrices, 50, h4.Count - 1);
                _cacheH4Ema200 = CalculateEma(h4.ClosePrices, 200, h4.Count - 1);
            }
        }

        private double CalculateRegimeScore(double atrNow)
        {
            // Long-window average true range as volatility baseline (0=chop, 1=trend).
            double baseline = 0;
            int n = Math.Min(_signalBars.Count - 1, 240);
            int start = Math.Max(1, n - 239);
            double sum = 0;
            int cnt = 0;

            for (int i = start; i <= n; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr1 = high - low;
                double tr2 = Math.Abs(high - prevClose);
                double tr3 = Math.Abs(low - prevClose);
                sum += Math.Max(tr1, Math.Max(tr2, tr3));
                cnt++;
            }
            if (cnt > 0) baseline = sum / cnt;

            double regime = 0.5;
            if (baseline > 0 && atrNow > 0)
            {
                double ratio = atrNow / baseline;
                regime = Clamp01((ratio - 0.8) / 0.8);
            }

            if (_cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                double pct = Math.Abs(_cacheH4Ema50 - _cacheH4Ema200) / _cacheH4Ema200;
                double trendStr = Clamp01(pct / 0.03);
                regime = 0.5 * regime + 0.5 * trendStr;
            }

            return regime;
        }

        private double CalculateTrendScore(TradeDirection direction)
        {
            if (!MTFEnabled && !H4FilterEnabled) return 1.0;

            double score = 0.7;
            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)
            {
                bool up = _cacheH1Ema50 > _cacheH1Ema200;
                if ((direction == TradeDirection.Buy && up) || (direction == TradeDirection.Sell && !up))
                    score = 1.0;
            }

            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                bool up4 = _cacheH4Ema50 > _cacheH4Ema200;
                if ((direction == TradeDirection.Buy && up4) || (direction == TradeDirection.Sell && !up4))
                    score = Math.Max(score, 1.0);
            }

            return score;
        }

        private double Clamp01(double v)
        {
            if (v < 0) return 0;
            if (v > 1) return 1;
            return v;
        }

        // ============================================================
        //  Order Geometry / Filters
        // ============================================================
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

            if (tpPips < slPips * MinRR)
                tpPips = slPips * MinRR;

            if (tpPips < MinTakeProfitPips) return false;

            TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;
            if (!HasMinDistanceFromMarket(tt, sl, MinStopDistancePips)) return false;

            return true;
        }

        private bool PassMtfFilter(TradeDirection direction)
        {
            if (!MTFEnabled && !H4FilterEnabled) return true;

            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)
            {
                bool ok = direction == TradeDirection.Buy ? _cacheH1Ema50 > _cacheH1Ema200 : _cacheH1Ema50 < _cacheH1Ema200;
                if (!ok) return false;
            }

            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                bool ok = direction == TradeDirection.Buy ? _cacheH4Ema50 > _cacheH4Ema200 : _cacheH4Ema50 < _cacheH4Ema200;
                if (!ok) return false;
            }

            return true;
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
            double ask = _symbol.Ask;
            double bid = _symbol.Bid;
            if (ask <= 0 || bid <= 0 || ask <= bid) return false; // market closed / bad quote

            double spreadPips = PriceToPips(ask - bid);
            if (spreadPips > MaxSpreadPips)
            {
                if ((Server.Time - _lastSpreadPrintTime).TotalMinutes >= 30)
                {
                    Print("[SKIP] Spread {0:F1} > {1:F1} pips", spreadPips, MaxSpreadPips);
                    _lastSpreadPrintTime = Server.Time;
                }
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
                if (!TimeSpan.TryParseExact(se[0].Trim(), @"h\:mm", CultureInfo.InvariantCulture, out s)) continue;
                if (!TimeSpan.TryParseExact(se[1].Trim(), @"h\:mm", CultureInfo.InvariantCulture, out e)) continue;

                bool inWin = s <= e ? (now >= s && now <= e) : (now >= s || now <= e);
                if (inWin)
                {
                    if ((Server.Time - _lastNewsPrintTime).TotalMinutes >= 5)
                    {
                        Print("[NEWS BLOCK] {0}", w.Trim());
                        _lastNewsPrintTime = Server.Time;
                    }
                    return true;
                }
            }
            return false;
        }

        private int CountOpenPositionsInDirection(TradeDirection direction, Position[] positions)
        {
            int count = 0;
            foreach (var p in positions)
            {
                if (p == null) continue;
                if (direction == TradeDirection.Buy && p.TradeType == TradeType.Buy) count++;
                else if (direction == TradeDirection.Sell && p.TradeType == TradeType.Sell) count++;
            }
            return count;
        }

        // ============================================================
        //  Restore / Protect
        // ============================================================
        private void RebuildRuntimeStateFromOpenPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            double atrNow = CurrentAtr();

            foreach (var p in positions)
            {
                if (!_tp1Done.ContainsKey(p.Id)) _tp1Done[p.Id] = false;
                if (!_patternByPosition.ContainsKey(p.Id)) _patternByPosition[p.Id] = "Unknown";

                if (!_initialRiskPips.ContainsKey(p.Id))
                {
                    double rp = p.StopLoss.HasValue
                        ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                        : EstimateRiskPips(atrNow);
                    _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
                }

                if (!_sumPriceVol.ContainsKey(p.Id)) _sumPriceVol[p.Id] = 0;
                if (!_totalClosedUnits.ContainsKey(p.Id)) _totalClosedUnits[p.Id] = 0;
                if (!_lastSlModifyTime.ContainsKey(p.Id)) _lastSlModifyTime[p.Id] = DateTime.MinValue;
            }
        }

        private void ReProtectExistingPositions()
        {
            var positions = Positions.FindAll(BotLabel, SymbolName);
            if (positions == null || positions.Length == 0) return;

            double atrNow = CurrentAtr();

            foreach (var p in positions)
            {
                if (!_tp1Done.ContainsKey(p.Id))
                    _tp1Done[p.Id] = true;

                if (!_initialRiskPips.ContainsKey(p.Id))
                {
                    double rp = p.StopLoss.HasValue
                        ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                        : EstimateRiskPips(atrNow);
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
            try
            {
                var positions = Positions.FindAll(BotLabel, SymbolName);
                if (positions == null || positions.Length == 0) return;

                double atrNow = CurrentAtr();
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
            catch (Exception ex)
            {
                Print("[STOP-PROTECT EXCEPTION] {0}", ex.Message);
            }
        }

        // ============================================================
        //  Helpers
        // ============================================================
        private double CurrentAtr()
        {
            if (_signalBars == null) return 0;
            int idx = _signalBars.Count - 1;
            if (idx <= AtrPeriod) return 0;
            return CalculateAtr(_signalBars, AtrPeriod, idx);
        }

        private double EstimateRiskPips(double atrNow)
        {
            double est = atrNow > 0 ? PriceToPips(atrNow * SlAtrMult) : MinStopLossPips;
            return Math.Max(est, 0.0001);
        }

        private bool HasMinDistanceFromMarket(TradeType tradeType, double stopPrice, double minDistancePips)
        {
            double dist = PipsToPrice(minDistancePips);
            if (tradeType == TradeType.Buy)
                return (_symbol.Bid - stopPrice) >= dist;
            return (stopPrice - _symbol.Ask) >= dist;
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

        private double CalculateEma(DataSeries series, int period, int endIndex)
        {
            if (series == null || period <= 0 || endIndex <= 0 || endIndex >= series.Count) return 0;

            int start = Math.Max(0, endIndex - period * 6);
            if (start + period - 1 > endIndex) return 0; // not enough bars to seed SMA

            // Seed with SMA(period) for a more accurate EMA.
            double seed = 0;
            for (int i = start; i < start + period; i++)
                seed += series[i];
            double ema = seed / period;

            double k = 2.0 / (period + 1.0);
            for (int i = start + period; i <= endIndex; i++)
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
    }

    // ================================================================
    //  PatternStat
    // ================================================================
    public class PatternStat
    {
        public int Trades;
        public int Wins;
        public int Losses;
        public double SumR;
        public double SumWinR;
        public double SumLossR;
        public double Pnl;
    }

    // ================================================================
    //  Enums
    // ================================================================
    public enum TradeDirection
    {
        Buy,
        Sell
    }

    public enum PatternFamily
    {
        Reversal,   // X-A-B-C-D
        ABCD,       // A-B-C-D
        Shark,      // O-X-A-B-C
        FiveZero    // O-X-A-B-C-D
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

    // ================================================================
    //  HarmonicPatternDetector (12 patterns)
    // ================================================================
    public class HarmonicPatternDetector
    {
        // Precise Fibonacci ratios.
        private const double R_382 = 0.382;
        private const double R_50 = 0.50;
        private const double R_618 = 0.618;
        private const double R_786 = 0.786;
        private const double R_886 = 0.886;
        private const double R_113 = 1.13;
        private const double R_1272 = 1.272;
        private const double R_1414 = 1.414;
        private const double R_1618 = 1.618;
        private const double R_20 = 2.0;
        private const double R_224 = 2.24;
        private const double R_2618 = 2.618;
        private const double R_272 = 2.72;
        private const double R_3618 = 3.618;

        private readonly int _depth;
        private readonly int _lookback;
        private readonly double _minConfidence;
        private readonly double _slAtrMult;
        private readonly double _tpCdMult;
        private readonly int _scanCount;
        private readonly double _minLegAtrRatio;
        private readonly double _globalMinScore;
        private readonly double _consensusBonus;
        private readonly double _fibTolerance;
        private readonly double _maxEntryDeviationAtr;

        private readonly Dictionary<string, bool> _enabled = new Dictionary<string, bool>();
        private readonly Dictionary<string, string> _disabledReason = new Dictionary<string, string>();

        private readonly PatternDef[] _defs;

        public HarmonicPatternDetector(int depth, int lookback, double minConfidence, double slAtrMult, double tpCdMult,
            int scanCount, double minLegAtrRatio, double globalMinScore, double consensusBonus,
            double fibTolerance, double maxEntryDeviationAtr,
            bool gartley, bool bat, bool butterfly, bool crab, bool cypher,
            bool rat, bool deepGartley, bool altBat, bool deepCrab, bool abcd,
            bool shark, bool fiveZero)
        {
            _depth = Math.Max(2, depth);
            _lookback = Math.Max(50, lookback);
            _minConfidence = minConfidence;
            _slAtrMult = slAtrMult;
            _tpCdMult = tpCdMult;
            _scanCount = Math.Max(5, scanCount);
            _minLegAtrRatio = Math.Max(0.1, minLegAtrRatio);
            _globalMinScore = globalMinScore;
            _consensusBonus = Math.Max(1.0, consensusBonus);
            _fibTolerance = Math.Max(0.0, Math.Min(0.5, fibTolerance));
            _maxEntryDeviationAtr = Math.Max(0.0, maxEntryDeviationAtr);

            _enabled["Gartley"] = gartley;
            _enabled["Bat"] = bat;
            _enabled["Butterfly"] = butterfly;
            _enabled["Crab"] = crab;
            _enabled["Cypher"] = cypher;
            _enabled["Rat"] = rat;
            _enabled["Deep Gartley"] = deepGartley;
            _enabled["Alt Bat"] = altBat;
            _enabled["Deep Crab"] = deepCrab;
            _enabled["ABCD"] = abcd;
            _enabled["Shark"] = shark;
            _enabled["5-0"] = fiveZero;

            _defs = GetAllDefs();
        }

        public bool IsPatternDisabled(string name)
        {
            return _disabledReason.ContainsKey(name);
        }

        public string GetDisableReason(string name)
        {
            string r;
            return _disabledReason.TryGetValue(name, out r) ? r : "";
        }

        public void DisablePattern(string name, string reason)
        {
            _disabledReason[name] = reason;
            _enabled[name] = false;
        }

        // ============================================================
        //  Pattern Definition
        // ============================================================
        private class PatternDef
        {
            public string Name;
            public PatternFamily Family;
            public double BMin, BMax, BIdeal;
            public double CMin, CMax, CIdeal;
            public double DMin, DMax, DIdeal;
            public double XDMin, XDMax, XDIdeal;
            public double Threshold;
            public double RegimeChop;
            public double RegimeTrend;
            public double Weight;

            public PatternDef(string name, PatternFamily family,
                double bMin, double bMax, double bIdeal,
                double cMin, double cMax, double cIdeal,
                double dMin, double dMax, double dIdeal,
                double xdMin, double xdMax, double xdIdeal,
                double threshold, double regimeChop, double regimeTrend, double weight)
            {
                Name = name;
                Family = family;
                BMin = bMin; BMax = bMax; BIdeal = bIdeal;
                CMin = cMin; CMax = cMax; CIdeal = cIdeal;
                DMin = dMin; DMax = dMax; DIdeal = dIdeal;
                XDMin = xdMin; XDMax = xdMax; XDIdeal = xdIdeal;
                Threshold = threshold;
                RegimeChop = regimeChop;
                RegimeTrend = regimeTrend;
                Weight = weight;
            }
        }

        private static PatternDef[] GetAllDefs()
        {
            return new PatternDef[]
            {
                new PatternDef("Gartley", PatternFamily.Reversal, 0.55, 0.72, R_618, 0.382, 0.886, R_618, 1.13, R_1618, R_1272, 0.70, 0.90, R_786, 0.70, 0.90, 0.60, 1.0),
                new PatternDef("Bat", PatternFamily.Reversal, 0.35, 0.55, R_50, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, 0.80, 0.95, R_886, 0.70, 0.80, 0.70, 1.0),
                new PatternDef("Butterfly", PatternFamily.Reversal, 0.70, 0.85, R_786, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, 1.20, R_1618, R_1272, 0.68, 0.70, 0.80, 1.0),
                new PatternDef("Crab", PatternFamily.Reversal, 0.35, 0.62, R_618, 0.382, 0.886, R_618, R_224, R_3618, R_2618, R_113, R_1618, R_1618, 0.70, 0.90, 0.50, 0.95),
                new PatternDef("Cypher", PatternFamily.Reversal, R_382, R_618, R_50, R_113, R_1414, R_1272, R_113, R_272, R_20, 0.70, 0.90, R_786, 0.68, 0.70, 0.70, 1.0),
                new PatternDef("Rat", PatternFamily.Reversal, R_382, R_618, R_50, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, R_382, R_618, R_50, 0.66, 0.80, 0.60, 1.0),
                new PatternDef("Deep Gartley", PatternFamily.Reversal, 0.70, 0.85, R_786, 0.382, 0.886, R_618, R_1272, R_1618, R_1272, 0.95, 1.05, 1.0, 0.68, 0.75, 0.75, 1.0),
                new PatternDef("Alt Bat", PatternFamily.Reversal, 0.30, 0.45, R_382, 0.382, 0.886, R_618, R_20, R_3618, R_20, 1.05, 1.25, R_113, 0.72, 0.70, 0.80, 1.0),
                new PatternDef("Deep Crab", PatternFamily.Reversal, 0.85, 0.95, R_886, 0.382, 0.886, R_618, R_20, R_3618, R_2618, 1.55, 1.70, R_1618, 0.70, 0.85, 0.60, 1.0),
                new PatternDef("ABCD", PatternFamily.ABCD, 0.90, 1.15, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.66, 0.60, 0.90, 1.0),
                new PatternDef("Shark", PatternFamily.Shark, R_113, R_1618, R_1272, 0.886, R_113, 1.0, 0, 0, 0, 0, 0, 0, 0.68, 0.30, 1.0, 1.0),
                new PatternDef("5-0", PatternFamily.FiveZero, R_113, R_1618, R_1272, 0.886, R_113, 1.0, 0, 0, 0, 0.45, 0.55, R_50, 0.70, 0.50, 0.90, 1.0)
            };
        }

        // ============================================================
        //  Detection
        // ============================================================
        public bool TryDetect(Bars bars, int currentIndex, double atrNow, Symbol symbol,
            double regimeScore, double buyTrend, double sellTrend, out Signal signal)
        {
            signal = null;
            if (bars == null || symbol == null || currentIndex < _depth * 4 || currentIndex >= bars.Count || atrNow <= 0)
                return false;

            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);
            if (pivots.Count < 5) return false;

            int start = Math.Max(0, pivots.Count - _scanCount);
            PatternDef[] defs = _defs;

            var all = new List<Candidate>();
            for (int i = start; i <= pivots.Count - 5; i++)
            {
                foreach (var def in defs)
                {
                    if (!IsDefEnabled(def)) continue;
                    Candidate c = Match(bars, pivots, i, def, atrNow, regimeScore, buyTrend, sellTrend);
                    if (c != null)
                        all.Add(c);
                }
            }

            // Group by anchor X; reject groups with conflicting buy/sell direction.
            var groups = new Dictionary<int, List<Candidate>>();
            for (int gi = 0; gi < all.Count; gi++)
            {
                Candidate c = all[gi];
                int key = c.X.Index;
                List<Candidate> slot;
                if (!groups.TryGetValue(key, out slot))
                {
                    slot = new List<Candidate>();
                    groups[key] = slot;
                }
                slot.Add(c);
            }

            Candidate best = null;
            double bestScore = -1;

            foreach (var kv in groups)
            {
                List<Candidate> slot = kv.Value;
                bool hasBuy = false, hasSell = false;
                for (int si = 0; si < slot.Count; si++)
                {
                    if (slot[si].IsBullish) hasBuy = true; else hasSell = true;
                }
                if (hasBuy && hasSell) continue;

                Candidate slotBest = null;
                double slotScore = -1;
                for (int si = 0; si < slot.Count; si++)
                {
                    Candidate c = slot[si];
                    double sc = c.Score;
                    if (slot.Count >= 2) sc *= _consensusBonus;
                    if (sc > slotScore) { slotScore = sc; slotBest = c; }
                }
                if (slotBest == null) continue;
                if (slotScore > bestScore) { best = slotBest; bestScore = slotScore; }
            }

            if (best == null) return false;

            double finalScore = Math.Min(1.0, bestScore);
            if (finalScore < best.Threshold) return false;
            if (finalScore < _globalMinScore) return false;

            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;
            double entry = dir == TradeDirection.Buy ? symbol.Ask : symbol.Bid;

            SwingPoint reference;
            if (best.Family == PatternFamily.Shark)
                reference = best.C;
            else
                reference = best.D;

            if (reference == null) return false;

            // Precise entry timing: current price must be near the completion point.
            double deviation = Math.Abs(entry - reference.Price);
            if (deviation > atrNow * _maxEntryDeviationAtr) return false;

            double stop, tp, tpDist;

            if (best.Family == PatternFamily.Shark)
            {
                stop = dir == TradeDirection.Buy ? reference.Price - atrNow * _slAtrMult : reference.Price + atrNow * _slAtrMult;
                double bc = Math.Abs(best.B.Price - best.C.Price);
                tpDist = Math.Max(bc * 0.5, atrNow * 1.2);
            }
            else if (best.Family == PatternFamily.FiveZero)
            {
                stop = dir == TradeDirection.Buy ? reference.Price - atrNow * _slAtrMult : reference.Price + atrNow * _slAtrMult;
                double bc = Math.Abs(best.B.Price - best.C.Price);
                tpDist = Math.Max(bc * 0.5, atrNow * 1.2);
            }
            else
            {
                stop = dir == TradeDirection.Buy ? reference.Price - atrNow * _slAtrMult : reference.Price + atrNow * _slAtrMult;
                double cd = best.C != null ? Math.Abs(best.C.Price - best.D.Price) : atrNow;
                tpDist = Math.Max(cd * _tpCdMult, atrNow * 1.2);
            }

            tp = dir == TradeDirection.Buy ? entry + tpDist : entry - tpDist;

            if (dir == TradeDirection.Buy && !(stop < entry && entry < tp)) return false;
            if (dir == TradeDirection.Sell && !(tp < entry && entry < stop)) return false;

            signal = new Signal
            {
                Direction = dir,
                EntryPrice = entry,
                StopLoss = stop,
                TakeProfit = tp,
                Confidence = finalScore,
                PatternName = best.PatternName
            };
            return true;
        }

        private bool IsDefEnabled(PatternDef def)
        {
            bool enabled;
            if (!_enabled.TryGetValue(def.Name, out enabled)) return false;
            return enabled;
        }

        // ============================================================
        //  Match
        // ============================================================
        private Candidate Match(Bars bars, List<SwingPoint> pivots, int i, PatternDef def,
            double atr, double regime, double buyTrend, double sellTrend)
        {
            bool isShark = def.Family == PatternFamily.Shark;
            bool isFiveZero = def.Family == PatternFamily.FiveZero;
            bool isAbcd = def.Family == PatternFamily.ABCD;

            if ((isShark || isFiveZero) && i < 1) return null;

            SwingPoint o = null, x = null, a, b, c = null, d = null;
            int idx = i;
            if (isShark || isFiveZero)
            {
                o = pivots[idx - 1];
                x = pivots[idx];
                a = pivots[idx + 1];
                b = pivots[idx + 2];
                c = pivots[idx + 3];
                if (isFiveZero && idx + 4 <= pivots.Count - 1)
                    d = pivots[idx + 4];
                else if (isFiveZero)
                    return null;
            }
            else if (isAbcd)
            {
                a = pivots[idx];
                b = pivots[idx + 1];
                c = pivots[idx + 2];
                d = pivots[idx + 3];
            }
            else
            {
                x = pivots[idx];
                a = pivots[idx + 1];
                b = pivots[idx + 2];
                c = pivots[idx + 3];
                d = pivots[idx + 4];
            }

            bool bull, bear;
            double ox = 0, xa = 0, ab = 0, bc = 0, cd = 0;

            if (isShark || isFiveZero)
            {
                bull = (x.Price > o.Price) && (a.Price < x.Price) && (b.Price > a.Price) && (c.Price < b.Price);
                bear = (x.Price < o.Price) && (a.Price > x.Price) && (b.Price < a.Price) && (c.Price > b.Price);
                ox = Math.Abs(x.Price - o.Price);
                xa = Math.Abs(a.Price - x.Price);
                ab = Math.Abs(b.Price - a.Price);
                bc = Math.Abs(c.Price - b.Price);
                if (isFiveZero)
                {
                    if (d == null) return null;
                    cd = Math.Abs(d.Price - c.Price);
                    if (cd < atr * 0.2) return null;
                }
            }
            else if (isAbcd)
            {
                bull = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);
                bear = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);
                ab = Math.Abs(b.Price - a.Price);
                bc = Math.Abs(c.Price - b.Price);
                cd = Math.Abs(d.Price - c.Price);
            }
            else
            {
                bull = (a.Price > x.Price) && (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);
                bear = (a.Price < x.Price) && (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);
                xa = Math.Abs(a.Price - x.Price);
                ab = Math.Abs(b.Price - a.Price);
                bc = Math.Abs(c.Price - b.Price);
                cd = Math.Abs(d.Price - c.Price);
            }

            if (!bull && !bear) return null;

            // Leg size filter (also guards all divisions below).
            if (isShark || isFiveZero)
            {
                if (ox < atr * _minLegAtrRatio || xa < atr * _minLegAtrRatio ||
                    ab < atr * _minLegAtrRatio || bc < atr * _minLegAtrRatio) return null;
            }
            else if (isAbcd)
            {
                if (ab < atr * _minLegAtrRatio || bc < atr * _minLegAtrRatio || cd < atr * _minLegAtrRatio) return null;
            }
            else
            {
                if (xa < atr * _minLegAtrRatio || ab < atr * _minLegAtrRatio ||
                    bc < atr * _minLegAtrRatio || cd < atr * _minLegAtrRatio) return null;
            }

            double geometry;
            double trendScore = bull ? buyTrend : sellTrend;

            if (isShark)
            {
                double rAB = ab / xa;
                double rBC = bc / ox;
                if (!InFibRange(rAB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rBC, def.CIdeal, def.CMin, def.CMax)) return null;
                double s1 = RatioScore(rAB, def.BIdeal);
                double s2 = RatioScore(rBC, def.CIdeal);
                geometry = (s1 + s2) / 2.0;
            }
            else if (isFiveZero)
            {
                double rAB = ab / xa;
                double rBC = bc / ox;
                double rCD = cd / bc;
                if (!InFibRange(rAB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rBC, def.CIdeal, def.CMin, def.CMax)) return null;
                if (!InFibRange(rCD, def.XDIdeal, def.XDMin, def.XDMax)) return null;
                double s1 = RatioScore(rAB, def.BIdeal);
                double s2 = RatioScore(rBC, def.CIdeal);
                double s3 = RatioScore(rCD, def.XDIdeal);
                geometry = (s1 + s2 + s3) / 3.0;
            }
            else if (isAbcd)
            {
                double rCD = cd / ab;
                if (!InFibRange(rCD, def.BIdeal, def.BMin, def.BMax)) return null;
                geometry = RatioScore(rCD, def.BIdeal);
            }
            else
            {
                double xd = Math.Abs(d.Price - x.Price);
                double rAB = ab / xa;
                double rBC = bc / ab;
                double rCD = cd / bc;
                double rXD = xd / xa;

                if (!InFibRange(rAB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rBC, def.CIdeal, def.CMin, def.CMax)) return null;
                if (!InFibRange(rCD, def.DIdeal, def.DMin, def.DMax)) return null;
                if (!InFibRange(rXD, def.XDIdeal, def.XDMin, def.XDMax)) return null;

                double s1 = RatioScore(rAB, def.BIdeal);
                double s2 = RatioScore(rBC, def.CIdeal);
                double s3 = RatioScore(rCD, def.DIdeal);
                double s4 = RatioScore(rXD, def.XDIdeal);
                geometry = (s1 + s2 + s3 + s4) / 4.0;
            }

            double regimeFit = def.RegimeChop * (1.0 - regime) + def.RegimeTrend * regime;

            // Confirmation: latest close must be on the correct side of the
            // completion point (D, or C for Shark), i.e. reversal is in motion.
            bool confirmed = false;
            int confirmIdx = (isShark ? c.Index : d.Index);
            double confirmLevel = (isShark ? c.Price : d.Price);
            int lastIdx = bars.Count - 1;
            if (confirmIdx >= 0 && lastIdx > confirmIdx)
            {
                double lastClose = bars.ClosePrices[lastIdx];
                confirmed = bull ? (lastClose > confirmLevel) : (lastClose < confirmLevel);
            }

            double score = geometry * 0.60 + regimeFit * 0.15 + trendScore * 0.15 + (confirmed ? 0.10 : 0.0);
            if (score > 1) score = 1;
            score *= def.Weight;

            if (score < def.Threshold) return null;
            if (score < _globalMinScore) return null;

            // Time symmetry.
            int tXA = 1, tAB = 1, tBC = 1, tCD = 1;
            if (isShark || isFiveZero)
            {
                tXA = Math.Max(1, x.Index - o.Index);
                tAB = Math.Max(1, a.Index - x.Index);
                tBC = Math.Max(1, b.Index - a.Index);
            }
            else if (isAbcd)
            {
                tAB = Math.Max(1, b.Index - a.Index);
                tBC = Math.Max(1, c.Index - b.Index);
                tCD = Math.Max(1, d.Index - c.Index);
            }
            else
            {
                tXA = Math.Max(1, a.Index - x.Index);
                tAB = Math.Max(1, b.Index - a.Index);
                tBC = Math.Max(1, c.Index - b.Index);
                tCD = Math.Max(1, d.Index - c.Index);
            }

            double ts;
            if (isShark || isFiveZero)
                ts = (SymmetryScore(tXA, tAB) + SymmetryScore(tAB, tBC)) / 2.0;
            else if (isAbcd)
                ts = (SymmetryScore(tAB, tBC) + SymmetryScore(tBC, tCD)) / 2.0;
            else
                ts = (SymmetryScore(tXA, tAB) + SymmetryScore(tAB, tBC) + SymmetryScore(tBC, tCD)) / 3.0;

            score = score * 0.9 + ts * 0.1;
            if (score < Math.Max(def.Threshold, _minConfidence)) return null;
            if (score < _globalMinScore) return null;

            return new Candidate
            {
                X = isShark || isFiveZero ? x : (isAbcd ? a : x),
                A = a,
                B = b,
                C = c,
                D = d,
                IsBullish = bull,
                Score = score,
                PatternName = def.Name,
                Family = def.Family,
                Threshold = Math.Max(def.Threshold, _minConfidence),
                Weight = def.Weight
            };
        }

        // ============================================================
        //  Swing Points
        // ============================================================
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

            pivots.Sort((p1, p2) => p1.Index.CompareTo(p2.Index));
            if (pivots.Count == 0) return pivots;

            // Compress consecutive same-direction pivots, keeping the extreme.
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

        // ============================================================
        //  Math helpers
        // ============================================================
        private bool InFibRange(double value, double ideal, double min, double max)
        {
            if (ideal > 0)
            {
                double lo = Math.Max(min, ideal - _fibTolerance);
                double hi = Math.Min(max, ideal + _fibTolerance);
                return value >= lo && value <= hi;
            }
            return value >= min && value <= max;
        }

        private bool InRange(double v, double min, double max)
        {
            return v >= min && v <= max;
        }

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
            // min/max ratio: 1.0 when legs are equal in length, approaches 0 when imbalanced.
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
            public string PatternName;
            public PatternFamily Family;
            public double Threshold;
            public double Weight;
        }
    }

    // ================================================================
    //  PerformanceTracker
    // ================================================================
    public class PerformanceTracker
    {
        private readonly Robot _robot;
        private readonly List<double> _rs = new List<double>();
        private readonly List<double> _money = new List<double>();
        private readonly List<double> _pips = new List<double>();
        private readonly Dictionary<string, double> _monthPnl = new Dictionary<string, double>();

        public double InitialEquity;

        public PerformanceTracker(Robot robot)
        {
            _robot = robot;
        }

        public void AddTrade(DateTime when, double r, double moneyPnl, double avgPips)
        {
            _rs.Add(r);
            _money.Add(moneyPnl);
            _pips.Add(avgPips);

            string key = when.ToString("yyyy-MM");
            double existing;
            if (!_monthPnl.TryGetValue(key, out existing)) existing = 0;
            _monthPnl[key] = existing + moneyPnl;
        }

        public void PrintReport(double finalEquity)
        {
            int total = _rs.Count;
            int wins = 0, losses = 0;
            double grossWin = 0, grossLoss = 0;
            double sumWinR = 0, sumLossR = 0;
            double totalPips = 0;

            // Equity-curve drawdown (InitialEquity + cumulative PnL).
            double equity = InitialEquity;
            double peakEq = equity;
            double maxDd = 0;

            for (int i = 0; i < total; i++)
            {
                double money = _money[i];
                double r = _rs[i];

                equity += money;
                if (equity > peakEq) peakEq = equity;
                double dd = peakEq > 0 ? (peakEq - equity) / peakEq * 100.0 : 0;
                if (dd > maxDd) maxDd = dd;

                if (money >= 0) { wins++; grossWin += money; sumWinR += r; }
                else { losses++; grossLoss += -money; sumLossR += -r; }

                totalPips += _pips[i];
            }

            double winRate = total > 0 ? (double)wins / total * 100.0 : 0;
            double pf = grossLoss > 0 ? grossWin / grossLoss : (grossWin > 0 ? 99.0 : 0);
            double avgWinR = wins > 0 ? sumWinR / wins : 0;
            double avgLossR = losses > 0 ? sumLossR / losses : 0;
            double realizedRR = avgLossR > 0 ? avgWinR / avgLossR : 0;
            double totalReturn = InitialEquity > 0 ? (finalEquity - InitialEquity) / InitialEquity * 100.0 : 0;
            double netProfit = finalEquity - InitialEquity;
            double avgR = total > 0 ? _rs.Average() : 0;
            double avgPips = total > 0 ? totalPips / total : 0;

            int profitableMonths = 0;
            foreach (var kv in _monthPnl)
                if (kv.Value > 0) profitableMonths++;

            _robot.Print("");
            _robot.Print("========================================================================");
            _robot.Print("           HARMONY BOT PRO - PERFORMANCE REPORT");
            _robot.Print("========================================================================");
            _robot.Print("  Initial Equity:     {0:F2}", InitialEquity);
            _robot.Print("  Final Equity:       {0:F2}", finalEquity);
            _robot.Print("  Net Profit:         {0:F2}    (Target >= {1:F2})", netProfit, InitialEquity);
            _robot.Print("  Total Return %:     {0:F2}    (Target >= 100)", totalReturn);
            _robot.Print("  Profit Factor:      {0:F3}    (Target >= 2.50)", pf);
            _robot.Print("  Max Drawdown %:     {0:F2}    (Target <= 10)", maxDd);
            _robot.Print("  Win Rate %:         {0:F2}    (Target >= 65)", winRate);
            _robot.Print("  Total Trades:       {0}       (Target >= 200)", total);
            _robot.Print("  Avg R / trade:      {0:F3}", avgR);
            _robot.Print("  Avg Pips / trade:   {0:F1}", avgPips);
            _robot.Print("  Realized Avg RR:    {0:F3}    (Target >= 2.0)", realizedRR);
            _robot.Print("  Profitable Months:  {0}/{1}   (Target >= 10/12)", profitableMonths, _monthPnl.Count);
            _robot.Print("========================================================================");
            _robot.Print("");
        }
    }
}
