using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    // Burned-calibration research-only family-native causal resolution.
    // This module does not alter the frozen detector, V51 ownership, risk kernel or execution path.
    public partial class HarmonyBotV71
    {
        private bool V72FamilyNativeCapitalSemanticsAllowed(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return false;
            string family = V71FamilyKey(e.Signal.PatternName);
            if (string.Equals(family, "ABCD", StringComparison.OrdinalIgnoreCase)) return false;
            if (e.Route == HarmonicRoute.TRANSITION_REVERSAL) return false;
            if (e.Regime != null && e.Regime.Transition) return false;
            if (e.Conflict == MtfConflict.TRANSITION || e.Conflict == MtfConflict.CONFLICT) return false;
            return true;
        }

        private void V72InitializeFamilyNativeShadow(V71ExpansionCandidate e, DateTime utc,
            TradeDirection direction, double entry, double stop, double target,
            double netRr, double confirmationScore, string lane, bool capitalSemanticsAllowed)
        {
            double risk = Math.Abs(entry - stop);
            e.CapitalDirection = direction;
            e.EntryAnchor = entry;
            e.StructuralStop = stop;
            e.CanonicalTarget = target;
            e.RiskDistance = risk;
            e.TargetR = Math.Abs(target - entry) / Math.Max(risk, _symbol.PipSize);
            e.NetRR = netRr;
            e.ConfirmationScore = confirmationScore;
            e.RegimeScore = RegimeContextScore(e.Signal, e.Conflict, e.Regime);
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
            e.CapitalReady = false; // shadow-only until a later formal execution-conversion gate
            e.CapitalEligible = e.CapitalEligible && capitalSemanticsAllowed;
            e.CapitalLane = lane;
            e.State = V71ExpansionState.ARMED;
            e.AsymmetryCompression = 1.0;
            e.EdgeMean = netRr;
            e.EdgeLcb = netRr;
            e.ExpectedSlotHours = Math.Max(.25, V71ExpansionShadowHorizonM1Bars / 60.0);
            e.ExpectedSlotHoursUcb = e.ExpectedSlotHours;
            e.SlotScore = netRr / Math.Max(.25, e.ExpectedSlotHours);
            _v71ExpansionArmed++;
            IncrementCounter(_v71FamilyArmed, V71FamilyKey(e.Signal.PatternName));
        }

        private bool V72PrepareFamilyNativeReversalShadow(int i, DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            if (!EnableV72FamilyNativeCausalAlpha || e == null || e.Signal == null ||
                i < 0 || i >= _m1Bars.Count) return false;

            TradeDirection direction = e.Signal.Direction;
            double entry = _m1Bars.ClosePrices[i];
            double stop = e.Signal.StructuralInvalidation;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(e.Signal, entry, stop, out target, out netRr)) return false;
            if (netRr + 1e-9 < MinimumNetRR) return false;

            bool allowed = V72FamilyNativeCapitalSemanticsAllowed(e) &&
                           e.CapitalEligible && !e.CoreOverlapObserved;
            string lane = allowed ? "FAMILY_NATIVE_REVERSAL" : "FAMILY_NATIVE_SHADOW_ONLY";
            V72InitializeFamilyNativeShadow(e, utc, direction, entry, stop, target, netRr,
                confirmationScore, lane, allowed);

            Print("[V72-FAMILY-NATIVE-PROVED] cid={0} family={1} dir={2} entry={3:F5} stop={4:F5} target={5:F5} netRR={6:F3} capitalSemantics={7}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), direction, entry, stop, target, netRr, allowed);
            return true;
        }

        private bool V72StartFamilyNativeFailureRetest(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if (!EnableV72FamilyNativeCausalAlpha || e == null || e.Signal == null ||
                !e.PrzTouchUtc.HasValue || !V72FailureBreakConfirmed(i, e)) return false;

            e.FailureContinuation = true;
            e.FailureBreakObserved = true;
            e.FailureBreakUtc = utc;
            e.FailureBoundary = e.Signal.StructuralInvalidation;
            e.FailureBreakPrice = _m1Bars.ClosePrices[i];
            e.CapitalDirection = V72OppositeDirection(e.Signal.Direction);
            e.FailureRetestExpiryUtc = MinDate(e.ExpiryUtc, V72NextM15Boundary(utc).AddMinutes(15));
            if (e.FailureRetestExpiryUtc <= utc.AddSeconds(1)) return false;
            e.State = V71ExpansionState.PROOF_WAIT;
            e.CapitalReady = false;
            e.CapitalLane = "FAMILY_NATIVE_FAILURE_WAIT";
            Print("[V72-FAMILY-FAILURE-BREAK] cid={0} family={1} originalDir={2} continuationDir={3} boundary={4:F5} close={5:F5} expiry={6:o}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Signal.Direction, e.CapitalDirection,
                e.FailureBoundary, e.FailureBreakPrice, e.FailureRetestExpiryUtc);
            return true;
        }

        private bool V72ProcessFamilyNativeFailureRetest(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || !e.FailureBreakObserved || !e.FailureContinuation)
                return false;
            if (!e.FailureBreakUtc.HasValue || utc <= e.FailureBreakUtc.Value) return false;
            if (utc >= e.FailureRetestExpiryUtc)
            {
                e.IsActive = false;
                e.State = V71ExpansionState.EXPIRED;
                Print("[V72-FAMILY-FAILURE-EXPIRE] cid={0} family={1}", e.CandidateId, V71FamilyKey(e.Signal.PatternName));
                return true;
            }

            TradeDirection direction = e.CapitalDirection;
            double boundary = e.FailureBoundary;
            double o = _m1Bars.OpenPrices[i], close = _m1Bars.ClosePrices[i];
            double high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i];
            bool touched = direction == TradeDirection.Buy ? low <= boundary : high >= boundary;
            bool closedContinuationSide = direction == TradeDirection.Buy ? close > boundary : close < boundary;
            bool directional = direction == TradeDirection.Buy ? close > o : close < o;
            if (!(touched && closedContinuationSide && directional)) return false;

            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            double entry = close;
            double stop = direction == TradeDirection.Buy ? low - buffer : high + buffer;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;
            double costPrice = PipsToPrice(ModeledCostPips());
            double target = direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            if (!GeometryValid(direction, entry, stop, target)) return false;
            double netRr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                           Math.Max(1e-9, PriceToPips(risk));
            if (netRr + 1e-9 < MinimumNetRR) return false;

            bool allowed = V72FamilyNativeCapitalSemanticsAllowed(e) &&
                           e.CapitalEligible && !e.CoreOverlapObserved;
            e.Route = HarmonicRoute.FAILURE_CONTINUATION;
            V72InitializeFamilyNativeShadow(e, utc, direction, entry, stop, target, netRr,
                1.0, allowed ? "FAMILY_NATIVE_FAILURE_CONTINUATION" : "FAMILY_NATIVE_SHADOW_ONLY", allowed);
            Print("[V72-FAMILY-FAILURE-RETEST] cid={0} family={1} dir={2} entry={3:F5} stop={4:F5} target={5:F5} netRR={6:F3} capitalSemantics={7}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), direction, entry, stop, target, netRr, allowed);
            return true;
        }
    }
}
