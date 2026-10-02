using System;
using System.Collections.Generic;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    // Terminal V71 one-shot challenger. Alpha truth is counterfactual and independent
    // of V51 capital-slot ownership; deployment remains V51-Core-first.
    public partial class HarmonyBotV71
    {
        [Parameter("Enable V72 HCOG Alpha", DefaultValue = false)]
        public bool EnableV72HcogAlpha { get; set; }

        private enum V72HcogState { WAIT_PRZ, WAIT_LIQUIDITY, WAIT_RECLAIM, WAIT_BOS, WAIT_RETEST, FAILURE_WAIT_RETEST, ACTIVE, CLOSED, EXPIRED }

        private static readonly double[] V74ProtectionTriggerR = { .25, .50, .75, 1.00, 1.50 };
        private static readonly double[] V74ProtectionFloorR = { .05, .10, .20, .40, .80 };
        private static readonly string[] V74ProtectionKey = { "025", "050", "075", "100", "150" };
        private static readonly double[] V74RcrReactionR = { .50, .75, 1.00 };
        private static readonly double[] V74RcrRetraceR = { .10, .25, .40 };
        private static readonly string[] V74RcrKey = { "R050_010", "R075_025", "R100_040" };
        private static readonly double[] V74HybridAdverseCutR = { -.20, -.30, -.40, -.50 };
        private static readonly string[] V74HybridKey = { "HS20", "HS30", "HS40", "HS50" };
        // Reaction-commit ladder: observe the harmonic thesis in shadow first, then commit
        // capital only after a completed-bar reaction hold. These are fixed research routes.
        private static readonly double[] V74ReactionCommitR = { .75, .75, 1.00, 1.00 };
        private static readonly double[] V74ReactionCommitStopFloorR = { .25, .25, .60, .60 };
        private static readonly double[] V74ReactionCommitAdverseCutR = { -.20, -.30, -.20, -.30 };
        private static readonly string[] V74ReactionCommitKey = { "RC075_C20", "RC075_C30", "RC100_C20", "RC100_C30" };
        private static readonly double[] V74ReactionCommitStageR = { .25, .50, .75, 1.00, 1.50 };
        private static readonly double[] V74ReactionCommitFloorR = { .05, .20, .40, .65, 1.00 };
        // High-conviction delayed capital: preserve canonical payoff asymmetry by waiting
        // until the virtual harmonic thesis has already demonstrated 1.75R/2.00R reaction.
        // Capital then enters only after a later completed M1 hold; stop is the completed
        // confirmation bar micro-structure and route NetRR must remain >=2.30.
        private static readonly double[] V74HighConvictionReactionR = { 1.75, 1.75, 2.00, 2.00 };
        private static readonly bool[] V74HighConvictionRequireDirectional = { false, true, false, true };
        private static readonly string[] V74HighConvictionKey = { "HC175_HOLD", "HC175_DIR", "HC200_HOLD", "HC200_DIR" };

        // V74 micro-positive-arm barbell reconstruction after Run #72.
        // The entry remains the same completed-bar causal reaction/hold route. Only
        // post-entry first-passage management changes: +0.05R/+0.10R/+0.15R is
        // observed, then a later completed M1 close must still hold +0.02/+0.05/+0.08R
        // before a single-basket 20%/30% crystallization. The remaining runner moves
        // to break-even and keeps the unchanged canonical target. No same-bar arm,
        // no stop widening, Grid, DCA, recovery, duplicate thesis or future label.
        private static readonly double[] V74SequentialReactionR = {
            .25,.25,.25,.25,.50,.50,.50,.50,
            .25,.25,.25,.25,.50,.50,.50,.50,
            .25,.25,.25,.25,.50,.50,.50,.50,
            .25,.25,.25,.25,.50,.50,.50,.50,
            .25,.25,.25,.25,.50,.50,.50,.50,
            .25,.25,.25,.25,.50,.50,.50,.50
        };
        private static readonly double[] V74SequentialHoldR = {
            .10,.10,.10,.10,.25,.25,.25,.25,
            .10,.10,.10,.10,.25,.25,.25,.25,
            .10,.10,.10,.10,.25,.25,.25,.25,
            .10,.10,.10,.10,.25,.25,.25,.25,
            .10,.10,.10,.10,.25,.25,.25,.25,
            .10,.10,.10,.10,.25,.25,.25,.25
        };
        private static readonly bool[] V74SequentialRequireDirectional = {
            false,false,true,true,false,false,true,true,
            false,false,true,true,false,false,true,true,
            false,false,true,true,false,false,true,true,
            false,false,true,true,false,false,true,true,
            false,false,true,true,false,false,true,true,
            false,false,true,true,false,false,true,true
        };
        private static readonly double[] V74SequentialDesiredRr = {
            3.5,3.5,3.5,3.5,3.5,3.5,3.5,3.5,
            4.0,4.0,4.0,4.0,4.0,4.0,4.0,4.0,
            3.5,3.5,3.5,3.5,3.5,3.5,3.5,3.5,
            4.0,4.0,4.0,4.0,4.0,4.0,4.0,4.0,
            3.5,3.5,3.5,3.5,3.5,3.5,3.5,3.5,
            4.0,4.0,4.0,4.0,4.0,4.0,4.0,4.0
        };
        private static readonly double[] V74SequentialPartialFraction = {
            .20,.30,.20,.30,.20,.30,.20,.30,
            .20,.30,.20,.30,.20,.30,.20,.30,
            .20,.30,.20,.30,.20,.30,.20,.30,
            .20,.30,.20,.30,.20,.30,.20,.30,
            .20,.30,.20,.30,.20,.30,.20,.30,
            .20,.30,.20,.30,.20,.30,.20,.30
        };
        private static readonly double[] V74SequentialTriggerR = {
            .05,.05,.05,.05,.05,.05,.05,.05,
            .05,.05,.05,.05,.05,.05,.05,.05,
            .10,.10,.10,.10,.10,.10,.10,.10,
            .10,.10,.10,.10,.10,.10,.10,.10,
            .15,.15,.15,.15,.15,.15,.15,.15,
            .15,.15,.15,.15,.15,.15,.15,.15
        };
        private static readonly double[] V74SequentialPartialHoldR = {
            .02,.02,.02,.02,.02,.02,.02,.02,
            .02,.02,.02,.02,.02,.02,.02,.02,
            .05,.05,.05,.05,.05,.05,.05,.05,
            .05,.05,.05,.05,.05,.05,.05,.05,
            .08,.08,.08,.08,.08,.08,.08,.08,
            .08,.08,.08,.08,.08,.08,.08,.08
        };
        private static readonly double[] V74SequentialAdverseCutR = {
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15,
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15,
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15,
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15,
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15,
            -.15,-.15,-.15,-.15,-.15,-.15,-.15,-.15
        };
        private static readonly string[] V74SequentialKey = {
            "M05_R025_H_RR35_F20","M05_R025_H_RR35_F30","M05_R025_D_RR35_F20","M05_R025_D_RR35_F30",
            "M05_R050_H_RR35_F20","M05_R050_H_RR35_F30","M05_R050_D_RR35_F20","M05_R050_D_RR35_F30",
            "M05_R025_H_RR40_F20","M05_R025_H_RR40_F30","M05_R025_D_RR40_F20","M05_R025_D_RR40_F30",
            "M05_R050_H_RR40_F20","M05_R050_H_RR40_F30","M05_R050_D_RR40_F20","M05_R050_D_RR40_F30",
            "M10_R025_H_RR35_F20","M10_R025_H_RR35_F30","M10_R025_D_RR35_F20","M10_R025_D_RR35_F30",
            "M10_R050_H_RR35_F20","M10_R050_H_RR35_F30","M10_R050_D_RR35_F20","M10_R050_D_RR35_F30",
            "M10_R025_H_RR40_F20","M10_R025_H_RR40_F30","M10_R025_D_RR40_F20","M10_R025_D_RR40_F30",
            "M10_R050_H_RR40_F20","M10_R050_H_RR40_F30","M10_R050_D_RR40_F20","M10_R050_D_RR40_F30",
            "M15_R025_H_RR35_F20","M15_R025_H_RR35_F30","M15_R025_D_RR35_F20","M15_R025_D_RR35_F30",
            "M15_R050_H_RR35_F20","M15_R050_H_RR35_F30","M15_R050_D_RR35_F20","M15_R050_D_RR35_F30",
            "M15_R025_H_RR40_F20","M15_R025_H_RR40_F30","M15_R025_D_RR40_F20","M15_R025_D_RR40_F30",
            "M15_R050_H_RR40_F20","M15_R050_H_RR40_F30","M15_R050_D_RR40_F20","M15_R050_D_RR40_F30"
        };


        // V74_LATE_ENTRY_TELEMETRY_SCHEMA_V2_2_REBUILD
        // True late-entry auction reuses the proven 48-route family/native payoff
        // geometry (M05/M10/M15 x R025/R050 x H/D x RR35/RR40 x F20/F30),
        // but moves capital admission to the completed-bar M-stage. Post-entry
        // F20/F30 crystallization is downstream execution only and can never feed
        // back into entry selection.
        private static readonly string[] V74LateAuctionKey = V74SequentialKey;
        private static readonly double[] V74LateAuctionStageR = V74SequentialTriggerR;
        private static readonly double[] V74LateAuctionStageHoldR = V74SequentialPartialHoldR;
        private static readonly double[] V74LateAuctionReactionR = V74SequentialReactionR;
        private static readonly double[] V74LateAuctionReactionHoldR = V74SequentialHoldR;
        private static readonly bool[] V74LateAuctionRequireDirectional = V74SequentialRequireDirectional;
        private static readonly double[] V74LateAuctionDesiredRr = V74SequentialDesiredRr;
        private static readonly double[] V74LateAuctionPartialFraction = V74SequentialPartialFraction;

        private sealed class V72HcogOpportunity
        {
            public string Id, SetupKey, Family, Hypotheses, Lane, Result;
            public PatternSignal Signal;
            public MtfConflict Conflict;
            public RegimeSnapshot Regime;
            public V72HcogState State;
            public bool Active = true, HasAbcdConfluence, StandaloneAbcd, CapitalSemantic, CoreOverlapAtEntry, CapitalQueued;
            public DateTime DetectedUtc, OverallExpiryUtc, ProofExpiryUtc, LastStageUtc, EntryUtc, FailureBreakUtc;
            public DateTime? PrzTouchUtc, ProofUtc;
            public TradeDirection Direction;
            public double LiquidityExtreme, BosBoundary, FailureBoundary, Entry, Stop, Target, RiskDistance, NetRr, MfeR, MaeR;
            public double HcapQ, HcapLcb, HcapHoldBars;
            public double ProofBodyAtr, ProofRejectionRatio, ProofSweepDepthAtr, ProofReclaimAtr, ProofBosAtr, ProofRetestAtr;
            public bool HcapSelected = true;
            public string HcapFeatureCsv = "", V74FeatureCsv = "", V74LiveProtectionKey = "NONE";
            public int BarsActive;
            public int[] V74ProtectionTriggerBar = Enumerable.Repeat(-1, 5).ToArray();
            public double[] V74ProtectionOutcomeR = Enumerable.Repeat(double.NaN, 5).ToArray();
            public string[] V74MilestoneFeatureCsv = new string[5];
            public int[] V74RcrReactionBar = Enumerable.Repeat(-1, 3).ToArray();
            public bool[] V74RcrActive = new bool[3];
            public int[] V74RcrBars = new int[3];
            public double[] V74RcrEntry = new double[3];
            public double[] V74RcrStop = new double[3];
            public double[] V74RcrTarget = new double[3];
            public double[] V74RcrRisk = new double[3];
            public double[] V74RcrNetRr = new double[3];
            public double[] V74RcrOutcomeR = Enumerable.Repeat(double.NaN, 3).ToArray();
            public double[] V74HybridOutcomeR = Enumerable.Repeat(double.NaN, 4).ToArray();
            public int[] V74ReactionCommitReactionBar = Enumerable.Repeat(-1, 4).ToArray();
            public bool[] V74ReactionCommitActive = new bool[4];
            public int[] V74ReactionCommitBars = new int[4];
            public int[] V74ReactionCommitStage = Enumerable.Repeat(-1, 4).ToArray();
            public int[] V74ReactionCommitStageBar = Enumerable.Repeat(-1, 4).ToArray();
            public double[] V74ReactionCommitEntry = new double[4];
            public double[] V74ReactionCommitStop = new double[4];
            public double[] V74ReactionCommitTarget = new double[4];
            public double[] V74ReactionCommitRisk = new double[4];
            public double[] V74ReactionCommitNetRr = new double[4];
            public double[] V74ReactionCommitOutcomeR = Enumerable.Repeat(double.NaN, 4).ToArray();
            public int[] V74HighConvictionReactionBar = Enumerable.Repeat(-1, 4).ToArray();
            public bool[] V74HighConvictionActive = new bool[4];
            public bool[] V74HighConvictionPositiveArmed = new bool[4];
            public double[] V74HighConvictionEntry = new double[4];
            public double[] V74HighConvictionStop = new double[4];
            public double[] V74HighConvictionTarget = new double[4];
            public double[] V74HighConvictionRisk = new double[4];
            public double[] V74HighConvictionNetRr = new double[4];
            public double[] V74HighConvictionOutcomeR = Enumerable.Repeat(double.NaN, 4).ToArray();
            public int[] V74SequentialReactionBar = Enumerable.Repeat(-1,V74SequentialKey.Length).ToArray();
            public int[] V74SequentialEntryBar = Enumerable.Repeat(-1,V74SequentialKey.Length).ToArray();
            public bool[] V74SequentialActive = new bool[V74SequentialKey.Length];
            public bool[] V74SequentialPositiveArmed = new bool[V74SequentialKey.Length];
            public int[] V74SequentialBars = new int[V74SequentialKey.Length];
            public int[] V74SequentialTriggerBar = Enumerable.Repeat(-1,V74SequentialKey.Length).ToArray();
            public int[] V74SequentialLockBar = Enumerable.Repeat(-1,V74SequentialKey.Length).ToArray();
            public double[] V74SequentialLockedR = new double[V74SequentialKey.Length];
            public double[] V74SequentialRouteMfeR = new double[V74SequentialKey.Length];
            public double[] V74SequentialRouteMaeR = new double[V74SequentialKey.Length];
            public double[] V74SequentialEntry = new double[V74SequentialKey.Length];
            public double[] V74SequentialStop = new double[V74SequentialKey.Length];
            public double[] V74SequentialTarget = new double[V74SequentialKey.Length];
            public double[] V74SequentialRisk = new double[V74SequentialKey.Length];
            public double[] V74SequentialNetRr = new double[V74SequentialKey.Length];
            public double[] V74SequentialOutcomeR = Enumerable.Repeat(double.NaN,V74SequentialKey.Length).ToArray();
            public string V74SequentialState025Csv = "", V74SequentialState050Csv = "";
            public string[] V74SequentialEntryStateCsv = new string[V74SequentialKey.Length];
            public string[] V74SequentialTriggerStateCsv = new string[V74SequentialKey.Length];
            public string[] V74SequentialDecisionStateCsv = new string[V74SequentialKey.Length];

            // True late-entry auction telemetry. Reaction/anchor/trigger bars are all
            // observed before capital entry. Outcome starts only after V74LateAuctionEntryBar.
            public int[] V74LateAuctionReactionBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public int[] V74LateAuctionAnchorBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public int[] V74LateAuctionTriggerBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public int[] V74LateAuctionEntryBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public bool[] V74LateAuctionPending = new bool[V74LateAuctionKey.Length];
            public bool[] V74LateAuctionActive = new bool[V74LateAuctionKey.Length];
            public int[] V74LateAuctionBars = new int[V74LateAuctionKey.Length];
            public double[] V74LateAuctionAnchorEntry = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionAnchorStop = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionAnchorRisk = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionAnchorMfeR = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionAnchorMaeR = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionEntry = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionStop = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionTarget = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionRisk = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionNetRr = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionOutcomeR = Enumerable.Repeat(double.NaN,V74LateAuctionKey.Length).ToArray();
            public string[] V74LateAuctionMaturityStateCsv = new string[V74LateAuctionKey.Length];
            public string[] V74LateAuctionEntryStateCsv = new string[V74LateAuctionKey.Length];

            public bool[] V74LateAuctionPositiveArmed = new bool[V74LateAuctionKey.Length];
            public int[] V74LateAuctionPostTriggerBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public int[] V74LateAuctionLockBar = Enumerable.Repeat(-1,V74LateAuctionKey.Length).ToArray();
            public double[] V74LateAuctionLockedR = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionRouteMfeR = new double[V74LateAuctionKey.Length];
            public double[] V74LateAuctionRouteMaeR = new double[V74LateAuctionKey.Length];

        }

        private readonly Dictionary<string,V72HcogOpportunity> _v72Hcog = new Dictionary<string,V72HcogOpportunity>(StringComparer.Ordinal);
        private readonly HashSet<string> _v72HcogSeen = new HashSet<string>(StringComparer.Ordinal);
        private readonly Dictionary<string,V72PayoffAccumulator> _v72HcogCensus = new Dictionary<string,V72PayoffAccumulator>(StringComparer.Ordinal);
        private readonly HashSet<string> _v72HcogPayoffSeen = new HashSet<string>(StringComparer.Ordinal);
        private int _v72HcogSeq, _v72HcogDetected, _v72HcogPrzTouched, _v72HcogProofs, _v72HcogArmed, _v72HcogClosed;
        private int _v72HcogFailureArmed, _v72HcogCoreOverlapAtEntry, _v72HcogAbcdPrimitive, _v72HcogCapitalQueued;

        private double V72HcogRatioResidual(double value,double lo,double hi)
        {
            if(hi<=0||hi<lo)return 0;
            if(!double.IsFinite(value)||value<=0)return 4.0;
            double mid=(lo+hi)*.5,half=Math.Max(.03,Math.Abs(hi-lo)*.5);
            return Math.Abs(value-mid)/half;
        }

        private double V72HcogGeometryLoss(PatternSignal s)
        {
            if(s==null||s.Profile==null)return 999;
            var p=s.Profile;double sum=0;int n=0;
            Action<double,double,double> add=(v,lo,hi)=>{if(hi<=0||hi<lo)return;sum+=V72HcogRatioResidual(v,lo,hi);n++;};
            add(s.Xab,p.XabMin,p.XabMax);add(s.Abc,p.AbcMin,p.AbcMax);add(s.Bcd,p.BcdMin,p.BcdMax);add(s.Xad,p.XadMin,p.XadMax);add(s.AbCd,p.AbcDMin,p.AbcDMax);
            return (n>0?sum/n:0)-.25*VClamp(s.GeometryQuality)-.25*VClamp(s.PrzConfluence);
        }

        private PatternSignal V72HcogSelectPrimary(List<PatternSignal> xs)
        {
            var parent=xs.Where(x=>!string.Equals(V71FamilyKey(x.PatternName),"ABCD",StringComparison.OrdinalIgnoreCase))
                .OrderBy(V72HcogGeometryLoss).ThenByDescending(x=>x.PrzConfluence).ThenByDescending(x=>x.GeometryQuality).FirstOrDefault();
            return parent??xs.OrderBy(V72HcogGeometryLoss).ThenByDescending(x=>x.PrzConfluence).ThenByDescending(x=>x.GeometryQuality).FirstOrDefault();
        }

        private void V72HcogTrackRawPool(IEnumerable<PatternSignal> pool,HarmonicState h4,HarmonicState h1,RegimeSnapshot regime)
        {
            if(!EnableV72HcogAlpha && !EnableV72HcapAlpha && !EnableV73OpportunityUniverse && !EnableV74ExternalPolicy && !EnableV74EmbeddedPolicy)return;
            foreach(var g in (pool??Enumerable.Empty<PatternSignal>()).Where(V71ExpansionIntegrity).GroupBy(BuildSetupGeometryKey))
            {
                string setup=g.Key;if(string.IsNullOrWhiteSpace(setup)||!_v72HcogSeen.Add(setup))continue;
                var xs=g.ToList();var s=V72HcogSelectPrimary(xs);if(s==null)continue;
                string fam=V71FamilyKey(s.PatternName);bool abcd=xs.Any(x=>V71FamilyKey(x.PatternName)=="ABCD");bool standalone=fam=="ABCD";
                if(abcd)_v72HcogAbcdPrimitive++;
                DateTime now=Server.Time.ToUniversalTime();
                var o=new V72HcogOpportunity{Id="HCOG-"+(++_v72HcogSeq).ToString("D7"),SetupKey=setup,Family=fam,
                    Hypotheses=string.Join(",",xs.Select(x=>V71FamilyKey(x.PatternName)).Distinct().OrderBy(x=>x)),Signal=s,
                    Conflict=ClassifyMtfConflict(s.Direction,h4,h1),Regime=regime,State=V72HcogState.WAIT_PRZ,DetectedUtc=now,
                    OverallExpiryUtc=now.AddMinutes(15.0*Math.Max(2,Math.Min(V71ExpansionTtlM15Bars,s.Profile.MaxAgeM15Bars))),
                    Direction=s.Direction,HasAbcdConfluence=abcd,StandaloneAbcd=standalone,CapitalSemantic=!standalone,
                    Lane=standalone?"HCOG_ABCD_STANDALONE_SHADOW":"HCOG_PENDING"};
                _v72Hcog[o.Id]=o;_v72HcogDetected++;
                if(!EnableV73OpportunityUniverse)Print("[V72-HCOG-DETECTED] id={0} setup={1} family={2} hypotheses={3} abcd={4} fitLoss={5:F6} conflict={6}",
                    o.Id,o.SetupKey,o.Family,o.Hypotheses,o.HasAbcdConfluence,V72HcogGeometryLoss(s),o.Conflict);
            }
        }

        private bool V72HcogStructuralBreak(int i,PatternSignal s)
        {
            double c=_m1Bars.ClosePrices[i];return s.Direction==TradeDirection.Buy?c<s.StructuralInvalidation:c>s.StructuralInvalidation;
        }

        private void V72HcogStartFailure(DateTime utc,V72HcogOpportunity o)
        {
            o.Direction=V72OppositeDirection(o.Signal.Direction);o.FailureBoundary=o.Signal.StructuralInvalidation;o.FailureBreakUtc=utc;
            o.ProofExpiryUtc=V72NextM15Boundary(utc).AddMinutes(15);if(o.ProofExpiryUtc>o.OverallExpiryUtc)o.ProofExpiryUtc=o.OverallExpiryUtc;
            o.LastStageUtc=utc;o.State=V72HcogState.FAILURE_WAIT_RETEST;
            if(!EnableV73OpportunityUniverse)Print("[V72-HCOG-FAILURE-BREAK] id={0} family={1} boundary={2:F5} dir={3} expiry={4:o}",o.Id,o.Family,o.FailureBoundary,o.Direction,o.ProofExpiryUtc);
        }

        private double[] V74ResearchFeatures(V72HcogOpportunity o)
        {
            var s=o==null?null:o.Signal;var r=o==null?null:o.Regime;
            if(s==null)return Enumerable.Repeat(0.0,46).ToArray();
            double atrPips=r==null?0.0:Math.Max(1e-9,r.AtrM15Pips);
            double riskPips=Math.Max(1e-9,PriceToPips(Math.Abs(o.Entry-o.Stop)));
            double targetPips=Math.Max(0.0,PriceToPips(Math.Abs(o.Target-o.Entry)));
            double przWidthPips=Math.Max(0.0,PriceToPips(Math.Abs(s.PrzHigh-s.PrzLow)));
            DateTime entryUtc=o.EntryUtc==default(DateTime)?Server.Time.ToUniversalTime():o.EntryUtc;
            double detectBars=Math.Max(0.0,(entryUtc-o.DetectedUtc).TotalMinutes/15.0);
            double touchBars=o.PrzTouchUtc.HasValue?Math.Max(0.0,(entryUtc-o.PrzTouchUtc.Value).TotalMinutes/15.0):detectBars;
            double completionBars=Math.Max(0.0,(entryUtc-s.CompletionTime.ToUniversalTime()).TotalMinutes/15.0);
            double liquidityR=0.0;
            if(o.RiskDistance>1e-12)
                liquidityR=o.Direction==TradeDirection.Buy?(o.Entry-o.LiquidityExtreme)/o.RiskDistance:(o.LiquidityExtreme-o.Entry)/o.RiskDistance;
            double bosR=o.RiskDistance>1e-12?Math.Abs(o.Entry-o.BosBoundary)/o.RiskDistance:0.0;
            var p=s.Profile;
            double rxab=p==null?4.0:V72HcogRatioResidual(s.Xab,p.XabMin,p.XabMax);
            double rabc=p==null?4.0:V72HcogRatioResidual(s.Abc,p.AbcMin,p.AbcMax);
            double rbcd=p==null?4.0:V72HcogRatioResidual(s.Bcd,p.BcdMin,p.BcdMax);
            double rxad=p==null?4.0:V72HcogRatioResidual(s.Xad,p.XadMin,p.XadMax);
            double rabcd=p==null?4.0:V72HcogRatioResidual(s.AbCd,p.AbcDMin,p.AbcDMax);
            double geometryLoss=Math.Max(0.0,V72HcogGeometryLoss(s));
            return new[]
            {
                VClamp(s.GeometryQuality),VClamp(s.PrzConfluence),VClamp(s.Confidence),
                VClamp(s.TimeSymmetry),VClamp(s.PivotQuality),VClamp(o.NetRr/4.0),
                r==null?0.0:VClamp(r.Efficiency),r==null?0.0:V71AtrFit(r),
                r==null?0.0:VClamp(r.ExtensionAtr/2.0),r==null?0.0:VClamp(r.TrendStrength),
                r==null?0.5:VClamp((r.AdxH1Slope+1.0)*0.5),V71MtfScore(o.Conflict),
                VClamp(s.Xab/1.5),VClamp(s.Abc/2.0),VClamp(s.Bcd/4.0),
                VClamp(s.Xad/2.0),VClamp(s.AbCd/3.0),VClamp(s.PivotScale/12.0),
                VClamp((przWidthPips/atrPips)/2.0),VClamp((riskPips/atrPips)/4.0),
                VClamp((targetPips/atrPips)/8.0),VClamp(detectBars/16.0),VClamp(touchBars/8.0),
                VClamp(Math.Max(0.0,liquidityR)/4.0),VClamp(bosR/2.0),
                r==null?0.0:VClamp(r.AtrRatio/3.0),r==null?0.0:VClamp(r.AtrPercentile),
                r==null?0.0:VClamp(r.AdxH1/60.0),r==null?0.0:VClamp(r.AdxH4/60.0),
                r!=null&&r.Transition?1.0:0.0,VClamp((ModeledCostPips()/riskPips)*4.0),
                o.Direction==TradeDirection.Buy?1.0:0.0,o.HasAbcdConfluence?1.0:0.0,
                VClamp(completionBars/16.0),VClamp(o.ProofBodyAtr/2.0),
                VClamp(o.ProofRejectionRatio/3.0),VClamp(o.ProofSweepDepthAtr/2.0),
                VClamp(o.ProofReclaimAtr/2.0),VClamp(o.ProofBosAtr/2.0),VClamp(o.ProofRetestAtr/2.0),
                VClamp(geometryLoss/4.0),VClamp(rxab/4.0),VClamp(rabc/4.0),
                VClamp(rbcd/4.0),VClamp(rxad/4.0),VClamp(rabcd/4.0)
            };
        }

        private bool V72HcogArm(DateTime utc,V72HcogOpportunity o,TradeDirection direction,double entry,double stop,double target,double rr,string lane)
        {
            if(direction==TradeDirection.Neutral||rr+1e-9<MinimumNetRR||!GeometryValid(direction,entry,stop,target))return false;
            double risk=Math.Abs(entry-stop);if(PriceToPips(risk)<MinStopLossPips)return false;
            o.Direction=direction;o.Entry=entry;o.Stop=stop;o.Target=target;o.RiskDistance=risk;o.NetRr=rr;o.EntryUtc=utc;o.ProofUtc=utc;o.State=V72HcogState.ACTIVE;
            o.Lane=o.StandaloneAbcd
                ? (lane=="HCOG_FAILURE_CONTINUATION"?"HCOG_ABCD_STANDALONE_CONTINUATION_SHADOW":"HCOG_ABCD_STANDALONE_REVERSAL_SHADOW")
                : lane;
            o.Regime=BuildRegimeSnapshot();
            o.V74FeatureCsv=string.Join(",",V74ResearchFeatures(o).Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
            if(EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)V74FrozenPolicyScoreOpportunity(o); else V72HcapScoreOpportunity(o);
            o.CoreOverlapAtEntry=V71CoreHasActiveThesis()||_activeSetupOwners.ContainsKey(o.SetupKey)||_executedSetupKeys.Contains(o.SetupKey);
            if(o.CoreOverlapAtEntry)_v72HcogCoreOverlapAtEntry++;_v72HcogProofs++;_v72HcogArmed++;if(lane=="HCOG_FAILURE_CONTINUATION")_v72HcogFailureArmed++;
            if(!EnableV73OpportunityUniverse)Print("[V72-HCOG-PROVED] id={0} family={1} lane={2} dir={3} entry={4:F5} stop={5:F5} target={6:F5} netRR={7:F4} coreOverlap={8} abcd={9}",
                o.Id,o.Family,o.Lane,o.Direction,o.Entry,o.Stop,o.Target,o.NetRr,o.CoreOverlapAtEntry,o.HasAbcdConfluence);
            bool v74StandaloneCapital=o.StandaloneAbcd&&(EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)&&o.HcapSelected;
            if((o.CapitalSemantic||v74StandaloneCapital)&&EnableV71ExpansionExecution&&((!EnableV72HcapAlpha&&!EnableV74ExternalPolicy&&!EnableV74EmbeddedPolicy)||o.HcapSelected))V72HcogQueueCapital(o,utc);
            return true;
        }

        private void V72HcogQueueCapital(V72HcogOpportunity o,DateTime utc)
        {
            if(o==null||o.CapitalQueued)return;
            bool v74StandaloneCapital=o.StandaloneAbcd&&(EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)&&o.HcapSelected;
            if(o.StandaloneAbcd&&!v74StandaloneCapital)return;
            DateTime exp=V72NextM15Boundary(utc).AddMinutes(15);if(exp>o.OverallExpiryUtc)exp=o.OverallExpiryUtc;if(exp<=utc.AddSeconds(1))return;
            string cid=((EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)?"V71EXP-V74-":(EnableV72HcapAlpha?"V71EXP-HCAP-":"V71EXP-HCOG-"))+o.Id.Substring(Math.Max(0,o.Id.Length-7));if(_v71Expansion.ContainsKey(cid))return;
            var e=new V71ExpansionCandidate{CandidateId=cid,IdentityKey=o.SetupKey+((EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)?"|V74":(EnableV72HcapAlpha?"|HCAP":"|HCOG")),SetupKey=o.SetupKey,Signal=o.Signal,Conflict=o.Conflict,
                Route=o.Lane=="HCOG_FAILURE_CONTINUATION"?HarmonicRoute.FAILURE_CONTINUATION:V71ExpansionRoute(o.Signal,o.Conflict,o.Regime),Regime=o.Regime,
                State=V71ExpansionState.ARMED,IsActive=true,DetectedUtc=o.DetectedUtc,ExpiryUtc=exp,PrzTouchUtc=o.PrzTouchUtc,ReactionProofUtc=o.ProofUtc,
                ConfirmationScore=1.0,NetRR=o.NetRr,EntryAnchor=o.Entry,StructuralStop=o.Stop,CanonicalTarget=o.Target,RiskDistance=o.RiskDistance,
                TargetR=Math.Abs(o.Target-o.Entry)/Math.Max(o.RiskDistance,_symbol.PipSize),CapitalDirection=o.Direction,CapitalEligible=true,CoreOverlapObserved=false,
                CapitalReady=true,AwaitingPullbackFill=true,PullbackFilled=false,PullbackExpiryUtc=exp,CapitalLane=o.Lane,
                AbcdRole=o.StandaloneAbcd?"ABCD_STANDALONE_OOF_PROVED":(o.HasAbcdConfluence?"PARENT_PLUS_ABCD_CONFLUENCE":"PARENT_FAMILY"),V74ProtectionKey=o.V74LiveProtectionKey,AsymmetryCompression=(EnableV72HcapAlpha||EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)?Math.Max(.0001,o.HcapLcb/Math.Max(.25,o.HcapHoldBars/60.0)):Math.Max(.10,Math.Abs(o.Signal.D.Price-o.Stop)/Math.Max(o.RiskDistance,_symbol.PipSize)),
                EdgeMean=(EnableV72HcapAlpha||EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)?o.HcapQ:o.NetRr,EdgeLcb=(EnableV72HcapAlpha||EnableV74ExternalPolicy||EnableV74EmbeddedPolicy)?o.HcapLcb:o.NetRr};
            _v71Expansion[cid]=e;_v71ExpansionDetected++;o.CapitalQueued=true;_v72HcogCapitalQueued++;
            Print("[V72-HCOG-CAPITAL-QUEUE] id={0} cid={1} setup={2} family={3} lane={4} expiry={5:o}",o.Id,cid,o.SetupKey,o.Family,o.Lane,exp);
        }

        private void V72HcogProcessFailureRetest(int i,DateTime utc,V72HcogOpportunity o)
        {
            if(utc<=o.FailureBreakUtc)return;if(utc>=o.ProofExpiryUtc){o.Active=false;o.State=V72HcogState.EXPIRED;return;}
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool touched=o.Direction==TradeDirection.Buy?low<=o.FailureBoundary:high>=o.FailureBoundary;
            bool side=o.Direction==TradeDirection.Buy?close>o.FailureBoundary:close<o.FailureBoundary;
            bool directional=o.Direction==TradeDirection.Buy?close>open:close<open;if(!(touched&&side&&directional))return;
            double buffer=Math.Max(PipsToPrice(ModeledCostPips()),_symbol.PipSize),entry=close;
            double stop=o.Direction==TradeDirection.Buy?Math.Min(low,o.FailureBoundary)-buffer:Math.Max(high,o.FailureBoundary)+buffer;
            double risk=Math.Abs(entry-stop);if(PriceToPips(risk)<MinStopLossPips)return;double cost=PipsToPrice(ModeledCostPips());
            double target=o.Direction==TradeDirection.Buy?entry+2.0*risk+cost:entry-2.0*risk-cost;
            double rr=(PriceToPips(Math.Abs(target-entry))-ModeledCostPips())/Math.Max(1e-9,PriceToPips(risk));
            double atr=Atr(_m1Bars,14,i);
            o.ProofBodyAtr=atr>0?Math.Abs(close-open)/atr:0.0;
            o.ProofRetestAtr=atr>0?Math.Abs(close-o.FailureBoundary)/atr:0.0;
            V72HcogArm(utc,o,o.Direction,entry,stop,target,rr,"HCOG_FAILURE_CONTINUATION");
        }

        private void V72HcogProcessProof(int i,DateTime utc,V72HcogOpportunity o)
        {
            if(utc>=o.ProofExpiryUtc){o.Active=false;o.State=V72HcogState.EXPIRED;return;}
            var s=o.Signal;double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            double pc=_m1Bars.ClosePrices[i-1],ph=Math.Max(_m1Bars.HighPrices[i-1],_m1Bars.HighPrices[i-2]),pl=Math.Min(_m1Bars.LowPrices[i-1],_m1Bars.LowPrices[i-2]);
            double body=Math.Max(Math.Abs(close-open),_symbol.PipSize),atr=Atr(_m1Bars,14,i);bool buy=s.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open,reclaim=buy?(close>s.PrzLow&&close>=pc):(close<s.PrzHigh&&close<=pc),bos=buy?close>ph:close<pl;
            double rejectionWick=buy?Math.Max(0,Math.Min(open,close)-low):Math.Max(0,high-Math.Max(open,close));
            double rejectionRatio=rejectionWick/Math.Max(body,_symbol.PipSize);
            double sweepDepth=buy?Math.Max(0,_m1Bars.LowPrices[i-1]-low):Math.Max(0,high-_m1Bars.HighPrices[i-1]);
            double sweepDepthAtr=atr>0?sweepDepth/atr:0.0;
            bool rejection=rejectionRatio>=.5;
            bool failed=buy?(low<_m1Bars.LowPrices[i-1]&&close>_m1Bars.LowPrices[i-1]):(high>_m1Bars.HighPrices[i-1]&&close<_m1Bars.HighPrices[i-1]);
            bool sweep=buy?low<_m1Bars.LowPrices[i-1]:high>_m1Bars.HighPrices[i-1];
            bool inside=close>=Math.Min(s.PrzLow,s.PrzHigh)&&close<=Math.Max(s.PrzLow,s.PrzHigh),displacement=atr>0&&body>=atr*.30;
            if(buy)o.LiquidityExtreme=o.LiquidityExtreme==0?low:Math.Min(o.LiquidityExtreme,low);else o.LiquidityExtreme=o.LiquidityExtreme==0?high:Math.Max(o.LiquidityExtreme,high);
            bool extension=o.Family=="AltBat"||o.Family=="Butterfly"||o.Family=="Crab"||o.Family=="DeepCrab";
            bool transition=o.Family=="Shark"||o.Family=="FiveZero";bool liquidity=extension?(sweep&&failed):(transition?failed:(rejection||failed));
            if(o.State==V72HcogState.WAIT_LIQUIDITY){if(!liquidity)return;o.ProofBodyAtr=atr>0?body/atr:0.0;o.ProofRejectionRatio=rejectionRatio;o.ProofSweepDepthAtr=sweepDepthAtr;o.LastStageUtc=utc;o.State=V72HcogState.WAIT_RECLAIM;return;}
            if(o.State==V72HcogState.WAIT_RECLAIM){if(utc<=o.LastStageUtc)return;bool pass=(extension||transition)?(reclaim||inside):reclaim;if(!pass)return;double reclaimDist=buy?Math.Max(0,close-s.PrzLow):Math.Max(0,s.PrzHigh-close);o.ProofReclaimAtr=atr>0?reclaimDist/atr:0.0;o.LastStageUtc=utc;o.State=V72HcogState.WAIT_BOS;return;}
            if(o.State==V72HcogState.WAIT_BOS){if(utc<=o.LastStageUtc)return;bool pass=transition?(bos&&directional):(bos&&displacement);if(!pass)return;o.BosBoundary=buy?ph:pl;o.ProofBosAtr=atr>0?Math.Abs(close-o.BosBoundary)/atr:0.0;o.ProofBodyAtr=Math.Max(o.ProofBodyAtr,atr>0?body/atr:0.0);o.LastStageUtc=utc;o.State=V72HcogState.WAIT_RETEST;return;}
            if(o.State==V72HcogState.WAIT_RETEST)
            {
                if(utc<=o.LastStageUtc)return;bool touched=buy?low<=o.BosBoundary:high>=o.BosBoundary,side=buy?close>o.BosBoundary:close<o.BosBoundary;
                if(!(touched&&side&&directional))return;o.ProofRetestAtr=atr>0?Math.Abs(close-o.BosBoundary)/atr:0.0;double buffer=Math.Max(PipsToPrice(ModeledCostPips()),_symbol.PipSize);
                double causalStop=buy?o.LiquidityExtreme-buffer:o.LiquidityExtreme+buffer,stop=buy?Math.Max(s.StructuralInvalidation,causalStop):Math.Min(s.StructuralInvalidation,causalStop);
                double target,rr;if(!SelectCanonicalBasketTarget(s,close,stop,out target,out rr))return;V72HcogArm(utc,o,s.Direction,close,stop,target,rr,"HCOG_REVERSAL");
            }
        }

        private void V72HcogRecord(V72HcogOpportunity o,double r)
        {
            string dedupe=o.SetupKey+"|"+o.Lane;if(!_v72HcogPayoffSeen.Add(dedupe))return;string key=o.Lane+"|"+o.Family;V72PayoffAccumulator z;
            if(!_v72HcogCensus.TryGetValue(key,out z)){z=new V72PayoffAccumulator();_v72HcogCensus[key]=z;}z.N++;z.SumR+=r;z.SumSqR+=r*r;
            if(r>0){z.GrossProfitR+=r;z.Wins++;}else if(r<0)z.GrossLossR+=-r;
        }

        private double[] V74MilestoneFeatures(V72HcogOpportunity o,int i,double milestoneR)
        {
            if(o==null||o.RiskDistance<=0||i<0||i>=_m1Bars.Count)return Enumerable.Repeat(0.0,12).ToArray();
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            double atr=Math.Max(_symbol.PipSize,Atr(_m1Bars,14,i)),body=Math.Max(_symbol.PipSize,Math.Abs(close-open));
            bool buy=o.Direction==TradeDirection.Buy;
            double closeR=(buy?close-o.Entry:o.Entry-close)/o.RiskDistance;
            double favWick=buy?Math.Max(0,high-Math.Max(open,close)):Math.Max(0,Math.Min(open,close)-low);
            double adverseWick=buy?Math.Max(0,Math.Min(open,close)-low):Math.Max(0,high-Math.Max(open,close));
            bool directional=buy?close>open:close<open;
            double remainingR=Math.Abs(o.Target-close)/Math.Max(o.RiskDistance,_symbol.PipSize);
            var rr=BuildRegimeSnapshot();
            return new[]
            {
                VClamp(milestoneR/2.0),
                VClamp(o.BarsActive/180.0),
                VClamp((closeR+1.0)/4.0),
                VClamp(o.MfeR/3.0),
                VClamp(o.MaeR/2.0),
                VClamp((body/atr)/2.0),
                VClamp((favWick/body)/3.0),
                VClamp((adverseWick/body)/3.0),
                VClamp(Math.Max(0.0,o.MfeR-closeR)/2.0),
                VClamp(remainingR/4.0),
                directional?1.0:0.0,
                rr==null?0.0:VClamp(rr.Efficiency)
            };
        }

        private double[] V74RouteStateFeatures(V72HcogOpportunity o,int i,double entry,double risk,double target,
            int bars,double mfeR,double maeR,double milestoneR)
        {
            const int FeatureCount=42;
            if(o==null||risk<=0||i<0||i>=_m1Bars.Count)return Enumerable.Repeat(0.0,FeatureCount).ToArray();
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            double atr=Math.Max(_symbol.PipSize,Atr(_m1Bars,14,i)),body=Math.Max(_symbol.PipSize,Math.Abs(close-open));
            bool buy=o.Direction==TradeDirection.Buy;
            double closeR=(buy?close-entry:entry-close)/risk;
            double favWick=buy?Math.Max(0,high-Math.Max(open,close)):Math.Max(0,Math.Min(open,close)-low);
            double adverseWick=buy?Math.Max(0,Math.Min(open,close)-low):Math.Max(0,high-Math.Max(open,close));
            double remainingR=Math.Abs(target-close)/Math.Max(risk,_symbol.PipSize);
            double mom3=0.0,mom5=0.0;
            if(i>=3){double p3=_m1Bars.ClosePrices[i-3];mom3=(buy?close-p3:p3-close)/atr;}
            if(i>=5){double p5=_m1Bars.ClosePrices[i-5];mom5=(buy?close-p5:p5-close)/atr;}
            double range=Math.Max(_symbol.PipSize,high-low);
            double alignedClose=buy?(close-low)/range:(high-close)/range;
            var rr=BuildRegimeSnapshot();
            DateTime utc=_m1Bars.OpenTimes[i].ToUniversalTime();
            double phase=(utc.Hour*60.0+utc.Minute)/1440.0;

            // V74 causal path-state v3: every term below is observable no later than
            // this completed M1 decision bar. No future MFE/MAE/outcome is referenced.
            double v1=0.0,prevV1=0.0,dir3=0.0,dir5=0.0,abs3=0.0,abs5=0.0,avgRange5=0.0;
            if(i>=1)
            {
                double p1=_m1Bars.ClosePrices[i-1];
                v1=(buy?close-p1:p1-close)/atr;
            }
            if(i>=2)
            {
                double p1=_m1Bars.ClosePrices[i-1],p2=_m1Bars.ClosePrices[i-2];
                prevV1=(buy?p1-p2:p2-p1)/atr;
            }
            for(int j=0;j<5;j++)
            {
                int ix=i-j;
                if(ix<1)break;
                double c0=_m1Bars.ClosePrices[ix],c1=_m1Bars.ClosePrices[ix-1];
                bool aligned=buy?c0>c1:c0<c1;
                if(j<3&&aligned)dir3+=1.0;
                if(aligned)dir5+=1.0;
                double step=Math.Abs(c0-c1);
                if(j<3)abs3+=step;
                abs5+=step;
                avgRange5+=Math.Max(_symbol.PipSize,_m1Bars.HighPrices[ix]-_m1Bars.LowPrices[ix]);
            }
            int n3=Math.Min(3,Math.Max(0,i)),n5=Math.Min(5,Math.Max(0,i));
            double pathEff3=i>=3?Math.Abs(close-_m1Bars.ClosePrices[i-3])/Math.Max(_symbol.PipSize,abs3):0.0;
            double pathEff5=i>=5?Math.Abs(close-_m1Bars.ClosePrices[i-5])/Math.Max(_symbol.PipSize,abs5):0.0;
            double rangeCompression=n5>0?range/Math.Max(_symbol.PipSize,avgRange5/n5):1.0;
            double sincePrz=o.PrzTouchUtc.HasValue?Math.Max(0.0,(utc-o.PrzTouchUtc.Value.ToUniversalTime()).TotalMinutes):0.0;
            double sinceProof=o.ProofUtc.HasValue?Math.Max(0.0,(utc-o.ProofUtc.Value.ToUniversalTime()).TotalMinutes):0.0;

            return new[]
            {
                VClamp(milestoneR),VClamp(bars/120.0),VClamp((closeR+1.0)/4.0),
                VClamp(mfeR/3.0),VClamp(maeR/2.0),VClamp((body/atr)/2.0),
                VClamp((favWick/body)/3.0),VClamp((adverseWick/body)/3.0),
                VClamp(Math.Max(0.0,mfeR-closeR)/2.0),VClamp(remainingR/4.0),
                (buy?close>open:close<open)?1.0:0.0,rr==null?0.0:VClamp(rr.Efficiency),
                VClamp((mom3+3.0)/6.0),VClamp((mom5+4.0)/8.0),VClamp((range/atr)/3.0),VClamp(alignedClose),
                rr==null?0.0:VClamp(rr.TrendStrength),rr==null?0.0:VClamp(rr.AdxH1/60.0),
                rr==null?0.0:VClamp(rr.AdxH4/60.0),rr==null?0.0:VClamp(rr.AtrPercentile),
                rr==null?0.0:VClamp(rr.AtrRatio/3.0),rr!=null&&rr.Transition?1.0:0.0,
                VClamp((Math.Sin(2.0*Math.PI*phase)+1.0)*0.5),
                VClamp((Math.Cos(2.0*Math.PI*phase)+1.0)*0.5),

                VClamp(o.ProofBodyAtr/3.0),
                VClamp(o.ProofRejectionRatio/4.0),
                VClamp(o.ProofSweepDepthAtr/3.0),
                VClamp(o.ProofReclaimAtr/3.0),
                VClamp(o.ProofBosAtr/3.0),
                VClamp(o.ProofRetestAtr/3.0),
                VClamp((v1+3.0)/6.0),
                VClamp(((v1-prevV1)+3.0)/6.0),
                VClamp(n3>0?dir3/n3:0.0),
                VClamp(n5>0?dir5/n5:0.0),
                VClamp(pathEff3),
                VClamp(pathEff5),
                VClamp(rangeCompression/2.0),
                VClamp(sincePrz/180.0),
                VClamp(sinceProof/120.0),
                o.HasAbcdConfluence?1.0:0.0,
                o.StandaloneAbcd?1.0:0.0,
                VClamp(Math.Max(0.0,mfeR-maeR+1.0)/4.0)
            };
        }

        private void V74PropagateProtectionDecision(V72HcogOpportunity o,string key)
        {
            if(o==null||string.IsNullOrWhiteSpace(key)||key=="NONE")return;
            string cid="V71EXP-V74-"+o.Id.Substring(Math.Max(0,o.Id.Length-7));
            V71ExpansionCandidate e;
            if(_v71Expansion.TryGetValue(cid,out e))e.V74ProtectionKey=key;
            foreach(var basket in _baskets.Values.Where(b=>b.IsActive&&b.CandidateId==cid).ToList())
            {
                basket.V74ProtectionKey=key;
                double triggerR,floorR;
                if(V74ProtectionLevels(key,out triggerR,out floorR))
                {
                    basket.V74ProtectionTriggerR=triggerR;
                    basket.V74ProtectionFloorR=floorR;
                }
            }
            Print("[V74-PROTECTION-DECISION] id={0} cid={1} setup={2} key={3}",o.Id,cid,o.SetupKey,key);
        }

        private void V74UpdateProtectionCounterfactuals(V72HcogOpportunity o,int i,bool stop,bool target)
        {
            if(o==null||o.RiskDistance<=0||i<0||i>=_m1Bars.Count)return;
            double high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            double fav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;
            for(int k=0;k<V74ProtectionTriggerR.Length;k++)
            {
                if(o.V74ProtectionTriggerBar[k]<0&&!stop&&fav+1e-12>=V74ProtectionTriggerR[k])
                {
                    o.V74ProtectionTriggerBar[k]=o.BarsActive;
                    double[] mf=V74MilestoneFeatures(o,i,V74ProtectionTriggerR[k]);
                    o.V74MilestoneFeatureCsv[k]=string.Join(",",mf
                        .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                    if(EnableV74EmbeddedPolicy&&o.V74LiveProtectionKey=="NONE")
                    {
                        bool handled=false,protect=false;double delta=0,lcb=-999;
                        V74EmbeddedProtect(o,k,mf,ref handled,ref protect,ref delta,ref lcb);
                        if(handled)
                        {
                            Print("[V74-EMBEDDED-PROTECT-SCORE] id={0} setupHash={1} key={2} delta={3:F9} lcb={4:F9} protect={5}",
                                o.Id,V74SetupHash(o.SetupKey),V74ProtectionKey[k],delta,lcb,protect);
                            if(protect)
                            {
                                o.V74LiveProtectionKey=V74ProtectionKey[k];
                                V74PropagateProtectionDecision(o,o.V74LiveProtectionKey);
                            }
                        }
                    }
                }
                if(o.V74ProtectionTriggerBar[k]<0||!double.IsNaN(o.V74ProtectionOutcomeR[k]))continue;
                if(o.BarsActive<=o.V74ProtectionTriggerBar[k])continue; // completed-bar activation: never same-bar protect
                double floor=o.Direction==TradeDirection.Buy
                    ?o.Entry+o.RiskDistance*V74ProtectionFloorR[k]
                    :o.Entry-o.RiskDistance*V74ProtectionFloorR[k];
                bool floorHit=buy?low<=floor:high>=floor;
                // Conservative OHLC ambiguity: if floor and target are both touched after activation, protection fires first.
                if(floorHit){o.V74ProtectionOutcomeR[k]=V74ProtectionFloorR[k];continue;}
                if(target){o.V74ProtectionOutcomeR[k]=o.NetRr;continue;}
                if(stop){o.V74ProtectionOutcomeR[k]=-1.0;continue;}
            }
        }


        private void V74UpdateReactionConfirmedReentry(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<0||i>=_m1Bars.Count)return;
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open;
            double fav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;
            for(int k=0;k<V74RcrKey.Length;k++)
            {
                if(o.V74RcrReactionBar[k]<0&&!nativeStop&&fav+1e-12>=V74RcrReactionR[k])
                {
                    o.V74RcrReactionBar[k]=o.BarsActive;
                    // RCR reaction is summarized once at finalization to preserve cTrader log budget.
                }
                if(double.IsFinite(o.V74RcrOutcomeR[k]))continue;
                if(!o.V74RcrActive[k])
                {
                    if(o.V74RcrReactionBar[k]<0||o.BarsActive<=o.V74RcrReactionBar[k]||nativeStop||nativeTarget)continue;
                    double retrace=buy?o.Entry+o.RiskDistance*V74RcrRetraceR[k]:o.Entry-o.RiskDistance*V74RcrRetraceR[k];
                    bool touched=buy?low<=retrace:high>=retrace;
                    bool side=buy?close>retrace:close<retrace;
                    if(!(touched&&side&&directional))continue;
                    double buffer=Math.Max(PipsToPrice(ModeledCostPips()),_symbol.PipSize);
                    double entry=close;
                    double localStop=buy?low-buffer:high+buffer;
                    double stop=buy?Math.Max(o.Stop,localStop):Math.Min(o.Stop,localStop);
                    double risk=Math.Abs(entry-stop);
                    if(PriceToPips(risk)<MinStopLossPips||!GeometryValid(o.Direction,entry,stop,o.Target))continue;
                    double rr=(PriceToPips(Math.Abs(o.Target-entry))-ModeledCostPips())/Math.Max(1e-9,PriceToPips(risk));
                    if(rr+1e-9<MinimumNetRR)continue;
                    o.V74RcrActive[k]=true;o.V74RcrEntry[k]=entry;o.V74RcrStop[k]=stop;o.V74RcrTarget[k]=o.Target;
                    o.V74RcrRisk[k]=risk;o.V74RcrNetRr[k]=rr;o.V74RcrBars[k]=0;
                    continue; // completed-bar entry: no same-bar outcome; summarized at finalization
                }
                o.V74RcrBars[k]++;
                bool stopHit=buy?low<=o.V74RcrStop[k]:high>=o.V74RcrStop[k];
                bool targetHit=buy?high>=o.V74RcrTarget[k]:low<=o.V74RcrTarget[k];
                if(stopHit){o.V74RcrOutcomeR[k]=-1.0;o.V74RcrActive[k]=false;continue;} // conservative if both
                if(targetHit){o.V74RcrOutcomeR[k]=o.V74RcrNetRr[k];o.V74RcrActive[k]=false;continue;}
            }
        }

        private void V74UpdateHybridSurvivalFrontiers(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<0||i>=_m1Bars.Count)return;
            double high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i],close=_m1Bars.ClosePrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            double closeR=(buy?close-o.Entry:o.Entry-close)/o.RiskDistance;
            for(int p=0;p<V74HybridKey.Length;p++)
            {
                if(double.IsFinite(o.V74HybridOutcomeR[p]))continue;
                // Native stop/target has priority on the bar it occurs. This avoids assuming
                // an intrabar ordering that completed-bar logic cannot observe.
                if(nativeStop){o.V74HybridOutcomeR[p]=-1.0;continue;}
                if(nativeTarget){o.V74HybridOutcomeR[p]=o.NetRr;continue;}

                int stage=-1;
                for(int k=0;k<V74ProtectionTriggerBarLength(o);k++)
                    if(o.V74ProtectionTriggerBar[k]>=0&&o.BarsActive>o.V74ProtectionTriggerBar[k])stage=k;

                if(stage<0)
                {
                    // Early adverse cut is evaluated only at a completed M1 close and only
                    // before a positive-reaction milestone has armed. It can never widen risk.
                    if(closeR<=V74HybridAdverseCutR[p])
                        o.V74HybridOutcomeR[p]=Math.Max(-1.0,closeR);
                    continue;
                }

                double floor=buy
                    ?o.Entry+o.RiskDistance*V74ProtectionFloorR[stage]
                    :o.Entry-o.RiskDistance*V74ProtectionFloorR[stage];
                bool floorHit=buy?low<=floor:high>=floor;
                // Conservative ambiguity: if a floor and a later favorable excursion share
                // one bar, the already-armed protective floor is assumed to fire first.
                if(floorHit)o.V74HybridOutcomeR[p]=V74ProtectionFloorR[stage];
            }
        }

        private void V74UpdateReactionCommitLadders(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<1||i>=_m1Bars.Count)return;
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open;
            double virtualFav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;

            for(int k=0;k<V74ReactionCommitKey.Length;k++)
            {
                if(double.IsFinite(o.V74ReactionCommitOutcomeR[k]))continue;

                if(o.V74ReactionCommitReactionBar[k]<0&&!nativeStop&&virtualFav+1e-12>=V74ReactionCommitR[k])
                {
                    o.V74ReactionCommitReactionBar[k]=o.BarsActive;
                    continue; // reaction bar itself is observation only; capital cannot enter same bar
                }

                if(!o.V74ReactionCommitActive[k])
                {
                    if(o.V74ReactionCommitReactionBar[k]<0||o.BarsActive<=o.V74ReactionCommitReactionBar[k]||nativeStop||nativeTarget)continue;
                    double holdR=Math.Max(0.0,V74ReactionCommitR[k]-.25);
                    double holdPrice=buy?o.Entry+o.RiskDistance*holdR:o.Entry-o.RiskDistance*holdR;
                    bool holds=buy?close>holdPrice:close<holdPrice;
                    if(!(holds&&directional))continue;

                    double entry=close;
                    double stop=buy?o.Entry+o.RiskDistance*V74ReactionCommitStopFloorR[k]
                                   :o.Entry-o.RiskDistance*V74ReactionCommitStopFloorR[k];
                    double risk=Math.Abs(entry-stop);
                    if(PriceToPips(risk)<MinStopLossPips||!GeometryValid(o.Direction,entry,stop,o.Target))continue;
                    double rr=(PriceToPips(Math.Abs(o.Target-entry))-ModeledCostPips())/Math.Max(1e-9,PriceToPips(risk));
                    if(rr+1e-9<2.30)continue;

                    o.V74ReactionCommitActive[k]=true;
                    o.V74ReactionCommitEntry[k]=entry;o.V74ReactionCommitStop[k]=stop;o.V74ReactionCommitTarget[k]=o.Target;
                    o.V74ReactionCommitRisk[k]=risk;o.V74ReactionCommitNetRr[k]=rr;o.V74ReactionCommitBars[k]=0;
                    o.V74ReactionCommitStage[k]=-1;o.V74ReactionCommitStageBar[k]=-1;
                    continue;
                }

                o.V74ReactionCommitBars[k]++;
                double entryR=(buy?close-o.V74ReactionCommitEntry[k]:o.V74ReactionCommitEntry[k]-close)/o.V74ReactionCommitRisk[k];
                double favR=buy?(high-o.V74ReactionCommitEntry[k])/o.V74ReactionCommitRisk[k]
                               :(o.V74ReactionCommitEntry[k]-low)/o.V74ReactionCommitRisk[k];
                bool stopHit=buy?low<=o.V74ReactionCommitStop[k]:high>=o.V74ReactionCommitStop[k];
                bool targetHit=buy?high>=o.V74ReactionCommitTarget[k]:low<=o.V74ReactionCommitTarget[k];

                int newStage=o.V74ReactionCommitStage[k];
                for(int s=0;s<V74ReactionCommitStageR.Length;s++)
                    if(favR+1e-12>=V74ReactionCommitStageR[s])newStage=s;
                if(newStage>o.V74ReactionCommitStage[k])
                {
                    o.V74ReactionCommitStage[k]=newStage;
                    o.V74ReactionCommitStageBar[k]=o.V74ReactionCommitBars[k];
                }

                int stage=o.V74ReactionCommitStage[k];
                if(stage>=0&&o.V74ReactionCommitBars[k]>o.V74ReactionCommitStageBar[k])
                {
                    double floor=buy?o.V74ReactionCommitEntry[k]+o.V74ReactionCommitRisk[k]*V74ReactionCommitFloorR[stage]
                                    :o.V74ReactionCommitEntry[k]-o.V74ReactionCommitRisk[k]*V74ReactionCommitFloorR[stage];
                    bool floorHit=buy?low<=floor:high>=floor;
                    if(floorHit){o.V74ReactionCommitOutcomeR[k]=V74ReactionCommitFloorR[stage];o.V74ReactionCommitActive[k]=false;continue;}
                }

                // Existing broker stop/target orders resolve before a close-only early-adverse decision.
                if(stopHit){o.V74ReactionCommitOutcomeR[k]=-1.0;o.V74ReactionCommitActive[k]=false;continue;}
                if(targetHit){o.V74ReactionCommitOutcomeR[k]=o.V74ReactionCommitNetRr[k];o.V74ReactionCommitActive[k]=false;continue;}
                if(stage<0&&entryR<=V74ReactionCommitAdverseCutR[k])
                {
                    o.V74ReactionCommitOutcomeR[k]=Math.Max(-1.0,entryR);
                    o.V74ReactionCommitActive[k]=false;
                }
            }
        }

        private void V74FinalizeReactionCommitLadders(V72HcogOpportunity o,double close)
        {
            if(o==null)return;
            for(int k=0;k<V74ReactionCommitKey.Length;k++)
            {
                if(double.IsFinite(o.V74ReactionCommitOutcomeR[k])||!o.V74ReactionCommitActive[k]||o.V74ReactionCommitRisk[k]<=0)continue;
                double closeR=(o.Direction==TradeDirection.Buy?close-o.V74ReactionCommitEntry[k]:o.V74ReactionCommitEntry[k]-close)/o.V74ReactionCommitRisk[k];
                o.V74ReactionCommitOutcomeR[k]=Math.Max(-1.0,Math.Min(o.V74ReactionCommitNetRr[k],closeR));
                o.V74ReactionCommitActive[k]=false;
            }
        }

        private void V74UpdateHighConvictionDelayedCommit(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<1||i>=_m1Bars.Count)return;
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open;
            double virtualFav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;
            double virtualCloseR=(buy?close-o.Entry:o.Entry-close)/o.RiskDistance;

            for(int k=0;k<V74HighConvictionKey.Length;k++)
            {
                if(double.IsFinite(o.V74HighConvictionOutcomeR[k]))continue;
                if(o.V74HighConvictionReactionBar[k]<0&&!nativeStop&&!nativeTarget&&virtualFav+1e-12>=V74HighConvictionReactionR[k])
                {
                    o.V74HighConvictionReactionBar[k]=o.BarsActive;
                    continue; // reaction bar is observation only; no same-bar capital
                }

                if(!o.V74HighConvictionActive[k])
                {
                    if(o.V74HighConvictionReactionBar[k]<0||o.BarsActive<=o.V74HighConvictionReactionBar[k]||nativeStop||nativeTarget)continue;
                    double holdR=V74HighConvictionReactionR[k]-.25;
                    if(virtualCloseR+1e-12<holdR)continue;
                    if(V74HighConvictionRequireDirectional[k]&&!directional)continue;

                    double buffer=Math.Max(PipsToPrice(ModeledCostPips()),_symbol.PipSize);
                    double entry=close;
                    double stop=buy?low-buffer:high+buffer; // completed-bar micro invalidation
                    double risk=Math.Abs(entry-stop);
                    if(PriceToPips(risk)<MinStopLossPips||!GeometryValid(o.Direction,entry,stop,o.Target))continue;
                    double rr=(PriceToPips(Math.Abs(o.Target-entry))-ModeledCostPips())/Math.Max(1e-9,PriceToPips(risk));
                    if(rr+1e-9<2.30)continue;

                    o.V74HighConvictionActive[k]=true;
                    o.V74HighConvictionEntry[k]=entry;o.V74HighConvictionStop[k]=stop;o.V74HighConvictionTarget[k]=o.Target;
                    o.V74HighConvictionRisk[k]=risk;o.V74HighConvictionNetRr[k]=rr;o.V74HighConvictionPositiveArmed[k]=false;
                    continue;
                }

                double routeFav=buy?(high-o.V74HighConvictionEntry[k])/o.V74HighConvictionRisk[k]
                                   :(o.V74HighConvictionEntry[k]-low)/o.V74HighConvictionRisk[k];
                double routeCloseR=(buy?close-o.V74HighConvictionEntry[k]:o.V74HighConvictionEntry[k]-close)/o.V74HighConvictionRisk[k];
                if(routeFav+1e-12>=.25)o.V74HighConvictionPositiveArmed[k]=true;

                bool stopHit=buy?low<=o.V74HighConvictionStop[k]:high>=o.V74HighConvictionStop[k];
                bool targetHit=buy?high>=o.V74HighConvictionTarget[k]:low<=o.V74HighConvictionTarget[k];
                if(stopHit){o.V74HighConvictionOutcomeR[k]=-1.0;o.V74HighConvictionActive[k]=false;continue;}
                if(targetHit){o.V74HighConvictionOutcomeR[k]=o.V74HighConvictionNetRr[k];o.V74HighConvictionActive[k]=false;continue;}

                // Before the live trade proves +0.25R, cut a completed-close adverse move.
                // This only reduces loss magnitude; it never converts a loser into a fake win.
                if(!o.V74HighConvictionPositiveArmed[k]&&routeCloseR<=-.25)
                {
                    o.V74HighConvictionOutcomeR[k]=Math.Max(-1.0,routeCloseR);
                    o.V74HighConvictionActive[k]=false;
                }
            }
        }

        private void V74UpdateCausalSequentialDelayedCommit(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<1||i>=_m1Bars.Count)return;
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open;
            double virtualFav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;
            double virtualCloseR=(buy?close-o.Entry:o.Entry-close)/o.RiskDistance;

            for(int k=0;k<V74SequentialKey.Length;k++)
            {
                if(double.IsFinite(o.V74SequentialOutcomeR[k]))continue;
                double reactionR=V74SequentialReactionR[k];
                if(o.V74SequentialReactionBar[k]<0&&!nativeStop&&!nativeTarget&&virtualFav+1e-12>=reactionR)
                {
                    o.V74SequentialReactionBar[k]=o.BarsActive;
                    string state=string.Join(",",V74RouteStateFeatures(o,i,o.Entry,o.RiskDistance,o.Target,o.BarsActive,o.MfeR,o.MaeR,reactionR).Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                    if(reactionR<.40&&string.IsNullOrWhiteSpace(o.V74SequentialState025Csv))o.V74SequentialState025Csv=state;
                    if(reactionR>=.40&&string.IsNullOrWhiteSpace(o.V74SequentialState050Csv))o.V74SequentialState050Csv=state;
                    continue;
                }
                if(!o.V74SequentialActive[k])
                {
                    if(o.V74SequentialReactionBar[k]<0||o.BarsActive<=o.V74SequentialReactionBar[k]||nativeStop||nativeTarget)continue;
                    if(virtualCloseR+1e-12<V74SequentialHoldR[k])continue;
                    if(V74SequentialRequireDirectional[k]&&!directional)continue;
                    double entry=close,netTargetPips=PriceToPips(Math.Abs(o.Target-entry))-ModeledCostPips();
                    if(netTargetPips<=0)continue;
                    double desiredRisk=PipsToPrice(netTargetPips/Math.Max(2.30,V74SequentialDesiredRr[k]));
                    double desiredStop=buy?entry-desiredRisk:entry+desiredRisk;
                    double stop=buy?Math.Max(o.Stop,desiredStop):Math.Min(o.Stop,desiredStop);
                    double risk=Math.Abs(entry-stop);
                    if(PriceToPips(risk)<MinStopLossPips||!GeometryValid(o.Direction,entry,stop,o.Target))continue;
                    double rr=netTargetPips/Math.Max(1e-9,PriceToPips(risk));if(rr+1e-9<2.30)continue;
                    o.V74SequentialActive[k]=true;o.V74SequentialEntryBar[k]=o.BarsActive;o.V74SequentialEntry[k]=entry;o.V74SequentialStop[k]=stop;o.V74SequentialTarget[k]=o.Target;
                    o.V74SequentialRisk[k]=risk;o.V74SequentialNetRr[k]=rr;o.V74SequentialBars[k]=0;o.V74SequentialTriggerBar[k]=-1;
                    o.V74SequentialLockBar[k]=-1;o.V74SequentialLockedR[k]=0;o.V74SequentialRouteMfeR[k]=0;o.V74SequentialRouteMaeR[k]=0;
                    o.V74SequentialPositiveArmed[k]=false;
                    o.V74SequentialEntryStateCsv[k]=string.Join(",",V74RouteStateFeatures(o,i,entry,risk,o.Target,0,0,0,reactionR)
                        .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                    continue;
                }
                o.V74SequentialBars[k]++;
                double ce=o.V74SequentialEntry[k],cr=o.V74SequentialRisk[k];
                double routeFav=buy?(high-ce)/cr:(ce-low)/cr,routeAdv=buy?(ce-low)/cr:(high-ce)/cr;
                double routeCloseR=(buy?close-ce:ce-close)/cr;
                o.V74SequentialRouteMfeR[k]=Math.Max(o.V74SequentialRouteMfeR[k],routeFav);
                o.V74SequentialRouteMaeR[k]=Math.Max(o.V74SequentialRouteMaeR[k],routeAdv);
                if(o.V74SequentialPositiveArmed[k]&&o.V74SequentialBars[k]>o.V74SequentialLockBar[k])
                {
                    // Run #74 proved that an intrabar BE runner preserves positive-basket
                    // supply but destroys too much right-tail payoff. Keep the original
                    // structural stop and canonical target as real intrabar orders, while
                    // the runner frontier is evaluated only on a later COMPLETED M1 close.
                    // Ambiguous stop+target remains stop-first conservative.
                    double remain=1.0-V74SequentialPartialFraction[k];
                    bool runnerStop=buy?low<=o.V74SequentialStop[k]:high>=o.V74SequentialStop[k];
                    bool runnerTarget=buy?high>=o.V74SequentialTarget[k]:low<=o.V74SequentialTarget[k];
                    if(runnerStop){o.V74SequentialOutcomeR[k]=o.V74SequentialLockedR[k]-remain;o.V74SequentialActive[k]=false;continue;}
                    if(runnerTarget){o.V74SequentialOutcomeR[k]=o.V74SequentialLockedR[k]+remain*o.V74SequentialNetRr[k];o.V74SequentialActive[k]=false;continue;}
                    if(routeCloseR<0.0)
                    {
                        double runnerR=Math.Max(-1.0,Math.Min(o.V74SequentialNetRr[k],routeCloseR));
                        o.V74SequentialOutcomeR[k]=o.V74SequentialLockedR[k]+remain*runnerR;
                        o.V74SequentialActive[k]=false;continue;
                    }
                    continue;
                }
                bool stopHit=buy?low<=o.V74SequentialStop[k]:high>=o.V74SequentialStop[k],targetHit=buy?high>=o.V74SequentialTarget[k]:low<=o.V74SequentialTarget[k];
                if(stopHit){o.V74SequentialOutcomeR[k]=-1.0;o.V74SequentialActive[k]=false;continue;}
                if(targetHit){o.V74SequentialOutcomeR[k]=o.V74SequentialNetRr[k];o.V74SequentialActive[k]=false;continue;}
                if(routeCloseR<=V74SequentialAdverseCutR[k]){o.V74SequentialOutcomeR[k]=Math.Max(-1.0,routeCloseR);o.V74SequentialActive[k]=false;continue;}
                if(o.V74SequentialTriggerBar[k]<0&&routeFav+1e-12>=V74SequentialTriggerR[k])
                {
                    o.V74SequentialTriggerBar[k]=o.V74SequentialBars[k];
                    o.V74SequentialTriggerStateCsv[k]=string.Join(",",V74RouteStateFeatures(o,i,ce,cr,o.V74SequentialTarget[k],o.V74SequentialBars[k],
                        o.V74SequentialRouteMfeR[k],o.V74SequentialRouteMaeR[k],V74SequentialTriggerR[k])
                        .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                    continue;
                }
                if(o.V74SequentialTriggerBar[k]>=0&&o.V74SequentialBars[k]>o.V74SequentialTriggerBar[k]&&routeCloseR+1e-12>=V74SequentialPartialHoldR[k])
                {
                    o.V74SequentialDecisionStateCsv[k]=string.Join(",",V74RouteStateFeatures(o,i,ce,cr,o.V74SequentialTarget[k],o.V74SequentialBars[k],
                        o.V74SequentialRouteMfeR[k],o.V74SequentialRouteMaeR[k],routeCloseR)
                        .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                    double fraction=V74SequentialPartialFraction[k];o.V74SequentialLockedR[k]=fraction*routeCloseR;
                    o.V74SequentialPositiveArmed[k]=true;o.V74SequentialLockBar[k]=o.V74SequentialBars[k];
                }
            }
        }


        private void V74UpdateTrueLateEntryAuction(V72HcogOpportunity o,int i,bool nativeStop,bool nativeTarget)
        {
            if(o==null||o.RiskDistance<=0||i<1||i>=_m1Bars.Count)return;
            double open=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool buy=o.Direction==TradeDirection.Buy;
            bool directional=buy?close>open:close<open;
            double virtualFav=buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance;
            double virtualCloseR=(buy?close-o.Entry:o.Entry-close)/o.RiskDistance;

            for(int k=0;k<V74LateAuctionKey.Length;k++)
            {
                if(double.IsFinite(o.V74LateAuctionOutcomeR[k]))continue;

                // Capital exists only after the legal M-stage decision. From that point
                // onward resolve this route independently of the native shadow thesis.
                if(o.V74LateAuctionActive[k])
                {
                    o.V74LateAuctionBars[k]++;
                    double ae=o.V74LateAuctionEntry[k],ar=o.V74LateAuctionRisk[k];
                    double routeFav=buy?(high-ae)/ar:(ae-low)/ar;
                    double routeAdv=buy?(ae-low)/ar:(high-ae)/ar;
                    double routeCloseR=(buy?close-ae:ae-close)/ar;
                    o.V74LateAuctionRouteMfeR[k]=Math.Max(o.V74LateAuctionRouteMfeR[k],routeFav);
                    o.V74LateAuctionRouteMaeR[k]=Math.Max(o.V74LateAuctionRouteMaeR[k],routeAdv);

                    if(o.V74LateAuctionPositiveArmed[k]&&o.V74LateAuctionBars[k]>o.V74LateAuctionLockBar[k])
                    {
                        double remain=1.0-V74LateAuctionPartialFraction[k];
                        bool runnerStop=buy?low<=o.V74LateAuctionStop[k]:high>=o.V74LateAuctionStop[k];
                        bool runnerTarget=buy?high>=o.V74LateAuctionTarget[k]:low<=o.V74LateAuctionTarget[k];
                        // Conservative OHLC ambiguity: structural stop precedes target.
                        if(runnerStop){o.V74LateAuctionOutcomeR[k]=o.V74LateAuctionLockedR[k]-remain;o.V74LateAuctionActive[k]=false;continue;}
                        if(runnerTarget){o.V74LateAuctionOutcomeR[k]=o.V74LateAuctionLockedR[k]+remain*o.V74LateAuctionNetRr[k];o.V74LateAuctionActive[k]=false;continue;}
                        if(routeCloseR<0.0)
                        {
                            double runnerR=Math.Max(-1.0,Math.Min(o.V74LateAuctionNetRr[k],routeCloseR));
                            o.V74LateAuctionOutcomeR[k]=o.V74LateAuctionLockedR[k]+remain*runnerR;
                            o.V74LateAuctionActive[k]=false;
                        }
                        continue;
                    }

                    bool stopHit=buy?low<=o.V74LateAuctionStop[k]:high>=o.V74LateAuctionStop[k];
                    bool targetHit=buy?high>=o.V74LateAuctionTarget[k]:low<=o.V74LateAuctionTarget[k];
                    if(stopHit){o.V74LateAuctionOutcomeR[k]=-1.0;o.V74LateAuctionActive[k]=false;continue;}
                    if(targetHit){o.V74LateAuctionOutcomeR[k]=o.V74LateAuctionNetRr[k];o.V74LateAuctionActive[k]=false;continue;}
                    if(routeCloseR<=-.15){o.V74LateAuctionOutcomeR[k]=Math.Max(-1.0,routeCloseR);o.V74LateAuctionActive[k]=false;continue;}

                    // Profit capture is strictly post-entry. Its state is never emitted as
                    // an admission feature and cannot affect the M-stage entry decision.
                    if(o.V74LateAuctionPostTriggerBar[k]<0&&routeFav+1e-12>=V74LateAuctionStageR[k])
                    {
                        o.V74LateAuctionPostTriggerBar[k]=o.V74LateAuctionBars[k];
                        continue;
                    }
                    if(o.V74LateAuctionPostTriggerBar[k]>=0&&
                       o.V74LateAuctionBars[k]>o.V74LateAuctionPostTriggerBar[k]&&
                       routeCloseR+1e-12>=V74LateAuctionStageHoldR[k])
                    {
                        double fraction=V74LateAuctionPartialFraction[k];
                        o.V74LateAuctionLockedR[k]=fraction*routeCloseR;
                        o.V74LateAuctionPositiveArmed[k]=true;
                        o.V74LateAuctionLockBar[k]=o.V74LateAuctionBars[k];
                    }
                    continue;
                }

                // Before entry this arm has zero capital. A dead native thesis cannot
                // spawn a hindsight trade.
                if(nativeStop||nativeTarget)
                {
                    o.V74LateAuctionPending[k]=false;
                    continue;
                }

                if(o.V74LateAuctionReactionBar[k]<0)
                {
                    if(virtualFav+1e-12>=V74LateAuctionReactionR[k])
                        o.V74LateAuctionReactionBar[k]=o.BarsActive;
                    continue; // reaction bar itself is observation only
                }

                if(!o.V74LateAuctionPending[k])
                {
                    if(o.BarsActive<=o.V74LateAuctionReactionBar[k])continue;
                    if(virtualCloseR+1e-12<V74LateAuctionReactionHoldR[k])continue;
                    if(V74LateAuctionRequireDirectional[k]&&!directional)continue;

                    // Freeze an observable no-capital anchor using the same canonical target
                    // and desired RR geometry. M05/M10/M15 maturity is measured from here.
                    double anchorEntry=close;
                    double netTargetPips=PriceToPips(Math.Abs(o.Target-anchorEntry))-ModeledCostPips();
                    if(netTargetPips<=0)continue;
                    double desiredRisk=PipsToPrice(netTargetPips/Math.Max(2.30,V74LateAuctionDesiredRr[k]));
                    double desiredStop=buy?anchorEntry-desiredRisk:anchorEntry+desiredRisk;
                    double anchorStop=buy?Math.Max(o.Stop,desiredStop):Math.Min(o.Stop,desiredStop);
                    double anchorRisk=Math.Abs(anchorEntry-anchorStop);
                    if(PriceToPips(anchorRisk)<MinStopLossPips||!GeometryValid(o.Direction,anchorEntry,anchorStop,o.Target))continue;

                    o.V74LateAuctionPending[k]=true;o.V74LateAuctionAnchorBar[k]=o.BarsActive;
                    o.V74LateAuctionAnchorEntry[k]=anchorEntry;o.V74LateAuctionAnchorStop[k]=anchorStop;o.V74LateAuctionAnchorRisk[k]=anchorRisk;
                    o.V74LateAuctionAnchorMfeR[k]=0;o.V74LateAuctionAnchorMaeR[k]=0;o.V74LateAuctionTriggerBar[k]=-1;
                    continue;
                }

                double ce=o.V74LateAuctionAnchorEntry[k],cr=o.V74LateAuctionAnchorRisk[k];
                if(cr<=0){o.V74LateAuctionPending[k]=false;continue;}
                double anchorFav=buy?(high-ce)/cr:(ce-low)/cr;
                double anchorAdv=buy?(ce-low)/cr:(high-ce)/cr;
                double anchorCloseR=(buy?close-ce:ce-close)/cr;
                o.V74LateAuctionAnchorMfeR[k]=Math.Max(o.V74LateAuctionAnchorMfeR[k],anchorFav);
                o.V74LateAuctionAnchorMaeR[k]=Math.Max(o.V74LateAuctionAnchorMaeR[k],anchorAdv);

                if(o.V74LateAuctionTriggerBar[k]<0)
                {
                    if(anchorFav+1e-12>=V74LateAuctionStageR[k])
                        o.V74LateAuctionTriggerBar[k]=o.BarsActive;
                    continue; // first-passage bar itself is observation only
                }
                if(o.BarsActive<=o.V74LateAuctionTriggerBar[k]||anchorCloseR+1e-12<V74LateAuctionStageHoldR[k])continue;

                // Legal auction decision: state exists on a completed M1 bar while this
                // arm still holds zero capital.
                o.V74LateAuctionMaturityStateCsv[k]=string.Join(",",V74RouteStateFeatures(
                    o,i,ce,cr,o.Target,Math.Max(0,o.BarsActive-o.V74LateAuctionAnchorBar[k]),
                    o.V74LateAuctionAnchorMfeR[k],o.V74LateAuctionAnchorMaeR[k],V74LateAuctionStageR[k])
                    .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));

                double entry=close,lateNetTargetPips=PriceToPips(Math.Abs(o.Target-entry))-ModeledCostPips();
                if(lateNetTargetPips<=0)continue;
                double lateDesiredRisk=PipsToPrice(lateNetTargetPips/Math.Max(2.30,V74LateAuctionDesiredRr[k]));
                double lateDesiredStop=buy?entry-lateDesiredRisk:entry+lateDesiredRisk;
                double stop=buy?Math.Max(o.Stop,lateDesiredStop):Math.Min(o.Stop,lateDesiredStop);
                double risk=Math.Abs(entry-stop);
                if(PriceToPips(risk)<MinStopLossPips||!GeometryValid(o.Direction,entry,stop,o.Target))continue;
                double rr=lateNetTargetPips/Math.Max(1e-9,PriceToPips(risk));
                if(rr+1e-9<2.30)continue;

                o.V74LateAuctionPending[k]=false;o.V74LateAuctionActive[k]=true;o.V74LateAuctionEntryBar[k]=o.BarsActive;
                o.V74LateAuctionEntry[k]=entry;o.V74LateAuctionStop[k]=stop;o.V74LateAuctionTarget[k]=o.Target;
                o.V74LateAuctionRisk[k]=risk;o.V74LateAuctionNetRr[k]=rr;o.V74LateAuctionBars[k]=0;
                o.V74LateAuctionPositiveArmed[k]=false;o.V74LateAuctionPostTriggerBar[k]=-1;o.V74LateAuctionLockBar[k]=-1;
                o.V74LateAuctionLockedR[k]=0;o.V74LateAuctionRouteMfeR[k]=0;o.V74LateAuctionRouteMaeR[k]=0;
                o.V74LateAuctionEntryStateCsv[k]=string.Join(",",V74RouteStateFeatures(
                    o,i,entry,risk,o.Target,0,0,0,V74LateAuctionStageR[k])
                    .Select(v=>v.ToString("R",System.Globalization.CultureInfo.InvariantCulture)));
                // No same-bar payoff after completed-bar capital admission.
            }
        }

        private void V74FinalizeTrueLateEntryAuction(V72HcogOpportunity o,double close)
        {
            if(o==null)return;
            for(int k=0;k<V74LateAuctionKey.Length;k++)
            {
                if(double.IsFinite(o.V74LateAuctionOutcomeR[k])||!o.V74LateAuctionActive[k]||o.V74LateAuctionRisk[k]<=0)continue;
                double closeR=(o.Direction==TradeDirection.Buy?close-o.V74LateAuctionEntry[k]:o.V74LateAuctionEntry[k]-close)/o.V74LateAuctionRisk[k];
                if(o.V74LateAuctionPositiveArmed[k])
                {
                    double remain=1.0-V74LateAuctionPartialFraction[k];
                    double runnerR=Math.Max(-1.0,Math.Min(o.V74LateAuctionNetRr[k],closeR));
                    o.V74LateAuctionOutcomeR[k]=o.V74LateAuctionLockedR[k]+remain*runnerR;
                }
                else o.V74LateAuctionOutcomeR[k]=Math.Max(-1.0,Math.Min(o.V74LateAuctionNetRr[k],closeR));
                o.V74LateAuctionActive[k]=false;
            }
        }

        private void V74FinalizeCausalSequentialDelayedCommit(V72HcogOpportunity o,double close)
        {
            if(o==null)return;
            for(int k=0;k<V74SequentialKey.Length;k++)
            {
                if(double.IsFinite(o.V74SequentialOutcomeR[k])||!o.V74SequentialActive[k]||o.V74SequentialRisk[k]<=0)continue;
                double closeR=(o.Direction==TradeDirection.Buy?close-o.V74SequentialEntry[k]:o.V74SequentialEntry[k]-close)/o.V74SequentialRisk[k];
                if(o.V74SequentialPositiveArmed[k])
                {
                    double remain=1.0-V74SequentialPartialFraction[k],runnerR=Math.Max(-1.0,Math.Min(o.V74SequentialNetRr[k],closeR));
                    o.V74SequentialOutcomeR[k]=o.V74SequentialLockedR[k]+remain*runnerR;
                }
                else o.V74SequentialOutcomeR[k]=Math.Max(-1.0,Math.Min(o.V74SequentialNetRr[k],closeR));
                o.V74SequentialActive[k]=false;
            }
        }

        private void V74FinalizeHighConvictionDelayedCommit(V72HcogOpportunity o,double close)
        {
            if(o==null)return;
            for(int k=0;k<V74HighConvictionKey.Length;k++)
            {
                if(double.IsFinite(o.V74HighConvictionOutcomeR[k])||!o.V74HighConvictionActive[k]||o.V74HighConvictionRisk[k]<=0)continue;
                double closeR=(o.Direction==TradeDirection.Buy?close-o.V74HighConvictionEntry[k]:o.V74HighConvictionEntry[k]-close)/o.V74HighConvictionRisk[k];
                o.V74HighConvictionOutcomeR[k]=Math.Max(-1.0,Math.Min(o.V74HighConvictionNetRr[k],closeR));
                o.V74HighConvictionActive[k]=false;
            }
        }

        private int V74ProtectionTriggerBarLength(V72HcogOpportunity o)
        {
            return o==null||o.V74ProtectionTriggerBar==null?0:o.V74ProtectionTriggerBar.Length;
        }

        private void V74FinalizeReactionConfirmedReentry(V72HcogOpportunity o,double close)
        {
            if(o==null)return;
            for(int k=0;k<V74RcrKey.Length;k++)
            {
                if(double.IsFinite(o.V74RcrOutcomeR[k])||!o.V74RcrActive[k]||o.V74RcrRisk[k]<=0)continue;
                double closeR=(o.Direction==TradeDirection.Buy?close-o.V74RcrEntry[k]:o.V74RcrEntry[k]-close)/o.V74RcrRisk[k];
                o.V74RcrOutcomeR[k]=Math.Max(-1.0,Math.Min(o.V74RcrNetRr[k],closeR));
                o.V74RcrActive[k]=false;
            }
        }

        private int V74ProtectionOutcomeRLength(V72HcogOpportunity o){return o==null||o.V74ProtectionOutcomeR==null?0:o.V74ProtectionOutcomeR.Length;}

        private void V72HcogFinalizeOutcome(V72HcogOpportunity o,int i,string result,double? forcedR=null)
        {
            if(o==null||!o.Active||o.State!=V72HcogState.ACTIVE||o.RiskDistance<=0)return;
            double close=i>=0&&i<_m1Bars.Count?_m1Bars.ClosePrices[i]:(o.Direction==TradeDirection.Buy?_symbol.Bid:_symbol.Ask);
            double closeR=(o.Direction==TradeDirection.Buy?close-o.Entry:o.Entry-close)/o.RiskDistance,r=forcedR.HasValue?forcedR.Value:Math.Max(-1.0,Math.Min(o.NetRr,closeR));
            for(int k=0;k<V74ProtectionOutcomeRLength(o);k++)if(double.IsNaN(o.V74ProtectionOutcomeR[k]))o.V74ProtectionOutcomeR[k]=r;
            for(int k=0;k<o.V74HybridOutcomeR.Length;k++)if(double.IsNaN(o.V74HybridOutcomeR[k]))o.V74HybridOutcomeR[k]=r;
            V74FinalizeReactionConfirmedReentry(o,close);
            V74FinalizeReactionCommitLadders(o,close);
            V74FinalizeHighConvictionDelayedCommit(o,close);
            V74FinalizeCausalSequentialDelayedCommit(o,close);
            V74FinalizeTrueLateEntryAuction(o,close);
            o.Result=result;o.Active=false;o.State=V72HcogState.CLOSED;_v72HcogClosed++;V72HcogRecord(o,r);
            Print("[V72-HCOG-OUTCOME] id={0} setup={1} family={2} lane={3} abcd={4} coreOverlap={5} r={6:F6} mfeR={7:F6} maeR={8:F6} bars={9} result={10} hcapSelected={11} q={12:F9} lcb={13:F9} hold={14:F3} features={15} v74features={16}",
                o.Id,o.SetupKey,o.Family,o.Lane,o.HasAbcdConfluence,o.CoreOverlapAtEntry,r,o.MfeR,o.MaeR,o.BarsActive,result,
                o.HcapSelected,o.HcapQ,o.HcapLcb,o.HcapHoldBars,string.IsNullOrWhiteSpace(o.HcapFeatureCsv)?"NONE":o.HcapFeatureCsv,
                string.IsNullOrWhiteSpace(o.V74FeatureCsv)?"NONE":o.V74FeatureCsv);
            Print("[V74-PROTECTION-PATH] setup={0} family={1} lane={2} p025={3:F6} p050={4:F6} p075={5:F6} p100={6:F6} p150={7:F6} m025={8} m050={9} m075={10} m100={11} m150={12} r050010={13} rr050010={14:F6} r075025={15} rr075025={16:F6} r100040={17} rr100040={18:F6} hs20={19:F6} hs30={20:F6} hs40={21:F6} hs50={22:F6} rc075c20={23} rc075c30={24} rc100c20={25} rc100c30={26} hc175h={27} hc175d={28} hc200h={29} hc200d={30}",
                o.SetupKey,o.Family,o.Lane,o.V74ProtectionOutcomeR[0],o.V74ProtectionOutcomeR[1],o.V74ProtectionOutcomeR[2],o.V74ProtectionOutcomeR[3],o.V74ProtectionOutcomeR[4],
                string.IsNullOrWhiteSpace(o.V74MilestoneFeatureCsv[0])?"NONE":o.V74MilestoneFeatureCsv[0],
                string.IsNullOrWhiteSpace(o.V74MilestoneFeatureCsv[1])?"NONE":o.V74MilestoneFeatureCsv[1],
                string.IsNullOrWhiteSpace(o.V74MilestoneFeatureCsv[2])?"NONE":o.V74MilestoneFeatureCsv[2],
                string.IsNullOrWhiteSpace(o.V74MilestoneFeatureCsv[3])?"NONE":o.V74MilestoneFeatureCsv[3],
                string.IsNullOrWhiteSpace(o.V74MilestoneFeatureCsv[4])?"NONE":o.V74MilestoneFeatureCsv[4],
                double.IsFinite(o.V74RcrOutcomeR[0])?o.V74RcrOutcomeR[0].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",o.V74RcrNetRr[0],
                double.IsFinite(o.V74RcrOutcomeR[1])?o.V74RcrOutcomeR[1].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",o.V74RcrNetRr[1],
                double.IsFinite(o.V74RcrOutcomeR[2])?o.V74RcrOutcomeR[2].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",o.V74RcrNetRr[2],
                o.V74HybridOutcomeR[0],o.V74HybridOutcomeR[1],o.V74HybridOutcomeR[2],o.V74HybridOutcomeR[3],
                double.IsFinite(o.V74ReactionCommitOutcomeR[0])?o.V74ReactionCommitOutcomeR[0].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74ReactionCommitOutcomeR[1])?o.V74ReactionCommitOutcomeR[1].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74ReactionCommitOutcomeR[2])?o.V74ReactionCommitOutcomeR[2].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74ReactionCommitOutcomeR[3])?o.V74ReactionCommitOutcomeR[3].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74HighConvictionOutcomeR[0])?o.V74HighConvictionOutcomeR[0].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74HighConvictionOutcomeR[1])?o.V74HighConvictionOutcomeR[1].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74HighConvictionOutcomeR[2])?o.V74HighConvictionOutcomeR[2].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA",
                double.IsFinite(o.V74HighConvictionOutcomeR[3])?o.V74HighConvictionOutcomeR[3].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA");
            var seqParts=new List<string>{"setup="+o.SetupKey,"family="+o.Family,"lane="+o.Lane,
                "m025="+(string.IsNullOrWhiteSpace(o.V74SequentialState025Csv)?"NONE":o.V74SequentialState025Csv),
                "m050="+(string.IsNullOrWhiteSpace(o.V74SequentialState050Csv)?"NONE":o.V74SequentialState050Csv)};
            for(int k=0;k<V74SequentialKey.Length;k++)
            {
                seqParts.Add("e"+k+"="+(string.IsNullOrWhiteSpace(o.V74SequentialEntryStateCsv[k])?"NONE":o.V74SequentialEntryStateCsv[k]));
                seqParts.Add("t"+k+"="+(string.IsNullOrWhiteSpace(o.V74SequentialTriggerStateCsv[k])?"NONE":o.V74SequentialTriggerStateCsv[k]));
                seqParts.Add("d"+k+"="+(string.IsNullOrWhiteSpace(o.V74SequentialDecisionStateCsv[k])?"NONE":o.V74SequentialDecisionStateCsv[k]));
                seqParts.Add("b"+k+"="+(double.IsFinite(o.V74SequentialOutcomeR[k])?o.V74SequentialOutcomeR[k].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA"));
                seqParts.Add("rr"+k+"="+o.V74SequentialNetRr[k].ToString("R",System.Globalization.CultureInfo.InvariantCulture));
                seqParts.Add("rb"+k+"="+o.V74SequentialBars[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                seqParts.Add("re"+k+"="+o.V74SequentialReactionBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                seqParts.Add("eb"+k+"="+o.V74SequentialEntryBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                seqParts.Add("tb"+k+"="+(o.V74SequentialEntryBar[k]>=0&&o.V74SequentialTriggerBar[k]>=0?o.V74SequentialEntryBar[k]+o.V74SequentialTriggerBar[k]:-1).ToString(System.Globalization.CultureInfo.InvariantCulture));
                seqParts.Add("lb"+k+"="+(o.V74SequentialEntryBar[k]>=0&&o.V74SequentialLockBar[k]>=0?o.V74SequentialEntryBar[k]+o.V74SequentialLockBar[k]:-1).ToString(System.Globalization.CultureInfo.InvariantCulture));
            }
            Print("[V74-SEQUENTIAL-PATH] "+string.Join(" ",seqParts));

            var auctionParts=new List<string>{"setup="+o.SetupKey,"family="+o.Family,"lane="+o.Lane};
            for(int k=0;k<V74LateAuctionKey.Length;k++)
            {
                auctionParts.Add("m"+k+"="+(string.IsNullOrWhiteSpace(o.V74LateAuctionMaturityStateCsv[k])?"NONE":o.V74LateAuctionMaturityStateCsv[k]));
                auctionParts.Add("e"+k+"="+(string.IsNullOrWhiteSpace(o.V74LateAuctionEntryStateCsv[k])?"NONE":o.V74LateAuctionEntryStateCsv[k]));
                auctionParts.Add("b"+k+"="+(double.IsFinite(o.V74LateAuctionOutcomeR[k])?o.V74LateAuctionOutcomeR[k].ToString("R",System.Globalization.CultureInfo.InvariantCulture):"NA"));
                auctionParts.Add("rr"+k+"="+o.V74LateAuctionNetRr[k].ToString("R",System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("rx"+k+"="+o.V74LateAuctionReactionBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("ab"+k+"="+o.V74LateAuctionAnchorBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("tb"+k+"="+o.V74LateAuctionTriggerBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("eb"+k+"="+o.V74LateAuctionEntryBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("rb"+k+"="+o.V74LateAuctionBars[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("pt"+k+"="+o.V74LateAuctionPostTriggerBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
                auctionParts.Add("lb"+k+"="+o.V74LateAuctionLockBar[k].ToString(System.Globalization.CultureInfo.InvariantCulture));
            }
            Print("[V74-LATE-AUCTION-PATH] "+string.Join(" ",auctionParts));

        }

        private void V72HcogProcessActive(int i,DateTime utc,V72HcogOpportunity o)
        {
            if(utc<=o.EntryUtc)return;o.BarsActive++;double high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            double fav=o.Direction==TradeDirection.Buy?(high-o.Entry)/o.RiskDistance:(o.Entry-low)/o.RiskDistance,adv=o.Direction==TradeDirection.Buy?(o.Entry-low)/o.RiskDistance:(high-o.Entry)/o.RiskDistance;
            o.MfeR=Math.Max(o.MfeR,fav);o.MaeR=Math.Max(o.MaeR,adv);bool stop=o.Direction==TradeDirection.Buy?low<=o.Stop:high>=o.Stop,target=o.Direction==TradeDirection.Buy?high>=o.Target:low<=o.Target;
            V74UpdateProtectionCounterfactuals(o,i,stop,target);
            V74UpdateReactionConfirmedReentry(o,i,stop,target);
            V74UpdateHybridSurvivalFrontiers(o,i,stop,target);
            V74UpdateReactionCommitLadders(o,i,stop,target);
            V74UpdateHighConvictionDelayedCommit(o,i,stop,target);
            V74UpdateCausalSequentialDelayedCommit(o,i,stop,target);
            V74UpdateTrueLateEntryAuction(o,i,stop,target);
            if(stop&&target){V72HcogFinalizeOutcome(o,i,"AMBIGUOUS_STOP_FIRST_CONSERVATIVE",-1.0);return;}if(stop){V72HcogFinalizeOutcome(o,i,"STRUCTURAL_STOP",-1.0);return;}
            if(target){V72HcogFinalizeOutcome(o,i,"CANONICAL_TARGET",o.NetRr);return;}if(o.BarsActive>=180)V72HcogFinalizeOutcome(o,i,"FIXED_180M_HORIZON");
        }

        private void V72HcogProcessM1(int i,DateTime utc)
        {
            if((!EnableV72HcogAlpha&&!EnableV72HcapAlpha&&!EnableV73OpportunityUniverse&&!EnableV74ExternalPolicy&&!EnableV74EmbeddedPolicy)||i<3)return;
            foreach(var o in _v72Hcog.Values.Where(x=>x.Active).ToList())
            {
                if(utc<=o.DetectedUtc)continue;if(o.State==V72HcogState.ACTIVE){V72HcogProcessActive(i,utc,o);continue;}
                if(utc>=o.OverallExpiryUtc){o.Active=false;o.State=V72HcogState.EXPIRED;continue;}
                if(o.State!=V72HcogState.WAIT_PRZ&&o.State!=V72HcogState.FAILURE_WAIT_RETEST&&o.PrzTouchUtc.HasValue&&V72HcogStructuralBreak(i,o.Signal)){V72HcogStartFailure(utc,o);continue;}
                if(o.State==V72HcogState.WAIT_PRZ){if(!BarTouchesPrz(i,o.Signal))continue;o.PrzTouchUtc=utc;o.ProofExpiryUtc=V72NextM15Boundary(utc).AddMinutes(15);if(o.ProofExpiryUtc>o.OverallExpiryUtc)o.ProofExpiryUtc=o.OverallExpiryUtc;
                    o.LiquidityExtreme=o.Signal.Direction==TradeDirection.Buy?_m1Bars.LowPrices[i]:_m1Bars.HighPrices[i];o.LastStageUtc=utc;o.State=V72HcogState.WAIT_LIQUIDITY;_v72HcogPrzTouched++;continue;}
                if(o.State==V72HcogState.FAILURE_WAIT_RETEST){V72HcogProcessFailureRetest(i,utc,o);continue;}V72HcogProcessProof(i,utc,o);
            }
        }

        private void V72HcogFinalizeAndPrint()
        {
            if(!EnableV72HcogAlpha&&!EnableV72HcapAlpha&&!EnableV73OpportunityUniverse&&!EnableV74ExternalPolicy&&!EnableV74EmbeddedPolicy)return;int i=LastClosedIndex(_m1Bars);
            foreach(var o in _v72Hcog.Values.Where(x=>x.Active&&x.State==V72HcogState.ACTIVE).ToList())V72HcogFinalizeOutcome(o,i,"BACKTEST_END");
            foreach(var kv in _v72HcogCensus.OrderBy(x=>x.Key)){string[] p=kv.Key.Split('|');string lane=p.Length>0?p[0]:"UNKNOWN",fam=p.Length>1?p[1]:"UNKNOWN";var z=kv.Value;
                Print("[V72-HCOG-CENSUS] lane={0} family={1} n={2} sumR={3:F9} sumSqR={4:F9} gpR={5:F9} glR={6:F9} wins={7}",lane,fam,z.N,z.SumR,z.SumSqR,z.GrossProfitR,z.GrossLossR,z.Wins);}
            Print("[V72-HCOG-SUMMARY] detected={0} przTouched={1} proofs={2} armed={3} failureArmed={4} closed={5} coreOverlapAtEntry={6} abcdPrimitive={7} capitalQueued={8} active={9} counterfactualCoreIndependent=True",
                _v72HcogDetected,_v72HcogPrzTouched,_v72HcogProofs,_v72HcogArmed,_v72HcogFailureArmed,_v72HcogClosed,_v72HcogCoreOverlapAtEntry,_v72HcogAbcdPrimitive,_v72HcogCapitalQueued,_v72Hcog.Values.Count(x=>x.Active));
            V72HcapPrintSummary();
            V73PrintUniverseSummary();
        }
    }
}
