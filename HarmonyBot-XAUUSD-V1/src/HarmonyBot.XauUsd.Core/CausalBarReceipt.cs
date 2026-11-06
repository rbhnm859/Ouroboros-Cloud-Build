using System;

namespace HarmonyBot.XauUsd.Core;

/// <summary>
/// A confirmed candle from OnBar(), with a separate first-tick receipt time.
/// The next bar's open is an observation boundary, NOT evidence of the final
/// tick time of the previous bar; the exact last traded tick may be unknown.
/// </summary>
public sealed record CausalBarReceipt(
    CompletedBar ClosedBar,
    DateTimeOffset NextBarOpenUtc,
    DateTimeOffset ObservedAtUtc,
    DateTimeOffset AvailableAtUtc)
{
    public static CausalBarReceipt CaptureOnBarOpened(
        DateTimeOffset closedOpenUtc, DateTimeOffset nextBarOpenUtc,
        DateTimeOffset firstObservedTickUtc,
        decimal open, decimal high, decimal low, decimal close)
    {
        Contract.Utc(closedOpenUtc, nameof(closedOpenUtc));
        Contract.Utc(nextBarOpenUtc, nameof(nextBarOpenUtc));
        Contract.Utc(firstObservedTickUtc, nameof(firstObservedTickUtc));
        if (nextBarOpenUtc <= closedOpenUtc)
            throw new ArgumentException("Non-increasing bar-open sequence");
        if (firstObservedTickUtc < nextBarOpenUtc)
            throw new ArgumentException("First observed tick predates new bar");
        var completed = new CompletedBar(closedOpenUtc, nextBarOpenUtc,
            open, high, low, close);
        completed.Validate();
        return new CausalBarReceipt(completed, nextBarOpenUtc,
            firstObservedTickUtc, firstObservedTickUtc);
    }
}
