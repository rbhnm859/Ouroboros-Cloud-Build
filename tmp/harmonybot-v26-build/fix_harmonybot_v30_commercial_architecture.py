from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# ---------------------------------------------------------------------
# V30.0 MAJOR ARCHITECTURE RESET
# Harmonic/Fibonacci stays the sole setup generator.
# Risk sizing / broker protection / anti-hedge / duplicate protection stay frozen.
# ---------------------------------------------------------------------

param_anchor = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
'''
param_new = '''        [Parameter("V29.5 Min Invalidation Age Min", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V295MinInvalidationAgeMinutes { get; set; }

        [Parameter("V30 Architecture Enabled", DefaultValue = true)]
        public bool V30ArchitectureEnabled { get; set; }

        [Parameter("V30 Portfolio Max Candidates", DefaultValue = 8, MinValue = 2, MaxValue = 20)]
        public int V30PortfolioMaxCandidates { get; set; }

        [Parameter("V30 ATR Baseline Bars", DefaultValue = 240, MinValue = 60, MaxValue = 2880)]
        public int V30AtrBaselineBars { get; set; }

        [Parameter("V30 Min ATR Ratio", DefaultValue = 0.55, MinValue = 0.20, MaxValue = 1.20)]
        public double V30MinAtrRatio { get; set; }

        [Parameter("V30 Max ATR Ratio", DefaultValue = 1.70, MinValue = 1.00, MaxValue = 3.00)]
        public double V30MaxAtrRatio { get; set; }

        [Parameter("V30 Continuation M15", DefaultValue = 0.55, MinValue = 0.40, MaxValue = 0.90)]
        public double V30ContinuationM15 { get; set; }

        [Parameter("V30 Reversal M15", DefaultValue = 0.62, MinValue = 0.40, MaxValue = 0.90)]
        public double V30ReversalM15 { get; set; }

        [Parameter("V30 Confirmation", DefaultValue = 0.55, MinValue = 0.30, MaxValue = 0.95)]
        public double V30MinConfirmation { get; set; }

        [Parameter("V30 Reversal Confirmation", DefaultValue = 0.65, MinValue = 0.40, MaxValue = 0.95)]
        public double V30ReversalConfirmation { get; set; }

        [Parameter("V30 Reversal Geometry", DefaultValue = 0.58, MinValue = 0.40, MaxValue = 0.90)]
        public double V30ReversalGeometry { get; set; }

        [Parameter("V30 Reversal PRZ", DefaultValue = 0.58, MinValue = 0.40, MaxValue = 0.90)]
        public double V30ReversalPrz { get; set; }

        [Parameter("V30 Thesis Kill R", DefaultValue = 0.80, MinValue = 0.50, MaxValue = 1.20)]
        public double V30ThesisKillR { get; set; }

        [Parameter("V30 Thesis Proof R", DefaultValue = 0.15, MinValue = 0.05, MaxValue = 0.50)]
        public double V30ThesisProofR { get; set; }

        [Parameter("V30 Thesis Min Age Min", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 30.0)]
        public double V30ThesisMinAgeMinutes { get; set; }

        [Parameter("V30 Breakeven Trigger R", DefaultValue = 1.00, MinValue = 0.50, MaxValue = 2.00)]
        public double V30BreakevenTriggerR { get; set; }

        [Parameter("V30 Breakeven Lock R", DefaultValue = 0.10, MinValue = 0.00, MaxValue = 0.50)]
        public double V30BreakevenLockR { get; set; }

        [Parameter("V30 Trail Trigger R", DefaultValue = 1.50, MinValue = 0.80, MaxValue = 3.00)]
        public double V30TrailTriggerR { get; set; }

        [Parameter("V30 Trail Distance R", DefaultValue = 0.75, MinValue = 0.30, MaxValue = 1.50)]
        public double V30TrailDistanceR { get; set; }

        private long _v294DirectionBlocked;
        private long _v295ThesisInvalidations;
        private long _v295GridProofBlocked;
        private long _v30PortfolioBars;
        private long _v30PortfolioSignals;
        private long _v30RouteRejected;
        private long _v30SelectedBuy;
        private long _v30SelectedSell;
        private long _v30ThesisExits;
        private long _v30BreakevenLocks;
        private long _v30TrailUpdates;
        private readonly Dictionary<long, double> _v30PeakR = new Dictionary<long, double>();
        private readonly Dictionary<string, long> _v30PatternSeen = new Dictionary<string, long>();
        private readonly Dictionary<string, long> _v30PatternSelected = new Dictionary<string, long>();
'''
if s.count(param_anchor) != 1:
    raise SystemExit(f'V30 parameter anchor count={s.count(param_anchor)}; expected 1')
s = s.replace(param_anchor, param_new, 1)

# Portfolio detector path: collect multiple valid harmonic candidates instead of losing
# every alternative when the legacy single "best" candidate is rejected downstream.
portfolio_anchor = '''        private bool IsDefEnabled(PatternDef def)
'''
portfolio_method = '''        public bool TryDetectPortfolio(Bars bars, int currentIndex, double atrNow, Symbol symbol,
            double regimeScore, double buyTrend, double sellTrend, int maxSignals, out List<Signal> signals)
        {
            signals = new List<Signal>();
            if (bars == null || symbol == null || currentIndex < _depth * 4 || currentIndex >= bars.Count || atrNow <= 0)
                return false;

            List<SwingPoint> pivots = BuildSwingPoints(bars, currentIndex, _lookback, _depth);
            if (_closedBarProvisionalD)
                AppendClosedBarProvisionalPivot(pivots, bars, currentIndex, atrNow, _provisionalDMinMoveAtr);
            if (pivots.Count < 4) return false;

            int start = Math.Max(0, pivots.Count - _scanCount);
            var all = new List<Candidate>();
            for (int i = start; i <= pivots.Count - 4; i++)
            {
                foreach (var def in _defs)
                {
                    if (!IsDefEnabled(def)) continue;
                    Candidate c = Match(bars, pivots, i, def, atrNow, regimeScore, buyTrend, sellTrend, currentIndex);
                    if (c == null) continue;
                    SwingPoint reference = c.Family == PatternFamily.Shark ? c.C : c.D;
                    if (reference == null) continue;
                    if (_candidateMaxAgeBars > 0 && currentIndex - reference.Index > _candidateMaxAgeBars) continue;
                    double candidateEntry = c.IsBullish ? symbol.Ask : symbol.Bid;
                    if (candidateEntry <= 0) continue;
                    if (Math.Abs(candidateEntry - reference.Price) > atrNow * _maxEntryDeviationAtr) continue;
                    all.Add(c);
                }
            }
            if (all.Count == 0) return false;

            var emitted = new HashSet<string>();
            foreach (Candidate best in all.OrderByDescending(c => c.Score))
            {
                if (signals.Count >= Math.Max(2, maxSignals)) break;
                int groupKey = best.X != null ? best.X.Index : best.A.Index;
                int sameDirectionConsensus = all.Count(c => (c.X != null ? c.X.Index : c.A.Index) == groupKey && c.IsBullish == best.IsBullish);
                double finalScore = Math.Min(1.0, best.Score * (sameDirectionConsensus >= 2 ? _consensusBonus : 1.0));
                if (finalScore < best.Threshold || finalScore < _globalMinScore || finalScore < _minConfidence) continue;

                TradeDirection dir = best.IsBullish ? TradeDirection.Buy : TradeDirection.Sell;
                SwingPoint referencePoint = best.Family == PatternFamily.Shark ? best.C : best.D;
                if (referencePoint == null) continue;
                string key = (best.PatternName ?? "NA") + "|" + dir + "|" + referencePoint.Index;
                if (!emitted.Add(key)) continue;

                double entry = dir == TradeDirection.Buy ? symbol.Ask : symbol.Bid;
                double stop = dir == TradeDirection.Buy
                    ? referencePoint.Price - atrNow * _slAtrMult
                    : referencePoint.Price + atrNow * _slAtrMult;
                double tpDist;
                if (best.Family == PatternFamily.Shark || best.Family == PatternFamily.FiveZero)
                {
                    double bc = Math.Abs(best.B.Price - best.C.Price);
                    tpDist = Math.Max(bc * 0.5, atrNow * 1.2);
                }
                else
                {
                    double cd = best.C != null && best.D != null ? Math.Abs(best.C.Price - best.D.Price) : atrNow;
                    tpDist = Math.Max(cd * _tpCdMult, atrNow * 1.2);
                }
                double tp = dir == TradeDirection.Buy ? entry + tpDist : entry - tpDist;
                if (dir == TradeDirection.Buy && !(stop < entry && entry < tp)) continue;
                if (dir == TradeDirection.Sell && !(tp < entry && entry < stop)) continue;

                signals.Add(new Signal
                {
                    Direction = dir,
                    EntryPrice = entry,
                    StopLoss = stop,
                    TakeProfit = tp,
                    Confidence = finalScore,
                    PatternName = best.PatternName,
                    CompletionIndex = referencePoint.Index,
                    GeometryQuality = best.GeometryQuality,
                    PrzConfluence = best.PrzConfluence,
                    TimeSymmetry = best.TimeSymmetry,
                    PivotQuality = best.PivotQuality,
                    ReferencePrice = referencePoint.Price
                });
            }
            return signals.Count > 0;
        }

'''
if s.count(portfolio_anchor) != 1:
    raise SystemExit(f'V30 portfolio method anchor count={s.count(portfolio_anchor)}; expected 1')
s = s.replace(portfolio_anchor, portfolio_method + portfolio_anchor, 1)

# Replace the single-best detector call with portfolio routing when V30 is active.
detect_old = '''                Signal signal = null;
                bool v29FromPending = false;
                if (v29EvaluationOpen && V29TryGetTriggeredPending(atrNow, signalIndex, out signal))
                {
                    v29FromPending = true;
                }
                else
                {
                    if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))
                        return;
                    if (signal == null) return;
                    if (v29EvaluationOpen) _diagSignalsDetected++; else _v29WarmupDetected++;
                }
