using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;
using cAlgo.API.Requests;

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

        [Parameter("Max Consecutive Losses", DefaultValue = 3, MinValue = 0, MaxValue = 20)]
        public int MaxConsecutiveLosses { get; set; }

        [Parameter("Consecutive Loss Cooldown Min", DefaultValue = 60, MinValue = 0, MaxValue = 1440)]
        public int ConsecutiveLossCooldownMin { get; set; }

        [Parameter("Margin Buffer %", DefaultValue = 20.0, MinValue = 0.0, MaxValue = 90.0)]
        public double MarginBufferPercent { get; set; }

        // --- Small account ($100) support ---------------------------------
        [Parameter("Small Account Mode", DefaultValue = true)]
        public bool SmallAccountMode { get; set; }

        [Parameter("Small Account Threshold USD", DefaultValue = 100.0, MinValue = 10.0, MaxValue = 5000.0)]
        public double SmallAccountThreshold { get; set; }

        [Parameter("Micro Min SL (pips)", DefaultValue = 25.0, MinValue = 5.0, MaxValue = 1000.0)]
        public double SmallAccountMinSLPips { get; set; }

        [Parameter("Micro Min TP (pips)", DefaultValue = 50.0, MinValue = 10.0, MaxValue = 2000.0)]
        public double SmallAccountMinTPPips { get; set; }

        [Parameter("Allow Min Volume Fallback", DefaultValue = true)]
        public bool AllowMinVolumeFallback { get; set; }

        [Parameter("Min Volume Risk Cap %", DefaultValue = 5.0, MinValue = 0.5, MaxValue = 20.0)]
        public double MinVolumeRiskCapPercent { get; set; }

        [Parameter("Micro Min Volume Risk Cap %", DefaultValue = 10.0, MinValue = 0.5, MaxValue = 30.0)]
        public double MicroMinVolumeRiskCapPercent { get; set; }

        [Parameter("Max Notional / Equity", DefaultValue = 500.0, MinValue = 10.0, MaxValue = 500.0)]
        public double MaxNotionalToEquityRatio { get; set; }

        // ============================================================
        //  2. Session / Filters
        // ============================================================
        [Parameter("Session Start (GMT)", DefaultValue = 8, MinValue = 0, MaxValue = 23)]
        public int SessionStart { get; set; }

        [Parameter("Session End (GMT)", DefaultValue = 22, MinValue = 0, MaxValue = 23)]
        public int SessionEnd { get; set; }

        [Parameter("DST-Aware London-NY Session", DefaultValue = true)]
        public bool DstAwareInstitutionalSession { get; set; }

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

        [Parameter("Anti-Hedge (Block Opposite)", DefaultValue = true)]
        public bool AntiHedge { get; set; }

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

        [Parameter("Use Cost-Adjusted RR", DefaultValue = true)]
        public bool UseCostAdjustedRR { get; set; }

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

        [Parameter("Max Slippage (pips)", DefaultValue = 30.0, MinValue = 0.0, MaxValue = 300.0)]
        public double MaxSlippagePips { get; set; }

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

        [Parameter("Adaptive Frequency Recovery", DefaultValue = true)]
        public bool AdaptiveFrequencyRecovery { get; set; }

        [Parameter("Soft MTF Reversal Gate", DefaultValue = true)]
        public bool SoftMtfReversalGate { get; set; }

        [Parameter("Countertrend Confidence Buffer", DefaultValue = 0.06, MinValue = 0.0, MaxValue = 0.20)]
        public double CounterTrendConfidenceBuffer { get; set; }

        [Parameter("Adaptive Entry Dev Floor (ATR)", DefaultValue = 0.85, MinValue = 0.5, MaxValue = 2.0)]
        public double AdaptiveEntryDeviationFloor { get; set; }

        [Parameter("Closed-Bar Provisional D", DefaultValue = true)]
        public bool ClosedBarProvisionalD { get; set; }

        [Parameter("Provisional D Min Move (ATR)", DefaultValue = 0.30, MinValue = 0.10, MaxValue = 1.00)]
        public double ProvisionalDMinMoveAtr { get; set; }

        [Parameter("Small Account Grid Guard", DefaultValue = true)]
        public bool SmallAccountGridGuard { get; set; }

        [Parameter("Commercial Risk Engine", DefaultValue = true)]
        public bool CommercialRiskEngine { get; set; }

        [Parameter("Projected Risk Guard", DefaultValue = true)]
        public bool ProjectedRiskGuard { get; set; }

        [Parameter("Risk Headroom %", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 2.0)]
        public double RiskHeadroomPercent { get; set; }

        [Parameter("Compress SL To Risk Budget", DefaultValue = true)]
        public bool CompressStopToRiskBudget { get; set; }

        [Parameter("Max SL Compression Ratio", DefaultValue = 0.90, MinValue = 0.0, MaxValue = 1.0)]
        public double MaxStopCompressionRatio { get; set; }

        [Parameter("Disable Partial TP At Min Volume", DefaultValue = true)]
        public bool DisablePartialAtMinVolume { get; set; }

        [Parameter("Adaptive Min ATR Factor", DefaultValue = 0.70, MinValue = 0.40, MaxValue = 1.00)]
        public double AdaptiveMinAtrFactor { get; set; }

        [Parameter("Commercial Swing Depth Reduction", DefaultValue = 1, MinValue = 0, MaxValue = 2)]
        public int CommercialSwingDepthReduction { get; set; }

        [Parameter("Commercial Pivot Scan Min", DefaultValue = 20, MinValue = 10, MaxValue = 60)]
        public int CommercialPivotScanMin { get; set; }

        [Parameter("Candidate Max Age Bars", DefaultValue = 48, MinValue = 4, MaxValue = 192)]
        public int CandidateMaxAgeBars { get; set; }

        [Parameter("Direction Dominance Margin", DefaultValue = 0.04, MinValue = 0.0, MaxValue = 0.20)]
        public double DirectionDominanceMargin { get; set; }

        [Parameter("Fib Range Boundary Score", DefaultValue = 0.60, MinValue = 0.30, MaxValue = 0.90)]
        public double FibRangeBoundaryScore { get; set; }

        [Parameter("Reversal Trend Score Floor", DefaultValue = 0.45, MinValue = 0.0, MaxValue = 0.80)]
        public double ReversalTrendScoreFloor { get; set; }

        [Parameter("Commission / $1M / side", DefaultValue = 35.0, MinValue = 0.0, MaxValue = 200.0)]
        public double CommissionPerMillionPerSide { get; set; }

        [Parameter("Signal Dedupe Bars", DefaultValue = 96, MinValue = 16, MaxValue = 384)]
        public int SignalDedupeBars { get; set; }

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
        //  7. Fibonacci Grid Engine — Golden-Ratio Higher-Math Core
        // ============================================================
        [Parameter("Enable Fibonacci Grid", DefaultValue = false)]
        public bool EnableFibGrid { get; set; }

        [Parameter("Grid Max Levels", DefaultValue = 5, MinValue = 1, MaxValue = 8)]
        public int GridMaxLevels { get; set; }

        [Parameter("Grid Level Fibs (manual override)", DefaultValue = "0.382,0.618,0.786,1.0,1.272,1.618,2.618,4.236")]
        public string GridLevelFibs { get; set; }

        [Parameter("Grid Size Fibs (manual override)", DefaultValue = "1,1,2,3,5,8,13,21")]
        public string GridSizeFibs { get; set; }

        [Parameter("Grid Profit Fib", DefaultValue = 0.618, MinValue = 0.236, MaxValue = 1.618)]
        public double GridProfitFib { get; set; }

        [Parameter("Grid Stop Fib", DefaultValue = 2.618, MinValue = 1.618, MaxValue = 6.854)]
        public double GridStopFib { get; set; }

        [Parameter("Grid Max Total Risk %", DefaultValue = 10.0, MinValue = 1.0, MaxValue = 50.0)]
        public double GridMaxTotalRiskPercent { get; set; }

        [Parameter("Grid Cooldown Min (base)", DefaultValue = 15, MinValue = 0, MaxValue = 240)]
        public int GridCooldownMinutes { get; set; }

        [Parameter("Grid Min Step (pips)", DefaultValue = 20.0, MinValue = 5.0, MaxValue = 500.0)]
        public double GridMinStepPips { get; set; }

        [Parameter("Grid Only With Trend", DefaultValue = true)]
        public bool GridOnlyWithTrend { get; set; }

        // --- Golden Math / Profit Maximization -----------------------
        [Parameter("Use Golden Math Core", DefaultValue = true)]
        public bool GridUseGoldenMath { get; set; }

        [Parameter("Golden Risk Convergence", DefaultValue = true)]
        public bool GridGoldenRiskConvergence { get; set; }

        [Parameter("Golden Trail Compression", DefaultValue = true)]
        public bool GridGoldenTrailCompression { get; set; }

        [Parameter("Grid Breakeven Trigger R", DefaultValue = 0.25, MinValue = 0.1, MaxValue = 2.0)]
        public double GridBreakevenTriggerR { get; set; }

        [Parameter("Grid Breakeven Lock Pips", DefaultValue = 5.0, MinValue = 1.0, MaxValue = 100.0)]
        public double GridBreakevenLockPips { get; set; }

        [Parameter("Grid Trail Trigger R", DefaultValue = 0.5, MinValue = 0.2, MaxValue = 3.0)]
        public double GridTrailTriggerR { get; set; }

        [Parameter("Grid Trail Distance Fib", DefaultValue = 0.382, MinValue = 0.1, MaxValue = 1.5)]
        public double GridTrailDistanceFib { get; set; }

        [Parameter("Grid Scale-out Enabled", DefaultValue = true)]
        public bool GridScaleOutEnabled { get; set; }

        [Parameter("Grid Scale-out R", DefaultValue = 0.618, MinValue = 0.2, MaxValue = 2.0)]
        public double GridScaleOutR { get; set; }

        [Parameter("Grid Scale-out %", DefaultValue = 38.2, MinValue = 10.0, MaxValue = 70.0)]
        public double GridScaleOutPercent { get; set; }

        [Parameter("Grid Max Adds / Day", DefaultValue = 6, MinValue = 1, MaxValue = 20)]
        public int GridMaxAddsPerDay { get; set; }

        [Parameter("Grid Volatility Adapt", DefaultValue = true)]
        public bool GridVolatilityAdapt { get; set; }

        [Parameter("Grid Drawdown Scale Risk", DefaultValue = true)]
        public bool GridDrawdownScaleRisk { get; set; }

        // ============================================================
        //  State
        // ============================================================
        private const string BotLabel = "HarmonyBotPro";
        private const string GridLabel = "HarmonyBotPro-G";

        private Symbol _symbol;
        private Bars _signalBars;

        private double _initialEquity;
        private double _equityPeak;
        private DateTime _lastTradeTime = DateTime.MinValue;
        private DateTime _lastProcessedSignalBarTime = DateTime.MinValue;
        private bool _ddClosedFlag;
        private bool _pendingPrimaryUseGrid;
        private long _diagSignalsDetected;
        private long _diagRiskCompressed;
        private long _diagRiskBlocked;
        private long _diagOrdersOpened;
        private long _diagPartialSkipped;
        private long _diagAtrBlocked;
        private long _diagBudgetBlocked;
        private long _diagMtfBlocked;
        private long _diagGeometryBlocked;
        private long _diagVolumeBlocked;
        private long _diagDuplicateBlocked;
        private long _diagCapitalInfeasible;
        private readonly Dictionary<string, int> _executedSignalBars = new Dictionary<string, int>();
        private DateTime _lastSpreadPrintTime = DateTime.MinValue;
        private DateTime _lastNewsPrintTime = DateTime.MinValue;
        private DateTime _lastVolumeWarnTime = DateTime.MinValue;
        private DateTime _lastNotionalWarnTime = DateTime.MinValue;
        private DateTime _lastMarginWarnTime = DateTime.MinValue;
        private DateTime _lastConsecutiveLossPrint = DateTime.MinValue;
        private DateTime _lastGridPrint = DateTime.MinValue;
        private DateTime _lastEquityWarnTime = DateTime.MinValue;
        private string _lastOpenedPattern = "";
        private double _lastPrimaryRiskPips = 0;

        private int _consecutiveLosses = 0;
        private DateTime _lastLossTime = DateTime.MinValue;

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
        private readonly Dictionary<long, double> _initialVolumeUnits = new Dictionary<long, double>();
        private readonly HashSet<long> _partialClosing = new HashSet<long>();
        private readonly Dictionary<long, DateTime> _lastSlModifyTime = new Dictionary<long, DateTime>();
        private readonly Dictionary<long, double> _sumPriceVol = new Dictionary<long, double>();
        private readonly Dictionary<long, double> _totalClosedUnits = new Dictionary<long, double>();

        // Fibonacci grid state
        private readonly Dictionary<long, GridBasket> _gridBaskets = new Dictionary<long, GridBasket>();
        private readonly Dictionary<long, long> _positionToBasket = new Dictionary<long, long>();
        private readonly HashSet<long> _basketsClosing = new HashSet<long>();
        private long _pendingGridBasketId = 0;
        private int _pendingGridLevel = 0;
        private double[] _gridLevelFibs;
        private double[] _gridSizeFibs;

        // EMA cache (per completed bar)
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
            EnableFibGrid = false; // v28 Commercial Final RC forbids Grid/DCA/Recovery
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

                double effectiveMinLegAtrRatio = AdaptiveFrequencyRecovery ? Math.Min(MinLegAtrRatio, 0.70) : MinLegAtrRatio;
                double effectiveFibTolerance = AdaptiveFrequencyRecovery ? Math.Min(0.20, FibTolerance + 0.015) : FibTolerance;
                double effectiveEntryDeviationAtr = AdaptiveFrequencyRecovery ? Math.Max(MaxEntryDeviationAtr, AdaptiveEntryDeviationFloor) : MaxEntryDeviationAtr;
                int effectiveSwingDepth = AdaptiveFrequencyRecovery ? Math.Max(3, SwingDepth - Math.Max(0, CommercialSwingDepthReduction)) : SwingDepth;
                int effectivePivotScan = AdaptiveFrequencyRecovery ? Math.Max(PivotScanCount, CommercialPivotScanMin) : PivotScanCount;

                _detector = new HarmonicPatternDetector(
                    effectiveSwingDepth, SwingLookback, PatternConfidence, SlAtrMult, TpCdMult,
                    effectivePivotScan, effectiveMinLegAtrRatio, GlobalMinScore, ConsensusBonus,
                    effectiveFibTolerance, effectiveEntryDeviationAtr,
                    ClosedBarProvisionalD && AdaptiveFrequencyRecovery, ProvisionalDMinMoveAtr,
                    CandidateMaxAgeBars, DirectionDominanceMargin, FibRangeBoundaryScore, ReversalTrendScoreFloor,
                    EnableGartley, EnableBat, EnableButterfly, EnableCrab, EnableCypher,
                    EnableRat, EnableDeepGartley, EnableAltBat, EnableDeepCrab, EnableABCD,
                    EnableShark, EnableFiveZero);

                _tracker = new PerformanceTracker(this);

                _initialEquity = Account.Equity;
                _equityPeak = Account.Equity;
                _tracker.InitialEquity = _initialEquity;

                // --- Fibonacci grid init ---
                _gridLevelFibs = FibonacciGridEngine.DefaultLevelFibs;
                _gridSizeFibs = FibonacciGridEngine.DefaultSizeFibs;
                double[] lv, sz;
                if (FibonacciGridEngine.TryParseFibList(GridLevelFibs, out lv))
                    _gridLevelFibs = FibonacciGridEngine.EnsureLength(lv, Math.Max(1, GridMaxLevels), false);
                if (FibonacciGridEngine.TryParseFibList(GridSizeFibs, out sz))
                    _gridSizeFibs = FibonacciGridEngine.EnsureLength(sz, Math.Max(1, GridMaxLevels), true);

                if (EnableFibGrid)
                {
                    var ladder = new List<string>();
                    for (int lvl = 1; lvl <= GridMaxLevels; lvl++)
                    {
                        double ratio = GridUseGoldenMath
                            ? FibonacciMathCore.GoldenLevelRatio(lvl)
                            : (lvl - 1 < _gridLevelFibs.Length ? _gridLevelFibs[lvl - 1] : FibonacciMathCore.GoldenLevelRatio(lvl));
                        double size = GridUseGoldenMath
                            ? FibonacciMathCore.GoldenSizeMultiplier(lvl)
                            : (lvl - 1 < _gridSizeFibs.Length ? _gridSizeFibs[lvl - 1] : FibonacciMathCore.GoldenSizeMultiplier(lvl));
                        ladder.Add(string.Format(CultureInfo.InvariantCulture, "L{0}(d={1:F3},s={2:F2})", lvl, ratio, size));
                    }
                    double capPreview = GridGoldenRiskConvergence
                        ? FibonacciMathCore.GoldenRiskBudgetCumulative(GridMaxLevels, GridMaxTotalRiskPercent)
                        : GridMaxTotalRiskPercent;

                    Print("[GRID] Fibonacci Grid ENABLED | GoldenMath={0} RiskConverge={1} TrailCompress={2}",
                        GridUseGoldenMath, GridGoldenRiskConvergence, GridGoldenTrailCompression);
                    Print("[GRID] Ladder: {0} | cumRisk@MaxLevel={1:F2}%", string.Join(" ", ladder), capPreview);
                }

                ResetCalendarStates(true);
                RebuildRuntimeStateFromOpenPositions();
                RebuildGridBasketsFromOpenPositions();

                if (AutoReprotectOnStart)
                    ReProtectExistingPositions();

                Positions.Opened += OnPositionOpened;
                Positions.Closed += OnPositionClosed;

                Print("HarmonyBotPro v1.5.1-$100 | {0} TF={1} Equity={2:F2} | Micro={3} AntiHedge={4} Risk={5:F1}% | DailyLock={6:F1}% ConsecLossLimit={7} | FibGrid={8}",
                    SymbolName, Bars.TimeFrame, _initialEquity, IsSmallAccountMode(), AntiHedge, RiskPercent, DailyLossLimitPercent, MaxConsecutiveLosses, EnableFibGrid);
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
                PrintGridReport();
                Print("[COMMERCIAL-DIAG] signals={0} orders={1} compressed={2} riskBlocked={3} partialSkipped={4} atrBlocked={5} budgetBlocked={6} mtfBlocked={7} geometryBlocked={8} volumeBlocked={9} duplicateBlocked={10} capitalInfeasible={11}",
                    _diagSignalsDetected, _diagOrdersOpened, _diagRiskCompressed, _diagRiskBlocked, _diagPartialSkipped,
                    _diagAtrBlocked, _diagBudgetBlocked, _diagMtfBlocked, _diagGeometryBlocked, _diagVolumeBlocked, _diagDuplicateBlocked, _diagCapitalInfeasible);
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
                PruneStateDictionaries();
                UpdateRiskLocks();

                if (IsEquityUnsafe()) return;

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

                if (MaxConsecutiveLosses > 0 && ConsecutiveLossCooldownMin > 0 && _consecutiveLosses >= MaxConsecutiveLosses)
                {
                    double sinceLastLoss = (Server.Time - _lastLossTime).TotalMinutes;
                    if (sinceLastLoss < ConsecutiveLossCooldownMin)
                    {
                        if ((Server.Time - _lastConsecutiveLossPrint).TotalMinutes >= 30)
                        {
                            Print("[GUARD] {0} consecutive losses - cooling down ({1:F0} min left).",
                                _consecutiveLosses, Math.Max(0, ConsecutiveLossCooldownMin - sinceLastLoss));
                            _lastConsecutiveLossPrint = Server.Time;
                        }
                        return;
                    }
                    _consecutiveLosses = 0;
                }

                if (_signalBars == null)
                    _signalBars = MarketData.GetBars(Bars.TimeFrame, SymbolName);

                if (_signalBars == null || _signalBars.Count < Math.Max(100, SwingLookback))
                    return;
                if (_signalBars.Count < 2)
                    return;

                int signalIndex = _signalBars.Count - 2;

                DateTime barTime = _signalBars.OpenTimes[signalIndex];
                if (barTime <= _lastProcessedSignalBarTime) return;
                _lastProcessedSignalBarTime = barTime;

                double atrNow = CalculateAtr(_signalBars, AtrPeriod, signalIndex);
                double effectiveMinAtr = AdaptiveFrequencyRecovery
                    ? Math.Max(0.1, MinAtrPrice * Math.Max(0.40, Math.Min(1.0, AdaptiveMinAtrFactor)))
                    : MinAtrPrice;
                if (atrNow <= 0 || atrNow < effectiveMinAtr)
                {
                    _diagAtrBlocked++;
                    return;
                }

                double regimeScore = CalculateRegimeScore(atrNow);
                double buyTrend = CalculateTrendScore(TradeDirection.Buy);
                double sellTrend = CalculateTrendScore(TradeDirection.Sell);

                Signal signal;
                if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))
                    return;
                if (signal == null) return;
                _diagSignalsDetected++;

                PruneExecutedSignalKeys(signalIndex);
                string signalKey = BuildSignalKey(signal);
                int priorSignalBar;
                if (_executedSignalBars.TryGetValue(signalKey, out priorSignalBar) &&
                    signalIndex - priorSignalBar <= Math.Max(16, SignalDedupeBars))
                {
                    _diagDuplicateBlocked++;
                    return;
                }

                int cap = Math.Min(MaxTradesPerDay, Math.Max(1, (int)Math.Ceiling(MaxTradesPerDay * (MaxTradesPerPatternPercent / 100.0))));
                int used = _patternDailyCount.ContainsKey(signal.PatternName) ? _patternDailyCount[signal.PatternName] : 0;
                if (used >= cap)
                {
                    _diagBudgetBlocked++;
                    Print("[BUDGET] {0} daily cap reached.", signal.PatternName);
                    return;
                }

                if (!PassMtfFilter(signal))
                {
                    _diagMtfBlocked++;
                    return;
                }

                if (AntiHedge)
                {
                    TradeDirection opposite = signal.Direction == TradeDirection.Buy ? TradeDirection.Sell : TradeDirection.Buy;
                    var all = GetAllManagedPositions();
                    if (CountOpenPositionsInDirection(opposite, all) > 0)
                    {
                        Print("[ANTI-HEDGE] Opposite {0} position exists - skip {1}.", opposite, signal.Direction);
                        return;
                    }
                }

                if (CountOpenPositionsInDirection(signal.Direction, open) >= MaxSameDirectionTrades) return;

                double slPips, tpPips;
                if (!ValidateOrderGeometryAndReprice(signal, out slPips, out tpPips))
                {
                    _diagGeometryBlocked++;
                    return;
                }

                double riskBudgetPct = GetTradeRiskBudgetPercent();
                if (CommercialRiskEngine && !ApplyCommercialRiskGeometry(ref slPips, ref tpPips, riskBudgetPct))
                {
                    _diagRiskBlocked++;
                    return;
                }

                TradeType tt = signal.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;

                double orderSlPips = slPips;
                double? orderTpPips = tpPips;
                double volumeInUnits;

                bool useGridForThisTrade = false; // v28 commercial: Grid forbidden
                _pendingPrimaryUseGrid = useGridForThisTrade;

                if (useGridForThisTrade)
                {
                    orderSlPips = slPips * GridStopFib;
                    orderTpPips = null;
                    _lastPrimaryRiskPips = slPips;
                    volumeInUnits = CalculateVolumeByRisk(orderSlPips, riskBudgetPct);
                }
                else
                {
                    _lastPrimaryRiskPips = 0;
                    volumeInUnits = CalculateVolumeByRisk(slPips, riskBudgetPct);
                    if (false)
                        Print("[GRID-GUARD] Small account mode: primary trade uses normal SL/TP; grid disabled for this position.");
                }

                if (volumeInUnits <= 0)
                {
                    _diagVolumeBlocked++;
                    _pendingPrimaryUseGrid = false;
                    return;
                }

                _lastOpenedPattern = signal.PatternName;

                // Hardened order with slippage protection & stop trigger method
                var tr = ExecuteRobotMarketOrder(tt, volumeInUnits, orderSlPips, orderTpPips);
                _pendingPrimaryUseGrid = false;

                if (tr != null && tr.IsSuccessful)
                {
                    _lastTradeTime = Server.Time;
                    _dailyTradeCount++;
                    _diagOrdersOpened++;
                    _executedSignalBars[signalKey] = signalIndex;
                    _patternDailyCount[signal.PatternName] = used + 1;

                    if (tr.Position != null)
                        _patternByPosition[tr.Position.Id] = signal.PatternName;

                    Print("[TRADE] {0} {1} vol={2} sl={3:F1} tp={4} conf={5:F3}",
                        signal.PatternName, tt, volumeInUnits, orderSlPips,
                        orderTpPips.HasValue ? orderTpPips.Value.ToString("F1") : "GRID",
                        signal.Confidence);
                }
                else
                {
                    _lastOpenedPattern = "";
                    _lastPrimaryRiskPips = 0;
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

                if (IsEquityUnsafe()) return;

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
                ManageGridBaskets();
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
            if (p == null || p.SymbolName != SymbolName) return;

            if (p.Label == GridLabel)
            {
                long basketId = _pendingGridBasketId;
                int level = _pendingGridLevel;

                _positionToBasket[p.Id] = basketId;
                _patternByPosition[p.Id] = "Grid-L" + level;
                _tp1Done[p.Id] = true;
                _partialClosing.Remove(p.Id);
                _sumPriceVol[p.Id] = 0;
                _totalClosedUnits[p.Id] = 0;
                _initialVolumeUnits[p.Id] = p.VolumeInUnits;

                double rp = p.StopLoss.HasValue
                    ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                    : EstimateRiskPips(CurrentAtr());
                _initialRiskPips[p.Id] = Math.Max(rp, 0.0001);
                _lastSlModifyTime[p.Id] = DateTime.MinValue;

                if (basketId > 0 && _gridBaskets.TryGetValue(basketId, out GridBasket bb))
                {
                    if (!bb.PositionIds.Contains(p.Id)) bb.PositionIds.Add(p.Id);
                    bb.LevelsOpened = Math.Max(bb.LevelsOpened, level);
                }
                return;
            }

            if (p.Label != BotLabel) return;

            if (!_patternByPosition.ContainsKey(p.Id))
                _patternByPosition[p.Id] = _lastOpenedPattern;

            _tp1Done[p.Id] = false;
            _partialClosing.Remove(p.Id);
            _sumPriceVol[p.Id] = 0;
            _totalClosedUnits[p.Id] = 0;
            _initialVolumeUnits[p.Id] = p.VolumeInUnits;

            double rp2 = p.StopLoss.HasValue
                ? PriceToPips(Math.Abs(p.EntryPrice - p.StopLoss.Value))
                : EstimateRiskPips(CurrentAtr());

            _initialRiskPips[p.Id] = Math.Max(rp2, 0.0001);
            _lastSlModifyTime[p.Id] = DateTime.MinValue;

            if (EnableFibGrid && _pendingPrimaryUseGrid)
                CreateBasketFor(p);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            var p = args.Position;
            if (p == null || p.SymbolName != SymbolName) return;

            if (p.Label == GridLabel)
            {
                AccountGridClose(p);
                return;
            }

            if (p.Label != BotLabel) return;

            // [FIX] 用 NetProfit 作為權威損益（平倉後 VolumeInUnits=0，舊算法 = 0）
            double money = p.NetProfit;
            double lifecyclePips = p.Pips;
            double lifecycleVol;
            double historyMoney, historyPips;
            if (TryGetPositionLifecycleFromHistory(p.Id, out historyMoney, out historyPips, out lifecycleVol))
            {
                money = historyMoney;
                lifecyclePips = historyPips;
            }
            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;
            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;
            double r = ComputeR(money, riskPips, initVol, lifecyclePips);

            // [FIX] 虧損判斷改用實損益金額，確保連續虧損保護生效
            if (money < 0)
            {
                _consecutiveLosses++;
                _lastLossTime = Server.Time;
            }
            else
            {
                _consecutiveLosses = 0;
            }

            if (_tracker != null)
                _tracker.AddTrade(Server.Time, r, money, lifecyclePips);

            string pat = _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "Unknown";
            AddToLedger(pat, r, money);

            long basketId = _positionToBasket.ContainsKey(p.Id) ? _positionToBasket[p.Id] : 0;
            _positionToBasket.Remove(p.Id);

            if (basketId > 0 && _gridBaskets.TryGetValue(basketId, out GridBasket b))
            {
                b.PositionIds.Remove(p.Id);

                if (p.Id == b.ParentPositionId)
                {
                    if (!_basketsClosing.Contains(basketId))
                        CloseRemainingBasketPositions(basketId, b, "ParentClosed");
                    _gridBaskets.Remove(basketId);
                }
                else if (b.PositionIds.Count == 0)
                {
                    _gridBaskets.Remove(basketId);
                }
            }

            _patternByPosition.Remove(p.Id);
            _tp1Done.Remove(p.Id);
            _initialRiskPips.Remove(p.Id);
            _initialVolumeUnits.Remove(p.Id);
            _partialClosing.Remove(p.Id);
            _lastSlModifyTime.Remove(p.Id);
            _sumPriceVol.Remove(p.Id);
            _totalClosedUnits.Remove(p.Id);
        }

        private void AccountGridClose(Position p)
        {
            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? _initialRiskPips[p.Id] : 0.0001;
            double initVol = _initialVolumeUnits.ContainsKey(p.Id) ? _initialVolumeUnits[p.Id] : 0;
            double money = p.NetProfit;
            double lifecyclePips = p.Pips;
            double lifecycleVol;
            double historyMoney, historyPips;
            if (TryGetPositionLifecycleFromHistory(p.Id, out historyMoney, out historyPips, out lifecycleVol))
            {
                money = historyMoney;
                lifecyclePips = historyPips;
            }
            double r = ComputeR(money, riskPips, initVol, lifecyclePips);

            long basketId = _positionToBasket.ContainsKey(p.Id) ? _positionToBasket[p.Id] : 0;
            bool isBasketParent = false;
            if (basketId > 0 && _gridBaskets.TryGetValue(basketId, out GridBasket bb))
                isBasketParent = (bb.ParentPositionId == p.Id);

            if (isBasketParent)
            {
                if (money < 0)
                {
                    _consecutiveLosses++;
                    _lastLossTime = Server.Time;
                }
                else
                {
                    _consecutiveLosses = 0;
                }
            }

            if (_tracker != null)
                _tracker.AddTrade(Server.Time, r, money, lifecyclePips);

            string pat = _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "Grid";
            AddToLedger(pat, r, money);

            _positionToBasket.Remove(p.Id);

            if (basketId > 0 && _gridBaskets.TryGetValue(basketId, out GridBasket b))
            {
                b.PositionIds.Remove(p.Id);
                if (b.PositionIds.Count == 0) _gridBaskets.Remove(basketId);
            }

            _patternByPosition.Remove(p.Id);
            _tp1Done.Remove(p.Id);
            _initialRiskPips.Remove(p.Id);
            _initialVolumeUnits.Remove(p.Id);
            _partialClosing.Remove(p.Id);
            _lastSlModifyTime.Remove(p.Id);
            _sumPriceVol.Remove(p.Id);
            _totalClosedUnits.Remove(p.Id);
        }

        // [FIX] 統一 R 計算：優先依初始風險成本，缺資料時回退 pips 比
        private bool TryGetPositionLifecycleFromHistory(long positionId, out double netProfit, out double weightedPips, out double totalClosedVolume)
        {
            netProfit = 0;
            weightedPips = 0;
            totalClosedVolume = 0;
            try
            {
                var deals = History.Where(h => (long)h.PositionId == positionId).ToArray();
                if (deals == null || deals.Length == 0) return false;

                double pipVol = 0;
                foreach (var h in deals)
                {
                    if (h == null || h.SymbolName != SymbolName) continue;
                    double v = Math.Max(0.0, h.VolumeInUnits);
                    netProfit += h.NetProfit;
                    pipVol += h.Pips * v;
                    totalClosedVolume += v;
                }
                if (totalClosedVolume <= 0) return false;
                weightedPips = pipVol / totalClosedVolume;
                return true;
            }
            catch
            {
                netProfit = 0;
                weightedPips = 0;
                totalClosedVolume = 0;
                return false;
            }
        }

        private double ComputeR(double money, double riskPips, double initVol, double pips)
        {
            if (initVol > 0 && _symbol != null && riskPips > 0)
            {
                try
                {
                    double riskMoney = _symbol.AmountRisked(initVol, riskPips);
                    if (riskMoney > 0) return money / riskMoney;
                }
                catch { }
            }
            return pips / Math.Max(riskPips, 0.0001);
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
            Print("           PATTERN-WISE LEDGER (12 PATTERNS + GRID)");
            Print("================================================================");
            Print("  PATTERN        TRADES  WIN%    AVGR    PF      STATUS  DISABLED-REASON");
            Print("  ------------------------------------------------------------");

            foreach (var kv in _ledger.OrderBy(kv => kv.Key))
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

        private void PrintGridReport()
        {
            if (_gridBaskets.Count == 0) return;
            Print("");
            Print("================================================================");
            Print("           FIBONACCI GOLDEN GRID REPORT (OPEN BASKETS)");
            Print("================================================================");
            foreach (var kv in _gridBaskets)
            {
                GridBasket b = kv.Value;
                double cur = GetClosePrice(b.Direction);
                double r = BasketR(b, cur);
                double cumBudget = GridGoldenRiskConvergence
                    ? FibonacciMathCore.GoldenRiskBudgetCumulative(Math.Max(1, b.LevelsOpened), GridMaxTotalRiskPercent)
                    : GridMaxTotalRiskPercent;
                Print("  Basket #{0} {1} | levels={2} units={3} avgEntry={4:F2} target={5:F2} stop={6:F2} r={7:F2} BE={8} Trail={9} ScaledOut={10} riskBudget={11:F2}%",
                    b.Id, b.Direction, b.LevelsOpened, b.TotalUnits, b.WeightedEntry, b.TargetPrice, b.StopPrice,
                    r, b.BreakevenLocked, b.TrailingLocked, b.ScaledOut, cumBudget);
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
                if (kv.Key.StartsWith("Grid", StringComparison.Ordinal)) continue;
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
        //  Trade Management (primary, non-grid positions)
        // ============================================================
        private void ManageOpenPositions()
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

        private bool TryPartialClose(Position p)
        {
            try
            {
                double minVol = _symbol.VolumeInUnitsMin;
                if (p.VolumeInUnits < minVol * 2.0 - 1e-9) return false;

                double closeUnitsRaw = p.VolumeInUnits * (Tp1ClosePercent / 100.0);
                double norm = _symbol.NormalizeVolumeInUnits(closeUnitsRaw, RoundingMode.Down);
                double closeUnits = norm;
                if (closeUnits < minVol) return false;

                double remain = p.VolumeInUnits - closeUnits;
                if (remain < minVol) return false;

                var tr = ClosePosition(p, closeUnits);
                if (tr != null && tr.IsSuccessful)
                {
                    double px = GetClosePrice(p.TradeType);
                    double signedPips = PriceToPips(p.TradeType == TradeType.Buy ? (px - p.EntryPrice) : (p.EntryPrice - px));
                    double partialMoney = 0;
                    try
                    {
                        double absMoney = _symbol.AmountRisked(closeUnits, Math.Abs(signedPips));
                        partialMoney = signedPips >= 0 ? absMoney : -absMoney;
                    }
                    catch { partialMoney = 0; }

                    _sumPriceVol[p.Id] = (_sumPriceVol.ContainsKey(p.Id) ? _sumPriceVol[p.Id] : 0) + partialMoney;
                    _totalClosedUnits[p.Id] = (_totalClosedUnits.ContainsKey(p.Id) ? _totalClosedUnits[p.Id] : 0) + closeUnits;

                    Print("[TP1] Partial close | PosId={0} closed={1} remain={2} realized={3:F2}",
                        p.Id, closeUnits, Math.Max(0, remain), partialMoney);
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
            if (p == null) return false;
            Position live = Positions.FindById((int)p.Id);
            if (live == null) return false;
            p = live;
            if (!CanImproveStopLoss(p, newSl)) return false;

            DateTime last = _lastSlModifyTime.ContainsKey(p.Id) ? _lastSlModifyTime[p.Id] : DateTime.MinValue;
            if ((Server.Time - last).TotalSeconds < SlUpdateCooldownSec) return false;

            var mr = ModifyPosition(p, newSl, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade);
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
            if (!_initialVolumeUnits.ContainsKey(p.Id)) _initialVolumeUnits[p.Id] = p.VolumeInUnits;
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

        private void PruneStateDictionaries()
        {
            var openIds = new HashSet<long>();
            var positions = GetAllManagedPositions();
            foreach (var p in positions)
                if (p != null) openIds.Add(p.Id);

            RemoveMissing(_patternByPosition, openIds);
            RemoveMissing(_tp1Done, openIds);
            RemoveMissing(_initialRiskPips, openIds);
            RemoveMissing(_initialVolumeUnits, openIds);
            RemoveMissing(_lastSlModifyTime, openIds);
            RemoveMissing(_sumPriceVol, openIds);
            RemoveMissing(_totalClosedUnits, openIds);
            _partialClosing.RemoveWhere(k => !openIds.Contains(k));
        }

        private void RemoveMissing<T>(Dictionary<long, T> dict, HashSet<long> openIds)
        {
            if (dict == null || dict.Count == 0) return;
            var stale = dict.Keys.Where(k => !openIds.Contains(k)).ToList();
            foreach (var k in stale) dict.Remove(k);
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

        // [HARD] 權益安全檢查：爆倉前置防護
        private bool IsEquityUnsafe()
        {
            double eq = Account.Equity;
            if (eq > 0) return false;

            if ((Server.Time - _lastEquityWarnTime).TotalSeconds >= 30)
            {
                Print("[FATAL] Account.Equity <= 0; halting.");
                _lastEquityWarnTime = Server.Time;
            }
            return true;
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
            var positions = GetAllManagedPositions();
            foreach (var p in positions)
            {
                var tr = ClosePosition(p);
                if (tr != null && tr.IsSuccessful)
                    Print("[FORCE CLOSE] PosId={0} by {1}", p.Id, reason);
            }
        }

        // ============================================================
        //  Order Execution (hardened)
        // ============================================================
        private TradeResult ExecuteRobotMarketOrder(TradeType tt, double volumeInUnits, double? slPips, double? tpPips)
        {
            if (_symbol == null || volumeInUnits <= 0) return null;

            double vol = _symbol.NormalizeVolumeInUnits(volumeInUnits, RoundingMode.Down);
            if (vol < _symbol.VolumeInUnitsMin || vol > _symbol.VolumeInUnitsMax) return null;

            double basePrice = tt == TradeType.Buy ? _symbol.Ask : _symbol.Bid;
            if (basePrice <= 0) return null;

            if (MaxSlippagePips > 0)
            {
                return ExecuteMarketRangeOrder(tt, SymbolName, vol, MaxSlippagePips, basePrice,
                    BotLabel, slPips, tpPips, "HarmonyBotPro", false, StopTriggerMethod.Trade);
            }

            return ExecuteMarketOrder(tt, SymbolName, vol, BotLabel, slPips, tpPips,
                "HarmonyBotPro", false, StopTriggerMethod.Trade);
        }

        private double GetCurrentDayDrawdownPercent()
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
            double executionReservePips = EstimateExecutionReservePips();
            double maxPips;
            try { maxPips = _symbol.PipsForFixedRisk(riskAmount, minVol) - executionReservePips; }
            catch { return false; }

            double floorPips = Math.Max(EffectiveMinStopLossPips(), MinStopDistancePips);
            if (double.IsNaN(maxPips) || double.IsInfinity(maxPips) || maxPips < floorPips)
            {
                _diagCapitalInfeasible++;
                double requiredEquity = EstimateRequiredEquityForRisk(minVol, floorPips, riskBudgetPct);
                if ((Server.Time - _lastVolumeWarnTime).TotalMinutes >= 5)
                {
                    Print("[RISK-BLOCK] minVol={0} riskBudget={1:F2}% cannot support minSL={2:F1} pips after execution reserve={3:F1} (maxStop={4:F1}).",
                        minVol, riskBudgetPct, floorPips, executionReservePips, maxPips);
                    Print("[CAPITAL-FEASIBILITY] equity={0:F2} requiredEquity={1:F2} minVol={2} structuralSL={3:F1} executionReserve={4:F1} riskBudget={5:F2}%.",
                        Account.Equity, requiredEquity, minVol, floorPips, executionReservePips, riskBudgetPct);
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
                    _diagCapitalInfeasible++;
                    double requiredEquity = EstimateRequiredEquityForRisk(minVol, slPips, riskBudgetPct);
                    Print("[RISK-BLOCK] SL compression {0:P1} exceeds limit {1:P1}; original={2:F1} maxStop={3:F1} executionReserve={4:F1}.",
                        compression, MaxStopCompressionRatio, slPips, maxPips, executionReservePips);
                    Print("[CAPITAL-FEASIBILITY] equity={0:F2} requiredEquity={1:F2} minVol={2} structuralSL={3:F1} executionReserve={4:F1} riskBudget={5:F2}%.",
                        Account.Equity, requiredEquity, minVol, slPips, executionReservePips, riskBudgetPct);
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

        private double EstimateExecutionReservePips()
        {
            double slip = Math.Max(0.0, MaxSlippagePips);
            double commission = Math.Max(0.0, EstimateRoundTurnCommissionPips());
            double reserve = slip + commission;
            return double.IsNaN(reserve) || double.IsInfinity(reserve) ? slip : reserve;
        }

        private double EstimateRequiredEquityForRisk(double volumeInUnits, double slPips, double riskBudgetPct)
        {
            if (_symbol == null || volumeInUnits <= 0 || slPips <= 0 || riskBudgetPct <= 0) return double.MaxValue;
            try
            {
                double allInPips = slPips + EstimateExecutionReservePips();
                double riskMoney = _symbol.AmountRisked(volumeInUnits, allInPips);
                if (riskMoney <= 0 || double.IsNaN(riskMoney) || double.IsInfinity(riskMoney)) return double.MaxValue;
                return riskMoney / (riskBudgetPct / 100.0);
            }
            catch { return double.MaxValue; }
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
            double allInRiskPips = slPips + (CommercialRiskEngine ? EstimateExecutionReservePips() : 0.0);
            double vol;
            try { vol = _symbol.VolumeForFixedRisk(riskAmount, allInRiskPips, RoundingMode.Down); }
            catch { return 0; }
            if (double.IsNaN(vol) || double.IsInfinity(vol) || vol <= 0) return 0;

            vol = _symbol.NormalizeVolumeInUnits(vol, RoundingMode.Down);
            if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;

            if (vol >= _symbol.VolumeInUnitsMin)
                return (CheckNotionalLimit(vol) && CheckMarginLimit(vol)) ? vol : 0;

            if (!AllowMinVolumeFallback) return 0;

            double minVol = _symbol.VolumeInUnitsMin;
            double minRisk;
            try { minRisk = _symbol.AmountRisked(minVol, allInRiskPips); }
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

        private bool CheckNotionalLimit(double volume)
        {
            double price = _symbol.Ask > 0 ? _symbol.Ask : _symbol.Bid;
            if (price <= 0) return true;
            if (_symbol.PipSize <= 0 || _symbol.PipValue <= 0) return true;

            double unitsPerVolume = _symbol.PipValue / _symbol.PipSize;
            double notional = volume * unitsPerVolume * price;
            double maxNotional = Account.Equity * MaxNotionalToEquityRatio;

            if (double.IsNaN(notional) || double.IsInfinity(notional)) return false;

            if (notional > maxNotional)
            {
                if ((Server.Time - _lastNotionalWarnTime).TotalMinutes >= 5)
                {
                    Print("[NOTIONAL] vol={0} notional={1:F2} > max={2:F2} (equity x {3:F0}). Trade skipped.",
                        volume, notional, maxNotional, MaxNotionalToEquityRatio);
                    _lastNotionalWarnTime = Server.Time;
                }
                return false;
            }
            return true;
        }

        private bool CheckMarginLimit(double volume)
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

        private bool IsSmallAccountMode()
        {
            return SmallAccountMode && Account.Equity <= SmallAccountThreshold + 1e-9;
        }

        private double EffectiveMinStopLossPips()
        {
            return IsSmallAccountMode() ? Math.Min(MinStopLossPips, SmallAccountMinSLPips) : MinStopLossPips;
        }

        private double EffectiveMinTakeProfitPips()
        {
            return IsSmallAccountMode() ? Math.Min(MinTakeProfitPips, SmallAccountMinTPPips) : MinTakeProfitPips;
        }

        private double GetClosePrice(TradeType tradeType)
        {
            return tradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
        }

        private double GetClosePrice(TradeDirection direction)
        {
            return direction == TradeDirection.Buy ? _symbol.Bid : _symbol.Ask;
        }

        // ============================================================
        //  Regime / Trend
        // ============================================================
        private void RefreshEmaCache()
        {
            int lastIdx = _signalBars != null ? _signalBars.Count - 1 : -1;
            int completedIdx = lastIdx - 1;

            DateTime barTime = completedIdx >= 0 ? _signalBars.OpenTimes[completedIdx] : DateTime.MinValue;

            if (_emaCacheBar == barTime) return;
            _emaCacheBar = barTime;

            _cacheH1Ema50 = _cacheH1Ema200 = 0;
            _cacheH4Ema50 = _cacheH4Ema200 = 0;

            var h1 = MarketData.GetBars(TimeFrame.Hour, SymbolName);
            if (h1 != null && h1.Count >= 201)
            {
                int e = h1.Count - 2;
                if (e >= 0)
                {
                    _cacheH1Ema50 = CalculateEma(h1.ClosePrices, 50, e);
                    _cacheH1Ema200 = CalculateEma(h1.ClosePrices, 200, e);
                }
            }

            var h4 = MarketData.GetBars(TimeFrame.Hour4, SymbolName);
            if (h4 != null && h4.Count >= 201)
            {
                int e = h4.Count - 2;
                if (e >= 0)
                {
                    _cacheH4Ema50 = CalculateEma(h4.ClosePrices, 50, e);
                    _cacheH4Ema200 = CalculateEma(h4.ClosePrices, 200, e);
                }
            }
        }

        private double CalculateRegimeScore(double atrNow)
        {
            double baseline = 0;
            int n = Math.Min(Math.Max(0, _signalBars.Count - 2), 240);
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
                else
                    score = 0.3;
            }

            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
            {
                bool up4 = _cacheH4Ema50 > _cacheH4Ema200;
                bool aligned = (direction == TradeDirection.Buy && up4) || (direction == TradeDirection.Sell && !up4);
                if (aligned)
                    score = Math.Max(score, 1.0);
                else
                    score = Math.Min(score, 0.3);
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

            if (slPips < EffectiveMinStopLossPips()) return false;

            double requiredTpPips = slPips * MinRR;
            if (UseCostAdjustedRR)
            {
                double spreadPips = Math.Max(0.0, PriceToPips(_symbol.Ask - _symbol.Bid));
                double commissionPips = EstimateRoundTurnCommissionPips();
                requiredTpPips += spreadPips + commissionPips;
            }

            // v28: reprice instead of reject. The old flow first set TP=MinRR and then
            // subtracted spread, making the same signal fail the very next check.
            if (tpPips < requiredTpPips)
                tpPips = requiredTpPips;

            if (tpPips < EffectiveMinTakeProfitPips())
                tpPips = EffectiveMinTakeProfitPips();

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

        private double EstimateRoundTurnCommissionPips()
        {
            if (CommissionPerMillionPerSide <= 0 || _symbol == null || _symbol.PipValue <= 0) return 0;
            double price = (_symbol.Ask > 0 && _symbol.Bid > 0) ? (_symbol.Ask + _symbol.Bid) * 0.5 : Math.Max(_symbol.Ask, _symbol.Bid);
            if (price <= 0) return 0;
            double roundTurnCostPerUnit = 2.0 * CommissionPerMillionPerSide * price / 1000000.0;
            double pips = roundTurnCostPerUnit / _symbol.PipValue;
            return double.IsNaN(pips) || double.IsInfinity(pips) ? 0 : Math.Max(0.0, pips);
        }

        private string BuildSignalKey(Signal signal)
        {
            if (signal == null) return "";
            return string.Format("{0}|{1}|{2}", signal.PatternName ?? "?", signal.Direction, signal.CompletionIndex);
        }

        private void PruneExecutedSignalKeys(int currentBarIndex)
        {
            int keep = Math.Max(16, SignalDedupeBars);
            var stale = _executedSignalBars
                .Where(kv => currentBarIndex - kv.Value > keep)
                .Select(kv => kv.Key)
                .ToList();
            foreach (string key in stale)
                _executedSignalBars.Remove(key);
        }

        private bool PassMtfFilter(Signal signal)
        {
            if (signal == null) return false;
            if (!MTFEnabled && !H4FilterEnabled) return true;

            bool h1Aligned = true;
            bool h4Aligned = true;

            if (MTFEnabled && _cacheH1Ema50 > 0 && _cacheH1Ema200 > 0)
                h1Aligned = signal.Direction == TradeDirection.Buy ? _cacheH1Ema50 > _cacheH1Ema200 : _cacheH1Ema50 < _cacheH1Ema200;

            if (H4FilterEnabled && _cacheH4Ema50 > 0 && _cacheH4Ema200 > 0)
                h4Aligned = signal.Direction == TradeDirection.Buy ? _cacheH4Ema50 > _cacheH4Ema200 : _cacheH4Ema50 < _cacheH4Ema200;

            if (h1Aligned && h4Aligned) return true;

            if (AdaptiveFrequencyRecovery && SoftMtfReversalGate)
            {
                double required = Math.Min(0.95, Math.Max(PatternConfidence, GlobalMinScore) + CounterTrendConfidenceBuffer);
                if (signal.Confidence >= required)
                {
                    Print("[MTF-SOFT] Counter-trend {0} accepted conf={1:F3} required={2:F3}",
                        signal.Direction, signal.Confidence, required);
                    return true;
                }
            }

            return false;
        }

        private bool IsTradingSession()
        {
            DateTime utc = Server.Time;
            if (DstAwareInstitutionalSession)
            {
                // London cash/FX morning: 08:00 local = 07:00 UTC in BST, 08:00 UTC in GMT.
                // New York 17:00 local = 21:00 UTC in EDT, 22:00 UTC in EST.
                int startMinutes = (IsUkDst(utc) ? 7 : 8) * 60;
                int endMinutes = (IsUsDst(utc) ? 21 : 22) * 60;
                int nowMinutes = utc.Hour * 60 + utc.Minute;
                return nowMinutes >= startMinutes && nowMinutes < endMinutes;
            }

            int h = utc.Hour;
            if (SessionStart == SessionEnd) return true;
            if (SessionStart < SessionEnd) return h >= SessionStart && h < SessionEnd;
            return h >= SessionStart || h < SessionEnd;
        }

        private static bool IsUkDst(DateTime utc)
        {
            int y = utc.Year;
            DateTime start = new DateTime(y, 3, LastSundayOfMonth(y, 3), 1, 0, 0, DateTimeKind.Utc);
            DateTime end = new DateTime(y, 10, LastSundayOfMonth(y, 10), 1, 0, 0, DateTimeKind.Utc);
            return utc >= start && utc < end;
        }

        private static bool IsUsDst(DateTime utc)
        {
            int y = utc.Year;
            int marchSecondSunday = NthSundayOfMonth(y, 3, 2);
            int novemberFirstSunday = NthSundayOfMonth(y, 11, 1);
            // US transition instants expressed in UTC for Eastern Time.
            DateTime start = new DateTime(y, 3, marchSecondSunday, 7, 0, 0, DateTimeKind.Utc);
            DateTime end = new DateTime(y, 11, novemberFirstSunday, 6, 0, 0, DateTimeKind.Utc);
            return utc >= start && utc < end;
        }

        private static int LastSundayOfMonth(int year, int month)
        {
            DateTime d = new DateTime(year, month, DateTime.DaysInMonth(year, month));
            return d.Day - (int)d.DayOfWeek;
        }

        private static int NthSundayOfMonth(int year, int month, int nth)
        {
            DateTime first = new DateTime(year, month, 1);
            int offset = ((int)DayOfWeek.Sunday - (int)first.DayOfWeek + 7) % 7;
            return 1 + offset + (nth - 1) * 7;
        }

        private bool IsSpreadValid()
        {
            double ask = _symbol.Ask;
            double bid = _symbol.Bid;
            if (ask <= 0 || bid <= 0 || ask <= bid) return false;

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
                if (!TryParseHm(se[0].Trim(), out s)) continue;
                if (!TryParseHm(se[1].Trim(), out e)) continue;

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

        private static bool TryParseHm(string s, out TimeSpan ts)
        {
            return TimeSpan.TryParseExact(s, @"h\:mm", CultureInfo.InvariantCulture, out ts)
                || TimeSpan.TryParseExact(s, @"hh\:mm", CultureInfo.InvariantCulture, out ts);
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

        private Position[] GetAllManagedPositions()
        {
            var primary = Positions.FindAll(BotLabel, SymbolName) ?? new Position[0];
            var grid = Positions.FindAll(GridLabel, SymbolName) ?? new Position[0];
            if (grid.Length == 0) return primary;

            var all = new List<Position>(primary.Length + grid.Length);
            all.AddRange(primary);
            all.AddRange(grid);
            return all.ToArray();
        }

        // ============================================================
        //  Restore / Protect
        // ============================================================
        private void RebuildRuntimeStateFromOpenPositions()
        {
            var positions = GetAllManagedPositions();
            double atrNow = CurrentAtr();

            foreach (var p in positions)
            {
                bool isGrid = p.Label == GridLabel;

                if (!_tp1Done.ContainsKey(p.Id)) _tp1Done[p.Id] = isGrid;
                if (!_patternByPosition.ContainsKey(p.Id)) _patternByPosition[p.Id] = isGrid ? "Grid" : "Unknown";
                if (!_initialVolumeUnits.ContainsKey(p.Id)) _initialVolumeUnits[p.Id] = p.VolumeInUnits;

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
            var positions = GetAllManagedPositions();
            if (positions == null || positions.Length == 0) return;

            double atrNow = CurrentAtr();
            double minSlPrice = PipsToPrice(EffectiveMinStopLossPips());
            double minTpPrice = PipsToPrice(EffectiveMinTakeProfitPips());

            foreach (var p in positions)
            {
                if (!_tp1Done.ContainsKey(p.Id))
                    _tp1Done[p.Id] = true;

                if (!_initialVolumeUnits.ContainsKey(p.Id))
                    _initialVolumeUnits[p.Id] = p.VolumeInUnits;

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

                    double slDistPrice = Math.Max(minSlPrice, atrNow * EmergencySlAtrMult);
                    double tpDistPrice = Math.Max(minTpPrice, slDistPrice * EmergencyTpRR);

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
                var positions = GetAllManagedPositions();
                if (positions == null || positions.Length == 0) return;

                double atrNow = CurrentAtr();
                if (atrNow <= 0) return;

                double minSlPrice = PipsToPrice(EffectiveMinStopLossPips());
                double minTpPrice = PipsToPrice(EffectiveMinTakeProfitPips());

                foreach (var p in positions)
                {
                    if (p.StopLoss.HasValue && p.TakeProfit.HasValue) continue;

                    double slDistPrice = Math.Max(minSlPrice, atrNow * EmergencySlAtrMult);
                    double tpDistPrice = Math.Max(minTpPrice, slDistPrice * EmergencyTpRR);

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
        //  Fibonacci Golden Grid Engine integration
        // ============================================================
        private void CreateBasketFor(Position p)
        {
            if (!EnableFibGrid) return;
            if (_positionToBasket.ContainsKey(p.Id)) return;

            double baseRiskPrice;
            if (_lastPrimaryRiskPips > 0)
            {
                baseRiskPrice = PipsToPrice(_lastPrimaryRiskPips);
            }
            else if (p.StopLoss.HasValue)
            {
                baseRiskPrice = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Math.Max(GridStopFib, 0.001);
            }
            else
            {
                baseRiskPrice = PipsToPrice(EstimateRiskPips(CurrentAtr()));
            }

            if (baseRiskPrice <= 0) baseRiskPrice = PipsToPrice(EffectiveMinStopLossPips());

            TradeDirection dir = p.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;
            double stopPrice = FibonacciGridEngine.BasketStopPrice(dir, p.EntryPrice, baseRiskPrice, GridStopFib);

            var b = new GridBasket
            {
                Id = p.Id,
                Direction = dir,
                PatternName = _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "Unknown",
                ParentPositionId = p.Id,
                BaseEntry = p.EntryPrice,
                BaseStop = stopPrice,
                BaseRisk = baseRiskPrice,
                ParentVolume = p.VolumeInUnits,
                LevelsOpened = 0,
                LastAddTime = Server.Time,
                WeightedEntry = p.EntryPrice,
                TotalUnits = p.VolumeInUnits,
                StopPrice = stopPrice,
                EntryAtr = CurrentAtr(),
                PeakPrice = p.EntryPrice,
                PeakProfitMoney = 0,
                BreakevenLocked = false,
                TrailingLocked = false,
                ScaledOut = false,
                IsSynthetic = false,
                DayTag = Server.Time.DayOfYear,
                DailyAdds = 0,
                LastProtectTime = Server.Time
            };
            b.TargetPrice = FibonacciGridEngine.BasketTargetPrice(b.Direction, b.WeightedEntry, b.BaseRisk, GridProfitFib);
            b.PositionIds.Add(p.Id);

            _gridBaskets[p.Id] = b;
            _positionToBasket[p.Id] = p.Id;

            _initialRiskPips[p.Id] = Math.Max(PriceToPips(Math.Abs(p.EntryPrice - stopPrice)), 0.0001);
            _lastPrimaryRiskPips = 0;

            Print("[GRID] Basket #{0} created | {1} | base={2:F2} baseRisk={3:F2} stop={4:F2} target={5:F2} atr={6:F2}",
                b.Id, b.PatternName, b.BaseEntry, b.BaseRisk, b.StopPrice, b.TargetPrice, b.EntryAtr);
        }

        private void ManageGridBaskets()
        {
            if (!EnableFibGrid || _gridBaskets.Count == 0) return;

            var positions = GetAllManagedPositions();
            var ids = _gridBaskets.Keys.ToList();

            foreach (var id in ids)
            {
                GridBasket b;
                if (!_gridBaskets.TryGetValue(id, out b)) continue;

                var open = positions.Where(p => _positionToBasket.ContainsKey(p.Id) && _positionToBasket[p.Id] == id).ToList();
                if (open.Count == 0)
                {
                    _gridBaskets.Remove(id);
                    continue;
                }

                RecomputeBasket(b, positions);
                double cur = GetClosePrice(b.Direction);
                double money = BasketFloatingMoney(b, cur, positions);
                double r = BasketR(b, cur);

                bool profitHit = b.Direction == TradeDirection.Buy ? cur >= b.TargetPrice : cur <= b.TargetPrice;
                if (profitHit)
                {
                    CloseBasket(id, b, "GridTP", positions);
                    Print("[GRID] Basket #{0} TP hit | profit={1:F2} | target={2:F2} r={3:F2}",
                        id, money, b.TargetPrice, r);
                    continue;
                }

                UpdateBasketProtection(b, cur, money, r, positions);

                if (GridScaleOutEnabled && !b.ScaledOut && r >= GridScaleOutR)
                {
                    ScaleOutBasket(b, GridScaleOutPercent, positions);
                    b.ScaledOut = true;

                    var positions2 = GetAllManagedPositions();
                    RecomputeBasket(b, positions2);
                    cur = GetClosePrice(b.Direction);
                    money = BasketFloatingMoney(b, cur, positions2);
                    r = BasketR(b, cur);
                    LockBasketBreakeven(b, positions2);
                    Print("[GRID] Basket #{0} SCALE-OUT {1:F1}% | locked profit={2:F2}",
                        id, GridScaleOutPercent, money);
                }

                bool stopHit = b.Direction == TradeDirection.Buy ? cur <= b.StopPrice : cur >= b.StopPrice;
                if (stopHit)
                {
                    CloseBasket(id, b, "GridStop", positions);
                    Print("[GRID] Basket #{0} STOP hit | stop={1:F2}", id, b.StopPrice);
                    continue;
                }

                TryAddGridLevel(b, positions);
            }
        }

        private void RecomputeBasket(GridBasket b, Position[] positions)
        {
            double sumVol = 0, sumEv = 0;

            foreach (var p in positions)
            {
                if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != b.Id) continue;
                sumEv += p.EntryPrice * p.VolumeInUnits;
                sumVol += p.VolumeInUnits;
            }

            b.TotalUnits = sumVol;
            b.WeightedEntry = sumVol > 0 ? sumEv / sumVol : b.BaseEntry;
            b.TargetPrice = FibonacciGridEngine.BasketTargetPrice(b.Direction, b.WeightedEntry, b.BaseRisk, GridProfitFib);
        }

        private double BasketFloatingMoney(GridBasket b, double cur, Position[] positions)
        {
            if (_symbol.PipSize <= 0 || _symbol.PipValue <= 0) return 0;
            double factor = _symbol.PipValue / _symbol.PipSize;
            double sum = 0;

            foreach (var p in positions)
            {
                if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != b.Id) continue;
                double signed = b.Direction == TradeDirection.Buy ? (cur - p.EntryPrice) : (p.EntryPrice - cur);
                sum += signed * factor * p.VolumeInUnits;
            }
            return sum;
        }

        private double ProjectedBasketLoss(GridBasket b, double addVolume, double addEntry, Position[] positions)
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

        private double BasketR(GridBasket b, double cur)
        {
            if (_symbol.PipSize <= 0 || b.BaseRisk <= 0) return 0;
            double diff = b.Direction == TradeDirection.Buy ? (cur - b.WeightedEntry) : (b.WeightedEntry - cur);
            return PriceToPips(diff) / Math.Max(PriceToPips(b.BaseRisk), 0.0001);
        }

        private void UpdateBasketProtection(GridBasket b, double cur, double money, double r, Position[] positions)
        {
            if (_symbol.PipSize <= 0 || b.BaseRisk <= 0) return;

            if (b.Direction == TradeDirection.Buy) { if (cur > b.PeakPrice) b.PeakPrice = cur; }
            else { if (cur < b.PeakPrice) b.PeakPrice = cur; }
            if (money > b.PeakProfitMoney) b.PeakProfitMoney = money;

            if (!b.BreakevenLocked && r >= GridBreakevenTriggerR)
                LockBasketBreakeven(b, positions);

            if (b.BreakevenLocked && r >= Math.Max(GridBreakevenTriggerR, GridTrailTriggerR))
            {
                double baseRiskPips = Math.Max(PriceToPips(b.BaseRisk), 0.0001);
                double trailFib = GridTrailDistanceFib;

                if (GridGoldenTrailCompression)
                    trailFib = FibonacciMathCore.GoldenTrailCompression(Math.Max(1, b.LevelsOpened), GridTrailDistanceFib);

                double trailDist = PipsToPrice(baseRiskPips * trailFib);
                double newStop = b.Direction == TradeDirection.Buy ? cur - trailDist : cur + trailDist;

                if (b.Direction == TradeDirection.Buy)
                {
                    if (newStop > b.StopPrice)
                    {
                        b.StopPrice = newStop;
                        b.TrailingLocked = true;
                        ApplyBasketStopToPositions(b, positions);
                    }
                }
                else
                {
                    if (newStop < b.StopPrice)
                    {
                        b.StopPrice = newStop;
                        b.TrailingLocked = true;
                        ApplyBasketStopToPositions(b, positions);
                    }
                }
            }
        }

        private void LockBasketBreakeven(GridBasket b, Position[] positions)
        {
            if (b.BreakevenLocked) return;

            double be = b.Direction == TradeDirection.Buy
                ? b.WeightedEntry + PipsToPrice(GridBreakevenLockPips)
                : b.WeightedEntry - PipsToPrice(GridBreakevenLockPips);

            if (b.Direction == TradeDirection.Buy)
            {
                if (be > b.StopPrice) { b.StopPrice = be; b.BreakevenLocked = true; }
            }
            else
            {
                if (be < b.StopPrice) { b.StopPrice = be; b.BreakevenLocked = true; }
            }

            if (b.BreakevenLocked)
                ApplyBasketStopToPositions(b, positions);
        }

        private void ApplyBasketStopToPositions(GridBasket b, Position[] positions)
        {
            if ((Server.Time - b.LastProtectTime).TotalSeconds < SlUpdateCooldownSec) return;
            b.LastProtectTime = Server.Time;

            foreach (var p in positions)
            {
                if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != b.Id) continue;

                if (p.StopLoss.HasValue)
                {
                    if (b.Direction == TradeDirection.Buy && b.StopPrice <= p.StopLoss.Value) continue;
                    if (b.Direction == TradeDirection.Sell && b.StopPrice >= p.StopLoss.Value) continue;
                }

                if (!HasMinDistanceFromMarket(p.TradeType, b.StopPrice, MinStopDistancePips)) continue;

                var mr = ModifyPosition(p, b.StopPrice, p.TakeProfit, p.HasTrailingStop, StopTriggerMethod.Trade);
                if (mr != null && mr.IsSuccessful)
                    _lastSlModifyTime[p.Id] = Server.Time;
            }
        }

        private void ScaleOutBasket(GridBasket b, double pct, Position[] positions)
        {
            if (pct <= 0 || pct >= 100) return;

            foreach (var p in positions)
            {
                if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != b.Id) continue;

                double closeRaw = p.VolumeInUnits * (pct / 100.0);
                double norm = _symbol.NormalizeVolumeInUnits(closeRaw, RoundingMode.Down);
                long closeUnits = (long)Math.Floor(norm);
                if (closeUnits <= 0) continue;

                double remain = p.VolumeInUnits - closeUnits;
                if (remain > 0 && remain < _symbol.VolumeInUnitsMin)
                    closeUnits = (long)Math.Floor(p.VolumeInUnits);

                if (closeUnits <= 0) continue;

                var tr = ClosePosition(p, closeUnits);
                if (tr != null && tr.IsSuccessful)
                    Print("[GRID] Scale-out #{0} PosId={1} closed={2}", b.Id, p.Id, closeUnits);
            }
        }

        private bool GridTrendAllows(TradeDirection direction)
        {
            if (!MTFEnabled && !H4FilterEnabled) return true;
            return PassMtfFilter(direction);
        }

        private void TryAddGridLevel(GridBasket b, Position[] positions)
        {
            if (b.LevelsOpened >= GridMaxLevels) return;
            if (b.BreakevenLocked || b.ScaledOut) return;
            if (_dailyLocked || _weeklyLocked) return;
            if (!IsTradingSession()) return;
            if (BlockNewsWindow && IsInBlockedNewsWindow(Server.Time)) return;
            if (!IsSpreadValid()) return;

            int dayTag = Server.Time.DayOfYear;
            if (b.DayTag != dayTag) { b.DayTag = dayTag; b.DailyAdds = 0; }
            if (b.DailyAdds >= GridMaxAddsPerDay) return;

            int nextLevel = b.LevelsOpened + 1;

            double cooldown = GridCooldownMinutes;
            if (GridUseGoldenMath)
                cooldown = FibonacciMathCore.GoldenCooldownMultiplier(nextLevel, GridCooldownMinutes);
            if (cooldown > 0 && (Server.Time - b.LastAddTime).TotalMinutes < cooldown) return;

            double cur = GetClosePrice(b.Direction);
            double adv = b.Direction == TradeDirection.Buy ? b.BaseEntry - cur : cur - b.BaseEntry;
            if (adv <= 0) return;

            double distPrice = FibonacciGridEngine.LevelDistance(nextLevel, b.BaseRisk, _gridLevelFibs, GridUseGoldenMath);
            double minStep = PipsToPrice(GridMinStepPips);
            if (distPrice < minStep) distPrice = minStep;

            if (adv < distPrice) return;

            if (GridOnlyWithTrend && !GridTrendAllows(b.Direction)) return;

            double sizeMult = FibonacciGridEngine.LevelSize(nextLevel, 1.0, _gridSizeFibs, GridUseGoldenMath);

            if (GridVolatilityAdapt)
            {
                double atrNow = CurrentAtr();
                if (b.EntryAtr > 0 && atrNow > 0)
                {
                    double volRatio = atrNow / b.EntryAtr;
                    if (volRatio < 0.7) sizeMult *= 0.5;
                    else if (volRatio > 1.6) sizeMult *= 0.7;
                }
            }

            double addVolume = _symbol.NormalizeVolumeInUnits(b.ParentVolume * sizeMult, RoundingMode.Down);

            if (addVolume < _symbol.VolumeInUnitsMin)
            {
                if (!AllowMinVolumeFallback) return;
                addVolume = _symbol.VolumeInUnitsMin;
                double addStopPips = PriceToPips(Math.Abs(cur - b.StopPrice));
                double addRisk;
                try { addRisk = _symbol.AmountRisked(addVolume, addStopPips); }
                catch { return; }
                double addRiskPct = Account.Equity > 0 ? addRisk / Account.Equity * 100.0 : double.MaxValue;
                if (addRiskPct > Math.Max(0.1, GridMaxTotalRiskPercent)) return;
            }
            if (addVolume > _symbol.VolumeInUnitsMax) addVolume = _symbol.VolumeInUnitsMax;
            if (addVolume < _symbol.VolumeInUnitsMin) return;

            double maxRiskPct = GridMaxTotalRiskPercent;
            if (GridDrawdownScaleRisk) maxRiskPct *= GetDynamicRiskFactor();
            if (maxRiskPct <= 0) return;

            double allowedRiskPct = maxRiskPct;
            if (GridGoldenRiskConvergence)
                allowedRiskPct = FibonacciMathCore.GoldenRiskBudgetCumulative(nextLevel, maxRiskPct);

            double exposure = ProjectedBasketLoss(b, addVolume, cur, positions);
            double equity = Account.Equity;
            if (equity > 0 && exposure / equity * 100.0 > allowedRiskPct)
            {
                if ((Server.Time - _lastGridPrint).TotalMinutes >= 5)
                {
                    Print("[GRID] Basket #{0} add L{1} blocked: projected risk {2:F2}% > golden budget {3:F2}%",
                        b.Id, nextLevel, exposure / equity * 100.0, allowedRiskPct);
                    _lastGridPrint = Server.Time;
                }
                return;
            }

            if (!CheckNotionalLimit(addVolume) || !CheckMarginLimit(addVolume)) return;

            double stopPips = PriceToPips(Math.Abs(cur - b.StopPrice));
            if (stopPips < EffectiveMinStopLossPips()) stopPips = EffectiveMinStopLossPips();

            TradeType tt = b.Direction == TradeDirection.Buy ? TradeType.Buy : TradeType.Sell;

            _pendingGridBasketId = b.Id;
            _pendingGridLevel = nextLevel;
            var tr = ExecuteRobotGridMarketOrder(tt, addVolume, stopPips);
            _pendingGridBasketId = 0;
            _pendingGridLevel = 0;

            if (tr != null && tr.IsSuccessful)
            {
                if (tr.Position != null)
                {
                    _positionToBasket[tr.Position.Id] = b.Id;
                    _patternByPosition[tr.Position.Id] = "Grid-L" + nextLevel;
                    _tp1Done[tr.Position.Id] = true;
                    _initialRiskPips[tr.Position.Id] = Math.Max(stopPips, 0.0001);
                    _initialVolumeUnits[tr.Position.Id] = tr.Position.VolumeInUnits;
                    if (!b.PositionIds.Contains(tr.Position.Id)) b.PositionIds.Add(tr.Position.Id);
                }

                b.LevelsOpened = nextLevel;
                b.LastAddTime = Server.Time;
                b.DailyAdds++;
                RecomputeBasket(b, GetAllManagedPositions());

                Print("[GRID] Basket #{0} add L{1} {2} vol={3} price={4:F2} sl={5:F2} sizeMult={6:F2}",
                    b.Id, nextLevel, tt, addVolume, cur, b.StopPrice, sizeMult);
            }
            else
            {
                Print("[GRID ERROR] Basket #{0} L{1}: {2}", b.Id, nextLevel, tr == null ? "null" : tr.Error.ToString());
            }
        }

        private TradeResult ExecuteRobotGridMarketOrder(TradeType tt, double volumeInUnits, double? slPips)
        {
            if (_symbol == null) return null;

            double vol = _symbol.NormalizeVolumeInUnits(volumeInUnits, RoundingMode.Down);
            double step = _symbol.VolumeInUnitsStep > 0 ? _symbol.VolumeInUnitsStep : 1;
            vol = Math.Floor(vol / step) * step;
            if (vol < _symbol.VolumeInUnitsMin) vol = _symbol.VolumeInUnitsMin;
            if (vol > _symbol.VolumeInUnitsMax) vol = _symbol.VolumeInUnitsMax;
            return ExecuteMarketOrder(tt, SymbolName, vol, GridLabel, slPips, null,
                "HarmonyBotPro-G", false, StopTriggerMethod.Trade);
        }

        private void CloseBasket(long basketId, GridBasket b, string reason, Position[] positions)
        {
            if (_basketsClosing.Contains(basketId)) return;
            _basketsClosing.Add(basketId);
            try
            {
                var ordered = positions
                    .Where(p => _positionToBasket.ContainsKey(p.Id) && _positionToBasket[p.Id] == basketId)
                    .OrderBy(p => p.Id == b.ParentPositionId ? 1 : 0)
                    .ToList();

                foreach (var p in ordered)
                {
                    var tr = ClosePosition(p);
                    if (tr != null && tr.IsSuccessful)
                        Print("[GRID] Close #{0} PosId={1} by {2}", basketId, p.Id, reason);
                }
                _gridBaskets.Remove(basketId);
            }
            finally
            {
                _basketsClosing.Remove(basketId);
            }
        }

        private void CloseRemainingBasketPositions(long basketId, GridBasket b, string reason)
        {
            var positions = GetAllManagedPositions();
            foreach (var p in positions)
            {
                if (p.Id == b.ParentPositionId) continue;
                if (!_positionToBasket.ContainsKey(p.Id) || _positionToBasket[p.Id] != basketId) continue;
                var tr = ClosePosition(p);
                if (tr != null && tr.IsSuccessful)
                    Print("[GRID] Close #{0} PosId={1} by {2}", basketId, p.Id, reason);
            }
        }

        private void RebuildGridBasketsFromOpenPositions()
        {
            if (!EnableFibGrid) return;

            var primaries = Positions.FindAll(BotLabel, SymbolName) ?? new Position[0];
            var gridKids = Positions.FindAll(GridLabel, SymbolName) ?? new Position[0];
            var allPositions = GetAllManagedPositions();
            var usedKids = new HashSet<long>();

            foreach (var p in primaries)
            {
                if (_positionToBasket.ContainsKey(p.Id)) continue;

                double baseRiskPrice;
                if (p.StopLoss.HasValue)
                    baseRiskPrice = Math.Abs(p.EntryPrice - p.StopLoss.Value) / Math.Max(GridStopFib, 0.001);
                else
                    baseRiskPrice = PipsToPrice(EstimateRiskPips(CurrentAtr()));
                if (baseRiskPrice <= 0) baseRiskPrice = PipsToPrice(EffectiveMinStopLossPips());

                TradeDirection dir = p.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;
                double stopPrice = FibonacciGridEngine.BasketStopPrice(dir, p.EntryPrice, baseRiskPrice, GridStopFib);

                var b = new GridBasket
                {
                    Id = p.Id,
                    Direction = dir,
                    PatternName = _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "Unknown",
                    ParentPositionId = p.Id,
                    BaseEntry = p.EntryPrice,
                    BaseStop = stopPrice,
                    BaseRisk = baseRiskPrice,
                    ParentVolume = p.VolumeInUnits,
                    LevelsOpened = 0,
                    LastAddTime = Server.Time,
                    WeightedEntry = p.EntryPrice,
                    TotalUnits = p.VolumeInUnits,
                    StopPrice = stopPrice,
                    EntryAtr = CurrentAtr(),
                    PeakPrice = p.EntryPrice,
                    PeakProfitMoney = 0,
                    IsSynthetic = false,
                    DayTag = Server.Time.DayOfYear,
                    DailyAdds = 0,
                    LastProtectTime = Server.Time
                };
                b.TargetPrice = FibonacciGridEngine.BasketTargetPrice(dir, p.EntryPrice, baseRiskPrice, GridProfitFib);
                b.PositionIds.Add(p.Id);

                _gridBaskets[p.Id] = b;
                _positionToBasket[p.Id] = p.Id;

                foreach (var k in gridKids)
                {
                    if (usedKids.Contains(k.Id)) continue;
                    TradeDirection kdir = k.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;
                    if (kdir != dir) continue;

                    _positionToBasket[k.Id] = p.Id;
                    _patternByPosition[k.Id] = "Grid";
                    _tp1Done[k.Id] = true;
                    if (!b.PositionIds.Contains(k.Id)) b.PositionIds.Add(k.Id);
                    b.LevelsOpened++;
                    usedKids.Add(k.Id);
                }

                RecomputeBasket(b, allPositions);
                Print("[GRID] Restored basket #{0} | {1} | {2} children", p.Id, b.PatternName, b.LevelsOpened);
            }

            var orphans = gridKids.Where(k => !usedKids.Contains(k.Id)).ToList();
            if (orphans.Count > 0)
            {
                foreach (var grp in orphans.GroupBy(k => k.TradeType))
                {
                    var first = grp.OrderBy(k => k.EntryTime).First();
                    TradeDirection dir = first.TradeType == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;

                    double baseRiskPrice = PipsToPrice(EstimateRiskPips(CurrentAtr()));
                    if (baseRiskPrice <= 0) baseRiskPrice = PipsToPrice(EffectiveMinStopLossPips());
                    double stopPrice = FibonacciGridEngine.BasketStopPrice(dir, first.EntryPrice, baseRiskPrice, GridStopFib);

                    var b = new GridBasket
                    {
                        Id = first.Id,
                        Direction = dir,
                        PatternName = "Grid",
                        ParentPositionId = first.Id,
                        BaseEntry = first.EntryPrice,
                        BaseStop = stopPrice,
                        BaseRisk = baseRiskPrice,
                        ParentVolume = first.VolumeInUnits,
                        LevelsOpened = 0,
                        LastAddTime = Server.Time,
                        WeightedEntry = first.EntryPrice,
                        TotalUnits = first.VolumeInUnits,
                        StopPrice = stopPrice,
                        EntryAtr = CurrentAtr(),
                        PeakPrice = first.EntryPrice,
                        PeakProfitMoney = 0,
                        IsSynthetic = true,
                        DayTag = Server.Time.DayOfYear,
                        DailyAdds = 0,
                        LastProtectTime = Server.Time
                    };
                    b.TargetPrice = FibonacciGridEngine.BasketTargetPrice(dir, first.EntryPrice, baseRiskPrice, GridProfitFib);

                    _gridBaskets[first.Id] = b;

                    foreach (var k in grp)
                    {
                        _positionToBasket[k.Id] = first.Id;
                        _patternByPosition[k.Id] = "Grid";
                        _tp1Done[k.Id] = true;
                        if (!b.PositionIds.Contains(k.Id)) b.PositionIds.Add(k.Id);
                        b.LevelsOpened++;
                    }

                    RecomputeBasket(b, allPositions);
                    Print("[GRID] Restored orphan basket #{0} | {1} children", first.Id, b.LevelsOpened);
                }
            }
        }

        // ============================================================
        //  Helpers
        // ============================================================
        private double CurrentAtr()
        {
            if (_signalBars == null) return 0;
            int idx = _signalBars.Count - 2;
            if (idx <= AtrPeriod) idx = _signalBars.Count - 1;
            if (idx <= AtrPeriod) return 0;
            return CalculateAtr(_signalBars, AtrPeriod, idx);
        }

        private double EstimateRiskPips(double atrNow)
        {
            double est = atrNow > 0 ? PriceToPips(atrNow * SlAtrMult) : EffectiveMinStopLossPips();
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
            if (start + period - 1 > endIndex) return 0;

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
            if (endIndex - period < 0) return 0;

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
        Reversal,
        ABCD,
        Shark,
        FiveZero
    }

    public class Signal
    {
        public TradeDirection Direction { get; set; }
        public double EntryPrice { get; set; }
        public double StopLoss { get; set; }
        public double TakeProfit { get; set; }
        public double Confidence { get; set; }
        public string PatternName { get; set; }
        public int CompletionIndex { get; set; }
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
        private readonly bool _closedBarProvisionalD;
        private readonly double _provisionalDMinMoveAtr;
        private readonly int _candidateMaxAgeBars;
        private readonly double _directionDominanceMargin;
        private readonly double _rangeBoundaryScore;
        private readonly double _reversalTrendFloor;

        private readonly Dictionary<string, bool> _enabled = new Dictionary<string, bool>();
        private readonly Dictionary<string, string> _disabledReason = new Dictionary<string, string>();

        private readonly PatternDef[] _defs;

        public HarmonicPatternDetector(int depth, int lookback, double minConfidence, double slAtrMult, double tpCdMult,
            int scanCount, double minLegAtrRatio, double globalMinScore, double consensusBonus,
            double fibTolerance, double maxEntryDeviationAtr,
            bool closedBarProvisionalD, double provisionalDMinMoveAtr,
            int candidateMaxAgeBars, double directionDominanceMargin, double rangeBoundaryScore, double reversalTrendFloor,
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
            _closedBarProvisionalD = closedBarProvisionalD;
            _provisionalDMinMoveAtr = Math.Max(0.10, Math.Min(1.00, provisionalDMinMoveAtr));
            _candidateMaxAgeBars = Math.Max(4, candidateMaxAgeBars);
            _directionDominanceMargin = Math.Max(0.0, Math.Min(0.20, directionDominanceMargin));
            _rangeBoundaryScore = Math.Max(0.30, Math.Min(0.90, rangeBoundaryScore));
            _reversalTrendFloor = Math.Max(0.0, Math.Min(0.80, reversalTrendFloor));

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

        private class Candidate
        {
            public SwingPoint X, A, B, C, D;
            public bool IsBullish;
            public double Score;
            public double Threshold;
            public string PatternName;
            public PatternFamily Family;
        }

        private static PatternDef[] GetAllDefs()
        {
            return new PatternDef[]
            {
                new PatternDef("Gartley", PatternFamily.Reversal, 0.55, 0.72, R_618, 0.382, 0.886, R_618, 1.13, R_1618, R_1272, 0.70, 0.90, R_786, 0.70, 0.90, 0.60, 1.0),
                new PatternDef("Bat", PatternFamily.Reversal, 0.35, 0.55, R_50, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, 0.80, 0.95, R_886, 0.70, 0.80, 0.85, 1.0),
                new PatternDef("Butterfly", PatternFamily.Reversal, 0.70, 0.85, R_786, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, 1.20, R_1618, R_1272, 0.68, 0.70, 0.80, 1.0),
                new PatternDef("Crab", PatternFamily.Reversal, 0.35, 0.62, R_50, 0.382, 0.886, R_618, R_224, R_3618, R_2618, R_1618, R_1618, R_1618, 0.70, 0.90, 0.50, 0.95),
                new PatternDef("Cypher", PatternFamily.Reversal, R_382, R_618, R_50, R_113, R_1414, R_1272, 0, 0, 0, 0.70, 0.90, R_786, 0.68, 0.70, 0.70, 1.0),
                new PatternDef("Rat", PatternFamily.Reversal, R_382, R_618, R_50, 0.382, 0.886, R_618, R_1618, R_2618, R_1618, R_382, R_618, R_50, 0.66, 0.80, 0.60, 1.0),
                new PatternDef("Deep Gartley", PatternFamily.Reversal, 0.588, 0.648, R_618, 0.382, 0.886, R_618, R_1618, R_2618, R_20, R_786, R_886, R_886, 0.68, 0.75, 0.75, 1.0),
                new PatternDef("Alt Bat", PatternFamily.Reversal, 0.30, 0.45, R_382, 0.382, 0.886, R_618, R_20, R_3618, R_20, 1.05, 1.25, R_113, 0.72, 0.70, 0.80, 1.0),
                new PatternDef("Deep Crab", PatternFamily.Reversal, 0.85, 0.95, R_886, 0.382, 0.886, R_618, R_20, R_3618, R_2618, 1.55, 1.70, R_1618, 0.70, 0.85, 0.60, 1.0),
                new PatternDef("ABCD", PatternFamily.ABCD, 0.90, 1.15, 1.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.66, 0.60, 0.90, 1.0),
                new PatternDef("Shark", PatternFamily.Shark, R_113, R_1618, R_1272, 0.886, R_113, 1.0, 0, 0, 0, 0, 0, 0, 0.68, 0.30, 1.0, 1.0),
                new PatternDef("5-0", PatternFamily.FiveZero, R_113, R_1618, R_1272, 0.886, R_113, 1.0, 0, 0, 0, 0.45, 0.55, R_50, 0.70, 0.50, 0.90, 1.0)
            };
        }

        public bool TryDetect(Bars bars, int currentIndex, double atrNow, Symbol symbol,
            double regimeScore, double buyTrend, double sellTrend, out Signal signal)
        {
            signal = null;
            if (bars == null || symbol == null || currentIndex < _depth * 4 || currentIndex >= bars.Count || atrNow <= 0)
                return false;

            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);
            if (_closedBarProvisionalD)
                AppendClosedBarProvisionalPivot(pivots, bars, currentIndex, atrNow, _provisionalDMinMoveAtr);
            if (pivots.Count < 4) return false;

            int start = Math.Max(0, pivots.Count - _scanCount);
            var all = new List<Candidate>();

            for (int i = start; i <= pivots.Count - 4; i++)
            {
                foreach (var def in _defs)
                {
                    if (!IsDefEnabled(def)) continue;
                    Candidate c = Match(bars, pivots, i, def, atrNow, regimeScore, buyTrend, sellTrend, currentIndex);
                    if (c == null) continue;

                    SwingPoint reference = c.Family == PatternFamily.Shark ? c.C : c.D;
                    if (reference == null) continue;
                    if (_candidateMaxAgeBars > 0 && currentIndex - reference.Index > _candidateMaxAgeBars) continue;

                    double candidateEntry = c.IsBullish ? symbol.Ask : symbol.Bid;
                    if (candidateEntry <= 0) continue;
                    if (Math.Abs(candidateEntry - reference.Price) > atrNow * _maxEntryDeviationAtr) continue;

                    all.Add(c);
                }
            }

            if (all.Count == 0) return false;

            var groups = new Dictionary<int, List<Candidate>>();
            foreach (Candidate c in all)
            {
                int key = c.X != null ? c.X.Index : c.A.Index;
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
                double bestBuy = -1, bestSell = -1;
                int buyCount = 0, sellCount = 0;
                for (int i = 0; i < slot.Count; i++)
                {
                    Candidate c = slot[i];
                    if (c.IsBullish) { buyCount++; if (c.Score > bestBuy) bestBuy = c.Score; }
                    else { sellCount++; if (c.Score > bestSell) bestSell = c.Score; }
                }

                bool? dominantBull = null;
                if (buyCount > 0 && sellCount > 0)
                {
                    if (Math.Abs(bestBuy - bestSell) < _directionDominanceMargin) continue;
                    dominantBull = bestBuy > bestSell;
                }

                Candidate slotBest = null;
                double slotScore = -1;
                int dominantCount = dominantBull.HasValue ? (dominantBull.Value ? buyCount : sellCount) : slot.Count;

                for (int i = 0; i < slot.Count; i++)
                {
                    Candidate c = slot[i];
                    if (dominantBull.HasValue && c.IsBullish != dominantBull.Value) continue;
                    double sc = c.Score;
                    if (dominantCount >= 2) sc *= _consensusBonus;
                    if (sc > slotScore) { slotScore = sc; slotBest = c; }
                }

                if (slotBest != null && slotScore > bestScore)
                {
                    best = slotBest;
                    bestScore = slotScore;
                }
            }

            if (best == null) return false;

            double finalScore = Math.Min(1.0, bestScore);
            if (finalScore < best.Threshold || finalScore < _globalMinScore || finalScore < _minConfidence)
                return false;

            TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;
            double entry = dir == TradeDirection.Buy ? symbol.Ask : symbol.Bid;
            SwingPoint referencePoint = best.Family == PatternFamily.Shark ? best.C : best.D;
            if (referencePoint == null) return false;

            double stop, tpDist;
            stop = dir == TradeDirection.Buy
                ? referencePoint.Price - atrNow * _slAtrMult
                : referencePoint.Price + atrNow * _slAtrMult;

            if (best.Family == PatternFamily.Shark || best.Family == PatternFamily.FiveZero)
            {
                double bc = Math.Abs(best.B.Price - best.C.Price);
                tpDist = Math.Max(bc * 0.5, atrNow * 1.2);
            }
            else
            {
                double cd = best.C != null && best.D != null ? Math.Abs(best.C.Price - best.D.Price) : atrNow;
                tpDist = Math.Max(cd * _tpCdMult, atrNow * 1.2);
            }

            double tp = dir == TradeDirection.Buy ? entry + tpDist : entry - tpDist;
            if (dir == TradeDirection.Buy && !(stop < entry && entry < tp)) return false;
            if (dir == TradeDirection.Sell && !(tp < entry && entry < stop)) return false;

            signal = new Signal
            {
                Direction = dir,
                EntryPrice = entry,
                StopLoss = stop,
                TakeProfit = tp,
                Confidence = finalScore,
                PatternName = best.PatternName,
                CompletionIndex = referencePoint.Index
            };
            return true;
        }

        private bool IsDefEnabled(PatternDef def)
        {
            bool enabled;
            if (!_enabled.TryGetValue(def.Name, out enabled)) return false;
            return enabled;
        }

        private Candidate Match(Bars bars, List<SwingPoint> pivots, int i, PatternDef def,
            double atr, double regime, double buyTrend, double sellTrend, int currentIndex)
        {
            bool isShark = def.Family == PatternFamily.Shark;
            bool isFiveZero = def.Family == PatternFamily.FiveZero;
            bool isAbcd = def.Family == PatternFamily.ABCD;

            if ((isShark || isFiveZero) && i < 1) return null;

            int idx = i;
            int maxNeeded = idx + ((isAbcd || isShark) ? 3 : 4);
            if (maxNeeded >= pivots.Count) return null;
            if ((isShark || isFiveZero) && idx - 1 < 0) return null;

            SwingPoint o = null, x = null, a, b, c = null, d = null;
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
                    if (bull && d.Price <= c.Price) return null;
                    if (bear && d.Price >= c.Price) return null;
                }
            }
            else if (isAbcd)
            {
                bull = (b.Price < a.Price) && (c.Price > b.Price) && (d.Price < c.Price);
                bear = (b.Price > a.Price) && (c.Price < b.Price) && (d.Price > c.Price);
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
            if (def.Family == PatternFamily.Reversal)
                trendScore = Math.Max(trendScore, _reversalTrendFloor);

            if (isShark)
            {
                double rAB = ab / xa;
                double rBC = bc / ox;
                if (!InFibRange(rAB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rBC, def.CIdeal, def.CMin, def.CMax)) return null;
                double s1 = RangeAwareRatioScore(rAB, def.BIdeal, def.BMin, def.BMax);
                double s2 = RangeAwareRatioScore(rBC, def.CIdeal, def.CMin, def.CMax);
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
                double s1 = RangeAwareRatioScore(rAB, def.BIdeal, def.BMin, def.BMax);
                double s2 = RangeAwareRatioScore(rBC, def.CIdeal, def.CMin, def.CMax);
                double s3 = RangeAwareRatioScore(rCD, def.XDIdeal, def.XDMin, def.XDMax);
                geometry = (s1 + s2 + s3) / 3.0;
            }
            else if (isAbcd)
            {
                if (ab <= 0 || bc <= 0 || cd <= 0) return null;
                double cRetrace = bc / ab;
                double abcdEquality = cd / ab;
                double bcProjection = cd / bc;

                if (cRetrace < 0.382 - _fibTolerance || cRetrace > 0.886 + _fibTolerance) return null;
                if (!InFibRange(abcdEquality, def.BIdeal, def.BMin, def.BMax)) return null;
                if (bcProjection < 1.13 - _fibTolerance || bcProjection > 2.618 + _fibTolerance) return null;

                double reciprocalIdeal = 1.0 / Math.Max(cRetrace, 0.0001);
                reciprocalIdeal = Math.Max(1.13, Math.Min(2.618, reciprocalIdeal));
                double sC = RangeAwareRatioScore(cRetrace, 0.618, 0.382, 0.886);
                double sEq = RangeAwareRatioScore(abcdEquality, 1.0, 0.90, 1.15);
                double sProj = RangeAwareRatioScore(bcProjection, reciprocalIdeal, 1.13, 2.618);
                geometry = sEq * 0.50 + sC * 0.25 + sProj * 0.25;
            }
            else if (def.Name == "Cypher")
            {
                double xc = Math.Abs(c.Price - x.Price);
                if (xc <= 0) return null;
                double xd = Math.Abs(d.Price - x.Price);
                double rAB = ab / xa;
                double rC = xc / xa;
                double rD = xd / xc;

                bool dSideOk = bull ? (d.Price > x.Price && d.Price < c.Price)
                                    : (d.Price < x.Price && d.Price > c.Price);
                if (!dSideOk) return null;

                if (!InFibRange(rAB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rC, def.CIdeal, def.CMin, def.CMax)) return null;
                if (!InFibRange(rD, def.XDIdeal, def.XDMin, def.XDMax)) return null;

                double s1 = RangeAwareRatioScore(rAB, def.BIdeal, def.BMin, def.BMax);
                double s2 = RangeAwareRatioScore(rC, def.CIdeal, def.CMin, def.CMax);
                double s3 = RangeAwareRatioScore(rD, def.XDIdeal, def.XDMin, def.XDMax);
                geometry = (s1 + s2 + s3) / 3.0;
            }
            else
            {
                double rB = ab / xa;
                double rC = bc / ab;
                double rD = cd / bc;
                double rXD = Math.Abs(d.Price - x.Price) / xa;

                if (!InFibRange(rB, def.BIdeal, def.BMin, def.BMax)) return null;
                if (!InFibRange(rC, def.CIdeal, def.CMin, def.CMax)) return null;
                if (!InFibRange(rD, def.DIdeal, def.DMin, def.DMax)) return null;
                if (!InFibRange(rXD, def.XDIdeal, def.XDMin, def.XDMax)) return null;

                double s1 = RangeAwareRatioScore(rB, def.BIdeal, def.BMin, def.BMax);
                double s2 = RangeAwareRatioScore(rC, def.CIdeal, def.CMin, def.CMax);
                double s3 = RangeAwareRatioScore(rD, def.DIdeal, def.DMin, def.DMax);
                double s4 = RangeAwareRatioScore(rXD, def.XDIdeal, def.XDMin, def.XDMax);
                geometry = (s1 + s2 + s3 + s4) / 4.0;
            }

            double score = geometry * 0.60 + trendScore * 0.25 + regime * 0.15;
            score *= def.Weight;
            score = Clamp01(score);

            return new Candidate
            {
                X = x,
                A = a,
                B = b,
                C = c,
                D = d,
                IsBullish = bull,
                Score = score,
                Threshold = def.Threshold,
                PatternName = def.Name,
                Family = def.Family
            };
        }

        private double RangeAwareRatioScore(double ratio, double ideal, double min, double max)
        {
            if (ideal <= 0) return _rangeBoundaryScore;
            double lo = max > 0 ? min - _fibTolerance : min;
            double hi = max > 0 ? max + _fibTolerance : max;
            if (max > 0 && (ratio < lo || ratio > hi)) return 0;

            double span;
            if (ratio <= ideal) span = Math.Max(ideal - lo, 0.0001);
            else span = Math.Max(hi - ideal, 0.0001);

            double normalized = Math.Min(1.0, Math.Abs(ratio - ideal) / span);
            double score = 1.0 - (1.0 - _rangeBoundaryScore) * normalized;
            return Clamp01(score);
        }

        private bool InFibRange(double r, double ideal, double min, double max)
        {
            if (max <= 0) return true;
            double lo = min - _fibTolerance;
            double hi = max + _fibTolerance;
            return r >= lo && r <= hi;
        }

        private static double Clamp01(double v)
        {
            if (v < 0) return 0;
            if (v > 1) return 1;
            return v;
        }

        private static void AppendClosedBarProvisionalPivot(List<SwingPoint> pivots, Bars bars, int currentIndex, double atr, double minMoveAtr)
        {
            if (pivots == null || pivots.Count == 0 || bars == null || currentIndex < 0 || currentIndex >= bars.Count || atr <= 0) return;

            SwingPoint last = pivots[pivots.Count - 1];
            if (last == null || last.Index >= currentIndex) return;

            bool nextIsHigh = !last.IsHigh;
            double price = nextIsHigh ? bars.HighPrices[currentIndex] : bars.LowPrices[currentIndex];
            if (price <= 0) return;
            if (Math.Abs(price - last.Price) < atr * Math.Max(0.10, minMoveAtr)) return;

            // Only use a completed-bar extreme and preserve alternating pivot structure.
            pivots.Add(new SwingPoint { Index = currentIndex, Price = price, IsHigh = nextIsHigh });
        }

        private static List<SwingPoint> BuildSwingPoints(Bars bars, int endIndex, int lookback, int depth)
        {
            var raw = new List<SwingPoint>();
            int from = Math.Max(depth, endIndex - lookback + 1);
            int to = Math.Min(endIndex - depth, bars.Count - 1 - depth);

            for (int i = from; i <= to; i++)
            {
                if (IsSwingHigh(bars, i, depth))
                    raw.Add(new SwingPoint { Index = i, Price = bars.HighPrices[i], IsHigh = true });
                else if (IsSwingLow(bars, i, depth))
                    raw.Add(new SwingPoint { Index = i, Price = bars.LowPrices[i], IsHigh = false });
            }

            return MergeAlternating(raw);
        }

        private static bool IsSwingHigh(Bars bars, int i, int depth)
        {
            double h = bars.HighPrices[i];
            for (int k = 1; k <= depth; k++)
            {
                if (i - k < 0 || i + k >= bars.Count) return false;
                if (bars.HighPrices[i - k] >= h || bars.HighPrices[i + k] >= h) return false;
            }
            return true;
        }

        private static bool IsSwingLow(Bars bars, int i, int depth)
        {
            double l = bars.LowPrices[i];
            for (int k = 1; k <= depth; k++)
            {
                if (i - k < 0 || i + k >= bars.Count) return false;
                if (bars.LowPrices[i - k] <= l || bars.LowPrices[i + k] <= l) return false;
            }
            return true;
        }

        private static List<SwingPoint> MergeAlternating(List<SwingPoint> raw)
        {
            var result = new List<SwingPoint>();
            foreach (var sp in raw)
            {
                if (result.Count == 0)
                {
                    result.Add(sp);
                    continue;
                }

                var last = result[result.Count - 1];
                if (last.IsHigh == sp.IsHigh)
                {
                    if ((sp.IsHigh && sp.Price > last.Price) || (!sp.IsHigh && sp.Price < last.Price))
                        result[result.Count - 1] = sp;
                }
                else
                {
                    result.Add(sp);
                }
            }
            return result;
        }
    }

    // ================================================================
    //  GridBasket
    // ================================================================
    public class GridBasket
    {
        public long Id;
        public TradeDirection Direction;
        public string PatternName;
        public long ParentPositionId;
        public double BaseEntry;
        public double BaseStop;
        public double BaseRisk;
        public double ParentVolume;
        public int LevelsOpened;
        public DateTime LastAddTime;
        public double WeightedEntry;
        public double TotalUnits;
        public double TargetPrice;
        public double StopPrice;
        public List<long> PositionIds = new List<long>();

        public double EntryAtr;
        public double PeakPrice;
        public double PeakProfitMoney;
        public bool BreakevenLocked;
        public bool TrailingLocked;
        public bool ScaledOut;
        public bool IsSynthetic;
        public int DayTag;
        public int DailyAdds;
        public DateTime LastProtectTime;
    }

    // ================================================================
    //  FibonacciMathCore — Golden-ratio higher-math engine
    // ================================================================
    public static class FibonacciMathCore
    {
        public const double Phi = 1.618033988749895;
        public const double Psi = -0.618033988749895;   // 1 - phi
        public const double Sqrt5 = 2.236067977499790;
        public const double PhiSquared = 2.618033988749895;
        public const double PhiCubed = 4.236067977499790;

        public static double FibonacciBinet(int n)
        {
            if (n < 0) n = -n;
            if (n == 0) return 0;
            return (Math.Pow(Phi, n) - Math.Pow(Psi, n)) / Sqrt5;
        }

        public static double GoldenLevelRatio(int level)
        {
            int n = Math.Max(1, level);
            double exponent = (n - 1) * 0.5 - 2.0;
            return Math.Pow(Phi, exponent);
        }

        public static double GoldenSizeMultiplier(int level)
        {
            return Math.Max(1.0, Math.Round(FibonacciBinet(Math.Max(1, level)), 4));
        }

        public static double GoldenRiskBudgetLevel(int level, double cap)
        {
            if (level < 1) return 0;
            double geo = cap / PhiSquared;
            double share = Math.Pow(1.0 / Phi, level - 1);
            return geo * share;
        }

        public static double GoldenRiskBudgetCumulative(int levels, double cap)
        {
            if (levels < 1 || cap <= 0) return 0;
            return cap * (1.0 - Math.Pow(1.0 / Phi, levels));
        }

        public static double GoldenTrailCompression(int level, double baseFib)
        {
            int n = Math.Max(1, level);
            double factor = Math.Pow(1.0 / Phi, n - 1);
            double min = 1.0 / PhiCubed;
            double result = baseFib * factor;
            if (result < min) result = min;
            return result;
        }

        public static double GoldenCooldownMultiplier(int level, double baseMinutes)
        {
            if (level < 1) return baseMinutes;
            double f = FibonacciBinet(level);
            if (f <= 0) f = 1;
            return baseMinutes * f;
        }
    }

    // ================================================================
    //  FibonacciGridEngine — grid spacing/sizing + basket pricing
    // ================================================================
    public static class FibonacciGridEngine
    {
        public static readonly double[] DefaultLevelFibs = { 0.382, 0.618, 0.786, 1.0, 1.272, 1.618, 2.618, 4.236 };
        public static readonly double[] DefaultSizeFibs = { 1, 1, 2, 3, 5, 8, 13, 21 };

        public static bool TryParseFibList(string s, out double[] values)
        {
            values = null;
            if (string.IsNullOrWhiteSpace(s)) return false;

            var parts = s.Split(new[] { ',', ';', ' ' }, StringSplitOptions.RemoveEmptyEntries);
            var list = new List<double>();
            foreach (var p in parts)
            {
                double v;
                if (!double.TryParse(p.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture, out v))
                    return false;
                if (v <= 0) return false;
                list.Add(v);
            }

            if (list.Count == 0) return false;
            values = list.ToArray();
            return true;
        }

        public static double[] EnsureLength(double[] arr, int n, bool padWithLast)
        {
            n = Math.Max(1, n);
            if (arr == null || arr.Length == 0)
            {
                var src = padWithLast ? DefaultSizeFibs : DefaultLevelFibs;
                return src.Take(n).ToArray();
            }
            if (arr.Length >= n) return arr.Take(n).ToArray();

            var r = new double[n];
            Array.Copy(arr, r, arr.Length);
            double fill = padWithLast ? arr[arr.Length - 1] : 1.0;
            for (int i = arr.Length; i < n; i++) r[i] = fill;
            return r;
        }

        public static double LevelDistance(int level, double baseRisk, double[] levelFibs, bool useGoldenMath)
        {
            double ratio;
            if (useGoldenMath)
            {
                ratio = FibonacciMathCore.GoldenLevelRatio(level);
            }
            else
            {
                int idx = Math.Max(0, level - 1);
                ratio = idx < (levelFibs != null ? levelFibs.Length : 0)
                    ? levelFibs[idx]
                    : FibonacciMathCore.GoldenLevelRatio(level);
            }
            return Math.Max(0.0, baseRisk * ratio);
        }

        public static double LevelSize(int level, double baseSize, double[] sizeFibs, bool useGoldenMath)
        {
            double mult;
            if (useGoldenMath)
            {
                mult = FibonacciMathCore.GoldenSizeMultiplier(level);
            }
            else
            {
                int idx = Math.Max(0, level - 1);
                mult = idx < (sizeFibs != null ? sizeFibs.Length : 0)
                    ? sizeFibs[idx]
                    : FibonacciMathCore.GoldenSizeMultiplier(level);
            }
            return Math.Max(0.0, baseSize * mult);
        }

        public static double BasketTargetPrice(TradeDirection dir, double weightedEntry, double baseRisk, double profitFib)
        {
            return dir == TradeDirection.Buy ? weightedEntry + baseRisk * profitFib : weightedEntry - baseRisk * profitFib;
        }

        public static double BasketStopPrice(TradeDirection dir, double baseEntry, double baseRisk, double stopFib)
        {
            return dir == TradeDirection.Buy ? baseEntry - baseRisk * stopFib : baseEntry + baseRisk * stopFib;
        }
    }

    // ================================================================
    //  PerformanceTracker
    // ================================================================
    public class PerformanceTracker
    {
        private readonly Robot _robot;
        public double InitialEquity;

        private int _trades;
        private int _wins;
        private int _losses;
        private double _sumR;
        private double _sumPnl;
        private double _bestR;
        private double _worstR;

        public PerformanceTracker(Robot robot)
        {
            _robot = robot;
        }

        public void AddTrade(DateTime time, double r, double pnl, double pips)
        {
            _trades++;
            _sumR += r;
            _sumPnl += pnl;
            if (pnl >= 0) _wins++; else _losses++;
            if (_trades == 1 || r > _bestR) _bestR = r;
            if (_trades == 1 || r < _worstR) _worstR = r;
        }

        public void PrintReport(double equity)
        {
            if (_robot == null) return;

            double winRate = _trades > 0 ? (double)_wins / _trades * 100.0 : 0;
            double avgR = _trades > 0 ? _sumR / _trades : 0;
            double net = equity - InitialEquity;
            double netPct = InitialEquity > 0 ? net / InitialEquity * 100.0 : 0;

            _robot.Print("");
            _robot.Print("================================================================");
            _robot.Print("           PERFORMANCE REPORT");
            _robot.Print("================================================================");
            _robot.Print("  Initial Equity : {0:F2}", InitialEquity);
            _robot.Print("  Current Equity : {0:F2}", equity);
            _robot.Print("  Net PnL        : {0:F2} USD ({1:F2}%)", net, netPct);
            _robot.Print("  Trades         : {0}", _trades);
            _robot.Print("  Wins / Losses  : {0} / {1}", _wins, _losses);
            _robot.Print("  Win Rate       : {0:F1}%", winRate);
            _robot.Print("  Avg R          : {0:F2}", avgR);
            _robot.Print("  Expectancy     : {0:F2}R", avgR);
            _robot.Print("  Best R         : {0:F2}", _bestR);
            _robot.Print("  Worst R        : {0:F2}", _worstR);
            _robot.Print("  Total PnL      : {0:F2} USD", _sumPnl);
            _robot.Print("================================================================");
            _robot.Print("");
        }
    }
}
