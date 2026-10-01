#!/usr/bin/env python3
import json,math,pathlib,re,statistics

FAMILIES=["Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero"]
ACTIONS=["REVERSAL","CONTINUATION"]
FEATURE_NAMES=["geometry","prz","confidence","time_symmetry","pivot_quality","net_rr_scaled",
               "efficiency","atr_fit","extension_scaled","trend_strength","adx_slope_norm","mtf_score"]
STATE_IDXS=[0,6,7,9,11]
Z=1.645

RX=re.compile(
 r"\[V72-HCOG-OUTCOME\]\s+id=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+lane=(\S+)\s+"
 r"abcd=(True|False)\s+coreOverlap=(True|False)\s+r=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+"
 r"maeR=([-0-9.]+)\s+bars=(\d+)\s+result=(\S+)\s+hcapSelected=(True|False)\s+"
 r"q=([-0-9.]+)\s+lcb=([-0-9.]+)\s+hold=([-0-9.]+)\s+features=(\S+)"
)

def window_of(path,windows):
    s=str(path)
    for w in windows:
        if w in s:return w
    return None

def load_rows(root,windows):
    root=pathlib.Path(root); rows=[]
    for p in root.rglob("*.log"):
        w=window_of(p,windows)
        if not w: continue
        txt=p.read_text(errors="ignore")
        for m in RX.finditer(txt):
            fam=m.group(3); lane=m.group(4); raw=m.group(15)
            if fam=="ABCD" or fam not in FAMILIES or lane not in ("HCOG_REVERSAL","HCOG_FAILURE_CONTINUATION") or raw=="NONE":
                continue
            fv=[float(x) for x in raw.split(",")]
            if len(fv)!=len(FEATURE_NAMES) or not all(math.isfinite(x) for x in fv): continue
            rows.append({"window":w,"id":m.group(1),"setup":m.group(2),"family":fam,
                         "action":"REVERSAL" if lane=="HCOG_REVERSAL" else "CONTINUATION",
                         "r":float(m.group(7)),"mfe":float(m.group(8)),"mae":float(m.group(9)),
                         "bars":int(m.group(10)),"result":m.group(11),"features":fv})
    # HCOG setup identity is the anti-duplicate truth. Last copy is equivalent if repeated artifact paths exist.
    d={}
    for r in rows:d[(r["window"],r["setup"])]=r
    return list(d.values())

def metrics(rows):
    v=[r["r"] for r in rows]; n=len(v)
    if not n:return {"n":0,"mean_r":0.0,"pf_r":0.0,"lcb_r":-999.0,"win_rate":0.0,"average_rr":0.0,"median_hold_bars":0.0}
    mean=sum(v)/n; gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
    pf=gp/gl if gl else (999.0 if gp else 0.0)
    wr=sum(x>0 for x in v)/n
    sd=statistics.stdev(v) if n>1 else 999.0
    lcb=mean-Z*sd/math.sqrt(n) if n>1 else -999.0
    wins=[x for x in v if x>0]; losses=[-x for x in v if x<0]
    aw=sum(wins)/len(wins) if wins else 0.0; al=sum(losses)/len(losses) if losses else 0.0
    rr=aw/al if al>0 else (999.0 if aw>0 else 0.0)
    return {"n":n,"mean_r":mean,"pf_r":pf,"lcb_r":lcb,"win_rate":wr,"average_rr":rr,
            "median_hold_bars":float(statistics.median([max(1,r["bars"]) for r in rows]))}

def fnv64_utf16(s):
    h=14695981039346656037
    for c in (s or ""):
        o=ord(c)
        h^=o&255; h=(h*1099511628211)&0xffffffffffffffff
        h^=(o>>8)&255; h=(h*1099511628211)&0xffffffffffffffff
    return f"{h:016X}"

def _acc(rows):
    if not rows:return {"n":0,"sum":0.0,"sumsq":0.0,"wins":0,"hold":[]}
    return {"n":len(rows),"sum":sum(r["r"] for r in rows),"sumsq":sum(r["r"]**2 for r in rows),
            "wins":sum(r["r"]>0 for r in rows),"hold":[max(1,r["bars"]) for r in rows]}

def _summary(a):
    n=a["n"]
    if not n:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0,"hold":180.0}
    mean=a["sum"]/n; var=max(0.0,(a["sumsq"]-n*mean*mean)/max(1,n-1))
    return {"n":n,"mean":mean,"win":a["wins"]/n,"sigma":math.sqrt(var),"hold":float(statistics.median(a["hold"]))}

