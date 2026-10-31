using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    // One-shot V72-grade family-native causal conversion.
    // Frozen detector -> family-specific completed-bar proof -> own D/PRZ retest -> own structural stop/canonical target.
    // H4/H1 regime/conflict are context telemetry here, not hard Alpha vetoes.
    public partial class HarmonyBotV71
    {
        private bool V72FamilyNativeCapitalSemanticsAllowed(V71ExpansionCandidate e)
        {
            if (e == null || e.Signal == null) return false;
            return !string.Equals(V71FamilyKey(e.Signal.PatternName), "ABCD", StringComparison.OrdinalIgnoreCase);
        }

        private bool V72FamilyNativeCausalProof(int i, V71ExpansionCandidate e, out double score)
        {
            score = 0;
            if (e == null || e.Signal == null || i < 3 || i >= _m1Bars.Count) return false;
            if (e.NativeEvidenceState == null)
            {
                e.NativeEvidenceState = new CandidateRecord
                {
                    CandidateId = e.CandidateId + "-FAMILY-CAUSAL",
                    SetupKey = e.SetupKey, Signal = e.Signal, Route = e.Route, Regime = e.Regime, IsActive = true
                };
            }
            CandidateRecord c = e.NativeEvidenceState;
            double o=_m1Bars.OpenPrices[i], cl=_m1Bars.ClosePrices[i], h=_m1Bars.HighPrices[i], l=_m1Bars.LowPrices[i];
            double pc=_m1Bars.ClosePrices[i-1], ph=_m1Bars.HighPrices[i-1], pl=_m1Bars.LowPrices[i-1];
            double body=Math.Max(Math.Abs(cl-o),_symbol.PipSize);
            double prevBody=Math.Max(Math.Abs(_m1Bars.ClosePrices[i-1]-_m1Bars.OpenPrices[i-1]),_symbol.PipSize);
            double atr=Atr(_m1Bars,14,i);
            bool buy=e.Signal.Direction==TradeDirection.Buy;
            bool directional=buy?cl>o:cl<o;
            bool reclaim=buy?(cl>e.Signal.PrzLow&&cl>=pc):(cl<e.Signal.PrzHigh&&cl<=pc);
            bool bos=buy?cl>ph:cl<pl;
            bool rejection=buy?Math.Max(0,Math.Min(o,cl)-l)>=body*.5:Math.Max(0,h-Math.Max(o,cl))>=body*.5;
            bool sweep=buy?l<pl:h>ph;
            bool failedExtension=buy?(l<pl&&cl>pl):(h>ph&&cl<ph);
            bool insidePrz=cl>=Math.Min(e.Signal.PrzLow,e.Signal.PrzHigh)&&cl<=Math.Max(e.Signal.PrzLow,e.Signal.PrzHigh);
            bool displacement=atr>0&&body>=atr*.30;
            bool deceleration=body<=prevBody*.85;
            double przMid=(e.Signal.PrzLow+e.Signal.PrzHigh)*.5;
            bool retest=insidePrz||Math.Abs(cl-przMid)<=Math.Max(atr*.25,_symbol.PipSize);

            c.FamilyDirectional|=directional; c.FamilyReclaim|=reclaim; c.FamilyBos|=bos;
            c.FamilyRejection|=rejection; c.FamilySweep|=sweep; c.FamilyFailedExtension|=failedExtension;
            c.FamilyInsidePrz|=insidePrz; c.FamilyDisplacement|=displacement; c.FamilyRetest|=retest;

            int prior=c.NativeStage; bool step=false; string fam=V71FamilyKey(e.Signal.PatternName);
            switch(fam)
            {
                case "Gartley": step=prior==0?rejection:prior==1?reclaim:prior==2?bos:prior==3&&displacement; break;
                case "Bat": step=prior==0?sweep:prior==1?reclaim:prior==2?bos:prior==3&&displacement; break;
                case "DeepGartley": step=prior==0?failedExtension:prior==1?reclaim:prior==2?bos:prior==3&&displacement; break;
                case "Rat": step=prior==0?rejection:prior==1?reclaim:prior==2?displacement:prior==3&&bos; break;
                case "AltBat": step=prior==0?sweep:prior==1?failedExtension:prior==2?reclaim:prior==3&&bos; break;
                case "Butterfly": step=prior==0?sweep:prior==1?failedExtension:prior==2?bos:prior==3&&displacement; break;
                case "Crab": step=prior==0?sweep:prior==1?failedExtension:prior==2?reclaim:prior==3&&displacement; break;
                case "DeepCrab": step=prior==0?sweep:prior==1?failedExtension:prior==2?reclaim:prior==3&&bos; break;
                case "Cypher": step=prior==0?rejection:prior==1?reclaim:prior==2?bos:prior==3&&displacement; break;
                case "Shark": step=prior==0?sweep:prior==1?failedExtension:prior==2?reclaim:prior==3&&bos; break;
                case "FiveZero": step=prior==0?failedExtension:prior==1?bos:prior==2?retest:prior==3&&directional; break;
                case "ABCD": step=prior==0?deceleration:prior==1?failedExtension:prior==2?(directional&&displacement):prior==3&&bos; break;
                default: return false;
            }
            if(step&&prior<4)c.NativeStage=prior+1;
            score=Math.Min(1.0,c.NativeStage/4.0);
            return c.NativeStage>=4;
        }

        private void V72ArmFamilyNativePath(V71ExpansionCandidate e, DateTime utc,
            TradeDirection direction,double entry,double stop,double target,double netRr,
            double confirmationScore,string lane,bool capitalSemanticsAllowed)
        {
            double risk=Math.Abs(entry-stop);
            e.CapitalDirection=direction; e.EntryAnchor=entry; e.StructuralStop=stop; e.CanonicalTarget=target;
            e.RiskDistance=risk; e.TargetR=Math.Abs(target-entry)/Math.Max(risk,_symbol.PipSize); e.NetRR=netRr;
            e.ConfirmationScore=confirmationScore; e.RegimeScore=RegimeContextScore(e.Signal,e.Conflict,e.Regime);
            e.ModeledCostR=PipsToPrice(ModeledCostPips())/Math.Max(risk,_symbol.PipSize);
            e.PullbackExpiryUtc=e.ExpiryUtc; e.AwaitingPullbackFill=true; e.PullbackFilled=false;
            e.ShadowStarted=false; e.ShadowFinished=false; e.ArmedUtc=null; e.ShadowPeakR=0; e.ShadowProtectionR=-1.0;
            e.PathState=0; e.PathUsable=false;
            e.CapitalEligible=e.CapitalEligible&&capitalSemanticsAllowed;
            e.CapitalReady=EnableV71ExpansionExecution&&e.CapitalEligible&&!e.CoreOverlapObserved;
            e.CapitalLane=lane; e.State=V71ExpansionState.ARMED; e.AsymmetryCompression=1.0;
            e.EdgeMean=netRr; e.EdgeLcb=netRr;
            e.ExpectedSlotHours=Math.Max(.25,(e.PullbackExpiryUtc-utc).TotalHours);
            e.ExpectedSlotHoursUcb=e.ExpectedSlotHours; e.SlotScore=netRr/Math.Max(.25,e.ExpectedSlotHours);
            _v71ExpansionArmed++; IncrementCounter(_v71FamilyArmed,V71FamilyKey(e.Signal.PatternName));
        }

        private bool V72PrepareFamilyNativeReversalShadow(int i, DateTime utc, V71ExpansionCandidate e, double confirmationScore)
        {
            if(!EnableV72FamilyNativeCausalAlpha||e==null||e.Signal==null||i<0||i>=_m1Bars.Count)return false;
            double lo=Math.Min(e.Signal.PrzLow,e.Signal.PrzHigh), hi=Math.Max(e.Signal.PrzLow,e.Signal.PrzHigh);
            double entry=e.Signal.D!=null?e.Signal.D.Price:(lo+hi)*.5;
            entry=Math.Max(lo,Math.Min(hi,entry));
            double stop=e.Signal.StructuralInvalidation, risk=Math.Abs(entry-stop);
            if(PriceToPips(risk)<MinStopLossPips)return false;
            double target,netRr;
            if(!SelectCanonicalBasketTarget(e.Signal,entry,stop,out target,out netRr)||netRr+1e-9<MinimumNetRR)return false;
            bool allowed=V72FamilyNativeCapitalSemanticsAllowed(e)&&e.CapitalEligible&&!e.CoreOverlapObserved;
            string lane=allowed?"FAMILY_NATIVE_D_PRZ_REVERSAL":"FAMILY_NATIVE_SHADOW_ONLY";
            V72ArmFamilyNativePath(e,utc,e.Signal.Direction,entry,stop,target,netRr,confirmationScore,lane,allowed);
            Print("[V72-FAMILY-NATIVE-ARM] cid={0} family={1} dir={2} dEntry={3:F5} stop={4:F5} target={5:F5} netRR={6:F3} capitalReady={7}",
                e.CandidateId,V71FamilyKey(e.Signal.PatternName),e.Signal.Direction,entry,stop,target,netRr,e.CapitalReady);
            return true;
        }

        private bool V72StartFamilyNativeFailureRetest(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if(!EnableV72FamilyNativeCausalAlpha||e==null||e.Signal==null||!e.PrzTouchUtc.HasValue||!V72FailureBreakConfirmed(i,e))return false;
            e.FailureContinuation=true; e.FailureBreakObserved=true; e.FailureBreakUtc=utc;
            e.FailureBoundary=e.Signal.StructuralInvalidation; e.FailureBreakPrice=_m1Bars.ClosePrices[i];
            e.CapitalDirection=V72OppositeDirection(e.Signal.Direction); e.FailureRetestExpiryUtc=e.ExpiryUtc;
            if(e.FailureRetestExpiryUtc<=utc.AddSeconds(1))return false;
            e.State=V71ExpansionState.PROOF_WAIT; e.CapitalReady=false; e.CapitalLane="FAMILY_NATIVE_FAILURE_WAIT";
            Print("[V72-FAMILY-FAILURE-BREAK] cid={0} family={1} originalDir={2} continuationDir={3} boundary={4:F5} close={5:F5} expiry={6:o}",
                e.CandidateId,V71FamilyKey(e.Signal.PatternName),e.Signal.Direction,e.CapitalDirection,e.FailureBoundary,e.FailureBreakPrice,e.FailureRetestExpiryUtc);
            return true;
        }

        private bool V72ProcessFamilyNativeFailureRetest(int i, DateTime utc, V71ExpansionCandidate e)
        {
            if(e==null||e.Signal==null||!e.FailureBreakObserved||!e.FailureContinuation)return false;
            if(!e.FailureBreakUtc.HasValue||utc<=e.FailureBreakUtc.Value)return false;
            if(utc>=e.FailureRetestExpiryUtc){e.IsActive=false;e.State=V71ExpansionState.EXPIRED;Print("[V72-FAMILY-FAILURE-EXPIRE] cid={0}",e.CandidateId);return true;}
            TradeDirection direction=e.CapitalDirection; double boundary=e.FailureBoundary;
            double o=_m1Bars.OpenPrices[i],close=_m1Bars.ClosePrices[i],high=_m1Bars.HighPrices[i],low=_m1Bars.LowPrices[i];
            bool touched=low<=boundary&&high>=boundary;
            bool held=direction==TradeDirection.Buy?close>boundary:close<boundary;
            bool directional=direction==TradeDirection.Buy?close>o:close<o;
            if(!(touched&&held&&directional))return false;
            double buffer=Math.Max(PipsToPrice(ModeledCostPips()),_symbol.PipSize);
            double entry=close, stop=direction==TradeDirection.Buy?low-buffer:high+buffer;
            double risk=Math.Abs(entry-stop); if(PriceToPips(risk)<MinStopLossPips)return false;
            double cost=PipsToPrice(ModeledCostPips());
            double target=direction==TradeDirection.Buy?entry+2.0*risk+cost:entry-2.0*risk-cost;
            if(!GeometryValid(direction,entry,stop,target))return false;
            double netRr=(PriceToPips(Math.Abs(target-entry))-ModeledCostPips())/Math.Max(1e-9,PriceToPips(risk));
            if(netRr+1e-9<MinimumNetRR)return false;
            bool allowed=V72FamilyNativeCapitalSemanticsAllowed(e)&&e.CapitalEligible&&!e.CoreOverlapObserved;
            e.Route=HarmonicRoute.FAILURE_CONTINUATION;
            V72ArmFamilyNativePath(e,utc,direction,entry,stop,target,netRr,1.0,
                allowed?"FAMILY_NATIVE_FAILURE_CONTINUATION":"FAMILY_NATIVE_SHADOW_ONLY",allowed);
            Print("[V72-FAMILY-FAILURE-RETEST] cid={0} family={1} dir={2} entry={3:F5} stop={4:F5} target={5:F5} netRR={6:F3} capitalReady={7}",
                e.CandidateId,V71FamilyKey(e.Signal.PatternName),direction,entry,stop,target,netRr,e.CapitalReady);
            return true;
        }
    }
}
