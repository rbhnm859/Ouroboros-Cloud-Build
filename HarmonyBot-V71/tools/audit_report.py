#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,hashlib
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","variant"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")

# Replay identity must come from the completed cTrader execution report, not from
# best-effort basket-close telemetry. Bot-specific labels/comments are excluded;
# all economic fills, times, prices, volumes, PnL, drawdown and trade statistics remain.
def canonical_report_fingerprint(report):
 main={k:v for k,v in report.get("main",{}).items() if k not in {"cBotName","embedded","cBotLink","authorNickName","authorLink"}}
 history=[{k:v for k,v in x.items() if k not in {"label","comment"}} for x in report.get("history",{}).get("items",[])]
 payload={"main":main,"equity":report.get("equity",{}),"tradeStatistics":report.get("tradeStatistics",{}),
          "history":history,"entries":report.get("entries",{}),"profitsLosses":report.get("profitsLosses",{}),"roi":report.get("roi",{})}
 raw=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 return hashlib.sha256(raw).hexdigest(),len(history)

def core_pipeline_fingerprint(log_text):
 tags=("[V51-PIPELINE]","[V51-SUMMARY]","[V51-ALPHA-SUMMARY]","[V51-FREQUENCY-SUMMARY]",
       "[V51-INDEPENDENT-SETUP-SUMMARY]","[V51-CONVERSION-SUMMARY]","[V51-FAMILY-CONTRACT-SUMMARY]",
       "[V51-GRID-REJECT-SUMMARY]","[V51-EXECUTION-ERROR-SUMMARY]")
 lines=[]
 for line in log_text.splitlines():
  p=line.find("[V51-")
  if p < 0: continue
  z=line[p:]
  if z.startswith(tags): lines.append(z)
 raw="\n".join(lines).encode()
 return hashlib.sha256(raw).hexdigest(),len(lines)

report_sha,report_history_items=canonical_report_fingerprint(d)
pipeline_sha,pipeline_fingerprint_lines=core_pipeline_fingerprint(t)
core_pres=re.findall(r"\[V71-CORE-PRESERVATION\]\s+executed=(\d+)\s+fnv64=([0-9A-Fa-f]+)",t)
core_execution_fingerprint={"executed":int(core_pres[-1][0]),"fnv64":core_pres[-1][1].upper()} if core_pres else None

rx=re.compile(r"\[V51-BASKET-CLOSED\].*?cid=(\S+)\s+setup=(\S+)\s+pattern=(.*?)\s+subtype=(\S+)\s+route=(\S+)\s+dir=(\S+).*?mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+realizedR=([-0-9.]+)\s+net=([-0-9.]+)\s+reason=(\S+)")
rows=[]
for m in rx.finditer(t):
 rows.append({"cid":m.group(1),"setup":m.group(2),"pattern":m.group(3),"subtype":m.group(4),"route":m.group(5),"direction":m.group(6),
              "mfe":float(m.group(7)),"mae":float(m.group(8)),"r":float(m.group(9)),"net":float(m.group(10)),"reason":m.group(11)})
def metrics(z):
 v=[x["net"] for x in z]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
 return {"baskets":len(z),"net":sum(v),"pf":gp/gl if gl else (999 if gp else 0),
         "expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0}
core=[x for x in rows if not x["cid"].startswith("V71EXP-")]
exp=[x for x in rows if x["cid"].startswith("V71EXP-")]
allm=metrics(rows); corem=metrics(core); expm=metrics(exp)

pat=(r"\[V51-SUMMARY\].*?executionErrors=(\d+)\s+gridRiskViolations=(\d+)\s+duplicateGridLegs=(\d+)\s+"
 r"orphanPendingOrders=(\d+)\s+stopWideningViolations=(\d+)\s+gapThroughInvalidations=(\d+)\s+gapThroughSurvivors=(\d+)\s+"
 r"unprotectedSurvivors=(\d+)\s+postFillProtectionFailures=(\d+)\s+actualBasketRiskViolations=(\d+)\s+executionStateViolations=(\d+)\s+"
 r"virtualGridFills=(\d+)\s+microModeBaskets=(\d+)\s+capitalRejectedBaskets=(\d+)\s+marginRiskViolations=(\d+)")
m=re.findall(pat,t)
keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_invalidations",
"gap_through_survivors","unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations",
"virtual_grid_fills","micro_mode_baskets","capital_rejected_baskets","margin_risk_violations"]
c={k:0 for k in keys}
if m:
 for k,z in zip(keys,map(int,m[-1])): c[k]=z