# Model A: hierarchical competing-risk proxy. It estimates positive-outcome probability and
# Net-R on family/state cells with fixed shrinkage toward action/global parents.
def train_hier(rows):
    model={"type":"HIERARCHICAL_COMPETING_RISK","actions":{}}
    for action in ACTIONS:
        rr=[r for r in rows if r["action"]==action]
        med=[statistics.median([r["features"][j] for r in rr]) if rr else 0.0 for j in range(len(FEATURE_NAMES))]
        def state(r):
            return "".join("1" if r["features"][j]>=med[j] else "0" for j in STATE_IDXS)
        glob=_summary(_acc(rr)); fam={}; st={}; fs={}
        for f in FAMILIES:fam[f]=_summary(_acc([r for r in rr if r["family"]==f]))
        states=sorted({state(r) for r in rr})
        for z in states:st[z]=_summary(_acc([r for r in rr if state(r)==z]))
        for f in FAMILIES:
            for z in states:
                q=[r for r in rr if r["family"]==f and state(r)==z]
                if q:fs[f+"|"+z]=_summary(_acc(q))
        model["actions"][action]={"medians":med,"global":glob,"family":fam,"state":st,"family_state":fs}
    return model

def pred_hier(model,r):
    m=model["actions"][r["action"]]; med=m["medians"]
    state="".join("1" if r["features"][j]>=med[j] else "0" for j in STATE_IDXS)
    g=m["global"]; f=m["family"].get(r["family"],{"n":0,"mean":g["mean"],"win":g["win"],"sigma":g["sigma"],"hold":g["hold"]})
    st=m["state"].get(state,{"n":0,"mean":g["mean"],"win":g["win"],"sigma":g["sigma"],"hold":g["hold"]})
    cell=m["family_state"].get(r["family"]+"|"+state)
    def shrink(z,parent_mean,parent_win,k):
        n=z["n"]
        return ((z["mean"]*n+parent_mean*k)/(n+k),(z["win"]*n+parent_win*k)/(n+k),n,z["hold"])
    fm,fw,fn,fh=shrink(f,g["mean"],g["win"],30.0)
    sm,sw,sn,sh=shrink(st,g["mean"],g["win"],30.0)
    prior_m=(fm+sm)/2; prior_w=(fw+sw)/2
    if cell:
        mean,win,n,hold=shrink(cell,prior_m,prior_w,40.0); support=cell["n"]
    else:
        mean,win,n,hold=prior_m,prior_w,min(fn,sn),statistics.median([fh,sh])
        support=min(fn,sn)
    se=max(.05,g["sigma"])/math.sqrt(max(1,support))
    lcb=mean-Z*se
    selected=(support>=12 and mean>=.90 and win>=.70 and lcb>.15)
    return {"mean":mean,"win":win,"lcb":lcb,"hold":hold,"support":support,"selected":selected}

def _quantile(vals,q):
    if not vals:return 0.0
    xs=sorted(vals); i=(len(xs)-1)*q; lo=int(math.floor(i)); hi=int(math.ceil(i))
    if lo==hi:return xs[lo]
    return xs[lo]*(hi-i)+xs[hi]*(i-lo)

def _stump_train(X,y,rounds=12,lr=.08):
    n=len(y)
    if not n:return {"base":0.0,"stumps":[],"sigma":10.0}
    pred=[sum(y)/n]*n; stumps=[]
    thresholds=[[_quantile([x[j] for x in X],q) for q in (.33,.67)] for j in range(len(X[0]))]
    for _ in range(rounds):
        res=[y[i]-pred[i] for i in range(n)]
        best=None
        for j in range(len(X[0])):
            for t in thresholds[j]:
                li=[i for i,x in enumerate(X) if x[j]<=t]; ri=[i for i,x in enumerate(X) if x[j]>t]
                if len(li)<8 or len(ri)<8: continue
                lv=sum(res[i] for i in li)/len(li); rv=sum(res[i] for i in ri)/len(ri)
                sse=sum((res[i]-(lv if X[i][j]<=t else rv))**2 for i in range(n))
                cand=(sse,j,t,lv,rv,len(li),len(ri))
                if best is None or cand[0]<best[0]:best=cand
        if best is None:break
        _,j,t,lv,rv,ln,rn=best; lv*=lr; rv*=lr
        stumps.append({"j":j,"t":t,"l":lv,"r":rv,"ln":ln,"rn":rn})
        for i in range(n):pred[i]+=lv if X[i][j]<=t else rv
    residual=[y[i]-pred[i] for i in range(n)]
    sigma=statistics.stdev(residual) if len(residual)>1 else 10.0
    return {"base":sum(y)/n,"stumps":stumps,"sigma":sigma}

def _stump_pred(m,x):
    v=m["base"]; support=10**9
    for z in m["stumps"]:
        left=x[z["j"]]<=z["t"]; v+=z["l"] if left else z["r"]; support=min(support,z["ln"] if left else z["rn"])
    return v,(0 if support==10**9 else support)

