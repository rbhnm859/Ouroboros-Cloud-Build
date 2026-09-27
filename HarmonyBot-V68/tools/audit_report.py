#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,math
ap=argparse.ArgumentParser()
for k in ("report","log","out","window","family"): ap.add_argument("--"+k,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
hist=d.get("history",{}).get("items",[]) or []; eq=d.get("equity",{}); main=d.get("main",{})
CANON={"Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"}

def num(x,*keys,default=0.0):
    for k in keys:
        if isinstance(x,dict) and k in x:
            try:return float(x[k] or 0)
            except:pass
    return default
def txt(x,*keys,default=""):
    for k in keys:
        if isinstance(x,dict) and x.get(k) is not None:return str(x.get(k))
    return default
def label_basket(label):
    p=str(label or "").split("|")
    return p[1] if len(p)>=3 and p[0]=="HB68" else ""
def kv_comment(c):
    z={}
    for piece in str(c or "").split(";"):
        if "=" in piece:
            k,v=piece.split("=",1); z[k.strip().lower()]=v.strip()
    return z

basket_meta={}
rx=re.compile(r"\[V68-BASKET-EVENT\]\s+basket=(\S+)\s+cid=(\S+)\s+canonicalSetup=(\S*)\s+familyId=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+state=(\S+)\s+reason=(.*)$",re.M)
for m in rx.finditer(t):
    basket_meta[m.group(1)]={"cid":m.group(2),"setup":m.group(3),"family_id":m.group(4),"pattern":m.group(5).strip(),"route":m.group(6)}

cid_meta={}
rx=re.compile(r"\[V68-EVENT\]\s+cid=(\S+)\s+canonicalSetup=(\S*)\s+familyId=(\S+)\s+pattern=(.*?)\s+subtype=(.*?)\s+scale=(\d+)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+legacyRoute=(\S+)\s+conflict=(\S+)\s+waitMin=([-0-9.]+)\s+reason=(.*)$",re.M)
for m in rx.finditer(t):
    cid_meta[m.group(1)]={"setup":m.group(2),"family_id":m.group(3),"pattern":m.group(4).strip(),"subtype":m.group(5).strip(),"direction":m.group(8),"route":m.group(10),"legacy_route":m.group(11)}

close_meta={}
rx=re.compile(r"\[V68-BASKET-CLOSED\].*?basket=(\S+)\s+cid=(\S+)\s+setup=(\S*)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
for m in rx.finditer(t):
    close_meta[m.group(1)]={"cid":m.group(2),"setup":m.group(3),"pattern":m.group(4).strip(),"subtype":m.group(5).strip(),
        "route":m.group(6),"direction":m.group(7),"mfe":float(m.group(8)),"mae":float(m.group(9)),"r":float(m.group(10)),"logged_net":float(m.group(11)),"reason":m.group(12)}

groups={}; report_schema=set()
for idx,x in enumerate(hist):
    if isinstance(x,dict):report_schema.update(x.keys())
    label=txt(x,"label","Label"); cm=kv_comment(txt(x,"comment","Comment"))
    basket=label_basket(label) or cm.get("basket","") or "REPORTROW-"+str(idx)
    z=groups.setdefault(basket,{"basket":basket,"net":0.0,"labels":set(),"entry_time":None,"close_time":None,"direction":"","fragments":0})
    z["net"]+=num(x,"net","netProfit","profit"); z["labels"].add(label); z["fragments"]+=1
    et=num(x,"entryTime","EntryTime",default=0); ct=num(x,"closeTime","CloseTime",default=0)
    z["entry_time"]=et if z["entry_time"] is None else min(z["entry_time"],et or z["entry_time"])
    z["close_time"]=ct if z["close_time"] is None else max(z["close_time"],ct or z["close_time"])
    z["direction"]=z["direction"] or txt(x,"direction","Direction").replace("TradeDirection.","")
    z["cid"]=cm.get("cid",""); z["pattern"]=cm.get("pattern",""); z["route"]=cm.get("route","")

rows=[]
for basket,z in groups.items():
    bm=basket_meta.get(basket,{}); cl=close_meta.get(basket,{})
    cid=z.get("cid") or cl.get("cid","") or bm.get("cid",""); cm=cid_meta.get(cid,{})
    z.update(cid=cid,
      canonical_setup=bm.get("setup") or cl.get("setup") or cm.get("setup") or ("BASKET:"+basket),
      family_id=bm.get("family_id") or cm.get("family_id") or "Unknown",
      pattern=z.get("pattern") or cl.get("pattern") or bm.get("pattern") or cm.get("pattern") or "UNKNOWN",
      route=z.get("route") or cl.get("route") or bm.get("route") or cm.get("route") or "UNKNOWN",
      subtype=cl.get("subtype") or cm.get("subtype") or z.get("pattern") or "UNKNOWN",
      legacy_route=cm.get("legacy_route",""),
      mfe=cl.get("mfe"),mae=cl.get("mae"),r=cl.get("r"),reason=cl.get("reason",""))
    z["direction"]=z["direction"] or cl.get("direction","") or cm.get("direction","")
    z["labels"]=sorted(z["labels"]); rows.append(z)
rows.sort(key=lambda z:((z["entry_time"] or 0),z["basket"]))

v=[x["net"] for x in rows]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
summary=re.findall(r"\[V68-SUMMARY\].*?executionErrors=(\d+).*?gridRiskViolations=(\d+).*?duplicateGridLegs=(\d+).*?orphanPendingOrders=(\d+).*?stopWideningViolations=(\d+).*?gapThroughSurvivors=(\d+).*?unprotectedSurvivors=(\d+).*?postFillProtectionFailures=(\d+).*?actualBasketRiskViolations=(\d+).*?executionStateViolations=(\d+).*?marginRiskViolations=(\d+)",t)
names=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean={k:0 for k in names}
if summary:
    for k,zv in zip(names,map(int,summary[-1])):clean[k]=zv
engineering=bool(summary) and all(clean[k]==0 for k in names)

idrx=re.findall(r"\[V68-IDENTITY-SUMMARY\]\s+canonicalFamilyViolations=(\d+)\s+failClosed=(\S+)\s+canonicalIdentity=(\S+)\s+evidencePreserving=(\S+)\s+familyExpansion=(\S+)\s+gridChallenger=(\S+)",t)
identity={"canonical_family_violations":0,"fail_closed":False,"canonical_identity":False,"evidence_preserving":False,"family_expansion":False,"grid_challenger":False}
if idrx:
    q=idrx[-1]; identity={"canonical_family_violations":int(q[0]),"fail_closed":q[1].lower()=="true","canonical_identity":q[2].lower()=="true","evidence_preserving":q[3].lower()=="true","family_expansion":q[4].lower()=="true","grid_challenger":q[5].lower()=="true"}
canon_count=sum(r["family_id"] in CANON for r in rows)
canonical_coverage=canon_count/len(rows) if rows else 0.0
identity_clean=bool(idrx) and identity["canonical_family_violations"]==0 and (not identity["canonical_identity"] or canonical_coverage==1.0)

thr=re.findall(r"\[V68-THROUGHPUT-SUMMARY\].*?slotBlocked=(\d+).*?parked=(\d+).*?recoveredExecutions=(\d+).*?avgSlotWaitMin=([-0-9.]+).*?avgBasketOccupancyMin=([-0-9.]+).*?missedPositive=(\d+).*?avoidedNegative=(\d+)",t)
throughput={"slot_blocked":0,"parked":0,"recovered_executions":0,"avg_slot_wait_min":0.0,"avg_basket_occupancy_min":0.0,"missed_positive":0,"avoided_negative":0}
if thr:
    q=thr[-1]; throughput.update(slot_blocked=int(q[0]),parked=int(q[1]),recovered_executions=int(q[2]),avg_slot_wait_min=float(q[3]),avg_basket_occupancy_min=float(q[4]),missed_positive=int(q[5]),avoided_negative=int(q[6]))

slot_rows=[]
rx=re.compile(r"\[V68-SLOT-OCCUPANCY\].*?basket=(\S+).*?pattern=(.*?)\s+route=(\S+)\s+occupancyMinutes=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
for m in rx.finditer(t):slot_rows.append({"basket":m.group(1),"pattern":m.group(2).strip(),"route":m.group(3),"occupancy_minutes":float(m.group(4)),"realized_r":float(m.group(5)),"net":float(m.group(6))})

pipeline={}
rx=re.compile(r"\[V68-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pn=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
for m in rx.finditer(t):pipeline[m.group(1)]={k:int(vv) for k,vv in zip(pn,m.groups()[1:])}

mfe=[x["mfe"] for x in rows if x["mfe"] is not None]; mae=[x["mae"] for x in rows if x["mae"] is not None]; rr=[x["r"] for x in rows if x["r"] is not None]
report_net=sum(v); main_net=num(main,"netProfit","NetProfit",default=report_net)
out={"variant":a.family,"window":a.window,"years":a.years,"starting_balance":a.balance,
 "evidence_source":"CTRADER_REPORT_HISTORY_GROUPED_BY_HB68_BASKET_LABEL","report_history_fragments":len(hist),"report_schema":sorted(report_schema),
 "baskets":len(rows),"unique_setups":len({x["canonical_setup"] for x in rows}),
 "net":report_net,"report_main_net":main_net,"net_reconciled":abs(report_net-main_net)<=max(.05,abs(main_net)*1e-6),
 "gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),"expectancy":report_net/len(rows) if rows else 0,
 "win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(rows)/a.years if a.years else 0,
 "max_dd_pct":num(eq,"maxEquityDrawdownPercent","maxEquityDrawdownPercentages","maxDrawdownPercent"),
 "engineering_clean":engineering,"identity_clean":identity_clean,"canonical_family_coverage":canonical_coverage,
 "mean_mfe_r":statistics.mean(mfe) if mfe else None,"mean_mae_r":statistics.mean(mae) if mae else None,
 "tail_telemetry_coverage":len(rr)/len(rows) if rows else 0.0,"pattern_pipeline":pipeline,
 "pipeline_basket_closed":sum(x.get("basket_closed",0) for x in pipeline.values()),"pipeline_executed":sum(x.get("executed",0) for x in pipeline.values()),
 "basket_outcomes":rows,"slot_occupancy":slot_rows,**identity,**throughput,**clean}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ("basket_outcomes","slot_occupancy")},indent=2))