'''
detect_new = '''                Signal signal = null;
                bool v29FromPending = false;
                if (v29EvaluationOpen && V29TryGetTriggeredPending(atrNow, signalIndex, out signal))
                {
                    v29FromPending = true;
                }
                else if (V30ArchitectureEnabled)
                {
                    List<Signal> v30Portfolio;
                    if (!_detector.TryDetectPortfolio(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend,
                        V30PortfolioMaxCandidates, out v30Portfolio))
                        return;
                    _v30PortfolioBars++;
                    _v30PortfolioSignals += v30Portfolio.Count;
                    foreach (var v30s in v30Portfolio)
                    {
                        string pn = v30s.PatternName ?? "NA";
                        _v30PatternSeen[pn] = (_v30PatternSeen.ContainsKey(pn) ? _v30PatternSeen[pn] : 0) + 1;
                    }
                    signal = V30SelectPortfolioSignal(v30Portfolio, signalIndex, atrNow);
                    if (signal == null) return;
                    if (v29EvaluationOpen) _diagSignalsDetected++; else _v29WarmupDetected++;
                }
                else
                {
                    if (!_detector.TryDetect(_signalBars, signalIndex, atrNow, _symbol, regimeScore, buyTrend, sellTrend, out signal))
                        return;
                    if (signal == null) return;
                    if (v29EvaluationOpen) _diagSignalsDetected++; else _v29WarmupDetected++;
                }
