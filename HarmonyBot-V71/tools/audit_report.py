#!/usr/bin/env python3
import argparse,json,pathlib,re,statistics,hashlib
ap=argparse.ArgumentParser()
for x in ("report","log","out","window","variant"): ap.add_argument("--"+x,required=True)
ap.add_argument("--years",type=float,required=True); ap.add_argument("--balance",type=float,required=True)
ap.add_argument("--data-snapshot",default="")
a=ap.parse_args(); d=json.load(open(a.report,encoding="utf-8-sig")); t=pathlib.Path(a.log).read_text(errors="ignore")
data_snapshot_sha256=""
if a.data_snapshot:
 p=pathlib.Path(a.data_snapshot)
 if not p.is_file(): raise SystemExit(f"missing data snapshot marker: {p}")
 data_snapshot_sha256=p.read_text().strip()
 if not re.fullmatch(r"[0-9a-fA-F]{64}",data_snapshot_sha256): raise SystemExit("invalid data snapshot sha256")
 data_snapshot_sha256=data_snapshot_sha256.lower()

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

rx=re.compile(r"\\[V51-BASKET-CLOSED\\]\\s+basket=(?P<basket>\\S+)\\s+cid=(?P<cid>\\S+)\\s+setup=(?P<setup>\\S+)\\s+pattern=(?P<pattern>.*?)\\s+subtype=(?P<subtype>\\S+)\\s+route=(?P<route>\\S+)\\s+dir=(?P<direction>\\S+).*?mfeR=(?P<mfe>[-0-9.]+)\\s+maeR=(?P<mae>[-0-9.]+)\\s+realizedR=(?P<r>[-0-9.]+)\\s+net=(?P<net>[-0-9.]+)\\s+reason=(?P<reason>\\S+)")
log_rows=[]
for q in rx.finditer(t):
 g=q.groupdict()
 log_rows.append({"basket_id":g["basket"],"cid":g["cid"],"setup":g["setup"],"pattern":g["pattern"],"subtype":g["subtype"],
                  "route":g["route"],"direction":g["direction"],"mfe":float(g["mfe"]),"mae":float(g["mae"]),
                  "r":float(g["r"]),"net":float(g["net"]),"reason":g["reason"]})
log_by_basket={x["basket_id"]:x for x in log_rows}

def comment_meta(x):
 z={}
 if not x: return z
 for part in str(x).split(";"):
  if "=" in part:
   k,v=part.split("=",1); z[k.strip()]=v.strip()
 return z

# Economic truth comes from the completed cTrader report. Console telemetry is
# intentionally forensic-only because long OnStop/shadow output can truncate
# earlier [V51-BASKET-CLOSED] lines in the cTrader log.
history=d.get("history",{}).get("items",[])
groups={}; unmapped_history=[]; comment_basket_mismatch=[]
for h in history:
 label=str(h.get("label") or "")
 lm=re.fullmatch(r"HB\\d+\\|([^|]+)\\|L(\\d+)",label)
 if not lm:
  unmapped_history.append(label); continue
 bid=lm.group(1)
 entry=int(h.get("entryTime",0) or 0)
 z=groups.setdefault(bid,{"basket_id":bid,"net":0.0,"fills":0,"first_entry":entry,
                          "cid":"","pattern":"","route":"","setup":"","direction":str(h.get("direction") or "")})
 z["net"]+=float(h.get("net",0) or 0); z["fills"]+=1
 if entry and (not z["first_entry"] or entry<z["first_entry"]): z["first_entry"]=entry
 meta=comment_meta(h.get("comment"))
 if meta.get("basket") and meta["basket"]!=bid: comment_basket_mismatch.append({"label":label,"comment_basket":meta["basket"]})
 for k in ("cid","pattern","route","setup"):
  if meta.get(k) and not z[k]: z[k]=meta[k]

rows=[]
for bid,z in sorted(groups.items(),key=lambda kv:(kv[1]["first_entry"],kv[0])):
 q=log_by_basket.get(bid,{})
 cid=z["cid"] or q.get("cid") or ("CORE-REPORT-"+bid)
 rows.append({"cid":cid,"basket_id":bid,
              "setup":z["setup"] or q.get("setup") or ("BASKET:"+bid),
              "pattern":z["pattern"] or q.get("pattern") or "UNKNOWN",
              "subtype":q.get("subtype","UNKNOWN"),
              "route":z["route"] or q.get("route") or "UNKNOWN",
              "direction":z["direction"] or q.get("direction","UNKNOWN"),
              "mfe":q.get("mfe",0.0),"mae":q.get("mae",0.0),"r":q.get("r",0.0),
              "net":z["net"],"reason":q.get("reason","RAW_REPORT_HISTORY"),
              "fills":z["fills"],"economic_source":"RAW_REPORT_HISTORY"})

def metrics(z):
 v=[x["net"] for x in z]; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
 return {"baskets":len(z),"net":sum(v),"pf":gp/gl if gl else (999 if gp else 0),
         "expectancy":sum(v)/len(v) if v else 0,"win_rate":sum(x>0 for x in v)/len(v) if v else 0}

