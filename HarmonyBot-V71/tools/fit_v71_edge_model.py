#!/usr/bin/env python3
import json,pathlib,sys,math,collections,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
BASE=["g","prz","conf","ts","pv","m1","rr","reg","eff","atr","ext","mtf"]
ENR=["atp","adx1","adx4","adxs","trend","spr","ses","przc","trans"]
ALL=BASE+ENR
Z=1.645; MIN_N=60; MIN_PF=1.10
SURV_TS_Q=.25; SURV_ATR_Q=.90; SURV_EXT_MIN=.999999
rows=[]
for w in W:
 xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
 if len(xs)!=1: raise SystemExit(f"missing shadow {w}: {len(xs)}")
 seen=set()
 for r in json.load(open(xs[0])).get("shadow_outcomes",[]):
  k=(r["setup"],r["family"],r["route"])
  if k in seen: continue
  seen.add(k); q=dict(r); q["window"]=w
  for k2 in ENR:
   if k2 not in q: raise SystemExit(f"missing enriched pre-entry feature {k2} in {w}")
  rows.append(q)
if len(rows)<60: raise SystemExit(f"insufficient rows {len(rows)}")

def mean(v): return sum(v)/len(v) if v else 0.
def sd(v):
 if len(v)<2:return 0.
 m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
def pct(v,q):
 z=sorted(v); p=(len(z)-1)*q; a=int(math.floor(p)); b=int(math.ceil(p))
 return z[a] if a==b else z[a]*(b-p)+z[b]*(p-a)
def pf(v):
 gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
 return gp/gl if gl else (999. if gp else 0.)
def lcb(v): return mean(v)-Z*sd(v)/math.sqrt(len(v)) if len(v)>1 else -999.

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

def ridge(data,features,target="outcome_r",lam=8.,stability=True):
 mu=[mean([float(r[k]) for r in data]) for k in features]; ss=[max(1e-6,sd([float(r[k]) for r in data])) for k in features]
 ym=mean([float(r[target]) for r in data]); p=len(features); xx=[[0.]*p for _ in range(p)]; xy=[0.]*p
 for r in data:
  x=[(float(r[k])-mu[i])/ss[i] for i,k in enumerate(features)]; y=float(r[target])-ym
  for i in range(p):
   xy[i]+=x[i]*y
   for j in range(p):xx[i][j]+=x[i]*x[j]
 for i in range(p):xx[i][i]+=lam
 bz=solve(xx,xy); keep=[True]*p
 years=sorted(set(r["window"] for r in data))
 if stability and len(years)>1:
  yb=[]
  for w in years: yb.append(ridge([r for r in data if r["window"]==w],features,target,lam,False)[1])
  for i in range(p):
   s=1 if bz[i]>0 else -1 if bz[i]<0 else 0
   keep[i]=s!=0 and all((1 if b[i]>0 else -1 if b[i]<0 else 0)==s for b in yb) and abs(bz[i])>=.01
 beta=[bz[i]/ss[i] if keep[i] else 0. for i in range(p)]
 return ym-sum(beta[i]*mu[i] for i in range(p)),beta,keep

def survival_contract(data):
 return {"ts_min":pct([float(r["ts"]) for r in data],SURV_TS_Q),
         "atr_max":pct([float(r["atr"]) for r in data],SURV_ATR_Q),
         "ext_min":SURV_EXT_MIN}
def survives(r,c):
 return float(r["ts"])>=c["ts_min"] and float(r["ext"])>=c["ext_min"] and float(r["atr"])<=c["atr_max"]

def deviation_priors(data,gm):
 fg=collections.defaultdict(list); rg=collections.defaultdict(list)
 for r in data:
  y=float(r["outcome_r"]); fg[r["family"]].append(y);rg[(r["family"],r["route"])].append(y)
 fam={f:(sum(v)+40*gm)/(len(v)+40) for f,v in fg.items()}
 return {(f,rt):(sum(v)+30*fam.get(f,gm))/(len(v)+30)-gm for (f,rt),v in rg.items()}

