using System;
using System.Collections.Generic;
using cAlgo.API;

namespace cAlgo.Robots
{
    // Shared domain/state contracts extracted from the Robot implementation so detector,
    // resolution, risk and execution layers exchange explicit immutable-ish records instead
    // of relying on physical source-file colocation. No runtime semantics are changed here.
    public enum TradeDirection { Neutral, Buy, Sell }
    public enum HarmonicState { Neutral, Bullish, Bearish }
    public enum MtfConflict { NEUTRAL, ALIGNED, SUPPORTED, TRANSITION, CONFLICT }
    public enum HarmonicRoute { NO_TRADE, TREND_ALIGNED_REVERSAL, EXHAUSTION_REVERSAL, TRANSITION_REVERSAL, FAILURE_CONTINUATION }
    public enum CandidateState { DETECTED, VALIDATED, ROUTED, WAIT_PRZ, CONFIRMING, ARMED, SLOT_BLOCKED, PARKED, REVALIDATING, EXECUTABLE, EXECUTED, EXPIRED, REJECTED, INVALIDATED }
    public enum PatternMode { STANDARD, ABCD, CYPHER, SHARK, FIVEZERO }

    public sealed class PatternProfile
    {
        public string Name;
        public PatternMode Mode;
        public double XabMin, XabMax, AbcMin, AbcMax, BcdMin, BcdMax, XadMin, XadMax, AbcDMin, AbcDMax;
        public double PrzWidthAtr, StopBufferAtr, Target1Cd, Target2Cd;
        public int MaxAgeM15Bars;
        public double MinGeometry, MinPrz;
        public bool GridEnabled;
        public double[] GridFractions = new double[0];
        public int MaximumGridLegs;
        public double[] GridRiskWeights = new double[0];
        public string GridAnchorRule;
        public double MinimumGridSpanXa, MaximumGridSpanXa, GridStructuralTolerance, StructuralStopFibBuffer;
        public int PendingTtlMinutes;
        public string CanonicalTargetPolicy;
    }

    public sealed class PivotPoint
    {
        public int Index;
        public double Price;
        public bool IsHigh;
    }

    public sealed class PatternSignal
    {
        public string PatternName;
        public PatternProfile Profile;
        public TradeDirection Direction;
        public PivotPoint X, A, B, C, D;
        public int PivotScale;
        public double Xab, Abc, Bcd, Xad, AdXa, XdXa, AbCd;
        public string HarmonicSubtype;
        public string ResearchRole;
        public double PrzLow, PrzHigh;
        public double GeometryQuality, PrzConfluence, TimeSymmetry, PivotQuality, Confidence;
        public double StructuralInvalidation, CanonicalTarget1, CanonicalTarget2;
        public DateTime CompletionTime;
        public string Timeframe;
    }

    public sealed class RegimeSnapshot
    {
        public TradeDirection TrendDirection;
        public bool Transition;
        public double AtrRatio;
        public double AtrM15Pips;
        public double AtrPercentile;
        public double Efficiency;
        public double ExtensionAtr;
        public double AdxH1;
        public double AdxH4;
        public double AdxH1Slope;
        public double TrendStrength;
    }

    public enum V71ExpansionState { WAIT_PRZ, CONFIRMING, PROOF_WAIT, PROOF_ACTIVE, ARMED, EXECUTED, EXPIRED, REJECTED, INVALIDATED }

    public sealed class V72PayoffAccumulator
    {
        public int N, Wins;
        public double SumR, SumSqR, GrossProfitR, GrossLossR;
    }

    public sealed class V71ExpansionCandidate
    {
        public string CandidateId, IdentityKey, SetupKey;
        public PatternSignal Signal;
        public MtfConflict Conflict;
        public HarmonicRoute Route;
        public RegimeSnapshot Regime;
        public V71ExpansionState State;
        public bool IsActive, Executed, ShadowStarted, ShadowFinished;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc, ArmedUtc, ReactionProofUtc, VirtualProofStartUtc, FailureBreakUtc;
        public DateTime PullbackExpiryUtc, VirtualProofExpiryUtc, FailureRetestExpiryUtc;
        public double ConfirmationScore, NetRR, RegimeScore;
        public double ReactionProofPrice, ReactionExtremePrice, ReactionScore;
        public double VirtualEntryAnchor, VirtualStructuralStop, VirtualRiskDistance, VirtualProofPrice;
        public double FailureBoundary, FailureBreakPrice;
        public double AsymmetryCompression = 1.0;
        public TradeDirection CapitalDirection = TradeDirection.Neutral;
        public double EntryAnchor, StructuralStop, CanonicalTarget, RiskDistance, TargetR;
        public double EdgeMean, EdgeLcb, SlotScore, ShadowOutcomeR;
        public double AtrPercentile, AdxH1Norm, AdxH4Norm, AdxSlopeNorm, TrendStrength;
        public double SpreadAtr, SessionPhase, PrzCompression, TransitionState;
        public double SupportDistance, ExpectedSlotHours, ExpectedSlotHoursUcb, SurvivalProbability = .50;
        public double ModeledCostR, PathProbability, PathLcb, RunnerProbability, RunnerLcb, CoreArrivalHazard;
        public bool SupportEligible = true;
        public bool CoreOverlapObserved, CapitalEligible = true, NativeExitCaptured, PathUsable;
        public bool ReactionProved, ReactionExtremeInitialized, AwaitingPullbackFill, PullbackFilled;
        public bool AwaitingVirtualProofFill, VirtualProofActive, TrendProofConfirmed, FailureContinuation, FailureBreakObserved, CapitalReady;
        public string CapitalLane = "NONE";
        public string AbcdRole = "PARENT_FAMILY", NativeExitResult;
        public double NativeExitR, ShadowPeakR, ShadowProtectionR = -1.0;
        public double ShadowMfeR, ShadowMaeR, ShadowMaxGivebackR;
        public int ShadowBars, NativeConfirmBars, PathState;
        public int TimeTo05R = -1, TimeTo1R = -1, TimeTo2R = -1, TimeToStopR = -1, TimeToMfeBars = -1;
        public CandidateRecord NativeEvidenceState;
    }

