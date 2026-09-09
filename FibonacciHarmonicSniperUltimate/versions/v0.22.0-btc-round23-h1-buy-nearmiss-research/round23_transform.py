from pathlib import Path
import hashlib, sys

if len(sys.argv) != 3:
    raise SystemExit('usage: round23_transform.py <round22.cs> <round23.cs>')
src = Path(sys.argv[1])
out = Path(sys.argv[2])
text = src.read_text()
expected = 'd103dce25851d89bd51cb736c14ae91f416927dedfc692a441f28115a3343029'
actual = hashlib.sha256(text.encode()).hexdigest()
if actual != expected:
    raise SystemExit(f'Round22 source SHA mismatch: {actual}')

param_anchor = '''        [Parameter("Debug Logging", DefaultValue = true, Group = "Diagnostics")]
        public bool DebugLogging { get; set; }
'''
param_insert = param_anchor + '''
        [Parameter("R23 H1 Buy Near-Miss Diagnostics", DefaultValue = true, Group = "BTC Round23 Near-Miss")]
        public bool Round23NearMissDiagnostics { get; set; }

        [Parameter("R23 Score Floor", DefaultValue = 82.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round23 Near-Miss")]
        public double Round23ScoreFloor { get; set; }

        [Parameter("R23 Max Extended Age Bars", DefaultValue = 18, MinValue = 16, MaxValue = 30, Group = "BTC Round23 Near-Miss")]
        public int Round23MaxExtendedAgeBars { get; set; }

        [Parameter("R23 Max Extended Distance ATR", DefaultValue = 2.0, MinValue = 1.8, MaxValue = 3.0, Group = "BTC Round23 Near-Miss")]
        public double Round23MaxExtendedDistanceAtr { get; set; }

        [Parameter("R23 Shadow Horizon Bars", DefaultValue = 48, MinValue = 12, MaxValue = 168, Group = "BTC Round23 Near-Miss")]
        public int Round23ShadowHorizonBars { get; set; }
'''
if param_anchor not in text:
    raise SystemExit('parameter anchor not found')
text = text.replace(param_anchor, param_insert, 1)

state_anchor = '''        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);

        protected override void OnStart()
'''
state_insert = '''        private readonly Dictionary<string, PatternStats> _stats = new Dictionary<string, PatternStats>(StringComparer.OrdinalIgnoreCase);

        private sealed class Round23ShadowState
        {
            public string Category;
            public string Pattern;
            public string SignalKey;
            public int DIndex;
            public double Score;
            public int AgeBars;
            public double DistanceAtr;
            public bool FeasibleAtSignal;
            public int StartBar;
            public DateTime StartTime;
            public double EntryPrice;
            public double StopPrice;
            public double TargetPrice;
            public double RiskDistance;
            public double TargetR;
            public double MfeR;
            public double MaeR;
        }

        private sealed class Round23PendingConfirm
        {
            public PatternMatch Match;
            public int SourceBar;
            public string SeenKey;
        }

        private readonly List<Round23ShadowState> _round23Shadows = new List<Round23ShadowState>();
        private readonly List<Round23PendingConfirm> _round23Pending = new List<Round23PendingConfirm>();
        private readonly HashSet<string> _round23Seen = new HashSet<string>(StringComparer.Ordinal);
        private int _round23Created;
        private int _round23Completed;
        private int _round23BaselineResolved;

        protected override void OnStart()
'''
if state_anchor not in text:
    raise SystemExit('state anchor not found')
text = text.replace(state_anchor, state_insert, 1)

onstart_anchor = '''            Print("BTC Round22 Capital Efficiency | H1 Buy={0:F2}% H1 Sell={1:F2}% M30 Buy={2:F2}% M30 Sell={3:F2}%", Round22H1BuyRiskPercent, Round22H1SellRiskPercent, Round22M30BuyRiskPercent, Round22M30SellRiskPercent);
'''
onstart_insert = onstart_anchor + '''            Print("BTC Round23 Near-Miss Research | enabled={0} scoreFloor={1:F1} ageMax={2} distMax={3:F2}ATR horizon={4} bars", Round23NearMissDiagnostics, Round23ScoreFloor, Round23MaxExtendedAgeBars, Round23MaxExtendedDistanceAtr, Round23ShadowHorizonBars);
'''
if onstart_anchor not in text:
    raise SystemExit('onstart anchor not found')
text = text.replace(onstart_anchor, onstart_insert, 1)