def fit_h1(data):
 i,b,keep=ridge(data,BASE); gm=mean([float(r["outcome_r"]) for r in data]); pri=deviation_priors(data,gm)
 pred=[i+sum(b[j]*float(r[k]) for j,k in enumerate(BASE))+pri.get((r["family"],r["route"]),0.) for r in data]
 resid=[float(r["outcome_r"])-pred[n] for n,r in enumerate(data)]
 margin=max(.03,.10*math.sqrt(mean([x*x for x in resid])))
 return {"arch":"H1","features":BASE,"i":i,"b":b,"keep":keep,"pri":pri,"margin":margin,"survival":None,"slot":None}

def fit_survival(data,arch):
 c=survival_contract(data); cohort=[r for r in data if survives(r,c)]
 if len(cohort)<MIN_N: raise SystemExit(f"insufficient survival cohort {arch}: {len(cohort)}")
 gm=mean([float(r["outcome_r"]) for r in cohort]); pri=deviation_priors(cohort,gm)
 pred=[gm+pri.get((r["family"],r["route"]),0.) for r in cohort]
 resid=[float(r["outcome_r"])-pred[n] for n,r in enumerate(cohort)]
 margin=max(.03,.10*math.sqrt(mean([x*x for x in resid])))
 slot=None
 if arch=="H3":
  z=[dict(r,slot_log=math.log(max(.5,min(12.,float(r.get("bars",60))/60.)))) for r in cohort]
  shi,shb,_=ridge(z,ALL,"slot_log",12.,False); slot=(shi,shb)
 return {"arch":arch,"features":ALL,"i":gm,"b":[0.]*len(ALL),"keep":[],"pri":pri,"margin":margin,"survival":c,"slot":slot}

def fit(data,arch): return fit_h1(data) if arch=="H1" else fit_survival(data,arch)

def score(r,m):
 ok=True if m["survival"] is None else survives(r,m["survival"])
 edge=m["i"]+sum(m["b"][j]*float(r[k]) for j,k in enumerate(m["features"]))+m["pri"].get((r["family"],r["route"]),0.)-m["margin"]
 hours=1.5 if r["route"]=="TREND_ALIGNED_REVERSAL" else 2. if r["route"]=="EXHAUSTION_REVERSAL" else 1.25
 if m["arch"]=="H3" and m["slot"] is not None:
  shi,shb=m["slot"]; lh=shi+sum(shb[j]*float(r[k]) for j,k in enumerate(ALL)); hours=max(.5,min(12.,math.exp(max(-2.,min(3.,lh)))))
 return edge,ok,hours,edge/max(.5,hours)

def diag(sc,arch):
 use=[(r,h) for r,e,ok,h,ss in sc if ok and e>0]
 v=[float(r["outcome_r"]) for r,h in use]
 slot=[float(r["outcome_r"])/max(.5,h) for r,h in use]
 return {"selected_n":len(v),"selected_mean_r":mean(v),"selected_pf_r":pf(v),"selected_lcb_r":lcb(v),
         "selected_mean_r_per_expected_slot_hour":mean(slot),"selection_floor":0.0,
         "pass":len(v)>=MIN_N and mean(v)>0 and pf(v)>=MIN_PF and lcb(v)>0}

def pspec(p):
 def rk(x):return "T" if x=="TREND_ALIGNED_REVERSAL" else "E" if x=="EXHAUSTION_REVERSAL" else "X"
 return ";".join(f"{f}:{rk(rt)}:{max(-2,min(2,v)):.10f}" for (f,rt),v in sorted(p.items()))
def mspec(m):
 coeff={k:0. for k in ALL}
 for k,v in zip(m["features"],m["b"]): coeff[k]=v
 a=[f"i:{m['i']:.10f}"]+[f"{k}:{coeff[k]:.10f}" for k in ALL]+["prior:1.0000000000"]
 if m["survival"] is not None:
  a += ["survival_gate:1.0000000000",f"survival_ts_min:{m['survival']['ts_min']:.10f}",
        f"survival_atr_max:{m['survival']['atr_max']:.10f}",f"survival_ext_min:{m['survival']['ext_min']:.10f}"]
 else:a += ["survival_gate:0.0000000000"]
 a.append(f"slot_gate:{1.0 if m['arch']=='H3' else 0.0:.10f}")
 if m["arch"]=="H3" and m["slot"] is not None:
  shi,shb=m["slot"]; a.append(f"shi:{shi:.10f}"); a += [f"sh_{k}:{shb[j]:.10f}" for j,k in enumerate(ALL)]
 return ";".join(a)