    public sealed class CandidateRecord
    {
        public string CandidateId;
        public string SetupKey;
        public PatternSignal Signal;
        public CandidateState State;
        public bool IsActive = true;
        public DateTime DetectedUtc, ExpiryUtc;
        public DateTime? PrzTouchUtc;
        public MtfConflict Conflict = MtfConflict.NEUTRAL;
        public HarmonicRoute Route = HarmonicRoute.NO_TRADE;
        public RegimeSnapshot Regime;
        public double ConfirmationScore, NetRR, SelectedTarget, Rank;
        public double AlphaQualityScore, RegimeScore, CapitalMinL0Risk, CapitalMinL0Margin;
        public int RescueBarsObserved;
        public double RescueBestScore;
        public DateTime? ArmedUtc, ParkedUtc, ParkedHardExpiryUtc;
        public bool ArmedGraceApplied, WasParked, OpportunityTerminalLogged;
        public int NativeM1BarsObserved, NativeStage;
        public int FamilyConfirmationBarsObserved;
        public bool FamilyDirectional, FamilyReclaim, FamilyBos, FamilyRejection, FamilySweep,
                    FamilyFailedExtension, FamilyInsidePrz, FamilyDisplacement, FamilyRetest;
        public double OriginalRank, OriginalGeometry, OriginalPrzConfluence, OriginalM1Evidence, OriginalEntryAnchor, ShadowRiskDistance, ShadowMfeR, ShadowMaeR;
        public double CompletionAnchorPrice, NativeConfirmAnchorPrice, NativeRetestAnchorPrice;
        public double CompletionAnchorMfeR, CompletionAnchorMaeR, NativeConfirmMfeR, NativeConfirmMaeR, NativeRetestMfeR, NativeRetestMaeR;
        public bool TemporalDirectional, TemporalReclaim, TemporalBos1, TemporalBos2, TemporalRejection, TemporalFailedExtension, TemporalDisplacement;
        public bool CapitalFeasible;
        public bool V71Expansion;
        public bool V72BifurcationAlpha;
        public double V71RiskPercent = 1.0;
        public FibonacciGridPlan GridPlan;
        public long PositionId;
        public string LastReason;
    }

    public sealed class PositionLedger
    {
        public long PositionId;
        public string CandidateId;
        public string PatternName;
        public HarmonicRoute Route;
        public TradeDirection Direction;
        public DateTime EntryUtc;
        public double InitialRiskPips;
        public double RiskAmount;
        public double PeakR;
        public double MaxAdverseR;
        public string ExitOverride;
        public string BasketId;
        public int LegIndex;
    }

    public enum GridLegState { PLANNED, SUBMITTING, SUBMITTED, FILLED_UNVERIFIED, PROTECTED, VIRTUAL_ONLY, VIRTUAL_FILLED, FAIL_CLOSED, CANCELLED, EXPIRED, REJECTED, RISK_REJECTED }
    public enum FibonacciBasketState { PLANNED, LEG0_EXECUTED, GRID_PENDING, PARTIALLY_FILLED, BASKET_ACTIVE, BASKET_PROTECTED, CLOSED, CANCELLED, EXPIRED, INVALIDATED, RISK_REJECTED, MARGIN_REJECTED, SESSION_EXPIRED }

    public sealed class FibonacciGridLeg
    {
        public int Index;
        public double Fraction, PlannedPrice, RiskWeight, RiskBudget, Volume, PlannedRisk, ModeledCost, MinBrokerRisk;
        public long PendingOrderId, PositionId;
        public bool Physical, FillCounted;
        public GridLegState State;
    }

    public sealed class FibonacciGridPlan
    {
        public string CandidateId, BasketId, Pattern;
        public TradeDirection Direction;
        public HarmonicRoute Route;
        public DateTime CreatedUtc, ExpirationUtc;
        public double EntryAnchor, StructuralStop, GridDistance, CanonicalTarget, ExpectedWeightedEntry;
        public double BasketRiskAmount, WorstCaseRisk, ExpectedNetRR, VirtualWeightedEntry, EstimatedPhysicalMargin;
        public int LogicalLegCount, PhysicalDepth;
        public bool MicroCapitalMode;
        public readonly List<FibonacciGridLeg> Legs = new List<FibonacciGridLeg>();
    }

    public sealed class FibonacciBasket
    {
        public string BasketId, CandidateId, Pattern, ExitOverride, ExitReason;
        public TradeDirection Direction;
        public HarmonicRoute Route;
        public FibonacciBasketState State;
        public DateTime CreatedUtc, ExpirationUtc;
        public double EntryAnchor, AverageEntry, StructuralStop, CanonicalTarget;
        public double InitialBasketRisk, PlannedWorstCaseRisk, PeakR, MaxAdverseR, RealizedNet, ProtectionFrontier;
        public int FilledLegs, ClosedLegs;
        public bool IsActive;
        public FibonacciGridPlan Plan;
        public CandidateRecord Candidate;
    }

    public sealed class PipelineCounter
    {
        public long Detected, Validated, Routed, PrzWaiting, Confirming, NativeTemporalPass, Armed, SlotBlocked, Parked, Revalidated, RevalidationRejected, BasketPlanned;
        public long Leg0Executed, Leg1Filled, Leg2Filled, Leg3Filled, BasketClosed;
        public long Executed, Expired, Rejected, Invalidated;
    }}
