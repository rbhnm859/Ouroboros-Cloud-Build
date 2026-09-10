using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal enum RiskBudgetMode
    {
        PercentEquity,
        FixedCash
    }

    internal sealed class PivotPoint
    {
        public PivotPoint(int index, double price, bool isHigh)
        {
            Index = index;
            Price = price;
            IsHigh = isHigh;
        }

        public int Index { get; private set; }
        public double Price { get; private set; }
        public bool IsHigh { get; private set; }
    }

    internal sealed class HarmonicSignal
    {
        public string PatternName;
        public TradeType Direction;
        public double PatternScore;
        public PivotPoint X;
        public PivotPoint A;
        public PivotPoint B;
        public PivotPoint C;
        public PivotPoint D;
        public double AbXa;
        public double BcAb;
        public double CdBc;
        public double AdXa;
        public double Atr;
        public double PrzLow;
        public double PrzHigh;

        public string Key
        {
            get
            {
                return PatternName + "|" + Direction + "|" + X.Index + "|" + A.Index + "|" + B.Index + "|" + C.Index + "|" + D.Index;
            }
        }
    }

    internal sealed class RegimeSnapshot
    {
        public bool Allowed;
        public string RejectReason;
        public double AtrFast;
        public double AtrSlow;
        public double AtrRegime;
        public double RelativeTickVolume;
        public double SpreadAtrRatio;
        public double FlashVolatilityRatio;
        public double EmaFast;
        public double EmaSlow;
        public double EmaFastSlope;
        public bool TrendAligned;
    }

    internal sealed class ConfirmationSnapshot
    {
        public bool DirectionalCandle;
        public bool Rejection;
        public bool Momentum;
        public bool MicroBreak;
        public int RulesPassed;
        public double BodyRatio;
        public double DistanceAtr;
    }

    internal sealed class TradePlan
    {
        public TradeType Direction;
        public double EntryPrice;
        public double StopPrice;
        public double TargetPrice;
        public double StopLossPips;
        public double TakeProfitPips;
        public double EffectiveRiskReward;
        public double VolumeInUnits;
        public double EstimatedRiskCash;
        public double EstimatedMargin;
        public string Comment;
    }

    internal sealed class TradeMetadata
    {
        public string PatternName;
        public TradeType Direction;
        public double PatternScore;
        public double EffectiveRiskReward;
        public int ConfirmationRules;
        public double RelativeTickVolume;
        public double InitialStopLossPips;
        public int EntryBarIndex;
    }
}
