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
def kv_comment(c):
    z={}
    for piece in str(c or "").split(";"):
        if "=" in piece:
            k,v=piece.split("=",1); z[k.strip().lower()]=v.strip()
    return z
def label_basket(label):
    p=str(label or "").split("|")
    return p[1] if len(p)>=3 and p[0]=="HB70" else ""

basket_meta={}
rx=re.compile(r"\[V70-BASKET-EVENT\]\s+basket=(\S+)\s+cid=(\S+)\s+canonicalSetup=(\S*)\s+familyId=(\S+)\s+pattern=(.*?)\s+route=(\S+)\s+state=(\S+)\s+reason=(.*)$",re.M)
for m in rx.finditer(t):
    basket_meta[m.group(1)]={"cid":m.group(2),"setup":m.group(3),"family_id":m.group(4),"pattern":m.group(5).strip(),"route":m.group(6)}

cid_meta={}
rx=re.compile(r"\[V70-EVENT\]\s+cid=(\S+)\s+canonicalSetup=(\S*)\s+familyId=(\S+)\s+pattern=(.*?)\s+subtype=(.*?)\s+scale=(\d+)\s+tf=(\S+)\s+dir=(\S+)\s+state=(\S+)\s+route=(\S+)\s+legacyRoute=(\S+)\s+conflict=(\S+)\s+waitMin=([-0-9.]+)\s+reason=(.*)$",re.M)
for m in rx.finditer(t):
    cid_meta[m.group(1)]={"setup":m.group(2),"family_id":m.group(3),"pattern":m.group(4).strip(),"subtype":m.group(5).strip(),"direction":m.group(8),"route":m.group(10),"legacy_route":m.group(11)}

