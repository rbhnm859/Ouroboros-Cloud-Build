using System;
using cAlgo.API;

namespace cAlgo.Robots
{
    public partial class CumulativeDeltaScalper_FX_Commercial_v3
    {
        [Parameter("Exception Entry Lockout Minutes", Group = "Protection", DefaultValue = 30, MinValue = 1, MaxValue = 1440)]
        public int ExceptionEntryLockoutMinutes { get; set; }

        [Parameter("Max Exceptions / Day", Group = "Protection", DefaultValue = 3, MinValue = 1, MaxValue = 20)]
        public int MaxExceptionsPerDay { get; set; }

        private DateTime _exceptionDay = DateTime.MinValue;
        private int _exceptionsToday;

        protected override void OnException(Exception exception)
        {
            // Keep the handler deliberately small: exceptions thrown from inside OnException are not
            // handled by OnException again. Existing broker-side SL/TP remain the primary fail-safe.
            var today = Server.Time.Date;
            if (_exceptionDay != today)
            {
                _exceptionDay = today;
                _exceptionsToday = 0;
            }

            _exceptionsToday++;
            var requestedLockout = Server.Time.AddMinutes(Math.Max(1, ExceptionEntryLockoutMinutes));
            if (_exceptionsToday >= MaxExceptionsPerDay)
                requestedLockout = today.AddDays(1);
            if (requestedLockout > _nextTradeTime)
                _nextTradeTime = requestedLockout;

            Print("[V3 EXCEPTION] count={0} type={1} message={2} entryLockoutUntil={3:o}",
                _exceptionsToday,
                exception == null ? "unknown" : exception.GetType().FullName,
                exception == null ? "unknown" : exception.Message,
                _nextTradeTime);
        }
    }
}
