using System;
using System.Collections.Generic;

namespace HarmonyBot.XauUsd.Core;

public sealed record BrokerSnapshot(
    bool Verified, bool SymbolTradable, bool MarketOpen, bool CurrencyConversionVerified,
    decimal VolumeMin, decimal VolumeMax, decimal VolumeStep, decimal TickSize,
    decimal PipSize, decimal MinStopDistancePrice, decimal MarginPerVolumeUnit,
    decimal MoneyPerPriceUnitPerVolumeUnit, DateTimeOffset ObservedAtUtc);

public sealed record PortfolioSnapshot(
    decimal EquityUsd, decimal PeakEquityUsd, decimal FreeMarginUsd,
    int OpenXauPositions, int PendingXauOrders, bool ReconciliationComplete,
    bool ExclusiveExecutionLeaseHeld, bool UnknownOrderOutcome);

public sealed record ProposedTrade(
    string EventId, Side Direction, decimal Entry, decimal Stop, decimal Target,
    decimal RoundTripFeesPerVolumeUnit, decimal StressedSlippagePerVolumeUnit,
    decimal RequestedRiskPercent, decimal SpreadPrice, DateTimeOffset DecisionAtUtc);

public sealed record TradeAllocation(
    string EventId, decimal VolumeInUnits, decimal InitialRiskUsd,
    decimal NetRewardRisk, decimal RequiredMarginUsd, decimal RiskPerVolumeUnitUsd);

public sealed record RiskDecision(bool Approved, string Reason, TradeAllocation? Allocation)
{
    public static RiskDecision Reject(string reason) => new(false, reason, null);
}

public static class RiskGate
{
    public static RiskDecision Evaluate(ProposedTrade t, BrokerSnapshot b, PortfolioSnapshot p)
    {
        if (string.IsNullOrWhiteSpace(t.EventId)) return RiskDecision.Reject("MISSING_EVENT_ID");
        Contract.Utc(t.DecisionAtUtc, nameof(t.DecisionAtUtc));
        Contract.Utc(b.ObservedAtUtc, nameof(b.ObservedAtUtc));
        if (!b.Verified || !b.CurrencyConversionVerified || !b.SymbolTradable || !b.MarketOpen)
            return RiskDecision.Reject("BROKER_CAPABILITY_UNVERIFIED");
        if (b.ObservedAtUtc > t.DecisionAtUtc
            || t.DecisionAtUtc - b.ObservedAtUtc > TimeSpan.FromMinutes(2))
            return RiskDecision.Reject("STALE_BROKER_SNAPSHOT");
        if (!p.ReconciliationComplete || !p.ExclusiveExecutionLeaseHeld || p.UnknownOrderOutcome)
            return RiskDecision.Reject("EXECUTION_CUSTODY_UNVERIFIED");
        if (p.OpenXauPositions < 0 || p.PendingXauOrders < 0)
            return RiskDecision.Reject("INVALID_EXPOSURE_COUNT");
        if (p.OpenXauPositions != 0 || p.PendingXauOrders != 0)
            return RiskDecision.Reject("XAUUSD_EXPOSURE_ALREADY_EXISTS");
        if (p.EquityUsd < 100 || p.FreeMarginUsd <= 0
            || p.PeakEquityUsd < p.EquityUsd || p.PeakEquityUsd <= 0)
            return RiskDecision.Reject("CAPITAL_OR_PEAK_INVALID");
        if ((p.PeakEquityUsd - p.EquityUsd) / p.PeakEquityUsd >= 0.10m)
            return RiskDecision.Reject("MAX_DRAWDOWN_LIMIT");
        if (t.RequestedRiskPercent <= 0 || t.RequestedRiskPercent > 5)
            return RiskDecision.Reject("RISK_PERCENT_LIMIT");
        if (b.VolumeMin <= 0 || b.VolumeMax < b.VolumeMin || b.VolumeStep <= 0
            || b.TickSize <= 0 || b.PipSize <= 0 || b.MarginPerVolumeUnit <= 0
            || b.MoneyPerPriceUnitPerVolumeUnit <= 0 || b.MinStopDistancePrice < 0)
            return RiskDecision.Reject("INVALID_BROKER_NUMERICS");
        if (t.Direction != Side.Buy && t.Direction != Side.Sell)
            return RiskDecision.Reject("INVALID_SIDE");
        if (t.Entry <= 0 || t.Stop <= 0 || t.Target <= 0
            || t.SpreadPrice < 0 || t.RoundTripFeesPerVolumeUnit < 0
            || t.StressedSlippagePerVolumeUnit < 0)
            return RiskDecision.Reject("INVALID_TRADE_NUMERICS");
        if (t.Entry % b.TickSize != 0 || t.Stop % b.TickSize != 0
            || t.Target % b.TickSize != 0)
            return RiskDecision.Reject("PRICE_OFF_TICK_GRID");
        bool correctOrder = t.Direction == Side.Buy
            ? t.Stop < t.Entry && t.Entry < t.Target
            : t.Target < t.Entry && t.Entry < t.Stop;
        if (!correctOrder || Math.Abs(t.Entry - t.Stop) < b.MinStopDistancePrice
            || Math.Abs(t.Entry - t.Target) < b.MinStopDistancePrice)
            return RiskDecision.Reject("INVALID_STOP_TARGET_GEOMETRY");
        decimal cost = t.RoundTripFeesPerVolumeUnit + t.StressedSlippagePerVolumeUnit
                       + t.SpreadPrice * b.MoneyPerPriceUnitPerVolumeUnit;
        decimal perUnitRisk = Math.Abs(t.Entry - t.Stop)
            * b.MoneyPerPriceUnitPerVolumeUnit + cost;
        decimal perUnitReward = Math.Abs(t.Entry - t.Target)
            * b.MoneyPerPriceUnitPerVolumeUnit - cost;
        if (perUnitRisk <= 0 || perUnitReward <= 0 || perUnitReward / perUnitRisk < 2)
            return RiskDecision.Reject("NET_RR_BELOW_2");
        // Conservative planned-loss budget: do not size an intended stop
        // that would already exceed the 10% peak-equity DD lock.
        // Gaps/slippage may STILL breach it; no live execution guarantee.
        decimal drawdownRoomUsd = p.EquityUsd - 0.90m * p.PeakEquityUsd;
        decimal allowedUsd = Math.Min(
            p.EquityUsd * t.RequestedRiskPercent / 100m, drawdownRoomUsd);
        if (allowedUsd <= 0m)
            return RiskDecision.Reject("DRAWDOWN_ROOM_EXHAUSTED");
        decimal maxAffordable = Math.Min(allowedUsd / perUnitRisk,
            p.FreeMarginUsd / b.MarginPerVolumeUnit);
        if (maxAffordable < b.VolumeMin)
            return RiskDecision.Reject("MINIMUM_VOLUME_UNAFFORDABLE");
        decimal maxVolume = Math.Min(maxAffordable, b.VolumeMax);
        // Volume-grid anchor is broker minimum volume, not zero.
        decimal steps = decimal.Floor((maxVolume - b.VolumeMin) / b.VolumeStep);
        decimal volume = b.VolumeMin + steps * b.VolumeStep;
        if (volume < b.VolumeMin || volume > b.VolumeMax || volume <= 0)
            return RiskDecision.Reject("VOLUME_NORMALIZATION_FAIL");
        decimal initialRiskUsd = volume * perUnitRisk;
        decimal requiredMarginUsd = volume * b.MarginPerVolumeUnit;
        if (initialRiskUsd > allowedUsd || requiredMarginUsd > p.FreeMarginUsd)
            return RiskDecision.Reject("POST_ROUNDING_RISK_OR_MARGIN");
        return new RiskDecision(true, "RESEARCH_ALLOCATION_ONLY",
            new TradeAllocation(t.EventId, volume, initialRiskUsd,
                perUnitReward / perUnitRisk, requiredMarginUsd, perUnitRisk));
    }
}