'''
if s.count(detect_old) != 1:
    raise SystemExit(f'V30 detector block count={s.count(detect_old)}; expected 1')
s = s.replace(detect_old, detect_new, 1)

# Re-evaluate pending candidates through V30 router and bypass the legacy trend gate,
# which was built for trend-following alignment rather than harmonic reversal/transition routing.
mtf_old = '''                if (!PassMtfFilter(signal))
                {
                    _diagMtfBlocked++;
                    if (v29FromPending) _v29PendingMtfBlocked++;
                    return;
                }
'''
mtf_new = '''                if (V30ArchitectureEnabled)
                {
                    string v30Route;
                    double v30RouteQuality, v30Confirmation, v30AtrRatio, v30M15;
                    if (!V30EvaluateSignal(signal, signalIndex, atrNow, out v30Route, out v30RouteQuality, out v30Confirmation, out v30AtrRatio, out v30M15))
                    {
                        _v30RouteRejected++;
                        if (v29FromPending) V29RemovePending(signal, "V30_ROUTE_RECHECK", false);
                        return;
                    }
                    Print("[V30-ROUTE] pattern={0} dir={1} route={2} routeQ={3:F3} confirm={4:F3} atrRatio={5:F3} m15={6:F3} q={7:F3} prz={8:F3}",
                        signal.PatternName ?? "NA", signal.Direction, v30Route, v30RouteQuality, v30Confirmation, v30AtrRatio, v30M15,
                        signal.GeometryQuality, signal.PrzConfluence);
                }
                else if (!PassMtfFilter(signal))
                {
                    _diagMtfBlocked++;
                    if (v29FromPending) _v29PendingMtfBlocked++;
                    return;
                }
