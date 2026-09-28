#!/usr/bin/env python3
import json,pathlib,sys,math,collections,hashlib
root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
wins=["Y2021","Y2022","Y2023"]
features=["g","prz","conf","ts","pv","m1","rr","reg","eff","atr","ext","mtf"]
rows=[]
for w in wins:
 xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
 if len(xs)!=1: raise SystemExit(f"missing shadow {w}: {len(xs)}")
 d=json.load(open(xs[0]))
 seen=set()
 for r in d.get("shadow_outcomes",[]):
  k=(w,r["setup"],r["family"],r["route"])
  if k in seen: continue
  seen.add(k); q=dict(r); q["window"]=w; rows.append(q)
if len(rows)<60: raise SystemExit(f"insufficient expansion shadow rows: {len(rows)}")

def solve(a,b):
 n=len(b); a=[list(map(float,row))+[float(b[i])] for i,row in enumerate(a)]
 for i in range(n):
  piv=max(range(i,n),key=lambda r:abs(a[r][i]))
  if abs(a[piv][i])<1e-12: a[piv][i]=1e-12
  a[i],a[piv]=a[piv],a[i]
  d=a[i][i]
  for j in range(i,n+1): a[i][j]/=d
  for r in range(n):
   if r==i: continue
   f=a[r][i]
   if abs(f)<1e-15: continue
   for j in range(i,n+1): a[r][j]-=f*a[i][j]
 return [a[i][n] for i in range(n)]

def fit(train):
 p=1+len(features); lam=2.0
 xtx=[[0.0]*p for _ in range(p)]; xty=[0.0]*p
 for r in train:
  x=[1.0]+[float(r[k]) for k in features]; y=float(r["outcome_r"])
  for i in range(p):
   xty[i]+=x[i]*y
   for j in range(p): xtx[i][j]+=x[i]*x[j]
 for i in range(1,p): xtx[i][i]+=lam
 beta=solve(xtx,xty)
 preds=[]
 for r in train:
  x=[1.0]+[float(r[k]) for k in features]
  preds.append(sum(beta[i]*x[i] for i in range(p)))
 rmse=math.sqrt(sum((float(r["outcome_r"])-preds[i])**2 for i,r in enumerate(train))/max(1,len(train)))
 gm=sum(float(r["outcome_r"]) for r in train)/len(train)
 grp=collections.defaultdict(list)
 for r in train: grp[(r["family"],r["route"])].append(float(r["outcome_r"]))
 pri={}
 alpha=20.0
 for k,v in grp.items(): pri[k]=(sum(v)+alpha*gm)/(len(v)+alpha)
 margin=max(.03,.10*rmse)
 return beta,rmse,pri,margin

def spec(beta):
 keys=["i"]+features
 return ";".join(f"{k}:{beta[i]:.10f}" for i,k in enumerate(keys))+";prior:0.2500000000"
def pspec(pri):
 def rk(route):
  return "T" if route=="TREND_ALIGNED_REVERSAL" else "E" if route=="EXHAUSTION_REVERSAL" else "X" if route=="TRANSITION_REVERSAL" else "N"
 return ";".join(f"{fam}:{rk(route)}:{max(-1,min(1,v)):.10f}" for (fam,route),v in sorted(pri.items()))
def predict(r,beta,pri,margin):
 x=[1.0]+[float(r[k]) for k in features]
 base=sum(beta[i]*x[i] for i in range(len(x)))
 return base+.25*pri.get((r["family"],r["route"]),0.0)-margin
def pf(v):
 gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
 return gp/gl if gl else (999 if gp else 0)

manifest={"architecture":"THREE_FOLD_TEMPORAL_CROSSFIT_EXPECTED_NET_R","features":features,"rows":len(rows),"folds":{}}
fold_pass=True
for test in wins:
 train=[r for r in rows if r["window"]!=test]; hold=[r for r in rows if r["window"]==test]
 beta,rmse,pri,margin=fit(train)
 pred=[(r,predict(r,beta,pri,margin)) for r in hold]
 pos=[r for r,p in pred if p>0]
 vals=[float(r["outcome_r"]) for r in pos]
 diag={"train_n":len(train),"test_n":len(hold),"selected_n":len(pos),"selected_mean_r":sum(vals)/len(vals) if vals else 0,
       "selected_pf_r":pf(vals),"rmse":rmse,"lcb_margin":margin}
 diag["pass"]=len(pos)>=10 and diag["selected_mean_r"]>0 and diag["selected_pf_r"]>=1.10
 fold_pass=fold_pass and diag["pass"]
 model={"model_id":"V71-XFIT-"+test,"training_windows":[w for w in wins if w!=test],"test_window":test,
        "spec":spec(beta),"family_prior_spec":pspec(pri),"lcb_margin":margin,"diagnostic":diag}
 (out/f"{test}.json").write_text(json.dumps(model,indent=2))
 manifest["folds"][test]=diag

beta,rmse,pri,margin=fit(rows)
full={"model_id":"V71-XFIT-FULL","training_windows":wins,"spec":spec(beta),"family_prior_spec":pspec(pri),"lcb_margin":margin,
      "diagnostic":{"train_n":len(rows),"rmse":rmse}}
(out/"FULL.json").write_text(json.dumps(full,indent=2))
manifest["crossfit_gate"]=fold_pass
manifest["full_model_sha256"]=hashlib.sha256((out/"FULL.json").read_bytes()).hexdigest()
(out/"MODEL_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
