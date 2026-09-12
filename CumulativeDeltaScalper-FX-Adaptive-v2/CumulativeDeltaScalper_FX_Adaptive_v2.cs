// ===================================================================
//  CumulativeDeltaScalper_FX_Adaptive_v2
//  Deep-repaired multi-FX edition derived from Original Candidate K.
//
//  Main upgrades:
//  - Adaptive normalized pressure score (-100..+100 per bar), removing
//    raw-tick-count scale distortion across brokers, pairs and timeframes.
//  - Closed-bar ATR/HTF EMA/ADX/DMI reads to avoid using forming bars.
//  - Portfolio single-position lock by shared label (default ON).
//  - O(1) runtime daily accounting; History is rebuilt only at start/day reset.
//  - Restart recovery for open-position time, direction, risk and breakeven state.
//  - Risk hard-cap verification with Symbol.AmountRisked after volume rounding.
//  - Margin guard with Symbol.GetEstimatedMargin.
//  - Cost-aware spread/ATR and effective RR filters.
//  - Broker market-hours/trading-enabled checks and min-distance adaptation.
//  - R-based breakeven + optional ATR trailing with broker-distance validation.
//  - Automatic broad liquidity sessions by currency group + rollover blackout.
//
//  Strategy constraints:
//  - No hedging, grid, martingale, DCA, recovery or loss averaging.
//  - One open bot position across all configured FX symbols by default.
//  - Every entry carries SL and TP.
// ===================================================================

using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public enum CdsFxRiskModeV2
    {
        FixedLots = 0,
        RiskPercent = 1,
        FixedMoneyRisk = 2
    }

    public enum CdsPressureMode
    {
        Hybrid = 0,
        TickImbalance = 1,
        CandlePressure = 2
    }

    public enum CdsSessionMode
    {
        Off = 0,
        ManualUtc = 1,
        AutoCurrencyLiquidity = 2
    }

    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class CumulativeDeltaScalper_FX_Adaptive_v2 : Robot
    {
        private const string Prefix = "[CDS-FX-Adaptive-v2] ";
        private const int AtrPeriod = 14;
        private const int EmaPeriod = 50;
        private const int AdxPeriod = 14;

        private static readonly object PortfolioOrderLock = new object();

        private const string DefaultFxPairs =
            "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD," +
            "CADCHF,CADJPY," +
            "CHFJPY," +
            "EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD," +
            "GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD," +
            "NZDCAD,NZDCHF,NZDJPY,NZDUSD," +
            "USDCAD,USDCHF,USDJPY";

        private static readonly string[] KnownCurrencies =
        {
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"
        };

        // ============================================================
        // General
        // ============================================================

        [Parameter("Bot Label", DefaultValue = "CDS_FX_ADAPTIVE_V2", Group = "General")]
        public string TradeLabel { get; set; }

        [Parameter("Debug Logging", DefaultValue = false, Group = "General")]
        public bool DebugLogging { get; set; }

        [Parameter("Summary Logging", DefaultValue = true, Group = "General")]
        public bool SummaryLogging { get; set; }

        [Parameter("Portfolio Single Position", DefaultValue = true, Group = "General")]
        public bool PortfolioSinglePosition { get; set; }

        [Parameter("Use Allowed FX List", DefaultValue = true, Group = "General")]
        public bool UseAllowedFxList { get; set; }

        [Parameter("Allowed FX Pairs", DefaultValue = DefaultFxPairs, Group = "General")]
        public string AllowedFxPairs { get; set; }

        [Parameter("Allow M1", DefaultValue = true, Group = "General")]
        public bool AllowM1 { get; set; }

        [Parameter("Allow M5", DefaultValue = true, Group = "General")]
        public bool AllowM5 { get; set; }

        [Parameter("Allow M15", DefaultValue = true, Group = "General")]
        public bool AllowM15 { get; set; }

        [Parameter("Allow M30", DefaultValue = true, Group = "General")]
        public bool AllowM30 { get; set; }

        // ============================================================
        // Adaptive pressure / delta proxy
        // ============================================================

        [Parameter("Pressure Mode", DefaultValue = CdsPressureMode.Hybrid, Group = "Pressure")]
        public CdsPressureMode PressureMode { get; set; }

        [Parameter("Pressure Window", DefaultValue = 8, MinValue = 3, MaxValue = 30, Group = "Pressure")]
        public int PressureWindow { get; set; }

        [Parameter("Cumulative Threshold", DefaultValue = 180.0, MinValue = 20.0, Step = 10.0, Group = "Pressure")]
        public double CumulativePressureThreshold { get; set; }

        [Parameter("Min Directional Bars", DefaultValue = 2, MinValue = 1, MaxValue = 5, Group = "Pressure")]
        public int MinDirectionalBars { get; set; }

        [Parameter("Min Momentum Score", DefaultValue = 12.0, MinValue = 0.0, Step = 1.0, Group = "Pressure")]
        public double MinMomentumScore { get; set; }

        [Parameter("Min Tick Samples/Bar", DefaultValue = 8, MinValue = 0, Group = "Pressure")]
        public int MinTickSamplesPerBar { get; set; }

        [Parameter("Hybrid Tick Weight", DefaultValue = 0.65, MinValue = 0.0, MaxValue = 1.0, Step = 0.05, Group = "Pressure")]
        public double HybridTickWeight { get; set; }

        [Parameter("Candle Close Weight", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 1.0, Step = 0.05, Group = "Pressure")]
        public double CandleCloseLocationWeight { get; set; }

        // ============================================================
        // Trend / volatility filters
        // ============================================================

        [Parameter("Min Confirmations", DefaultValue = 4, MinValue = 0, MaxValue = 5, Group = "Filters")]
        public int MinConfirmations { get; set; }

        [Parameter("Use HTF EMA", DefaultValue = true, Group = "Filters")]
        public bool UseHtfEmaFilter { get; set; }

        [Parameter("HTF Timeframe", DefaultValue = "Minute15", Group = "Filters")]
        public string HtfTimeFrameName { get; set; }

        [Parameter("EMA Slope Bars", DefaultValue = 3, MinValue = 1, MaxValue = 20, Group = "Filters")]
        public int EmaSlopeBars { get; set; }

        [Parameter("ADX Threshold", DefaultValue = 17.0, MinValue = 0.0, Step = 0.5, Group = "Filters")]
        public double AdxThreshold { get; set; }

        [Parameter("Require DMI Direction", DefaultValue = true, Group = "Filters")]
        public bool RequireDmiDirection { get; set; }

        [Parameter("Min ATR (Pips)", DefaultValue = 0.0, MinValue = 0.0, Step = 0.1, Group = "Filters")]
        public double MinAtrPips { get; set; }

        [Parameter("Max ATR (Pips, 0=Off)", DefaultValue = 0.0, MinValue = 0.0, Step = 0.5, Group = "Filters")]
        public double MaxAtrPips { get; set; }

        [Parameter("Min ATR/Spread Ratio", DefaultValue = 4.0, MinValue = 0.0, Step = 0.25, Group = "Filters")]
        public double MinAtrToSpreadRatio { get; set; }

        // ============================================================
        // Session / execution
        // ============================================================

        [Parameter