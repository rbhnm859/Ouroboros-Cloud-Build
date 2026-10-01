using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    // Candidate-state, telemetry and numerical helper layer.
    // No alpha admission semantics are introduced here.
    public partial class HarmonyBotV71
    {
        // ---------------- Candidate state / telemetry ----------------

        private string BuildSetupGeometryKey(PatternSignal s)
        {
            if (s == null) return "INVALID";
            string px(double v) { return Math.Round(v, _symbol.Digits).ToString("F" + _symbol.Digits, CultureInfo.InvariantCulture); }
            return s.Direction + "|" + s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture) + "|" +
                   px(s.X.Price) + "|" + px(s.A.Price) + "|" + px(s.B.Price) + "|" + px(s.C.Price) + "|" + px(s.D.Price);
        }

        private string NewCandidateId(PatternSignal s)
        {
            _candidateSeq++;
            return "V47-" + _candidateSeq.ToString("D8", CultureInfo.InvariantCulture) + "-" +
                   s.PatternName.Replace(" ", "") + "-" + s.Direction + "-" + s.CompletionTime.ToString("yyyyMMddHHmm", CultureInfo.InvariantCulture);
        }

        private void Transition(CandidateRecord c, CandidateState next, string reason)
        {
            CandidateState prior = c.State;
            c.State = next;
            c.LastReason = reason;
            Event(c, prior + "->" + next + ":" + reason);
        }

        private void Reject(CandidateRecord c, string reason)
        {
            c.State = CandidateState.REJECTED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Rejected++;
            Event(c, "REJECTED:" + reason);
        }

        private void Expire(CandidateRecord c, string reason)
        {
            c.State = CandidateState.EXPIRED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Expired++;
            Event(c, "EXPIRED:" + reason);
        }

        private void Invalidate(CandidateRecord c, string reason)
        {
            c.State = CandidateState.INVALIDATED;
            c.IsActive = false;
            if (c != null) _parkedCandidateIds.Remove(c.CandidateId);
            if (EnableCanonicalSetupIdentity && c != null && !string.IsNullOrWhiteSpace(c.SetupKey)) _activeSetupOwners.Remove(c.SetupKey);
            c.LastReason = reason;
            CountPipeline(c.Signal.PatternName).Invalidated++;
            Event(c, "INVALIDATED:" + reason);
        }

        private void Ledger(CandidateRecord c, CandidateState state, string reason)
        {
            double wait = c.ParkedUtc.HasValue ? Math.Max(0, (Server.Time.ToUniversalTime() - c.ParkedUtc.Value).TotalMinutes) : 0;
            Print("[V51-EVENT] cid={0} setup={1} pattern={2} subtype={3} scale={4} tf={5} dir={6} state={7} route={8} conflict={9} waitMin={10:F2} reason={11}",
                c.CandidateId, c.SetupKey ?? "", c.Signal.PatternName, c.Signal.HarmonicSubtype ?? c.Signal.PatternName,
                c.Signal.PivotScale, c.Signal.Timeframe, c.Signal.Direction, state, c.Route, c.Conflict, wait, reason);
        }

        private void Event(CandidateRecord c, string reason)
        {
            Ledger(c, c.State, reason);
        }

        private PipelineCounter CountPipeline(string pattern)
        {
            PipelineCounter x;
            if (!_pipeline.TryGetValue(pattern, out x))
            {
                x = new PipelineCounter();
                _pipeline[pattern] = x;
            }
            return x;
        }

        private void TrimCandidateBook()
        {
            if (_candidates.Count <= 2000) return;
            foreach (var k in _candidates.Where(kv => !kv.Value.IsActive).OrderBy(kv => kv.Value.DetectedUtc).Take(_candidates.Count - 1500).Select(kv => kv.Key).ToList())
                _candidates.Remove(k);
        }

        private bool PatternInvalidatedBeforeEntry(PatternSignal s)
        {
            return s.Direction == TradeDirection.Buy ? _symbol.Bid <= s.StructuralInvalidation : _symbol.Ask >= s.StructuralInvalidation;
        }

        // ---------------- Math ----------------

        private bool BarsObjectsReady()
        {
            return _h4Bars != null && _h1Bars != null && _m15Bars != null && _m1Bars != null;
        }

        private void WarmupBars(Bars bars, int minimum, string name)
        {
            if (bars == null) return;
            int loops = 0;
            while (bars.Count < minimum && loops < 32)
            {
                int added = 0;
                try { added = bars.LoadMoreHistory(); }
                catch (Exception ex)
                {
                    Print("[V51-WARMUP-ERROR] tf={0} count={1} error={2}", name, bars.Count, ex.Message);
                    break;
                }
                loops++;
                Print("[V51-WARMUP] tf={0} added={1} count={2}", name, added, bars.Count);
                if (added <= 0) break;
            }
        }

        private bool BarsReady()
        {
            return BarsObjectsReady() && Count(_h4Bars) >= 230 && Count(_h1Bars) >= 230 && Count(_m15Bars) >= 360 && Count(_m1Bars) >= 50;
        }

        private int Count(Bars b) { return b == null ? 0 : b.Count; }
        private int LastClosedIndex(Bars b) { return b == null ? -1 : b.Count - 2; }
        private double PriceToPips(double d) { return _symbol.PipSize > 0 ? d / _symbol.PipSize : 0; }
        private double PipsToPrice(double p) { return p * _symbol.PipSize; }
        private bool InRange(double x, double a, double b) { return x >= a && x <= b; }
        private double Mid(double a, double b) { return (a + b) / 2.0; }
        private double VClamp(double x) { return Math.Max(0, Math.Min(1, x)); }
        private double RatioScore(double x, double ideal) { return ideal <= 0 ? 0 : VClamp(1.0 - Math.Abs(x - ideal) / ideal); }
        private double Symmetry(double a, double b) { return a <= 0 || b <= 0 ? 0 : Math.Min(a, b) / Math.Max(a, b); }

        private bool GeometryValid(TradeDirection d, double entry, double sl, double tp)
        {
            return d == TradeDirection.Buy ? sl < entry && entry < tp : tp < entry && entry < sl;
        }

        private double Atr(Bars bars, int period, int end)
        {
            if (bars == null || end < period + 1 || end >= bars.Count) return 0;
            double sum = 0;
            for (int i = end - period + 1; i <= end; i++)
            {
                double h = bars.HighPrices[i], l = bars.LowPrices[i], pc = bars.ClosePrices[i - 1];
                sum += Math.Max(h - l, Math.Max(Math.Abs(h - pc), Math.Abs(l - pc)));
            }
            return sum / period;
        }

        private double RollingAtrMean(Bars bars, int period, int end, int lookback)
        {
            int start = Math.Max(period + 1, end - lookback + 1);
            double sum = 0; int n = 0;
            for (int i = start; i <= end; i++)
            {
                double a = Atr(bars, period, i);
                if (a > 0) { sum += a; n++; }
            }
            return n > 0 ? sum / n : 0;
        }

        private double AtrPercentile(Bars bars, int period, int end, int lookback)
        {
            double now = Atr(bars, period, end);
            if (now <= 0) return .5;
            int start = Math.Max(period + 1, end - lookback + 1), n = 0, below = 0;
            for (int i = start; i <= end; i++)
            {
                double a = Atr(bars, period, i);
                if (a <= 0) continue;
                n++; if (a <= now) below++;
            }
            return n > 0 ? (double)below / n : .5;
        }

        private double Ema(DataSeries s, int period, int end)
        {
            if (s == null || end <= 0 || end >= s.Count) return 0;
            int start = Math.Max(0, end - period * 6);
            double k = 2.0 / (period + 1.0), ema = s[start];
            for (int i = start + 1; i <= end; i++) ema = s[i] * k + ema * (1.0 - k);
            return ema;
        }

        private int TrendVote(double fast, double slow, double slope)
        {
            if (fast > slow && slope > 0) return 1;
            if (fast < slow && slope < 0) return -1;
            return 0;
        }

        private double EfficiencyRatio(DataSeries s, int end, int period)
        {
            if (s == null || end < period || end >= s.Count) return 0;
            double net = Math.Abs(s[end] - s[end - period]), path = 0;
            for (int i = end - period + 1; i <= end; i++) path += Math.Abs(s[i] - s[i - 1]);
            return path > 0 ? VClamp(net / path) : 0;
        }    }
}
