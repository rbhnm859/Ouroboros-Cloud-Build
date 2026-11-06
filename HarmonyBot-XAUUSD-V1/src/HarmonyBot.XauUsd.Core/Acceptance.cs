using System;
using System.Collections.Generic;
using System.Linq;

namespace HarmonyBot.XauUsd.Core;

public sealed record AnnualOosEvidence(
    int Year, bool CompleteYear, bool OutOfSample, bool DataLineageVerified,
    bool FeesAndExecutionVerified, string DatasetSha256, string ConfigurationSha256,
    string CostModelSha256, int WholeTrades, decimal MeanR, decimal PfR,
    decimal WinRate, decimal AverageWinningR, decimal LowerConfidenceBound95);

public sealed record AnnualGateResult(int Year, bool Passed, string Reason);

public static class CommercialResearchGate
{
    // Separate, V1-only contract. This does NOT supersede V74's frozen 3/3 gates.
    public static AnnualGateResult Check(AnnualOosEvidence y)
    {
        if (y.Year < 2000 || !y.CompleteYear || !y.OutOfSample ||
            !y.DataLineageVerified || !y.FeesAndExecutionVerified ||
            !IsSha256(y.DatasetSha256) || !IsSha256(y.ConfigurationSha256) ||
            !IsSha256(y.CostModelSha256))
            return new(y.Year, false, "PROVENANCE_OR_OOS_INCOMPLETE");
        if (y.WholeTrades < 500) return new(y.Year, false, "N_LT_500");
        if (y.MeanR < .90m) return new(y.Year, false, "MEAN_R_LT_0_90");
        if (y.PfR < 3.30m) return new(y.Year, false, "PF_R_LT_3_30");
        if (y.WinRate < .60m) return new(y.Year, false, "WR_LT_0_60");
        if (y.AverageWinningR < 2.30m) return new(y.Year, false, "AVG_WIN_R_LT_2_30");
        if (y.LowerConfidenceBound95 <= 0m) return new(y.Year, false, "LCB95_NONPOSITIVE");
        return new(y.Year, true, "METRIC_CONTRACT_ONLY");
    }

    public static bool CheckAll(IReadOnlyList<AnnualOosEvidence> years) =>
        years.Count > 0 && years.Select(y=>y.Year).Distinct().Count()==years.Count
        && years.All(y=>Check(y).Passed);

    private static bool IsSha256(string hash) =>
        hash != null && hash.Length == 64 && hash.All(c =>
            c is >= '0' and <= '9' or >= 'a' and <= 'f');
}

// An entire thesis remains one trade even after multiple partial reductions.
// Input net PnL MUST include commissions, spread, swap and other broker costs.
public sealed class WholeTradeAccounting
{
    public string ThesisId { get; }
    public decimal InitialUnits { get; }
    public decimal InitialApprovedRiskUsd { get; }
    public decimal RemainingUnits { get; private set; }
    public decimal RealizedNetPnlUsd { get; private set; }
    public int PartialCloseCount { get; private set; }
    public int WholeTradeCount => RemainingUnits == 0 ? 1 : 0;
    public bool Closed => RemainingUnits == 0;

    public WholeTradeAccounting(string thesisId, decimal initialUnits, decimal initialRiskUsd)
    {
        if (string.IsNullOrWhiteSpace(thesisId)) throw new ArgumentException(nameof(thesisId));
        Contract.Positive(initialUnits, nameof(initialUnits));
        Contract.Positive(initialRiskUsd, nameof(initialRiskUsd));
        ThesisId = thesisId;
        InitialUnits = RemainingUnits = initialUnits;
        InitialApprovedRiskUsd = initialRiskUsd;
    }

    public void RecordNetClose(decimal closedUnits, decimal closeNetPnlUsd)
    {
        if (RemainingUnits <= 0 || closedUnits <= 0 || closedUnits > RemainingUnits)
            throw new InvalidOperationException("Invalid close: cannot add exposure");
        RemainingUnits -= closedUnits;
        RealizedNetPnlUsd += closeNetPnlUsd;
        PartialCloseCount++;
    }
    public decimal FinalNetR()
    {
        if (!Closed) throw new InvalidOperationException("Unrealized trade cannot finalize R");
        return ResearchStatistics.RealizedR(RealizedNetPnlUsd, InitialApprovedRiskUsd);
    }
}
