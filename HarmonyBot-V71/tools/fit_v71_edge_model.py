#!/usr/bin/env python3
import json,pathlib,sys,math,collections,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
F=["g","prz","conf","ts","pv","m1","rr","reg","eff","atr","ext","mtf","atp","adx1","adx4","adxs","trend","spr","ses","przc","trans"]
SF=["g","prz","m1","rr","reg","eff","atr","ext","atp","trend","spr","ses","przc","trans"]
Z=1.645; MIN_N=60; MIN_PF=1.10; CONTEXT_MIN_PER_TRAIN_WINDOW=8; FIXED_SCORE_FLOOR=.015
CAPITAL_EXCLUDED_FAMILIES={"ABCD"}
rows=[]; coverage={}
for w in W:
 xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
 if len(xs)!=1: raise SystemExit(f"missing shadow {w}: {len(xs)}")
 doc=json.load(open(xs[0])); coverage[w]=doc.get("family_census",{})
 seen=set()
 for r in doc.get("shadow_outcomes",[]):
  k=(r["setup"],r["family"],r["route"])
  if k in seen: continue
  seen.add(k); q=dict(r); q["window"]=w; rows.append(q)
if len(rows)<60: raise SystemExit(f"insufficient rows {len(rows)}")
raw_rows=list(rows)
# Same-bar stop/2R ambiguity is excluded. Core-overlap and AB=CD remain research evidence
# but cannot enter Capital model training.
rows=[r for r in rows if r.get("capital_eligible",False) and r["family"] not in CAPITAL_EXCLUDED_FAMILIES and int(r.get("path_state",0))!=-2]
if len(rows)<60: raise SystemExit(f"insufficient capital-eligible structural rows {len(rows)}")

def mean(v): return sum(v)/len(v) if v else 0.
def sd(v):
 if len(v)<2:return 0.
 m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
def pct(v,q):
 z=sorted(v)
 if not z:return 0.
 p=(len(z)-1)*q; a=int(math.floor(p)); b=int(math.ceil(p))
 return z[a] if a==b else z[a]*(b-p)+z[b]*(p-a)
def pf(v):
 gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
 return gp/gl if gl else (999. if gp else 0.)
def lcb(v): return mean(v)-Z*sd(v)/math.sqrt(len(v)) if len(v)>1 else -999.
def clamp(x,a,b): return max(a,min(b,x))

def solve(a,b):
 n=len(b); a=[list(map(float,r))+[float(b[i])] for i,r in enumerate(a)]
 for i in range(n):
  p=max(range(i,n),key=lambda r:abs(a[r][i])); a[i],a[p]=a[p],a[i]
  if abs(a[i][i])<1e-10:a[i][i]=1e-10
  d=a[i][i]
  for j in range(i,n+1):a[i][j]/=d
  for r in range(n):
   if r==i:continue
   x=a[r][i]
   for j in range(i,n+1):a[r][j]-=x*a[i][j]
 return [a[i][n] for i in range(n)]

def ridge(data,target,lam=10.,stability=True):
 mu=[mean([float(r.get(k,0)) for r in data]) for k in F]
 ss=[max(1e-6,sd([float(r.get(k,0)) for r in data])) for k in F]
 ym=mean([float(r[target]) for r in data]); p=len(F); xx=[[0.]*p for _ in range(p)]; xy=[0.]*p
 for r in data:
  x=[(float(r.get(k,0))-mu[i])/ss[i] for i,k in enumerate(F)]; y=float(r[target])-ym
  for i in range(p):
   xy[i]+=x[i]*y
   for j in range(p):xx[i][j]+=x[i]*x[j]
 for i in range(p):xx[i][i]+=lam
 bz=solve(xx,xy); keep=[True]*p
 years=sorted(set(r["window"] for r in data))
 if stability and len(years)>1:
  yearly=[]
  for w in years:
   sub=[r for r in data if r["window"]==w]
   if len(sub)<max(20,p+2): continue
   yearly.append(ridge(sub,target,lam,False)[1])
  if yearly:
   for i in range(p):
    s=1 if bz[i]>0 else -1 if bz[i]<0 else 0
    keep[i]=s!=0 and all((1 if b[i]>0 else -1 if b[i]<0 else 0)==s for b in yearly) and abs(bz[i])>=.01
 beta=[bz[i]/ss[i] if keep[i] else 0. for i in range(p)]
 return ym-sum(beta[i]*mu[i] for i in range(p)),beta,keep

def context(r):
 if float(r.get("trans",0))>=.5:return "TRANSITION"
 if float(r.get("mtf",0))>=.85 and float(r.get("trend",0))>=.50:return "ALIGNED_TREND"
 if float(r.get("ext",0))>=.50 and float(r.get("mtf",0))<=.65:return "EXHAUSTION"
 if float(r.get("eff",0))<.30:return "RANGE"
 return "MIXED"

