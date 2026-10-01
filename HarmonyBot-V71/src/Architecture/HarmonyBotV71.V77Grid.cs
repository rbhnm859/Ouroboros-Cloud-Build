using System;
using System.Collections.Generic;
using System.Linq;

namespace cAlgo.Robots
{
    public partial class HarmonyBotV71
    {
        private bool V77BuildExpansionGrid(CandidateRecord c,V71ExpansionCandidate e)
        {
            if(c==null||e==null||e.RiskDistance<=0)return false;
            double[] fractions; double[] weights;
            if(e.Route==HarmonicRoute.EXHAUSTION_REVERSAL)
            {
                fractions=new[]{0.0,.382}; weights=new[]{.65,.35};
            }
            else if(e.Route==HarmonicRoute.TRANSITION_REVERSAL)
            {
                fractions=new[]{0.0,.236,.382}; weights=new[]{.50,.30,.20};
            }
            else
            {
                fractions=new[]{0.0,.236,.382,.618}; weights=new[]{.40,.30,.20,.10};
            }

            double riskPct=V71ExpansionRiskFor(e);
            var plan=new FibonacciGridPlan
            {
                CandidateId=c.CandidateId,Pattern=e.Signal.PatternName,Direction=V72CapitalDirection(e),
                Route=e.Route,EntryAnchor=e.EntryAnchor,StructuralStop=e.StructuralStop,
                GridDistance=e.RiskDistance,BasketRiskAmount=Account.Equity*riskPct/100.0,
                CreatedUtc=Server.Time.ToUniversalTime(),ExpirationUtc=e.ExpiryUtc,
                MicroCapitalMode=AdaptiveCapitalMode&&Account.Equity<=MicroCapitalThreshold
            };
            if(plan.BasketRiskAmount<=0)return false;
            for(int i=0;i<fractions.Length;i++)
            {
                double price=plan.Direction==TradeDirection.Buy
                    ? e.EntryAnchor-fractions[i]*e.RiskDistance
                    : e.EntryAnchor+fractions[i]*e.RiskDistance;
                double slPips=PriceToPips(Math.Abs(price-e.StructuralStop));
                if(slPips<MinStopLossPips)continue;
                double minVolume=_symbol.VolumeInUnitsMin;
                double minRisk=minVolume*_symbol.PipValue*(slPips+ModeledCostPips());
                plan.Legs.Add(new FibonacciGridLeg
                {
                    Index=i,Fraction=fractions[i],PlannedPrice=price,RiskWeight=weights[i],
                    RiskBudget=plan.BasketRiskAmount*weights[i],MinBrokerRisk=minRisk,
                    Volume=0,PlannedRisk=0,ModeledCost=0,Physical=false,State=GridLegState.VIRTUAL_ONLY
                });
            }
            if(plan.Legs.Count==0||plan.Legs[0].Index!=0)return false;
            plan.LogicalLegCount=plan.Legs.Count;
            if(!ConfigureCapitalExecution(plan))return false;
            var physical=plan.Legs.Where(x=>x.Physical&&x.Volume>0).ToList();
            if(physical.Count==0||physical[0].Index!=0)return false;
            double totalVolume=physical.Sum(x=>x.Volume);
            plan.ExpectedWeightedEntry=physical.Sum(x=>x.PlannedPrice*x.Volume)/totalVolume;
            plan.VirtualWeightedEntry=plan.ExpectedWeightedEntry;
            plan.CanonicalTarget=e.CanonicalTarget;
            double rewardPips=PriceToPips(Math.Abs(e.CanonicalTarget-plan.ExpectedWeightedEntry))-ModeledCostPips();
            double riskPips=PriceToPips(Math.Abs(plan.ExpectedWeightedEntry-e.StructuralStop));
            plan.ExpectedNetRR=rewardPips/Math.Max(1e-9,riskPips);
            if(plan.ExpectedNetRR+1e-9<MinimumNetRR)return false;
            c.GridPlan=plan;c.SelectedTarget=e.CanonicalTarget;c.NetRR=plan.ExpectedNetRR;
            Print("[V77-EXP-GRID] cid={0} setup={1} route={2} legs={3} physical={4} riskPct={5:F2} weighted={6:F5} stop={7:F5} target={8:F5} netRR={9:F3}",
                c.CandidateId,c.SetupKey,e.Route,plan.LogicalLegCount,plan.PhysicalDepth,riskPct,
                plan.ExpectedWeightedEntry,plan.StructuralStop,plan.CanonicalTarget,plan.ExpectedNetRR);
            return true;
        }
    }
}
