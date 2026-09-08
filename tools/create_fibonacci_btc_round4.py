#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_VERSION = "Fibonacci-v0.4.0-research1"
TARGET_VERSION = "Fibonacci-v0.6.0-btc-round4-mtf"
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

    # Version + frozen BTC Growth Champion defaults.
    s = replace_once(s, 'Print("VERSION v0.4.0-research1");', 'Print("VERSION v0.6.0-btc-round4-mtf");', 'version')
    s = replace_once(s, '[Parameter("Enabled Patterns", DefaultValue = "CORE", Group = "Patterns")]', '[Parameter("Enabled Patterns", DefaultValue = "Reciprocal ABCD", Group = "Patterns")]', 'pattern default')
    s = replace_once(s, '[Parameter("Min Pattern Score %", DefaultValue = 85.0, MinValue = 50.0, MaxValue = 100.0, Group = "Patterns")]', '[Parameter("Min Pattern Score %", DefaultValue = 84.0, MinValue = 50.0, MaxValue = 100.0, Group = "Patterns")]', 'score default')
    s = replace_once(s, '[Parameter("Pivot Left Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]', '[Parameter("Pivot Left Bars", DefaultValue = 2, MinValue = 2, MaxValue = 30, Group = "Pivots")]', 'pivot left default')
    s = replace_once(s, '[Parameter("Pivot Right Bars", DefaultValue = 4, MinValue = 2, MaxValue = 30, Group = "Pivots")]', '[Parameter("Pivot Right Bars", DefaultValue = 2, MinValue = 2, MaxValue = 30, Group = "Pivots")]', 'pivot right default')
    s = replace_once(s, '[Parameter("Max Pattern Age Bars", DefaultValue = 12, MinValue = 1, MaxValue = 100, Group = "Pivots")]', '[Parameter("Max Pattern Age Bars", DefaultValue = 16, MinValue = 1, MaxValue = 100, Group = "Pivots")]', 'age default')
    s = replace_once(s, '[Parameter("Confirmation Move ATR", DefaultValue = 0.10, MinValue = 0.0, MaxValue = 2.0, Group = "Confirmation")]', '[Parameter("Confirmation Move ATR", DefaultValue = 0.05, MinValue = 0.0, MaxValue = 2.0, Group = "Confirmation")]', 'confirmation default')
    s = replace_once(s, '[Parameter("Max Entry Distance ATR", DefaultValue = 1.50, MinValue = 0.1, MaxValue = 10.0, Group = "Confirmation")]', '[Parameter("Max Entry Distance ATR", DefaultValue = 1.80, MinValue = 0.1, MaxValue = 10.0, Group = "Confirmation")]', 'entry distance default')
    s = replace_once(s, '[Parameter("Cooldown Bars", DefaultValue = 3, MinValue = 0, MaxValue = 500, Group = "Limits")]', '[Parameter("Cooldown Bars", DefaultValue = 2, MinValue = 0, MaxValue = 500, Group = "Limits")]', 'cooldown default')
    s = replace_once(s, '[Parameter("Stop Anchor Mode", DefaultValue = StopAnchorModeKind.PatternInvalidation, Group = "Risk")]', '[Parameter("Stop Anchor Mode", DefaultValue = StopAnchorModeKind.LegacyD, Group = "Risk")]', 'stop mode default')
    s = replace_once(s, '[Parameter("Target RR Policy", DefaultValue = TargetRiskRewardPolicyKind.RejectPoorGeometry, Group = "Risk")]', '[Parameter("Target RR Policy", DefaultValue = TargetRiskRewardPolicyKind.LegacyFallback, Group = "Risk")]', 'target policy default')

    # Multi-timeframe parameters. The same .algo supports H4+H1 by running on H1
    # with HigherTimeFrame=Hour4, and H1+M30 by running on M30 with HigherTimeFrame=Hour.
    anchor = '''        [Parameter("Ratio Tolerance %", DefaultValue = 6.0, MinValue = 0.0, MaxValue = 25.0, Group = "Patterns")]
        public double RatioTolerancePercent { get; set; }
'''
    block = anchor + '''
        [Parameter("MTF Mode", DefaultValue = MultiTimeframeMode.RequireAgreement, Group = "BTC Round4 MTF")]
        public MultiTimeframeMode MtfMode { get; set; }

        [Parameter("Higher TimeFrame", DefaultValue = "Hour4", Group = "BTC Round4 MTF")]
        public TimeFrame HigherTimeFrame { get; set; }

        [Parameter("HTF Patterns", DefaultValue = "Reciprocal ABCD", Group = "BTC Round4 MTF")]
        public string HigherEnabledPatterns { get; set; }

        [Parameter("HTF Min Pattern Score %", DefaultValue = 84.0, MinValue = 50.0, MaxValue = 100.0, Group = "BTC Round4 MTF")]
        public double HigherMinPatternScore { get; set; }

        [Parameter("HTF Ratio Tolerance %", DefaultValue = 6.0, MinValue = 0.0, MaxValue = 25.0, Group = "BTC Round4 MTF")]
        public double HigherRatioTolerancePercent { get; set; }

        [Parameter("HTF Pivot Left", DefaultValue = 2, MinValue = 2, MaxValue = 30, Group = "BTC Round4 MTF")]
        public int HigherPivotLeft { get; set; }

        [Parameter("HTF Pivot Right", DefaultValue = 2, MinValue = 2, MaxValue = 30, Group = "BTC Round4 MTF")]
        public int HigherPivotRight { get; set; }

        [Parameter("HTF Pivot Lookback", DefaultValue = 500, MinValue = 100, MaxValue = 5000, Group = "BTC Round4 MTF")]
        public int HigherPivotLookback { get; set; }

        [Parameter("HTF Max Pattern Age Bars", DefaultValue = 6, MinValue = 1, MaxValue = 100, Group = "BTC Round4 MTF")]
        public int HigherMaxPatternAgeBars { get; set; }

        [Parameter("Parent/Child Max Hours", DefaultValue = 12.0, MinValue = 0.0, MaxValue = 168.0, Group = "BTC Round4 MTF")]
        public double ParentChildMaxHours { get; set; }

        [Parameter("Log Shadow Conflicts", DefaultValue = true, Group = "BTC Round4 MTF")]
        public bool LogShadowConflicts { get; set; }
'''
    s = replace_once(s, anchor, block, 'mtf parameters')

    fields_anchor = '''        private AverageTrueRange _atr;
        private ExponentialMovingAverage _ema;
'''
    fields_block = '''        private AverageTrueRange _atr;
        private ExponentialMovingAverage _ema;
        private Bars _higherBars;
        private int _mtfAgreementCount;
        private int _mtfConflictCount;
        private int _mtfNoBiasCount;
        private int _mtfParentChildCount;
'''
    s = replace_once(s, fields_anchor, fields_block, 'mtf fields')

    start_anchor = '''            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);
            _patterns = PatternLibrary.Create();
'''
    start_block = '''            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);
            _ema = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaPeriod);
            _higherBars = MarketData.GetBars(HigherTimeFrame);
            _patterns = PatternLibrary.Create();
'''
    s = replace_once(s, start_anchor, start_block, 'higher bars init')

    print_anchor = '''            Print("FHSU started | Symbol={0} | TimeFrame={1} | Patterns={2} | Trading={3}", SymbolName, TimeFrame, _patterns.Count, TradingEnabled);
            Print("Pattern selector: CORE = canonical set, ALL = entire database, or comma separated names.");
'''
    print_block = '''            Print("FHSU started | Symbol={0} | TimeFrame={1} | Patterns={2} | Trading={3}", SymbolName, TimeFrame, _patterns.Count, TradingEnabled);
            Print("Pattern selector: CORE = canonical set, ALL = entire database, or comma separated names.");
            Print("BTC Round4 MTF | Mode={0} | ExecutionTF={1} | HigherTF={2} | HTFPatterns={3}", MtfMode, TimeFrame, HigherTimeFrame, HigherEnabledPatterns);
'''
    s = replace_once(s, print_anchor, print_block, 'mtf startup print')

    gate_anchor = '''            if (best == null)
            {
                Reject("no_candidate_or_conflict");
                return;
            }


            if (DebugLogging)
'''
    gate_block = '''            if (best == null)
            {
                Reject("no_candidate_or_conflict");
                return;
            }

            MtfBiasSignal higherBias = null;
            if (MtfMode != MultiTimeframeMode.Off)
            {
                higherBias = FindHigherTimeframeBias();
                if (!PassMultiTimeframeGate(best, higherBias))
                    return;
            }

            if (DebugLogging)
'''
    s = replace_once(s, gate_anchor, gate_block, 'mtf execution gate')

    stop_anchor = '''        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            foreach (var item in _diagnostics) Print("[DIAG] {0}={1}", item.Key, item.Value);
'''
    stop_block = '''        protected override void OnStop()
        {
            Positions.Closed -= OnPositionClosed;
            Print("[MTF STATS] agreement={0} conflict={1} noBias={2} parentChild={3}", _mtfAgreementCount, _mtfConflictCount, _mtfNoBiasCount, _mtfParentChildCount);
            foreach (var item in _diagnostics) Print("[DIAG] {0}={1}", item.Key, item.Value);
'''
    s = replace_once(s, stop_anchor, stop_block, 'mtf stop stats')

    build_anchor = '''        private List<PivotPoint> BuildConfirmedPivots()
        {
            var pivots = new List<PivotPoint>();
            int latestConfirmed = Bars.Count - 1 - PivotRight;
            int first = Math.Max(PivotLeft, Bars.Count - PivotLookback);

            for (int i = first; i <= latestConfirmed; i++)
            {
                bool isHigh = true;
                bool isLow = true;

                for (int j = 1; j <= PivotLeft; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i - j]) isHigh = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i - j]) isLow = false;
                }
                for (int j = 1; j <= PivotRight; j++)
                {
                    if (Bars.HighPrices[i] <= Bars.HighPrices[i + j]) isHigh = false;
                    if (Bars.LowPrices[i] >= Bars.LowPrices[i + j]) isLow = false;
                }

                if (isHigh && !isLow)
                    AddAlternatingPivot(pivots, new PivotPoint(i, Bars.HighPrices[i], PivotKind.High));
                else if (isLow && !isHigh)
                    AddAlternatingPivot(pivots, new PivotPoint(i, Bars.LowPrices[i], PivotKind.Low));
            }

            const int maxPivots = 80;
            if (pivots.Count > maxPivots)
                pivots = pivots.GetRange(pivots.Count - maxPivots, maxPivots);
            return pivots;
        }
'''
    build_block = '''        private List<PivotPoint> BuildConfirmedPivots()
        {
            return BuildConfirmedPivots(Bars, PivotLeft, PivotRight, PivotLookback);
        }

        private List<PivotPoint> BuildConfirmedPivots(Bars sourceBars, int left, int right, int lookback)
        {
            var pivots = new List<PivotPoint>();
            int latestConfirmed = sourceBars.Count - 1 - right;
            int first = Math.Max(left, sourceBars.Count - lookback);

            for (int i = first; i <= latestConfirmed; i++)
            {
                bool isHigh = true;
                bool isLow = true;

                for (int j = 1; j <= left; j++)
                {
                    if (sourceBars.HighPrices[i] <= sourceBars.HighPrices[i - j]) isHigh = false;
                    if (sourceBars.LowPrices[i] >= sourceBars.LowPrices[i - j]) isLow = false;
                }
                for (int j = 1; j <= right; j++)
                {
                    if (sourceBars.HighPrices[i] <= sourceBars.HighPrices[i + j]) isHigh = false;
                    if (sourceBars.LowPrices[i] >= sourceBars.LowPrices[i + j]) isLow = false;
                }

                if (isHigh && !isLow)
                    AddAlternatingPivot(pivots, new PivotPoint(i, sourceBars.HighPrices[i], PivotKind.High));
                else if (isLow && !isHigh)
                    AddAlternatingPivot(pivots, new PivotPoint(i, sourceBars.LowPrices[i], PivotKind.Low));
            }

            const int maxPivots = 80;
            if (pivots.Count > maxPivots)
                pivots = pivots.GetRange(pivots.Count - maxPivots, maxPivots);
            return pivots;
        }
'''
    s = replace_once(s, build_anchor, build_block, 'generic pivot builder')

    # Insert the higher-timeframe detector and gate immediately before current-TF FindBestPattern.
    find_anchor = '''        private PatternMatch FindBestPattern(List<PivotPoint> pivots)
        {
'''
    find_block = '''        private MtfBiasSignal FindHigherTimeframeBias()
        {
            if (_higherBars == null || _higherBars.Count < Math.Max(100, HigherPivotLeft + HigherPivotRight + 20))
                return null;

            var pivots = BuildConfirmedPivots(_higherBars, HigherPivotLeft, HigherPivotRight, HigherPivotLookback);
            if (pivots.Count < 5)
                return null;

            var candidates = new List<MtfBiasSignal>();
            int firstWindow = Math.Max(0, pivots.Count - 20);
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

                int age = _higherBars.Count - 1 - d.Index;
                if (age < 0 || age > HigherMaxPatternAgeBars)
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

                foreach (var def in _patterns)
                {
                    if (!IsPatternSelected(def, HigherEnabledPatterns))
                        continue;
                    double score = def.Score(xb, ac, bd, xd, cdAb, HigherRatioTolerancePercent);
                    if (score < HigherMinPatternScore)
                        continue;
                    candidates.Add(new MtfBiasSignal(def.Name, direction.Value, d.Index, score));
                }
            }

            if (candidates.Count == 0)
                return null;

            return candidates.OrderByDescending(x => x.DIndex).ThenByDescending(x => x.Score).First();
        }

        private bool PassMultiTimeframeGate(PatternMatch lower, MtfBiasSignal higher)
        {
            bool directionNeedsAgreement = MtfMode == MultiTimeframeMode.RequireAgreement
                || (MtfMode == MultiTimeframeMode.SellRequiresAgreement && lower.Direction == TradeType.Sell)
                || (MtfMode == MultiTimeframeMode.BuyRequiresAgreement && lower.Direction == TradeType.Buy);

            if (higher == null)
            {
                _mtfNoBiasCount++;
                if (LogShadowConflicts)
                    Print("[MTF SHADOW] no HTF bias | lower={0} {1} score={2:F1}", lower.Definition.Name, lower.Direction, lower.Score);
                return !directionNeedsAgreement || MtfMode == MultiTimeframeMode.ScoreOnly || MtfMode == MultiTimeframeMode.Off
                    ? true : Reject("mtf_no_bias");
            }

            bool agrees = higher.Direction == lower.Direction;
            if (!agrees)
            {
                _mtfConflictCount++;
                if (LogShadowConflicts)
                    Print("[MTF SHADOW] conflict | HTF={0} {1} {2:F1}% | LTF={3} {4} {5:F1}%",
                        higher.PatternName, higher.Direction, higher.Score, lower.Definition.Name, lower.Direction, lower.Score);
                return !directionNeedsAgreement || MtfMode == MultiTimeframeMode.ScoreOnly || MtfMode == MultiTimeframeMode.Off
                    ? true : Reject("mtf_direction_conflict");
            }

            _mtfAgreementCount++;
            DateTime lowerDTime = Bars.OpenTimes[lower.D.Index];
            DateTime higherDTime = _higherBars.OpenTimes[higher.DIndex];
            bool parentChild = ParentChildMaxHours > 0 && Math.Abs((lowerDTime - higherDTime).TotalHours) <= ParentChildMaxHours;
            if (parentChild)
            {
                _mtfParentChildCount++;
                if (DebugLogging)
                    Print("[MTF PARENT_CHILD] HTF={0} {1} D={2:u} | LTF={3} D={4:u}", higher.PatternName, higher.Direction, higherDTime, lower.Definition.Name, lowerDTime);
            }
            if (DebugLogging)
                Print("[MTF AGREE] HTF={0} {1} {2:F1}% | LTF={3} {4} {5:F1}%",
                    higher.PatternName, higher.Direction, higher.Score, lower.Definition.Name, lower.Direction, lower.Score);
            return true;
        }

        private bool IsPatternSelected(PatternDefinition def, string selectorText)
        {
            string selector = (selectorText ?? "CORE").Trim();
            if (selector.Equals("ALL", StringComparison.OrdinalIgnoreCase))
                return true;
            if (selector.Equals("CORE", StringComparison.OrdinalIgnoreCase))
                return def.IsCore;
            string[] parts = selector.Split(new[] { ',', ';', '|' }, StringSplitOptions.RemoveEmptyEntries);
            foreach (string part in parts)
                if (part.Trim().Equals(def.Name, StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }

        private PatternMatch FindBestPattern(List<PivotPoint> pivots)
        {
'''
    s = replace_once(s, find_anchor, find_block, 'mtf methods')

    enum_anchor = '''        public enum RiskSizingMode
        {
'''
    enum_block = '''        public enum MultiTimeframeMode
        {
            Off,
            RequireAgreement,
            SellRequiresAgreement,
            BuyRequiresAgreement,
            ScoreOnly
        }

        public enum RiskSizingMode
        {
'''
    s = replace_once(s, enum_anchor, enum_block, 'mtf enum')

    class_anchor = '''        private sealed class PatternMatch
        {
'''
    class_block = '''        private sealed class MtfBiasSignal
        {
            public MtfBiasSignal(string patternName, TradeType direction, int dIndex, double score)
            {
                PatternName = patternName;
                Direction = direction;
                DIndex = dIndex;
                Score = score;
            }
            public string PatternName { get; private set; }
            public TradeType Direction { get; private set; }
            public int DIndex { get; private set; }
            public double Score { get; private set; }
        }

        private sealed class PatternMatch
        {
'''
    s = replace_once(s, class_anchor, class_block, 'mtf signal class')

    p.write_text(s, encoding="utf-8")

    # Stamp project version too.
    csproj = target / "FibonacciHarmonicSniperUltimate.csproj"
    if csproj.is_file():
        text = csproj.read_text(encoding="utf-8")
        text = text.replace('<Version>0.3.0-fix3</Version>', '<Version>0.6.0-btc-round4-mtf</Version>')
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