def route_key(x):return "T" if x=="TREND_ALIGNED_REVERSAL" else "E" if x=="EXHAUSTION_REVERSAL" else "X"
def ctx_key(r): return (r["family"],r["route"],context(r))

def hierarchical_pair_priors(data):
 gm=mean([float(r["outcome_r"]) for r in data]); fam=collections.defaultdict(list); pair=collections.defaultdict(list)
 for r in data:
  fam[r["family"]].append(float(r["outcome_r"])); pair[(r["family"],r["route"])].append(float(r["outcome_r"]))
 fp={k:(sum(v)+40*gm)/(len(v)+40) for k,v in fam.items()}
 return {k:(sum(v)+25*fp.get(k[0],gm))/(len(v)+25) for k,v in pair.items()}

def stable_contexts(data):
 years=sorted(set(r["window"] for r in data)); out=set()
 for k in sorted(set(ctx_key(r) for r in data)):
  ok=True
  for w in years:
   v=[float(r["outcome_r"]) for r in data if r["window"]==w and ctx_key(r)==k]
   if len(v)<CONTEXT_MIN_PER_TRAIN_WINDOW or mean(v)<=0 or pf(v)<=1.0:
    ok=False; break
  if ok: out.add(k)
 return out

def support(data):
 c={k:mean([float(r.get(k,0)) for r in data]) for k in SF}
 s={k:max(.05,sd([float(r.get(k,0)) for r in data])) for k in SF}
 d=[math.sqrt(sum(((float(r.get(k,0))-c[k])/s[k])**2 for k in SF)/len(SF)) for r in data]
 return c,s,max(.75,pct(d,.975))

def fit(data):
 i,b,keep=ridge(data,"outcome_r",10.,True)
 resolved=[r for r in data if int(r.get("path_state",0)) in (-1,1)]
 for r in resolved:r["path_success_float"]=1.0 if int(r["path_state"])==1 else 0.0
 if len(resolved)>=40:
  si,sb,skeep=ridge(resolved,"path_success_float",12.,True)
 else:
  si,sb,skeep=.5,[0.]*len(F),[False]*len(F)
 slot=[dict(r,slot_log=math.log(max(.5,min(12.,float(r.get("bars",60))/60.)))) for r in data]
 shi,shb,_=ridge(slot,"slot_log",12.,False)
 pr=hierarchical_pair_priors(data); stable=stable_contexts(data); c,s,mx=support(data)
 pred=[i+sum(b[j]*float(r.get(k,0)) for j,k in enumerate(F))+pr.get((r["family"],r["route"]),0.) for r in data]
 resid=[float(r["outcome_r"])-pred[n] for n,r in enumerate(data)]
 margin=max(.03,.10*math.sqrt(mean([x*x for x in resid])))
 return {"i":i,"b":b,"keep":keep,"si":si,"sb":sb,"skeep":skeep,"shi":shi,"shb":shb,
         "pri":pr,"stable":stable,"c":c,"s":s,"support_max":mx,"margin":margin}

def score(r,m):
 pair=(r["family"],r["route"]); ctx=ctx_key(r)
 edge=m["i"]+sum(m["b"][j]*float(r.get(k,0)) for j,k in enumerate(F))+m["pri"].get(pair,0.)-m["margin"]
 surv=clamp(m["si"]+sum(m["sb"][j]*float(r.get(k,0)) for j,k in enumerate(F)),.05,.95)
 dist=math.sqrt(sum(((float(r.get(k,0))-m["c"][k])/m["s"][k])**2 for k in SF)/len(SF))
 ok=dist<=m["support_max"] and ctx in m["stable"]
 lh=m["shi"]+sum(m["shb"][j]*float(r.get(k,0)) for j,k in enumerate(F))
 hours=max(.5,min(12.,math.exp(max(-2.,min(3.,lh)))))
 return edge,surv,ok,hours,edge*surv/hours

def diag(sc):
 use=[r for r,e,su,ok,h,ss in sc if ok and e>0 and ss>FIXED_SCORE_FLOOR]
 v=[float(r["outcome_r"]) for r in use]; resolved=[r for r in use if int(r.get("path_state",0)) in (-1,1)]
 succ=sum(int(r.get("path_state",0))==1 for r in resolved)/len(resolved) if resolved else 0
 return {"selected_n":len(v),"selected_mean_r":mean(v),"selected_pf_r":pf(v),"selected_lcb_r":lcb(v),
         "resolved_path_n":len(resolved),"two_r_before_stop_rate":succ,"selection_floor":FIXED_SCORE_FLOOR,
         "pass":len(v)>=MIN_N and mean(v)>0 and pf(v)>=MIN_PF and lcb(v)>0}

def pspec(p):
 return ";".join(f"{f}:{route_key(rt)}:{max(-2,min(2,v)):.10f}" for (f,rt),v in sorted(p.items()))
def pairspec(stable):
 return ";".join(sorted(set(f"{f}:{route_key(rt)}" for f,rt,ctx in stable)))