report_history_net=sum(float(h.get("net",0) or 0) for h in history)
ts=d.get("tradeStatistics",{})
ts_net_field=ts.get("netProfit",{}) if isinstance(ts,dict) else {}
ts_total_field=ts.get("totalTrades",{}) if isinstance(ts,dict) else {}
trade_statistics_net=float(ts_net_field.get("all",report_history_net) or 0) if isinstance(ts_net_field,dict) else report_history_net
trade_statistics_total=int(ts_total_field.get("all",len(history)) or 0) if isinstance(ts_total_field,dict) else len(history)
report_economic_integrity=(not unmapped_history and not comment_basket_mismatch and
                           abs(report_history_net-trade_statistics_net)<=0.011 and
                           len(history)==trade_statistics_total)
if not report_economic_integrity:
 raise SystemExit("raw report economic integrity failure: unmapped=%d commentBasketMismatch=%d historyNet=%.9f statsNet=%.9f historyItems=%d statsTrades=%d" %
                  (len(unmapped_history),len(comment_basket_mismatch),report_history_net,trade_statistics_net,len(history),trade_statistics_total))

core=[x for x in rows if not x["cid"].startswith("V71EXP-")]
exp=[x for x in rows if x["cid"].startswith("V71EXP-")]
allm=metrics(rows); corem=metrics(core); expm=metrics(exp)
log_basket_ids={x["basket_id"] for x in log_rows}
report_basket_ids=set(groups)
log_basket_telemetry_complete=(log_basket_ids==report_basket_ids)
logm=metrics(log_rows)

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
clean=bool(m) and all(c[k]==0 for k in clean_keys) and report_economic_integrity

srx=re.compile(r"\[V71-EXP-SHADOW\]\s+cid=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+role=(\S+)\s+route=(\S+)\s+coreOverlap=(True|False)\s+capitalEligible=(True|False)\s+g=([-0-9.]+)\s+prz=([-0-9.]+)\s+conf=([-0-9.]+)\s+ts=([-0-9.]+)\s+pv=([-0-9.]+)\s+m1=([-0-9.]+)\s+rr=([-0-9.]+)\s+reg=([-0-9.]+)\s+eff=([-0-9.]+)\s+atr=([-0-9.]+)\s+ext=([-0-9.]+)\s+mtf=([-0-9.]+)\s+atp=([-0-9.]+)\s+adx1=([-0-9.]+)\s+adx4=([-0-9.]+)\s+adxs=([-0-9.]+)\s+trend=([-0-9.]+)\s+spr=([-0-9.]+)\s+ses=([-0-9.]+)\s+przc=([-0-9.]+)\s+trans=([-0-9.]+)\s+survival=([-0-9.]+)\s+structuralR=([-0-9.]+)\s+nativeR=([-0-9.]+)\s+nativeResult=(\S+)\s+pathState=(-?\d+)\s+pathUsable=(True|False)\s+mfeR=([-0-9.]+)\s+maeR=([-0-9.]+)\s+t05=(-?\d+)\s+t1=(-?\d+)\s+t2=(-?\d+)\s+tstop=(-?\d+)\s+tmfe=(-?\d+)\s+givebackR=([-0-9.]+)\s+result=(\S+)\s+bars=(\d+)(?:\s+costR=([-0-9.]+))?(?:\s+lane=(\S+))?")
shadow=[]
for q in srx.finditer(t):
 shadow.append({"cid":q.group(1),"setup":q.group(2),"family":q.group(3),"role":q.group(4),"route":q.group(5),
 "core_overlap":q.group(6)=="True","capital_eligible":q.group(7)=="True",
 "g":float(q.group(8)),"prz":float(q.group(9)),"conf":float(q.group(10)),"ts":float(q.group(11)),"pv":float(q.group(12)),
 "m1":float(q.group(13)),"rr":float(q.group(14)),"reg":float(q.group(15)),"eff":float(q.group(16)),"atr":float(q.group(17)),
 "ext":float(q.group(18)),"mtf":float(q.group(19)),"atp":float(q.group(20)),"adx1":float(q.group(21)),
 "adx4":float(q.group(22)),"adxs":float(q.group(23)),"trend":float(q.group(24)),"spr":float(q.group(25)),
 "ses":float(q.group(26)),"przc":float(q.group(27)),"trans":float(q.group(28)),"runtime_survival":float(q.group(29)),
 "outcome_r":float(q.group(30)),"structural_r":float(q.group(30)),"native_outcome_r":float(q.group(31)),"native_result":q.group(32),
 "path_state":int(q.group(33)),"path_usable":q.group(34)=="True","path_success":1 if int(q.group(33))==1 else 0 if int(q.group(33))==-1 else None,
 "mfe":float(q.group(35)),"mae":float(q.group(36)),"time_to_05":int(q.group(37)),"time_to_1":int(q.group(38)),
 "time_to_2":int(q.group(39)),"time_to_stop":int(q.group(40)),"time_to_mfe":int(q.group(41)),"giveback_r":float(q.group(42)),
 "result":q.group(43),"bars":int(q.group(44)),"cost_r":float(q.group(45)) if q.group(45) is not None else 0.0,
 "lane":q.group(46) if q.group(46) is not None else q.group(5)})

