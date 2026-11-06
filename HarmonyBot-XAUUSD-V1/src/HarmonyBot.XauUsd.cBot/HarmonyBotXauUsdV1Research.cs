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
            if (!string.Equals(SymbolName, "XAUUSD", StringComparison.OrdinalIgnoreCase))
            {
                Print("[HBXAU-V1] REFUSED: unverified symbol identity; only exact XAUUSD allowed until broker adapter verification");
                Stop();
                return;
            }
            _pivots = new CausalPivotDetector(PivotLeftBars, PivotRightBars);
            _assembler = new CausalPatternAssembler();
            Print("[HBXAU-V1] RESEARCH_ONLY; orders permanently disabled in this build; symbol={0}", SymbolName);
            Print("[HBXAU-V1] Broker contract and original harmonic specifications NOT VERIFIED.");
        }

        // OnBar(): Bars.Last(0) is the newly FORMING bar and is used ONLY
        // for its open boundary. Bars.Last(1) is the just-completed bar.
        // Avoid the documented OnBarClosed()/Last(1) ambiguity.
        protected override void OnBar()
        {
            if (_pivots == null || Bars.Count < PivotLeftBars + PivotRightBars + 3)
                return;
            try
            {
                var closed = Bars.Last(1);
                var newlyOpened = Bars.Last(0);
                var sourceOpenUtc = new DateTimeOffset(
                    DateTime.SpecifyKind(closed.OpenTime, DateTimeKind.Utc));
                var nextOpenUtc = new DateTimeOffset(
                    DateTime.SpecifyKind(newlyOpened.OpenTime, DateTimeKind.Utc));
                // The new bar only opens when a tick arrives. Friday close
                // can therefore become available on Monday, not Friday.
                var tickObservedUtc = new DateTimeOffset(
                    DateTime.SpecifyKind(Server.Time, DateTimeKind.Utc));
                var receipt = CausalBarReceipt.CaptureOnBarOpened(
                    sourceOpenUtc, nextOpenUtc, tickObservedUtc,
                    (decimal)closed.Open, (decimal)closed.High,
                    (decimal)closed.Low, (decimal)closed.Close);
                var events = _pivots.AppendCompleted(
                    receipt.ClosedBar, receipt.AvailableAtUtc);
                foreach (var pivot in events)
                {
                    Print("[HBXAU-V1-PIVOT] source={0} confirm={1} kind={2} price={3} available={4:o}",
                        pivot.SourceBarIndex, pivot.ConfirmationBarIndex,
                        pivot.Kind, pivot.Price, pivot.AvailableAtUtc.UtcDateTime);
                    // Research event after five alternating CONFIRMED pivots.
                    // The decision remains locked REJECT; NO trade API is invoked.
                    var observation = _assembler!.Observe(pivot,receipt.AvailableAtUtc,(decimal)Symbol.TickSize);
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
