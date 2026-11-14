#!/usr/bin/env python3
"""Observability only. Prints sealed facts as Markdown in Taipei GMT+8.
Never computes alpha, never edits a manifest, never relaxes any gate.
Usage: r18_report.py window <WINDOW> <OUTPUT_DIR>
       r18_report.py gate <MANIFEST_JSON> <UNIVERSE_RESULT>
"""
import datetime
import glob
import json
import os
import sys

TZ = datetime.timezone(datetime.timedelta(hours=8))


def now():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


def scalars(d):
    return {k: v for k, v in d.items() if isinstance(v, (bool, int, float, str)) or v is None}


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # report, never hide
        return {"_read_error": str(e)}


def window(win, out):
    print(f"### [WINDOW-REPORT] {win} ({now()} Taipei GMT+8)")
    if not os.path.isdir(out):
        print("- output dir missing: NOT_VERIFIED (not zero)")
        return
    files = [p for p in glob.glob(out + "/**/*", recursive=True) if os.path.isfile(p)]
    print(f"- files: {len(files)}, bytes: {sum(os.path.getsize(p) for p in files)}")
    if os.path.exists(out + "/failure/exit_code.txt"):
        print("- FAILURE exit_code:", open(out + "/failure/exit_code.txt").read().strip())
    cus = out + "/R18_SEMANTIC_CUSTODY.json"
    if os.path.exists(cus):
        print("- custody:", json.dumps(scalars(load(cus)), ensure_ascii=False))
    else:
        print("- custody: NOT_FOUND (window NOT_VERIFIED)")
    for p in sorted(glob.glob(out + "/R_V73_OPPORTUNITY_UNIVERSE-*.json")):
        print("- audit:", os.path.basename(p), json.dumps(scalars(load(p)), ensure_ascii=False)[:1500])
    for p in sorted(glob.glob(out + "/raw-logs/*-R15.log")):
        n = 0
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("[V74-R18-SUMMARY]") and n < 3:
                    print("```\n" + line.strip()[:1500] + "\n```")
                    n += 1
        if n == 0:
            print("- no [V74-R18-SUMMARY] line in", os.path.basename(p), "(NOT_VERIFIED)")


def gate(path, universe_result):
    print(f"### [GATE-SUMMARY] V74 R18 semantic verdict ({now()} Taipei GMT+8)")
    print(f"- universe job result: {universe_result}")
    if universe_result != "success":
        print("- gate evaluation NOT_RUN (a window did not succeed). FAIL_CLOSED, no PASS.")
        return
    if not os.path.exists(path):
        print("- manifest NOT_FOUND. FAIL_CLOSED, no PASS.")
        return
    m = load(path)
    print("```")
    for k, v in scalars(m).items():
        print(f"{k}: {v}")
    print("```")
    print("- nested keys:", ", ".join(k for k, v in m.items() if isinstance(v, (dict, list))))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "window":
        window(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[1] == "gate":
        gate(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(2)
