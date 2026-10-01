using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    // Research-only / challenger-resolution boundary.
    // No detector ratios, protected-core ownership, risk ceilings, or execution semantics
    // are defined here. Changes in this file must remain shadow/fail-closed until gates pass.
    public partial class HarmonyBotV71
    {
        // ---------------- V71 protected-core incremental expansion ----------------

        private string V71FamilyKey(string pattern)
        {
            if (pattern == "AB=CD") return "ABCD";
            if (pattern == "5-0") return "FiveZero";
            return (pattern ?? "UNKNOWN").Replace(" ", "").Replace("-", "");
        }

        private double V71MtfScore(MtfConflict c)
        {
            return c == MtfConflict.ALIGNED ? 1.0 :
                   c == MtfConflict.SUPPORTED ? .85 :
                   c == MtfConflict.TRANSITION ? .65 :
                   c == MtfConflict.NEUTRAL ? .55 : .25;
        }

        private HarmonicRoute V71ExpansionRoute(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (r != null && (r.Transition || conflict == MtfConflict.TRANSITION))
                return HarmonicRoute.TRANSITION_REVERSAL;
            bool opposed = r != null && r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            if (opposed && r.ExtensionAtr >= 1.0)
                return HarmonicRoute.EXHAUSTION_REVERSAL;
            return HarmonicRoute.TREND_ALIGNED_REVERSAL;
        }

        private bool V71ExpansionIntegrity(PatternSignal s)
        {
            if (s == null || s.Profile == null) return false;
            if (string.IsNullOrWhiteSpace(s.PatternName)) return false;
            if (!double.IsFinite(s.GeometryQuality) || !double.IsFinite(s.PrzConfluence) ||
                !double.IsFinite(s.Confidence) || !double.IsFinite(s.StructuralInvalidation))
                return false;
            if (s.StructuralInvalidation <= 0 || s.PrzHigh <= s.PrzLow) return false;
            return true;
        }

        private List<PatternSignal> V71SelectExpansionSignals(IEnumerable<PatternSignal> pool, int maxCandidates)
        {
            int limit = Math.Max(8, Math.Min(32, maxCandidates));
            var ordered = (pool ?? Enumerable.Empty<PatternSignal>())
                .Where(x => x != null && x.Profile != null)
                // Expansion research must preserve competing family interpretations of the
                // same XABCD geometry. Core canonical identity remains geometry-only.
                .GroupBy(x => V71FamilyKey(x.PatternName) + "|" + BuildSetupGeometryKey(x))
                .Select(g => g.OrderByDescending(x => x.Confidence).ThenByDescending(x => x.GeometryQuality).First())
                .OrderByDescending(x => x.Confidence)
                .ThenByDescending(x => x.GeometryQuality)
                .ToList();

            if (!EnableV71FamilyBalancedCensus)
                return ordered.Take(limit).ToList();

            int familyCap = Math.Max(2, Math.Min(12, V71PerFamilyCensusCap));
            int abcdBudget = (int)Math.Floor(limit * Math.Max(0, Math.Min(25, V71AbcdCensusSharePercent)) / 100.0);
            var familyBuckets = ordered
                .Where(x => !string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                .GroupBy(x => V71FamilyKey(x.PatternName))
                .OrderBy(g => g.Key)
                .ToDictionary(
                    g => g.Key,
                    g => new Queue<PatternSignal>(g.Take(familyCap)));

            var selected = new List<PatternSignal>();
            int nonAbcdBudget = Math.Max(0, limit - abcdBudget);
            bool progressed = true;
            while (selected.Count < nonAbcdBudget && progressed)
            {
                progressed = false;
                foreach (var key in familyBuckets.Keys.OrderBy(x => x).ToList())
                {
                    Queue<PatternSignal> q = familyBuckets[key];
                    if (q.Count == 0) continue;
                    selected.Add(q.Dequeue());
                    progressed = true;
                    if (selected.Count >= nonAbcdBudget) break;
                }
            }

            if (abcdBudget > 0 && selected.Count < limit)
            {
                foreach (var x in ordered.Where(x => string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                                         .Take(Math.Min(abcdBudget, limit - selected.Count)))
                    selected.Add(x);
            }

            return selected;
        }

        private void V71TrackExpansionSignal(PatternSignal s, HarmonicState h4, HarmonicState h1, RegimeSnapshot regime)
        {
            if (!V71ExpansionIntegrity(s)) return;
            string setup = BuildSetupGeometryKey(s);
            bool coreOverlap = _executedSetupKeys.Contains(setup) || _activeSetupOwners.ContainsKey(setup);
            string id = V71FamilyKey(s.PatternName) + "|" + setup;
            if (_v71Expansion.ContainsKey(id)) return;

            var conflict = ClassifyMtfConflict(s.Direction, h4, h1);
            string fam = V71FamilyKey(s.PatternName);
            var e = new V71ExpansionCandidate
            {
                CandidateId = "V71EXP-" + V71StableHash32(id).ToString("X8", CultureInfo.InvariantCulture) + "-" +
                              s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture),
                IdentityKey = id,
                SetupKey = setup,
                Signal = s,
                Conflict = conflict,
                Regime = regime,
                Route = V71ExpansionRoute(s, conflict, regime),
                DetectedUtc = Server.Time.ToUniversalTime(),
                ExpiryUtc = Server.Time.ToUniversalTime().AddMinutes(15.0 * Math.Max(4, Math.Min(32, V71ExpansionTtlM15Bars))),
                State = V71ExpansionState.WAIT_PRZ,
                IsActive = true,
                CoreOverlapObserved = coreOverlap,
                CapitalEligible = !coreOverlap && !string.Equals(fam, "ABCD", StringComparison.OrdinalIgnoreCase),
                AbcdRole = string.IsNullOrWhiteSpace(s.ResearchRole) ? (fam == "ABCD" ? "ABCD_STANDALONE" : "PARENT_FAMILY") : s.ResearchRole
            };
            _v71Expansion[id] = e;
            _v71ExpansionDetected++;
            IncrementCounter(_v71FamilyTracked, fam);
            if (coreOverlap) IncrementCounter(_v71FamilyCoreOverlap, fam);
            Print("[V71-EXP-DETECTED] cid={0} setup={1} family={2} subtype={3} role={4} route={5} conflict={6} coreOverlap={7} capitalEligible={8} g={9:F4} prz={10:F4} conf={11:F4}",
                e.CandidateId, e.SetupKey, fam, s.HarmonicSubtype ?? s.PatternName, e.AbcdRole,
                e.Route, e.Conflict, e.CoreOverlapObserved, e.CapitalEligible,
                s.GeometryQuality, s.PrzConfluence, s.Confidence);
        }

        private uint V71StableHash32(string value)
        {
            unchecked
            {
                uint h = 2166136261u;
                foreach (char ch in value ?? "")
                {
                    h ^= (byte)(ch & 0xFF);
                    h *= 16777619u;
                    if (ch > 0xFF)
                    {
                        h ^= (byte)((ch >> 8) & 0xFF);
                        h *= 16777619u;
                    }
                }
                return h;
            }
        }

        private void V71RefreshExpansionDecisionContext(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return;
            var h4 = GetActiveHarmonicState(_h4Bars, H4SwingDepth, 220, 3);
            var h1 = GetActiveHarmonicState(_h1Bars, H1SwingDepth, 260, 4);
            var regime = BuildRegimeSnapshot();
            e.Conflict = ClassifyMtfConflict(e.Signal.Direction, h4, h1);
            e.Regime = regime;
            e.Route = V71ExpansionRoute(e.Signal, e.Conflict, regime);
        }

        private bool V71ExpansionM1Confirmation(int i, V71ExpansionCandidate e, out double score)
        {
            score = 0;
            if (e == null || e.Signal == null || i <= 2 || i >= _m1Bars.Count) return false;
            double close = _m1Bars.ClosePrices[i];
            bool structurallyAlive = e.Signal.Direction == TradeDirection.Buy
                ? close > e.Signal.StructuralInvalidation
                : close < e.Signal.StructuralInvalidation;
            if (!structurallyAlive) return false;

            if (EnableV72FamilyNativeCausalAlpha)
                return V72FamilyNativeCausalProof(i, e, out score);

            if (!EnableV71FamilyNativeConfirmation)
            {
                score = M1ConfirmationScore(i, e.Signal);
                bool directional = e.Signal.Direction == TradeDirection.Buy
                    ? close > _m1Bars.OpenPrices[i] || close > _m1Bars.ClosePrices[i - 1]
                    : close < _m1Bars.OpenPrices[i] || close < _m1Bars.ClosePrices[i - 1];
                return directional && score >= .50;
            }

            if (e.NativeEvidenceState == null)
            {
                e.NativeEvidenceState = new CandidateRecord
                {
                    CandidateId = e.CandidateId + "-SHADOW-DAG",
                    SetupKey = e.SetupKey,
                    Signal = e.Signal,
                    Route = e.Route,
                    Regime = e.Regime,
                    IsActive = true
                };
            }
            e.NativeEvidenceState.Route = e.Route;
            e.NativeEvidenceState.Regime = e.Regime;
            e.NativeConfirmBars++;
            double nativeScore;
            bool pass = UpdatePatternNativeM1State(i, e.NativeEvidenceState, out nativeScore);
            score = Math.Max(nativeScore, M1ConfirmationScore(i, e.Signal));
            return pass;
        }

        private double V71AtrFit(RegimeSnapshot r)
        {
            if (r == null) return .5;
            return VClamp(1.0 - Math.Abs(r.AtrRatio - 1.0));
        }

        private DateTime V72NextM15Boundary(DateTime utc)
        {
            utc = DateTime.SpecifyKind(utc, DateTimeKind.Utc);
            int minute = (utc.Minute / 15) * 15;
            DateTime baseBar = new DateTime(utc.Year, utc.Month, utc.Day, utc.Hour, minute, 0, DateTimeKind.Utc);
            DateTime next = baseBar.AddMinutes(15);
            return next <= utc ? next.AddMinutes(15) : next;
        }

        private TradeDirection V72CapitalDirection(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return TradeDirection.Neutral;
            return e.CapitalDirection != TradeDirection.Neutral ? e.CapitalDirection : e.Signal.Direction;
        }

        private TradeDirection V72OppositeDirection(TradeDirection d)
        {
            return d == TradeDirection.Buy ? TradeDirection.Sell :
                   d == TradeDirection.Sell ? TradeDirection.Buy : TradeDirection.Neutral;
        }

        private bool V72ArmCapitalPullback(DateTime utc, V71ExpansionCandidate e, TradeDirection direction,
            double entry, double stop, double target, double confirmationScore, string lane, bool capitalReady)
        {
            if (e == null || e.Signal == null || direction == TradeDirection.Neutral) return false;
            if (!GeometryValid(direction, entry, stop, target)) return false;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;
            double netRr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                           Math.Max(1e-9, PriceToPips(risk));
            if (netRr + 1e-9 < MinimumNetRR) return false;

            e.CapitalDirection = direction;
            e.EntryAnchor = entry;
            e.StructuralStop = stop;
            e.CanonicalTarget = target;
            e.RiskDistance = risk;
            e.TargetR = Math.Abs(target - entry) / risk;
            e.NetRR = netRr;
            e.ConfirmationScore = confirmationScore;
            e.RegimeScore = RegimeContextScore(e.Signal, e.Conflict, e.Regime);
            e.ModeledCostR = PipsToPrice(ModeledCostPips()) / risk;
            e.PullbackExpiryUtc = MinDate(e.ExpiryUtc, V72NextM15Boundary(utc));
            if (e.PullbackExpiryUtc <= utc.AddSeconds(1)) return false;
            e.AwaitingPullbackFill = true;
            e.PullbackFilled = false;
            e.ShadowStarted = false;
            e.ArmedUtc = null;
            e.CapitalReady = capitalReady;
            e.CapitalLane = lane ?? "UNKNOWN";
            if (!capitalReady) e.CapitalEligible = false;
            e.State = V71ExpansionState.ARMED;
            double originalRisk = Math.Abs(entry - e.Signal.StructuralInvalidation);
            e.AsymmetryCompression = e.FailureContinuation ? 1.0 :
                Math.Max(.10, originalRisk / Math.Max(risk, _symbol.PipSize));
            e.EdgeMean = e.NetRR;
            e.EdgeLcb = e.NetRR;
            e.ExpectedSlotHours = Math.Max(.25, (e.PullbackExpiryUtc - utc).TotalHours);
            e.ExpectedSlotHoursUcb = e.ExpectedSlotHours;
            e.SlotScore = e.AsymmetryCompression * e.NetRR / Math.Max(.25, e.ExpectedSlotHours);
            _v71ExpansionArmed++;
            IncrementCounter(_v71FamilyArmed, V71FamilyKey(e.Signal.PatternName));
            Print("[V72-BIFURCATION-PLAN] cid={0} lane={1} family={2} route={3} dir={4} entry={5:F5} stop={6:F5} target={7:F5} rr={8:F3} asym={9:F3} expiry={10:o}",
                e.CandidateId, e.CapitalLane, V71FamilyKey(e.Signal.PatternName), e.Route, direction,
                entry, stop, target, netRr, e.AsymmetryCompression, e.PullbackExpiryUtc);
            return true;
        }

        private bool V72PreparePullbackEntry(DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            if (e == null || e.Signal == null || !e.ReactionProved) return false;
            double proof = e.ReactionProofPrice;
            double extreme = e.ReactionExtremePrice;
            double displacement = e.Signal.Direction == TradeDirection.Buy ? proof - extreme : extreme - proof;
            if (displacement <= _symbol.PipSize) return false;
            double entry = e.Signal.Direction == TradeDirection.Buy
                ? proof - .618 * displacement
                : proof + .618 * displacement;

            double originalStop = e.Signal.StructuralInvalidation;
            double reactionBuffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            double reactionStop = e.Signal.Direction == TradeDirection.Buy
                ? extreme - reactionBuffer
                : extreme + reactionBuffer;
            double stop = e.Signal.Direction == TradeDirection.Buy
                ? Math.Max(originalStop, reactionStop)
                : Math.Min(originalStop, reactionStop);
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;

            double canonical, canonicalRr;
            if (!SelectCanonicalBasketTarget(e.Signal, entry, stop, out canonical, out canonicalRr))
                return false;
            double costPrice = PipsToPrice(ModeledCostPips());
            double target = e.Signal.Direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            bool canonicalCovers = e.Signal.Direction == TradeDirection.Buy ? canonical >= target : canonical <= target;
            if (!canonicalCovers) return false;
            string lane = e.Route == HarmonicRoute.EXHAUSTION_REVERSAL ? "EXHAUSTION_REVERSAL" : "TRANSITION_SHADOW";
            bool capitalReady = e.Route == HarmonicRoute.EXHAUSTION_REVERSAL;
            return V72ArmCapitalPullback(utc, e, e.Signal.Direction, entry, stop, target,
                confirmationScore, lane, capitalReady);
        }

        private bool V72PrepareTrendVirtualProof(DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            if (e == null || e.Signal == null || !e.ReactionProved) return false;
            double proof = e.ReactionProofPrice;
            double extreme = e.ReactionExtremePrice;
            double displacement = e.Signal.Direction == TradeDirection.Buy ? proof - extreme : extreme - proof;
            if (displacement <= _symbol.PipSize) return false;
            double entry = e.Signal.Direction == TradeDirection.Buy
                ? proof - .618 * displacement
                : proof + .618 * displacement;
            double originalStop = e.Signal.StructuralInvalidation;
            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            double reactionStop = e.Signal.Direction == TradeDirection.Buy ? extreme - buffer : extreme + buffer;
            double stop = e.Signal.Direction == TradeDirection.Buy
                ? Math.Max(originalStop, reactionStop)
                : Math.Min(originalStop, reactionStop);
            if (!GeometryValid(e.Signal.Direction, entry, stop,
                e.Signal.Direction == TradeDirection.Buy ? entry + Math.Abs(entry-stop) : entry - Math.Abs(entry-stop)))
                return false;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;

            e.VirtualEntryAnchor = entry;
            e.VirtualStructuralStop = stop;
            e.VirtualRiskDistance = risk;
            e.VirtualProofExpiryUtc = MinDate(e.ExpiryUtc, V72NextM15Boundary(utc));
            if (e.VirtualProofExpiryUtc <= utc.AddSeconds(1)) return false;
            e.AwaitingVirtualProofFill = true;
            e.VirtualProofActive = false;
            e.TrendProofConfirmed = false;
            e.CapitalReady = false;
            e.CapitalDirection = e.Signal.Direction;
            e.CapitalLane = "TREND_VIRTUAL_PROOF";
            e.ConfirmationScore = confirmationScore;
            e.State = V71ExpansionState.PROOF_WAIT;
            Print("[V72-TREND-PROOF-WAIT] cid={0} family={1} entry={2:F5} stop={3:F5} proofR=0.500 expiry={4:o}",
                e.CandidateId, V71FamilyKey(e.Signal.PatternName), entry, stop, e.VirtualProofExpiryUtc);
            return true;
        }

        private bool V72PrepareTrendReload(DateTime utc, V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || !e.TrendProofConfirmed || e.VirtualRiskDistance <= 0) return false;
            double start = e.VirtualEntryAnchor;
            double proof = e.VirtualProofPrice;
            double displacement = Math.Abs(proof - start);
            if (displacement <= _symbol.PipSize) return false;
            double entry = e.Signal.Direction == TradeDirection.Buy
                ? proof - .618 * displacement
                : proof + .618 * displacement;
            double stop = e.VirtualStructuralStop;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;
            double canonical, canonicalRr;
            if (!SelectCanonicalBasketTarget(e.Signal, entry, stop, out canonical, out canonicalRr))
                return false;
            double costPrice = PipsToPrice(ModeledCostPips());
            double target = e.Signal.Direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            bool canonicalCovers = e.Signal.Direction == TradeDirection.Buy ? canonical >= target : canonical <= target;
            if (!canonicalCovers) return false;
            return V72ArmCapitalPullback(utc, e, e.Signal.Direction, entry, stop, target,
                e.ConfirmationScore, "TREND_PROOF_RELOAD", true);
        }

        private bool V72FailureBreakConfirmed(int i, V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || i < 0 || i >= _m1Bars.Count) return false;
            double close = _m1Bars.ClosePrices[i];
            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            return e.Signal.Direction == TradeDirection.Buy
                ? close < e.Signal.StructuralInvalidation - buffer
                : close > e.Signal.StructuralInvalidation + buffer;
        }

        private bool V72PrepareFailureContinuation(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null || !e.PrzTouchUtc.HasValue || !V72FailureBreakConfirmed(i,e)) return false;
            TradeDirection direction = V72OppositeDirection(e.Signal.Direction);
            double boundary = e.Signal.StructuralInvalidation;
            double proof = _m1Bars.ClosePrices[i];
            double displacement = Math.Abs(proof - boundary);
            if (displacement <= _symbol.PipSize) return false;
            double entry = direction == TradeDirection.Buy
                ? proof - .618 * displacement
                : proof + .618 * displacement;
            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
            double stop = direction == TradeDirection.Buy ? boundary - buffer : boundary + buffer;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;
            double costPrice = PipsToPrice(ModeledCostPips());
            double target = direction == TradeDirection.Buy
                ? entry + 2.0 * risk + costPrice
                : entry - 2.0 * risk - costPrice;
            e.FailureContinuation = true;
            e.Route = HarmonicRoute.FAILURE_CONTINUATION;
            e.ReactionProved = false;
            bool ok = V72ArmCapitalPullback(utc, e, direction, entry, stop, target,
                1.0, "FAILURE_CONTINUATION", true);
            if (ok)
                Print("[V72-FAILURE-PROVED] cid={0} family={1} originalDir={2} continuationDir={3} boundary={4:F5} proof={5:F5}",
                    e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Signal.Direction, direction, boundary, proof);
            return ok;
        }

        private void V71ProcessExpansionM1(int i, DateTime utc)
        {
            foreach (var e in _v71Expansion.Values.Where(x => x.IsActive).ToList())
            {
                bool overlapNow = _executedSetupKeys.Contains(e.SetupKey) || _activeSetupOwners.ContainsKey(e.SetupKey);
                if (overlapNow && !e.CoreOverlapObserved)
                {
                    e.CoreOverlapObserved = true;
                    e.CapitalEligible = false;
                    IncrementCounter(_v71FamilyCoreOverlap, V71FamilyKey(e.Signal.PatternName));
                }

                if (utc >= e.ExpiryUtc)
                {
                    if (e.ShadowStarted && !e.ShadowFinished) V71FinalizeExpansionShadow(e, i, "TTL");
                    e.IsActive = false;
                    e.State = V71ExpansionState.EXPIRED;
                    continue;
                }

                if (!e.ShadowStarted && !e.FailureContinuation && PatternInvalidatedBeforeEntry(e.Signal))
                {
                    if (EnableV72FailureAuctionCausalAlpha && e.PrzTouchUtc.HasValue &&
                        V72StartFailureAuction(i, utc, e))
                        continue;
                    if (EnableV72FamilyNativeCausalAlpha && e.PrzTouchUtc.HasValue &&
                        V72StartFamilyNativeFailureRetest(i, utc, e))
                        continue;
                    if (EnableV72BifurcationAlpha && e.PrzTouchUtc.HasValue &&
                        e.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL &&
                        V72PrepareFailureContinuation(i, utc, e))
                        continue;
                    e.IsActive = false;
                    e.State = V71ExpansionState.INVALIDATED;
                    continue;
                }

                if (e.State == V71ExpansionState.WAIT_PRZ)
                {
                    if (BarTouchesPrz(i, e.Signal))
                    {
                        e.PrzTouchUtc = utc;
                        e.State = V71ExpansionState.CONFIRMING;
                    }
                    continue;
                }

                if (e.State == V71ExpansionState.CONFIRMING)
                {
                    if (!e.PrzTouchUtc.HasValue || utc <= e.PrzTouchUtc.Value) continue;
                    if (EnableV72BifurcationAlpha)
                    {
                        double lo = _m1Bars.LowPrices[i], hi = _m1Bars.HighPrices[i];
                        if (!e.ReactionExtremeInitialized)
                        {
                            e.ReactionExtremePrice = e.Signal.Direction == TradeDirection.Buy ? lo : hi;
                            e.ReactionExtremeInitialized = true;
                        }
                        else if (e.Signal.Direction == TradeDirection.Buy)
                            e.ReactionExtremePrice = Math.Min(e.ReactionExtremePrice, lo);
                        else
                            e.ReactionExtremePrice = Math.Max(e.ReactionExtremePrice, hi);
                    }

                    V71RefreshExpansionDecisionContext(e);
                    double score;
                    if (V71ExpansionM1Confirmation(i, e, out score))
                    {
                        if (!EnableV72BifurcationAlpha && !EnableV72FamilyNativeCausalAlpha && !EnableV72FailureAuctionCausalAlpha)
                        {
                            e.IsActive = false;
                            e.State = V71ExpansionState.REJECTED;
                            continue;
                        }
                        e.ReactionProved = true;
                        e.ReactionProofUtc = utc;
                        e.ReactionProofPrice = _m1Bars.ClosePrices[i];
                        e.ReactionScore = score;
                        Print("[V72-REACTION-PROVED] cid={0} family={1} route={2} score={3:F3} proof={4:F5} extreme={5:F5}",
                            e.CandidateId, V71FamilyKey(e.Signal.PatternName), e.Route, score,
                            e.ReactionProofPrice, e.ReactionExtremePrice);

                        if (EnableV72FailureAuctionCausalAlpha)
                        {
                            e.State = V71ExpansionState.FAILURE_WAIT;
                            e.CapitalReady = false;
                            e.CapitalLane = "FAILURE_AUCTION_WAIT_FAILURE";
                            Print("[V72-FAILURE-AUCTION-WAIT] cid={0} family={1} proofUtc={2:o} structuralInvalidation={3:F5}",
                                e.CandidateId, V71FamilyKey(e.Signal.PatternName), utc, e.Signal.StructuralInvalidation);
                            continue;
                        }

                        bool prepared = false;
                        if (EnableV72FamilyNativeCausalAlpha)
                            prepared = V72PrepareFamilyNativeReversalShadow(i, utc, e, score);
                        else if (e.Route == HarmonicRoute.EXHAUSTION_REVERSAL)
                            prepared = V72PreparePullbackEntry(utc, e, score);
                        else if (e.Route == HarmonicRoute.TREND_ALIGNED_REVERSAL)
                            prepared = V72PrepareTrendVirtualProof(utc, e, score);
                        else if (e.Route == HarmonicRoute.TRANSITION_REVERSAL)
                        {
                            e.CapitalEligible = false;
                            prepared = V72PreparePullbackEntry(utc, e, score);
                        }
                        if (!prepared)
                        {
                            e.IsActive = false;
                            e.State = V71ExpansionState.REJECTED;
                            Print("[V72-RESOLUTION-REJECT] cid={0} familyNative={1} reason=NO_LEGAL_POST_REACTION_PATH",
                                e.CandidateId, EnableV72FamilyNativeCausalAlpha);
                        }
                    }
                    continue;
                }

                if (e.State == V71ExpansionState.FAILURE_WAIT)
                    continue;

                if (e.State == V71ExpansionState.PROOF_WAIT)
                {
                    if (EnableV72FailureAuctionCausalAlpha && e.FailureContinuation && e.FailureBreakObserved)
                    {
                        V72ProcessFailureAuction(i, utc, e);
                        continue;
                    }

                    if (EnableV72FamilyNativeCausalAlpha && e.FailureContinuation && e.FailureBreakObserved)
                    {
                        V72ProcessFamilyNativeFailureRetest(i, utc, e);
                        continue;
                    }

                    if (utc >= e.VirtualProofExpiryUtc)
                    {
                        e.IsActive = false; e.State = V71ExpansionState.EXPIRED;
                        Print("[V72-TREND-PROOF-EXPIRE] cid={0} stage=WAIT_FILL", e.CandidateId);
                        continue;
                    }
                    TradeDirection dir = e.Signal.Direction;
                    bool touched = dir == TradeDirection.Buy
                        ? _m1Bars.LowPrices[i] <= e.VirtualEntryAnchor
                        : _m1Bars.HighPrices[i] >= e.VirtualEntryAnchor;
                    if (!touched) continue;
                    double proofLevel = dir == TradeDirection.Buy
                        ? e.VirtualEntryAnchor + .50 * e.VirtualRiskDistance
                        : e.VirtualEntryAnchor - .50 * e.VirtualRiskDistance;
                    bool hitStop = dir == TradeDirection.Buy
                        ? _m1Bars.LowPrices[i] <= e.VirtualStructuralStop
                        : _m1Bars.HighPrices[i] >= e.VirtualStructuralStop;
                    bool hitProof = dir == TradeDirection.Buy
                        ? _m1Bars.HighPrices[i] >= proofLevel
                        : _m1Bars.LowPrices[i] <= proofLevel;
                    if (hitProof)
                    {
                        e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                        Print("[V72-TREND-PROOF-REJECT] cid={0} reason=FILL_PROOF_SAME_BAR_AMBIGUOUS", e.CandidateId);
                        continue;
                    }
                    if (hitStop)
                    {
                        if (V72PrepareFailureContinuation(i, utc, e)) continue;
                        e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                        Print("[V72-TREND-PROOF-REJECT] cid={0} reason=VIRTUAL_STOP_ON_FILL", e.CandidateId);
                        continue;
                    }
                    e.AwaitingVirtualProofFill = false;
                    e.VirtualProofActive = true;
                    e.VirtualProofStartUtc = utc;
                    e.VirtualProofExpiryUtc = MinDate(e.ExpiryUtc, V72NextM15Boundary(utc));
                    e.State = V71ExpansionState.PROOF_ACTIVE;
                    Print("[V72-TREND-PROOF-FILL] cid={0} entry={1:F5} expiry={2:o}",
                        e.CandidateId, e.VirtualEntryAnchor, e.VirtualProofExpiryUtc);
                    continue;
                }

                if (e.State == V71ExpansionState.PROOF_ACTIVE)
                {
                    if (!e.VirtualProofStartUtc.HasValue || utc <= e.VirtualProofStartUtc.Value) continue;
                    if (utc >= e.VirtualProofExpiryUtc)
                    {
                        e.IsActive = false; e.State = V71ExpansionState.EXPIRED;
                        Print("[V72-TREND-PROOF-EXPIRE] cid={0} stage=ACTIVE", e.CandidateId);
                        continue;
                    }
                    TradeDirection dir = e.Signal.Direction;
                    double proofLevel = dir == TradeDirection.Buy
                        ? e.VirtualEntryAnchor + .50 * e.VirtualRiskDistance
                        : e.VirtualEntryAnchor - .50 * e.VirtualRiskDistance;
                    bool hitStop = dir == TradeDirection.Buy
                        ? _m1Bars.LowPrices[i] <= e.VirtualStructuralStop
                        : _m1Bars.HighPrices[i] >= e.VirtualStructuralStop;
                    bool hitProof = dir == TradeDirection.Buy
                        ? _m1Bars.HighPrices[i] >= proofLevel
                        : _m1Bars.LowPrices[i] <= proofLevel;
                    if (hitStop && hitProof)
                    {
                        e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                        Print("[V72-TREND-PROOF-REJECT] cid={0} reason=PROOF_STOP_SAME_BAR_AMBIGUOUS", e.CandidateId);
                        continue;
                    }
                    if (hitStop)
                    {
                        if (V72PrepareFailureContinuation(i, utc, e)) continue;
                        e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                        Print("[V72-TREND-PROOF-REJECT] cid={0} reason=VIRTUAL_STOP_FIRST", e.CandidateId);
                        continue;
                    }
                    if (hitProof)
                    {
                        e.TrendProofConfirmed = true;
                        e.VirtualProofPrice = proofLevel;
                        Print("[V72-TREND-PROOF-CONFIRMED] cid={0} family={1} proof={2:F5}",
                            e.CandidateId, V71FamilyKey(e.Signal.PatternName), proofLevel);
                        if (!V72PrepareTrendReload(utc, e))
                        {
                            e.IsActive = false; e.State = V71ExpansionState.REJECTED;
                            Print("[V72-TREND-PROOF-REJECT] cid={0} reason=NO_LEGAL_RELOAD", e.CandidateId);
                        }
                    }
                    continue;
                }

                if (e.State == V71ExpansionState.ARMED && !e.ShadowFinished)
                {
                    if (e.AwaitingPullbackFill)
                    {
                        if (utc >= e.PullbackExpiryUtc)
                        {
                            e.IsActive = false;
                            e.State = V71ExpansionState.EXPIRED;
                            Print("[V72-BIFURCATION-EXPIRE] cid={0} lane={1}", e.CandidateId, e.CapitalLane);
                            continue;
                        }
                        TradeDirection fillDir = V72CapitalDirection(e);
                        bool touched = fillDir == TradeDirection.Buy
                            ? _m1Bars.LowPrices[i] <= e.EntryAnchor
                            : _m1Bars.HighPrices[i] >= e.EntryAnchor;
                        if (!touched) continue;

                        e.AwaitingPullbackFill = false;
                        e.PullbackFilled = true;
                        e.ShadowStarted = true;
                        e.ArmedUtc = utc;
                        e.ShadowPeakR = 0;
                        e.ShadowProtectionR = -1.0;
                        Print("[V72-BIFURCATION-FILL-SHADOW] cid={0} lane={1} dir={2} entry={3:F5} utc={4:o}",
                            e.CandidateId, e.CapitalLane, fillDir, e.EntryAnchor, utc);

                        bool sameBarStop = fillDir == TradeDirection.Buy
                            ? _m1Bars.LowPrices[i] <= e.StructuralStop
                            : _m1Bars.HighPrices[i] >= e.StructuralStop;
                        bool sameBarTarget = fillDir == TradeDirection.Buy
                            ? _m1Bars.HighPrices[i] >= e.CanonicalTarget
                            : _m1Bars.LowPrices[i] <= e.CanonicalTarget;
                        if (sameBarStop || sameBarTarget)
                        {
                            e.PathState = -2;
                            e.PathUsable = false;
                            V71FinalizeExpansionShadow(e, i, "PULLBACK_FILL_SAME_BAR_AMBIGUOUS");
                        }
                        continue;
                    }

                    if (!e.ShadowStarted || !e.ArmedUtc.HasValue || utc <= e.ArmedUtc.Value) continue;
                    TradeDirection dir = V72CapitalDirection(e);
                    e.ShadowBars++;
                    double high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i], close = _m1Bars.ClosePrices[i];
                    double risk = Math.Max(e.RiskDistance, _symbol.PipSize);
                    double favR = dir == TradeDirection.Buy
                        ? (high - e.EntryAnchor) / risk
                        : (e.EntryAnchor - low) / risk;
                    double adverseR = dir == TradeDirection.Buy
                        ? (e.EntryAnchor - low) / risk
                        : (high - e.EntryAnchor) / risk;
                    double closeR = dir == TradeDirection.Buy
                        ? (close - e.EntryAnchor) / risk
                        : (e.EntryAnchor - close) / risk;

                    if (favR > e.ShadowPeakR)
                    {
                        e.ShadowPeakR = favR;
                        e.TimeToMfeBars = e.ShadowBars;
                    }
                    e.ShadowMfeR = Math.Max(e.ShadowMfeR, favR);
                    e.ShadowMaeR = Math.Max(e.ShadowMaeR, adverseR);
                    e.ShadowMaxGivebackR = Math.Max(e.ShadowMaxGivebackR, Math.Max(0, e.ShadowPeakR - closeR));
                    if (e.TimeTo05R < 0 && favR >= .50) e.TimeTo05R = e.ShadowBars;
                    if (e.TimeTo1R < 0 && favR >= 1.00) e.TimeTo1R = e.ShadowBars;
                    if (e.TimeTo2R < 0 && favR >= e.TargetR) e.TimeTo2R = e.ShadowBars;
                    if (e.TimeToStopR < 0 && adverseR >= 1.00) e.TimeToStopR = e.ShadowBars;

                    if (e.PathState == 0)
                    {
                        bool hitTarget = favR >= Math.Max(2.0, e.TargetR);
                        bool hitStop = adverseR >= 1.00;
                        if (hitTarget && hitStop)
                        {
                            e.PathState = -2; e.PathUsable = false;
                            V71FinalizeExpansionShadow(e, i, "PATH_AMBIGUOUS_SAME_BAR");
                            continue;
                        }
                        if (hitStop)
                        {
                            e.PathState = -1; e.PathUsable = true;
                            V71FinalizeExpansionShadow(e, i, "STRUCTURAL_STOP_FIRST");
                            continue;
                        }
                        if (hitTarget)
                        {
                            e.PathState = 1; e.PathUsable = true;
                            if (EnableV72FailureAuctionCausalAlpha)
                                V71FinalizeExpansionShadow(e, i, "FAILURE_AUCTION_TARGET", e.NetRR);
                            else if (EnableV72FamilyNativeCausalAlpha)
                                V71FinalizeExpansionShadow(e, i, "FAMILY_NATIVE_TARGET", e.NetRR);
                            else
                                V71FinalizeExpansionShadow(e, i, "V72_FIXED_2R_TARGET", 2.0);
                            continue;
                        }
                    }

                    if (e.ShadowBars >= Math.Max(30, V71ExpansionShadowHorizonM1Bars))
                    {
                        if (EnableV72FamilyNativeCausalAlpha || EnableV72FailureAuctionCausalAlpha) e.PathUsable = true;
                        V71FinalizeExpansionShadow(e, i,
                            EnableV72FailureAuctionCausalAlpha ? "FAILURE_AUCTION_HORIZON" :
                            (EnableV72FamilyNativeCausalAlpha ? "FAMILY_NATIVE_HORIZON" : "STRUCTURAL_HORIZON"));
                    }
                }
            }

            if (_v71Expansion.Count > 16000)
            {
                foreach (var k in _v71Expansion.Where(kv => !kv.Value.IsActive && kv.Value.ShadowFinished)
                    .OrderBy(kv => kv.Value.DetectedUtc).Take(_v71Expansion.Count - 12000).Select(kv => kv.Key).ToList())
                    _v71Expansion.Remove(k);
            }
        }

        private void V72RecordPayoffCensus(V71ExpansionCandidate e, double structuralR)
        {
            if (e == null || e.Signal == null) return;
            if (!e.CapitalEligible || e.CoreOverlapObserved || e.PathState == -2) return;
            string lane = string.IsNullOrWhiteSpace(e.CapitalLane) ? e.Route.ToString() : e.CapitalLane;
            if (string.Equals(lane, "TRANSITION_SHADOW", StringComparison.Ordinal)) return;
            string family = V71FamilyKey(e.Signal.PatternName);
            string dedupe = (e.SetupKey ?? "") + "|" + family + "|" + lane;
            if (!_v72PayoffSeen.Add(dedupe)) return;
            string key = lane + "|" + family;
            V72PayoffAccumulator z;
            if (!_v72PayoffCensus.TryGetValue(key, out z))
            {
                z = new V72PayoffAccumulator();
                _v72PayoffCensus[key] = z;
            }
            z.N++;
            z.SumR += structuralR;
            z.SumSqR += structuralR * structuralR;
            if (structuralR > 0)
            {
                z.GrossProfitR += structuralR;
                z.Wins++;
            }
            else if (structuralR < 0)
                z.GrossLossR += -structuralR;
        }

        private void V71FinalizeExpansionShadow(V71ExpansionCandidate e, int i, string result, double? forcedR = null)
        {
            if (e == null || e.ShadowFinished || !e.ShadowStarted || e.RiskDistance <= 0) return;
            TradeDirection dir = V72CapitalDirection(e);
            double close = i >= 0 && i < _m1Bars.Count ? _m1Bars.ClosePrices[i] :
                           (dir == TradeDirection.Buy ? _symbol.Bid : _symbol.Ask);
            double closeR = (dir == TradeDirection.Buy ? close - e.EntryAnchor : e.EntryAnchor - close) / e.RiskDistance;

            double structuralR;
            if (forcedR.HasValue) structuralR = forcedR.Value;
            else if (e.PathState == 1) structuralR = 2.0;
            else if (e.PathState == -1) structuralR = -1.0;
            else structuralR = Math.Max(-1.0, Math.Min(2.0, closeR));

            if (!e.NativeExitCaptured)
            {
                e.NativeExitCaptured = true;
                e.NativeExitR = Math.Max(-1.0, Math.Min(Math.Max(0, e.TargetR), closeR));
                e.NativeExitResult = "V51_NATIVE_PROXY_" + result;
            }

            e.ShadowOutcomeR = structuralR;
            V72RecordPayoffCensus(e, structuralR);
            e.ShadowFinished = true;
            e.IsActive = false;
            _v71ExpansionShadowClosed++;
            IncrementCounter(_v71FamilyShadowClosed, V71FamilyKey(e.Signal.PatternName));
            Print("[V71-EXP-SHADOW] cid={0} setup={1} family={2} role={3} route={4} coreOverlap={5} capitalEligible={6} g={7:F6} prz={8:F6} conf={9:F6} ts={10:F6} pv={11:F6} m1={12:F6} rr={13:F6} reg={14:F6} eff={15:F6} atr={16:F6} ext={17:F6} mtf={18:F6} atp={19:F6} adx1={20:F6} adx4={21:F6} adxs={22:F6} trend={23:F6} spr={24:F6} ses={25:F6} przc={26:F6} trans={27:F6} survival={28:F6} structuralR={29:F6} nativeR={30:F6} nativeResult={31} pathState={32} pathUsable={33} mfeR={34:F6} maeR={35:F6} t05={36} t1={37} t2={38} tstop={39} tmfe={40} givebackR={41:F6} result={42} bars={43} costR={44:F6} lane={45} label=STRUCTURAL_PATH_PLUS_NATIVE_EXIT_COMPLETED_M1",
                e.CandidateId, e.SetupKey, V71FamilyKey(e.Signal.PatternName), e.AbcdRole, e.Route,
                e.CoreOverlapObserved, e.CapitalEligible,
                VClamp(e.Signal.GeometryQuality), VClamp(e.Signal.PrzConfluence), VClamp(e.Signal.Confidence),
                VClamp(e.Signal.TimeSymmetry), VClamp(e.Signal.PivotQuality), VClamp(e.ConfirmationScore),
                VClamp(e.NetRR / 4.0), VClamp(e.RegimeScore),
                e.Regime == null ? 0 : VClamp(e.Regime.Efficiency), V71AtrFit(e.Regime),
                e.Regime == null ? 0 : VClamp(e.Regime.ExtensionAtr / 2.0), V71MtfScore(e.Conflict),
                e.AtrPercentile, e.AdxH1Norm, e.AdxH4Norm, e.AdxSlopeNorm, e.TrendStrength,
                e.SpreadAtr, e.SessionPhase, e.PrzCompression, e.TransitionState, e.SurvivalProbability,
                structuralR, e.NativeExitR, e.NativeExitResult ?? "NONE", e.PathState, e.PathUsable,
                e.ShadowMfeR, e.ShadowMaeR, e.TimeTo05R, e.TimeTo1R, e.TimeTo2R, e.TimeToStopR,
                e.TimeToMfeBars, e.ShadowMaxGivebackR, result, e.ShadowBars, e.ModeledCostR, e.CapitalLane ?? "NONE");
        }

        private void V71FinalizeExpansionShadows()
        {
            int i = LastClosedIndex(_m1Bars);
            foreach (var e in _v71Expansion.Values.Where(x => x.ShadowStarted && !x.ShadowFinished).ToList())
                V71FinalizeExpansionShadow(e, i, "BACKTEST_END");
        }

        private bool V71CoreHasActiveThesis()
        {
            return _candidates.Values.Any(x => x.IsActive);
        }

        private void V71PreemptExpansionForCore(DateTime now)
        {
            if (!EnableV71ExpansionExecution || !V71CoreHasActiveThesis()) return;
            foreach (var basket in _baskets.Values
                .Where(b => b.IsActive && !string.IsNullOrWhiteSpace(b.CandidateId) &&
                            b.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                .ToList())
            {
                CancelBasketPending(basket, "V51_CORE_PREEMPT");
                CloseBasketPositions(basket, "V51_CORE_PREEMPT");
                bool hasPosition = OwnPositions().Any(p => LabelBasketId(p.Label) == basket.BasketId);
                bool hasPending = OwnPendingOrders().Any(o => LabelBasketId(o.Label) == basket.BasketId);
                if (!hasPosition && !hasPending)
                {
                    basket.State = FibonacciBasketState.CANCELLED;
                    basket.IsActive = false;
                }
                Print("[V71-EXP-PREEMPT] basket={0} candidate={1} coreActive={2} utc={3:o}",
                    basket.BasketId, basket.CandidateId, V71CoreHasActiveThesis(), now);
            }
        }

        private void V71RecordCoreExecution(CandidateRecord c)
        {
            if (c == null || c.V71Expansion || c.Signal == null) return;
            string token = (c.SetupKey ?? "") + "|" + c.Signal.PatternName + "|" + c.Route + "|" + c.Signal.Direction + ";";
            unchecked
            {
                foreach (char ch in token)
                {
                    _v71CoreExecutionFnv ^= (byte)(ch & 0xFF);
                    _v71CoreExecutionFnv *= 1099511628211UL;
                    if (ch > 0xFF)
                    {
                        _v71CoreExecutionFnv ^= (byte)((ch >> 8) & 0xFF);
                        _v71CoreExecutionFnv *= 1099511628211UL;
                    }
                }
            }
            _v71CoreExecutionCount++;
        }

        private double V71ExpansionContributionNet()
        {
            double open = 0;
            foreach (var p in OwnPositions())
            {
                PositionLedger ledger;
                FibonacciBasket basket;
                if (!_positions.TryGetValue(p.Id, out ledger) || string.IsNullOrWhiteSpace(ledger.BasketId) ||
                    !_baskets.TryGetValue(ledger.BasketId, out basket) || string.IsNullOrWhiteSpace(basket.CandidateId) ||
                    !basket.CandidateId.StartsWith("V71EXP-", StringComparison.Ordinal))
                    continue;
                open += p.NetProfit;
            }
            return _v71ExpansionRealizedNet + open;
        }

        private bool V71ExpansionRiskReserveAllows(double riskPct)
        {
            double pct = Math.Min(5.0, Math.Max(.10, riskPct));
            double corePct = Math.Min(5.0, Math.Max(.10, BasketRiskPercent));
            double plannedRisk = Math.Max(0, Account.Equity) * pct / 100.0;
            double coreReserve = Math.Max(0, Account.Equity) * corePct / 100.0;
            double sleeveBudget = Math.Max(0, _initialEquity) * corePct / 100.0;
            double contribution = V71ExpansionContributionNet();

            // Expansion may spend its own accumulated profit, but it may not create a
            // cumulative loss larger than one frozen V51 core basket risk unit.
            if (contribution - plannedRisk < -sleeveBudget - 1e-8)
            {
                _v71ExpansionRiskReserveBlocked++;
                return false;
            }

            double peakBudget = Math.Max(0, _equityPeak) * Math.Max(0, MaxDrawdownPercent) / 100.0;
            double peakUsed = Math.Max(0, _equityPeak - Account.Equity);
            double peakHeadroom = Math.Max(0, peakBudget - peakUsed);
            double dayBudget = Math.Max(0, _dayStartEquity) * Math.Max(0, DailyLossLimitPercent) / 100.0;
            double dayUsed = Math.Max(0, _dayStartEquity - Account.Equity);
            double dayHeadroom = Math.Max(0, dayBudget - dayUsed);

            // Preserve enough causal headroom for the next legal V51 core basket.
            if (plannedRisk + coreReserve > peakHeadroom + 1e-8 ||
                plannedRisk + coreReserve > dayHeadroom + 1e-8)
            {
                _v71ExpansionRiskReserveBlocked++;
                return false;
            }
            return true;
        }

        private double V71ExpansionRiskFor(V71ExpansionCandidate e)
        {
            double cap = Math.Min(5.0, Math.Max(.10, V71ExpansionRiskPercent));
            double requested = 1.0;
            if (EnableV71ExpansionAdaptiveRisk)
            {
                if (e != null && e.EdgeLcb >= .15) requested = 2.0;
                if (e != null && e.EdgeLcb >= .30) requested = 3.0;
                if (e != null && e.EdgeLcb >= .50) requested = 5.0;
            }
            requested = Math.Min(cap, requested);

            // Protected-Core invariant: expansion capacity research cannot consume more
            // per basket than the frozen core risk unit before Alpha is qualified.
            double protectedCap = Math.Min(cap, Math.Min(5.0, Math.Max(.10, BasketRiskPercent)));
            double r = Math.Min(requested, protectedCap);
            if (requested > r + 1e-9) _v71ExpansionRiskCapped++;
            if (r > 1.000001) _v71ExpansionRiskScaled++;
            return r;
        }

        private double V71CandidateRiskPercent(CandidateRecord c)
        {
            if (c != null && c.V71Expansion)
                return Math.Min(5.0, Math.Max(.10, c.V71RiskPercent));
            return Math.Min(5.0, Math.Max(.10, BasketRiskPercent));
        }

        private bool V71BuildExpansionSingleLeg(CandidateRecord c)
        {
            if (c == null || c.Signal == null || c.Signal.Profile == null) return false;
            double anchor = c.Signal.Direction == TradeDirection.Buy ? _symbol.Ask : _symbol.Bid;
            double stop = c.Signal.StructuralInvalidation;
            double distance = Math.Abs(anchor - stop);
            if (PriceToPips(distance) < MinStopLossPips) return false;

            double target, netRr;
            if (!SelectCanonicalBasketTarget(c.Signal, anchor, stop, out target, out netRr) || netRr < MinimumNetRR)
                return false;

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = c.Signal.Direction,
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = distance,
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = MinDate(c.ExpiryUtc, Server.Time.ToUniversalTime().AddMinutes(Math.Max(15, c.Signal.Profile.PendingTtlMinutes))),
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold,
                CanonicalTarget = target,
                ExpectedNetRR = netRr,
                ExpectedWeightedEntry = anchor,
                VirtualWeightedEntry = anchor
            };
            if (plan.BasketRiskAmount <= 0) return false;

            double slPips = PriceToPips(distance);
            double minRisk = _symbol.VolumeInUnitsMin * _symbol.PipValue * (slPips + ModeledCostPips());
            plan.Legs.Add(new FibonacciGridLeg
            {
                Index = 0, Fraction = 0, PlannedPrice = anchor, RiskWeight = 1.0,
                RiskBudget = plan.BasketRiskAmount, MinBrokerRisk = minRisk,
                Volume = 0, PlannedRisk = 0, ModeledCost = 0, Physical = false,
                State = GridLegState.VIRTUAL_ONLY
            });
            plan.LogicalLegCount = 1;
            if (!ConfigureCapitalExecution(plan)) return false;
            if (plan.Legs.Count == 0 || !plan.Legs[0].Physical || plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) return false;

            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = netRr;
            return true;
        }

        private bool V72BuildPullbackSingleLeg(CandidateRecord c, V71ExpansionCandidate e)
        {
            if (c == null || e == null || c.Signal == null || !e.AwaitingPullbackFill) return false;
            double anchor = e.EntryAnchor;
            double stop = e.StructuralStop;
            double target = e.CanonicalTarget;
            double distance = Math.Abs(anchor - stop);
            if (PriceToPips(distance) < MinStopLossPips || e.NetRR < MinimumNetRR) return false;

            var plan = new FibonacciGridPlan
            {
                CandidateId = c.CandidateId,
                Pattern = c.Signal.PatternName,
                Direction = V72CapitalDirection(e),
                Route = c.Route,
                EntryAnchor = anchor,
                StructuralStop = stop,
                GridDistance = distance,
                BasketRiskAmount = Account.Equity * V71CandidateRiskPercent(c) / 100.0,
                CreatedUtc = Server.Time.ToUniversalTime(),
                ExpirationUtc = e.PullbackExpiryUtc,
                MicroCapitalMode = AdaptiveCapitalMode && Account.Equity <= MicroCapitalThreshold,
                CanonicalTarget = target,
                ExpectedNetRR = e.NetRR,
                ExpectedWeightedEntry = anchor,
                VirtualWeightedEntry = anchor
            };
            if (plan.BasketRiskAmount <= 0 || plan.ExpirationUtc <= Server.Time.ToUniversalTime().AddSeconds(1)) return false;
            double slPips = PriceToPips(distance);
            double minRisk = _symbol.VolumeInUnitsMin * _symbol.PipValue * (slPips + ModeledCostPips());
            plan.Legs.Add(new FibonacciGridLeg
            {
                Index = 0, Fraction = .618, PlannedPrice = anchor, RiskWeight = 1.0,
                RiskBudget = plan.BasketRiskAmount, MinBrokerRisk = minRisk,
                Volume = 0, PlannedRisk = 0, ModeledCost = 0, Physical = false,
                State = GridLegState.VIRTUAL_ONLY
            });
            plan.LogicalLegCount = 1;
            if (!ConfigureCapitalExecution(plan)) return false;
            if (plan.Legs.Count == 0 || !plan.Legs[0].Physical || plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) return false;
            c.GridPlan = plan;
            c.SelectedTarget = target;
            c.NetRR = e.NetRR;
            return true;
        }

        private bool V72SubmitPullbackSingleLeg(CandidateRecord c)
        {
            var plan = c == null ? null : c.GridPlan;
            if (plan == null || plan.Legs.Count != 1) return false;
            if (Account.FreeMargin < plan.BasketRiskAmount * MinFreeMarginRiskMultiple) return false;
            if (plan.WorstCaseRisk > plan.BasketRiskAmount + 1e-8) { _gridRiskViolations++; return false; }

            string basketId = NewBasketId();
            plan.BasketId = basketId;
            var basket = new FibonacciBasket
            {
                BasketId = basketId, CandidateId = c.CandidateId, Pattern = c.Signal.PatternName,
                Direction = plan.Direction, Route = c.Route, State = FibonacciBasketState.PLANNED,
                CreatedUtc = Server.Time.ToUniversalTime(), ExpirationUtc = plan.ExpirationUtc,
                EntryAnchor = plan.EntryAnchor, StructuralStop = plan.StructuralStop,
                CanonicalTarget = plan.CanonicalTarget, InitialBasketRisk = plan.BasketRiskAmount,
                PlannedWorstCaseRisk = plan.WorstCaseRisk, ProtectionFrontier = plan.StructuralStop,
                Plan = plan, Candidate = c, IsActive = true
            };
            _baskets[basketId] = basket;
            CountPipeline(c.Signal.PatternName).BasketPlanned++;
            BasketEvent(basket, "V72_PULLBACK_BASKET_PLANNED");

            var l0 = plan.Legs[0];
            if (!PlaceGridLimit(basket, l0))
            {
                basket.State = FibonacciBasketState.CANCELLED;
                basket.IsActive = false;
                return false;
            }
            basket.State = FibonacciBasketState.GRID_PENDING;
            Transition(c, CandidateState.EXECUTED, "V72_PULLBACK_LIMIT_SUBMITTED");
            if (!string.IsNullOrWhiteSpace(c.SetupKey)) _v71ExpansionExecutedSetupKeys.Add(c.SetupKey);
            BasketEvent(basket, "V72_PULLBACK_LIMIT_SUBMITTED");
            return true;
        }

        private void V71TryExecuteExpansion(DateTime now)
        {
            if (!EnableV71ExpansionExecution || (!EnableV72BifurcationAlpha && !EnableV72FamilyNativeCausalAlpha && !EnableV72HcogAlpha && !EnableV72HcapAlpha)) return;
            if (V71CoreHasActiveThesis()) { _v71ExpansionCoreBlocked++; return; }
            if (OwnPositions().Any() || OwnPendingOrders().Any() || _baskets.Values.Any(b => b.IsActive)) return;
            if (!IsInstitutionalSession(now) || !SpreadValid()) return;

            var eligible = _v71Expansion.Values
                .Where(e => e.IsActive && e.State == V71ExpansionState.ARMED && !e.Executed &&
                            e.CapitalEligible && !e.CoreOverlapObserved && e.CapitalReady &&
                            e.AwaitingPullbackFill && e.NetRR >= MinimumNetRR &&
                            !_executedSetupKeys.Contains(e.SetupKey) &&
                            !_v71ExpansionExecutedSetupKeys.Contains(e.SetupKey))
                .OrderByDescending(e => e.AsymmetryCompression)
                .ThenByDescending(e => e.NetRR)
                .ThenBy(e => e.ReactionProofUtc ?? e.DetectedUtc)
                .ToList();

            if (eligible.Count == 0)
            {
                if (_v71Expansion.Values.Any(e => e.IsActive && e.State == V71ExpansionState.ARMED &&
                    (!e.CapitalEligible || e.CoreOverlapObserved || !e.CapitalReady ||
                     !e.AwaitingPullbackFill || e.NetRR < MinimumNetRR)))
                    _v71ExpansionEligibilityRejected++;
                return;
            }

            var e = eligible[0];
            double riskPct = V71ExpansionRiskFor(e);
            if (!V71ExpansionRiskReserveAllows(riskPct)) return;
            var candidate = new CandidateRecord
            {
                CandidateId = e.CandidateId,
                SetupKey = e.SetupKey,
                Signal = e.Signal,
                State = CandidateState.EXECUTABLE,
                IsActive = true,
                DetectedUtc = e.DetectedUtc,
                ExpiryUtc = e.ExpiryUtc,
                PrzTouchUtc = e.PrzTouchUtc,
                Conflict = e.Conflict,
                Route = e.Route,
                Regime = e.Regime,
                ConfirmationScore = e.ConfirmationScore,
                NetRR = e.NetRR,
                SelectedTarget = e.CanonicalTarget,
                V71Expansion = true,
                V72BifurcationAlpha = EnableV72BifurcationAlpha,
                V72FamilyNativeCausalAlpha = EnableV72FamilyNativeCausalAlpha,
                V71RiskPercent = riskPct
            };

            if (!V72BuildPullbackSingleLeg(candidate, e) || candidate.GridPlan == null || candidate.NetRR < MinimumNetRR)
                return;

            Print("[V72-ALPHA-EXECUTE] architecture={0} cid={1} setup={2} family={3} lane={4} route={5} dir={6} rr={7:F3} asym={8:F3} riskPct={9:F2}",
                EnableV72HcapAlpha ? "HARMONIC_COUNTERFACTUAL_ACTION_POLICY" : (EnableV72HcogAlpha ? "HARMONIC_CAUSAL_OPPORTUNITY_GRAPH" : (EnableV72FamilyNativeCausalAlpha ? "FAMILY_NATIVE_CAUSAL" : "LEGACY_BIFURCATION")),
                e.CandidateId, e.SetupKey, V71FamilyKey(e.Signal.PatternName), e.CapitalLane, e.Route,
                V72CapitalDirection(e), e.NetRR, e.AsymmetryCompression, riskPct);

            if (V72SubmitPullbackSingleLeg(candidate))
            {
                e.Executed = true;
                e.IsActive = false;
                e.State = V71ExpansionState.EXECUTED;
                _v71ExpansionExecuted++;
            }
        }

    }
}
