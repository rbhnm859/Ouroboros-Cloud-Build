#!/usr/bin/env python3
import re,sys

cases = [
    (
        re.compile(r"\[V70-FILTER-EVIDENCE\]\s+filter=(\S+)\s+observed=(\d+)\s+pass=(\d+)\s+blocked=(\d+)\s+convertedToObservation=(\d+)"),
        "[V70-FILTER-EVIDENCE] filter=M1_CONFIRMATION observed=10 pass=6 blocked=4 convertedToObservation=4",
        ("M1_CONFIRMATION","10","6","4","4")
    ),
    (
        re.compile(r"\[V70-ADMISSION-SUMMARY\]\s+protectedAdmissions=(\d+)\s+challengerAdmissions=(\d+)\s+hardVetoObservations=(\d+)\s+timingDeferrals=(\d+)\s+arbitrationSelections=(\d+)"),
        "[V70-ADMISSION-SUMMARY] protectedAdmissions=7 challengerAdmissions=9 hardVetoObservations=11 timingDeferrals=13 arbitrationSelections=15",
        ("7","9","11","13","15")
    )
]
for rx,line,expected in cases:
    m=rx.search(line)
    if not m or m.groups()!=expected:
        print("PARSER_SELF_TEST_FAIL",rx.pattern,line,m.groups() if m else None,expected)
        sys.exit(2)
print("PARSER_SELF_TEST_PASS")
