using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;

namespace cAlgo.Robots
{
    public partial class HarmonyBotV71
    {
        // V74-R16 research-only causal microstructure telemetry.
        // No entry, route, risk, exit, or capital mechanics are changed.
        private void V74R16EmitMicrostructure(V72HcogOpportunity o, int i)
        {
            if (!EnableV73OpportunityUniverse) return;
            if (o == null || o.Signal == null || o.Signal.D == null || o.V74R15AnchorIndex < 0 ||
                i < 32 || i > LastClosedIndex(_m1Bars) || i - o.V74R15AnchorIndex != o.BarsActive ||
                !(o.RiskDistance > 0) || !double.IsFinite(o.RiskDistance))
                throw new InvalidOperationException("R16_MICRO_CAUSAL_CONTRACT");

            const int length = 24;
            int start = i - length + 1;
            var cells = new List<string>();
            var times = new List<string>();
            DateTime previous = DateTime.MinValue;
            double risk = Math.Max(_symbol.PipSize, o.RiskDistance);

            for (int j = start; j <= i; j++)
            {
                DateTime closeUtc = DateTime.SpecifyKind(_m1Bars.OpenTimes[j], DateTimeKind.Utc).AddMinutes(1);
                if (closeUtc <= previous) throw new InvalidOperationException("R16_TIMESTAMP_ORDER");
                previous = closeUtc;
                times.Add(closeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture));

                double op = _m1Bars.OpenPrices[j], cl = _m1Bars.ClosePrices[j], hi = _m1Bars.HighPrices[j], lo = _m1Bars.LowPrices[j];
                double atr = Math.Max(_symbol.PipSize, Atr(_m1Bars, 14, j));
                double range = Math.Max(_symbol.PipSize, hi - lo);
                if (!double.IsFinite(atr) || hi < Math.Max(op, cl) || lo > Math.Min(op, cl))
                    throw new InvalidOperationException("R16_OHLC_ATR_CONTRACT");

                int p0 = Math.Max(1, j - 20), pn = 0;
                double tvSum = 0, tvSq = 0, rangeSum = 0, atrSum = 0;
                for (int k = p0; k < j; k++)
                {
                    double tvk = _m1Bars.TickVolumes[k];
                    double rk = Math.Max(_symbol.PipSize, _m1Bars.HighPrices[k] - _m1Bars.LowPrices[k]);
                    double ak = Math.Max(_symbol.PipSize, Atr(_m1Bars, 14, k));
                    if (!double.IsFinite(tvk) || tvk < 0 || !double.IsFinite(rk) || !double.IsFinite(ak))
                        throw new InvalidOperationException("R16_PRIOR_WINDOW_CONTRACT");
                    tvSum += tvk; tvSq += tvk * tvk; rangeSum += rk; atrSum += ak; pn++;
                }

                double tv = _m1Bars.TickVolumes[j];
                if (!double.IsFinite(tv) || tv < 0) throw new InvalidOperationException("R16_TICK_VOLUME_CONTRACT");
                double tvMean = pn > 0 ? tvSum / pn : Math.Max(1.0, tv);
                double tvVar = pn > 1 ? Math.Max(1.0, tvSq / pn - tvMean * tvMean) : 1.0;
                double rangeMean = pn > 0 ? rangeSum / pn : range;
                double atrMean = pn > 0 ? atrSum / pn : atr;

                double ret1 = (cl - _m1Bars.ClosePrices[j - 1]) / atr;
                double prevRet = (_m1Bars.ClosePrices[j - 1] - _m1Bars.ClosePrices[j - 2]) / atr;
                double ret3 = (cl - _m1Bars.ClosePrices[j - 3]) / atr;
                double ret5 = (cl - _m1Bars.ClosePrices[j - 5]) / atr;
                double path5 = 0, sq5 = 0; int n5 = 0;
                for (int k = j - 4; k <= j; k++)
                {
                    if (k < 1) continue;
                    double stepPrice = _m1Bars.ClosePrices[k] - _m1Bars.ClosePrices[k - 1];
                    path5 += Math.Abs(stepPrice);
                    double step = stepPrice / atr;
                    sq5 += step * step; n5++;
                }
                double eff5 = (cl - _m1Bars.ClosePrices[j - 5]) / Math.Max(_symbol.PipSize, path5);
                double rv5 = Math.Sqrt(Math.Max(0.0, sq5 / Math.Max(1, n5)));
                double upper = Math.Max(0.0, hi - Math.Max(op, cl)) / atr;
                double lower = Math.Max(0.0, Math.Min(op, cl) - lo) / atr;
                double closeLoc = 2.0 * (cl - lo) / range - 1.0;
                double przMid = (o.Signal.PrzLow + o.Signal.PrzHigh) * 0.5;
                double inside = (hi + _symbol.PipSize >= o.Signal.PrzLow && lo - _symbol.PipSize <= o.Signal.PrzHigh) ? 1.0 : 0.0;

                double[] x = {
                    ret1, (cl-op)/atr, range/atr, upper, lower, closeLoc,
                    (cl-o.Signal.D.Price)/atr, (cl-przMid)/atr, inside,
                    tv/Math.Max(1.0,tvMean), (tv-tvMean)/Math.Sqrt(tvVar),
                    range/Math.Max(_symbol.PipSize,rangeMean), ret3, ret5, ret1-prevRet,
                    eff5, rv5, atr/Math.Max(_symbol.PipSize,atrMean)
                };
                if (x.Any(v => !double.IsFinite(v))) throw new InvalidOperationException("R16_NONFINITE");
                cells.Add(string.Join(",", x.Select(v => v.ToString("G9", CultureInfo.InvariantCulture))));
            }