// In-memory research idempotency. Never substitute for broker reconciliation,
// durable transaction log, or distributed lease in a real execution gateway.
public sealed class ResearchIntentLedger
{
    private readonly HashSet<string> _seen = new(StringComparer.Ordinal);
    private readonly object _mutex = new();
    private readonly int _capacity;
    private bool _saturated;

    // Bounded memory with NO eviction: if the capacity is reached, new
    // candidates stop, rather than forgetting past IDs and re-emitting them.
    // This is NOT a durable/distributed idempotency or execution ledger.
    public ResearchIntentLedger(int capacity = 8192)
    {
        if (capacity < 1) throw new ArgumentOutOfRangeException(nameof(capacity));
        _capacity = capacity;
    }
    public bool Saturated { get { lock (_mutex) return _saturated; } }
    public int Count { get { lock (_mutex) return _seen.Count; } }

    public bool TryReserve(string thesisId)
    {
        if (string.IsNullOrWhiteSpace(thesisId) || thesisId.Length > 256) return false;
        lock (_mutex)
        {
            if (_seen.Contains(thesisId)) return false;
            if (_seen.Count >= _capacity)
            {
                _saturated = true;
                return false;
            }
            return _seen.Add(thesisId);
        }
    }
    public bool Contains(string thesisId)
    {
        lock (_mutex) return _seen.Contains(thesisId);
    }
}

public static class VirtualProfitGrid
{
    // Only manages existing single-position protective stop; never increases size.
    public static decimal TightenStop(Side direction, decimal initialStop,
        decimal currentStop, decimal proposedStop)
    {
        if (initialStop <= 0 || currentStop <= 0 || proposedStop <= 0)
            throw new ArgumentOutOfRangeException(nameof(proposedStop));
        if (direction == Side.Buy)
        {
            if (currentStop < initialStop || proposedStop < currentStop)
                throw new InvalidOperationException("Stop widening forbidden");
        }
        else if (currentStop > initialStop || proposedStop > currentStop)
            throw new InvalidOperationException("Stop widening forbidden");
        return proposedStop;
    }

    public static decimal PartialClose(decimal remainingUnits, decimal closeUnits)
    {
        if (remainingUnits <= 0 || closeUnits <= 0 || closeUnits > remainingUnits)
            throw new InvalidOperationException("Partial close must only reduce exposure");
        return remainingUnits - closeUnits;
    }
}

public static class ResearchStatistics
{
    // Net PnL is assumed already cost-inclusive and normalized to APPROVED initial risk.
    public static decimal RealizedR(decimal netPnlUsd, decimal approvedInitialRiskUsd)
    {
        Contract.Positive(approvedInitialRiskUsd, nameof(approvedInitialRiskUsd));
        return netPnlUsd / approvedInitialRiskUsd;
    }
}
