using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GoldenWaveProRiskEngineMobile : Robot
    {
        private RiskManagementEngine? _riskEngine;
        private decimal _initialEquity;
        private bool _emergencyLogged;

        protected override void OnStart()
        {
            _initialEquity = (decimal)Account.Equity;
            _riskEngine = new RiskManagementEngine(() => (decimal)Account.Equity);
            _riskEngine.UpdateEquity((decimal)Account.Equity);

            Print("GoldenWavePro Risk Engine Mobile started. This build contains the supplied risk-management engine only; no entry strategy was provided, so it does not open trades by itself.");
        }

        protected override void OnTick()
        {
            if (_riskEngine == null)
                return;

            var currentEquity = (decimal)Account.Equity;
            _riskEngine.UpdateEquity(currentEquity);

            if (!_emergencyLogged && _initialEquity > 0 && _riskEngine.ShouldCloseAllPositions(currentEquity, _initialEquity))
            {
                _emergencyLogged = true;
                Print("GoldenWavePro emergency threshold reached. No automatic liquidation is performed by this risk-engine-only wrapper.");
            }
        }
    }

    public class RiskManagementEngine
    {
        // 核心風險參數
        private const double MaxRiskPerTrade = 0.003;          // 單筆最大風險 0.3%
        private const double EmergencyStopThreshold = 0.25;    // 緊急停損閾值 25%
        private const double DailyLossLimit = 0.05;            // 每日損失限制 5%
        private const double WeeklyLossLimit = 0.12;           // 每週損失限制 12%
        private const double MaxDrawdownThreshold = 0.18;      // 最大回撤閾值 18%

        // 動態參數
        private const double DynamicProfitTake = 0.618;        // 動態止盈比例
        private const double VolatilityAdjustmentFactor = 1.3; // 波動率調整因子

        // 狀態追蹤
        private DateTime? _lastTradeTime;
        private readonly List<decimal> _dailyPnLHistory = new();
        private readonly List<decimal> _weeklyPnLHistory = new();
        private decimal _peakEquity;
        private int _currentWeekNumber;
        private readonly Func<decimal> _currentEquityProvider;

        public RiskManagementEngine(Func<decimal> currentEquityProvider)
        {
            _currentEquityProvider = currentEquityProvider ?? throw new ArgumentNullException(nameof(currentEquityProvider));
        }

        public PositionSizeInfo CalculatePositionSize(decimal equity, decimal entryPrice, decimal stopLossPrice)
        {
            var riskAmount = equity * (decimal)MaxRiskPerTrade;
            var stopLossPoints = Math.Abs(entryPrice - stopLossPrice);

            if (stopLossPoints == 0)
                throw new ArgumentException("Stop loss distance cannot be zero");

            var positionSize = (riskAmount / stopLossPoints) * entryPrice * 0.1m;
            var maxAllowed = equity * 0.3m; // 最大暴露 30%

            var finalSize = Math.Min(positionSize, maxAllowed);

            return new PositionSizeInfo
            {
                Size = Math.Max(finalSize, 100m), // 最小交易量
                RiskAmount = riskAmount,
                RiskPercentage = MaxRiskPerTrade
            };
        }

        public StopLossTakeProfitLevels CalculateStopLossTakeProfit(
            decimal entryPrice,
            FibonacciLevels fibLevels,
            TradeDirection direction)
        {
            var stopLossDistance = direction == TradeDirection.Buy
                ? Math.Abs(fibLevels.SwingLow - entryPrice)
                : Math.Abs(entryPrice - fibLevels.SwingHigh);

            // 動態止損距離調整
            var adjustedStopLossDistance = stopLossDistance * (decimal)VolatilityAdjustmentFactor;

            var stopLoss = direction == TradeDirection.Buy
                ? entryPrice - adjustedStopLossDistance
                : entryPrice + adjustedStopLossDistance;

            // 動態止盈等級
            var takeProfit1 = CalculateTakeProfit(entryPrice, fibLevels.Level382, direction);
            var takeProfit2 = CalculateTakeProfit(entryPrice, fibLevels.Level618, direction);
            var takeProfit3 = CalculateTakeProfit(entryPrice, fibLevels.Level786, direction);

            return new StopLossTakeProfitLevels
            {
                StopLoss = stopLoss,
                TakeProfits = new[] { takeProfit1, takeProfit2, takeProfit3 }
            };
        }

        public bool ShouldCloseAllPositions(decimal currentEquity, decimal initialEquity)
        {
            if (initialEquity <= 0)
                return false;

            return (initialEquity - currentEquity) / initialEquity >= (decimal)EmergencyStopThreshold;
        }

        public bool ShouldStopTrading()
        {
            var currentDate = DateTime.Today;

            // 檢查每日損失限制
            if (_dailyPnLHistory.Any())
            {
                var todayPnL = _dailyPnLHistory.LastOrDefault();
                if (todayPnL <= -(decimal)DailyLossLimit)
                    return true;
            }

            // 檢查每週損失限制
            var currentWeek = GetWeekOfYear(currentDate);
            if (currentWeek != _currentWeekNumber)
            {
                _currentWeekNumber = currentWeek;
                _weeklyPnLHistory.Clear(); // 新週重新計算
            }

            if (_weeklyPnLHistory.Any())
            {
                var weekPnL = _weeklyPnLHistory.Sum();
                if (weekPnL <= -(decimal)WeeklyLossLimit)
                    return true;
            }

            // 檢查最大回撤
            if (_peakEquity > 0)
            {
                var drawdown = (_peakEquity - GetCurrentEquity()) / _peakEquity;
                if (drawdown >= (decimal)MaxDrawdownThreshold)
                    return true;
            }

            return false;
        }

        public void UpdateEquity(decimal currentEquity)
        {
            _peakEquity = Math.Max(_peakEquity, currentEquity);
        }

        public void RecordDailyPnL(decimal pnl)
        {
            _dailyPnLHistory.Add(pnl);
            if (_dailyPnLHistory.Count > 30) // 保留最近30天
                _dailyPnLHistory.RemoveAt(0);
        }

        public void RecordWeeklyPnL(decimal pnl)
        {
            _weeklyPnLHistory.Add(pnl);
        }

        private decimal GetCurrentEquity() => _currentEquityProvider();

        private static int GetWeekOfYear(DateTime dt)
        {
            var diff = (int)(dt.DayOfYear - (int)((dt.Day + 6) / 7) * 7 + 12) / 7 + 1;
            return (diff + 1) / 7;
        }

        private decimal CalculateTakeProfit(decimal entryPrice, decimal fibLevel, TradeDirection direction)
        {
            return direction == TradeDirection.Buy
                ? entryPrice + (fibLevel - entryPrice) * (decimal)DynamicProfitTake
                : entryPrice - (entryPrice - fibLevel) * (decimal)DynamicProfitTake;
        }
    }

    public enum TradeDirection
    {
        Buy,
        Sell
    }

    public class PositionSizeInfo
    {
        public decimal Size { get; set; }
        public decimal RiskAmount { get; set; }
        public double RiskPercentage { get; set; }
    }

    public class StopLossTakeProfitLevels
    {
        public decimal StopLoss { get; set; }
        public decimal[] TakeProfits { get; set; } = Array.Empty<decimal>();
    }

    public class FibonacciLevels
    {
        public decimal SwingLow { get; set; }
        public decimal SwingHigh { get; set; }
        public decimal Level382 { get; set; }
        public decimal Level5 { get; set; }
        public decimal Level618 { get; set; }
        public decimal Level786 { get; set; }
    }
}
