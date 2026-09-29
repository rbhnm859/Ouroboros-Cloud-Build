#!/usr/bin/env python3
import json,pathlib,sys,math,collections,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
F=["g","prz","conf","ts","pv","m1","rr","reg","eff","atr","ext","mtf"]
SF=["g","prz","m1","rr","reg","eff","atr","ext"]
TH=[-.10,-.05,0,.025,.05,.075,.10,.125,.15,.20,.25,.30]
Z=1.645; MIN_N=60; MIN_PF=1.10
rows=[]
for w in W:
 xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
 if len(xs)!=1: raise SystemExit(f"missing shadow {w}: {len(xs)}")
 seen=set()
 for r in json.load(open(xs[0])).get("shadow_outcomes",[]):
  k=(r["setup"],r["family"],r["route"])
  if k in seen: continue
  seen.add(k); q=dict(r); q["window"]=w; rows.append(q)
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

def ridge(data,target="outcome_r",lam=8.,stability=True):
 mu=[mean([float(r[k]) for r in data]) for k in F]; ss=[max(1e-6,sd([float(r[k]) for r in data])) for k in F]
 ym=mean([float(r[target]) for r in data]); p=len(F); xx=[[0.]*p for _ in range(p)]; xy=[0.]*p
 for r in data:
  x=[(float(r[k])-mu[i])/ss[i] for i,k in enumerate(F)]; y=float(r[target])-ym
  for i in range(p):
   xy[i]+=x[i]*y
   for j in range(p):xx[i][j]+=x[i]*x[j]
 for i in range(p):xx[i][i]+=lam
 bz=solve(xx,xy); keep=[True]*p
 years=sorted(set(r["window"] for r in data))
 if stability and len(years)>1:
  yb=[]
  for w in years: yb.append(ridge([r for r in data if r["window"]==w],target,lam,False)[1])
  for i in range(p):
   s=1 if bz[i]>0 else -1 if bz[i]<0 else 0
   keep[i]=s!=0 and all((1 if b[i]>0 else -1 if b[i]<0 else 0)==s for b in yb) and abs(bz[i])>=.01
 beta=[bz[i]/ss[i] if keep[i] else 0. for i in range(p)]
 return ym-sum(beta[i]*mu[i] for i in range(p)),beta,keep

def priors(data):
 gm=mean([float(r["outcome_r"]) for r in data]); fg=collections.defaultdict(list); rg=collections.defaultdict(list)
 for r in data:fg[r["family"]].append(float(r["outcome_r"]));rg[(r["family"],r["route"])].append(float(r["outcome_r"]))
 fam={f:(sum(v)+30*gm)/(len(v)+30) for f,v in fg.items()}
 return {(f,rt):(sum(v)+20*fam.get(f,gm))/(len(v)+20) for (f,rt),v in rg.items()}

def support(data):
 c={k:mean([float(r[k]) for r in data]) for k in SF}; s={k:max(.05,sd([float(r[k]) for r in data])) for k in SF}
 d=[math.sqrt(sum(((float(r[k])-c[k])/s[k])**2 for k in SF)/len(SF)) for r in data]
 return c,s,max(.75,pct(d,.975))

def fit(data,arch):
 i,b,keep=ridge(data); pr=priors(data); c,s,mx=support(data)
 slot=[dict(r,slot_log=math.log(max(.5,min(12.,float(r.get("bars",60))/60.)))) for r in data]
 shi,shb,_=ridge(slot,"slot_log",12.,False)
 pred=[i+sum(b[j]*float(r[k]) for j,k in enumerate(F))+pr.get((r["family"],r["route"]),0.) for r in data]
 resid=[float(r["outcome_r"])-pred[n] for n,r in enumerate(data)]
 margin=max(.03,.10*math.sqrt(mean([x*x for x in resid])))
 return {"arch":arch,"i":i,"b":b,"keep":keep,"pri":pr,"c":c,"s":s,"support_max":mx if arch!="H1" else 999.,
         "shi":shi,"shb":shb,"margin":margin}

def score(r,m):
 edge=m["i"]+sum(m["b"][j]*float(r[k]) for j,k in enumerate(F))+m["pri"].get((r["family"],r["route"]),0.)-m["margin"]
 dist=math.sqrt(sum(((float(r[k])-m["c"][k])/m["s"][k])**2 for k in SF)/len(SF)); ok=dist<=m["support_max"]
 hours=1.5 if r["route"]=="TREND_ALIGNED_REVERSAL" else 2. if r["route"]=="EXHAUSTION_REVERSAL" else 1.25
 if m["arch"]=="H3":
  lh=m["shi"]+sum(m["shb"][j]*float(r[k]) for j,k in enumerate(F)); hours=max(.5,min(12.,math.exp(max(-2.,min(3.,lh)))))
 return edge,ok,hours,edge/max(.5,hours)

def diag(sc,t,arch):
 use=[r for r,e,ok,h,ss in sc if ok and (ss if arch=="H3" else e)>t]
 v=[float(r["outcome_r"]) for r in use]
 return {"selected_n":len(v),"selected_mean_r":mean(v),"selected_pf_r":pf(v),"selected_lcb_r":lcb(v),
         "selection_floor":t,"pass":len(v)>=MIN_N and mean(v)>0 and pf(v)>=MIN_PF and lcb(v)>0}