'''
if s.count(mtf_old) != 1:
    raise SystemExit(f'V30 MTF anchor count={s.count(mtf_old)}; expected 1')
s = s.replace(mtf_old, mtf_new, 1)

# V30 helpers before legacy signal key helper.
helper_anchor = '''        private string BuildSignalKey(Signal signal)
'''
helpers = '''        private double V30Clamp01(double x)
        {
            return Math.Max(0.0, Math.Min(1.0, x));
        }

        private double V30RollingTrueRangeBaseline(int endIndex)
        {
            if (_signalBars == null || endIndex < 1) return 0;
            int lookback = Math.Max(60, Math.Min(2880, V30AtrBaselineBars));
            int end = Math.Min(endIndex, _signalBars.Count - 1);
            int start = Math.Max(1, end - lookback + 1);
            double sum = 0;
            int count = 0;
            for (int i = start; i <= end; i++)
            {
                double high = _signalBars.HighPrices[i];
                double low = _signalBars.LowPrices[i];
                double prevClose = _signalBars.ClosePrices[i - 1];
                double tr = Math.Max(high - low, Math.Max(Math.Abs(high - prevClose), Math.Abs(low - prevClose)));
                sum += tr;
                count++;
            }
            return count > 0 ? sum / count : 0;
        }

        private int V30AlignmentState(TradeDirection direction, double fast, double slow)
        {
            if (fast <= 0 || slow <= 0) return -1;
            bool aligned = direction == TradeDirection.Buy ? fast > slow : fast < slow;
            return aligned ? 1 : 0;
        }

        private double V30M15DirectionalScore(Signal signal, int signalIndex, double atrNow)
        {
            if (signal == null || _signalBars == null || atrNow <= 0) return 0.50;
            int i = Math.Min(signalIndex, _signalBars.Count - 2);
            if (i < 12) return 0.50;
            int j = i - 12;
            double impulse = _signalBars.ClosePrices[i] - _signalBars.ClosePrices[j];
            if (signal.Direction == TradeDirection.Sell) impulse = -impulse;
            double normalized = impulse / Math.Max(atrNow, 1e-9);
            return V30Clamp01(0.50 + 0.30 * normalized);
        }

        private double V30ConfirmationScore(Signal signal, int signalIndex, double atrNow)
        {
            if (signal == null || _signalBars == null || atrNow <= 0) return 0;
            int i = Math.Min(signalIndex, _signalBars.Count - 2);
            if (i < 2) return 0;
            double open = _signalBars.OpenPrices[i];
            double close = _signalBars.ClosePrices[i];
            double high = _signalBars.HighPrices[i];
            double low = _signalBars.LowPrices[i];
            double prevClose = _signalBars.ClosePrices[i - 1];
            double prevHigh = _signalBars.HighPrices[i - 1];
            double prevLow = _signalBars.LowPrices[i - 1];
            double body = Math.Abs(close - open);
            double safeBody = Math.Max(body, atrNow * 0.005);
            bool directional, reclaim, microBreak, rejection;
            if (signal.Direction == TradeDirection.Buy)
            {
                directional = close > open;
                reclaim = close >= prevClose;
                microBreak = close > prevHigh;
                double wick = Math.Max(0.0, Math.Min(open, close) - low);
                rejection = wick >= safeBody * 0.50;
            }
            else
            {
                directional = close < open;
                reclaim = close <= prevClose;
                microBreak = close < prevLow;
                double wick = Math.Max(0.0, high - Math.Max(open, close));
                rejection = wick >= safeBody * 0.50;
            }
            return (directional ? 0.25 : 0.0) + (reclaim ? 0.20 : 0.0) + (microBreak ? 0.35 : 0.0) + (rejection ? 0.20 : 0.0);
        }

        private bool V30EvaluateSignal(Signal signal, int signalIndex, double atrNow,
            out string route, out double routeQuality, out double confirmation, out double atrRatio, out double m15)
        {
            route = "REJECT";
            routeQuality = 0;
            confirmation = V30ConfirmationScore(signal, signalIndex, atrNow);
            double baseline = V30RollingTrueRangeBaseline(signalIndex);
            atrRatio = baseline > 0 ? atrNow / baseline : 1.0;
            m15 = V30M15DirectionalScore(signal, signalIndex, atrNow);
            if (atrRatio < V30MinAtrRatio || atrRatio > V30MaxAtrRatio) return false;

            int h1 = V30AlignmentState(signal.Direction, _cacheH1Ema50, _cacheH1Ema200);
            int h4 = V30AlignmentState(signal.Direction, _cacheH4Ema50, _cacheH4Ema200);
            int known = (h1 >= 0 ? 1 : 0) + (h4 >= 0 ? 1 : 0);
            int aligned = (h1 == 1 ? 1 : 0) + (h4 == 1 ? 1 : 0);
            int opposed = (h1 == 0 ? 1 : 0) + (h4 == 0 ? 1 : 0);

            bool continuation = aligned >= 1 && m15 >= V30ContinuationM15 && confirmation >= V30MinConfirmation;
            bool reversal = opposed >= 1 && m15 >= V30ReversalM15
                && signal.GeometryQuality >= V30ReversalGeometry && signal.PrzConfluence >= V30ReversalPrz
                && confirmation >= V30ReversalConfirmation;
            bool transition = known == 2 && aligned == 1 && opposed == 1
                && m15 >= 0.60 && confirmation >= V30ReversalConfirmation;

            double contQ = continuation ? V30Clamp01(0.35 * m15 + 0.25 * confirmation + 0.20 * signal.GeometryQuality + 0.20 * signal.PrzConfluence) : -1;
            double revQ = reversal ? V30Clamp01(0.30 * m15 + 0.25 * confirmation + 0.25 * signal.GeometryQuality + 0.20 * signal.PrzConfluence) : -1;
            double transQ = transition ? V30Clamp01(0.30 * m15 + 0.30 * confirmation + 0.20 * signal.GeometryQuality + 0.20 * signal.PrzConfluence) : -1;

            if (contQ < 0 && revQ < 0 && transQ < 0) return false;
            if (revQ >= contQ && revQ >= transQ) { route = "REVERSAL"; routeQuality = revQ; }
            else if (transQ >= contQ) { route = "TRANSITION"; routeQuality = transQ; }
            else { route = "CONTINUATION"; routeQuality = contQ; }
            return true;
        }

        private Signal V30SelectPortfolioSignal(List<Signal> portfolio, int signalIndex, double atrNow)
        {
            if (portfolio == null || portfolio.Count == 0) return null;
            Signal best = null;
            double bestRank = double.MinValue;
            string bestRoute = "";
            double bestRouteQ = 0, bestConfirm = 0, bestRatio = 0, bestM15 = 0;

            foreach (var candidate in portfolio)
            {
                string route;
                double routeQ, confirmation, ratio, m15;
                if (!V30EvaluateSignal(candidate, signalIndex, atrNow, out route, out routeQ, out confirmation, out ratio, out m15))
                {
                    _v30RouteRejected++;
                    continue;
                }
                double rank = 0.30 * candidate.Confidence + 0.25 * candidate.GeometryQuality + 0.15 * candidate.PrzConfluence
                    + 0.15 * confirmation + 0.15 * routeQ;
                if (rank > bestRank)
                {
                    bestRank = rank; best = candidate; bestRoute = route; bestRouteQ = routeQ;
                    bestConfirm = confirmation; bestRatio = ratio; bestM15 = m15;
                }
            }

            if (best != null)
            {
                string pn = best.PatternName ?? "NA";
                _v30PatternSelected[pn] = (_v30PatternSelected.ContainsKey(pn) ? _v30PatternSelected[pn] : 0) + 1;
                if (best.Direction == TradeDirection.Buy) _v30SelectedBuy++; else _v30SelectedSell++;
                Print("[V30-SELECT] pattern={0} dir={1} route={2} rank={3:F3} routeQ={4:F3} confirm={5:F3} atrRatio={6:F3} m15={7:F3} portfolio={8}",
                    pn, best.Direction, bestRoute, bestRank, bestRouteQ, bestConfirm, bestRatio, bestM15, portfolio.Count);
            }
            return best;
        }

