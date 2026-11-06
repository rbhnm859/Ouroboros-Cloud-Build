using System;
using System.Collections.Generic;
using System.Linq;

namespace HarmonyBot.XauUsd.Core;

/// <summary>
/// Historical research envelopes only. Projection from X/A/B/C does not
/// authenticate source ratios, prove fills, or authorize a trading signal.
/// A D price must NEVER enter the projection API.
/// </summary>
public sealed record ResearchPrzProjection(
    PatternFamily Family, Side Direction, PriceInterval TickAlignedZone,
    DateTimeOffset AvailableAtUtc, bool SourceVerified);

public static class CausalPrzProjector
{
    public static IReadOnlyList<ResearchPrzProjection> Project(
        IReadOnlyList<ConfirmedPivot> xabc,
        DateTimeOffset decisionAtUtc, decimal tickSize)
    {
        Contract.Utc(decisionAtUtc, nameof(decisionAtUtc));
        Contract.Positive(tickSize, nameof(tickSize));
        if (xabc == null || xabc.Count != 4)
            throw new ArgumentException("Exactly four already-confirmed X/A/B/C pivots required");
        for (int i = 0; i < 4; i++)
        {
            xabc[i].Validate(decisionAtUtc);
            if (i > 0 && (xabc[i].SourceBarIndex <= xabc[i-1].SourceBarIndex
                || xabc[i].EventAtUtc <= xabc[i-1].EventAtUtc
                || xabc[i].Kind == xabc[i-1].Kind))
                throw new ArgumentException("Non-causal X/A/B/C sequence");
        }
        var direction = xabc[0].Kind == PivotKind.Low ? Side.Buy : Side.Sell;
        if ((direction == Side.Buy && !(xabc[1].Price > xabc[0].Price &&
                xabc[2].Price < xabc[1].Price &&
                xabc[3].Price > xabc[2].Price))
            || (direction == Side.Sell && !(xabc[1].Price < xabc[0].Price &&
                xabc[2].Price > xabc[1].Price &&
                xabc[3].Price < xabc[2].Price)))
            throw new ArgumentException("X/A/B/C directional geometry invalid");

        decimal xa = Math.Abs(xabc[1].Price - xabc[0].Price);
        decimal ab = Math.Abs(xabc[2].Price - xabc[1].Price);
        decimal bc = Math.Abs(xabc[3].Price - xabc[2].Price);
        if (xa <= 0 || ab <= 0 || bc <= 0)
            throw new ArgumentException("Degenerate X/A/B/C geometry");
        decimal xabRatio = ab/xa;
        decimal abcRatio = bc/ab;
        var zones = new List<ResearchPrzProjection>();
        foreach (var rule in PatternCatalog.ResearchOnly)
        {
            if (rule.Mode == GeometryMode.Specialized) continue;
            if (!rule.Abc.Contains(abcRatio)) continue;
            if (rule.Mode == GeometryMode.Xabcd && !rule.Xab.Contains(xabRatio))
                continue;
            var bands = new List<PriceInterval>
            {
                ProjectLeg(xabc[3].Price, bc, rule.Bcd, direction)
            };
            if (rule.Mode == GeometryMode.Xabcd)
                bands.Add(ProjectLeg(xabc[1].Price, xa, rule.Xad, direction));
            else
                bands.Add(ProjectLeg(xabc[3].Price, ab, rule.CdAb, direction));

            PriceInterval? intersection = PriceInterval.Intersect(bands);
            if (intersection == null) continue;
            decimal low = Math.Ceiling(intersection.Low/tickSize)*tickSize;
            decimal high = Math.Floor(intersection.High/tickSize)*tickSize;
            if (low <= 0 || low > high) continue;
            zones.Add(new ResearchPrzProjection(rule.Family, direction,
                new PriceInterval(low,high), xabc[3].AvailableAtUtc,
                SourceVerified:false));
        }
        return zones;
    }

    private static PriceInterval ProjectLeg(decimal anchor, decimal size,
        RatioBand band, Side direction)
    {
        if (!band.Contains(band.Minimum) || !band.Contains(band.Maximum))
            throw new ArgumentException("Invalid research ratio band");
        return direction == Side.Buy
            ? new PriceInterval(anchor - band.Maximum*size,
                                anchor - band.Minimum*size)
            : new PriceInterval(anchor + band.Minimum*size,
                                anchor + band.Maximum*size);
    }
}
