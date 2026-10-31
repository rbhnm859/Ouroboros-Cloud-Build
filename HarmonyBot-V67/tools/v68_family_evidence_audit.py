#!/usr/bin/env python3
import json,sys,collections,pathlib
CANONICAL={'Gartley','Bat','Alt Bat','Butterfly','Crab','Deep Crab','Deep Gartley','Rat','Cypher','Shark','5-0','AB=CD'}
def main():
    if len(sys.argv)!=3: raise SystemExit('usage: v68_family_evidence_audit.py attribution.json out.json')
    rows=json.load(open(sys.argv[1],encoding='utf-8'))
    malformed=sorted({str(r.get('family','')) for r in rows if str(r.get('family','')) not in CANONICAL})
    variants=collections.defaultdict(lambda:collections.defaultdict(lambda:{'count':0,'net':0.0}))
    for r in rows:
        f=str(r.get('family',''))
        if f not in CANONICAL: continue
        x=variants[str(r.get('variant','UNKNOWN'))][f]; x['count']+=int(r.get('count') or 0); x['net']+=float(r.get('net') or 0)
    out={'version':'HarmonyBot V68','stage':'PRE_ALPHA_DATA_GOVERNANCE','canonical_families':sorted(CANONICAL),'malformed_family_labels':malformed,'telemetry_identity_clean':not malformed,'variants':variants,'veto':'PASS' if not malformed else 'FAIL_CLOSED','rule':'No family-native alpha/grid promotion may use attribution containing non-canonical family labels.'}
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out,indent=2,default=dict),encoding='utf-8'); print(json.dumps(out,indent=2,default=dict))
    if malformed: raise SystemExit(23)
if __name__=='__main__': main()
