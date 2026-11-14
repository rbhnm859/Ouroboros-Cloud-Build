using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    // Context / family-resolution support layer.
    // Behavior-preserving extraction from HarmonyBotV71.cs; no thresholds or rules changed.
    public partial class HarmonyBotV71
    {

        private MtfConflict ClassifyMtfConflict(TradeDirection direction, HarmonicState h4, HarmonicState h1)
        {
            int same = 0, opposite = 0, neutral = 0;
            foreach (var s in new[] { h4, h1 })
            {
                if (s == HarmonicState.Neutral) neutral++;
                else if ((direction == TradeDirection.Buy && s == HarmonicState.Bullish) ||
                         (direction == TradeDirection.Sell && s == HarmonicState.Bearish)) same++;
                else opposite++;
            }
            if (same == 2) return MtfConflict.ALIGNED;
            if (same == 1 && neutral == 1) return MtfConflict.SUPPORTED;
            if (same == 1 && opposite == 1) return MtfConflict.TRANSITION;
            if (opposite == 2) return MtfConflict.CONFLICT;
            return MtfConflict.NEUTRAL;
        }

        private RegimeSnapshot BuildRegimeSnapshot()
        {
            int h4 = LastClosedIndex(_h4Bars);
            int h1 = LastClosedIndex(_h1Bars);
            int m15 = LastClosedIndex(_m15Bars);
            var r = new RegimeSnapshot();

            double h4e50 = Ema(_h4Bars.ClosePrices, 50, h4);
            double h4e200 = Ema(_h4Bars.ClosePrices, 200, h4);
            double h4e50Prev = Ema(_h4Bars.ClosePrices, 50, Math.Max(1, h4 - 3));
            double h1e50 = Ema(_h1Bars.ClosePrices, 50, h1);
            double h1e200 = Ema(_h1Bars.ClosePrices, 200, h1);
            double h1e50Prev = Ema(_h1Bars.ClosePrices, 50, Math.Max(1, h1 - 4));

            int h4Dir = TrendVote(h4e50, h4e200, h4e50 - h4e50Prev);
            int h1Dir = TrendVote(h1e50, h1e200, h1e50 - h1e50Prev);
            int sum = h4Dir + h1Dir;
            r.TrendDirection = sum > 0 ? TradeDirection.Buy : sum < 0 ? TradeDirection.Sell : TradeDirection.Neutral;
            r.Transition = h4Dir != 0 && h1Dir != 0 && h4Dir != h1Dir;

            double atrNow = Atr(_m15Bars, 14, m15);
            double atrBase = RollingAtrMean(_m15Bars, 14, m15, 120);
            r.AtrM15Pips = PriceToPips(Math.Max(0, atrNow));
            r.AtrRatio = atrBase > 0 ? atrNow / atrBase : 1.0;
            r.AtrPercentile = AtrPercentile(_m15Bars, 14, m15, 120);
            r.Efficiency = EfficiencyRatio(_m15Bars.ClosePrices, m15, 20);
            r.AdxH1 = Adx(_h1Bars, 14, h1);
            r.AdxH4 = Adx(_h4Bars, 14, h4);
            double adxH1Prev = Adx(_h1Bars, 14, Math.Max(30, h1 - 4));
            r.AdxH1Slope = r.AdxH1 - adxH1Prev;
            r.TrendStrength = VClamp(((r.AdxH1 + r.AdxH4) * 0.5) / 40.0);
            double refEma = h1e50;
            double h1Atr = Atr(_h1Bars, 14, h1);
            r.ExtensionAtr = h1Atr > 0 ? Math.Abs(_h1Bars.ClosePrices[h1] - refEma) / h1Atr : 0;
            return r;
        }

        private HarmonicRoute RouteSignalV34(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            bool trendAligned = r.TrendDirection == s.Direction;
            bool trendOpposed = r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            bool strong = s.GeometryQuality >= .68 && s.PrzConfluence >= .68 && s.Confidence >= .64;
            bool exhaustion = trendOpposed && r.ExtensionAtr >= 1.20 && strong && r.AtrRatio <= 1.80;
            bool transition = conflict == MtfConflict.TRANSITION || r.Transition || r.TrendDirection == TradeDirection.Neutral;

            if ((conflict == MtfConflict.ALIGNED || conflict == MtfConflict.SUPPORTED || conflict == MtfConflict.NEUTRAL) &&
                trendAligned && r.Efficiency >= .18 && r.AtrRatio >= .55 && r.AtrRatio <= 1.75)
                return HarmonicRoute.TREND_ALIGNED_REVERSAL;

            if (exhaustion && (conflict != MtfConflict.CONFLICT || (s.GeometryQuality >= .75 && s.PrzConfluence >= .75)))
                return HarmonicRoute.EXHAUSTION_REVERSAL;

            if (transition && strong && r.AtrRatio >= .50 && r.AtrRatio <= 1.80)
                return HarmonicRoute.TRANSITION_REVERSAL;

            return HarmonicRoute.NO_TRADE;
        }


        private HarmonicRoute StructuredRecallRoute(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (s == null || r == null) return HarmonicRoute.NO_TRADE;
            if (conflict == MtfConflict.CONFLICT) return HarmonicRoute.NO_TRADE;
            if (s.GeometryQuality < RecallMinGeometry || s.PrzConfluence < RecallMinPrz || s.Confidence < RecallMinConfidence)
                return HarmonicRoute.NO_TRADE;
            if (r.AtrRatio < .55 || r.AtrRatio > 1.75 || r.Efficiency < .14)
                return HarmonicRoute.NO_TRADE;

            bool aligned = r.TrendDirection == s.Direction;
            bool opposed = r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            bool transition = r.Transition || conflict == MtfConflict.TRANSITION || r.TrendDirection == TradeDirection.Neutral;

            if (aligned && (conflict == MtfConflict.ALIGNED || conflict == MtfConflict.SUPPORTED || conflict == MtfConflict.NEUTRAL))
                return HarmonicRoute.TREND_ALIGNED_REVERSAL;

            if (opposed && r.ExtensionAtr >= 1.00 && r.AdxH1Slope <= .50)
                return HarmonicRoute.EXHAUSTION_REVERSAL;

            if (transition && r.AdxH1Slope <= 1.00)
                return HarmonicRoute.TRANSITION_REVERSAL;

            return HarmonicRoute.NO_TRADE;
        }

        private HarmonicRoute RouteSignal(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            HarmonicRoute baseRoute = RouteSignalV34(s, conflict, r);
            if (baseRoute == HarmonicRoute.NO_TRADE && EnableStructuredRecallExpansion)
            {
                baseRoute = StructuredRecallRoute(s, conflict, r);
                if (baseRoute != HarmonicRoute.NO_TRADE)
                {
                    _structuredRecallAdmitted++;
                    Print("[V51-RECALL-ADMIT] pattern={0} direction={1} route={2} conflict={3} geometry={4:F3} prz={5:F3} confidence={6:F3} efficiency={7:F3} atrRatio={8:F3} extensionAtr={9:F3}",
                        s.PatternName, s.Direction, baseRoute, conflict, s.GeometryQuality, s.PrzConfluence, s.Confidence,
                        r.Efficiency, r.AtrRatio, r.ExtensionAtr);
                }
            }
            if (baseRoute == HarmonicRoute.NO_TRADE)
                return HarmonicRoute.NO_TRADE;

            if (baseRoute == HarmonicRoute.TRANSITION_REVERSAL && EnableTransitionProofGate)
            {
                bool actualStructuralTransition = r.Transition || conflict == MtfConflict.TRANSITION;
                if (!actualStructuralTransition)
                {
                    _transitionProofRejected++;
                    Print("[V51-TRANSITION-PROOF-REJECT] pattern={0} conflict={1} transition={2} adxSlope={3:F2}",
                        s.PatternName, conflict, r.Transition, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            if (baseRoute == HarmonicRoute.TRANSITION_REVERSAL && EnableTransitionStateVeto)
            {
                bool actualStateDisagreement = r.Transition || conflict == MtfConflict.TRANSITION;
                bool trendNotStrengthening = r.AdxH1Slope <= 0;
                if (!(actualStateDisagreement && trendNotStrengthening))
                {
                    _regimeRejected++;
                    Print("[V51-ROUTE-VETO] type=TRANSITION_STATE conflict={0} transition={1} adxSlope={2:F2}",
                        conflict, r.Transition, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            if (baseRoute == HarmonicRoute.EXHAUSTION_REVERSAL && EnableExhaustionEvidenceVeto)
            {
                bool structurallyExtended = r.ExtensionAtr >= 1.20;
                bool trendNotStrengthening = r.AdxH1Slope <= 0;
                if (!(structurallyExtended && trendNotStrengthening))
                {
                    _regimeRejected++;
                    Print("[V51-ROUTE-VETO] type=EXHAUSTION_EVIDENCE extensionAtr={0:F3} adxSlope={1:F2}",
                        r.ExtensionAtr, r.AdxH1Slope);
                    return HarmonicRoute.NO_TRADE;
                }
            }

            return baseRoute;
        }

        private double HarmonicRobustnessScore(PatternSignal s)
        {
            if (s == null) return 0;
            return VClamp(.35 * s.GeometryQuality + .25 * s.PrzConfluence +
                          .20 * s.TimeSymmetry + .20 * s.PivotQuality);
        }

        private bool HarmonicRobustnessEligible(PatternSignal s, double score)
        {
            if (s == null) return false;
            if (score < MinHarmonicRobustness) return false;
            // Prevent a strong ratio fit from fully compensating for weak temporal/pivot structure.
            if (s.TimeSymmetry < .25 || s.PivotQuality < .25) return false;
            return true;
        }

        private double RegimeContextScore(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (s == null || r == null) return 0;
            double mtf = conflict == MtfConflict.ALIGNED ? 1.0 :
                         conflict == MtfConflict.SUPPORTED ? .85 :
                         conflict == MtfConflict.TRANSITION ? .65 :
                         conflict == MtfConflict.NEUTRAL ? .60 : .30;
            double directionFit = r.TrendDirection == s.Direction ? 1.0 :
                                  r.TrendDirection == TradeDirection.Neutral ? .65 : .35;
            double volHealth = 1.0 - Math.Min(1.0, Math.Abs(r.AtrPercentile - .55) / .55);
            double persistence = VClamp(.55 * r.Efficiency + .45 * r.TrendStrength);
            return VClamp(.30 * mtf + .25 * directionFit + .20 * volHealth + .25 * persistence);
        }

        private bool CapitalFeasibilityEligible(CandidateRecord c, out double minL0Risk, out double minL0Margin)
        {
            minL0Risk = 0;
            minL0Margin = 0;
            if (c == null || c.Signal == null || _symbol == null) return false;
            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            if ((c.Signal.Direction == TradeDirection.Buy && stop >= anchor) ||
                (c.Signal.Direction == TradeDirection.Sell && stop <= anchor))
                return false;

            double slPips = PriceToPips(Math.Abs(anchor - stop));
            if (slPips < MinStopLossPips) return false;
            double minVolume = _symbol.VolumeInUnitsMin;
            if (minVolume <= 0) return false;
            minL0Risk = minVolume * _symbol.PipValue * (slPips + ModeledCostPips());
            minL0Margin = EstimatedMargin(c.Signal.Direction, minVolume);
            double budget = Account.Equity * BasketRiskPercent / 100.0;
            if (minL0Risk > budget + 1e-8) return false;
            if (Account.FreeMargin - minL0Margin < budget * MinFreeMarginRiskMultiple) return false;
            return true;
        }

        private bool RouteSpecificM1EvidencePass(int i, PatternSignal s, HarmonicRoute route)
        {
            if (i < 3 || i >= _m1Bars.Count) return false;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);

            bool reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                reclaim = c > s.PrzLow && c >= pc;
                bos1 = c > ph1;
                bos2 = c > ph2;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl1 && c > pl1;
            }
            else
            {
                reclaim = c < s.PrzHigh && c <= pc;
                bos1 = c < pl1;
                bos2 = c < pl2;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph1 && c < ph1;
            }

            if (route == HarmonicRoute.TRANSITION_REVERSAL)
                return reclaim && bos2 && rejection;
            if (route == HarmonicRoute.EXHAUSTION_REVERSAL)
                return reclaim && rejection && (failedExtension || bos1);
            return reclaim && (bos1 || failedExtension);
        }

        private bool IsFamilyCompletionLane(string pattern)
        {
            return pattern == "Gartley" || pattern == "Bat" || pattern == "Alt Bat" ||
                   pattern == "Butterfly" || pattern == "Crab" || pattern == "Deep Crab" ||
                   pattern == "Deep Gartley" || pattern == "Rat" || pattern == "5-0";
        }

        private void IncrementCounter(Dictionary<string, int> map, string key)
        {
            if (string.IsNullOrWhiteSpace(key)) key = "UNKNOWN";
            int n; map.TryGetValue(key, out n); map[key] = n + 1;
        }

        private bool UpdateFamilyCompletionEvidence(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || i >= _m1Bars.Count || c == null || c.Signal == null) return false;
            var sig = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);
            bool buy = sig.Direction == TradeDirection.Buy;
            bool directional = buy ? cl > o : cl < o;
            bool reclaim = buy ? (cl > sig.PrzLow && cl >= pc) : (cl < sig.PrzHigh && cl <= pc);
            bool bos = buy ? cl > ph : cl < pl;
            bool rejection = buy ? Math.Max(0, Math.Min(o, cl) - l) >= body * .5 : Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
            bool sweep = buy ? l < pl : h > ph;
            bool failedExtension = buy ? (l < pl && cl > pl) : (h > ph && cl < ph);
            bool insidePrz = cl >= Math.Min(sig.PrzLow, sig.PrzHigh) && cl <= Math.Max(sig.PrzLow, sig.PrzHigh);
            bool displacement = atr > 0 && body >= atr * .30;
            bool retest = insidePrz || Math.Abs(cl - (sig.PrzLow + sig.PrzHigh) * .5) <= Math.Max(atr * .25, _symbol.PipSize);

            c.FamilyDirectional |= directional; c.FamilyReclaim |= reclaim; c.FamilyBos |= bos;
            c.FamilyRejection |= rejection; c.FamilySweep |= sweep; c.FamilyFailedExtension |= failedExtension;
            c.FamilyInsidePrz |= insidePrz; c.FamilyDisplacement |= displacement; c.FamilyRetest |= retest;

            string p = sig.PatternName ?? "";
            bool retracement = p == "Gartley" || p == "Bat" || p == "Deep Gartley" || p == "Rat";
            bool extension = p == "Alt Bat" || p == "Butterfly" || p == "Crab" || p == "Deep Crab";
            if (retracement)
            {
                score = (c.FamilyReclaim ? .30 : 0) + ((c.FamilyRejection || c.FamilyFailedExtension) ? .25 : 0) +
                        (c.FamilyBos ? .25 : 0) + (c.FamilyDisplacement ? .20 : 0);
                return c.FamilyReclaim && (c.FamilyRejection || c.FamilyFailedExtension) &&
                       (c.FamilyBos || c.FamilyDisplacement) && score >= .75;
            }
            if (extension)
            {
                score = (c.FamilySweep ? .20 : 0) + (c.FamilyFailedExtension ? .25 : 0) +
                        ((c.FamilyReclaim || c.FamilyInsidePrz) ? .25 : 0) +
                        (c.FamilyBos ? .20 : 0) + (c.FamilyDisplacement ? .10 : 0);
                return c.FamilySweep && c.FamilyFailedExtension && (c.FamilyReclaim || c.FamilyInsidePrz) &&
                       (c.FamilyBos || c.FamilyDisplacement) && score >= .75;
            }
            if (p == "5-0")
            {
                score = (c.FamilyFailedExtension ? .25 : 0) + (c.FamilyBos ? .30 : 0) +
                        (c.FamilyRetest ? .25 : 0) + (c.FamilyDirectional ? .20 : 0);
                return c.FamilyFailedExtension && c.FamilyBos && c.FamilyRetest && c.FamilyDirectional && score >= .80;
            }
            return false;
        }

        private bool UpdatePatternNativeM1State(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || c == null || c.Signal == null) return false;
            var s = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i], h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double prevBody = Math.Max(Math.Abs(_m1Bars.ClosePrices[i - 1] - _m1Bars.OpenPrices[i - 1]), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);
            bool bullish = s.Direction == TradeDirection.Buy;
            bool directional = bullish ? cl > o : cl < o;
            bool reclaim = bullish ? (cl > s.PrzLow && cl >= pc) : (cl < s.PrzHigh && cl <= pc);
            bool bos = bullish ? cl > ph : cl < pl;
            bool rejection = bullish ? Math.Max(0, Math.Min(o, cl) - l) >= body * .5 : Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
            bool failedExtension = bullish ? (l < pl && cl > pl) : (h > ph && cl < ph);
            bool sweep = bullish ? l < pl : h > ph;
            bool insidePrz = cl >= Math.Min(s.PrzLow, s.PrzHigh) && cl <= Math.Max(s.PrzLow, s.PrzHigh);
            bool displacement = atr > 0 && body >= atr * .30;
            bool deceleration = body <= prevBody * .85;
            bool retest = insidePrz || Math.Abs(cl - (s.PrzLow + s.PrzHigh) * .5) <= Math.Max(atr * .25, _symbol.PipSize);

            string p = s.PatternName ?? "";
            bool retracement = p == "Gartley" || p == "Bat" || p == "Deep Gartley" || p == "Rat";
            bool extension = p == "Alt Bat" || p == "Butterfly" || p == "Crab" || p == "Deep Crab";
            bool abcd = p == "AB=CD";
            bool transition = p == "Shark" || p == "5-0";
            bool cypher = p == "Cypher";

            if (retracement)
            {
                int prior = c.NativeStage;
                if (prior == 0 && rejection) c.NativeStage = 1;
                else if (prior == 1 && reclaim) c.NativeStage = 2;
                else if (prior == 2 && bos) c.NativeStage = 3;
                else if (prior == 3 && displacement) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (extension)
            {
                int prior = c.NativeStage;
                if (prior == 0 && sweep) c.NativeStage = 1;
                else if (prior == 1 && failedExtension) c.NativeStage = 2;
                else if (prior == 2 && insidePrz) c.NativeStage = 3;
                else if (prior == 3 && bos) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (abcd)
            {
                int prior = c.NativeStage;
                if (prior == 0 && deceleration) c.NativeStage = 1;
                else if (prior == 1 && failedExtension) c.NativeStage = 2;
                else if (prior == 2 && directional && displacement) c.NativeStage = 3;
                else if (prior == 3 && bos) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (transition)
            {
                int prior = c.NativeStage;
                if (prior == 0 && failedExtension) c.NativeStage = 1;
                else if (prior == 1 && bos) c.NativeStage = 2;
                else if (prior == 2 && retest) c.NativeStage = 3;
                else if (prior == 3 && directional) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }
            if (cypher)
            {
                int prior = c.NativeStage;
                if (prior == 0 && rejection) c.NativeStage = 1;
                else if (prior == 1 && reclaim) c.NativeStage = 2;
                else if (prior == 2 && bos) c.NativeStage = 3;
                else if (prior == 3 && displacement) c.NativeStage = 4;
                score = c.NativeStage / 4.0;
                return c.NativeStage >= 4;
            }

            score = 0;
            return false;
        }

        private bool UpdateM1TemporalEvidence(int i, CandidateRecord c, out double score)
        {
            score = 0;
            if (i < 3 || i >= _m1Bars.Count || c == null || c.Signal == null) return false;
            var s = c.Signal;
            double o = _m1Bars.OpenPrices[i], cl = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(cl - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);

            bool directional, reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = cl > o;
                reclaim = cl > s.PrzLow && cl >= pc;
                bos1 = cl > ph1;
                bos2 = cl > ph2;
                rejection = Math.Max(0, Math.Min(o, cl) - l) >= body * .5;
                failedExtension = l < pl1 && cl > pl1;
            }
            else
            {
                directional = cl < o;
                reclaim = cl < s.PrzHigh && cl <= pc;
                bos1 = cl < pl1;
                bos2 = cl < pl2;
                rejection = Math.Max(0, h - Math.Max(o, cl)) >= body * .5;
                failedExtension = h > ph1 && cl < ph1;
            }
            bool displacement = atr > 0 && body >= atr * .30;

            c.TemporalDirectional |= directional;
            c.TemporalReclaim |= reclaim;
            c.TemporalBos1 |= bos1;
            c.TemporalBos2 |= bos2;
            c.TemporalRejection |= rejection;
            c.TemporalFailedExtension |= failedExtension;
            c.TemporalDisplacement |= displacement;

            score = (c.TemporalDirectional ? .10 : 0) + (c.TemporalReclaim ? .20 : 0) +
                    (c.TemporalBos1 ? .20 : 0) + (c.TemporalBos2 ? .10 : 0) +
                    (c.TemporalRejection ? .15 : 0) + (c.TemporalFailedExtension ? .15 : 0) +
                    (c.TemporalDisplacement ? .10 : 0);

            if (c.Route == HarmonicRoute.EXHAUSTION_REVERSAL)
                return c.TemporalReclaim && c.TemporalRejection &&
                       (c.TemporalFailedExtension || c.TemporalBos1) && score >= .60;
            if (c.Route == HarmonicRoute.TRANSITION_REVERSAL)
                return c.TemporalReclaim && c.TemporalBos2 && c.TemporalRejection && score >= .65;
            return c.TemporalReclaim && (c.TemporalBos1 || c.TemporalFailedExtension) &&
                   c.TemporalDirectional && score >= .55;
        }

        private double EnhancedM1ConfirmationScore(int i, PatternSignal s, HarmonicRoute route, RegimeSnapshot regime)
        {
            if (i < 3 || i >= _m1Bars.Count) return 0;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i],
                   h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1];
            double ph1 = _m1Bars.HighPrices[i - 1], pl1 = _m1Bars.LowPrices[i - 1];
            double ph2 = Math.Max(ph1, _m1Bars.HighPrices[i - 2]);
            double pl2 = Math.Min(pl1, _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);
            double atr = Atr(_m1Bars, 14, i);

            bool directional, reclaim, bos1, bos2, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = c > o;
                reclaim = c > s.PrzLow && c >= pc;
                bos1 = c > ph1;
                bos2 = c > ph2;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl1 && c > pl1;
            }
            else
            {
                directional = c < o;
                reclaim = c < s.PrzHigh && c <= pc;
                bos1 = c < pl1;
                bos2 = c < pl2;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph1 && c < ph1;
            }

            bool displacement = atr > 0 && body >= atr * .30;
            double score = (directional ? .15 : 0) + (reclaim ? .15 : 0) +
                           (bos1 ? .20 : 0) + (bos2 ? .15 : 0) +
                           (rejection ? .15 : 0) + (failedExtension ? .10 : 0) +
                           (displacement ? .10 : 0);

            // Counter-trend exhaustion requires actual rejection/structure evidence, not candle color alone.
            if (route == HarmonicRoute.EXHAUSTION_REVERSAL && !(rejection && (bos1 || failedExtension)))
                score = Math.Min(score, .55);
            return VClamp(score);
        }

        private double EnhancedM1Threshold(HarmonicRoute route)
        {
            return route == HarmonicRoute.EXHAUSTION_REVERSAL ? .70 :
                   route == HarmonicRoute.TRANSITION_REVERSAL ? .65 : .55;
        }

        private double DirectionalIndex(Bars bars, int period, int end)
        {
            if (bars == null || end < period + 1 || end >= bars.Count) return 0;
            double trSum = 0, plusSum = 0, minusSum = 0;
            int start = Math.Max(1, end - period + 1);
            for (int i = start; i <= end; i++)
            {
                double up = bars.HighPrices[i] - bars.HighPrices[i - 1];
                double down = bars.LowPrices[i - 1] - bars.LowPrices[i];
                double plusDm = up > down && up > 0 ? up : 0;
                double minusDm = down > up && down > 0 ? down : 0;
                double prevClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(bars.HighPrices[i] - bars.LowPrices[i],
                    Math.Max(Math.Abs(bars.HighPrices[i] - prevClose), Math.Abs(bars.LowPrices[i] - prevClose)));
                trSum += tr; plusSum += plusDm; minusSum += minusDm;
            }
            if (trSum <= 0) return 0;
            double plusDi = 100.0 * plusSum / trSum;
            double minusDi = 100.0 * minusSum / trSum;
            double den = plusDi + minusDi;
            return den > 0 ? 100.0 * Math.Abs(plusDi - minusDi) / den : 0;
        }

        private double Adx(Bars bars, int period, int end)
        {
            if (bars == null || end < period * 2 || end >= bars.Count) return 0;
            int start = Math.Max(period + 1, end - period + 1);
            double sum = 0; int n = 0;
            for (int i = start; i <= end; i++)
            {
                double dx = DirectionalIndex(bars, period, i);
                if (dx < 0) continue;
                sum += dx; n++;
            }
            return n > 0 ? sum / n : 0;
        }

        // ---------------- M1 confirmation / scheduler ----------------

        private bool BarTouchesPrz(int i, PatternSignal s)
        {
            if (i < 0 || i >= _m1Bars.Count) return false;
            return _m1Bars.HighPrices[i] >= s.PrzLow && _m1Bars.LowPrices[i] <= s.PrzHigh;
        }

        private double M1ConfirmationScore(int i, PatternSignal s)
        {
            if (i < 2 || i >= _m1Bars.Count) return 0;
            double o = _m1Bars.OpenPrices[i], c = _m1Bars.ClosePrices[i], h = _m1Bars.HighPrices[i], l = _m1Bars.LowPrices[i];
            double po = _m1Bars.OpenPrices[i - 1], pc = _m1Bars.ClosePrices[i - 1], ph = _m1Bars.HighPrices[i - 1], pl = _m1Bars.LowPrices[i - 1];
            double body = Math.Max(Math.Abs(c - o), _symbol.PipSize);
            bool directional, reclaim, bos, rejection, failedExtension;
            if (s.Direction == TradeDirection.Buy)
            {
                directional = c > o;
                reclaim = c > s.PrzLow && c >= pc;
                bos = c > ph;
                rejection = Math.Max(0, Math.Min(o, c) - l) >= body * .5;
                failedExtension = l < pl && c > pl;
            }
            else
            {
                directional = c < o;
                reclaim = c < s.PrzHigh && c <= pc;
                bos = c < pl;
                rejection = Math.Max(0, h - Math.Max(o, c)) >= body * .5;
                failedExtension = h > ph && c < ph;
            }
            return (directional ? .20 : 0) + (reclaim ? .20 : 0) + (bos ? .30 : 0) + (rejection ? .15 : 0) + (failedExtension ? .15 : 0);
        }

        private double CandidateRank(CandidateRecord c)
        {
            double mtf = c.Conflict == MtfConflict.ALIGNED ? 1.0 :
                         c.Conflict == MtfConflict.SUPPORTED ? .85 :
                         c.Conflict == MtfConflict.TRANSITION ? .70 :
                         c.Conflict == MtfConflict.NEUTRAL ? .60 : .40;
            double regime = VClamp(.45 * c.Regime.Efficiency + .25 * (1.0 - Math.Min(1.0, Math.Abs(c.Regime.AtrRatio - 1.0))) +
                                   .30 * Math.Min(1.0, c.Regime.ExtensionAtr / 2.0));
            double baseRank = .25 * c.Signal.GeometryQuality + .15 * c.Signal.PrzConfluence + .15 * mtf + .15 * regime +
                              .15 * c.ConfirmationScore + .15 * VClamp(c.NetRR / 3.0);
            if (!EnableFrequencyAgingPriority || CandidateAgeRankBoost <= 0) return baseRank;
            double ttl = Math.Max(60.0, (c.ExpiryUtc - c.DetectedUtc).TotalSeconds);
            double age = Math.Max(0.0, (Server.Time.ToUniversalTime() - c.DetectedUtc).TotalSeconds);
            double ageFrac = VClamp(age / ttl);
            return baseRank + CandidateAgeRankBoost * ageFrac;
        }

        private double CurrentSpreadPips()
        {
            return PriceToPips(Math.Max(0, _symbol.Ask - _symbol.Bid));
        }

    }
}
