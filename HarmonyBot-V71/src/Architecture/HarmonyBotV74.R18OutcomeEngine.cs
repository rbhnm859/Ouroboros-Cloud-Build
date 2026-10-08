using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class HarmonyBotV71
    {
        // V74-R18 research-only execution-semantic outcome engine.
        // It never places/cancels/modifies an order. It shadows legal V74 actions after
        // completed-bar admission and resolves them on chronological server ticks.
        private sealed class V74R18OutcomeTracker
        {
            public string Key;
            public string Setup;
            public string Family;
            public string Source;
            public string Route;
            public TradeDirection Direction;
            public DateTime DecisionUtc;
            public DateTime DeadlineUtc;
            public double PlannedEntry;
            public double FillPrice;
            public double Stop;
            public double Target;
            public double Risk;
            public double PlannedNetRr;
            public double EntrySpreadPips;
            public bool MinCapitalFeasible;
            public bool Resolved;
        }

        private readonly Dictionary<string,V74R18OutcomeTracker> _v74R18Outcome =
            new Dictionary<string,V74R18OutcomeTracker>(StringComparer.Ordinal);
        private int _v74R18Registered;
        private int _v74R18Resolved;
        private int _v74R18NoFill;
        private int _v74R18Censored;
        private int _v74R18Divergence;

        private static string V74R18OutcomeKey(string setup,string source,string route)
            => (setup??"")+"|"+(source??"")+"|"+(route??"");

        private DateTime V74R18DecisionUtc(int i)
        {
            if(i<0||i>=_m1Bars.Count)return Server.Time.ToUniversalTime();
            return DateTime.SpecifyKind(_m1Bars.OpenTimes[i],DateTimeKind.Utc).AddMinutes(1);
        }

        private double V74R18ExitPrice(TradeDirection direction)
            => direction==TradeDirection.Buy?_symbol.Bid:_symbol.Ask;

        private double V74R18EntryPrice(TradeDirection direction)
            => direction==TradeDirection.Buy?_symbol.Ask:_symbol.Bid;

        private double V74R18ExtraCostPips()
            => Math.Max(0.0,RoundTurnCommissionPips)+Math.Max(0.0,SlippageStressPips);

        private bool V74R18GeometryValid(TradeDirection d,double entry,double stop,double target)
        {
            if(!(double.IsFinite(entry)&&double.IsFinite(stop)&&double.IsFinite(target)))return false;
            return d==TradeDirection.Buy
                ? stop+_symbol.TickSize<entry&&entry+_symbol.TickSize<target
                : target+_symbol.TickSize<entry&&entry+_symbol.TickSize<stop;
        }

        private void V74R18Emit(V74R18OutcomeTracker t,string cause,double exitPx,DateTime utc,bool executed)
        {
            if(t==null||t.Resolved)return;
            t.Resolved=true;
            _v74R18Resolved++;

            double riskPips=PriceToPips(Math.Max(_symbol.PipSize,t.Risk));
            double grossR=0.0,netR=0.0;
            if(executed)
            {
                grossR=(t.Direction==TradeDirection.Buy?exitPx-t.FillPrice:t.FillPrice-exitPx)/Math.Max(_symbol.PipSize,t.Risk);
                netR=grossR-V74R18ExtraCostPips()/Math.Max(1e-9,riskPips);
            }
            else _v74R18NoFill++;
            if(cause=="CENSORED")_v74R18Censored++;
            if(cause=="RUNTIME_DIVERGENCE")_v74R18Divergence++;

            V74R15ResearchPrint(
                "[V74-R18-OUTCOME] schema=V74_R18_OUTCOME_V1 setup={0} family={1} source={2} route={3} dir={4} decision={5} exit={6} cause={7} executed={8} planned_entry={9} fill={10} stop={11} target={12} exit_px={13} risk={14} gross_r={15} net_r={16} planned_rr={17} entry_spread_pips={18} extra_cost_pips={19} min_cap_feasible={20}",
                t.Setup,t.Family,t.Source,t.Route,t.Direction==TradeDirection.Buy?"BUY":"SELL",
                t.DecisionUtc.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",CultureInfo.InvariantCulture),
                utc.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ",CultureInfo.InvariantCulture),
                cause,executed?"true":"false",
                t.PlannedEntry.ToString("R",CultureInfo.InvariantCulture),
                t.FillPrice.ToString("R",CultureInfo.InvariantCulture),
                t.Stop.ToString("R",CultureInfo.InvariantCulture),
                t.Target.ToString("R",CultureInfo.InvariantCulture),
                exitPx.ToString("R",CultureInfo.InvariantCulture),
                t.Risk.ToString("R",CultureInfo.InvariantCulture),
                grossR.ToString("R",CultureInfo.InvariantCulture),
                netR.ToString("R",CultureInfo.InvariantCulture),
                t.PlannedNetRr.ToString("R",CultureInfo.InvariantCulture),
                t.EntrySpreadPips.ToString("R",CultureInfo.InvariantCulture),
                V74R18ExtraCostPips().ToString("R",CultureInfo.InvariantCulture),
                t.MinCapitalFeasible?"true":"false");
        }

        private void V74R18Register(V72HcogOpportunity o,int i,string source,string route,
            TradeDirection direction,double plannedEntry,double stop,double target,double plannedRisk,double plannedNetRr)
        {
            if(!EnableV74R18OutcomeResearch||o==null||direction==TradeDirection.Neutral)return;
            string key=V74R18OutcomeKey(o.SetupKey,source,route);
            if(_v74R18Outcome.ContainsKey(key))return;

            DateTime decision=V74R18DecisionUtc(i);
            double spreadPips=Math.Max(0.0,SpreadPips());
            double fill=V74R18EntryPrice(direction);
            double risk=Math.Abs(fill-stop);
            double riskPips=PriceToPips(risk);
            DateTime deadline=o.EntryUtc==default(DateTime)
                ? decision.AddMinutes(180)
                : o.EntryUtc.ToUniversalTime().AddMinutes(180);
            if(o.OverallExpiryUtc!=default(DateTime)&&o.OverallExpiryUtc.ToUniversalTime()<deadline)
                deadline=o.OverallExpiryUtc.ToUniversalTime();

            double minRiskUsd=_symbol.VolumeInUnitsMin*_symbol.PipValue*
                (Math.Max(0.0,riskPips)+V74R18ExtraCostPips());
            bool minCapFeasible=minRiskUsd<=100.0*.01+1e-8;

            var t=new V74R18OutcomeTracker{
                Key=key,Setup=o.SetupKey,Family=o.Family,Source=source,Route=route,
                Direction=direction,DecisionUtc=decision,DeadlineUtc=deadline,
                PlannedEntry=plannedEntry,FillPrice=fill,Stop=stop,Target=target,
                Risk=risk,PlannedNetRr=plannedNetRr,EntrySpreadPips=spreadPips,
                MinCapitalFeasible=minCapFeasible
            };
            _v74R18Outcome[key]=t;
            _v74R18Registered++;

            if(!IsInstitutionalSession(decision)){V74R18Emit(t,"NO_FILL_SESSION",fill,decision,false);return;}
            if(spreadPips>MaxSpreadPips+1e-9){V74R18Emit(t,"NO_FILL_SPREAD",fill,decision,false);return;}
            if(!V74R18GeometryValid(direction,fill,stop,target)){V74R18Emit(t,"NO_FILL_GEOMETRY",fill,decision,false);return;}
            if(riskPips+1e-9<MinStopLossPips){V74R18Emit(t,"NO_FILL_MIN_STOP",fill,decision,false);return;}

            V74R15ResearchPrint(
                "[V74-R18-ADMISSION] schema=V74_R18_ADMISSION_V1 setup={0} family={1} source={2} route={3} dir={4} decision={5} planned_entry={6} fill={7} stop={8} target={9} risk={10} planned_rr={11} spread_pips={12} min_cap_feasible={13}",
                t.Setup,t.Family,t.Source,t.Route,direction==TradeDirection.Buy?"BUY":"SELL",
                decision.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",CultureInfo.InvariantCulture),
                plannedEntry.ToString("R",CultureInfo.InvariantCulture),
                fill.ToString("R",CultureInfo.InvariantCulture),
                stop.ToString("R",CultureInfo.InvariantCulture),
                target.ToString("R",CultureInfo.InvariantCulture),
                risk.ToString("R",CultureInfo.InvariantCulture),
                plannedNetRr.ToString("R",CultureInfo.InvariantCulture),
                spreadPips.ToString("R",CultureInfo.InvariantCulture),
                minCapFeasible?"true":"false");
        }

        private void V74R18SyncOpportunity(V72HcogOpportunity o,int i)
        {
            if(!EnableV74R18OutcomeResearch||o==null)return;

            for(int k=0;k<V74SequentialKey.Length;k++)
                if(o.V74SequentialActive[k]&&o.V74SequentialEntryBar[k]>=0)
                    V74R18Register(o,i,"EARLY",V74SequentialKey[k],o.Direction,
                        o.V74SequentialEntry[k],o.V74SequentialStop[k],o.V74SequentialTarget[k],
                        o.V74SequentialRisk[k],o.V74SequentialNetRr[k]);

            for(int k=0;k<V74LateAuctionKey.Length;k++)
                if(o.V74LateAuctionActive[k]&&o.V74LateAuctionEntryBar[k]>=0)
                    V74R18Register(o,i,"LATE",V74LateAuctionKey[k],o.Direction,
                        o.V74LateAuctionEntry[k],o.V74LateAuctionStop[k],o.V74LateAuctionTarget[k],
                        o.V74LateAuctionRisk[k],o.V74LateAuctionNetRr[k]);

            for(int k=0;k<V74SurvivalFreshKey.Length;k++)
                if(o.V74SurvivalFreshActive[k]&&o.V74SurvivalFreshEntryBar[k]>=0)
                    V74R18Register(o,i,"SURVIVAL",V74SurvivalFreshKey[k],o.Direction,
                        o.V74SurvivalFreshEntry[k],o.V74SurvivalFreshStop[k],o.V74SurvivalFreshTarget[k],
                        o.V74SurvivalFreshRisk[k],o.V74SurvivalFreshNetRr[k]);

            for(int k=0;k<V74HighConvictionKey.Length;k++)
                if(o.V74HighConvictionActive[k]&&o.V74HighConvictionEntryBar[k]>=0)
                    V74R18Register(o,i,"SURVIVAL",V74HighConvictionKey[k],o.Direction,
                        o.V74HighConvictionEntry[k],o.V74HighConvictionStop[k],o.V74HighConvictionTarget[k],
                        o.V74HighConvictionRisk[k],o.V74HighConvictionNetRr[k]);

            for(int k=0;k<V74ReactionCommitKey.Length;k++)
                if(o.V74ReactionCommitActive[k]&&o.V74ReactionCommitEntryBar[k]>=0)
                    V74R18Register(o,i,"REACTION",V74ReactionCommitKey[k],o.Direction,
                        o.V74ReactionCommitEntry[k],o.V74ReactionCommitStop[k],o.V74ReactionCommitTarget[k],
                        o.V74ReactionCommitRisk[k],o.V74ReactionCommitNetRr[k]);

            if(o.V74FailureFreshActive&&o.V74FailureEntryBar>=0)
            {
                TradeDirection d=o.Direction==TradeDirection.Buy?TradeDirection.Sell:TradeDirection.Buy;
                V74R18Register(o,i,"FAILURE","FC230",d,
                    o.V74FailureEntry,o.V74FailureStop,o.V74FailureTarget,
                    o.V74FailureRisk,o.V74FailureNetRr);
            }
        }

        private void V74R18OnTick()
        {
            if(!EnableV74R18OutcomeResearch||_symbol==null)return;
            DateTime now=Server.Time.ToUniversalTime();
            double bid=_symbol.Bid,ask=_symbol.Ask;
            foreach(var t in _v74R18Outcome.Values.Where(x=>!x.Resolved).ToList())
            {
                if(now<=t.DecisionUtc)continue;
                double exitPx=V74R18ExitPrice(t.Direction);

                if(now>=t.DeadlineUtc){V74R18Emit(t,"TIME_EXPIRE",exitPx,now,true);continue;}
                if(!IsInstitutionalSession(now)){V74R18Emit(t,"SESSION_EXPIRE",exitPx,now,true);continue;}

                bool sl=t.Direction==TradeDirection.Buy?bid<=t.Stop:ask>=t.Stop;
                bool tp=t.Direction==TradeDirection.Buy?bid>=t.Target:ask<=t.Target;
                // Chronological ticks remove OHLC ordering ambiguity. If a malformed quote
                // crosses both boundaries simultaneously, fail closed to the loss side.
                if(sl){V74R18Emit(t,"SL_FIRST",exitPx,now,true);continue;}
                if(tp){V74R18Emit(t,"TP_FIRST",exitPx,now,true);continue;}
            }
        }

        private void V74R18FinalizeOpportunity(V72HcogOpportunity o,string result)
        {
            if(!EnableV74R18OutcomeResearch||o==null)return;
            string prefix=(o.SetupKey??"")+"|";
            DateTime now=Server.Time.ToUniversalTime();
            foreach(var t in _v74R18Outcome.Values.Where(x=>!x.Resolved&&x.Key.StartsWith(prefix,StringComparison.Ordinal)).ToList())
            {
                string cause;
                string r=result??"";
                if(r.Contains("180M")||r.Contains("TIMEOUT"))cause="TIME_EXPIRE";
                else if(r.Contains("STRUCTURAL_STOP")||r.Contains("AMBIGUOUS_STOP"))cause="STRUCTURAL_INVALIDATION";
                else if(r.Contains("CANONICAL_TARGET"))cause="PARENT_TARGET_TERMINATION";
                else if(r.Contains("BACKTEST_END"))cause="CENSORED";
                else cause="CENSORED";
                V74R18Emit(t,cause,V74R18ExitPrice(t.Direction),now,true);
            }
        }

        private void V74R18Seal()
        {
            if(!EnableV74R18OutcomeResearch)return;
            DateTime now=Server.Time.ToUniversalTime();
            foreach(var t in _v74R18Outcome.Values.Where(x=>!x.Resolved).ToList())
                V74R18Emit(t,"CENSORED",V74R18ExitPrice(t.Direction),now,true);
            V74R15ResearchPrint(
                "[V74-R18-SUMMARY] schema=V74_R18_OUTCOME_V1 registered={0} resolved={1} nofill={2} censored={3} divergence={4} burnedUsed=false validationUsed=false freshUsed=false",
                _v74R18Registered,_v74R18Resolved,_v74R18NoFill,_v74R18Censored,_v74R18Divergence);
        }
    }
}