def evaluate(arch):
 folds={}; mods={}
 for test in W:
  tr=[r for r in rows if r["window"]!=test]; ho=[r for r in rows if r["window"]==test]; m=fit(tr,arch)
  sc=[(r,)+score(r,m) for r in ho]; d=diag(sc,arch)
  d.update({"train_n":len(tr),"test_n":len(ho),"lcb_margin":m["margin"],
            "survival_contract":m["survival"],"survival_rejected":sum(1 for r,e,ok,h,ss in sc if not ok),
            "stable_features":[k for k,z in zip(m["features"],m["keep"]) if z]})
  folds[test]=d;mods[test]=m
 return {"folds":folds,"crossfit_gate":all(x["pass"] for x in folds.values()),"folds_passed":sum(x["pass"] for x in folds.values()),
         "worst_fold_lcb_r":min(x["selected_lcb_r"] for x in folds.values()),"min_fold_pf_r":min(x["selected_pf_r"] for x in folds.values()),"models":mods}

C={a:evaluate(a) for a in ["H1","H2","H3"]}
sel=max(C,key=lambda a:(C[a]["crossfit_gate"],C[a]["folds_passed"],C[a]["worst_fold_lcb_r"],C[a]["min_fold_pf_r"],1 if a=="H2" else 0))
best=C[sel]
for test,m in best["models"].items():
 json.dump({"model_id":f"V71-{sel}-XFIT-{test}","architecture":sel,"training_windows":[w for w in W if w!=test],"test_window":test,
  "spec":mspec(m),"family_prior_spec":pspec(m["pri"]),"lcb_margin":m["margin"],"selection_lcb_r":0.0,"diagnostic":best["folds"][test]},
  open(out/f"{test}.json","w"),indent=2)
m=fit(rows,sel)
full={"model_id":f"V71-{sel}-XFIT-FULL","architecture":sel,"training_windows":W,"spec":mspec(m),"family_prior_spec":pspec(m["pri"]),
      "lcb_margin":m["margin"],"selection_lcb_r":0.0,"diagnostic":{"train_n":len(rows),"survival_contract":m["survival"],"stable_features":[k for k,z in zip(m["features"],m["keep"]) if z]}}
json.dump(full,open(out/"FULL.json","w"),indent=2)
manifest={"architecture":"PREREGISTERED_H1_H2_H3_TEMPORAL_CROSSFIT_V2","rows":len(rows),"challengers":["H1","H2","H3"],
 "regime_survival_contract":"TRAIN_ONLY_Q25_TIME_SYMMETRY_AND_EXTENSION_SATURATION_AND_TRAIN_ONLY_Q90_ATR_FIT_CEILING",
 "regime_survival_quantiles":{"time_symmetry_floor_q":SURV_TS_Q,"atr_fit_ceiling_q":SURV_ATR_Q,"extension_floor":SURV_EXT_MIN},
 "family_route_policy":"HIERARCHICAL_SHRINKAGE_SOFT_PRIOR_ONLY","capital_alignment":"SURVIVAL_PASS_AND_EDGE_LCB_GT_0;_SLOT_HOUR_RANKING_FOR_H3",
 "selected_architecture":sel,"selection_objective":"MAXIMIZE_WORST_TEMPORAL_FOLD_CONSERVATIVE_LCB","base_features":BASE,"enriched_preentry_features":ENR,
 "min_selected_per_fold":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,"folds":best["folds"],"crossfit_gate":best["crossfit_gate"],
 "challenger_summary":{a:{k:v for k,v in C[a].items() if k!="models"} for a in C},
 "full_model_sha256":hashlib.sha256((out/"FULL.json").read_bytes()).hexdigest()}
json.dump(manifest,open(out/"MODEL_MANIFEST.json","w"),indent=2)
print(json.dumps(manifest,indent=2))
