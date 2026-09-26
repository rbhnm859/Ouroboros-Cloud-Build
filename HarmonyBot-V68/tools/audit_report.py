#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,math
ap=argparse.ArgumentParser()
for k in ("report","log","out","window","family"): ap.add_argument("--"+k,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args()
d=json.load(open(a.report,encoding="utf-8-sig"))
t=pathlib.Path(a.log).read_text(errors="ignore")
hist=d.get("history",{}).get("items",[]) or []
eq=d.get("equity",{}); main=d.get("main",{})

def num(x,*keys,default=0.0):
    for k in keys:
        if isinstance(x,dict) and k in x:
            try: return float(x[k] or 0)
            except Exception: pass
    return default
def txt(x,*keys,default=""):
    for k in keys:
        if isinstance(x,dict) and x.get(k) is not None:
            return str(x.get(k))
    return default
def label_basket(label):
    p=str(label or "").split("|")
    if len(p)>=3 and p[0] in ("HB52","HB67","HB68"): return p[1]
    return ""
def kv_comment(c):
    z={}
    for piece in str(c or "").split(";"):
        if "=" in piece:
            k,v=piece.split("=",1); z[k.strip().lower()]=v.strip()
    return z

# Telemetry is attribution-only. Profit/loss and basket existence come from broker report history.
event_rx=re.compile(r"\[V(?:52|67|68)-BASKET-EVENT\]\s+basket=(\S+)\s+cid=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+state=(\S+)\s+reason=(.*)$",re.M)
basket_meta={}
for m in event_rx.finditer(t):
    basket_meta[m.group(1)]={"cid":m.group(2),"pattern":m.group(3).strip(),"route":m.group(4)}

cand_rx=re.compile(r"\[V(?:52|67|68)-EVENT\]\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+scale=(\d+)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+conflict=(\S+)\s+waitMin=([-0-9.]+)\s+reason=(.*)$",re.M)
cid_meta={}
for m in cand_rx.finditer(t):
    cid_meta[m.group(1)]={"setup":m.group(2),"pattern":m.group(3).strip(),"subtype":m.group(4),"route":m.group(9),"direction":m.group(7)}

close_rx=re.compile(r"\[V(?:52|67|68)-BASKET-CLOSED\].*?basket=(\S+)\s+cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
close_meta={}
for m in close_rx.finditer(t):
    close_meta[m.group(1)]={"cid":m.group(2),"setup":m.group(3),"pattern":m.group(4).strip(),"subtype":m.group(5),
        "route":m.group(6),"direction":m.group(7),"mfe":float(m.group(8)),"mae":float(m.group(9)),"r":float(m.group(10)),
        "logged_net":float(m.group(11)),"reason":m.group(12)}

groups={}
report_schema=set()
for idx,x in enumerate(hist):
    if isinstance(x,dict): report_schema.update(x.keys())
    label=txt(x,"label","Label")
    comment=txt(x,"comment","Comment")
    cm=kv_comment(comment)
    basket=label_basket(label) or cm.get("basket","")
    if not basket:
        # Fail-safe fallback keeps broker-history rows distinct rather than inventing a basket merge.
        basket="REPORTROW-"+str(idx)
    z=groups.setdefault(basket,{"basket":basket,"net":0.0,"labels":set(),"comments":[],"entry_time":None,"close_time":None,
        "direction":"","fragments":0,"cid":"","pattern":"","route":"","setup":"","subtype":"","mfe":None,"mae":None,"r":None,"reason":""})
    z["net"]+=num(x,"net","netProfit","profit")
    z["labels"].add(label)
    if comment: z["comments"].append(comment)
    z["fragments"]+=1
    et=num(x,"entryTime","EntryTime",default=0); ct=num(x,"closeTime","CloseTime",default=0)
    z["entry_time"]=et if z["entry_time"] is None else min(z["entry_time"],et or z["entry_time"])
    z["close_time"]=ct if z["close_time"] is None else max(z["close_time"],ct or z["close_time"])
    z["direction"]=z["direction"] or txt(x,"direction","Direction").replace("TradeDirection.","")
    if cm:
        z["cid"]=z["cid"] or cm.get("cid","")
        z["pattern"]=z["pattern"] or cm.get("pattern","")
        z["route"]=z["route"] or cm.get("route","")

rows=[]
for basket,z in groups.items():
    bm=basket_meta.get(basket,{})
    cl=close_meta.get(basket,{})
    cid=z["cid"] or cl.get("cid","") or bm.get("cid","")
    cm=cid_meta.get(cid,{})
    z["cid"]=cid
    z["pattern"]=z["pattern"] or cl.get("pattern","") or bm.get("pattern","") or cm.get("pattern","") or "UNKNOWN"
    z["route"]=z["route"] or cl.get("route","") or bm.get("route","") or cm.get("route","") or "UNKNOWN"
    z["setup"]=cl.get("setup","") or cm.get("setup","") or ("BASKET:"+basket)
    z["subtype"]=cl.get("subtype","") or cm.get("subtype","") or z["pattern"]
    z["direction"]=z["direction"] or cl.get("direction","") or cm.get("direction","")
    if cl:
        z["mfe"]=cl["mfe"]; z["mae"]=cl["mae"]; z["r"]=cl["r"]; z["reason"]=cl["reason"]
    # Normalize non-JSON types.
    z["labels"]=sorted(z["labels"])
    rows.append(z)
rows.sort(key=lambda z:((z["entry_time"] or 0),z["basket"]))

v=[x["net"] for x in rows]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
summary=re.findall(r"\[V(?:52|67|68)-SUMMARY\].*?executionErrors=(\d+).*?gridRiskViolations=(\d+).*?duplicateGridLegs=(\d+).*?orphanPendingOrders=(\d+).*?stopWideningViolations=(\d+).*?gapThroughSurvivors=(\d+).*?unprotectedSurvivors=(\d+).*?postFillProtectionFailures=(\d+).*?actualBasketRiskViolations=(\d+).*?executionStateViolations=(\d+).*?marginRiskViolations=(\d+)",t)
names=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean={k:0 for k in names}
if summary:
    for k,z in zip(names,map(int,summary[-1])): clean[k]=z
engineering=bool(summary) and all(clean[k]==0 for k in names)

thr=re.findall(r"\[V(?:52|67|68)-THROUGHPUT-SUMMARY\].*?slotBlocked=(\d+).*?parked=(\d+).*?recoveredExecutions=(\d+).*?avgSlotWaitMin=([-0-9.]+).*?avgBasketOccupancyMin=([-0-9.]+).*?missedPositive=(\d+).*?avoidedNegative=(\d+)",t)
throughput={"slot_blocked":0,"parked":0,"recovered_executions":0,"avg_slot_wait_min":0.0,"avg_basket_occupancy_min":0.0,"missed_positive":0,"avoided_negative":0}
if thr:
    q=thr[-1]; throughput.update(slot_blocked=int(q[0]),parked=int(q[1]),recovered_executions=int(q[2]),avg_slot_wait_min=float(q[3]),avg_basket_occupancy_min=float(q[4]),missed_positive=int(q[5]),avoided_negative=int(q[6]))

slot_rx=re.compile(r"\[V(?:52|67|68)-SLOT-OCCUPANCY\].*?basket=(\S+).*?pattern=(.*?)\s+route=(\S+)\s+occupancyMinutes=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)")
slot_rows=[]
for m in slot_rx.finditer(t):
    slot_rows.append({"basket":m.group(1),"pattern":m.group(2).strip(),"route":m.group(3),"occupancy_minutes":float(m.group(4)),"realized_r":float(m.group(5)),"net":float(m.group(6))})

pipe_rx=re.compile(r"\[V(?:52|67|68)-PIPELINE\]\s+pattern=(.*?)\s+detected=(\d+)\s+validated=(\d+)\s+routed=(\d+)\s+prz=(\d+)\s+confirming=(\d+)\s+nativeTemporalPass=(\d+)\s+armed=(\d+)\s+slotBlocked=(\d+)\s+parked=(\d+)\s+revalidated=(\d+)\s+revalidationRejected=(\d+)\s+basketPlanned=(\d+)\s+leg0=(\d+)\s+leg1=(\d+)\s+leg2=(\d+)\s+leg3=(\d+)\s+basketClosed=(\d+)\s+executed=(\d+)\s+expired=(\d+)\s+rejected=(\d+)\s+invalidated=(\d+)")
pipeline={}
pipe_names=["detected","validated","routed","prz","confirming","native_temporal_pass","armed","slot_blocked","parked","revalidated","revalidation_rejected","basket_planned","leg0","leg1","leg2","leg3","basket_closed","executed","expired","rejected","invalidated"]
for m in pipe_rx.finditer(t):
    pipeline[m.group(1)]={k:int(v) for k,v in zip(pipe_names,m.groups()[1:])}
pipeline_closed=sum(x.get("basket_closed",0) for x in pipeline.values())
pipeline_executed=sum(x.get("executed",0) for x in pipeline.values())

mfe=[x["mfe"] for x in rows if x["mfe"] is not None]; mae=[x["mae"] for x in rows if x["mae"] is not None]; rr=[x["r"] for x in rows if x["r"] is not None]
attrib_ok=sum(x["pattern"]!="UNKNOWN" and x["route"]!="UNKNOWN" for x in rows)
tail_ok=len(rr)
report_net=sum(v); main_net=num(main,"netProfit","NetProfit",default=report_net)
net_reconciled=abs(report_net-main_net)<=max(.05,abs(main_net)*1e-6)
out={
 "variant":a.family,"window":a.window,"years":a.years,"starting_balance":a.balance,
 "evidence_source":"CTRADER_REPORT_HISTORY_GROUPED_BY_BASKET_LABEL","report_history_fragments":len(hist),
 "report_schema":sorted(report_schema),"baskets":len(rows),"unique_setups":len({x["setup"] for x in rows}),
 "net":report_net,"report_main_net":main_net,"net_reconciled":net_reconciled,
 "gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),
 "expectancy":report_net/len(rows) if rows else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0,
 "frequency":len(rows)/a.years if a.years else 0,
 "max_dd_pct":num(eq,"maxEquityDrawdownPercent","maxEquityDrawdownPercentages","maxDrawdownPercent"),
 "engineering_clean":engineering,"summary_present":bool(summary),"broker_profile_present":("[V68-BROKER-PROFILE]" in t or "[V67-BROKER-PROFILE]" in t or "[V52-BROKER-PROFILE]" in t),
 "mean_mfe_r":statistics.mean(mfe) if mfe else None,"mean_mae_r":statistics.mean(mae) if mae else None,
 "tail_telemetry_coverage":tail_ok/len(rows) if rows else 0,"attribution_coverage":attrib_ok/len(rows) if rows else 0,
 "pattern_pipeline":pipeline,"pipeline_basket_closed":pipeline_closed,"pipeline_executed":pipeline_executed,
 "basket_outcomes":rows,"slot_occupancy":slot_rows,**throughput,**clean
}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ("basket_outcomes","slot_occupancy")},indent=2))
