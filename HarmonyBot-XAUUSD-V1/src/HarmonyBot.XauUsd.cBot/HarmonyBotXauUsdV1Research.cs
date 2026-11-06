using System;
using HarmonyBot.XauUsd.Core;
using cAlgo.API;

namespace cAlgo.Robots
{
    // PHASE 1 / RESEARCH ONLY. Deliberately has ZERO order creation, modification
    // or cancellation calls. Editing cTrader parameters cannot enable live trading.
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public sealed class HarmonyBotXauUsdV1Research : Robot
    {
        [Parameter("Pivot Left Bars", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int PivotLeftBars { get; set; }

        [Parameter("Pivot Right Bars", DefaultValue = 3, MinValue = 1, MaxValue = 10)]
        public int PivotRightBars { get; set; }

        private CausalPivotDetector? _pivots;
        private CausalPatternAssembler? _assembler;

        protected override void OnStart()
        {
            if (SymbolName.IndexOf("XAU", StringComparison.OrdinalIgnoreCase) < 0)
            {
                Print("[HBXAU-V1] REFUSED: selected symbol does not resemble XAUUSD");
                Stop();
                return;
            }
            _pivots = new CausalPivotDetector(PivotLeftBars, PivotRightBars);
            _assembler = new CausalPatternAssembler();
            Print("[HBXAU-V1] RESEARCH_ONLY; orders permanently disabled in this build; symbol={0}", SymbolName);
            Print("[HBXAU-V1] Broker contract and original harmonic specifications NOT VERIFIED.");
        }

        protected override void OnBarClosed()
        {
            if (_pivots == null || Bars.Count < PivotLeftBars + PivotRightBars + 3)
                return;
            try
            {
                // Bars.Last(1) is the previous completed bar in the official
                // cTrader OnBarClosed examples. Last(0).OpenTime is its end.
                var closed = Bars.Last(1);
                var next = Bars.Last(0);
                var start = new DateTimeOffset(DateTime.SpecifyKind(closed.OpenTime, DateTimeKind.Utc));
                var end = new DateTimeOffset(DateTime.SpecifyKind(next.OpenTime, DateTimeKind.Utc));
                var bar = new CompletedBar(start, end, (decimal)closed.Open,
                    (decimal)closed.High, (decimal)closed.Low, (decimal)closed.Close);
                var events = _pivots.AppendCompleted(bar);
                foreach (var pivot in events)
                {
                    Print("[HBXAU-V1-PIVOT] source={0} confirm={1} kind={2} price={3} available={4:o}",
                        pivot.SourceBarIndex, pivot.ConfirmationBarIndex,
                        pivot.Kind, pivot.Price, pivot.AvailableAtUtc.UtcDateTime);
                    // Research event after five alternating CONFIRMED pivots.
                    // The decision remains locked REJECT; NO trade API is invoked.
                    var observation = _assembler!.Observe(pivot,end,(decimal)Symbol.TickSize);
                    if (observation != null)
                    {
                        var verdict = StrategyDecision.Evaluate(observation,true,false);
                        Print("[HBXAU-V1-CANDIDATE] event={0} matched={1} verdict={2} blocker={3}",
                            observation.EventId,
                            string.Join(",",observation.ResearchMatches),
                            verdict.Action,verdict.Reason);
                    }
                }
            }
            catch (Exception ex)
            {
                Print("[HBXAU-V1] FAIL_CLOSED observation rejected: {0}", ex.Message);
                Stop();
            }
        }
    }
}