def choose_threshold(train,arch):
 years=sorted(set(r["window"] for r in train))
 if len(years)<2:return .015
 folds=[]
 for test in years:
  tr=[r for r in train if r["window"]!=test]; ho=[r for r in train if r["window"]==test]; m=fit(tr,arch)
  folds.append([(r,)+score(r,m) for r in ho])
 ranked=[]
 for t in TH:
  ds=[diag(x,t,arch) for x in folds]
  mn=min(d["selected_n"] for d in ds); mp=min(d["selected_pf_r"] for d in ds); wl=min(d["selected_lcb_r"] for d in ds)
  good=1 if mn>=20 and mp>1.0 else 0
  ranked.append((good,wl,mp,mn,-abs(t),t))
 return max(ranked)[-1]

def pspec(p):
 def rk(x):return "T" if x=="TREND_ALIGNED_REVERSAL" else "E" if x=="EXHAUSTION_REVERSAL" else "X"
 return ";".join(f"{f}:{rk(rt)}:{max(-2,min(2,v)):.10f}" for (f,rt),v in sorted(p.items()))
def mspec(m):
 a=[f"i:{m['i']:.10f}"]+[f"{k}:{m['b'][j]:.10f}" for j,k in enumerate(F)]+["prior:1.0000000000"]
 for k in SF:a += [f"mc_{k}:{m['c'][k]:.10f}",f"ms_{k}:{m['s'][k]:.10f}"]
 a.append(f"support_max:{m['support_max']:.10f}")
 a.append(f"slot_gate:{1.0 if m['arch']=='H3' else 0.0:.10f}")
 if m["arch"]=="H3":
  a.append(f"shi:{m['shi']:.10f}"); a += [f"sh_{k}:{m['shb'][j]:.10f}" for j,k in enumerate(F)]
 return ";".join(a)

def evaluate(arch):
 folds={}; mods={}
 for test in W:
  tr=[r for r in rows if r["window"]!=test]; ho=[r for r in rows if r["window"]==test]
  t=choose_threshold(tr,arch); m=fit(tr,arch); sc=[(r,)+score(r,m) for r in ho]; d=diag(sc,t,arch)
  d.update({"train_n":len(tr),"test_n":len(ho),"lcb_margin":m["margin"],"support_rejected":sum(1 for r,e,ok,h,ss in sc if not ok),
            "stable_features":[k for k,z in zip(F,m["keep"]) if z]})
  folds[test]=d;mods[test]=(m,t)
 return {"folds":folds,"crossfit_gate":all(x["pass"] for x in folds.values()),"folds_passed":sum(x["pass"] for x in folds.values()),
         "worst_fold_lcb_r":min(x["selected_lcb_r"] for x in folds.values()),"min_fold_pf_r":min(x["selected_pf_r"] for x in folds.values()),"models":mods}

C={a:evaluate(a) for a in ["H1","H2","H3"]}
sel=max(C,key=lambda a:(C[a]["crossfit_gate"],C[a]["folds_passed"],C[a]["worst_fold_lcb_r"],C[a]["min_fold_pf_r"]))
best=C[sel]
for test,(m,t) in best["models"].items():
 json.dump({"model_id":f"V71-{sel}-XFIT-{test}","architecture":sel,"training_windows":[w for w in W if w!=test],"test_window":test,
  "spec":mspec(m),"family_prior_spec":pspec(m["pri"]),"lcb_margin":m["margin"],"selection_lcb_r":t,"diagnostic":best["folds"][test]},
  open(out/f"{test}.json","w"),indent=2)
t=choose_threshold(rows,sel); m=fit(rows,sel)
full={"model_id":f"V71-{sel}-XFIT-FULL","architecture":sel,"training_windows":W,"spec":mspec(m),"family_prior_spec":pspec(m["pri"]),
      "lcb_margin":m["margin"],"selection_lcb_r":t,"diagnostic":{"train_n":len(rows),"stable_features":[k for k,z in zip(F,m["keep"]) if z]}}
json.dump(full,open(out/"FULL.json","w"),indent=2)
manifest={"architecture":"PREREGISTERED_H1_H2_H3_TEMPORAL_CROSSFIT","rows":len(rows),"challengers":["H1","H2","H3"],
 "selected_architecture":sel,"selection_objective":"MAXIMIZE_WORST_TEMPORAL_FOLD_CONSERVATIVE_LCB","features":F,"support_features":SF,
 "min_selected_per_fold":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,"folds":best["folds"],"crossfit_gate":best["crossfit_gate"],
 "challenger_summary":{a:{k:v for k,v in C[a].items() if k!="models"} for a in C},
 "full_model_sha256":hashlib.sha256((out/"FULL.json").read_bytes()).hexdigest()}
json.dump(manifest,open(out/"MODEL_MANIFEST.json","w"),indent=2)
print(json.dumps(manifest,indent=2))