'''
if s.count(helper_anchor) != 1:
    raise SystemExit(f'V30 helper anchor count={s.count(helper_anchor)}; expected 1')
s = s.replace(helper_anchor, helpers + helper_anchor, 1)

# V30 primary lifecycle replaces legacy partial/BE/trailing only for non-grid primary trades.
manage_anchor = '''                EnsureRuntimeState(p);
                double profitPips = p.Pips;
                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);

                if (EnablePartialTP && !_tp1Done[p.Id] && !_partialClosing.Contains(p.Id))
'''
manage_new = '''                EnsureRuntimeState(p);
                double profitPips = p.Pips;
                double beOffsetPips = Math.Max(BreakEvenOffsetPips, MinStopDistancePips);

                if (V30ArchitectureEnabled && !EnableFibGrid)
                {
                    V30ManagePrimaryPosition(p);
                    continue;
                }

                if (EnablePartialTP && !_tp1Done[p.Id] && !_partialClosing.Contains(p.Id))
'''
if s.count(manage_anchor) != 1:
    raise SystemExit(f'V30 primary lifecycle anchor count={s.count(manage_anchor)}; expected 1')
s = s.replace(manage_anchor, manage_new, 1)

partial_anchor = '''        private bool TryPartialClose(Position p)
'''
primary_helper = '''        private void V30ManagePrimaryPosition(Position p)
        {
            if (p == null) return;
            Position live = Positions.FindById((int)p.Id);
            if (live == null) return;
            p = live;
            double riskPips = _initialRiskPips.ContainsKey(p.Id) ? Math.Max(_initialRiskPips[p.Id], 0.0001) : 0.0001;
            double currentR = p.Pips / riskPips;
            double peakR = _v30PeakR.ContainsKey(p.Id) ? _v30PeakR[p.Id] : 0.0;
            if (currentR > peakR) peakR = currentR;
            _v30PeakR[p.Id] = peakR;

            double ageMin = Math.Max(0.0, (Server.Time - p.EntryTime).TotalMinutes);
            if (ageMin >= V30ThesisMinAgeMinutes && peakR < V30ThesisProofR && currentR <= -Math.Abs(V30ThesisKillR))
            {
                _v30ThesisExits++;
                Print("[V30-THESIS-EXIT] pos={0} pattern={1} dir={2} peakR={3:F3} currentR={4:F3} ageMin={5:F1}",
                    p.Id, _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "NA", p.TradeType, peakR, currentR, ageMin);
                ClosePosition(p);
                return;
            }

            if (peakR >= V30BreakevenTriggerR)
            {
                double lockPips = riskPips * Math.Max(0.0, V30BreakevenLockR);
                double be = p.TradeType == TradeType.Buy
                    ? p.EntryPrice + PipsToPrice(lockPips)
                    : p.EntryPrice - PipsToPrice(lockPips);
                if (TryModifyStopLoss(p, be)) _v30BreakevenLocks++;
            }

            live = Positions.FindById((int)p.Id);
            if (live == null) return;
            p = live;
            if (peakR >= V30TrailTriggerR)
            {
                double trailPips = riskPips * Math.Max(0.10, V30TrailDistanceR);
                double trail = p.TradeType == TradeType.Buy
                    ? _symbol.Bid - PipsToPrice(trailPips)
                    : _symbol.Ask + PipsToPrice(trailPips);
                if (TryModifyStopLoss(p, trail)) _v30TrailUpdates++;
            }

            Print("[V30-LIFECYCLE] pos={0} pattern={1} dir={2} currentR={3:F3} peakR={4:F3} ageMin={5:F1}",
                p.Id, _patternByPosition.ContainsKey(p.Id) ? _patternByPosition[p.Id] : "NA", p.TradeType, currentR, peakR, ageMin);
        }

