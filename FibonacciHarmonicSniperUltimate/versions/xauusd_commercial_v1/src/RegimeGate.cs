using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal sealed class RegimeGate
    {
        private readonly double _minAtrRegime;
        private readonly double _minRelativeTickVolume;
        private readonly int _volumeAverageBars;
        private readonly double _maxSpreadAtrRatio;
        private readonly double _maxFlashVolatilityRatio;
        private readonly int _emaFastPeriod;
        private readonly int _emaSlowPeriod;
        private readonly int _emaSlopeBars;
        private readonly bool _useTradingWindow;
        private readonly int _sessionStartHour;
        private readonly int _sessionStartMinute;
        private readonly int _sessionEndHour;
        private readonly int _sessionEndMinute;
        private readonly bool _blockRollover;
        private readonly int _rolloverStartHour;
        private readonly int _rolloverStartMinute;
        private readonly int _rolloverEndHour;
        private readonly int _rolloverEndMinute;

        public RegimeGate(
            double minAtrRegime,
            double minRelativeTickVolume,
            int volumeAverageBars,
            double maxSpreadAtrRatio,
            double maxFlashVolatilityRatio,
            int emaFastPeriod,
            int emaSlowPeriod,
            int emaSlopeBars,
            bool useTradingWindow,
            int sessionStartHour,
            int sessionStartMinute,
            int sessionEndHour,
            int sessionEndMinute,
            bool blockRollover,
            int rolloverStartHour,
            int rolloverStartMinute,
            int rolloverEndHour,
            int rolloverEndMinute)
        {
            _minAtrRegime = minAtrRegime;
            _minRelativeTickVolume = minRelativeTickVolume;
            _volumeAverageBars = volumeAverageBars;
            _maxSpreadAtrRatio = maxSpreadAtrRatio;
            _maxFlashVolatilityRatio = maxFlashVolatilityRatio;
            _emaFastPeriod = emaFastPeriod;
            _emaSlowPeriod = emaSlowPeriod;
            _emaSlopeBars = emaSlopeBars;
            _useTradingWindow = useTradingWindow;
            _sessionStartHour = sessionStartHour;
            _sessionStartMinute = sessionStartMinute;
            _sessionEndHour = sessionEndHour;
            _sessionEndMinute = sessionEndMinute;
            _blockRollover = blockRollover;
            _rolloverStartHour = rolloverStartHour;
            _rolloverStartMinute = rolloverStartMinute;
            _rolloverEndHour = rolloverEndHour;
            _rolloverEndMinute = rolloverEndMinute;
        }

        public RegimeSnapshot Evaluate(Bars bars, Symbol symbol, int index, TradeType direction, DateTime serverUtc)
        {
            var result = new RegimeSnapshot();

            if (_useTradingWindow && !MarketMath.IsWithinDailyWindow(serverUtc, _sessionStartHour, _sessionStartMinute, _sessionEndHour, _sessionEndMinute))
                return Reject(result, "outside-trading-window");

            if (_blockRollover && MarketMath.IsWithinDailyWindow(serverUtc, _rolloverStartHour, _rolloverStartMinute, _rolloverEndHour, _rolloverEndMinute))
                return Reject(result, "rollover-blackout");

            result.AtrFast = MarketMath.Atr(bars, index, 14);
            result.AtrSlow = MarketMath.Atr(bars, index, 50);
            if (result.AtrFast <= symbol.PipSize || result.AtrSlow <= symbol.PipSize)
                return Reject(result, "atr-unavailable");

            result.AtrRegime = result.AtrFast / result.AtrSlow;
            if (result.AtrRegime < _minAtrRegime)
                return Reject(result, "low-volatility-regime");

            result.RelativeTickVolume = MarketMath.RelativeTickVolume(bars, index, _volumeAverageBars);
            if (result.RelativeTickVolume < _minRelativeTickVolume)
                return Reject(result, "low-relative-tick-volume");

            result.SpreadAtrRatio = (symbol.Ask - symbol.Bid) / result.AtrFast;
            if (result.SpreadAtrRatio > _maxSpreadAtrRatio)
                return Reject(result, "spread-too-wide");

            result.FlashVolatilityRatio = MarketMath.TrueRange(bars, index) / result.AtrFast;
            if (_maxFlashVolatilityRatio > 0.0 && result.FlashVolatilityRatio > _maxFlashVolatilityRatio)
                return Reject(result, "flash-volatility");

            result.EmaFast = MarketMath.Ema(bars, index, _emaFastPeriod);
            result.EmaSlow = MarketMath.Ema(bars, index, _emaSlowPeriod);
            double priorFast = MarketMath.Ema(bars, Math.Max(0, index - _emaSlopeBars), _emaFastPeriod);
            result.EmaFastSlope = result.EmaFast - priorFast;

            double close = bars.ClosePrices[index];
            if (direction == TradeType.Buy)
                result.TrendAligned = close >= result.EmaFast && result.EmaFast >= result.EmaSlow && result.EmaFastSlope > 0.0;
            else
                result.TrendAligned = close <= result.EmaFast && result.EmaFast <= result.EmaSlow && result.EmaFastSlope < 0.0;

            result.Allowed = true;
            result.RejectReason = string.Empty;
            return result;
        }

        private static RegimeSnapshot Reject(RegimeSnapshot result, string reason)
        {
            result.Allowed = false;
            result.RejectReason = reason;
            return result;
        }
    }
}
