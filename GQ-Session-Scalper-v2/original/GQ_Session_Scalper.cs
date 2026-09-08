//+------------------------------------------------------------------+
//|                                           GQ_Session_Scalper.cs  |
//|                                                      Gueta Quant |
//|                                             https://guetaquant.com|
//|                                                                  |
//|  Aviso de Riesgo: Fines netamente educativos. Decreto 2555/2010. |
//+------------------------------------------------------------------+
using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Requests;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class GQ_Session_Scalper : Robot
    {
        [Parameter("Session Start (HH:mm)", Group = "Session", DefaultValue = "08:00")]
        public string SessionStart { get; set; }

        [Parameter("Session End (HH:mm)", Group = "Session", DefaultValue = "16:00")]
        public string SessionEnd { get; set; }

        [Parameter("EMA Period", Group = "Indicators", DefaultValue = 21)]
        public int EMAPeriod { get; set; }

        [Parameter("Momentum Period", Group = "Indicators", DefaultValue = 14)]
        public int MomentumPeriod { get; set; }

        [Parameter("SL Pips", Group = "Risk", DefaultValue = 10)]
        public double SL_Pips { get; set; }

        [Parameter("TP Ratio", Group = "Risk", DefaultValue = 1.5)]
        public double TP_Ratio { get; set; }

        [Parameter("Max Trades Per Session", Group = "Risk", DefaultValue = 5)]
        public int MaxTrades { get; set; }

        [Parameter("Lot Size", Group = "Risk", DefaultValue = 0.1)]
        public double LotSize { get; set; }

        [Parameter("ATR Period", Group = "ATR", DefaultValue = 14)]
        public int ATRPeriod { get; set; }

        [Parameter("Max Spread", Group = "Filter", DefaultValue = 15)]
        public double MaxSpread { get; set; }

        private ExponentialMovingAverage _ema;
        private Momentum _momentum;
        private AverageTrueRange _atr;
        private TimeSpan _sessionStart;
        private TimeSpan _sessionEnd;
        private int _tradesThisSession;
        private DateTime _currentSessionDate;

        protected override void OnStart()
        {
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EMAPeriod);
            _momentum = Indicators.Momentum(Bars.ClosePrices, MomentumPeriod);
            _atr = Indicators.AverageTrueRange(ATRPeriod, MovingAverageType.Simple);

            if (!TimeSpan.TryParse(SessionStart, out _sessionStart))
                _sessionStart = new TimeSpan(8, 0, 0);

            if (!TimeSpan.TryParse(SessionEnd, out _sessionEnd))
                _sessionEnd = new TimeSpan(16, 0, 0);

            _tradesThisSession = 0;
            _currentSessionDate = Server.Time.Date;
        }

        protected override void OnTick()
        {
            DateTime now = Server.Time;

            if (now.Date != _currentSessionDate)
            {
                _currentSessionDate = now.Date;
                _tradesThisSession = 0;
            }

            if (!IsInSession(now))
                return;

            if (_tradesThisSession >= MaxTrades)
                return;

            double spread = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (spread > MaxSpread)
                return;

            if (HasOpenPosition())
                return;

            EvaluateEntry();
        }

        private bool IsInSession(DateTime time)
        {
            TimeSpan currentTime = time.TimeOfDay;
            return currentTime >= _sessionStart && currentTime <= _sessionEnd;
        }

        private bool HasOpenPosition()
        {
            return Positions.Any(p => p.SymbolName == SymbolName && p.Label == "GQScalp");
        }

        private void EvaluateEntry()
        {
            double emaValue = _ema.Result.Last(1);
            double previousEma = _ema.Result.Last(2);
            double closePrice = Bars.ClosePrices.Last(1);
            double momentumValue = _momentum.Result.Last(1);
            double atrValue = _atr.Result.Last(1);
            double tpPips = SL_Pips * TP_Ratio;
            double volume = Symbol.NormalizeVolumeInUnits(LotSize);

            bool priceAboveEma = closePrice > emaValue;
            bool priceBelowEma = closePrice < emaValue;
            bool momentumAbove100 = momentumValue > 100;
            bool momentumBelow100 = momentumValue < 100;

            if (priceBelowEma && previousEma <= emaValue && momentumBelow100)
            {
                if (closePrice >= emaValue - atrValue * 0.5 && closePrice <= emaValue + atrValue * 0.5)
                {
                    ExecuteScalp(TradeType.Sell, volume);
                }
            }

            if (priceAboveEma && previousEma >= emaValue && momentumAbove100)
            {
                if (closePrice >= emaValue - atrValue * 0.5 && closePrice <= emaValue + atrValue * 0.5)
                {
                    ExecuteScalp(TradeType.Buy, volume);
                }
            }
        }

        private void ExecuteScalp(TradeType tradeType, double volume)
        {
            var request = new MarketOrderRequest(tradeType, volume)
            {
                StopLossPips = SL_Pips,
                TakeProfitPips = SL_Pips * TP_Ratio,
                Label = "GQScalp",
                Comment = $"Session:{SessionStart}-{SessionEnd}"
            };

            var result = ExecuteMarketOrder(request);
            if (!result.IsSuccessful)
            {
                Print($"Scalp entry failed: {result.Error}");
                return;
            }

            _tradesThisSession++;
            Print($"Scalp {tradeType} entered. Trade {_tradesThisSession}/{MaxTrades}");
        }

        protected override void OnPositionOpened(Position position)
        {
            if (position.Label != "GQScalp" || position.SymbolName != SymbolName)
                return;

            UpdatePanel();
        }

        protected override void OnPositionClosed(Position position)
        {
            if (position.Label != "GQScalp" || position.SymbolName != SymbolName)
                return;

            UpdatePanel();
        }

        private void UpdatePanel()
        {
            bool inSession = IsInSession(Server.Time);
            double atr = _atr.Result.Last(1);
            double ema = _ema.Result.Last(1);
            int openPositions = Positions.Count(p => p.SymbolName == SymbolName && p.Label == "GQScalp");

            Chart.DrawStaticText("SessActive", $"Session: {(inSession ? "ACTIVE" : "INACTIVE")}", VerticalAlignment.Top, HorizontalAlignment.Left, inSession ? Color.Green : Color.Red);
            Chart.DrawStaticText("SessTrades", $"Trades: {_tradesThisSession}/{MaxTrades}", VerticalAlignment.Top, HorizontalAlignment.Left, Color.Yellow);
            Chart.DrawStaticText("SessATR", $"ATR: {atr:F5}", VerticalAlignment.Top, HorizontalAlignment.Left, Color.Cyan);
            Chart.DrawStaticText("SessEMA", $"EMA: {ema:F5}", VerticalAlignment.Top, HorizontalAlignment.Left, Color.Magenta);
            Chart.DrawStaticText("SessOpen", $"Open Pos: {openPositions}", VerticalAlignment.Top, HorizontalAlignment.Left, Color.Orange);
        }
    }
}
