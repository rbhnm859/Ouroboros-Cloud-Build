using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal sealed class PatternMatch
    {
        public PatternMatch(PatternDefinition definition, TradeType direction, PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d,
            double baseScore, double xb, double ac, double bd, double xd, double cdAb)
        {
            Definition = definition;
            Direction = direction;
            X = x;
            A = a;
            B = b;
            C = c;
            D = d;
            BaseScore = baseScore;
            FinalScore = baseScore;
            Xb = xb;
            Ac = ac;
            Bd = bd;
            Xd = xd;
            CdAb = cdAb;
        }

        public PatternDefinition Definition { get; private set; }
        public TradeType Direction { get; private set; }
        public PivotPoint X { get; private set; }
        public PivotPoint A { get; private set; }
        public PivotPoint B { get; private set; }
        public PivotPoint C { get; private set; }
        public PivotPoint D { get; private set; }
        public double BaseScore { get; private set; }
        public double FinalScore { get; set; }
        public double Xb { get; private set; }
        public double Ac { get; private set; }
        public double Bd { get; private set; }
        public double Xd { get; private set; }
        public double CdAb { get; private set; }
        public bool TrendAligned { get; set; }

        public string SignalKey
        {
            get { return Definition.Name + "|" + Direction + "|" + D.Index; }
        }
    }

    internal sealed class PatternDefinition
    {
        public PatternDefinition(string name,
            double xbMin, double xbMax,
            double acMin, double acMax,
            double bdMin, double bdMax,
            double xdMin, double xdMax,
            double cdAbMin = 0.0, double cdAbMax = 0.0)
        {
            Name = name;
            XbMin = xbMin;
            XbMax = xbMax;
            AcMin = acMin;
            AcMax = acMax;
            BdMin = bdMin;
            BdMax = bdMax;
            XdMin = xdMin;
            XdMax = xdMax;
            CdAbMin = cdAbMin;
            CdAbMax = cdAbMax;
        }

        public string Name { get; private set; }
        public double XbMin { get; private set; }
        public double XbMax { get; private set; }
        public double AcMin { get; private set; }
        public double AcMax { get; private set; }
        public double BdMin { get; private set; }
        public double BdMax { get; private set; }
        public double XdMin { get; private set; }
        public double XdMax { get; private set; }
        public double CdAbMin { get; private set; }
        public double CdAbMax { get; private set; }

        public double Score(double xb, double ac, double bd, double xd, double cdAb, double tolerancePercent)
        {
            double sum = 0.0;
            double weight = 0.0;

            AddWeighted(ref sum, ref weight, BandScore(xb, XbMin, XbMax, tolerancePercent), 1.6);
            AddWeighted(ref sum, ref weight, BandScore(ac, AcMin, AcMax, tolerancePercent), 1.0);
            AddWeighted(ref sum, ref weight, BandScore(bd, BdMin, BdMax, tolerancePercent), 1.0);
            AddWeighted(ref sum, ref weight, BandScore(xd, XdMin, XdMax, tolerancePercent), 1.8);

            if (CdAbMin > 0 && CdAbMax > 0)
                AddWeighted(ref sum, ref weight, BandScore(cdAb, CdAbMin, CdAbMax, tolerancePercent), 1.2);

            if (weight <= 0)
                return 0;
            return sum / weight;
        }

        private static void AddWeighted(ref double sum, ref double weight, double score, double w)
        {
            if (score <= 0)
            {
                weight = -1;
                sum = 0;
                return;
            }
            if (weight < 0)
                return;
            sum += score * w;
            weight += w;
        }

        private static double BandScore(double value, double min, double max, double tolerancePercent)
        {
            if (min <= 0 && max <= 0)
                return 100.0;

            if (max < min)
            {
                double tmp = min;
                min = max;
                max = tmp;
            }

            if (Math.Abs(max - min) < 1e-12)
            {
                double target = min;
                double allowed = Math.Max(Math.Abs(target) * tolerancePercent / 100.0, 1e-9);
                double error = Math.Abs(value - target);
                if (error > allowed)
                    return 0;
                return 100.0 - 30.0 * (error / allowed);
            }

            double center = (min + max) * 0.5;
            double halfWidth = Math.Max((max - min) * 0.5, 1e-9);
            if (value >= min && value <= max)
            {
                double edgeFraction = Math.Min(1.0, Math.Abs(value - center) / halfWidth);
                return 100.0 - 15.0 * edgeFraction;
            }

            double boundary = value < min ? min : max;
            double allowedOutside = Math.Max(Math.Abs(boundary) * tolerancePercent / 100.0, 1e-9);
            double outside = Math.Abs(value - boundary);
            if (outside > allowedOutside)
                return 0;

            return 85.0 * (1.0 - outside / allowedOutside);
        }
    }

    internal sealed class HarmonicPatternEngine
    {
        private readonly List<PatternDefinition> _patterns;

        public HarmonicPatternEngine()
        {
            _patterns = CreateCoreLibrary();
        }

        public List<PatternMatch> FindCandidates(IReadOnlyList<PivotPoint> pivots, int barsCount, int maxPatternAgeBars,
            string enabledPatterns, double minPatternScore, double ratioTolerancePercent, int maxWindows)
        {
            var results = new List<PatternMatch>();
            if (pivots == null || pivots.Count < 5)
                return results;

            int start = Math.Max(0, pivots.Count - Math.Max(5, maxWindows + 4));
            for (int i = start; i <= pivots.Count - 5; i++)
            {
                var x = pivots[i];
                var a = pivots[i + 1];
                var b = pivots[i + 2];
                var c = pivots[i + 3];
                var d = pivots[i + 4];

                TradeType? direction = GetDirection(x, a, b, c, d);
                if (!direction.HasValue)
                    continue;

                int age = barsCount - 1 - d.Index;
                if (age < 0 || age > maxPatternAgeBars)
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
                    if (!IsEnabled(def.Name, enabledPatterns))
                        continue;

                    double score = def.Score(xb, ac, bd, xd, cdAb, ratioTolerancePercent);
                    if (score < minPatternScore)
                        continue;

                    results.Add(new PatternMatch(def, direction.Value, x, a, b, c, d, score, xb, ac, bd, xd, cdAb));
                }
            }

            return results;
        }

        private static TradeType? GetDirection(PivotPoint x, PivotPoint a, PivotPoint b, PivotPoint c, PivotPoint d)
        {
            bool bullish = x.Kind == PivotKind.Low && a.Kind == PivotKind.High && b.Kind == PivotKind.Low && c.Kind == PivotKind.High && d.Kind == PivotKind.Low;
            bool bearish = x.Kind == PivotKind.High && a.Kind == PivotKind.Low && b.Kind == PivotKind.High && c.Kind == PivotKind.Low && d.Kind == PivotKind.High;
            if (bullish)
                return TradeType.Buy;
            if (bearish)
                return TradeType.Sell;
            return null;
        }

        private static bool IsEnabled(string name, string selector)
        {
            string s = string.IsNullOrWhiteSpace(selector) ? "CORE" : selector.Trim();
            if (s.Equals("CORE", StringComparison.OrdinalIgnoreCase) || s.Equals("ALL", StringComparison.OrdinalIgnoreCase))
                return true;

            return s.Split(new[] { ',', ';', '|' }, StringSplitOptions.RemoveEmptyEntries)
                .Any(x => x.Trim().Equals(name, StringComparison.OrdinalIgnoreCase));
        }

        private static List<PatternDefinition> CreateCoreLibrary()
        {
            return new List<PatternDefinition>
            {
                new PatternDefinition("Gartley", 0.618, 0.618, 0.382, 0.886, 1.272, 1.618, 0.786, 0.786),
                new PatternDefinition("Bat", 0.382, 0.500, 0.382, 0.886, 1.618, 2.618, 0.886, 0.886),
                new PatternDefinition("Alt Bat", 0.382, 0.382, 0.382, 0.886, 2.000, 3.618, 1.128, 1.128),
                new PatternDefinition("Butterfly", 0.786, 0.786, 0.382, 0.886, 1.618, 2.618, 1.272, 1.618),
                new PatternDefinition("Crab", 0.382, 0.618, 0.382, 0.886, 2.240, 3.618, 1.618, 1.618),
                new PatternDefinition("Deep Crab", 0.886, 0.886, 0.382, 0.886, 2.618, 3.618, 1.618, 1.618),
                new PatternDefinition("Shark", 0.382, 0.618, 1.128, 1.618, 1.618, 2.236, 0.886, 1.128),
                new PatternDefinition("Cypher", 0.382, 0.618, 1.272, 1.414, 1.272, 2.000, 0.786, 0.786)
            };
        }
    }
}
