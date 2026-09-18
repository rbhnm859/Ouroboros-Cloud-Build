using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Major FX Adaptive Mode", Group = "Major FX", DefaultValue = true)]
        public bool MajorFxAdaptiveMode { get; set; }

        [Parameter("ATR Regime Lookback", Group = "Major FX", DefaultValue = 60, MinValue = 20, MaxValue = 240)]
        public int AtrRegimeLookback { get; set; }

        [Parameter("Min ATR Regime Ratio", Group = "Major FX", DefaultValue = 0.60, MinValue = 0.30, MaxValue = 1.00, Step = 0.05)]
        public double MinAtrRegimeRatio { get; set; }

        [Parameter("Max ATR Regime Ratio", Group = "Major FX", DefaultValue = 2.20, MinValue = 1.10, MaxValue = 5.00, Step = 0.05)]
        public double MaxAtrRegimeRatio { get; set; }

        [Parameter("Adaptive Profile Logging", Group = "Major FX", DefaultValue = false)]
        public bool AdaptiveProfileLogging { get; set; }

        private sealed class FxAdaptiveProfile
        {
            public string Name { get; set; }
            public double PressureScale { get; set; }
            public double AdxOffset { get; set; }
            public double BreakoutScale { get; set; }
            public double StopScale { get; set; }
            public double RewardScale { get; set; }
            public double SpreadCapScale { get; set; }
            public double AtrSpreadScale { get; set; }
            public double ExtensionScale { get; set; }
            public double EntryCandleScale { get; set; }
            public double PullbackDepthScale { get; set; }
            public double MinMomentumR { get; set; }
        }

        private FxAdaptiveProfile _cachedFxProfile;
        private string _cachedFxProfilePair = string.Empty;
        private bool _cachedFxAdaptiveMode;
        private int _cachedAtrRegimeIndex = -1;
        private int _cachedAtrRegimeLookback = -1;
        private double _cachedAtrRegimeRatio = 1.0;

        private FxAdaptiveProfile GetFxAdaptiveProfile()
        {
            var pair = CanonicalSymbolName();
            if (_cachedFxProfile != null && _cachedFxProfilePair == pair && _cachedFxAdaptiveMode == MajorFxAdaptiveMode)
                return _cachedFxProfile;

            _cachedFxProfilePair = pair;
            _cachedFxAdaptiveMode = MajorFxAdaptiveMode;

            if (!MajorFxAdaptiveMode)
            {
                _cachedFxProfile = BaselineFxProfile();
                return _cachedFxProfile;
            }

            if (pair == "EURUSD" || pair == "USDJPY")
            {
                _cachedFxProfile = new FxAdaptiveProfile
                {
                    Name = "Tier1Major",
                    PressureScale = 0.95,
                    AdxOffset = -1.0,
                    BreakoutScale = 0.95,
                    StopScale = 1.00,
                    RewardScale = 1.00,
                    SpreadCapScale = 0.80,
                    AtrSpreadScale = 1.10,
                    ExtensionScale = 0.95,
                    EntryCandleScale = 0.95,
                    PullbackDepthScale = 0.90,
                    MinMomentumR = 0.07
                };
                return _cachedFxProfile;
            }

            if (pair == "GBPUSD" || pair == "USDCHF" || pair == "USDCAD" || pair == "AUDUSD" || pair == "NZDUSD")
            {
                _cachedFxProfile = new FxAdaptiveProfile
                {
                    Name = "Major",
                    PressureScale = 1.00,
                    AdxOffset = 0.0,
                    BreakoutScale = 1.00,
                    StopScale = 1.05,
                    RewardScale = 1.02,
                    SpreadCapScale = 0.90,
                    AtrSpreadScale = 1.05,
                    ExtensionScale = 0.90,
                    EntryCandleScale = 0.95,
                    PullbackDepthScale = 0.90,
                    MinMomentumR = 0.08
                };
                return _cachedFxProfile;
            }

            if (pair.EndsWith("JPY", StringComparison.Ordinal) || pair.StartsWith("JPY", StringComparison.Ordinal))
            {
                _cachedFxProfile = new FxAdaptiveProfile
                {
                    Name = "JpyCross",
                    PressureScale = 1.05,
                    AdxOffset = 1.0,
                    BreakoutScale = 1.10,
                    StopScale = 1.12,
                    RewardScale = 1.05,
                    SpreadCapScale = 1.10,
                    AtrSpreadScale = 1.00,
                    ExtensionScale = 0.85,
                    EntryCandleScale = 0.90,
                    PullbackDepthScale = 0.80,
                    MinMomentumR = 0.10
                };
                return _cachedFxProfile;
            }

            _cachedFxProfile = new FxAdaptiveProfile
            {
                Name = "Cross",
                PressureScale = 1.08,
                AdxOffset = 1.0,
                BreakoutScale = 1.12,
                StopScale = 1.10,
                RewardScale = 1.03,
                SpreadCapScale = 1.15,
                AtrSpreadScale = 1.00,
                ExtensionScale = 0.85,
                EntryCandleScale = 0.90,
                PullbackDepthScale = 0.80,
                MinMomentumR = 0.10
            };
            return _cachedFxProfile;
        }

        private static FxAdaptiveProfile BaselineFxProfile()
        {
            return new FxAdaptiveProfile
            {
                Name = "Baseline",
                PressureScale = 1.0,
                AdxOffset = 0.0,
                BreakoutScale = 1.0,
                StopScale = 1.0,
                RewardScale = 1.0,
                SpreadCapScale = 1.0,
                AtrSpreadScale = 1.0,
                ExtensionScale = 1.0,
                EntryCandleScale = 1.0,
                PullbackDepthScale = 1.0,
                MinMomentumR = 0.08
            };
        }

        private double GetAtrRegimeRatio(int index)
        {
            if (_atr == null || index <= 1)
                return 1.0;

            if (_cachedAtrRegimeIndex == index && _cachedAtrRegimeLookback == AtrRegimeLookback)
                return _cachedAtrRegimeRatio;

            var current = _atr.Result[index];
            if (current <= 0 || double.IsNaN(current) || double.IsInfinity(current))
            {
                _cachedAtrRegimeIndex = index;
                _cachedAtrRegimeLookback = AtrRegimeLookback;
                _cachedAtrRegimeRatio = 1.0;
                return _cachedAtrRegimeRatio;
            }

            var start = Math.Max(1, index - Math.Max(20, AtrRegimeLookback));
            double sum = 0.0;
            int count = 0;
            for (var i = start; i < index; i++)
            {
                var value = _atr.Result[i];
                if (value > 0 && !double.IsNaN(value) && !double.IsInfinity(value))
                {
                    sum += value;
                    count++;
                }
            }

            var ratio = 1.0;
            if (count >= 10)
            {
                var average = sum / count;
                if (average > 0)
                    ratio = current / average;
            }

            _cachedAtrRegimeIndex = index;
            _cachedAtrRegimeLookback = AtrRegimeLookback;
            _cachedAtrRegimeRatio = ratio;
            return ratio;
        }

        private bool PassAdaptiveFxRegime(int index)
        {
            if (!MajorFxAdaptiveMode)
                return true;

            var ratio = GetAtrRegimeRatio(index);
            var pass = ratio >= MinAtrRegimeRatio && ratio <= MaxAtrRegimeRatio;
            if (!pass && AdaptiveProfileLogging)
                Print("[V3 FX ADAPT] regime blocked pair={0} ratio={1:F2} allowed={2:F2}-{3:F2}", CanonicalSymbolName(), ratio, MinAtrRegimeRatio, MaxAtrRegimeRatio);
            return pass;
        }

        private double GetRegimeSignalScale(int index)
        {
            if (!MajorFxAdaptiveMode)
                return 1.0;
            var ratio = GetAtrRegimeRatio(index);
            if (ratio < 0.85)
                return 1.08;
            if (ratio > 1.55)
                return 1.06;
            return 1.0;
        }

        private double GetRegimeBreakoutScale(int index)
        {
            if (!MajorFxAdaptiveMode)
                return 1.0;
            var ratio = GetAtrRegimeRatio(index);
            if (ratio > 1.55)
                return 1.15;
            if (ratio < 0.85)
                return 1.05;
            return 1.0;
        }

        private double GetRegimeStopScale(int index)
        {
            if (!MajorFxAdaptiveMode)
                return 1.0;
            var ratio = GetAtrRegimeRatio(index);
            if (ratio > 1.55)
                return 1.10;
            if (ratio < 0.85)
                return 0.95;
            return 1.0;
        }

        private double GetRegimeExtensionScale(int index)
        {
            if (!MajorFxAdaptiveMode)
                return 1.0;
            var ratio = GetAtrRegimeRatio(index);
            if (ratio > 1.55)
                return 0.85;
            if (ratio < 0.85)
                return 0.90;
            return 1.0;
        }

        private double EffectiveMinAveragePressure(int index)
        {
            var profile = GetFxAdaptiveProfile();
            return MinAveragePressure * profile.PressureScale * GetRegimeSignalScale(index);
        }

        private double EffectiveMinLastPressure(int index)
        {
            var profile = GetFxAdaptiveProfile();
            return MinLastPressure * profile.PressureScale * GetRegimeSignalScale(index);
        }

        private double EffectiveMinAdx()
        {
            return Math.Max(5.0, MinAdx + GetFxAdaptiveProfile().AdxOffset);
        }

        private double EffectiveBreakoutBufferAtr(int index)
        {
            return BreakoutBufferAtr * GetFxAdaptiveProfile().BreakoutScale * GetRegimeBreakoutScale(index);
        }

        private double EffectiveMaxEntryCandleAtr(int index)
        {
            return MaxEntryCandleAtr * GetFxAdaptiveProfile().EntryCandleScale * GetRegimeExtensionScale(index);
        }

        private double EffectiveMaxEmaExtensionAtr(int index)
        {
            return MaxEmaExtensionAtr * GetFxAdaptiveProfile().ExtensionScale * GetRegimeExtensionScale(index);
        }

        private double EffectivePullbackSlowPenetrationAtr()
        {
            return PullbackSlowPenetrationAtr * GetFxAdaptiveProfile().PullbackDepthScale;
        }

        private double EffectiveMinMomentumR()
        {
            return GetFxAdaptiveProfile().MinMomentumR;
        }

        private double EffectiveMaxSpreadPips()
        {
            return MaxSpreadPips * GetFxAdaptiveProfile().SpreadCapScale;
        }

        private double EffectiveMinAtrToSpreadRatio()
        {
            return MinAtrToSpreadRatio * GetFxAdaptiveProfile().AtrSpreadScale;
        }

        private double EffectiveStopAtrMultiplier(int index)
        {
            return StopAtrMultiplier * GetFxAdaptiveProfile().StopScale * GetRegimeStopScale(index);
        }

        private double EffectiveTargetRewardRisk(int index)
        {
            var regimeRewardScale = GetAtrRegimeRatio(index) > 1.55 ? 1.05 : 1.0;
            return TargetRewardRisk * GetFxAdaptiveProfile().RewardScale * regimeRewardScale;
        }

        private void LogAdaptiveFxProfile(int index)
        {
            if (!AdaptiveProfileLogging)
                return;
            var profile = GetFxAdaptiveProfile();
            Print("[V3 FX ADAPT] pair={0} profile={1} atrRegime={2:F2} avgP={3:F1} lastP={4:F1} adx={5:F1} spreadCap={6:F2} atrSpread={7:F2} stopATR={8:F2} targetRR={9:F2}",
                CanonicalSymbolName(), profile.Name, GetAtrRegimeRatio(index), EffectiveMinAveragePressure(index), EffectiveMinLastPressure(index), EffectiveMinAdx(), EffectiveMaxSpreadPips(), EffectiveMinAtrToSpreadRatio(), EffectiveStopAtrMultiplier(index), EffectiveTargetRewardRisk(index));
        }
    }
}
