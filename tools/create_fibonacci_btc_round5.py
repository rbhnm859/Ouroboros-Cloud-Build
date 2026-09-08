#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.6.0-btc-round4-mtf"
TARGET_VERSION = "Fibonacci-v0.7.0-btc-round5-state-matrix"
SOURCE_FILE = "FibonacciHarmonicSniperUltimate.cs"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def build(repo_root: Path, force: bool = False) -> Path:
    base = repo_root / BASE_VERSION
    target = repo_root / TARGET_VERSION
    if not (base / SOURCE_FILE).is_file():
        raise FileNotFoundError(base / SOURCE_FILE)
    if target.exists():
        if not force:
            raise FileExistsError(target)
        shutil.rmtree(target)
    shutil.copytree(base, target)

    p = target / SOURCE_FILE
    s = p.read_text(encoding="utf-8")

    s = replace_once(s,
        'Print("VERSION v0.6.0-btc-round4-mtf");',
        'Print("VERSION v0.7.0-btc-round5-state-matrix");',
        'version marker')

    # Round4 full-pattern coincidence gate is disabled by default. Round5 owns the hierarchy.
    s = replace_once(s,
        '[Parameter("MTF Mode", DefaultValue = MultiTimeframeMode.RequireAgreement, Group = "BTC Round4 MTF")]',
        '[Parameter("MTF Mode", DefaultValue = MultiTimeframeMode.Off, Group = "BTC Round4 MTF")]',
        'round4 gate default')

    param_anchor = '''        [Parameter("Log Shadow Conflicts", DefaultValue = true, Group = "BTC Round4 MTF")]
        public bool LogShadowConflicts { get; set; }
'''
    param_block = param_anchor + '''
        [Parameter("Round5 Decision Mode", DefaultValue = Round5DecisionMode.MacroVeto, Group = "BTC Round5 State")]
        public Round5DecisionMode Round5Mode { get; set; }

        [Parameter("D1 Patterns", DefaultValue = "Gartley,Bat,Butterfly,Crab,Deep Crab", Group = "BTC Round5 State")]
        public string D1Patterns { get; set; }

        [Parameter("H4 Patterns", DefaultValue = "Gartley,Bat,Crab,Reciprocal ABCD", Group = "BTC Round5 State")]
        public string H4Patterns { get; set; }

        [Parameter("H1 Patterns", DefaultValue = "Reciprocal ABCD", Group = "BTC Round5 State")]
        public string H1Patterns { get; set; }

        [Parameter("M30 Patterns", DefaultValue = "Reciprocal ABCD,ABCD", Group = "BTC Round5 State")]
        public string M30Patterns { get; set; }

        [Parameter("M15 Patterns", DefaultValue = "ABCD,Reciprocal ABCD", Group = "BTC Round5 State")]
        public string M15Patterns { get; set; }

        [Parameter("M5 Patterns", DefaultValue = "ABCD", Group = "BTC Round5 State")]
        public string M5Patterns { get; set; }

        [Parameter("M1 Patterns", DefaultValue = "ABCD", Group = "BTC Round5 State")]
        public string M1Patterns { get; set; }

        [Parameter("Macro Min Score %", DefaultValue = 82.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round5 State")]
        public double MacroStateMinScore { get; set; }

        [Parameter("Direction Min Score %", DefaultValue = 84.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round5 State")]
        public double DirectionStateMinScore { get; set; }

        [Parameter("Confirmation Min Score %", DefaultValue = 80.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round5 State")]
        public double ConfirmationStateMinScore { get; set; }

        [Parameter("Timing Min Score %", DefaultValue = 78.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round5 State")]
        public double TimingStateMinScore { get; set; }

        [Parameter("State Ratio Tolerance %", DefaultValue = 8.0, MinValue = 0.0, MaxValue = 25.0, Group = "BTC Round5 State")]
        public double StateRatioTolerancePercent { get; set; }

        [Parameter("State Pivot Left", DefaultValue = 2, MinValue = 2, MaxValue = 20, Group = "BTC Round5 State")]
        public int StatePivotLeft { get; set; }

        [Parameter("State Pivot Right", DefaultValue = 2, MinValue = 2, MaxValue = 20, Group = "BTC Round5 State")]
        public int StatePivotRight { get; set; }

        [Parameter("State Pivot Lookback", DefaultValue = 300, MinValue = 100, MaxValue = 2000, Group = "BTC Round5 State")]
        public int StatePivotLookback { get; set; }

        [Parameter("D1 Max Age Bars", DefaultValue = 5, MinValue = 1, MaxValue = 50, Group = "BTC Round5 State")]
        public int D1StateMaxAge { get; set; }

        [Parameter("H4 Max Age Bars", DefaultValue = 8, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int H4StateMaxAge { get; set; }

        [Parameter("H1 Max Age Bars", DefaultValue = 16, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int H1StateMaxAge { get; set; }

        [Parameter("M30 Max Age Bars", DefaultValue = 12, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int M30StateMaxAge { get; set; }

        [Parameter("M15 Max Age Bars", DefaultValue = 10, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int M15StateMaxAge { get; set; }

        [Parameter("M5 Max Age Bars", DefaultValue = 8, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int M5StateMaxAge { get; set; }

        [Parameter("M1 Max Age Bars", DefaultValue = 6, MinValue = 1, MaxValue = 100, Group = "BTC Round5 State")]
        public int M1StateMaxAge { get; set; }

        [Parameter("State Age Decay %", DefaultValue = 50.0, MinValue = 0.0, MaxValue = 100.0, Group = "BTC Round5 State")]
        public double StateAgeDecayPercent { get; set; }

        [Parameter("Macro Weight D1", DefaultValue = 4.0, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double D1Weight { get; set; }

        [Parameter("Macro Weight H4", DefaultValue = 3.0, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double H4Weight { get; set; }

        [Parameter("Direction Weight H1", DefaultValue = 2.5, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double H1Weight { get; set; }

        [Parameter("Direction Weight M30", DefaultValue = 2.0, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double M30Weight { get; set; }

        [Parameter("Confirmation Weight M15", DefaultValue = 1.0, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double M15Weight { get; set; }

        [Parameter("Confirmation Weight M5", DefaultValue = 0.5, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double M5Weight { get; set; }

        [Parameter("Timing Weight M1", DefaultValue = 0.25, MinValue = 0.0, MaxValue = 20.0, Group = "BTC Round5 State")]
        public double M1Weight { get; set; }

        [Parameter("Weighted Gate Threshold", DefaultValue = 0.35, MinValue = 0.0, MaxValue = 1.0, Group = "BTC Round5 State")]
        public double WeightedGateThreshold { get; set; }

        [Parameter("Log Pattern Matrix", DefaultValue = true, Group = "BTC Round5 State")]
        public bool LogPatternMatrix { get; set; }
'''
    s = replace_once(s, param_anchor, param_block, 'round5 parameters')

    fields_anchor = '''        private int _mtfParentChildCount;
'''
    fields_block = '''        private int _mtfParentChildCount;
        private List<PatternDefinition> _allPatterns;
        private Bars _barsD1;
        private Bars _barsH4;
        private Bars _barsH1;
        private Bars _barsM30;
        private Bars _barsM15;
        private Bars _barsM5;
        private Bars _barsM1;
        private readonly Dictionary<string, string> _round5LastMatrixKey = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        private int _round5MacroVetoCount;
        private int _round5WeightedRejectCount;
        private int _round5AcceptedCount;
        private int _round5ShadowCount;
'''
    s = replace_once(s, fields_anchor, fields_block, 'round5 fields')

    start_anchor = '''            _higherBars = MarketData.GetBars(HigherTimeFrame);
            _patterns = PatternLibrary.Create();
'''
    start_block = '''            _higherBars = MarketData.GetBars(HigherTimeFrame);
            _allPatterns = PatternLibrary.Create();
            _barsD1 = MarketData.GetBars(TimeFrame.Daily);
            _barsH4 = MarketData.GetBars(TimeFrame.Hour4);
            _barsH1 = MarketData.GetBars(TimeFrame.Hour);
            _barsM30 = MarketData.GetBars(TimeFrame.Minute30);
            _barsM15 = MarketData.GetBars(TimeFrame.Minute15);
            _barsM5 = MarketData.GetBars(TimeFrame.Minute5);
            _barsM1 = MarketData.GetBars(TimeFrame.Minute);
            _patterns = PatternLibrary.Create();
'''
    s = replace_once(s, start_anchor, start_block, 'round5 bars init')

    startup_anchor = '''            Print("BTC Round4 MTF | Mode={0} | ExecutionTF={1} | HigherTF={2} | HTFPatterns={3}", MtfMode, TimeFrame, HigherTimeFrame, HigherEnabledPatterns);
'''
    startup_block = startup_anchor + '''            Print("BTC Round5 State Matrix | Mode={0} | D1={1} | H4={2} | H1={3} | M30={4} | M15={5} | M5={6} | M1={7}",
                Round5Mode, D1Patterns, H4Patterns, H1Patterns, M30Patterns, M15Patterns, M5Patterns, M1Patterns);
'''
    s = replace_once(s, startup_anchor, startup_block, 'round5 startup')

    gate_anchor = '''            if (MtfMode != MultiTimeframeMode.Off)
            {
                higherBias = FindHigherTimeframeBias();
                if (!PassMultiTimeframeGate(best, higherBias))
                    return;
            }

            if (DebugLogging)
'''
    gate_block = '''            if (MtfMode != MultiTimeframeMode.Off)
            {
                higherBias = FindHigherTimeframeBias();
                if (!PassMultiTimeframeGate(best, higherBias))
                    return;
            }

            Round5Snapshot round5 = BuildRound5Snapshot();
            LogRound5Matrix(round5);
            if (!PassRound5HierarchyGate(best, round5))
                return;

            if (DebugLogging)
'''
    s = replace_once(s, gate_anchor, gate_block, 'round5 execution gate')

    stop_anchor = '''            Print("[MTF STATS] agreement={0} conflict={1} noBias={2} parentChild={3}", _mtfAgreementCount, _mtfConflictCount, _mtfNoBiasCount, _mtfParentChildCount);
'''
    stop_block = stop_anchor + '''            Print("[ROUND5 STATS] accepted={0} macroVeto={1} weightedReject={2} shadow={3}", _round5AcceptedCount, _round5MacroVetoCount, _round5WeightedRejectCount, _round5ShadowCount);
'''
    s = replace_once(s, stop_anchor, stop_block, 'round5 stop stats')

    method_anchor = '''        private MtfBiasSignal FindHigherTimeframeBias()
'''
    method_block = r'''        private Round5Snapshot BuildRound5Snapshot()
        {
            return new Round5Snapshot
            {
                D1 = FindRound5State("D1", _barsD1, D1Patterns, MacroStateMinScore, D1StateMaxAge),
                H4 = FindRound5State("H4", _barsH4, H4Patterns, MacroStateMinScore, H4StateMaxAge),
                H1 = FindRound5State("H1", _barsH1, H1Patterns, DirectionStateMinScore, H1StateMaxAge),
                M30 = FindRound5State("M30", _barsM30, M30Patterns, DirectionStateMinScore, M30StateMaxAge),
                M15 = FindRound5State("M15", _barsM15, M15Patterns, ConfirmationStateMinScore, M15StateMaxAge),
                M5 = FindRound5State("M5", _barsM5, M5Patterns, ConfirmationStateMinScore, M5StateMaxAge),
                M1 = FindRound5State("M1", _barsM1, M1Patterns, TimingStateMinScore, M1StateMaxAge)
            };
        }

        private Round5FrameState FindRound5State(string tfName, Bars sourceBars, string selector, double minScore, int maxAge)
        {
            if (sourceBars == null || _allPatterns == null || sourceBars.Count < Math.Max(100, StatePivotLeft + StatePivotRight + 20))
                return null;

            var pivots = BuildConfirmedPivots(sourceBars, StatePivotLeft, StatePivotRight, StatePivotLookback);
            if (pivots.Count < 5)
                return null;

            Round5FrameState best = null;
            int firstWindow = Math.Max(0, pivots.Count - 24);
            for (int i = firstWindow; i <= pivots.Count - 5; i++)
            {
                var x = pivots[i];
                var a = pivots[i + 1];
                var b = pivots[i + 2];
                var c = pivots[i + 3];
                var d = pivots[i + 4];
                TradeType? direction = GetDirection(x, a, b, c, d);
                if (!direction.HasValue)
                    continue;

                int age = sourceBars.Count - 1 - d.Index;
                if (age < 0 || age > maxAge)
                    continue;

                double xa = Math.Abs(a.Price - x.Price);
                double ab = Math.Abs(b.Price - a.Price);
                double bc = Math.Abs(c.Price - b.Price);
                double cd = Math.Abs(d.Price - c.Price);
                if (xa <= 0 || ab <= 0 || bc <= 0 || cd <= 0)
                    continue;

                double xb = ab / xa;
                double ac = bc / ab;
                double bd = cd / bc;
                double xd = Math.Abs(a.Price - d.Price) / xa;
                double cdAb = cd / ab;

                foreach (var def in _allPatterns)
                {
                    if (!IsPatternSelected(def, selector))
                        continue;
                    double score = def.Score(xb, ac, bd, xd, cdAb, StateRatioTolerancePercent);
                    if (score < minScore)
                        continue;

                    double close = sourceBars.ClosePrices[sourceBars.Count - 1];
                    double invalidation = direction.Value == TradeType.Buy
                        ? Math.Min(x.Price, d.Price)
                        : Math.Max(x.Price, d.Price);
                    bool invalidated = direction.Value == TradeType.Buy ? close <= invalidation : close >= invalidation;
                    if (invalidated)
                        continue;

                    double ageFraction = maxAge <= 0 ? 0.0 : Math.Min(1.0, (double)age / maxAge);
                    double decay = 1.0 - ageFraction * StateAgeDecayPercent / 100.0;
                    double confidence = Math.Max(0.0, score / 100.0 * decay);
                    var state = new Round5FrameState(tfName, def.Name, direction.Value, score, confidence, age, d.Index, invalidation);
                    if (best == null || state.DIndex > best.DIndex || (state.DIndex == best.DIndex && state.Confidence > best.Confidence))
                        best = state;
                }
            }
            return best;
        }

        private bool PassRound5HierarchyGate(PatternMatch lower, Round5Snapshot snapshot)
        {
            if (Round5Mode == Round5DecisionMode.ObserveOnly || snapshot == null)
            {
                _round5AcceptedCount++;
                return true;
            }

            // Hierarchical macro veto: only a clear D1+H4 agreement against the H1 setup can veto.
            bool macroOpposes = snapshot.D1 != null && snapshot.H4 != null
                && snapshot.D1.Direction == snapshot.H4.Direction
                && snapshot.D1.Direction != lower.Direction;
            if (macroOpposes)
            {
                _round5MacroVetoCount++;
                _round5ShadowCount++;
                if (LogShadowConflicts)
                    Print("[R5 SHADOW] macro veto | D1={0}/{1} H4={2}/{3} lower={4} {5}",
                        snapshot.D1.PatternName, snapshot.D1.Direction, snapshot.H4.PatternName, snapshot.H4.Direction,
                        lower.Definition.Name, lower.Direction);
                return Reject("round5_macro_veto");
            }

            double signed = 0.0;
            double total = 0.0;
            AddRound5Weighted(snapshot.D1, D1Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.H4, H4Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.H1, H1Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.M30, M30Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.M15, M15Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.M5, M5Weight, lower.Direction, ref signed, ref total);
            AddRound5Weighted(snapshot.M1, M1Weight, lower.Direction, ref signed, ref total);
            double normalized = total <= 0 ? 0.0 : signed / total;

            if (DebugLogging)
                Print("[R5 SNAPSHOT] lower={0} {1} composite={2:F3} D1={3} H4={4} H1={5} M30={6} M15={7} M5={8} M1={9}",
                    lower.Definition.Name, lower.Direction, normalized,
                    DescribeRound5(snapshot.D1), DescribeRound5(snapshot.H4), DescribeRound5(snapshot.H1), DescribeRound5(snapshot.M30),
                    DescribeRound5(snapshot.M15), DescribeRound5(snapshot.M5), DescribeRound5(snapshot.M1));

            if (Round5Mode == Round5DecisionMode.WeightedGate && normalized < WeightedGateThreshold)
            {
                _round5WeightedRejectCount++;
                _round5ShadowCount++;
                return Reject("round5_weighted_gate");
            }

            _round5AcceptedCount++;
            return true;
        }

        private void AddRound5Weighted(Round5FrameState state, double weight, TradeType desired, ref double signed, ref double total)
        {
            if (state == null || weight <= 0)
                return;
            double value = weight * state.Confidence;
            total += value;
            signed += state.Direction == desired ? value : -value;
        }

        private string DescribeRound5(Round5FrameState state)
        {
            if (state == null)
                return "Neutral";
            return state.PatternName + "/" + state.Direction + "/" + state.Confidence.ToString("F2");
        }

        private void LogRound5Matrix(Round5Snapshot snapshot)
        {
            if (!LogPatternMatrix || snapshot == null)
                return;
            LogRound5State(snapshot.D1);
            LogRound5State(snapshot.H4);
            LogRound5State(snapshot.H1);
            LogRound5State(snapshot.M30);
            LogRound5State(snapshot.M15);
            LogRound5State(snapshot.M5);
            LogRound5State(snapshot.M1);
        }

        private void LogRound5State(Round5FrameState state)
        {
            if (state == null)
                return;
            string key = state.PatternName + "|" + state.Direction + "|" + state.DIndex;
            string previous;
            if (_round5LastMatrixKey.TryGetValue(state.TimeFrameName, out previous) && previous == key)
                return;
            _round5LastMatrixKey[state.TimeFrameName] = key;
            Print("[R5 MATRIX] tf={0} pattern={1} dir={2} score={3:F1} confidence={4:F3} age={5} invalidation={6}",
                state.TimeFrameName, state.PatternName, state.Direction, state.Score, state.Confidence, state.AgeBars, state.InvalidationPrice);
        }

        private MtfBiasSignal FindHigherTimeframeBias()
'''
    s = replace_once(s, method_anchor, method_block, 'round5 methods')

    enum_anchor = '''        public enum MultiTimeframeMode
        {
'''
    enum_block = '''        public enum Round5DecisionMode
        {
            ObserveOnly,
            MacroVeto,
            WeightedGate
        }

        public enum MultiTimeframeMode
        {
'''
    s = replace_once(s, enum_anchor, enum_block, 'round5 enum')

    class_anchor = '''        private sealed class MtfBiasSignal
        {
'''
    class_block = '''        private sealed class Round5Snapshot
        {
            public Round5FrameState D1;
            public Round5FrameState H4;
            public Round5FrameState H1;
            public Round5FrameState M30;
            public Round5FrameState M15;
            public Round5FrameState M5;
            public Round5FrameState M1;
        }

        private sealed class Round5FrameState
        {
            public Round5FrameState(string timeFrameName, string patternName, TradeType direction, double score, double confidence, int ageBars, int dIndex, double invalidationPrice)
            {
                TimeFrameName = timeFrameName;
                PatternName = patternName;
                Direction = direction;
                Score = score;
                Confidence = confidence;
                AgeBars = ageBars;
                DIndex = dIndex;
                InvalidationPrice = invalidationPrice;
            }
            public string TimeFrameName { get; private set; }
            public string PatternName { get; private set; }
            public TradeType Direction { get; private set; }
            public double Score { get; private set; }
            public double Confidence { get; private set; }
            public int AgeBars { get; private set; }
            public int DIndex { get; private set; }
            public double InvalidationPrice { get; private set; }
        }

        private sealed class MtfBiasSignal
        {
'''
    s = replace_once(s, class_anchor, class_block, 'round5 state classes')

    p.write_text(s, encoding="utf-8")

    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.6.0-btc-round4-mtf</Version>', '<Version>0.7.0-btc-round5-state-matrix</Version>')
        csproj.write_text(text, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', type=Path, default=Path.cwd())
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    print(build(a.repo_root.resolve(), a.force))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
