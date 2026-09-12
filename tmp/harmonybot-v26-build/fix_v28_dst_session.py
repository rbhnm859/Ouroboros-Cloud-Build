from pathlib import Path

p = Path('cli-build/HarmonyBotPro_v261/HarmonyBotPro.cs')
s = p.read_text(encoding='utf-8')

# Commercial session upgrade: the intended institutional window is London open
# through New York 17:00 local, not a fixed UTC interval. Implement explicit
# UK/US DST rules so cloud/mobile behavior does not depend on OS timezone IDs.

needle = '''        [Parameter("Session End (GMT)", DefaultValue = 22, MinValue = 0, MaxValue = 23)]\n        public int SessionEnd { get; set; }\n'''
insert = needle + '''\n        [Parameter("DST-Aware London-NY Session", DefaultValue = true)]\n        public bool DstAwareInstitutionalSession { get; set; }\n'''
if needle not in s:
    raise SystemExit('session parameter insertion point missing')
s = s.replace(needle, insert, 1)

old = '''        private bool IsTradingSession()\n        {\n            int h = Server.Time.Hour;\n            if (SessionStart == SessionEnd) return true;\n            if (SessionStart < SessionEnd) return h >= SessionStart && h < SessionEnd;\n            return h >= SessionStart || h < SessionEnd;\n        }\n'''
new = '''        private bool IsTradingSession()\n        {\n            DateTime utc = Server.Time;\n            if (DstAwareInstitutionalSession)\n            {\n                // London cash/FX morning: 08:00 local = 07:00 UTC in BST, 08:00 UTC in GMT.\n                // New York 17:00 local = 21:00 UTC in EDT, 22:00 UTC in EST.\n                int startMinutes = (IsUkDst(utc) ? 7 : 8) * 60;\n                int endMinutes = (IsUsDst(utc) ? 21 : 22) * 60;\n                int nowMinutes = utc.Hour * 60 + utc.Minute;\n                return nowMinutes >= startMinutes && nowMinutes < endMinutes;\n            }\n\n            int h = utc.Hour;\n            if (SessionStart == SessionEnd) return true;\n            if (SessionStart < SessionEnd) return h >= SessionStart && h < SessionEnd;\n            return h >= SessionStart || h < SessionEnd;\n        }\n\n        private static bool IsUkDst(DateTime utc)\n        {\n            int y = utc.Year;\n            DateTime start = new DateTime(y, 3, LastSundayOfMonth(y, 3), 1, 0, 0, DateTimeKind.Utc);\n            DateTime end = new DateTime(y, 10, LastSundayOfMonth(y, 10), 1, 0, 0, DateTimeKind.Utc);\n            return utc >= start && utc < end;\n        }\n\n        private static bool IsUsDst(DateTime utc)\n        {\n            int y = utc.Year;\n            int marchSecondSunday = NthSundayOfMonth(y, 3, 2);\n            int novemberFirstSunday = NthSundayOfMonth(y, 11, 1);\n            // US transition instants expressed in UTC for Eastern Time.\n            DateTime start = new DateTime(y, 3, marchSecondSunday, 7, 0, 0, DateTimeKind.Utc);\n            DateTime end = new DateTime(y, 11, novemberFirstSunday, 6, 0, 0, DateTimeKind.Utc);\n            return utc >= start && utc < end;\n        }\n\n        private static int LastSundayOfMonth(int year, int month)\n        {\n            DateTime d = new DateTime(year, month, DateTime.DaysInMonth(year, month));\n            return d.Day - (int)d.DayOfWeek;\n        }\n\n        private static int NthSundayOfMonth(int year, int month, int nth)\n        {\n            DateTime first = new DateTime(year, month, 1);\n            int offset = ((int)DayOfWeek.Sunday - (int)first.DayOfWeek + 7) % 7;\n            return 1 + offset + (nth - 1) * 7;\n        }\n'''
if old not in s:
    raise SystemExit('legacy IsTradingSession block missing')
s = s.replace(old, new, 1)

for token in ['DstAwareInstitutionalSession', 'IsUkDst', 'IsUsDst', 'LastSundayOfMonth', 'NthSundayOfMonth']:
    if token not in s:
        raise SystemExit('DST session audit missing: ' + token)

p.write_text(s, encoding='utf-8')
print('Applied v28 DST-aware London-to-New-York institutional session')