family_census={}
for fam,tracked,armed,overlap,closed in re.findall(r"\[V71\-FAMILY\-CENSUS\]\s+family=(\S+)\s+tracked=(\d+)\s+armed=(\d+)\s+coreOverlap=(\d+)\s+shadowClosed=(\d+)",t):
 family_census[fam]={"tracked":int(tracked),"armed":int(armed),"core_overlap":int(overlap),"shadow_closed":int(closed)}

oracle_census={}
for fam,expected,matched,missed,recall in re.findall(r"\[V71\-ORACLE\-CENSUS\]\s+family=(\S+)\s+expected=(\d+)\s+matched=(\d+)\s+missed=(\d+)\s+recall=([-0-9.]+)",t):
 oracle_census[fam]={"expected":int(expected),"matched":int(matched),"missed":int(missed),"recall":float(recall)}

reject_attribution={}
for fam,reason,count in re.findall(r"\[V71\-EXP\-REJECT\-SUMMARY\]\s+family=(\S+)\s+reason=(\S+)\s+count=(\d+)",t):
 reject_attribution.setdefault(fam,{})[reason]=int(count)

oracle_summary={"expected":0,"matched":0,"missed":0,"perfect_recall":False}
om=re.findall(r"\[V71\-ORACLE\-SUMMARY\]\s+expected=(\d+)\s+matched=(\d+)\s+missed=(\d+)\s+perfectRecall=(True|False)",t)
if om:
 z=om[-1]
 oracle_summary={"expected":int(z[0]),"matched":int(z[1]),"missed":int(z[2]),"perfect_recall":z[3]=="True"}

es=re.findall(r"\[V71-EXPANSION-SUMMARY\].*?detected=(\d+)\s+armed=(\d+)\s+executed=(\d+)\s+coreBlocked=(\d+)\s+eligibilityRejected=(\d+)\s+shadowClosed=(\d+)\s+riskScaled=(\d+)\s+active=(\d+)\s+selectorModel=(\S+)",t)
exp_summary={"detected":0,"armed":0,"executed":0,"core_blocked":0,"eligibility_rejected":0,"shadow_closed":0,"risk_scaled":0,"active":0,"model":"NONE"}
if es:
 z=es[-1]
 for k,v in zip(["detected","armed","executed","core_blocked","eligibility_rejected","shadow_closed","risk_scaled","active"],z[:8]): exp_summary[k]=int(v)
 exp_summary["model"]=z[8]

payoff_census=[]
for lane,family,n,sumr,sumsq,gp,gl,wins in re.findall(r"\[V72-PAYOFF-CENSUS\]\s+lane=(\S+)\s+family=(\S+)\s+n=(\d+)\s+sumR=([-0-9.]+)\s+sumSqR=([-0-9.]+)\s+gpR=([-0-9.]+)\s+glR=([-0-9.]+)\s+wins=(\d+)",t):
 payoff_census.append({"lane":lane,"family":family,"n":int(n),"sum_r":float(sumr),"sum_sq_r":float(sumsq),
                       "gross_profit_r":float(gp),"gross_loss_r":float(gl),"wins":int(wins)})

eq=d.get("equity",{})
out={"variant":a.variant,"window":a.window,"years":a.years,"starting_balance":a.balance,
 **allm,"frequency":allm["baskets"]/a.years if a.years else 0,
 "max_dd_pct":float(eq.get("maxEquityDrawdownPercent",0) or 0),
 "engineering_clean":clean,"summary_present":bool(m),"basket_outcomes":rows,
 "economic_metrics_source":"RAW_REPORT_HISTORY_GROUPED_BY_BASKET_LABEL",
 "report_economic_integrity":report_economic_integrity,
 "report_history_net":report_history_net,"trade_statistics_net":trade_statistics_net,
 "report_history_items":len(history),"trade_statistics_total_trades":trade_statistics_total,
 "report_baskets":len(rows),"log_basket_rows_seen":len(log_rows),
 "log_basket_telemetry_complete":log_basket_telemetry_complete,"log_basket_metrics":logm,
 "log_basket_outcomes":log_rows,
 "canonical_report_sha256":report_sha,"canonical_report_history_items":report_history_items,
 "core_pipeline_sha256":pipeline_sha,"core_pipeline_fingerprint_lines":pipeline_fingerprint_lines,
 "core_execution_fingerprint":core_execution_fingerprint,
 "data_snapshot_sha256":data_snapshot_sha256,
 "core_basket_outcomes":core,"expansion_basket_outcomes":exp,
 "core_metrics":corem,"expansion_metrics":expm,"shadow_outcomes":shadow,"family_census":family_census,
 "oracle_census":oracle_census,"oracle_summary":oracle_summary,"reject_attribution":reject_attribution,
 "expansion_summary":exp_summary,"payoff_census":payoff_census,**c}
pathlib.Path(a.out).write_text(json.dumps(out,indent=2))
print(json.dumps({k:out[k] for k in ["variant","window","baskets","net","pf","expectancy","win_rate","frequency","max_dd_pct","engineering_clean"]},indent=2))
