using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    // HCAP: Harmonic Counterfactual Action Policy.
    // The harmonic detector and V51 protected core are frozen. HCAP only decides
    // whether a causally eligible REVERSAL / CONTINUATION action has a positive
    // conservative expected Net-R. NO_TRADE is implicit when LCB <= 0.
    public partial class HarmonyBotV71
    {
        [Parameter("Enable V72 HCAP Alpha", DefaultValue = false)]
        public bool EnableV72HcapAlpha { get; set; }

        [Parameter("V72 HCAP Reversal Model", DefaultValue = "")]
        public string V72HcapReversalModel { get; set; }

        [Parameter("V72 HCAP Continuation Model", DefaultValue = "")]
        public string V72HcapContinuationModel { get; set; }

        [Parameter("V72 HCAP LCB Z", DefaultValue = 1.645, MinValue = 1.0, MaxValue = 3.0)]
        public double V72HcapLcbZ { get; set; }

        private static readonly string[] V72HcapFamilies =
        {
            "Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab",
            "DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"
        };

        private const int V72HcapContinuousFeatureCount = 12;
        private const int V72HcapVectorCount = 25; // intercept + 12 standardized observables + 12 family indicators

        private sealed class V72HcapModel
        {
            public int N;
            public double Sigma;
            public double HoldBars;
            public double[] Mean = new double[V72HcapContinuousFeatureCount];
            public double[] Scale = new double[V72HcapContinuousFeatureCount];
            public double[] Beta = new double[V72HcapVectorCount];
            public double[] Info = new double[V72HcapVectorCount];
        }

        private int _v72HcapScored;
        private int _v72HcapSelected;
        private int _v72HcapRejected;
        private int _v72HcapModelParseFailures;

        private bool V72HcapTryParseModel(string raw, out V72HcapModel m)
        {
            m = null;
            if (string.IsNullOrWhiteSpace(raw)) return false;
            string[] p = raw.Split(',');
            int expected = 3 + V72HcapContinuousFeatureCount * 2 + V72HcapVectorCount * 2;
            if (p.Length != expected) return false;
            var z = new double[p.Length];
            for (int i = 0; i < p.Length; i++)
            {
                if (!double.TryParse(p[i], NumberStyles.Float, CultureInfo.InvariantCulture, out z[i]) ||
                    !double.IsFinite(z[i])) return false;
            }
            int k = 0;
            m = new V72HcapModel
            {
                N = Math.Max(0, (int)Math.Round(z[k++])),
                Sigma = Math.Max(1e-9, z[k++]),
                HoldBars = Math.Max(1.0, z[k++])
            };
            for (int i = 0; i < V72HcapContinuousFeatureCount; i++) m.Mean[i] = z[k++];
            for (int i = 0; i < V72HcapContinuousFeatureCount; i++) m.Scale[i] = Math.Max(1e-9, Math.Abs(z[k++]));
            for (int i = 0; i < V72HcapVectorCount; i++) m.Beta[i] = z[k++];
            for (int i = 0; i < V72HcapVectorCount; i++) m.Info[i] = Math.Max(1e-9, Math.Abs(z[k++]));
            return true;
        }

        private double[] V72HcapRawFeatures(V72HcogOpportunity o)
        {
            PatternSignal s = o == null ? null : o.Signal;
            RegimeSnapshot r = o == null ? null : o.Regime;
            if (s == null) return Enumerable.Repeat(0.0, V72HcapContinuousFeatureCount).ToArray();
            return new[]
            {
                VClamp(s.GeometryQuality),
                VClamp(s.PrzConfluence),
                VClamp(s.Confidence),
                VClamp(s.TimeSymmetry),
                VClamp(s.PivotQuality),
                VClamp(o.NetRr / 4.0),
                r == null ? 0.0 : VClamp(r.Efficiency),
                r == null ? 0.0 : V71AtrFit(r),
                r == null ? 0.0 : VClamp(r.ExtensionAtr / 2.0),
                r == null ? 0.0 : VClamp(r.TrendStrength),
                r == null ? 0.5 : VClamp((r.AdxH1Slope + 1.0) * 0.5),
                V71MtfScore(o.Conflict)
            };
        }

        private double[] V72HcapVector(V72HcogOpportunity o, V72HcapModel m, double[] raw)
        {
            var x = new double[V72HcapVectorCount];
            x[0] = 1.0;
            for (int i = 0; i < V72HcapContinuousFeatureCount; i++)
                x[1 + i] = (raw[i] - m.Mean[i]) / m.Scale[i];
            int fam = Array.FindIndex(V72HcapFamilies,
                f => string.Equals(f, o.Family, StringComparison.OrdinalIgnoreCase));
            if (fam >= 0) x[1 + V72HcapContinuousFeatureCount + fam] = 1.0;
            return x;
        }

        private void V72HcapScoreOpportunity(V72HcogOpportunity o)
        {
            if (o == null) return;
            double[] raw = V72HcapRawFeatures(o);
            o.HcapFeatureCsv = string.Join(",", raw.Select(v => v.ToString("R", CultureInfo.InvariantCulture)));
            o.HcapQ = 0.0;
            o.HcapLcb = 0.0;
            o.HcapHoldBars = 180.0;
            o.HcapSelected = true;

            if (!EnableV72HcapAlpha) return;
            _v72HcapScored++;

            bool continuation = string.Equals(o.Lane, "HCOG_FAILURE_CONTINUATION", StringComparison.Ordinal);
            bool reversal = string.Equals(o.Lane, "HCOG_REVERSAL", StringComparison.Ordinal);
            if (!continuation && !reversal)
            {
                o.HcapSelected = false;
                _v72HcapRejected++;
                return;
            }

            string modelRaw = continuation ? V72HcapContinuationModel : V72HcapReversalModel;
            if (string.IsNullOrWhiteSpace(modelRaw))
            {
                // Census mode: collect unbiased action outcomes. No capital may be
                // queued because EnableV71ExpansionExecution remains false.
                o.HcapSelected = true;
                _v72HcapSelected++;
                return;
            }

            V72HcapModel m;
            if (!V72HcapTryParseModel(modelRaw, out m))
            {
                o.HcapSelected = false;
                o.HcapQ = -999.0;
                o.HcapLcb = -999.0;
                _v72HcapModelParseFailures++;
                _v72HcapRejected++;
                return;
            }

            double[] x = V72HcapVector(o, m, raw);
            double q = 0.0, varianceFactor = 0.0;
            for (int i = 0; i < x.Length; i++)
            {
                q += m.Beta[i] * x[i];
                varianceFactor += x[i] * x[i] / m.Info[i];
            }
            double se = m.Sigma * Math.Sqrt(Math.Max(0.0, varianceFactor));
            double lcb = q - V72HcapLcbZ * se;
            o.HcapQ = q;
            o.HcapLcb = lcb;
            o.HcapHoldBars = m.HoldBars;
            o.HcapSelected = q > 0.0 && lcb > 0.0;
            if (o.HcapSelected) _v72HcapSelected++; else _v72HcapRejected++;

            Print("[V72-HCAP-SCORE] id={0} setup={1} family={2} action={3} n={4} q={5:F9} lcb={6:F9} holdBars={7:F3} selected={8}",
                o.Id, o.SetupKey, o.Family, continuation ? "CONTINUATION" : "REVERSAL",
                m.N, o.HcapQ, o.HcapLcb, o.HcapHoldBars, o.HcapSelected);
        }

        private void V72HcapPrintSummary()
        {
            if (!EnableV72HcapAlpha) return;
            Print("[V72-HCAP-SUMMARY] scored={0} selected={1} rejected={2} modelParseFailures={3} lcbZ={4:F3} noTradePolicy=LCB_NONPOSITIVE",
                _v72HcapScored, _v72HcapSelected, _v72HcapRejected, _v72HcapModelParseFailures, V72HcapLcbZ);
        }
    }
}
