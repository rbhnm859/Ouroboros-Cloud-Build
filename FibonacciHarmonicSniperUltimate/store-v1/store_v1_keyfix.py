from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: store_v1_keyfix.py <store-src-dir>')

root = Path(sys.argv[1])
safety = root / 'Store.Safety.cs'
if not safety.exists():
    raise SystemExit(f'missing {safety}')

s = safety.read_text()
old = '        private string StoreKeyPrefix => "BTC-Harmonic-Guard|" + BotLabel + "|" + SymbolName + "|";\n'
new = '''        private static string StoreSafeKeyPart(string value)\n        {\n            if (string.IsNullOrEmpty(value))\n                return "NA";\n            char[] chars = value.Where(c =>\n                (c >= 'A' && c <= 'Z') ||\n                (c >= 'a' && c <= 'z') ||\n                (c >= '0' && c <= '9')).ToArray();\n            return chars.Length == 0 ? "NA" : new string(chars);\n        }\n\n        private string StoreKeyPrefix => "BTCHarmonicGuard " +\n            StoreSafeKeyPart(BotLabel) + " " +\n            StoreSafeKeyPart(SymbolName) + " " +\n            StoreSafeKeyPart(Account.Number.ToString(CultureInfo.InvariantCulture)) + " ";\n'''
if old not in s:
    raise SystemExit('invalid-key anchor missing')
s = s.replace(old, new, 1)

old_exc = '''        protected override void OnException(Exception exception)\n        {\n            Print("[STORE EXCEPTION] {0}: {1}", exception.GetType().Name, exception.Message);\n            StorePersistAll();\n        }\n'''
new_exc = '''        protected override void OnException(Exception exception)\n        {\n            Print("[STORE EXCEPTION] {0}: {1}", exception.GetType().Name, exception.Message);\n            try\n            {\n                StorePersistAll();\n            }\n            catch (Exception persistException)\n            {\n                Print("[STORE PERSIST FAIL] {0}: {1}", persistException.GetType().Name, persistException.Message);\n            }\n        }\n'''
if old_exc not in s:
    raise SystemExit('OnException anchor missing')
s = s.replace(old_exc, new_exc, 1)

safety.write_text(s)
print('Store v1 LocalStorage key + OnException recursion fix applied')