clean_keys=["execution_errors","grid_risk_violations","duplicate_grid_legs","orphan_pending_orders","stop_widening_violations","gap_through_survivors",
"unprotected_survivors","post_fill_protection_failures","actual_basket_risk_violations","execution_state_violations","margin_risk_violations"]
clean=bool(m) and all(c[k]==0 for k in clean_keys)

srx=re.compile(r"\[V71-EXP-SHADOW\]\s+cid=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+route=(\S+)\s+g=([-0-9.]+)\s+prz=([-0-9.]+)\s+conf=([-0-9.]+)\s+ts=([-0-9.]+)\s+pv=([-0-9.]+)\s+m1=([-0-9.]+)\s+rr=([-0-9.]+)\s+reg=([-0-9.]+)\s+eff=([-0-9.]+)\s+atr=([-0-9.]+)\s+ext=([-0-9.]+)\s+mtf=([-0-9.]+)\s+atp=([-0-9.]+)\s+adx1=([-0-9.]+)\s+adx4=([-0-9.]+)\s+adxs=([-0-9.]+)\s+trend=([-0-9.]+)\s+spr=([-0-9.]+)\s+ses=([-0-9.]+)\s+przc=([-0-9.]+)\s+trans=([-0-9.]+)\s+outcomeR=([-0-9.]+)\s+result=(\S+)\s+bars=(\d+)")
shadow=[]
for q in srx.finditer(t):
 shadow.append({"cid":q.group(1),"setup":q.group(2),"family":q.group(3),"route":q.group(4),
 "g":float(q.group(5)),"prz":float(q.group(6)),"conf":float(q.group(7)),"ts":float(q.group(8)),"pv":float(q.group(9)),
 "m1":float(q.group(10)),"rr":float(q.group(11)),"reg":float(q.group(12)),"eff":float(q.group(13)),"atr":float(q.group(14)),
 "ext":float(q.group(15)),"mtf":float(q.group(16)),"atp":float(q.group(17)),"adx1":float(q.group(18)),
 "adx4":float(q.group(19)),"adxs":float(q.group(20)),"trend":float(q.group(21)),"spr":float(q.group(22)),
 "ses":float(q.group(23)),"przc":float(q.group(24)),"trans":float(q.group(25)),
 "outcome_r":float(q.group(26)),"result":q.group(27),"bars":int(q.group(28))})

es=re.findall(r"\[V71-EXPANSION-SUMMARY\].*?detected=(\d+)\s+armed=(\d+)\s+executed=(\d+)\s+coreBlocked=(\d+)\s+modelRejected=(\d+)\s+gridFallback=(\d+)\s+shadowClosed=(\d+)\s+riskScaled=(\d+)\s+active=(\d+)\s+model=(\S+)",t)
exp_summary={"detected":0,"armed":0,"executed":0,"core_blocked":0,"model_rejected":0,"grid_fallback":0,"shadow_closed":0,"risk_scaled":0,"active":0,"model":"NONE"}
if es:
 z=es[-1]
 for k,v in zip(["detected","armed","executed","core_blocked","model_rejected","grid_fallback","shadow_closed","risk_scaled","active"],z[:9]): exp_summary[k]=int(v)
 exp_summary["model"]=z[9]

eq=d.get("equity",{})
out={"variant":a.variant,"window":a.window,"years":a.years,"starting_balance":a.balance,
 **allm,"frequency":allm["baskets"]/a.years if a.years else 0,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":clean,"summary_present":bool(m),"basket_outcomes":rows,
 "canonical_report_sha256":report_sha,"canonical_report_history_items":report_history_items,
 "core_pipeline_sha256":pipeline_sha,"core_pipeline_fingerprint_lines":pipeline_fingerprint_lines,
 "core_execution_fingerprint":core_execution_fingerprint,
 "core_basket_outcomes":core,"expansion_basket_outcomes":exp,
 "core_metrics":corem,"expansion_metrics":expm,"shadow_outcomes":shadow,"expansion_summary":exp_summary,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps({k:out[k] for k in ["variant","window","baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean"]},indent=2))
