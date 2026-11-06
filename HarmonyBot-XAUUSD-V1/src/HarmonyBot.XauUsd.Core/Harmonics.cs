using System;
using System.Collections.Generic;
using System.Linq;

namespace HarmonyBot.XauUsd.Core;

public sealed record RatioBand(decimal Minimum, decimal Maximum)
{
    public bool Contains(decimal value) => Minimum > 0 && Minimum <= Maximum
        && value >= Minimum && value <= Maximum;
}

public sealed record HarmonicRatios(decimal Xab, decimal Abc, decimal Bcd, decimal Xad, decimal CdAb)
{
    public static HarmonicRatios Calculate(IReadOnlyList<ConfirmedPivot> p)
    {
        if (p.Count != 5) throw new ArgumentException("Exactly five pivots required");
        decimal xa = Math.Abs(p[1].Price - p[0].Price);
        decimal ab = Math.Abs(p[2].Price - p[1].Price);
        decimal bc = Math.Abs(p[3].Price - p[2].Price);
        decimal cd = Math.Abs(p[4].Price - p[3].Price);
        if (xa == 0 || ab == 0 || bc == 0) throw new ArgumentException("Degenerate geometry");
        return new HarmonicRatios(ab / xa, bc / ab, cd / bc,
            Math.Abs(p[4].Price - p[1].Price) / xa, cd / ab);
    }
}

public enum GeometryMode { Xabcd, AbCd, Specialized }
public sealed record PatternRule(
    PatternFamily Family, GeometryMode Mode, RatioBand Xab,
    RatioBand Abc, RatioBand Bcd, RatioBand Xad, RatioBand CdAb,
    string SourceRevision, bool SourceVerified, bool TradingApproved)
{
    public bool ResearchMatches(HarmonicRatios r) =>
        Mode switch
        {
            GeometryMode.Xabcd => Xab.Contains(r.Xab) && Abc.Contains(r.Abc)
                                  && Bcd.Contains(r.Bcd) && Xad.Contains(r.Xad),
            GeometryMode.AbCd => Abc.Contains(r.Abc) && Bcd.Contains(r.Bcd)
                                 && CdAb.Contains(r.CdAb),
            _ => false // Shark and 5-0 require distinct native pivot grammars.
        };
}

// These are internal V71 research-envelope transcriptions, NOT independently
// authenticated excerpts from Carney's primary books. Fail closed on trading.
public static class PatternCatalog
{
    private const string Provenance = "V71_INTERNAL_RESEARCH_ENVELOPES__PRIMARY_SOURCE_PENDING";
    private static readonly RatioBand Any = new(0.00001m, 100m);

    private static PatternRule Standard(PatternFamily family,
        decimal x1, decimal x2, decimal b1, decimal b2,
        decimal c1, decimal c2, decimal d1, decimal d2) =>
        new(family, GeometryMode.Xabcd, new(x1, x2), new(b1, b2),
            new(c1, c2), new(d1, d2), Any, Provenance, false, false);

    public static IReadOnlyList<PatternRule> ResearchOnly { get; } = new[]
    {
        Standard(PatternFamily.Gartley, .600m,.636m,.382m,.886m,1.130m,1.618m,.770m,.800m),
        Standard(PatternFamily.Bat, .382m,.500m,.382m,.886m,1.618m,2.618m,.875m,.895m),
        Standard(PatternFamily.AlternateBat, .300m,.395m,.382m,.886m,2.000m,3.618m,1.100m,1.160m),
        Standard(PatternFamily.Butterfly, .770m,.800m,.382m,.886m,1.618m,2.618m,1.240m,1.300m),
        Standard(PatternFamily.Crab, .382m,.618m,.382m,.886m,2.240m,3.618m,1.580m,1.660m),
        Standard(PatternFamily.DeepCrab, .875m,.900m,.382m,.886m,2.000m,3.618m,1.580m,1.660m),
        new(PatternFamily.Shark, GeometryMode.Specialized, Any, Any, Any, Any, Any,
            Provenance, false, false),
        new(PatternFamily.FiveZero, GeometryMode.Specialized, Any, Any, Any, Any, Any,
            Provenance, false, false),
        new(PatternFamily.AbCd, GeometryMode.AbCd, Any,
            new(.382m,.886m), new(1.130m,2.618m), Any, new(.800m,1.250m),
            Provenance, false, false),
        new(PatternFamily.AlternateAbCd, GeometryMode.AbCd, Any,
            new(.382m,.886m), new(1.130m,3.618m), Any, new(1.260m,1.640m),
            Provenance, false, false)
    };
}

public sealed record HarmonicObservation(
    string EventId, Side Direction, DateTimeOffset AvailableAtUtc,
    HarmonicRatios Ratios, IReadOnlyList<PatternFamily> ResearchMatches,
    bool ReadyForTrading, string Blocker);

public static class HarmonicAnalyzer
{
    public static HarmonicObservation Analyze(IReadOnlyList<ConfirmedPivot> pivots,
        DateTimeOffset decisionAtUtc, decimal tickSize)
    {
        Contract.Utc(decisionAtUtc, nameof(decisionAtUtc));
        if (pivots.Count != 5) throw new ArgumentException("Five confirmed pivots required");
        for (int i = 0; i < pivots.Count; ++i)
        {
            pivots[i].Validate(decisionAtUtc);
            if (i > 0 && (pivots[i - 1].SourceBarIndex >= pivots[i].SourceBarIndex
                          || pivots[i - 1].Kind == pivots[i].Kind))
                throw new ArgumentException("Non-causal or non-alternating pivot sequence");
        }
        Side direction = pivots[4].Kind == PivotKind.Low ? Side.Buy : Side.Sell;
        var ratios = HarmonicRatios.Calculate(pivots);
        var matches = PatternCatalog.ResearchOnly.Where(p => p.ResearchMatches(ratios))
            .Select(p => p.Family).ToArray();
        return new HarmonicObservation(EventIdentity.Create(direction, pivots[4], tickSize),
            direction, pivots[4].AvailableAtUtc, ratios, matches,
            false, "PRIMARY_RULES_AND_EXECUTION_PARITY_NOT_APPROVED");
    }
}

public sealed record PriceInterval(decimal Low, decimal High)
{
    public static PriceInterval? Intersect(IReadOnlyList<PriceInterval> zones)
    {
        if (zones.Count == 0) return null;
        decimal low = zones.Max(p => p.Low);
        decimal high = zones.Min(p => p.High);
        if (low <= 0 || high < low || zones.Any(z => z.Low <= 0 || z.High < z.Low))
            return null;
        return new PriceInterval(low, high);
    }
}