'''
if s.count(partial_anchor) != 1:
    raise SystemExit(f'V30 primary helper anchor count={s.count(partial_anchor)}; expected 1')
s = s.replace(partial_anchor, primary_helper + partial_anchor, 1)

# Runtime peak-R state.
ensure_anchor = '''            if (!_lastSlModifyTime.ContainsKey(p.Id)) _lastSlModifyTime[p.Id] = DateTime.MinValue;
'''
if s.count(ensure_anchor) != 1:
    raise SystemExit(f'V30 runtime state anchor count={s.count(ensure_anchor)}; expected 1')
s = s.replace(ensure_anchor, ensure_anchor + '''            if (!_v30PeakR.ContainsKey(p.Id)) _v30PeakR[p.Id] = 0.0;
''', 1)

prune_anchor = '''            RemoveMissing(_totalClosedUnits, openIds);
            _partialClosing.RemoveWhere(k => !openIds.Contains(k));
'''
if s.count(prune_anchor) != 1:
    raise SystemExit(f'V30 prune anchor count={s.count(prune_anchor)}; expected 1')
s = s.replace(prune_anchor, '''            RemoveMissing(_totalClosedUnits, openIds);
            RemoveMissing(_v30PeakR, openIds);
            _partialClosing.RemoveWhere(k => !openIds.Contains(k));
