#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('work')
cmd = [sys.executable, '.github/scripts/commercial_rc7_verify.py', str(root)]
r = subprocess.run(cmd, check=False)
rc7 = root / 'Commercial-RC7-Gate.json'
rc6_compat = root / 'Commercial-RC6-Gate.json'
if rc7.exists():
    shutil.copyfile(rc7, rc6_compat)
else:
    print('RC7 compatibility verifier: Commercial-RC7-Gate.json missing')
    raise SystemExit(2)
print('RC7 compatibility verifier: mirrored RC7 gate to legacy RC6 gate filename for existing workflow')
raise SystemExit(r.returncode)
