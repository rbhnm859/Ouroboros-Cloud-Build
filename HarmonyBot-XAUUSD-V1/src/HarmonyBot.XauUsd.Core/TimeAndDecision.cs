using System;
using System.Collections.Generic;
using System.Linq;

namespace HarmonyBot.XauUsd.Core;

public sealed record TimeStampedFeature(
    string Name, decimal Value, DateTimeOffset EventAtUtc,
    DateTimeOffset ObservedAtUtc, DateTimeOffset AvailableAtUtc);

public static class TemporalGate
{
    public static bool CanUse(TimeStampedFeature f, DateTimeOffset decisionAtUtc)
    {
        Contract.Utc(decisionAtUtc, nameof(decisionAtUtc));
        Contract.Utc(f.EventAtUtc, nameof(f.EventAtUtc));
        Contract.Utc(f.ObservedAtUtc, nameof(f.ObservedAtUtc));
        Contract.Utc(f.AvailableAtUtc, nameof(f.AvailableAtUtc));
        return f.EventAtUtc <= f.ObservedAtUtc &&
               f.ObservedAtUtc <= f.AvailableAtUtc &&
               f.AvailableAtUtc <= decisionAtUtc;
    }
    public static bool CanUseAll(IEnumerable<TimeStampedFeature> features,
        DateTimeOffset decisionAtUtc) => features.All(f => CanUse(f, decisionAtUtc));
}

public static class InstitutionalSession
{
    private static TimeZoneInfo Resolve(string iana, string windows)
    {
        try { return TimeZoneInfo.FindSystemTimeZoneById(iana); }
        catch (TimeZoneNotFoundException) { return TimeZoneInfo.FindSystemTimeZoneById(windows); }
    }

    public static bool IsOpen(DateTimeOffset utc, bool brokerHoursVerified,
        bool holidayAndSpreadVerified)
    {
        Contract.Utc(utc, nameof(utc));
        if (!brokerHoursVerified || !holidayAndSpreadVerified) return false;
        if (utc.DayOfWeek == DayOfWeek.Saturday || utc.DayOfWeek == DayOfWeek.Sunday)
            return false;
        var london = Resolve("Europe/London", "GMT Standard Time");
        var newYork = Resolve("America/New_York", "Eastern Standard Time");
        var localLondon = TimeZoneInfo.ConvertTime(utc, london);
        var localNy = TimeZoneInfo.ConvertTime(utc, newYork);
        // Resolve the local 08:00 London open and 17:00 New York close for
        // the same session date; no hard-coded year-round UTC offsets.
        DateTime day = utc.UtcDateTime.Date;
        DateTime londonOpen = new DateTime(day.Year, day.Month, day.Day, 8, 0, 0,
            DateTimeKind.Unspecified);
        DateTime nyClose = new DateTime(day.Year, day.Month, day.Day, 17, 0, 0,
            DateTimeKind.Unspecified);
        // Use local calendar dates instead of UTC midnight when offset changes.
        londonOpen = localLondon.Date.AddHours(8);
        nyClose = localNy.Date.AddHours(17);
        DateTime londonOpenUtc = TimeZoneInfo.ConvertTimeToUtc(londonOpen, london);
        DateTime nyCloseUtc = TimeZoneInfo.ConvertTimeToUtc(nyClose, newYork);
        return utc.UtcDateTime >= londonOpenUtc && utc.UtcDateTime < nyCloseUtc;
    }
}

public sealed record StrategyVerdict(
    Decision Action, Lifecycle Stage, string Reason, string? EventId);

public static class StrategyDecision
{
    // Production execution is hard-disabled in V1, even for qualified paper allocations.
    public static StrategyVerdict Evaluate(HarmonicObservation observation,
        bool allFeaturesCausal, bool brokerAndRiskKnown)
    {
        if (!allFeaturesCausal) return new(Decision.Reject, Lifecycle.Reject,
            "NON_CAUSAL_FEATURE", observation.EventId);
        if (!brokerAndRiskKnown) return new(Decision.Defer, Lifecycle.Defer,
            "BROKER_OR_RISK_UNVERIFIED", observation.EventId);
        if (!observation.ReadyForTrading) return new(Decision.Reject, Lifecycle.Reject,
            observation.Blocker, observation.EventId);
        return new(Decision.Reject, Lifecycle.Reject,
            "PHASE_1_EXECUTION_HARD_DISABLED", observation.EventId);
    }
}
