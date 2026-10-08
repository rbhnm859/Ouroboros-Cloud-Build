using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    public partial class HarmonyBotV71
    {
        private const int V74R17Minutes = 12;
        private const int V74R17Bins = 8;
        private const int V74R17Channels = 28;

        private sealed class V74R17TickMinute
        {
            public DateTime OpenUtc;
            public int Count;
            public DateTime FirstTime;
            public DateTime LastTime;
            public double FirstBid;
            public double FirstAsk;
            public double FirstMid;
            public double LastBid;
            public double LastAsk;
            public double LastMid;
            public double MinMid = double.PositiveInfinity;
            public double MaxMid = double.NegativeInfinity;
            public double SumDt;
            public double SumDtSq;
            public double MaxDt;
            public double Path;
            public double SqMove;
            public double SumSpread;
            public double SumSpreadSq;
            public double MaxSpread;
            public int Up;
            public int Down;
            public int Flat;
            public int Reversals;
            public int LastDirection;
            public int CurrentRun;
            public int MaxUpRun;
            public int MaxDownRun;
            public int BidOnly;
            public int AskOnly;
            public int Both;
            public readonly int[] BinCount = new int[V74R17Bins];
            public readonly double[] BinLastMid = new double[V74R17Bins];
            public readonly bool[] BinSeen = new bool[V74R17Bins];

            // V74-R18 causal truth: this accumulator is only defined for a
            // strictly oldest-to-newest tick feed. A newest-to-oldest feed made
            // Math.Max(0, timeUtc - LastTime) collapse every inter-tick interval
            // to zero and swapped FirstMid/LastMid.
            public void Add(DateTime timeUtc, double bid, double ask, double pip)
            {
                double mid = (bid + ask) * .5;
                double spread = Math.Max(0.0, ask - bid);
                if (!double.IsFinite(mid) || !double.IsFinite(spread)) return;

                if (Count == 0)
                {
                    FirstTime = timeUtc;
                    LastTime = timeUtc;
                    FirstBid = LastBid = bid;
                    FirstAsk = LastAsk = ask;
                    FirstMid = LastMid = mid;
                    MinMid = MaxMid = mid;
                }
                else
                {
                    double dt = Math.Max(0.0, (timeUtc - LastTime).TotalSeconds);
                    SumDt += dt;
                    SumDtSq += dt * dt;
                    MaxDt = Math.Max(MaxDt, dt);

                    double move = mid - LastMid;
                    Path += Math.Abs(move);
                    SqMove += move * move;
                    double eps = Math.Max(pip * .01, 1e-12);
                    int dir = move > eps ? 1 : (move < -eps ? -1 : 0);
                    if (dir > 0) Up++;
                    else if (dir < 0) Down++;
                    else Flat++;

                    if (dir != 0)
                    {
                        if (LastDirection != 0 && dir != LastDirection) Reversals++;
                        if (dir == LastDirection) CurrentRun++;
                        else CurrentRun = 1;
                        if (dir > 0) MaxUpRun = Math.Max(MaxUpRun, CurrentRun);
                        else MaxDownRun = Math.Max(MaxDownRun, CurrentRun);
                        LastDirection = dir;
                    }

                    bool bidChanged = Math.Abs(bid - LastBid) > eps;
                    bool askChanged = Math.Abs(ask - LastAsk) > eps;
                    if (bidChanged && askChanged) Both++;
                    else if (bidChanged) BidOnly++;
                    else if (askChanged) AskOnly++;

                    LastTime = timeUtc;
                    LastBid = bid;
                    LastAsk = ask;
                    LastMid = mid;
                    MinMid = Math.Min(MinMid, mid);
                    MaxMid = Math.Max(MaxMid, mid);
                }

                SumSpread += spread;
                SumSpreadSq += spread * spread;
                MaxSpread = Math.Max(MaxSpread, spread);

                double sec = (timeUtc - OpenUtc).TotalSeconds;
                int bin = Math.Max(0, Math.Min(V74R17Bins - 1, (int)Math.Floor(sec / (60.0 / V74R17Bins))));
                BinCount[bin]++;
                BinLastMid[bin] = mid;
                BinSeen[bin] = true;
                Count++;
            }

            public double[] FilledBinMid()
            {
                var x = new double[V74R17Bins];
                double first = FirstMid;
                for (int i = 0; i < V74R17Bins; i++)
                {
                    if (BinSeen[i]) { first = BinLastMid[i]; x[i] = first; }
                    else x[i] = first;
                }
                for (int i = V74R17Bins - 2; i >= 0; i--)
                    if (!BinSeen[i] && i == 0) x[i] = FirstMid;
                return x;
            }

            public double[] Features(double atr, double pip)
            {
                atr = Math.Max(pip, atr);
                int moves = Math.Max(1, Count - 1);
                double meanDt = moves > 0 ? SumDt / moves : 0.0;
                double varDt = moves > 1 ? Math.Max(0.0, SumDtSq / moves - meanDt * meanDt) : 0.0;
                double spreadMean = Count > 0 ? SumSpread / Count : 0.0;
                double spreadVar = Count > 1 ? Math.Max(0.0, SumSpreadSq / Count - spreadMean * spreadMean) : 0.0;
                int directional = Math.Max(1, Up + Down);
                double imbalance = (double)(Up - Down) / directional;

                double binMean = BinCount.Average();
                double binVar = BinCount.Select(v => (v - binMean) * (v - binMean)).Average();
                int early = BinCount[0] + BinCount[1];
                int late = BinCount[V74R17Bins - 2] + BinCount[V74R17Bins - 1];
                double activityTilt = (double)(late - early) / Math.Max(1, late + early);

                var bins = FilledBinMid();
                var f = new List<double>
                {
                    Math.Log(1.0 + Count),
                    meanDt / 60.0,
                    Math.Sqrt(varDt) / Math.Max(.05, meanDt),
                    MaxDt / 60.0,
                    (LastMid - FirstMid) / atr,
                    (MaxMid - MinMid) / atr,
                    Path / atr,
                    (LastMid - FirstMid) / Math.Max(pip, Path),
                    Math.Sqrt(Math.Max(0.0, SqMove)) / atr,
                    imbalance,
                    (double)Reversals / directional,
                    (double)MaxUpRun / Math.Max(1, Count),
                    (double)MaxDownRun / Math.Max(1, Count),
                    spreadMean / atr,
                    MaxSpread / atr,
                    Math.Sqrt(spreadVar) / Math.Max(pip, spreadMean),
                    (double)BidOnly / Math.Max(1, Count),
                    (double)AskOnly / Math.Max(1, Count),
                    Math.Sqrt(binVar) / Math.Max(1.0, binMean),
                    activityTilt
                };
                for (int i = 0; i < V74R17Bins; i++) f.Add((bins[i] - FirstMid) / atr);
                if (f.Count != V74R17Channels || f.Any(v => !double.IsFinite(v)))
                    throw new InvalidOperationException("R17_TICK_FEATURE_CONTRACT");
                return f.ToArray();
            }
        }

        private Ticks _v74R17Ticks;
        private readonly Dictionary<DateTime, V74R17TickMinute> _v74R17MinuteCache =
            new Dictionary<DateTime, V74R17TickMinute>();

        private static DateTime V74R17FloorMinute(DateTime t)
        {
            t = t.ToUniversalTime();
            return new DateTime(t.Year, t.Month, t.Day, t.Hour, t.Minute, 0, DateTimeKind.Utc);
        }

        private void V74R17EnsureTicks(DateTime fromUtc)
        {
            if (_v74R17Ticks == null) _v74R17Ticks = MarketData.GetTicks(SymbolName);
            int guard = 0;
            while (_v74R17Ticks.Count == 0 ||
                   _v74R17Ticks[0].Time.ToUniversalTime() > fromUtc)
            {
                int loaded = _v74R17Ticks.LoadMoreHistory();
                if (loaded <= 0) break;
                guard++;
                if (guard > 5000) throw new InvalidOperationException("R17_TICK_HISTORY_GUARD");
            }
        }

        // Seek only the exact [open, end) tick interval. The tick collection is
        // oldest-first and LoadMoreHistory prepends older ticks (official API).
        // The slice is then accumulated in ascending time order so that every
        // inter-tick interval, directional run and per-bin last-mid observation
        // is computed causally. The legacy newest-to-oldest feed is permanently
        // separated as fingerprint V74_R17_TICK_V1/V2 and is never produced again.
        private int V74R17LowerBoundTick(DateTime utc)
        {
            int lo = 0, hi = _v74R17Ticks.Count;
            while (lo < hi)
            {
                int mid = lo + ((hi - lo) >> 1);
                if (_v74R17Ticks[mid].Time.ToUniversalTime() < utc) lo = mid + 1;
                else hi = mid;
            }
            return lo;
        }

        private V74R17TickMinute V74R17GetMinute(DateTime openUtc)
        {
            V74R17TickMinute cached;
            if (_v74R17MinuteCache.TryGetValue(openUtc, out cached)) return cached;

            DateTime endUtc = openUtc.AddMinutes(1);
            V74R17EnsureTicks(openUtc);
            if (_v74R17Ticks == null || _v74R17Ticks.Count == 0) return null;

            int n = _v74R17Ticks.Count;
            if (_v74R17Ticks[0].Time.ToUniversalTime() >
                _v74R17Ticks[n - 1].Time.ToUniversalTime())
                throw new InvalidOperationException("R17_TICK_SERIES_ORDER");
            int first = V74R17LowerBoundTick(openUtc);
            int pastEnd = V74R17LowerBoundTick(endUtc);
            if (first > pastEnd ||
                (first > 0 && _v74R17Ticks[first - 1].Time.ToUniversalTime() >= openUtc) ||
                (first < n && _v74R17Ticks[first].Time.ToUniversalTime() < openUtc) ||
                (pastEnd > 0 && _v74R17Ticks[pastEnd - 1].Time.ToUniversalTime() >= endUtc) ||
                (pastEnd < n && _v74R17Ticks[pastEnd].Time.ToUniversalTime() < endUtc))
                throw new InvalidOperationException("R17_TICK_LOWER_BOUND_CONTRACT");

            var z = new V74R17TickMinute { OpenUtc = openUtc };
            // V74-R18 causal truth: accumulate the exact slice oldest-to-newest.
            // The previous descending feed forced every interval through
            // Math.Max(0,...) to zero and inverted the mid-price direction
            // channels, so the corrected fingerprint is a new schema.
            bool havePrev = false;
            DateTime prevUtc = default(DateTime);
            for (int k = first; k < pastEnd; k++)
            {
                Tick tick = _v74R17Ticks[k];
                DateTime t = tick.Time.ToUniversalTime();
                if (t < openUtc) continue;
                if (t >= endUtc) break;
                if (havePrev && t < prevUtc)
                    throw new InvalidOperationException("R17_TICK_TIME_DIRECTION");
                havePrev = true;
                prevUtc = t;
                z.Add(t, tick.Bid, tick.Ask, _symbol.PipSize);
            }
            if (z.Count < 2) return null;

            _v74R17MinuteCache[openUtc] = z;
            if (_v74R17MinuteCache.Count > 512)
            {
                foreach (var key in _v74R17MinuteCache.Keys.OrderBy(x => x).Take(_v74R17MinuteCache.Count - 384).ToList())
                    _v74R17MinuteCache.Remove(key);
            }
            return z;
        }

        private void V74R17EmitTickState(V72HcogOpportunity o, int i)
        {
            if (!EnableV74R17TickResearch) return;
            if (!EnableV73OpportunityUniverse || o == null || o.Signal == null || o.Signal.D == null ||
                i < 32 || i > LastClosedIndex(_m1Bars) || !(o.RiskDistance > 0) || !double.IsFinite(o.RiskDistance))
                throw new InvalidOperationException("R17_CAUSAL_CONTRACT");

            DateTime decision = DateTime.SpecifyKind(_m1Bars.OpenTimes[i], DateTimeKind.Utc).AddMinutes(1);
            DateTime firstMinute = DateTime.SpecifyKind(_m1Bars.OpenTimes[i - V74R17Minutes + 1], DateTimeKind.Utc);
            if (firstMinute.AddMinutes(V74R17Minutes) != decision)
                throw new InvalidOperationException("R17_DECISION_ALIGNMENT");

            var rows = new List<double[]>();
            var rawSequence = new List<double>();
            int totalTicks = 0;
            for (int j = i - V74R17Minutes + 1; j <= i; j++)
            {
                DateTime open = DateTime.SpecifyKind(_m1Bars.OpenTimes[j], DateTimeKind.Utc);
                var minute = V74R17GetMinute(open);
                if (minute == null) return;
                double atr = Atr(_m1Bars, 14, j);
                if (!(atr > 0) || !double.IsFinite(atr)) throw new InvalidOperationException("R17_ATR_CONTRACT");
                rows.Add(minute.Features(atr, _symbol.PipSize));
                totalTicks += minute.Count;
                rawSequence.AddRange(minute.FilledBinMid());
            }
            if (rows.Count != V74R17Minutes || rawSequence.Count != V74R17Minutes * V74R17Bins) return;

            double risk = Math.Max(_symbol.PipSize, o.RiskDistance);
            double d = o.Signal.D.Price;
            double przLow = Math.Min(o.Signal.PrzLow, o.Signal.PrzHigh);
            double przHigh = Math.Max(o.Signal.PrzLow, o.Signal.PrzHigh);
            double przMid = (przLow + przHigh) * .5;
            int dCross = 0, przEntries = 0, przDwell = 0;
            bool prevInside = false;
            double path = 0.0;
            for (int k = 0; k < rawSequence.Count; k++)
            {
                double p = rawSequence[k];
                bool inside = p >= przLow && p <= przHigh;
                if (inside) przDwell++;
                if (k > 0)
                {
                    double q = rawSequence[k - 1];
                    if ((q - d) * (p - d) < 0) dCross++;
                    if (!prevInside && inside) przEntries++;
                    path += Math.Abs(p - q);
                }
                prevInside = inside;
            }

            double first = rawSequence[0], last = rawSequence[rawSequence.Count - 1];
            double min = rawSequence.Min(), max = rawSequence.Max();
            int tailStart = Math.Max(0, rawSequence.Count - 16);
            double tailFirst = rawSequence[tailStart];
            double[] stat =
            {
                (double)dCross / Math.Max(1, rawSequence.Count - 1),
                (double)przDwell / rawSequence.Count,
                (double)przEntries / Math.Max(1, rawSequence.Count - 1),
                (last - przMid) / risk,
                (min - przMid) / risk,
                (max - przMid) / risk,
                (last - tailFirst) / risk,
                (last - first) / Math.Max(_symbol.PipSize, path),
                Math.Log(1.0 + totalTicks)
            };
            if (stat.Any(v => !double.IsFinite(v))) throw new InvalidOperationException("R17_STATIC_CONTRACT");

            string frozen = string.Format(CultureInfo.InvariantCulture,
                "[V74-R17-TICK] schema=V74_R17_TICK_V3 tick_order=FORWARD setup={0} bar={1} decision={2} minutes={3} channels={4} static={5} values={6}",
                o.SetupKey, o.BarsActive,
                decision.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture),
                V74R17Minutes, V74R17Channels,
                string.Join(",", stat.Select(v => v.ToString("G9", CultureInfo.InvariantCulture))),
                string.Join(";", rows.Select(v => string.Join(",", v.Select(x => x.ToString("G9", CultureInfo.InvariantCulture))))));

            byte[] raw = Encoding.UTF8.GetBytes(frozen);
            string encoded;
            using (var output = new MemoryStream())
            {
                using (var gzip = new GZipStream(output, CompressionLevel.Fastest, true))
                    gzip.Write(raw, 0, raw.Length);
                encoded = Convert.ToBase64String(output.ToArray());
            }
            string digest = Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant();
            string frame = "[V74-R17-FRAME] schema=V74_R17_TICK_V4 setup=" + o.SetupKey +
                " bar=" + o.BarsActive.ToString(CultureInfo.InvariantCulture) +
                " sha256=" + digest + " data=" + encoded;
            if (frame.Length > 16000) throw new InvalidOperationException("R17_TRANSPORT_LENGTH");
            V74R15ResearchPrint(frame);
        }
    }
}
