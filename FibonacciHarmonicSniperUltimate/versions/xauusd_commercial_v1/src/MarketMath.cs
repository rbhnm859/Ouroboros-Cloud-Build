using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    internal static class MarketMath
    {
        public static double Atr(Bars bars, int endIndex, int period)
        {
            if (bars == null || period < 1 || endIndex < period + 1 || endIndex >= bars.Count)
                return 0.0;

            double sum = 0.0;
            for (int i = endIndex - period + 1; i <= endIndex; i++)
            {
                double previousClose = bars.ClosePrices[i - 1];
                double tr = Math.Max(
                    bars.HighPrices[i] - bars.LowPrices[i],
                    Math.Max(
                        Math.Abs(bars.HighPrices[i] - previousClose),
                        Math.Abs(bars.LowPrices[i] - previousClose)));
                sum += tr;
            }
            return sum / period;
        }

        public static double Ema(Bars bars, int endIndex, int period)
        {
            if (bars == null || period < 2 || endIndex < 0 || endIndex >= bars.Count)
                return 0.0;

            int start = Math.Max(0, endIndex - Math.Max(period * 4, period + 10));
            double alpha = 2.0 / (period + 1.0);
            double ema = bars.ClosePrices[start];
            for (int i = start + 1; i <= endIndex; i++)
                ema = alpha * bars.ClosePrices[i] + (1.0 - alpha) * ema;
            return ema;
        }

        public static double RelativeTickVolume(Bars bars, int index, int averageBars)
        {
            if (bars == null || averageBars < 2 || index < averageBars + 1 || index >= bars.Count)
                return 0.0;

            double average = 0.0;
            for (int i = index - averageBars; i < index; i++)
                average += bars.TickVolumes[i];
            average /= averageBars;
            return average <= 0.0 ? 0.0 : bars.TickVolumes[index] / average;
        }

        public static double TrueRange(Bars bars, int index)
        {
            if (bars == null || index < 1 || index >= bars.Count)
                return 0.0;

            double previousClose = bars.ClosePrices[index - 1];
            return Math.Max(
                bars.HighPrices[index] - bars.LowPrices[index],
                Math.Max(
                    Math.Abs(bars.HighPrices[index] - previousClose),
                    Math.Abs(bars.LowPrices[index] - previousClose)));
        }

        public static int FindBarIndexAtOrBefore(Bars bars, DateTime utcTime)
        {
            if (bars == null || bars.Count == 0)
                return -1;

            for (int i = bars.Count - 1; i >= 0; i--)
                if (bars.OpenTimes[i] <= utcTime)
                    return i;
            return -1;
        }

        public static double Clamp(double value, double min, double max)
        {
            return Math.Max(min, Math.Min(max, value));
        }

        public static bool IsWithinDailyWindow(DateTime utc, int startHour, int startMinute, int endHour, int endMinute)
        {
            int now = utc.Hour * 60 + utc.Minute;
            int start = startHour * 60 + startMinute;
            int end = endHour * 60 + endMinute;

            if (start == end)
                return true;
            if (start < end)
                return now >= start && now < end;
            return now >= start || now < end;
        }
    }
}
