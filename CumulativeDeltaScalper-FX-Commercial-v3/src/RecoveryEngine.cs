using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private bool _dailyStateRecovered;
        private DateTime _recoveredDay = DateTime.MinValue;

        // Rebuild authoritative account state before every entry decision. History-derived recovery
        // may EXTEND an existing local lockout but must never shorten one (for example an OnException
        // circuit-breaker lockout that is not represented in trade history).
        private void EnsureDailyStateRecovered()
        {
            var dayStart = Server.Time.Date;
            var firstSyncForDay = !_dailyStateRecovered || _recoveredDay != dayStart;
            var existingLocalLockout = _nextTradeTime;

            var closedToday = History
                .Where(h => h.Label == TradeLabel &&
                            (PortfolioSinglePosition || h.SymbolName == SymbolName) &&
                            h.ClosingTime >= dayStart && h.ClosingTime < dayStart.AddDays(1))
                .OrderBy(h => h.ClosingTime)
                .ToList();

            var openToday = Positions
                .Where(p => p.Label == TradeLabel &&
                            (PortfolioSinglePosition || p.SymbolName == SymbolName) &&
                            p.EntryTime >= dayStart)
                .ToList();

            _currentDay = dayStart;
            _dailyRealized = closedToday.Sum(h => h.NetProfit);
            _tradesToday = closedToday.Count + openToday.Count;

            // Account.Balance already includes today's closed PnL. Removing today's realised PnL
            // reconstructs the start-of-day balance without allowing a restart to reset the loss cap.
            _dayStartEquity = Math.Max(1.0, Account.Balance - _dailyRealized);
            _consecutiveLosses = 0;
            var recoveredLossLockout = DateTime.MinValue;

            for (var i = closedToday.Count - 1; i >= 0; i--)
            {
                var trade = closedToday[i];
                if (trade.NetProfit < 0)
                {
                    _consecutiveLosses++;
                    if (recoveredLossLockout == DateTime.MinValue && LossCooldownMinutes > 0)
                        recoveredLossLockout = trade.ClosingTime.AddMinutes(LossCooldownMinutes);
                }
                else if (trade.NetProfit > 0)
                {
                    break;
                }
            }

            _nextTradeTime = existingLocalLockout > recoveredLossLockout
                ? existingLocalLockout
                : recoveredLossLockout;

            // Recover current-symbol bar cooldown. Portfolio trade-count/loss state is shared through
            // History, but a bar index is chart-specific and therefore recovered only from entries on
            // this symbol.
            var latestOwnEntry = DateTime.MinValue;
            foreach (var trade in closedToday.Where(h => h.SymbolName == SymbolName))
                if (trade.EntryTime > latestOwnEntry)
                    latestOwnEntry = trade.EntryTime;

            foreach (var position in Positions.Where(p => p.Label == TradeLabel && p.SymbolName == SymbolName))
                if (position.EntryTime > latestOwnEntry)
                    latestOwnEntry = position.EntryTime;

            if (latestOwnEntry == DateTime.MinValue && firstSyncForDay)
            {
                var latestHistoricalOwn = History
                    .Where(h => h.Label == TradeLabel && h.SymbolName == SymbolName)
                    .OrderByDescending(h => h.EntryTime)
                    .FirstOrDefault();
                if (latestHistoricalOwn != null)
                    latestOwnEntry = latestHistoricalOwn.EntryTime;
            }

            if (latestOwnEntry != DateTime.MinValue)
                _lastEntryBarIndex = FindBarIndexAtOrBefore(latestOwnEntry);
            else if (firstSyncForDay)
                _lastEntryBarIndex = -1000000;

            _dailyStateRecovered = true;
            _recoveredDay = dayStart;
            DebugLog("SYNC day={0:yyyy-MM-dd} realized={1:F2} trades={2} consecutiveLosses={3} nextTrade={4:o} lastEntryBar={5}",
                dayStart, _dailyRealized, _tradesToday, _consecutiveLosses, _nextTradeTime, _lastEntryBarIndex);
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
                InitialRiskMoney = Symbol.AmountRisked(position.VolumeInUnits, stopPips) + EstimateRoundTripCommissionMoney(position.VolumeInUnits) + EstimateSlippageReserveMoney(position.VolumeInUnits),
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
