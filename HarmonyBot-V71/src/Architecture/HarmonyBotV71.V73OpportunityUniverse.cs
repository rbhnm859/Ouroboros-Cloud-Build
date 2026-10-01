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

        [Parameter("V74 Policy Reaction", DefaultValue = "")]
        public string V74PolicyReaction { get; set; }

        private readonly int[] _v73ResearchSwingDepths = { 2, 3, 4, 5, 6, 7, 8 };
        private HashSet<string> _v74AllowedHashes;
        private Dictionary<string,double> _v74Utility;
        private Dictionary<string,double> _v74HoldBars;
        private Dictionary<string,string> _v74Protection;
        private Dictionary<string,string> _v74Reaction;
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
            _v74Reaction=V74ParseStringMap(V74PolicyReaction);
            Print("[V74-EXTERNAL-POLICY] allowed={0} utility={1} hold={2} protection={3} reaction={4}",
                _v74AllowedHashes.Count,_v74Utility.Count,_v74HoldBars.Count,_v74Protection.Count,_v74Reaction.Count);
        }

        // Optional generated implementation is compiled into the post-V77 .algo.
        // With no generated implementation the call is erased by the compiler.
        partial void V74EmbeddedScore(V72HcogOpportunity o, ref bool handled, ref bool selected,
            ref double mean, ref double lcb, ref double holdBars);
        partial void V74EmbeddedProtect(V72HcogOpportunity o, int milestoneIndex, double[] milestoneFeatures,
            ref bool handled, ref bool protect, ref double delta, ref double lcb);
        partial void V74EmbeddedReaction(V72HcogOpportunity o, ref bool handled, ref string reactionKey);

        private void V74FrozenPolicyScoreOpportunity(V72HcogOpportunity o)
        {
            if(o==null)return;
            bool handled=false,selected=false; double mean=0,lcb=0,hold=180;
            if(EnableV74EmbeddedPolicy)
                V74EmbeddedScore(o,ref handled,ref selected,ref mean,ref lcb,ref hold);
            if(handled)
            {
                o.HcapQ=mean;o.HcapLcb=lcb;o.HcapHoldBars=Math.Max(1,hold);o.HcapSelected=selected;
                bool reactionHandled=false;string reactionKey="NONE";
                if(selected)V74EmbeddedReaction(o,ref reactionHandled,ref reactionKey);
                o.V74LiveReactionKey=reactionHandled&&!string.IsNullOrWhiteSpace(reactionKey)?reactionKey:"NONE";
                Print("[V74-EMBEDDED-POLICY] id={0} setupHash={1} family={2} lane={3} mean={4:F9} lcb={5:F9} holdBars={6:F3} selected={7} reaction={8}",
                    o.Id,V74SetupHash(o.SetupKey),o.Family,o.Lane,mean,lcb,o.HcapHoldBars,selected,o.V74LiveReactionKey);
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
            string pk,rk;
            o.V74LiveProtectionKey=_v74Protection.TryGetValue(h,out pk)?pk:"NONE";
            o.V74LiveReactionKey=_v74Reaction.TryGetValue(h,out rk)?rk:"NONE";
            if(o.HcapSelected&&_v74Reaction.Count>0&&o.V74LiveReactionKey=="NONE")o.HcapSelected=false;
            Print("[V74-POLICY-SCORE] id={0} setupHash={1} family={2} lane={3} utility={4:F9} holdBars={5:F3} selected={6} protection={7} reaction={8}",
                o.Id,h,o.Family,o.Lane,u,o.HcapHoldBars,o.HcapSelected,o.V74LiveProtectionKey,o.V74LiveReactionKey);
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

                for(int dPos=Math.Max(4,pivots.Count-18);dPos<pivots.Count;dPos++)
                {
                    var d=pivots[dPos];
                    if(m15Index-d.Index>8)continue;

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
                                        string rejectReason;
                                        if(!V71ExpansionPrimaryContractPass(profile,x,a,b,c,d,atr,out rejectReason))
                                            continue;

                                        PatternSignal sig;
                                        if(!TryMatchProfile(profile,x,a,b,c,d,atr,_m15Bars.OpenTimes[d.Index],"M15",depth,out sig,false))
                                            continue;
                                        if(m15Index-d.Index>Math.Max(2,profile.MaxAgeM15Bars))
                                            continue;
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

            return familyNative.Take(Math.Max(128,Math.Min(1024,defaultLimit*8))).ToList();
        }

        private void V73PrintUniverseSummary()
        {
            if(!EnableV73OpportunityUniverse)return;
            Print("[V73-UNIVERSE-SUMMARY] swingDepths=2,3,4,5,6,7,8 independentDetected={0} przTouched={1} causalProofs={2} closedOutcomes={3} abcdPrimitive={4} coreOverlapObserved={5} capitalExecutionUsed=False",
                _v72HcogDetected,_v72HcogPrzTouched,_v72HcogProofs,_v72HcogClosed,_v72HcogAbcdPrimitive,_v72HcogCoreOverlapAtEntry);
        }
    }
}
