using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    // Architecture-level falsification: the broad reversal lane was negative in all burned years.
    // This experiment monetizes only a harmonic structural failure that completes:
    // break -> boundary retest -> later completed-bar continuation BOS.
    public partial class HarmonyBotV71
    {
        private bool V72FailureAuctionFamilyAllowed(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return false;
            return !string.Equals(V71FamilyKey(e.Signal.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase);
        }

        private bool V72StartFailureAuction(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if (!EnableV72FailureAuctionCausalAlpha || e == null || e.Signal == null ||
                !e.PrzTouchUtc.HasValue || !V72FailureAuctionFamilyAllowed(e) ||
                !V72FailureBreakConfirmed(i, e)) return false;

            e.FailureContinuation = true;
            e.FailureBreakObserved = true;
            e.FailureRetestObserved = false;
            e.FailureBreakUtc = utc;
            e.FailureRetestUtc = null;
            e.FailureBoundary = e.Signal.StructuralInvalidation;
            e.FailureBreakPrice = _m1Bars.ClosePrices[i];
            e.CapitalDirection = V72OppositeDirection(e.Signal.Direction);
            e.FailureRetestExpiryUtc = e.ExpiryUtc;
            if (e.FailureRetestExpiryUtc <= utc.AddSeconds(1)) return false;

            e.State = V71ExpansionState.PROOF_WAIT;
            e.CapitalReady = false;
            e.CapitalLane = "FAILURE_AUCTION_WAIT_RETEST";
            Print("[V72-FAILURE-AUCTION-BREAK] cid={0} family={1} originalDir={2} continuationDir={3} boundary={4:F5} close={5:F5} expiry={6:o}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Signal.Direction, e.CapitalDirection,
                e.FailureBoundary, e.FailureBreakPrice, e.FailureRetestExpiryUtc);
            return true;
        }

        private bool V72ProcessFailureAuction(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || !e.FailureBreakObserved || !e.FailureContinuation)
                return false;
            if (!e.FailureBreakUtc.HasValue || utc <= e.FailureBreakUtc.Value) return false;
            if (utc >= e.FailureRetestExpiryUtc)
            {
                e.IsActive = false;
                e.State = V71ExpansionState.EXPIRED;
                Print("[V72-FAILURE-AUCTION-EXPIRE] cid={0} stage={1}",
                    e.CandidateId, e.FailureRetestObserved ? "WAIT_BOS" : "WAIT_RETEST");
                return true;
            }

            TradeDirection direction = e.CapitalDirection;
            double boundary = e.FailureBoundary;
            double o = _m1Bars.OpenPrices[i], close = _m1Bars.ClosePrices[i];
            double high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i];

            if (!e.FailureRetestObserved)
            {
                bool touchedBoundary = low <= boundary && high >= boundary;
                bool heldFailureSide = direction == TradeDirection.Buy ? close > boundary : close < boundary;
                bool directional = direction == TradeDirection.Buy ? close > o : close < o;
                if (!(touchedBoundary && heldFailureSide && directional)) return false;

                e.FailureRetestObserved = true;
                e.FailureRetestUtc = utc;
                e.FailureRetestHigh = high;
                e.FailureRetestLow = low;
                e.CapitalLane = "FAILURE_AUCTION_WAIT_BOS";
                Print("[V72-FAILURE-AUCTION-RETEST] cid={0} family={1} dir={2} boundary={3:F5} high={4:F5} low={5:F5}",
                    e.CandidateId, V71FamilyKey(e.Signal.PatternName), direction, boundary, high, low);
                return true;
            }

            if (!e.FailureRetestUtc.HasValue || utc <= e.FailureRetestUtc.Value) return false;

            bool reclaimedPatternSide = direction == TradeDirection.Buy ? close <= boundary : close >= boundary;
            if (reclaimedPatternSide)
            {
                e.IsActive = false;
                e.State = V71ExpansionState.REJECTED;
                Print("[V72-FAILURE-AUCTION-REJECT] cid={0} reason=BOUNDARY_RECLAIM_BEFORE_BOS", e.CandidateId);
                return true;
            }

            bool continuationBos = direction == TradeDirection.Buy
                ? close > e.FailureRetestHigh
                : close < e.FailureRetestLow;
            if (!continuationBos) return false;

            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            double entry = close;
            double stop = direction == TradeDirection.Buy
                ? e.FailureRetestLow - buffer
                : e.FailureRetestHigh + buffer;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips)
            {
                e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                Print("[V72-FAILURE-AUCTION-REJECT] cid={0} reason=MIN_STOP", e.CandidateId);
                return true;
            }

            double costPrice = PipsToPrice(ModeledCostPips());
            double target = direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            if (!GeometryValid(direction, entry, stop, target))
            {
                e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                return true;
            }
            double netRr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                           Math.Max(1e-9, PriceToPips(risk));
            if (netRr + 1e-9 < MinimumNetRR)
            {
                e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                return true;
            }

            e.Route = HarmonicRoute.FAILURE_CONTINUATION;
            e.EntryAnchor = entry;
            e.StructuralStop = stop;
            e.CanonicalTarget = target;
            e.RiskDistance = risk;
            e.TargetR = Math.Abs(target - entry) / Math.Max(risk, _symbol.PipSize);
            e.NetRR = netRr;
            e.ModeledCostR = PipsToPrice(ModeledCostPips()) / Math.Max(risk, _symbol.PipSize);
            e.AwaitingPullbackFill = false;
            e.PullbackFilled = true;
            e.ShadowStarted = true;
            e.ShadowFinished = false;
            e.ArmedUtc = utc;
            e.ShadowPeakR = 0;
            e.ShadowProtectionR = -1.0;
            e.PathState = 0;
            e.PathUsable = false;
            e.CapitalEligible = e.CapitalEligible && !e.CoreOverlapObserved;
            e.CapitalReady = false; // explicit pre-capital architecture test
            e.CapitalLane = "FAILURE_AUCTION_CONTINUATION";
            e.State = V71ExpansionState.ARMED;
            e.AsymmetryCompression = 1.0;
            e.EdgeMean = netRr;
            e.EdgeLcb = netRr;
            e.ExpectedSlotHours = Math.Max(.25, V71ExpansionShadowHorizonM1Bars / 60.0);
            e.ExpectedSlotHoursUcb = e.ExpectedSlotHours;
            e.SlotScore = netRr / Math.Max(.25, e.ExpectedSlotHours);
            _v71ExpansionArmed++;
            IncrementCounter(_v71FamilyArmed, V71FamilyKey(e.Signal.PatternName));

            Print("[V72-FAILURE-AUCTION-BOS] cid={0} family={1} dir={2} entry={3:F5} stop={4:F5} target={5:F5} netRR={6:F3}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), direction, entry, stop, target, netRr);
            return true;
        }
    }
}