onbar_anchor = '''        protected override void OnBarClosed()
        {
            if (Bars.Count < Math.Max(100, PivotLeft + PivotRight + 20))
'''
onbar_insert = '''        protected override void OnBarClosed()
        {
            Round23UpdateShadows();
            Round23ProcessPendingConfirmations();
            Round23ScanH1BuyNearMisses();

            if (Bars.Count < Math.Max(100, PivotLeft + PivotRight + 20))
'''
if onbar_anchor not in text:
    raise SystemExit('OnBarClosed anchor not found')
text = text.replace(onbar_anchor, onbar_insert, 1)

onstop_anchor = '''        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
'''
onstop_insert = '''        protected override void OnStop()
        {
            Round23FlushShadows();
            Print("[R23 STATS] created={0} completed={1} active={2} pending={3} baselineResolved={4}", _round23Created, _round23Completed, _round23Shadows.Count, _round23Pending.Count, _round23BaselineResolved);
            Positions.Closed -= OnPositionClosed;
'''
if onstop_anchor not in text:
    raise SystemExit('OnStop anchor not found')
text = text.replace(onstop_anchor, onstop_insert, 1)

method_anchor = '''        private bool IsTrendAligned(TradeType direction)
'''
methods = r'''        private bool Round23BaseBuyConfirmation(PatternMatch m, int last, double atr, bool includeDistance)
        {
            if (m == null || m.Direction != TradeType.Buy || atr <= 0)
                return false;
            double close = Bars.ClosePrices[last];
            double open = Bars.OpenPrices[last];
            double distanceAtr = Math.Abs(close - m.D.Price) / atr;
            if (includeDistance && distanceAtr > MaxEntryDistanceAtr)
                return false;
            if (close < m.D.Price + atr * ConfirmationMoveAtr)
                return false;
            if (UseCandleConfirmation && close <= open)
                return false;
            if ((EmaFilterMode == TrendFilterMode.ConfirmOnly || EmaFilterMode == TrendFilterMode.Strict) && !IsTrendAligned(TradeType.Buy))
                return false;
            if (ConfirmationMode == EntryConfirmationMode.Conservative && close <= Bars.HighPrices[last - 1])
                return false;
            return true;
        }

        private void Round23TryCreateShadow(string category, PatternMatch m, int ageBars, double distanceAtr)
        {
            if (!Round23NearMissDiagnostics || m == null || m.Direction != TradeType.Buy)
                return;
            string key = category + "|" + m.SignalKey;
            if (_round23Seen.Contains(key))
                return;
            _round23Seen.Add(key);

            int last = Bars.Count - 1;
            double atr = _atr.Result.LastValue;
            if (atr <= 0)
                return;
            double entry = Symbol.Ask;
            double stopAnchor = ResolveStopAnchor(m);
            double slPrice = stopAnchor - atr * SlAtrBuffer;
            double stopDistance = entry - slPrice;
            if (double.IsNaN(stopDistance) || double.IsInfinity(stopDistance) || stopDistance <= 0)
                return;
            double slPips = stopDistance / Symbol.PipSize;
            if (slPips < MinStopPips)
                slPips = MinStopPips;
            if (MaxStopPips > 0 && slPips > MaxStopPips)
                return;
            double tpPips = CalculateTakeProfitPips(m, entry, slPips);
            if (tpPips < slPips * MinimumRiskReward)
            {
                if (TargetRiskRewardPolicy == TargetRiskRewardPolicyKind.RejectPoorGeometry)
                    return;
                tpPips = slPips * FallbackRiskReward;
            }
            if (tpPips < slPips * MinimumRiskReward)
                return;

            double riskDistance = slPips * Symbol.PipSize;
            var sh = new Round23ShadowState
            {
                Category = category,
                Pattern = m.Definition.Name,
                SignalKey = m.SignalKey,
                DIndex = m.D.Index,
                Score = m.Score,
                AgeBars = ageBars,
                DistanceAtr = distanceAtr,
                FeasibleAtSignal = PassGlobalLimits(),
                StartBar = last,
                StartTime = Server.Time,
                EntryPrice = entry,
                StopPrice = entry - riskDistance,
                TargetPrice = entry + tpPips * Symbol.PipSize,
                RiskDistance = riskDistance,
                TargetR = tpPips / slPips,
                MfeR = 0.0,
                MaeR = 0.0
            };
            _round23Shadows.Add(sh);
            _round23Created++;
            Print("[R23 SHADOW OPEN] cat={0} pattern={1} d={2} time={3:yyyy-MM-ddTHH:mm:ss} score={4:F2} age={5} distAtr={6:F3} feasible={7} entry={8:F2} stop={9:F2} target={10:F2} rr={11:F3}",
                category, m.Definition.Name.Replace(" ", "_"), m.D.Index, Server.Time, m.Score, ageBars, distanceAtr, sh.FeasibleAtSignal, sh.EntryPrice, sh.StopPrice, sh.TargetPrice, sh.TargetR);
        }

        private void Round23CloseShadow(int index, string result, double resultR)
        {
            var sh = _round23Shadows[index];
            bool baselineLater = _consumedSignals.Contains(sh.SignalKey);
            if (baselineLater) _round23BaselineResolved++;
            Print("[R23 SHADOW CLOSE] cat={0} pattern={1} d={2} start={3:yyyy-MM-ddTHH:mm:ss} end={4:yyyy-MM-ddTHH:mm:ss} score={5:F2} age={6} distAtr={7:F3} feasible={8} baselineLater={9} result={10} r={11:F4} mfeR={12:F4} maeR={13:F4} rr={14:F4}",
                sh.Category, sh.Pattern.Replace(" ", "_"), sh.DIndex, sh.StartTime, Server.Time, sh.Score, sh.AgeBars, sh.DistanceAtr,
                sh.FeasibleAtSignal, baselineLater, result, resultR, sh.MfeR, sh.MaeR, sh.TargetR);
            _round23Shadows.RemoveAt(index);
            _round23Completed++;
        }

        private void Round23UpdateShadows()
        {
            if (!Round23NearMissDiagnostics || _round23Shadows.Count == 0 || Bars.Count < 2)
                return;
            int last = Bars.Count - 1;
            double high = Bars.HighPrices[last];
            double low = Bars.LowPrices[last];
            double close = Bars.ClosePrices[last];
            for (int i = _round23Shadows.Count - 1; i >= 0; i--)
            {
                var sh = _round23Shadows[i];
                if (last <= sh.StartBar || sh.RiskDistance <= 0)
                    continue;
                double mfe = (high - sh.EntryPrice) / sh.RiskDistance;
                double mae = (low - sh.EntryPrice) / sh.RiskDistance;
                if (mfe > sh.MfeR) sh.MfeR = mfe;
                if (mae < sh.MaeR) sh.MaeR = mae;
                bool stopHit = low <= sh.StopPrice;
                bool targetHit = high >= sh.TargetPrice;
                if (stopHit && targetHit)
                {
                    Round23CloseShadow(i, "AMBIG_STOP", -1.0);
                    continue;
                }
                if (stopHit)
                {
                    Round23CloseShadow(i, "STOP", -1.0);
                    continue;
                }
                if (targetHit)
                {
                    Round23CloseShadow(i, "TARGET", sh.TargetR);
                    continue;
                }
                if (last - sh.StartBar >= Round23ShadowHorizonBars)
                {
                    double r = (close - sh.EntryPrice) / sh.RiskDistance;
                    Round23CloseShadow(i, "TIMEOUT", r);
                }
            }
        }

        private void Round23FlushShadows()
        {
            if (_round23Shadows.Count == 0 || Bars.Count == 0)
                return;
            double close = Bars.ClosePrices[Bars.Count - 1];
            for (int i = _round23Shadows.Count - 1; i >= 0; i--)
            {
                var sh = _round23Shadows[i];
                double r = sh.RiskDistance > 0 ? (close - sh.EntryPrice) / sh.RiskDistance : 0.0;
                Round23CloseShadow(i, "PARTIAL", r);
            }
        }

        private void Round23QueueNextBarConfirmation(PatternMatch m)
        {
            string key = "PENDING_CONFIRM_NEXT1|" + m.SignalKey;
            if (_round23Seen.Contains(key))
                return;
            _round23Seen.Add(key);
            _round23Pending.Add(new Round23PendingConfirm { Match = m, SourceBar = Bars.Count - 1, SeenKey = key });
            Print("[R23 PENDING] cat=CONFIRM_NEXT1 pattern={0} d={1} time={2:yyyy-MM-ddTHH:mm:ss} score={3:F2}", m.Definition.Name.Replace(" ", "_"), m.D.Index, Server.Time, m.Score);
        }

        private void Round23ProcessPendingConfirmations()
        {
            if (!Round23NearMissDiagnostics || _round23Pending.Count == 0 || Bars.Count < 2)
                return;
            int last = Bars.Count - 1;
            double atr = _atr.Result.LastValue;
            if (atr <= 0) return;
            for (int i = _round23Pending.Count - 1; i >= 0; i--)
            {
                var p = _round23Pending[i];
                if (last <= p.SourceBar)
                    continue;
                if (_consumedSignals.Contains(p.Match.SignalKey) || p.Match.D.Index == _lastBullishDIndex)
                {
                    Print("[R23 PENDING RESOLVED] d={0} baseline=true", p.Match.D.Index);
                    _round23Pending.RemoveAt(i);
                    continue;
                }
                int age = last - p.Match.D.Index;
                double distanceAtr = Math.Abs(Bars.ClosePrices[last] - p.Match.D.Price) / atr;
                p.Match.TrendAligned = IsTrendAligned(TradeType.Buy);
                if (age <= MaxPatternAgeBars && distanceAtr <= MaxEntryDistanceAtr && Round23BaseBuyConfirmation(p.Match, last, atr, true))
                    Round23TryCreateShadow("CONFIRM_NEXT1", p.Match, age, distanceAtr);
                else
                    Print("[R23 PENDING EXPIRE] d={0} age={1} distAtr={2:F3}", p.Match.D.Index, age, distanceAtr);
                _round23Pending.RemoveAt(i);
            }
        }

        private void Round23ScanH1BuyNearMisses()
        {
            if (!Round23NearMissDiagnostics || Bars.Count < Math.Max(100, PivotLeft + PivotRight + 20))
                return;
            var pivots = BuildConfirmedPivots();
            if (pivots.Count < 5)
                return;
            int last = Bars.Count - 1;
            double atr = _atr.Result.LastValue;
            if (atr <= 0)
                return;
            int firstWindow = Math.Max(0, pivots.Count - 20);
            for (int i = firstWindow; i <= pivots.Count - 5; i++)
            {
                var x = pivots[i]; var a = pivots[i + 1]; var b = pivots[i + 2]; var c = pivots[i + 3]; var d = pivots[i + 4];
                TradeType? direction = GetDirection(x, a, b, c, d);
                if (!direction.HasValue || direction.Value != TradeType.Buy)
                    continue;
                int age = last - d.Index;
                if (age < 0 || age > Round23MaxExtendedAgeBars)
                    continue;
                if (d.Index == _lastBullishDIndex)
                    continue;
                double xa = Math.Abs(a.Price - x.Price), ab = Math.Abs(b.Price - a.Price), bc = Math.Abs(c.Price - b.Price), cd = Math.Abs(d.Price - c.Price);
                if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0)
                    continue;
                if (MinXaPips > 0 && xa / Symbol.PipSize < MinXaPips)
                    continue;
                double xb = ab / xa, ac = bc / ab, bd = cd / bc, xd = Math.Abs(a.Price - d.Price) / xa, cdAb = cd / ab;
                foreach (var def in _patterns)
                {
                    if (!IsPatternEnabled(def))
                        continue;
                    double score = def.Score(xb, ac, bd, xd, cdAb, RatioTolerancePercent);
                    if (score < Round23ScoreFloor)
                        continue;
                    var m = new PatternMatch(def, TradeType.Buy, x, a, b, c, d, score, xb, ac, bd, xd, cdAb);
                    m.TrendAligned = IsTrendAligned(TradeType.Buy);
                    if ((EmaFilterMode == TrendFilterMode.Strict || EmaFilterMode == TrendFilterMode.ConfirmOnly) && !m.TrendAligned)
                        continue;
                    double distanceAtr = Math.Abs(Bars.ClosePrices[last] - d.Price) / atr;
                    bool baseConfirmIgnoringDistance = Round23BaseBuyConfirmation(m, last, atr, false);

                    if (age <= MaxPatternAgeBars && score >= Round23ScoreFloor && score < MinPatternScore && distanceAtr <= MaxEntryDistanceAtr && baseConfirmIgnoringDistance)
                        Round23TryCreateShadow("SCORE_82_84", m, age, distanceAtr);

                    if (age > MaxPatternAgeBars && age <= Round23MaxExtendedAgeBars && score >= MinPatternScore && distanceAtr <= MaxEntryDistanceAtr && baseConfirmIgnoringDistance)
                        Round23TryCreateShadow("AGE_17_18", m, age, distanceAtr);

                    if (age <= MaxPatternAgeBars && score >= MinPatternScore && distanceAtr > MaxEntryDistanceAtr && distanceAtr <= Round23MaxExtendedDistanceAtr && baseConfirmIgnoringDistance)
                        Round23TryCreateShadow("DIST_1.8_2.0", m, age, distanceAtr);

                    if (age <= MaxPatternAgeBars && score >= MinPatternScore && distanceAtr <= MaxEntryDistanceAtr && !baseConfirmIgnoringDistance)
                        Round23QueueNextBarConfirmation(m);
                }
            }
        }

'''
if method_anchor not in text:
    raise SystemExit('method anchor not found')
text = text.replace(method_anchor, methods + method_anchor, 1)

out.write_text(text)
print('Round23 source sha256:', hashlib.sha256(text.encode()).hexdigest())
