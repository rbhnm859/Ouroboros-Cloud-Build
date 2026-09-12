using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private sealed class EntryCandidate
        {
            public bool IsValid { get; set; }
            public TradeType Direction { get; set; }
            public double Pressure { get; set; }
            public double MomentumR { get; set; }
            public string Setup { get; set; }

            public static EntryCandidate Invalid()
            {
                return new EntryCandidate { IsValid = false, Setup = "none" };
            }
        }

        private sealed class TradeState
        {
            public long PositionId { get; set; }
            public int EntryBarIndex { get; set; }
            public double InitialStopPips { get; set; }
            public double InitialRiskMoney { get; set; }
            public double BestFavorablePips { get; set; }
            public int OppositePressureBars { get; set; }
            public bool BreakevenApplied { get; set; }
            public bool TrailingActivated { get; set; }
        }
    }
}
