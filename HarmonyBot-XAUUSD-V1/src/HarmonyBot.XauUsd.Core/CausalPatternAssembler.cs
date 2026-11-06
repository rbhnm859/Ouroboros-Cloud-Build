using System;
using System.Collections.Generic;
using System.Linq;

namespace HarmonyBot.XauUsd.Core;

// Stateful, single-threaded research aggregator: only confirmed pivots enter.
// Updates an uncommitted same-side swing to the more extreme confirmed pivot.
// Every emitted observation has immutable identity based on confirmed D.
public sealed class CausalPatternAssembler
{
    private readonly List<ConfirmedPivot> _recent = new();
    private readonly ResearchIntentLedger _emitted = new();
    private long _lastSource = -1;

    public HarmonicObservation? Observe(ConfirmedPivot pivot, DateTimeOffset decisionAtUtc,
        decimal tickSize)
    {
        pivot.Validate(decisionAtUtc);
        if (pivot.SourceBarIndex <= _lastSource)
            throw new InvalidOperationException("Non-monotone / ambiguous pivot delivery");
        _lastSource = pivot.SourceBarIndex;
        if (_recent.Count > 0 && _recent[^1].Kind == pivot.Kind)
        {
            var old = _recent[^1];
            bool isMoreExtreme = pivot.Kind == PivotKind.High
                ? pivot.Price > old.Price : pivot.Price < old.Price;
            if (isMoreExtreme) _recent[^1] = pivot;
            return null;
        }
        _recent.Add(pivot);
        if (_recent.Count > 5) _recent.RemoveAt(0);
        if (_recent.Count < 5) return null;
        HarmonicObservation candidate = HarmonicAnalyzer.Analyze(_recent,decisionAtUtc,tickSize);
        return _emitted.TryReserve(candidate.EventId) ? candidate : null;
    }
}