def ctxspec(stable):
 return ";".join(f"{f}:{route_key(rt)}:{ctx}" for f,rt,ctx in sorted(stable))
def mspec(m):
 a=[f"i:{m['i']:.10f}"]+[f"{k}:{m['b'][j]:.10f}" for j,k in enumerate(F)]+["prior:1.0000000000"]
 for k in SF:a += [f"mc_{k}:{m['c'][k]:.10f}",f"ms_{k}:{m['s'][k]:.10f}"]
 a += [f"support_max:{m['support_max']:.10f}",f"slot_gate:1.0000000000",f"shi:{m['shi']:.10f}"]
 a += [f"sh_{k}:{m['shb'][j]:.10f}" for j,k in enumerate(F)]
 a += [f"si:{m['si']:.10f}"]+[f"s_{k}:{m['sb'][j]:.10f}" for j,k in enumerate(F)]
 return ";".join(a)

folds={}; models={}
for test in W:
 tr=[r for r in rows if r["window"]!=test]; ho=[r for r in rows if r["window"]==test]
 m=fit(tr); sc=[(r,)+score(r,m) for r in ho]; d=diag(sc)
 d.update({"train_n":len(tr),"test_n":len(ho),"lcb_margin":m["margin"],
           "support_or_context_rejected":sum(1 for r,e,su,ok,h,ss in sc if not ok),
           "stable_contexts":len(m["stable"]),"stable_features":[k for k,z in zip(F,m["keep"]) if z],
           "stable_survival_features":[k for k,z in zip(F,m["skeep"]) if z]})
 folds[test]=d; models[test]=m

crossfit=all(x["pass"] for x in folds.values())
for test,m in models.items():
 json.dump({"model_id":f"V71-H4-REGIME-XFIT-{test}","architecture":"H4_REGIME_HIERARCHICAL_DUAL_HEAD",
  "training_windows":[w for w in W if w!=test],"test_window":test,"spec":mspec(m),
  "family_prior_spec":pspec(m["pri"]),"allowed_pair_spec":pairspec(m["stable"]),
  "allowed_context_spec":ctxspec(m["stable"]),"lcb_margin":m["margin"],"selection_lcb_r":FIXED_SCORE_FLOOR,
  "diagnostic":folds[test]},open(out/f"{test}.json","w"),indent=2)
fullm=fit(rows)
full={"model_id":"V71-H4-REGIME-XFIT-FULL","architecture":"H4_REGIME_HIERARCHICAL_DUAL_HEAD","training_windows":W,
      "spec":mspec(fullm),"family_prior_spec":pspec(fullm["pri"]),"allowed_pair_spec":pairspec(fullm["stable"]),
      "allowed_context_spec":ctxspec(fullm["stable"]),"lcb_margin":fullm["margin"],"selection_lcb_r":FIXED_SCORE_FLOOR,
      "diagnostic":{"train_n":len(rows),"stable_contexts":len(fullm["stable"]),"stable_features":[k for k,z in zip(F,fullm["keep"]) if z],
                    "stable_survival_features":[k for k,z in zip(F,fullm["skeep"]) if z]}}
json.dump(full,open(out/"FULL.json","w"),indent=2)

coverage_total=collections.defaultdict(lambda:{"tracked":0,"armed":0,"core_overlap":0,"shadow_closed":0})
for w,d in coverage.items():
 for fam,z in d.items():
  for k in coverage_total[fam]: coverage_total[fam][k]+=int(z.get(k,0))
manifest={"architecture":"H4_REGIME_HIERARCHICAL_DUAL_HEAD_PREREGISTERED","rows":len(rows),
 "capital_alignment":"STRUCTURAL_R_X_SURVIVAL_OVER_SLOT_HOURS_WITH_FAMILY_ROUTE_REGIME_WHITELIST",
 "selected_architecture":"H4","selection_objective":"FIXED_FLOOR__3OF3_TEMPORAL_CONSERVATIVE_LCB",
 "features":F,"support_features":SF,"min_selected_per_fold":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,
 "context_min_per_train_window":CONTEXT_MIN_PER_TRAIN_WINDOW,"fixed_score_floor":FIXED_SCORE_FLOOR,
 "capital_excluded_families":sorted(CAPITAL_EXCLUDED_FAMILIES),"raw_rows":len(raw_rows),"capital_rows":len(rows),
 "family_census":dict(sorted(coverage_total.items())),"folds":folds,"crossfit_gate":crossfit,
 "worst_fold_lcb_r":min(x["selected_lcb_r"] for x in folds.values()),"min_fold_pf_r":min(x["selected_pf_r"] for x in folds.values()),
 "full_model_sha256":hashlib.sha256((out/"FULL.json").read_bytes()).hexdigest()}
json.dump(manifest,open(out/"MODEL_MANIFEST.json","w"),indent=2)
print(json.dumps(manifest,indent=2))
