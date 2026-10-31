using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    // Protected risk/session/safety support layer.
    // This file remains part of the same partial Robot and must preserve fail-closed behavior.
    public partial class HarmonyBotV71
    {
        // ---------------- Risk / session / safety ----------------

        private bool IsInstitutionalSession(DateTime utc)
        {
            utc = DateTime.SpecifyKind(utc, DateTimeKind.Utc);
            DateTime londonLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _londonTz);
            DateTime nyLocal = TimeZoneInfo.ConvertTimeFromUtc(utc, _newYorkTz);
            DateTime londonOpenLocal = DateTime.SpecifyKind(londonLocal.Date.AddHours(8), DateTimeKind.Unspecified);
            DateTime nyCloseLocal = DateTime.SpecifyKind(nyLocal.Date.AddHours(17), DateTimeKind.Unspecified);
            DateTime londonOpenUtc = TimeZoneInfo.ConvertTimeToUtc(londonOpenLocal, _londonTz);
            DateTime nyCloseUtc = TimeZoneInfo.ConvertTimeToUtc(nyCloseLocal, _newYorkTz);
            return utc >= londonOpenUtc && utc < nyCloseUtc;
        }

        private TimeZoneInfo ResolveTimeZone(string iana, string windows)
        {
            try { return TimeZoneInfo.FindSystemTimeZoneById(iana); }
            catch { try { return TimeZoneInfo.FindSystemTimeZoneById(windows); } catch { return null; } }
        }

        private IEnumerable<Position> OwnPositions()
        {
            return Positions.Where(p => p.SymbolName == SymbolName && !string.IsNullOrWhiteSpace(p.Label) && p.Label.StartsWith(BotPrefix + "|", StringComparison.Ordinal));
        }

        private void ResetDaily(bool force)
        {
            DateTime d = Server.Time.ToUniversalTime().Date;
            if (!force && d == _currentDay) return;
            _currentDay = d;
            _dayStartEquity = Account.Equity;
            _dailyLocked = false;
        }

        private void UpdateRiskLocks()
        {
            if (Account.Equity > _equityPeak) _equityPeak = Account.Equity;
            if (_dayStartEquity > 0)
            {
                double dd = 100.0 * (_dayStartEquity - Account.Equity) / _dayStartEquity;
                if (dd >= DailyLossLimitPercent) _dailyLocked = true;
            }
        }

        private bool PeakDrawdownExceeded()
        {
            if (_equityPeak <= 0) return false;
            return 100.0 * (_equityPeak - Account.Equity) / _equityPeak >= MaxDrawdownPercent;
        }

        private bool SpreadValid() { return SpreadPips() <= MaxSpreadPips; }
        private double SpreadPips() { return _symbol.PipSize > 0 ? (_symbol.Ask - _symbol.Bid) / _symbol.PipSize : 99999; }

        private void EnsureServerProtection()
        {
            foreach (var p in OwnPositions())
            {
                if (p.StopLoss.HasValue && p.TakeProfit.HasValue) continue;

                PositionLedger l;
                FibonacciBasket basket;
                if (!_positions.TryGetValue(p.Id, out l) ||
                    string.IsNullOrWhiteSpace(l.BasketId) ||
                    !_baskets.TryGetValue(l.BasketId, out basket))
                    continue;

                TradeType tt = p.TradeType;
                TradeDirection direction = tt == TradeType.Buy ? TradeDirection.Buy : TradeDirection.Sell;
                if (!BrokerStopDistanceValid(tt, basket.StructuralStop) || !BrokerTargetDistanceValid(tt, basket.CanonicalTarget))
                {
                    basket.ExitOverride = "SERVER_PROTECTION_DISTANCE_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    continue;
                }

                TradeResult rs = p.StopLoss.HasValue ? null : p.ModifyStopLossPrice(basket.StructuralStop);
                if (rs != null && !rs.IsSuccessful)
                {
                    RecordExecutionError("SERVER_SL_FAILED_" + rs.Error, "basket=" + basket.BasketId + ";position=" + p.Id);
                    basket.ExitOverride = "SERVER_PROTECTION_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                    continue;
                }
                var live = Positions.FirstOrDefault(x => x.Id == p.Id);
                TradeResult rt = live != null && !live.TakeProfit.HasValue ? live.ModifyTakeProfitPrice(basket.CanonicalTarget) : null;
                if (rt != null && !rt.IsSuccessful)
                {
                    RecordExecutionError("SERVER_TP_FAILED_" + rt.Error, "basket=" + basket.BasketId + ";position=" + p.Id);
                    basket.ExitOverride = "SERVER_PROTECTION_FAIL_CLOSED";
                    FailClosePosition(p, basket, basket.ExitOverride);
                    if (PositionStillExists(p.Id)) _unprotectedSurvivors++;
                }
            }
        }

        private void RecordExecutionError(string code, string detail)
        {
            _executionErrors++;
            if (string.IsNullOrWhiteSpace(code)) code = "UNKNOWN";
            int n;
            _executionErrorReasons.TryGetValue(code, out n);
            _executionErrorReasons[code] = n + 1;
            Print("[V51-EXECUTION-ERROR] code={0} detail={1}", code, detail ?? "");
        }

        private bool PendingOrderStillExists(long id)
        {
            return PendingOrders.Any(o => o.Id == id);
        }

        private bool PositionStillExists(long id)
        {
            return Positions.Any(p => p.Id == id);
        }

        private double BrokerMinimumDistancePrice(double referencePrice, bool stopLoss)
        {
            double d = stopLoss ? _symbol.MinStopLossDistance : _symbol.MinTakeProfitDistance;
            if (d <= 0) return 0;
            if (_symbol.MinDistanceType == SymbolMinDistanceType.Pips)
                return d * _symbol.PipSize;
            return Math.Abs(referencePrice) * d / 100.0;
        }

        private bool BrokerProtectionDistancesValid(TradeDirection direction, double entry, double stop, double target)
        {
            if (!GeometryValid(direction, entry, stop, target)) return false;
            double minSl = BrokerMinimumDistancePrice(entry, true);
            double minTp = BrokerMinimumDistancePrice(entry, false);
            return Math.Abs(entry - stop) + 1e-12 >= minSl &&
                   Math.Abs(target - entry) + 1e-12 >= minTp;
        }

        private bool BrokerStopDistanceValid(TradeType tradeType, double proposedStop)
        {
            double reference = tradeType == TradeType.Buy ? _symbol.Bid : _symbol.Ask;
            double minSl = BrokerMinimumDistancePrice(reference, true);
            return tradeType == TradeType.Buy
                ? proposedStop < reference && reference - proposedStop + 1e-12 >= minSl
                : proposedStop > reference && proposedStop - reference + 1e-12 >= minSl;
        }

    }
}
