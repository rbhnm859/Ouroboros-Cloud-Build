using System;
using System.Linq;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        private bool IsValidationSymbolAllowed()
        {
            var canonical = CanonicalSymbolName();
            var source = UseProductionWhitelist ? ProductionWhitelist : ValidationUniverse;
            if (string.IsNullOrWhiteSpace(source))
                return false;

            return source.Split(',')
                .Select(x => x.Trim().ToUpperInvariant())
                .Where(x => x.Length == 6)
                .Any(x => x == canonical);
        }

        private string CanonicalSymbolName()
        {
            var letters = new string(SymbolName.ToUpperInvariant().Where(char.IsLetter).ToArray());
            if (letters.Length >= 6)
                return letters.Substring(0, 6);
            return letters;
        }

        private bool IsSupportedTimeFrame()
        {
            return TimeFrame == TimeFrame.Minute ||
                   TimeFrame == TimeFrame.Minute5 ||
                   TimeFrame == TimeFrame.Minute15 ||
                   TimeFrame == TimeFrame.Minute30;
        }

        private bool IsWithinTradingSession(DateTime utc)
        {
            // Entry guards are reached before every new order. Rebuild day state once after startup/restart
            // so a restart cannot reset daily loss, trade-count or consecutive-loss protection.
            EnsureDailyStateRecovered();

            if (SessionMode == V3SessionMode.Off)
                return true;
            if (SessionMode == V3SessionMode.ManualUtc)
                return IsHourInWindow(utc.Hour, ManualStartHour, ManualEndHour);

            var pair = CanonicalSymbolName();
            if (pair.Length < 6)
                return false;
            var a = pair.Substring(0, 3);
            var b = pair.Substring(3, 3);

            var hasAsia = IsOneOf(a, "AUD", "NZD", "JPY") || IsOneOf(b, "AUD", "NZD", "JPY");
            var hasEurope = IsOneOf(a, "EUR", "GBP", "CHF") || IsOneOf(b, "EUR", "GBP", "CHF");
            var hasNorthAmerica = IsOneOf(a, "USD", "CAD") || IsOneOf(b, "USD", "CAD");

            if (hasEurope && hasNorthAmerica)
                return IsHourInWindow(utc.Hour, 6, 18);
            if (hasEurope && hasAsia)
                return IsHourInWindow(utc.Hour, 5, 12);
            if (hasNorthAmerica && hasAsia)
            {
                if (IsOneOf(a, "JPY") || IsOneOf(b, "JPY"))
                    return IsHourInWindow(utc.Hour, 0, 18);
                return IsHourInWindow(utc.Hour, 0, 10) || IsHourInWindow(utc.Hour, 12, 17);
            }
            if (hasEurope)
                return IsHourInWindow(utc.Hour, 6, 17);
            if (hasNorthAmerica)
                return IsHourInWindow(utc.Hour, 12, 21);
            if (hasAsia)
                return IsHourInWindow(utc.Hour, 22, 10);

            return false;
        }

        private bool IsRolloverBlackout(DateTime utc)
        {
            var minutes = utc.Hour * 60 + utc.Minute;
            var start = 20 * 60 + 45;
            var end = 22 * 60 + 15;
            return minutes >= start && minutes < end;
        }

        private static bool IsHourInWindow(int hour, int startHour, int endHour)
        {
            if (startHour == endHour)
                return true;
            if (startHour < endHour)
                return hour >= startHour && hour < endHour;
            return hour >= startHour || hour < endHour;
        }

        private static bool IsOneOf(string value, params string[] items)
        {
            for (var i = 0; i < items.Length; i++)
                if (value == items[i])
                    return true;
            return false;
        }
    }
}