# Model B: fixed shallow boosted stumps + family residual shrinkage.
def train_boost(rows):
    model={"type":"BOUNDED_GRADIENT_STUMPS","actions":{}}
    for action in ACTIONS:
        rr=[r for r in rows if r["action"]==action]; X=[r["features"] for r in rr]
        rmod=_stump_train(X,[r["r"] for r in rr])
        wmod=_stump_train(X,[1.0 if r["r"]>0 else 0.0 for r in rr])
        fam={}
        for f in FAMILIES:
            q=[r for r in rr if r["family"]==f]
            if not q:continue
            residual=[]
            for r in q:
                p,_=_stump_pred(rmod,r["features"]); residual.append(r["r"]-p)
            fam[f]={"n":len(q),"delta":sum(residual)/(len(q)+24.0),
                    "hold":float(statistics.median([max(1,r["bars"]) for r in q]))}
        model["actions"][action]={"r":rmod,"w":wmod,"family":fam,
                                  "hold":float(statistics.median([max(1,r["bars"]) for r in rr])) if rr else 180.0}
    return model

def pred_boost(model,r):
    m=model["actions"][r["action"]]; mean,s1=_stump_pred(m["r"],r["features"]); win,s2=_stump_pred(m["w"],r["features"])
    f=m["family"].get(r["family"])
    if f:mean+=f["delta"]; hold=f["hold"]; fs=f["n"]
    else:hold=m["hold"]; fs=0
    win=min(1.0,max(0.0,win)); support=max(1,min(s1 or 1,s2 or 1,fs or 10**9))
    se=max(.05,m["r"]["sigma"])/math.sqrt(support); lcb=mean-Z*se
    selected=(support>=15 and mean>=.90 and win>=.70 and lcb>.10)
    return {"mean":mean,"win":win,"lcb":lcb,"hold":hold,"support":support,"selected":selected}

# Model C: family-first conformal nearest-neighbour manifold.
def train_knn(rows):
    means=[]; scales=[]
    for j in range(len(FEATURE_NAMES)):
        col=[r["features"][j] for r in rows]; mu=sum(col)/len(col) if col else 0.0
        sd=statistics.stdev(col) if len(col)>1 else 1.0
        means.append(mu); scales.append(sd if sd>1e-9 else 1.0)
    pts=[]
    for r in rows:
        pts.append({"f":r["family"],"a":r["action"],"x":[(r["features"][j]-means[j])/scales[j] for j in range(len(FEATURE_NAMES))],
                    "r":r["r"],"bars":max(1,r["bars"])})
    return {"type":"CONFORMAL_STATE_MANIFOLD","means":means,"scales":scales,"points":pts,"k":31}

def pred_knn(model,r):
    x=[(r["features"][j]-model["means"][j])/model["scales"][j] for j in range(len(FEATURE_NAMES))]
    same=[p for p in model["points"] if p["a"]==r["action"] and p["f"]==r["family"]]
    pool=same if len(same)>=model["k"] else [p for p in model["points"] if p["a"]==r["action"]]
    ds=[]
    for p in pool:
        d=sum((x[j]-p["x"][j])**2 for j in range(len(x)))
        if p["f"]!=r["family"]:d+=.75
        ds.append((d,p))
    ds.sort(key=lambda z:z[0]); q=[p for _,p in ds[:model["k"]]]
    if len(q)<12:return {"mean":0.0,"win":0.0,"lcb":-999.0,"hold":180.0,"support":len(q),"selected":False}
    v=[p["r"] for p in q]; mean=sum(v)/len(v); wr=sum(z>0 for z in v)/len(v)
    sd=statistics.stdev(v) if len(v)>1 else 10.0; lcb=mean-Z*sd/math.sqrt(len(v))
    gp=sum(z for z in v if z>0); gl=-sum(z for z in v if z<0); pf=gp/gl if gl else 999.0
    wins=[z for z in v if z>0]; losses=[-z for z in v if z<0]
    rr=(sum(wins)/len(wins))/(sum(losses)/len(losses)) if wins and losses else 0.0
    hold=float(statistics.median([p["bars"] for p in q]))
    selected=(mean>=.90 and wr>=.70 and pf>=3.30 and rr>=2.30 and lcb>0)
    return {"mean":mean,"win":wr,"lcb":lcb,"hold":hold,"support":len(q),"selected":selected,"neighbor_pf":pf,"neighbor_rr":rr}

TRAINERS={"A_HIERARCHICAL_COMPETING_RISK":train_hier,
          "B_BOUNDED_GRADIENT_STUMPS":train_boost,
          "C_CONFORMAL_STATE_MANIFOLD":train_knn}
PREDICTORS={"A_HIERARCHICAL_COMPETING_RISK":pred_hier,
            "B_BOUNDED_GRADIENT_STUMPS":pred_boost,
            "C_CONFORMAL_STATE_MANIFOLD":pred_knn}

def predict(name,model,row):
    return PREDICTORS[name](model,row)