''', 1)

# Do not path-dependently disable pattern families after observing in-run win rate.
auto_anchor = '''        private void AutoDisableWeakPatterns()
        {
            if (!AutoDisableLosing || _detector == null) return;
'''
if s.count(auto_anchor) != 1:
    raise SystemExit(f'V30 auto-disable anchor count={s.count(auto_anchor)}; expected 1')
s = s.replace(auto_anchor, '''        private void AutoDisableWeakPatterns()
        {
            if (V30ArchitectureEnabled) return;
            if (!AutoDisableLosing || _detector == null) return;
''', 1)

# Version/reporting.
stop_anchor = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            EnsureServerSideProtectionBeforeStop();
'''
stop_new = '''            Print("[V295-THESIS-SUMMARY] invalidations={0} gridProofBlocked={1} guard={2} killR={3:F2} proofR={4:F2}",
                _v295ThesisInvalidations, _v295GridProofBlocked, V295ThesisGuard, V295NoMfeKillR, V295MinFavorableProofR);
            Print("[V30-SUMMARY] portfolioBars={0} portfolioSignals={1} routeRejected={2} selectedBuy={3} selectedSell={4} thesisExits={5} beLocks={6} trailUpdates={7}",
                _v30PortfolioBars, _v30PortfolioSignals, _v30RouteRejected, _v30SelectedBuy, _v30SelectedSell,
                _v30ThesisExits, _v30BreakevenLocks, _v30TrailUpdates);
            foreach (var kv in _v30PatternSeen.OrderBy(k => k.Key))
                Print("[V30-PATTERN] pattern={0} seen={1} selected={2}", kv.Key, kv.Value,
                    _v30PatternSelected.ContainsKey(kv.Key) ? _v30PatternSelected[kv.Key] : 0);
            EnsureServerSideProtectionBeforeStop();
'''
if s.count(stop_anchor) != 1:
    raise SystemExit(f'V30 stop summary anchor count={s.count(stop_anchor)}; expected 1')
s = s.replace(stop_anchor, stop_new, 1)

old_version = 'V29.5-Thesis-Validity-Minimum-Patch-Dev'
if s.count(old_version) != 1:
    raise SystemExit(f'V30 version marker count={s.count(old_version)}; expected 1')
s = s.replace(old_version, 'V30.0-Regime-Routed-Harmonic-Portfolio-RC', 1)

start_print = 'HarmonyBotPro V29 Persistent PRZ | {0} TF={1} Equity={2:F2} | Micro={3} AntiHedge={4} Risk={5:F1}% | DailyLock={6:F1}% ConsecLossLimit={7} | FibGrid={8}'
if start_print in s:
    s = s.replace(start_print, 'HarmonyBotPro V30.0 Regime-Routed Harmonic Portfolio | {0} TF={1} Equity={2:F2} | Micro={3} AntiHedge={4} Risk={5:F1}% | DailyLock={6:F1}% ConsecLossLimit={7} | FibGrid={8}', 1)

required = [
    'V30.0-Regime-Routed-Harmonic-Portfolio-RC',
    'TryDetectPortfolio',
    'V30SelectPortfolioSignal',
    'V30EvaluateSignal',
    '[V30-SELECT]',
    '[V30-ROUTE]',
    '[V30-THESIS-EXIT]',
    '[V30-LIFECYCLE]',
    '[V30-SUMMARY]',
    'V29.3 GRID-RISK-CAP-HOTFIX',
    'V295ThesisGuard'
]
for token in required:
    if token not in s:
        raise SystemExit('missing V30 token: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied HarmonyBot V30.0 Regime-Routed Harmonic Portfolio Engine')
print('Major changes: multi-candidate portfolio routing + dual-direction-ready regime router + primary/Grid lifecycle decoupling')
print('Frozen: risk sizing, margin/min-volume protection, anti-hedge, duplicate protection, server SL, broker handling')
