using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    // V72 candidate: Regime-Conditioned Causal Resolution Engine (CRAE).
    // Research truth remains counterfactual and independent of V51 slot ownership.
    // Regime arbitration is deterministic from contemporaneous H4/H1/M15 observables;
    // there is no year classifier, PnL-trained selector, Validation/Fresh access, Grid Alpha, or risk upsizing.
    public partial class HarmonyBotV71
    {
        [Parameter("Enable V72 CRAE Alpha", DefaultValue = false)]
        public bool EnableV72CraeAlpha { get; set; }

        private enum V72CraeState
        {
            WAIT_PRZ, WAIT_LIQUIDITY, WAIT_RECLAIM, WAIT_BOS, WAIT_RETEST,
            FAILURE_WAIT_RETEST, ACTIVE, CLOSED, EXPIRED
        }

        private sealed class V72CraeOpportunity
        {
            public string Id, SetupKey, Family, Hypotheses, Lane, Mode, Result;
            public PatternSignal Signal;
            public MtfConflict Conflict;
            public RegimeSnapshot Regime;
            public V72CraeState State;
            public bool Active = true, HasAbcdConfluence, StandaloneAbcd, CapitalSemantic, CoreOverlapAtEntry, CapitalQueued;
            public DateTime DetectedUtc, OverallExpiryUtc, ProofExpiryUtc, LastStageUtc, EntryUtc, FailureBreakUtc;
            public DateTime? PrzTouchUtc, ProofUtc;
            public TradeDirection Direction;
            public double LiquidityExtreme, BosBoundary, FailureBoundary, Entry, Stop, Target, RiskDistance, NetRr, MfeR, MaeR;
            public int BarsActive;
        }

        private readonly Dictionary<string, V72CraeOpportunity> _v72Crae =
            new Dictionary<string, V72CraeOpportunity>(StringComparer.Ordinal);
        private readonly HashSet<string> _v72CraeSeen = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<string, V72PayoffAccumulator> _v72CraeCensus =
            new Dictionary<string, V72PayoffAccumulator>(StringComparer.Ordinal);
        private readonly HashSet<string> _v72CraePayoffSeen = new HashSet<string>(StringComparer.Ordinal);

        private int _v72CraeSeq, _v72CraeDetected, _v72CraePrzTouched, _v72CraeProofs, _v72CraeArmed, _v72CraeClosed;
        private int _v72CraeFailureArmed, _v72CraeCoreOverlapAtEntry, _v72CraeAbcdPrimitive, _v72CraeCapitalQueued, _v72CraeRegimeRejected;

        private double V72CraeRatioResidual(double value, double lo, double hi)
        {
            if (hi <= 0 || hi < lo) return 0;
            if (!double.IsFinite(value) || value <= 0) return 4.0;
            double mid = (lo + hi) * .5, half = Math.Max(.03, Math.Abs(hi - lo) * .5);
            return Math.Abs(value - mid) / half;
        }

        private double V72CraeGeometryLoss(PatternSignal s)
        {
            if (s == null || s.Profile == null) return 999;
            var p = s.Profile;
            double sum = 0;
            int n = 0;
            Action<double, double, double> add = (v, lo, hi) =>
            {
                if (hi <= 0 || hi < lo) return;
                sum += V72CraeRatioResidual(v, lo, hi);
                n++;
            };
            add(s.Xab, p.XabMin, p.XabMax);
            add(s.Abc, p.AbcMin, p.AbcMax);
            add(s.Bcd, p.BcdMin, p.BcdMax);
            add(s.Xad, p.XadMin, p.XadMax);
            add(s.AbCd, p.AbcDMin, p.AbcDMax);
            return (n > 0 ? sum / n : 0) - .25 * VClamp(s.GeometryQuality) - .25 * VClamp(s.PrzConfluence);
        }

        private PatternSignal V72CraeSelectPrimary(List<PatternSignal> xs)
        {
            var parent = xs.Where(x => !string.Equals(V71FamilyKey(x.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase))
                .OrderBy(V72CraeGeometryLoss)
                .ThenByDescending(x => x.PrzConfluence)
                .ThenByDescending(x => x.GeometryQuality)
                .FirstOrDefault();
            return parent ?? xs.OrderBy(V72CraeGeometryLoss)
                .ThenByDescending(x => x.PrzConfluence)
                .ThenByDescending(x => x.GeometryQuality)
                .FirstOrDefault();
        }

        private string V72CraeClassifyPrimary(PatternSignal s, MtfConflict conflict, RegimeSnapshot r)
        {
            if (s == null || r == null) return "NO_EDGE";
            if (r.Transition || conflict == MtfConflict.TRANSITION || conflict == MtfConflict.CONFLICT ||
                r.TrendDirection == TradeDirection.Neutral)
                return "TRANSITION_NO_TRADE";

            bool aligned = r.TrendDirection == s.Direction;
            bool opposed = r.TrendDirection != TradeDirection.Neutral && r.TrendDirection != s.Direction;
            bool normalVol = r.AtrRatio >= .55 && r.AtrRatio <= 1.75;
            bool persistentTrend = r.Efficiency >= .18 && r.TrendStrength >= .50 && r.AdxH1Slope >= 0;
            if (aligned && normalVol && persistentTrend)
                return "TREND_RELOAD";

            bool strongGeometry = s.GeometryQuality >= .68 && s.PrzConfluence >= .68 && s.Confidence >= .64;
            bool exhaustion = opposed && strongGeometry && r.ExtensionAtr >= 1.20 &&
                              r.AdxH1Slope <= .50 && r.AtrRatio >= .50 && r.AtrRatio <= 1.80;
            if (exhaustion)
                return "EXHAUSTION_REVERSAL";

            return "NO_EDGE";
        }

        private bool V72CraeFailureAllowed(V72CraeOpportunity o, RegimeSnapshot r)
        {
            if (o == null || o.Signal == null || r == null) return false;
            TradeDirection continuation = V72OppositeDirection(o.Signal.Direction);
            if (r.Transition || r.TrendDirection == TradeDirection.Neutral || r.TrendDirection != continuation)
                return false;
            return r.AtrRatio >= .55 && r.AtrRatio <= 1.75 &&
                   r.Efficiency >= .18 && r.TrendStrength >= .50 && r.AdxH1Slope >= 0;
        }

        private void V72CraeTrackRawPool(IEnumerable<PatternSignal> pool, HarmonicState h4, HarmonicState h1, RegimeSnapshot regime)
        {
            if (!EnableV72CraeAlpha) return;
            foreach (var g in (pool ?? Enumerable.Empty<PatternSignal>()).Where(V71ExpansionIntegrity).GroupBy(BuildSetupGeometryKey))
            {
                string setup = g.Key;
                if (string.IsNullOrWhiteSpace(setup) || !_v72CraeSeen.Add(setup)) continue;
                var xs = g.ToList();
                var s = V72CraeSelectPrimary(xs);
                if (s == null) continue;
                string fam = V71FamilyKey(s.PatternName);
                bool abcd = xs.Any(x => V71FamilyKey(x.PatternName) == "ABCD");
                bool standalone = fam == "ABCD";
                if (abcd) _v72CraeAbcdPrimitive++;
                DateTime now = Server.Time.ToUniversalTime();
                var o = new V72CraeOpportunity
                {
                    Id = "CRAE-" + (++_v72CraeSeq).ToString("D7"),
                    SetupKey = setup,
                    Family = fam,
                    Hypotheses = string.Join(",", xs.Select(x => V71FamilyKey(x.PatternName)).Distinct().OrderBy(x => x)),
                    Signal = s,
                    Conflict = ClassifyMtfConflict(s.Direction, h4, h1),
                    Regime = regime,
                    State = V72CraeState.WAIT_PRZ,
                    DetectedUtc = now,
                    OverallExpiryUtc = now.AddMinutes(15.0 * Math.Max(2, Math.Min(V71ExpansionTtlM15Bars, s.Profile.MaxAgeM15Bars))),
                    Direction = s.Direction,
                    HasAbcdConfluence = abcd,
                    StandaloneAbcd = standalone,
                    CapitalSemantic = !standalone,
                    Mode = "UNCLASSIFIED",
                    Lane = standalone ? "CRAE_ABCD_STANDALONE_SHADOW" : "CRAE_PENDING"
                };
                _v72Crae[o.Id] = o;
                _v72CraeDetected++;
                Print("[V72-CRAE-DETECTED] id={0} setup={1} family={2} hypotheses={3} abcd={4} fitLoss={5:F6} conflict={6}",
                    o.Id, o.SetupKey, o.Family, o.Hypotheses, o.HasAbcdConfluence, V72CraeGeometryLoss(s), o.Conflict);
            }
        }

        private bool V72CraeStructuralBreak(int i, PatternSignal s)
        {
            double c = _m1Bars.ClosePrices[i];
            return s.Direction == TradeDirection.Buy ? c < s.StructuralInvalidation : c > s.StructuralInvalidation;
        }

        private bool V72CraeStartFailure(int i, DateTime utc, V72CraeOpportunity o)
        {
            var current = BuildRegimeSnapshot();
            if (!V72CraeFailureAllowed(o, current))
            {
                o.Active = false;
                o.State = V72CraeState.EXPIRED;
                _v72CraeRegimeRejected++;
                return false;
            }
            o.Regime = current;
            o.Mode = "FAILURE_TREND";
            o.Direction = V72OppositeDirection(o.Signal.Direction);
            o.FailureBoundary = o.Signal.StructuralInvalidation;
            o.FailureBreakUtc = utc;
            o.ProofExpiryUtc = V72NextM15Boundary(utc).AddMinutes(15);
            if (o.ProofExpiryUtc > o.OverallExpiryUtc) o.ProofExpiryUtc = o.OverallExpiryUtc;
            o.LastStageUtc = utc;
            o.State = V72CraeState.FAILURE_WAIT_RETEST;
            Print("[V72-CRAE-FAILURE-BREAK] id={0} family={1} mode={2} boundary={3:F5} dir={4} expiry={5:o}",
                o.Id, o.Family, o.Mode, o.FailureBoundary, o.Direction, o.ProofExpiryUtc);
            return true;
        }

        private bool V72CraeArm(DateTime utc, V72CraeOpportunity o, TradeDirection direction,
            double entry, double stop, double target, double rr, string lane)
        {
            if (direction == TradeDirection.Neutral || rr + 1e-9 < MinimumNetRR ||
                !GeometryValid(direction, entry, stop, target)) return false;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return false;

            o.Direction = direction;
            o.Entry = entry;
            o.Stop = stop;
            o.Target = target;
            o.RiskDistance = risk;
            o.NetRr = rr;
            o.EntryUtc = utc;
            o.ProofUtc = utc;
            o.State = V72CraeState.ACTIVE;
            o.Lane = o.StandaloneAbcd ? "CRAE_ABCD_STANDALONE_SHADOW" : lane;
            o.CoreOverlapAtEntry = V71CoreHasActiveThesis() || _activeSetupOwners.ContainsKey(o.SetupKey) || _executedSetupKeys.Contains(o.SetupKey);
            if (o.CoreOverlapAtEntry) _v72CraeCoreOverlapAtEntry++;
            _v72CraeProofs++;
            _v72CraeArmed++;
            if (lane == "CRAE_FAILURE_CONTINUATION") _v72CraeFailureArmed++;

            Print("[V72-CRAE-PROVED] id={0} family={1} lane={2} mode={3} dir={4} entry={5:F5} stop={6:F5} target={7:F5} netRR={8:F4} coreOverlap={9} abcd={10}",
                o.Id, o.Family, o.Lane, o.Mode, o.Direction, o.Entry, o.Stop, o.Target, o.NetRr, o.CoreOverlapAtEntry, o.HasAbcdConfluence);
            if (o.CapitalSemantic && EnableV71ExpansionExecution) V72CraeQueueCapital(o, utc);
            return true;
        }

        private void V72CraeQueueCapital(V72CraeOpportunity o, DateTime utc)
        {
            if (o == null || o.CapitalQueued || o.StandaloneAbcd) return;
            DateTime exp = V72NextM15Boundary(utc).AddMinutes(15);
            if (exp > o.OverallExpiryUtc) exp = o.OverallExpiryUtc;
            if (exp <= utc.AddSeconds(1)) return;
            string cid = "V71EXP-CRAE-" + o.Id.Substring(Math.Max(0, o.Id.Length - 7));
            if (_v71Expansion.ContainsKey(cid)) return;

            HarmonicRoute route = o.Lane == "CRAE_FAILURE_CONTINUATION"
                ? HarmonicRoute.FAILURE_CONTINUATION
                : V71ExpansionRoute(o.Signal, o.Conflict, o.Regime);

            var e = new V71ExpansionCandidate
            {
                CandidateId = cid,
                IdentityKey = o.SetupKey + "|CRAE",
                SetupKey = o.SetupKey,
                Signal = o.Signal,
                Conflict = o.Conflict,
                Route = route,
                Regime = o.Regime,
                State = V71ExpansionState.ARMED,
                IsActive = true,
                DetectedUtc = o.DetectedUtc,
                ExpiryUtc = exp,
                PrzTouchUtc = o.PrzTouchUtc,
                ReactionProofUtc = o.ProofUtc,
                ConfirmationScore = 1.0,
                NetRR = o.NetRr,
                EntryAnchor = o.Entry,
                StructuralStop = o.Stop,
                CanonicalTarget = o.Target,
                RiskDistance = o.RiskDistance,
                TargetR = Math.Abs(o.Target - o.Entry) / Math.Max(o.RiskDistance, _symbol.PipSize),
                CapitalDirection = o.Direction,
                CapitalEligible = true,
                CoreOverlapObserved = false,
                CapitalReady = true,
                AwaitingPullbackFill = true,
                PullbackFilled = false,
                PullbackExpiryUtc = exp,
                CapitalLane = o.Lane,
                AbcdRole = o.HasAbcdConfluence ? "PARENT_PLUS_ABCD_CONFLUENCE" : "PARENT_FAMILY",
                AsymmetryCompression = Math.Max(.10, Math.Abs(o.Signal.D.Price - o.Stop) / Math.Max(o.RiskDistance, _symbol.PipSize)),
                EdgeMean = o.NetRr,
                EdgeLcb = o.NetRr
            };
            _v71Expansion[cid] = e;
            _v71ExpansionDetected++;
            o.CapitalQueued = true;
            _v72CraeCapitalQueued++;
            Print("[V72-CRAE-CAPITAL-QUEUE] id={0} cid={1} setup={2} family={3} lane={4} mode={5} expiry={6:o}",
                o.Id, cid, o.SetupKey, o.Family, o.Lane, o.Mode, exp);
        }

        private void V72CraeProcessFailureRetest(int i, DateTime utc, V72CraeOpportunity o)
        {
            if (utc <= o.FailureBreakUtc) return;
            if (utc >= o.ProofExpiryUtc)
            {
                o.Active = false;
                o.State = V72CraeState.EXPIRED;
                return;
            }
            double open = _m1Bars.OpenPrices[i], close = _m1Bars.ClosePrices[i],
                   high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i];
            bool touched = o.Direction == TradeDirection.Buy ? low <= o.FailureBoundary : high >= o.FailureBoundary;
            bool side = o.Direction == TradeDirection.Buy ? close > o.FailureBoundary : close < o.FailureBoundary;
            bool directional = o.Direction == TradeDirection.Buy ? close > open : close < open;
            if (!(touched && side && directional)) return;

            var r = BuildRegimeSnapshot();
            if (!V72CraeFailureAllowed(o, r))
            {
                o.Active = false;
                o.State = V72CraeState.EXPIRED;
                _v72CraeRegimeRejected++;
                return;
            }
            o.Regime = r;
            double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize), entry = close;
            double stop = o.Direction == TradeDirection.Buy
                ? Math.Min(low, o.FailureBoundary) - buffer
                : Math.Max(high, o.FailureBoundary) + buffer;
            double risk = Math.Abs(entry - stop);
            if (PriceToPips(risk) < MinStopLossPips) return;
            double cost = PipsToPrice(ModeledCostPips());
            double target = o.Direction == TradeDirection.Buy
                ? entry + 2.0 * risk + cost
                : entry - 2.0 * risk - cost;
            double rr = (PriceToPips(Math.Abs(target - entry)) - ModeledCostPips()) /
                        Math.Max(1e-9, PriceToPips(risk));
            V72CraeArm(utc, o, o.Direction, entry, stop, target, rr, "CRAE_FAILURE_CONTINUATION");
        }

        private void V72CraeProcessProof(int i, DateTime utc, V72CraeOpportunity o)
        {
            if (utc >= o.ProofExpiryUtc)
            {
                o.Active = false;
                o.State = V72CraeState.EXPIRED;
                return;
            }

            var s = o.Signal;
            double open = _m1Bars.OpenPrices[i], close = _m1Bars.ClosePrices[i],
                   high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i];
            double pc = _m1Bars.ClosePrices[i - 1],
                   ph = Math.Max(_m1Bars.HighPrices[i - 1], _m1Bars.HighPrices[i - 2]),
                   pl = Math.Min(_m1Bars.LowPrices[i - 1], _m1Bars.LowPrices[i - 2]);
            double body = Math.Max(Math.Abs(close - open), _symbol.PipSize), atr = Atr(_m1Bars, 14, i);
            bool buy = s.Direction == TradeDirection.Buy;
            bool directional = buy ? close > open : close < open;
            bool reclaim = buy ? (close > s.PrzLow && close >= pc) : (close < s.PrzHigh && close <= pc);
            bool bos = buy ? close > ph : close < pl;
            bool rejection = buy
                ? Math.Max(0, Math.Min(open, close) - low) >= body * .5
                : Math.Max(0, high - Math.Max(open, close)) >= body * .5;
            bool failed = buy
                ? (low < _m1Bars.LowPrices[i - 1] && close > _m1Bars.LowPrices[i - 1])
                : (high > _m1Bars.HighPrices[i - 1] && close < _m1Bars.HighPrices[i - 1]);
            bool sweep = buy ? low < _m1Bars.LowPrices[i - 1] : high > _m1Bars.HighPrices[i - 1];
            bool inside = close >= Math.Min(s.PrzLow, s.PrzHigh) && close <= Math.Max(s.PrzLow, s.PrzHigh);
            bool displacement = atr > 0 && body >= atr * .30;

            if (buy) o.LiquidityExtreme = o.LiquidityExtreme == 0 ? low : Math.Min(o.LiquidityExtreme, low);
            else o.LiquidityExtreme = o.LiquidityExtreme == 0 ? high : Math.Max(o.LiquidityExtreme, high);

            bool liquidity = o.Mode == "EXHAUSTION_REVERSAL" ? (sweep && failed) : (rejection || failed);
            if (o.State == V72CraeState.WAIT_LIQUIDITY)
            {
                if (!liquidity) return;
                o.LastStageUtc = utc;
                o.State = V72CraeState.WAIT_RECLAIM;
                return;
            }
            if (o.State == V72CraeState.WAIT_RECLAIM)
            {
                if (utc <= o.LastStageUtc) return;
                bool pass = o.Mode == "EXHAUSTION_REVERSAL" ? (reclaim || inside) : reclaim;
                if (!pass) return;
                o.LastStageUtc = utc;
                o.State = V72CraeState.WAIT_BOS;
                return;
            }
            if (o.State == V72CraeState.WAIT_BOS)
            {
                if (utc <= o.LastStageUtc || !(bos && displacement)) return;
                o.BosBoundary = buy ? ph : pl;
                o.LastStageUtc = utc;
                o.State = V72CraeState.WAIT_RETEST;
                return;
            }
            if (o.State == V72CraeState.WAIT_RETEST)
            {
                if (utc <= o.LastStageUtc) return;
                bool touched = buy ? low <= o.BosBoundary : high >= o.BosBoundary;
                bool side = buy ? close > o.BosBoundary : close < o.BosBoundary;
                if (!(touched && side && directional)) return;

                double buffer = Math.Max(PipsToPrice(ModeledCostPips()), _symbol.PipSize);
                double causalStop = buy ? o.LiquidityExtreme - buffer : o.LiquidityExtreme + buffer;
                double stop = buy
                    ? Math.Max(s.StructuralInvalidation, causalStop)
                    : Math.Min(s.StructuralInvalidation, causalStop);
                double target, rr;
                if (!SelectCanonicalBasketTarget(s, close, stop, out target, out rr)) return;
                string lane = o.Mode == "EXHAUSTION_REVERSAL" ? "CRAE_EXHAUSTION_REVERSAL" : "CRAE_TREND_RELOAD";
                V72CraeArm(utc, o, s.Direction, close, stop, target, rr, lane);
            }
        }

        private void V72CraeRecord(V72CraeOpportunity o, double r)
        {
            string dedupe = o.SetupKey + "|" + o.Lane;
            if (!_v72CraePayoffSeen.Add(dedupe)) return;
            string key = o.Lane + "|" + o.Family + "|" + o.Mode;
            V72PayoffAccumulator z;
            if (!_v72CraeCensus.TryGetValue(key, out z))
            {
                z = new V72PayoffAccumulator();
                _v72CraeCensus[key] = z;
            }
            z.N++;
            z.SumR += r;
            z.SumSqR += r * r;
            if (r > 0)
            {
                z.GrossProfitR += r;
                z.Wins++;
            }
            else if (r < 0) z.GrossLossR += -r;
        }

        private void V72CraeFinalizeOutcome(V72CraeOpportunity o, int i, string result, double? forcedR = null)
        {
            if (o == null || !o.Active || o.State != V72CraeState.ACTIVE || o.RiskDistance <= 0) return;
            double close = i >= 0 && i < _m1Bars.Count
                ? _m1Bars.ClosePrices[i]
                : (o.Direction == TradeDirection.Buy ? _symbol.Bid : _symbol.Ask);
            double closeR = (o.Direction == TradeDirection.Buy ? close - o.Entry : o.Entry - close) / o.RiskDistance;
            double r = forcedR.HasValue ? forcedR.Value : Math.Max(-1.0, Math.Min(o.NetRr, closeR));
            o.Result = result;
            o.Active = false;
            o.State = V72CraeState.CLOSED;
            _v72CraeClosed++;
            V72CraeRecord(o, r);
            Print("[V72-CRAE-OUTCOME] id={0} setup={1} family={2} lane={3} mode={4} abcd={5} coreOverlap={6} r={7:F6} mfeR={8:F6} maeR={9:F6} bars={10} result={11}",
                o.Id, o.SetupKey, o.Family, o.Lane, o.Mode, o.HasAbcdConfluence, o.CoreOverlapAtEntry,
                r, o.MfeR, o.MaeR, o.BarsActive, result);
        }

        private void V72CraeProcessActive(int i, DateTime utc, V72CraeOpportunity o)
        {
            if (utc <= o.EntryUtc) return;
            o.BarsActive++;
            double high = _m1Bars.HighPrices[i], low = _m1Bars.LowPrices[i];
            double fav = o.Direction == TradeDirection.Buy ? (high - o.Entry) / o.RiskDistance : (o.Entry - low) / o.RiskDistance;
            double adv = o.Direction == TradeDirection.Buy ? (o.Entry - low) / o.RiskDistance : (high - o.Entry) / o.RiskDistance;
            o.MfeR = Math.Max(o.MfeR, fav);
            o.MaeR = Math.Max(o.MaeR, adv);
            bool stop = o.Direction == TradeDirection.Buy ? low <= o.Stop : high >= o.Stop;
            bool target = o.Direction == TradeDirection.Buy ? high >= o.Target : low <= o.Target;
            if (stop && target)
            {
                V72CraeFinalizeOutcome(o, i, "AMBIGUOUS_STOP_FIRST_CONSERVATIVE", -1.0);
                return;
            }
            if (stop)
            {
                V72CraeFinalizeOutcome(o, i, "STRUCTURAL_STOP", -1.0);
                return;
            }
            if (target)
            {
                V72CraeFinalizeOutcome(o, i, "CANONICAL_TARGET", o.NetRr);
                return;
            }
            if (o.BarsActive >= 180)
                V72CraeFinalizeOutcome(o, i, "FIXED_180M_HORIZON");
        }

        private void V72CraeProcessM1(int i, DateTime utc)
        {
            if (!EnableV72CraeAlpha || i < 3) return;
            foreach (var o in _v72Crae.Values.Where(x => x.Active).ToList())
            {
                if (utc <= o.DetectedUtc) continue;
                if (o.State == V72CraeState.ACTIVE)
                {
                    V72CraeProcessActive(i, utc, o);
                    continue;
                }
                if (utc >= o.OverallExpiryUtc)
                {
                    o.Active = false;
                    o.State = V72CraeState.EXPIRED;
                    continue;
                }

                if (o.State != V72CraeState.WAIT_PRZ &&
                    o.State != V72CraeState.FAILURE_WAIT_RETEST &&
                    o.PrzTouchUtc.HasValue &&
                    V72CraeStructuralBreak(i, o.Signal))
                {
                    V72CraeStartFailure(i, utc, o);
                    continue;
                }

                if (o.State == V72CraeState.WAIT_PRZ)
                {
                    if (!BarTouchesPrz(i, o.Signal)) continue;
                    o.PrzTouchUtc = utc;
                    o.Regime = BuildRegimeSnapshot();
                    o.Mode = V72CraeClassifyPrimary(o.Signal, o.Conflict, o.Regime);
                    if (o.StandaloneAbcd || o.Mode == "NO_EDGE" || o.Mode == "TRANSITION_NO_TRADE")
                    {
                        o.Active = false;
                        o.State = V72CraeState.EXPIRED;
                        _v72CraeRegimeRejected++;
                        continue;
                    }
                    o.ProofExpiryUtc = V72NextM15Boundary(utc).AddMinutes(15);
                    if (o.ProofExpiryUtc > o.OverallExpiryUtc) o.ProofExpiryUtc = o.OverallExpiryUtc;
                    o.LiquidityExtreme = o.Signal.Direction == TradeDirection.Buy ? _m1Bars.LowPrices[i] : _m1Bars.HighPrices[i];
                    o.LastStageUtc = utc;
                    o.State = V72CraeState.WAIT_LIQUIDITY;
                    _v72CraePrzTouched++;
                    Print("[V72-CRAE-REGIME] id={0} family={1} mode={2} trend={3} atr={4:F4} eff={5:F4} strength={6:F4} adxSlope={7:F4} extAtr={8:F4}",
                        o.Id, o.Family, o.Mode, o.Regime.TrendDirection, o.Regime.AtrRatio, o.Regime.Efficiency,
                        o.Regime.TrendStrength, o.Regime.AdxH1Slope, o.Regime.ExtensionAtr);
                    continue;
                }

                if (o.State == V72CraeState.FAILURE_WAIT_RETEST)
                {
                    V72CraeProcessFailureRetest(i, utc, o);
                    continue;
                }

                V72CraeProcessProof(i, utc, o);
            }
        }

        private void V72CraeFinalizeAndPrint()
        {
            if (!EnableV72CraeAlpha) return;
            int i = LastClosedIndex(_m1Bars);
            foreach (var o in _v72Crae.Values.Where(x => x.Active && x.State == V72CraeState.ACTIVE).ToList())
                V72CraeFinalizeOutcome(o, i, "BACKTEST_END");

            foreach (var kv in _v72CraeCensus.OrderBy(x => x.Key))
            {
                string[] p = kv.Key.Split('|');
                string lane = p.Length > 0 ? p[0] : "UNKNOWN";
                string fam = p.Length > 1 ? p[1] : "UNKNOWN";
                string mode = p.Length > 2 ? p[2] : "UNKNOWN";
                var z = kv.Value;
                Print("[V72-CRAE-CENSUS] lane={0} family={1} mode={2} n={3} sumR={4:F9} sumSqR={5:F9} gpR={6:F9} glR={7:F9} wins={8}",
                    lane, fam, mode, z.N, z.SumR, z.SumSqR, z.GrossProfitR, z.GrossLossR, z.Wins);
            }
            Print("[V72-CRAE-SUMMARY] detected={0} przTouched={1} proofs={2} armed={3} failureArmed={4} closed={5} coreOverlapAtEntry={6} abcdPrimitive={7} capitalQueued={8} regimeRejected={9} active={10} counterfactualCoreIndependent=True",
                _v72CraeDetected, _v72CraePrzTouched, _v72CraeProofs, _v72CraeArmed, _v72CraeFailureArmed,
                _v72CraeClosed, _v72CraeCoreOverlapAtEntry, _v72CraeAbcdPrimitive, _v72CraeCapitalQueued,
                _v72CraeRegimeRejected, _v72Crae.Values.Count(x => x.Active));
        }
    }
}