close_meta={}
rx=re.compile(r"\[V70-BASKET-CLOSED\].*?basket=(\S+)\s+cid=(\S+)\s+setup=(\S*)\s+pattern=(.*?)\s+subtype=(.*?)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
for m in rx.finditer(t):
    close_meta[m.group(1)]={"cid":m.group(2),"setup":m.group(3),"pattern":m.group(4).strip(),"subtype":m.group(5).strip(),"route":m.group(6),"direction":m.group(7),
      "mfe":float(m.group(8)),"mae":float(m.group(9)),"r":float(m.group(10)),"logged_net":float(m.group(11)),"reason":m.group(12)}

groups={}
for idx,x in enumerate(hist):
    label=txt(x,"label","Label"); cm=kv_comment(txt(x,"comment","Comment"))
    basket=label_basket(label) or cm.get("basket","") or "REPORTROW-"+str(idx)
    z=groups.setdefault(basket,{"basket":basket,"net":0.0,"entry_time":None,"close_time":None,"direction":"","fragments":0,"family_id":"","canonical_setup":"","route":""})
    z["net"]+=num(x,"net","netProfit","profit"); z["fragments"]+=1
    et=num(x,"entryTime","EntryTime",default=0); ct=num(x,"closeTime","CloseTime",default=0)
    z["entry_time"]=et if z["entry_time"] is None else min(z["entry_time"],et or z["entry_time"])
    z["close_time"]=ct if z["close_time"] is None else max(z["close_time"],ct or z["close_time"])
    z["direction"]=z["direction"] or txt(x,"direction","Direction").replace("TradeDirection.","")
    z["family_id"]=z["family_id"] or cm.get("fid","")
    z["canonical_setup"]=z["canonical_setup"] or cm.get("sid","")
    z["route"]=z["route"] or cm.get("route","")

rows=[]
for basket,z in groups.items():
    bm=basket_meta.get(basket,{}); cl=close_meta.get(basket,{})
    cid=cl.get("cid","") or bm.get("cid",""); cm=cid_meta.get(cid,{})
    z.update(cid=cid,
      family_id=z["family_id"] or bm.get("family_id") or cm.get("family_id") or "Unknown",
      canonical_setup=z["canonical_setup"] or bm.get("setup") or cl.get("setup") or cm.get("setup") or ("BASKET:"+basket),
      pattern=cl.get("pattern") or bm.get("pattern") or cm.get("pattern") or "UNKNOWN",
      route=z["route"] or cl.get("route") or bm.get("route") or cm.get("route") or "UNKNOWN",
      subtype=cl.get("subtype") or cm.get("subtype") or "UNKNOWN",
      mfe=cl.get("mfe"),mae=cl.get("mae"),r=cl.get("r"),reason=cl.get("reason",""))
    z["direction"]=z["direction"] or cl.get("direction","") or cm.get("direction","")
    rows.append(z)
rows.sort(key=lambda z:((z["entry_time"] or 0),z["basket"]))

v=[x["net"] for x in rows]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
summary=re.findall(r"\[V70-SUMMARY\].*?executionErrors=(\d+).*?gridRiskPlanRejects=(\d+).*?duplicateGridLegs=(\d+).*?orphanPendingOrders=(\d+).*?stopWideningViolations=(\d+).*?gapThroughSurvivors=(\d+).*?unprotectedSurvivors=(\d+).*?postFillProtectionFailures=(\d+).*?actualBasketRiskViolations=(\d+).*?executionStateViolations=(\d+).*?marginRiskViolations=(\d+)",t)
names=["execution_errors","grid_risk_plan_rejects","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean={k:0 for k in names}
if summary:
    for k,zv in zip(names,map(int,summary[-1])): clean[k]=zv
engineering_names=[k for k in names if k!="grid_risk_plan_rejects"]
engineering=bool(summary) and all(clean[k]==0 for k in engineering_names)

idrx=re.findall(r"\[V70-IDENTITY-SUMMARY\]\s+canonicalFamilyViolations=(\d+)\s+failClosed=(\S+)\s+canonicalIdentity=(\S+)\s+evidencePreserving=(\S+)\s+familyExpansion=(\S+)\s+gridChallenger=(\S+)",t)
identity={"canonical_family_violations":0,"canonical_identity":False}
if idrx:
    q=idrx[-1]; identity={"canonical_family_violations":int(q[0]),"canonical_identity":q[2].lower()=="true"}
canon_count=sum(r["family_id"] in CANON for r in rows)
canonical_coverage=canon_count/len(rows) if rows else 0.0
identity_clean=bool(idrx) and identity["canonical_family_violations"]==0 and (not identity["canonical_identity"] or canonical_coverage==1.0)

funnel={}
rx=re.compile(r"\[V70-FAMILY-FUNNEL\]\s+familyId=(\S+)\s+topology=(\d+)\s+geometryMatched=(\d+)\s+ageRejected=(\d+)\s+selected=(\d+)\s+candidates=(\d+)\s+qualityPass=(\d+)\s+qualityReject=(\d+)\s+routePass=(\d+)\s+routeReject=(\d+)\s+przTouch=(\d+)\s+confirmationPass=(\d+)\s+gridPlanned=(\d+)\s+basketPlanned=(\d+)\s+executed=(\d+)\s+closed=(\d+)\s+rejected=(\d+)\s+expired=(\d+)\s+invalidated=(\d+)\s+shadowStarted=(\d+)\s+shadowResolved=(\d+)")
fn=["topology","geometry_matched","age_rejected","selected","candidates","quality_pass","quality_reject","route_pass","route_reject","prz_touch","confirmation_pass","grid_planned","basket_planned","executed","closed","rejected","expired","invalidated","shadow_started","shadow_resolved"]
for m in rx.finditer(t): funnel[m.group(1)]={k:int(vv) for k,vv in zip(fn,m.groups()[1:])}
for fid in sorted(CANON): funnel.setdefault(fid,{k:0 for k in fn})

terminal={}
rx=re.compile(r"\[V70-FAMILY-TERMINAL\]\s+key=(.*?)\s+count=(\d+)$",re.M)
for m in rx.finditer(t): terminal[m.group(1)]=int(m.group(2))

shadow=[]
rx=re.compile(r"\[V70-SHADOW-OUTCOME\]\s+familyId=(\S+)\s+setup=(\S+)\s+cid=(\S+)\s+route=(\S+)\s+terminalReason=(\S+)\s+result=(\S+)\s+outcomeR=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+targetR=([-0-9.]+)")
for m in rx.finditer(t):
    shadow.append({"family_id":m.group(1),"setup":m.group(2),"cid":m.group(3),"route":m.group(4),"terminal_reason":m.group(5),"result":m.group(6),
      "outcome_r":float(m.group(7)),"mfe_r":float(m.group(8)),"mae_r":float(m.group(9)),"target_r":float(m.group(10))})

filter_evidence={}
rx=re.compile(r"\[V70-FILTER-EVIDENCE\]\s+filter=(\S+)\s+observed=(\d+)\s+pass=(\d+)\s+blocked=(\d+)\s+convertedToObservation=(\d+)")
for m in rx.finditer(t):
    filter_evidence[m.group(1)]={"observed":int(m.group(2)),"pass":int(m.group(3)),"blocked":int(m.group(4)),"converted_to_observation":int(m.group(5))}

adm={"protected_admissions":0,"challenger_admissions":0,"hard_veto_observations":0,"timing_deferrals":0,"arbitration_selections":0}
rx=re.compile(r"\[V70-ADMISSION-SUMMARY\]\s+protectedAdmissions=(\d+)\s+challengerAdmissions=(\d+)\s+hardVetoObservations=(\d+)\s+timingDeferrals=(\d+)\s+arbitrationSelections=(\d+)")
mm=list(rx.finditer(t))
if mm:
    m=mm[-1]
    adm={"protected_admissions":int(m.group(1)),"challenger_admissions":int(m.group(2)),"hard_veto_observations":int(m.group(3)),"timing_deferrals":int(m.group(4)),"arbitration_selections":int(m.group(5))}

report_net=sum(v); main_net=num(main,"netProfit","NetProfit",default=report_net)
out={"variant":a.family,"window":a.window,"years":a.years,"starting_balance":a.balance,
 "evidence_source":"CTRADER_REPORT_HISTORY_PLUS_V70_RESEARCH_TELEMETRY","report_history_fragments":len(hist),
 "baskets":len(rows),"unique_setups":len({x["canonical_setup"] for x in rows}),
 "net":report_net,"report_main_net":main_net,"net_reconciled":abs(report_net-main_net)<=max(.05,abs(main_net)*1e-6),
 "gross_profit":gp,"gross_loss":gl,"pf":gp/gl if gl else (999 if gp else 0),"expectancy":report_net/len(rows) if rows else 0,
 "win_rate":sum(x>0 for x in v)/len(v) if v else 0,"frequency":len(rows)/a.years if a.years else 0,
 "max_dd_pct":num(eq,"maxEquityDrawdownPercent","maxEquityDrawdownPercentages","maxDrawdownPercent"),
 "engineering_clean":engineering,"identity_clean":identity_clean,"canonical_family_coverage":canonical_coverage,
 "basket_outcomes":rows,"family_funnel":funnel,"family_terminal_reasons":terminal,"shadow_outcomes":shadow,"filter_evidence":filter_evidence,**adm,**identity,**clean}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ("basket_outcomes","shadow_outcomes","family_terminal_reasons")},indent=2))
