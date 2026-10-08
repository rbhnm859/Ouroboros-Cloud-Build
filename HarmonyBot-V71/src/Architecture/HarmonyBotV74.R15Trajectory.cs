using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace cAlgo.Robots
{
    public partial class HarmonyBotV71
    {
        // Research telemetry only. No entry, route, risk or capital mechanics change.
        // All V73 action families freeze this common history at their legal decision.
        private void V74R15EmitTrajectory(V72HcogOpportunity o,int i)
        {
            if(!EnableV73OpportunityUniverse)return;
            if(o==null||o.Signal==null||o.Signal.D==null||o.V74R15AnchorIndex<0||
               i<32||i>LastClosedIndex(_m1Bars)||i-o.V74R15AnchorIndex!=o.BarsActive||
               !(o.RiskDistance>0)||!double.IsFinite(o.RiskDistance))
                throw new InvalidOperationException("R15_TRAJECTORY_CAUSAL_CONTRACT");
            if(o.V74R15Emitted.Contains(i))return;
            double sign=o.Direction==TradeDirection.Buy?1.0:-1.0,risk=o.RiskDistance;
            int start=i-31;
            var cells=new List<string>();var times=new List<string>();
            double path=0,net=0,sq=0,peak=double.NegativeInfinity;
            double first=_m1Bars.ClosePrices[start-1],prev=0;
            DateTime previous=DateTime.MinValue;
            for(int j=start;j<=i;j++)
            {
                DateTime closeUtc=DateTime.SpecifyKind(_m1Bars.OpenTimes[j],DateTimeKind.Utc).AddMinutes(1);
                if(closeUtc<=previous)throw new InvalidOperationException("R15_TIMESTAMP_ORDER");
                previous=closeUtc;times.Add(closeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ",CultureInfo.InvariantCulture));
                double op=_m1Bars.OpenPrices[j],cl=_m1Bars.ClosePrices[j],hi=_m1Bars.HighPrices[j],lo=_m1Bars.LowPrices[j];
                double atr=Atr(_m1Bars,14,j);
                if(!(atr>0)||!double.IsFinite(atr)||hi<Math.Max(op,cl)||lo>Math.Min(op,cl))
                    throw new InvalidOperationException("R15_OHLC_ATR_CONTRACT");
                double step=sign*(cl-_m1Bars.ClosePrices[j-1])/risk;
                path+=Math.Abs(step);net+=step;sq+=step*step;
                // Excursions refer to historical window origin, never future entry outcome.
                double favorable=(sign>0?hi-first:first-lo)/risk;
                double adverse=(sign>0?first-lo:hi-first)/risk;
                double signedClose=sign*(cl-first)/risk;
                peak=Math.Max(j==start?double.NegativeInfinity:peak,favorable);
                double priorRange=0;for(int k=Math.Max(0,j-4);k<j;k++)priorRange+=_m1Bars.HighPrices[k]-_m1Bars.LowPrices[k];
                double[] x={step,(hi-lo)/atr,sign*(cl-op)/atr,(hi-Math.Max(op,cl))/atr,(Math.Min(op,cl)-lo)/atr,
                    sign*(cl-o.Signal.D.Price)/risk,sign*(cl-o.Signal.PrzLow)/risk,sign*(cl-o.Signal.PrzHigh)/risk,
                    favorable,adverse,step,step-prev,Math.Abs(net)/Math.Max(1e-12,path),
                    sign*(cl-(o.Signal.PrzLow+o.Signal.PrzHigh)*.5)/risk,
                    (hi-lo)/Math.Max(_symbol.PipSize,priorRange/Math.Min(4,j)),
                    peak,peak-signedClose,Math.Sqrt(sq/(j-start+1))};
                if(x.Any(v=>!double.IsFinite(v)))throw new InvalidOperationException("R15_NONFINITE");
                cells.Add(string.Join(",",x.Select(v=>v.ToString("G9",CultureInfo.InvariantCulture))));prev=step;
            }
            DateTime decision=DateTime.SpecifyKind(_m1Bars.OpenTimes[i],DateTimeKind.Utc).AddMinutes(1);
            double phase=2*Math.PI*decision.TimeOfDay.TotalMinutes/1440;
            double spread=(_symbol.Ask-_symbol.Bid)/risk;
            if(!double.IsFinite(spread)||spread<0)throw new InvalidOperationException("R15_SPREAD_CONTRACT");
            Print("[V74-R15-TRAJECTORY] schema=V74_R15_TRAJECTORY_V1 setup={0} bar={1} anchor={2} index={3} decision={4} times={5} spread={6} sin={7} cos={8} values={9}",
                o.SetupKey,o.BarsActive,o.V74R15AnchorIndex,i,decision.ToString("yyyy-MM-ddTHH:mm:ssZ",CultureInfo.InvariantCulture),
                string.Join(",",times),spread.ToString("G9",CultureInfo.InvariantCulture),Math.Sin(phase).ToString("G9",CultureInfo.InvariantCulture),
                Math.Cos(phase).ToString("G9",CultureInfo.InvariantCulture),string.Join(";",cells));
            o.V74R15Emitted.Add(i);
        }
    }
}