            DateTime decision = DateTime.SpecifyKind(_m1Bars.OpenTimes[i], DateTimeKind.Utc).AddMinutes(1);
            double atrNow = Math.Max(_symbol.PipSize, Atr(_m1Bars, 14, i));
            double spread = Math.Max(0.0, _symbol.Ask - _symbol.Bid);
            double phase = 2.0 * Math.PI * decision.TimeOfDay.TotalMinutes / 1440.0;
            double completionAge = Math.Max(0.0, (decision - o.Signal.CompletionTime.ToUniversalTime()).TotalMinutes);
            double przAge = o.PrzTouchUtc.HasValue ? Math.Max(0.0, (decision - o.PrzTouchUtc.Value.ToUniversalTime()).TotalMinutes) : -1.0;
            double[] stat = { spread/atrNow, spread/risk, Math.Sin(phase), Math.Cos(phase), completionAge/240.0, przAge < 0 ? -1.0 : przAge/180.0 };
            if (stat.Any(v => !double.IsFinite(v))) throw new InvalidOperationException("R16_STATIC_CONTRACT");

            string frozen = string.Format(CultureInfo.InvariantCulture,
                "[V74-R16-MICRO] schema=V74_R16_MICRO_V1 setup={0} bar={1} anchor={2} index={3} decision={4} times={5} static={6} values={7}",
                o.SetupKey, o.BarsActive, o.V74R15AnchorIndex, i,
                decision.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture),
                string.Join(",", times),
                string.Join(",", stat.Select(v => v.ToString("G9", CultureInfo.InvariantCulture))),
                string.Join(";", cells));

            byte[] raw = Encoding.UTF8.GetBytes(frozen);
            string encoded;
            using (var output = new MemoryStream())
            {
                using (var gzip = new GZipStream(output, CompressionLevel.Fastest, true)) gzip.Write(raw, 0, raw.Length);
                encoded = Convert.ToBase64String(output.ToArray());
            }
            string digest = Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant();
            string frame = "[V74-R16-FRAME] schema=V74_R16_MICRO_V2 setup=" + o.SetupKey +
                " bar=" + o.BarsActive.ToString(CultureInfo.InvariantCulture) + " sha256=" + digest + " data=" + encoded;
            if (frame.Length > 7000) throw new InvalidOperationException("R16_TRANSPORT_LENGTH");
            V74R15ResearchPrint(frame);
        }
    }
}
