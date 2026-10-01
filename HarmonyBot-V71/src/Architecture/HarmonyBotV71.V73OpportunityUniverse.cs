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

        private readonly int[] _v73ResearchSwingDepths = { 2, 3, 4, 5 };
        private HashSet<string> _v74AllowedHashes;
        private Dictionary<string,double> _v74Utility;
        private Dictionary<string,double> _v74HoldBars;
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

        private void V74EnsurePolicyParsed()
        {
            if(_v74PolicyParsed) return;
            _v74PolicyParsed=true;
            _v74AllowedHashes=new HashSet<string>((V74AllowedSetupHashes??"")
                .Split(new[]{';'},StringSplitOptions.RemoveEmptyEntries).Select(x=>x.Trim()),
                StringComparer.OrdinalIgnoreCase);
            _v74Utility=V74ParseMap(V74PolicyUtility);
            _v74HoldBars=V74ParseMap(V74PolicyHoldBars);
            Print("[V74-EXTERNAL-POLICY] allowed={0} utility={1} hold={2}",
                _v74AllowedHashes.Count,_v74Utility.Count,_v74HoldBars.Count);
        }

        // Optional generated implementation is compiled into the post-V77 .algo.
        // With no generated implementation the call is erased by the compiler.
        partial void V74EmbeddedScore(V72HcogOpportunity o, ref bool handled, ref bool selected,
            ref double mean, ref double lcb, ref double holdBars);

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
            Print("[V74-POLICY-SCORE] id={0} setupHash={1} family={2} lane={3} utility={4:F9} holdBars={5:F3} selected={6}",
                o.Id,h,o.Family,o.Lane,u,o.HcapHoldBars,o.HcapSelected);
        }

        private List<PatternSignal> V73BuildOpportunityPool(int m15Index,int defaultLimit)
        {
            var all=new List<PatternSignal>();
            foreach(int depth in _v73ResearchSwingDepths)
            {
                var xs=V71DetectExpansionPatternCandidates(_m15Bars,m15Index,depth,M15SwingLookback,
                    Math.Max(64,defaultLimit),"M15-V73-D"+depth.ToString(CultureInfo.InvariantCulture));
                if(xs!=null) all.AddRange(xs);
            }
            return all;
        }

        private void V73PrintUniverseSummary()
        {
            if(!EnableV73OpportunityUniverse)return;
            Print("[V73-UNIVERSE-SUMMARY] swingDepths=2,3,4,5 independentDetected={0} przTouched={1} causalProofs={2} closedOutcomes={3} abcdPrimitive={4} coreOverlapObserved={5} capitalExecutionUsed=False",
                _v72HcogDetected,_v72HcogPrzTouched,_v72HcogProofs,_v72HcogClosed,_v72HcogAbcdPrimitive,_v72HcogCoreOverlapAtEntry);
        }
    }
}
