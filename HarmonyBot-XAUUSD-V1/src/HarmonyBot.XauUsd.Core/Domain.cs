using System;
using System.Globalization;

namespace HarmonyBot.XauUsd.Core;

public static class Contract
{
    public const string Version = "HBXAU-V1-DOMAIN-2026-11-06";
    public static void Utc(DateTimeOffset time, string name)
    {
        if (time.Offset != TimeSpan.Zero) throw new ArgumentException("UTC offset required", name);
    }
    public static void Positive(decimal value, string name)
    {
        if (value <= 0) throw new ArgumentOutOfRangeException(name);
    }
}

public enum Side { Buy, Sell }
public enum PivotKind { High, Low }
public enum Lifecycle { Discover, Project, Complete, Evaluate, Defer, Reject, Enter, Manage, Close }
public enum Decision { Defer, Reject, Enter }
public enum PatternFamily
{
    Gartley, Bat, AlternateBat, Butterfly, Crab, DeepCrab,
    Shark, FiveZero, AbCd, AlternateAbCd
}

public sealed record CompletedBar(
    DateTimeOffset OpenUtc, DateTimeOffset CloseUtc,
    decimal Open, decimal High, decimal Low, decimal Close)
{
    public void Validate()
    {
        Contract.Utc(OpenUtc, nameof(OpenUtc)); Contract.Utc(CloseUtc, nameof(CloseUtc));
        if (CloseUtc <= OpenUtc) throw new ArgumentException("Bar must be completed");
        if (Low <= 0 || High < Low || Open < Low || Open > High || Close < Low || Close > High)
            throw new ArgumentException("Invalid OHLC");
    }
}

public sealed record ConfirmedPivot(
    long SourceBarIndex, long ConfirmationBarIndex, PivotKind Kind,
    decimal Price, DateTimeOffset EventAtUtc, DateTimeOffset AvailableAtUtc)
{
    public void Validate(DateTimeOffset decisionAtUtc)
    {
        Contract.Utc(EventAtUtc, nameof(EventAtUtc));
        Contract.Utc(AvailableAtUtc, nameof(AvailableAtUtc));
        Contract.Utc(decisionAtUtc, nameof(decisionAtUtc));
        Contract.Positive(Price, nameof(Price));
        if (SourceBarIndex > ConfirmationBarIndex || EventAtUtc > AvailableAtUtc
            || AvailableAtUtc > decisionAtUtc)
            throw new ArgumentException("Pivot not yet causally available");
    }
}

public static class EventIdentity
{
    // One completed harmonic event, irrespective of overlapping family candidates.
    public static string Create(Side direction, ConfirmedPivot completedD, decimal tickSize)
    {
        Contract.Positive(tickSize, nameof(tickSize));
        completedD.Validate(completedD.AvailableAtUtc);
        decimal ticks = decimal.Round(completedD.Price / tickSize, 0, MidpointRounding.AwayFromZero);
        return string.Concat(direction.ToString().ToUpperInvariant(), "|",
            completedD.EventAtUtc.UtcTicks.ToString(CultureInfo.InvariantCulture), "|",
            ticks.ToString("0", CultureInfo.InvariantCulture));
    }
}

public sealed class CausalPivotDetector
{
    private readonly int _left;
    private readonly int _right;
    private readonly System.Collections.Generic.List<CompletedBar> _bars = new();
    private long _offset;
    public CausalPivotDetector(int leftBars = 3, int rightBars = 3)
    {
        if (leftBars < 1 || rightBars < 1) throw new ArgumentOutOfRangeException(nameof(leftBars));
        _left = leftBars; _right = rightBars;
    }

    public System.Collections.Generic.IReadOnlyList<ConfirmedPivot> AppendCompleted(CompletedBar closedBar)
    {
        closedBar.Validate();
        if (_bars.Count > 0 && closedBar.OpenUtc < _bars[^1].CloseUtc)
            throw new InvalidOperationException("Overlapping or out-of-order bars");
        _bars.Add(closedBar);
        var result = new System.Collections.Generic.List<ConfirmedPivot>(2);
        int center = _bars.Count - 1 - _right;
        if (center >= _left)
        {
            bool isHigh = true, isLow = true;
            for (int i = center - _left; i <= center + _right; ++i)
            {
                if (i == center) continue;
                if (_bars[center].High <= _bars[i].High) isHigh = false;
                if (_bars[center].Low >= _bars[i].Low) isLow = false;
            }
            long source = _offset + center;
            long confirmation = _offset + _bars.Count - 1;
            DateTimeOffset availableAt = _bars[^1].CloseUtc;
            if (isHigh) result.Add(new ConfirmedPivot(source, confirmation,
                PivotKind.High, _bars[center].High, _bars[center].CloseUtc, availableAt));
            if (isLow) result.Add(new ConfirmedPivot(source, confirmation,
                PivotKind.Low, _bars[center].Low, _bars[center].CloseUtc, availableAt));
        }
        // Bounded memory without resetting absolute source-bar indexes.
        if (_bars.Count > Math.Max(256, _left + _right + 2))
        {
            _bars.RemoveAt(0);
            _offset++;
        }
        return result;
    }
}
