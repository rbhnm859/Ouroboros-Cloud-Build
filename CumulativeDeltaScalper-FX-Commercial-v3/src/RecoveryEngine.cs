using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private bool _dailyStateRecovered;

        private void EnsureDailyStateRecovered()
        {
            if (_dailyStateRecovered)
                return;

            var dayStart = Server.Time.Date;
            var closedToday = History
                .Where(h => h.Label == TradeLabel &&
                            (PortfolioSinglePosition || h.SymbolName == SymbolName) &&
                            h.ClosingTime >= dayStart && h.ClosingTime < dayStart.AddDays(1))
                .OrderBy(h => h.ClosingTime)
                .ToList();

            _currentDay = dayStart;
            _dailyRealized = closedToday.Sum(h => h.NetProfit);
            _tradesToday = closedToday.Count + Positions.Count(p =>
                p.Label == TradeLabel &&
                (PortfolioSinglePosition || p.SymbolName == SymbolName) &&
                p.EntryTime >= dayStart);

            // Account.Balance includes today's closed trades. Subtract them to reconstruct the day's starting balance.
            _dayStartEquity = Math.Max(1.0, Account.Balance - _dailyRealized);
            _consecutiveLosses = 0;
            _nextTradeTime = DateTime.MinValue;

            for (var i = closedToday.Count - 1; i >= 0; i--)
            {
                var trade = closedToday[i];
                if (trade.NetProfit < 0)
                {
                    _consecutiveLosses++;
                    if (_nextTradeTime == DateTime.MinValue && LossCooldownMinutes > 0)
                        _nextTradeTime = trade.ClosingTime.AddMinutes(LossCooldownMinutes);
                }
                else if (trade.NetProfit > 0)
                {
                    break;
                }
            }

            _dailyStateRecovered = true;
            DebugLog("RECOVER day={0:yyyy-MM-dd} realized={1:F2} trades={2} consecutiveLosses={3} nextTrade={4:o}",
                dayStart, _dailyRealized, _tradesToday, _consecutiveLosses, _nextTradeTime);
        }

        private TradeState EnsureTradeState(Position position)
        {
            TradeState state;
            if (_tradeStates.TryGetValue(position.Id, out state))
                return state;

            var stopPips = position.StopLoss.HasValue && Symbol.PipSize > 0
                ? Math.Abs(position.EntryPrice - position.StopLoss.Value) / Symbol.PipSize
                : Math.Max(0.1, _atr == null || Bars.Count < 2 ? 1.0 : _atr.Result[Bars.Count - 2] / Symbol.PipSize * StopAtrMultiplier);

            var entryIndex = FindBarIndexAtOrBefore(position.EntryTime);
            state = new TradeState
            {
                PositionId = position.Id,
                EntryBarIndex = entryIndex,
                InitialStopPips = stopPips,
                InitialRiskMoney = Symbol.AmountRisked(position.VolumeInUnits, stopPips) + EstimateRoundTripCommissionMoney(position.VolumeInUnits),
                BestFavorablePips = Math.Max(0.0, GetFavorablePips(position)),
                OppositePressureBars = 0,
                BreakevenApplied = IsStopAtOrBeyondEntry(position),
                TrailingActivated = false
            };
            _tradeStates[position.Id] = state;
            DebugLog("RECOVER position id={0} entryBar={1} stop={2:F2} risk={3:F2}", position.Id, entryIndex, stopPips, state.InitialRiskMoney);
            return state;
        }

        private int FindBarIndexAtOrBefore(DateTime time)
        {
            for (var i = Bars.Count - 2; i >= 0; i--)
            {
                if (Bars.OpenTimes[i] <= time)
                    return i;
            }
            return Math.Max(0, Bars.Count - 2);
        }

        private bool IsStopAtOrBeyondEntry(Position position)
        {
            if (!position.StopLoss.HasValue)
                return false;
            return position.TradeType == TradeType.Buy
                ? position.StopLoss.Value >= position.EntryPrice
                : position.StopLoss.Value <= position.EntryPrice;
        }
    }
}
