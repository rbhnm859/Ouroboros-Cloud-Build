using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    // V73/V74 research-deployment bridge.
    // V73 broadens ONLY the research opportunity universe; the V51 protected core
    // continues to use its frozen M15SwingDepth and economic path.
    public partial class HarmonyBotV71
    {
        [Parameter("Enable V73 Opportunity Universe", DefaultValue = false)]
        public bool EnableV73OpportunityUniverse { get; set; }

        [Parameter("Enable V74 R17 Tick Research", DefaultValue = false)]
        public bool EnableV74R17TickResearch { get; set; }

        [Parameter("Enable V74 R18 Outcome Research", DefaultValue = false)]
        public bool EnableV74R18OutcomeResearch { get; set; }

        [Parameter("Enable V74 External Frozen Policy", DefaultValue = false)]
        public bool EnableV74ExternalPolicy { get; set; }

        [Parameter("Enable V74 Embedded Frozen Policy", DefaultValue = false)]
        public bool EnableV74EmbeddedPolicy { get; set; }

        [Parameter("V74 Allowed Setup Hashes", DefaultValue = "")]
        public string V74AllowedSetupHashes { get; set; }

        [Parameter("V74 Policy Utility", DefaultValue = "")]
        public string V74PolicyUtility { get; set; }

        [Parameter("V74 Policy Hold Bars", DefaultValue = "")]
        public string V74PolicyHoldBars { get; set; }

        [Parameter("V74 Policy Protection", DefaultValue = "")]
        public string V74PolicyProtection { get; set; }

        private readonly int[] _v73ResearchSwingDepths = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 };

        // Physical completion-event identity. BuildSetupGeometryKey format:
        // Direction|CompletionTime|X|A|B|C|D. X/A/B/C alternatives sharing
        // direction/time/D are confluence hypotheses, not independent supply.
        private string V73EventIdentityKey(PatternSignal s)
        {
            if(s==null)return string.Empty;
            string g=BuildSetupGeometryKey(s);
            var p=(g??string.Empty).Split('|');
            if(p.Length>=7)return p[0]+"|"+p[1]+"|"+p[p.Length-1];
            return g;
        }
        private HashSet<string> _v74AllowedHashes;
        private Dictionary<string,double> _v74Utility;
        private Dictionary<string,double> _v74HoldBars;
        private Dictionary<string,string> _v74Protection;
        private bool _v74PolicyParsed;

        private string V74SetupHash(string s)
        {
            unchecked
            {
                ulong h = 14695981039346656037UL;
                foreach(char c in (s ?? string.Empty))
                {
                    h ^= (byte)(c & 0xff); h *= 1099511628211UL;
                    h ^= (byte)((c >> 8) & 0xff); h *= 1099511628211UL;
                }
                return h.ToString("X16", CultureInfo.InvariantCulture);
            }
        }

        private Dictionary<string,double> V74ParseMap(string raw)
        {
            var d = new Dictionary<string,double>(StringComparer.OrdinalIgnoreCase);
            if(string.IsNullOrWhiteSpace(raw)) return d;
            foreach(var item in raw.Split(new[]{';'}, StringSplitOptions.RemoveEmptyEntries))
            {
                var p=item.Split('=');
                if(p.Length!=2) continue;
                double v;
                if(double.TryParse(p[1],NumberStyles.Float,CultureInfo.InvariantCulture,out v) && double.IsFinite(v))
                    d[p[0].Trim()]=v;
            }
            return d;
        }

        private Dictionary<string,string> V74ParseStringMap(string raw)
        {
            var d = new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
            if(string.IsNullOrWhiteSpace(raw)) return d;
            foreach(var item in raw.Split(new[]{';'}, StringSplitOptions.RemoveEmptyEntries))
            {
                var p=item.Split('=');
                if(p.Length!=2) continue;
                string k=p[0].Trim(),v=p[1].Trim();
                if(k.Length>0&&v.Length>0)d[k]=v;
            }
            return d;
        }

        private void V74EnsurePolicyParsed()
        {
            if(_v74PolicyParsed) return;
            _v74PolicyParsed=true;
            _v74AllowedHashes=new HashSet<string>((V74AllowedSetupHashes??"")
                .Split(new[]{';'},StringSplitOptions.RemoveEmptyEntries).Select(x=>x.Trim()),
                StringComparer.OrdinalIgnoreCase);
            _v74Utility=V74ParseMap(V74PolicyUtility);
            _v74HoldBars=V74ParseMap(V74PolicyHoldBars);
            _v74Protection=V74ParseStringMap(V74PolicyProtection);
            Print("[V74-EXTERNAL-POLICY] allowed={0} utility={1} hold={2} protection={3}",
                _v74AllowedHashes.Count,_v74Utility.Count,_v74HoldBars.Count,_v74Protection.Count);
        }

        // Optional generated implementation is compiled into the post-V77 .algo.
        // With no generated implementation the call is erased by the compiler.
        partial void V74EmbeddedScore(V72HcogOpportunity o, ref bool handled, ref bool selected,
            ref double mean, ref double lcb, ref double holdBars);
        partial void V74EmbeddedProtect(V72HcogOpportunity o, int milestoneIndex, double[] milestoneFeatures,
            ref bool handled, ref bool protect, ref double delta, ref double lcb);

        private void V74FrozenPolicyScoreOpportunity(V72HcogOpportunity o)
        {
            if(o==null)return;
            bool handled=false,selected=false; double mean=0,lcb=0,hold=180;
            if(EnableV74EmbeddedPolicy)
                V74EmbeddedScore(o,ref handled,ref selected,ref mean,ref lcb,ref hold);
            if(handled)
            {
                o.HcapQ=mean;o.HcapLcb=lcb;o.HcapHoldBars=Math.Max(1,hold);o.HcapSelected=selected;
                Print("[V74-EMBEDDED-POLICY] id={0} setupHash={1} family={2} lane={3} mean={4:F9} lcb={5:F9} holdBars={6:F3} selected={7}",
                    o.Id,V74SetupHash(o.SetupKey),o.Family,o.Lane,mean,lcb,o.HcapHoldBars,selected);
                return;
            }
            V74ExternalPolicyScoreOpportunity(o);
        }

        private void V74ExternalPolicyScoreOpportunity(V72HcogOpportunity o)
        {
            if(o==null) return;
            V74EnsurePolicyParsed();
            string h=V74SetupHash(o.SetupKey);
            double u=0,hold=180;
            _v74Utility.TryGetValue(h,out u);
            if(!_v74HoldBars.TryGetValue(h,out hold)) hold=180;
            o.HcapQ=u;
            o.HcapLcb=u;
            o.HcapHoldBars=Math.Max(1,hold);
            o.HcapSelected=_v74AllowedHashes.Contains(h);
            string pk;
            o.V74LiveProtectionKey=_v74Protection.TryGetValue(h,out pk)?pk:"NONE";
            Print("[V74-POLICY-SCORE] id={0} setupHash={1} family={2} lane={3} utility={4:F9} holdBars={5:F3} selected={6} protection={7}",
                o.Id,h,o.Family,o.Lane,u,o.HcapHoldBars,o.HcapSelected,o.V74LiveProtectionKey);
        }

        // Additive, observation-only instrumentation. No change to V51 capital, orders,
        // profile coordinates, matching decisions, or action rankings.
        private readonly Dictionary<string,long> _v74FamilyResearchFunnel = new Dictionary<string,long>(StringComparer.Ordinal);
        private void V74FamilyResearchCount(string family,string stage)
        {
            if(!EnableV73OpportunityUniverse)return;
            string key=V71FamilyKey(family)+"|"+stage;
            long n;
            _v74FamilyResearchFunnel.TryGetValue(key,out n);
            _v74FamilyResearchFunnel[key]=n+1L;
        }

        // Research counts must distinguish repeated bar-by-bar checks from
        // distinct matched geometries and distinct physical completion events.
        private readonly HashSet<string> _v74ResearchStageUnique = new HashSet<string>(StringComparer.Ordinal);
        private readonly HashSet<string> _v74ResearchPhysicalEvents = new HashSet<string>(StringComparer.Ordinal);

        private void V74FamilyResearchCountOnce(PatternSignal s,string stage)
        {
            if(!EnableV73OpportunityUniverse||s==null)return;
            string id=V71FamilyKey(s.PatternName)+"|"+BuildSetupGeometryKey(s)+"|"+s.PivotScale;
            if(_v74ResearchStageUnique.Add(stage+"|"+id))
                V74FamilyResearchCount(s.PatternName,stage);
        }

        private void V74FamilyResearchPhysicalEventOnce(PatternSignal s)
        {
            if(!EnableV73OpportunityUniverse||s==null)return;
            if(_v74ResearchStageUnique.Add("PHYSICAL_FAMILY|"+V71FamilyKey(s.PatternName)+"|"+V73EventIdentityKey(s)))
                V74FamilyResearchCount(s.PatternName,"PHYSICAL_FAMILY_EVENT");
            _v74ResearchPhysicalEvents.Add(V73EventIdentityKey(s));
        }

        private List<PatternSignal> V73BuildOpportunityPool(int m15Index,int defaultLimit)
        {
            var all=new List<PatternSignal>();
            double atr=Atr(_m15Bars,14,m15Index);
            if(atr<=0)return all;

            // Supply reconstruction only. All family identity / Fibonacci ratio / PRZ
            // contracts stay inside the frozen V71 matcher. V73 only broadens the
            // confirmed-pivot topology (depths 2..8) before canonical de-duplication.
            foreach(int depth in _v73ResearchSwingDepths)
            {
                var pivots=BuildConfirmedPivots(_m15Bars,m15Index,M15SwingLookback,depth);
                if(pivots.Count<5)continue;

                for(int dPos=Math.Max(4,pivots.Count-24);dPos<pivots.Count;dPos++)
                {
                    var d=pivots[dPos];
                    if(m15Index-d.Index>10)continue;

                    int c0=Math.Max(3,dPos-5);
                    for(int cPos=c0;cPos<dPos;cPos++)
                    {
                        if(!V71SparseLegInsideEnvelope(pivots,cPos,dPos))continue;
                        int b0=Math.Max(2,cPos-5);
                        for(int bPos=b0;bPos<cPos;bPos++)
                        {
                            if(!V71SparseLegInsideEnvelope(pivots,bPos,cPos))continue;
                            int a0=Math.Max(1,bPos-5);
                            for(int aPos=a0;aPos<bPos;aPos++)
                            {
                                if(!V71SparseLegInsideEnvelope(pivots,aPos,bPos))continue;
                                int x0=Math.Max(0,aPos-5);
                                for(int xPos=x0;xPos<aPos;xPos++)
                                {
                                    if(dPos-xPos>16||!V71SparseLegInsideEnvelope(pivots,xPos,aPos))continue;
                                    var x=pivots[xPos];var a=pivots[aPos];var b=pivots[bPos];var c=pivots[cPos];

                                    foreach(var profile in _profiles)
                                    {
                                        V74FamilyResearchCount(profile.Name,"ATTEMPTED");
                                        string rejectReason;
                                        if(!V71ExpansionPrimaryContractPass(profile,x,a,b,c,d,atr,out rejectReason))
                                        {
                                            V74FamilyResearchCount(profile.Name,"REJECT_"+rejectReason);
                                            continue;
                                        }
                                        V74FamilyResearchCount(profile.Name,"PRIMARY_PASS");
                                        PatternSignal sig;
                                        if(!TryMatchProfile(profile,x,a,b,c,d,atr,_m15Bars.OpenTimes[d.Index],"M15",depth,out sig,false))
                                        {
                                            V74FamilyResearchCount(profile.Name,"REJECT_MATCHER");
                                            continue;
                                        }
                                        V74FamilyResearchCount(profile.Name,"MATCH_PASS");
                                        if(m15Index-d.Index>Math.Max(2,profile.MaxAgeM15Bars))
                                        {
                                            V74FamilyResearchCount(profile.Name,"REJECT_AGE");
                                            continue;
                                        }
                                        V74FamilyResearchCount(profile.Name,"AGE_PASS");
                                        all.Add(sig);
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Preserve family interpretation first, then canonicalize exact geometry.
            // No PnL, year, route profitability or capital availability enters this pool.
            var familyNative=all
                .GroupBy(x=>V71FamilyKey(x.PatternName)+"|"+BuildSetupGeometryKey(x)+"|"+x.PivotScale)
                .Select(g=>g.OrderByDescending(x=>x.Confidence).ThenByDescending(x=>x.GeometryQuality).First())
                .OrderByDescending(x=>x.Confidence).ThenByDescending(x=>x.GeometryQuality).ToList();

            foreach(var signal in familyNative)
                signal.ResearchRole=V71AbcdResearchRole(signal,familyNative);

            var selected=familyNative.Take(Math.Max(128,Math.Min(1024,defaultLimit*8))).ToList();
            // The census is counted before selection. Same-event family hypotheses
            // are visible but must NEVER be treated as independent baskets.
            if(EnableV73OpportunityUniverse)
            {
                foreach(var s in familyNative)
                {
                    V74FamilyResearchCountOnce(s,"FAMILY_UNIQUE_GEOMETRY");
                    V74FamilyResearchPhysicalEventOnce(s);
                }
                foreach(var s in selected)V74FamilyResearchCountOnce(s,"RETURNED_GEOMETRY");
            }
            return selected;
        }

        private void V73PrintUniverseSummary()
        {
            if(!EnableV73OpportunityUniverse)return;
            Print("[V73-UNIVERSE-SUMMARY] swingDepths=1,2,3,4,5,6,7,8,9,10,11,12 independentDetected={0} przTouched={1} causalProofs={2} closedOutcomes={3} abcdPrimitive={4} coreOverlapObserved={5} capitalExecutionUsed=False",
                _v72HcogDetected,_v72HcogPrzTouched,_v72HcogProofs,_v72HcogClosed,_v72HcogAbcdPrimitive,_v72HcogCoreOverlapAtEntry);
            // One summary per real matcher/geometry rejection reason. No throttled
            // per-tick logging and no exposure of orders, credentials or PnL.
            foreach(var p in _profiles)
            {
                var family=V71FamilyKey(p.Name);
                foreach(var stage in new[]{"ATTEMPTED","PRIMARY_PASS","MATCH_PASS","AGE_PASS","FAMILY_UNIQUE_GEOMETRY","PHYSICAL_FAMILY_EVENT","RETURNED_GEOMETRY"})
                {
                    long n;
                    _v74FamilyResearchFunnel.TryGetValue(family+"|"+stage,out n);
                    Print("[V74-FAMILY-FUNNEL] family={0} stage={1} n={2}",family,stage,n);
                }
            }
            Print("[V74-FAMILY-PHYSICAL-UNIQUE] n={0} unit=direction_completion_time_d",_v74ResearchPhysicalEvents.Count);
            foreach(var kv in _v74FamilyResearchFunnel.Where(k=>k.Key.Contains("|REJECT_")).OrderBy(k=>k.Key))
            {
                int cut=kv.Key.IndexOf('|');
                Print("[V74-FAMILY-FUNNEL] family={0} stage={1} n={2}",
                    kv.Key.Substring(0,cut),kv.Key.Substring(cut+1),kv.Value);
            }
        }
    }
}
