#!/usr/bin/env python3
"""V74 robust nested-crossfit causal auction.

Mission: solve causal action selection/admission only.
Validation/Fresh are never loaded. Burned OOF test years never participate in
route choice, feature selection, hyper-parameter choice, threshold choice, or
model fitting.
"""
import json,math,pathlib,statistics,sys,time
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,FAMILIES

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"]
ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
FRACTIONS=("00","10","20","30");MSTAGES=("05","10","15")
BASES=[f"R{r}_{m}_RR{rr}" for r in ("025","050") for m in ("H","D") for rr in ("35","40")]
MASKS={
 "ALL":lambda b:True,
 "H_ONLY":lambda b:"_H_" in b,
 "RR40_ONLY":lambda b:b.endswith("RR40"),
 "H_RR40":lambda b:"_H_" in b and b.endswith("RR40"),
}
CONFIGS=[]
for mask in MASKS:
  for bins in (3,4):
    for shrink in (16.0,32.0):
      for kfeat in (14,22):
        CONFIGS.append({"mask":mask,"bins":bins,"shrink":shrink,"kfeat":kfeat,
                        "effect_w":0.85,"win_w":1.10,"lcb_w":0.55})
QGRID=[i/100.0 for i in (0,5,10,15,20,25,30,35,40,45,50)]

rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")
if sum(len(r.get("late_auction_entry_bars",{})) for r in rows)==0:raise SystemExit("V74 v2 late-auction telemetry missing")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def margin(m):
    if m["n"]<=0:return -999.0
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,
               m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25)
def qtile(v,q):
    if not v:return math.inf
    x=sorted(float(z) for z in v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def med(v,d=0.0):
    return statistics.median(v) if v else d
def key(m,b,f):return f"M{m}_{b}_F{f}"
def lev(b):return "025" if b.startswith("R025_") else "050"

def out_r(r,m,b,f):
    k20=key(m,b,"20");k30=key(m,b,"30")
    a=r.get("late_auction",{}).get(k20);c=r.get("late_auction",{}).get(k30)
    rr=r.get("late_auction_rr",{}).get(k20)
    if a is None or c is None or rr is None:return None
    a=float(a);c=float(c);rr=float(rr)
    if not all(math.isfinite(x) for x in (a,c,rr)) or rr+1e-9<MIN_RR:return None
    if f=="20":return a
    if f=="30":return c
    d=c-a
    return a-(2.0 if f=="00" else 1.0)*d

def entry_state(r,m,b):
    v=r.get("late_auction_entry_state",{}).get(key(m,b,"20"))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None
def maturity_state(r,m,b):
    v=r.get("late_auction_maturity_state",{}).get(key(m,b,"20"))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None
def ebar(r,m,b):
    try:return int(r.get("late_auction_entry_bars",{}).get(key(m,b,"20"),-1))
    except:return -1
def route_bars(r,m,b):
    try:return max(1,int(r.get("late_auction_bars",{}).get(key(m,b,"20"),r.get("bars",1)) or 1))
    except:return max(1,int(r.get("bars",1) or 1))

def cats(r,b):
    return [1.0 if r["family"]==f else 0.0 for f in FAMILIES]+[
      1.0 if r["action"]=="CONTINUATION" else 0.0,
      1.0 if b.startswith("R050_") else 0.0,
      1.0 if "_D_" in b else 0.0,
      1.0 if b.endswith("RR40") else 0.0]

def xvec(r,b,m):
    a=maturity_state(r,m,b);e=entry_state(r,m,b)
    if a is None or e is None:return None
    # V2 contract: maturity + completed entry state only. Trigger/post-trigger/
    # lock fields are deliberately excluded from admission features.
    return list(r.get("features",[]))+cats(r,b)+a+e+[e[i]-a[i] for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]

def telemetry_guard():
    n=0
    for r in rows:
      for b in BASES:
        for m in MSTAGES:
          k20=key(m,b,"20");k30=key(m,b,"30")
          for fld in ("late_auction_entry_bars","late_auction_maturity_state","late_auction_entry_state"):
            a=r.get(fld,{}).get(k20);c=r.get(fld,{}).get(k30)
            if a is not None and c is not None and a!=c:
              raise SystemExit(f"V74 F20/F30 pre-entry mismatch {fld} {r['setup']} {m} {b}")
        n+=1
    return n

def route_options(r,b):
    z=[]
    for m in MSTAGES:
      if ebar(r,m,b)<0:continue
      for f in FRACTIONS:
        y=out_r(r,m,b,f)
        if y is None:continue
        z.append((key(m,b,f),m,f,float(y)))
    return z

def robust_route_score(vals,years,shrink=18.0):
    if not vals:return -999.0
    all_y=[v for _,v in vals];pm=statistics.mean(all_y);pw=sum(v>0 for v in all_y)/len(all_y)
    ym=[];yw=[]
    for w in years:
      a=[v for ww,v in vals if ww==w]
      gm=[v for ww,v in vals if ww==w]
      if not a:continue
      mm=statistics.mean(a);wwin=sum(v>0 for v in a)/len(a)
      # shrink sparse year cells to pooled cell, not to a future/test distribution
      ym.append((mm*len(a)+pm*shrink)/(len(a)+shrink))
      yw.append((wwin*len(a)+pw*shrink)/(len(a)+shrink))
    if not ym:return -999.0
    return .55*min(ym)+.25*med(ym)+.20*pm + 1.15*min(yw)+.35*med(yw)

def fit_route_policy(xs,mask):
    years=sorted({r["window"] for r in xs});mf=MASKS[mask]
    tables={lvl:defaultdict(lambda:defaultdict(list)) for lvl in ("exact","fam_base","base")}
    for r in xs:
      for b in BASES:
        if not mf(b):continue
        for rk,m,f,y in route_options(r,b):
          tables["exact"][(r["family"],r["action"],b)][rk].append((r["window"],y))
          tables["fam_base"][(r["family"],b)][rk].append((r["window"],y))
          tables["base"][b][rk].append((r["window"],y))
    outp={}
    for lvl,t in tables.items():
      outp[lvl]={}
      for cell,rr in t.items():
        scored=[(robust_route_score(v,years),rk,len(v)) for rk,v in rr.items()]
        scored=[z for z in scored if z[0]>-900]
        if scored:
          scored.sort(reverse=True)
          outp[lvl][str(cell)]=scored[0][1]
    return {"mask":mask,"choices":outp}

def pick_route(r,b,pol):
    if not MASKS[pol["mask"]](b):return None
    opts={rk:(m,f,y) for rk,m,f,y in route_options(r,b)}
    keys=[
      ("exact",str((r["family"],r["action"],b))),
      ("fam_base",str((r["family"],b))),
      ("base",str(b)),
    ]
    for lvl,cell in keys:
      rk=pol["choices"].get(lvl,{}).get(cell)
      if rk in opts:
        m,f,y=opts[rk];return rk,m,f,y
    return None

def make_samples(xs,pol):
    out=[]
    for r in xs:
      for b in BASES:
        pr=pick_route(r,b,pol)
        if not pr:continue
        rk,m,f,y=pr;x=xvec(r,b,m)
        if x is None:continue
        out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                    "base":b,"route":rk,"m":m,"f":f,"x":x,"y":float(y),"route_bars":route_bars(r,m,b),"row":r})
    return out

def stable_idx(samples,k):
    if not samples:return []
    p=len(samples[0]["x"]);yrs=sorted({s["window"] for s in samples})
    ranked=[]
    for j in range(p):
      vv=[s["x"][j] for s in samples];cut=med(vv)
      eff=[]
      for w in yrs:
        q=[s for s in samples if s["window"]==w]
        lo=[s["y"] for s in q if s["x"][j]<cut];hi=[s["y"] for s in q if s["x"][j]>=cut]
        if len(lo)<18 or len(hi)<18:continue
        eff.append(statistics.mean(hi)-statistics.mean(lo))
      if len(eff)<max(3,len(yrs)//2):continue
      signs=[1 if z>=0 else -1 for z in eff]
      cons=abs(sum(signs))/len(signs)
      sc=(.55*abs(med(eff))+.45*min(abs(z) for z in eff))*cons
      if sc>0:ranked.append((sc,j))
    ranked.sort(reverse=True)
    return [j for _,j in ranked[:k]] or list(range(min(k,p)))

def bin_of(x,edges):
    b=0
    while b<len(edges) and x>edges[b]:b+=1
    return b

def robust_stat(samples,global_by_year,global_mean,global_win,shrink):
    if not samples:return {"n":0,"mean":global_mean,"win":global_win,"sigma":10.0}
    ys=[s["y"] for s in samples];pm=statistics.mean(ys);pw=sum(y>0 for y in ys)/len(ys)
    yrs=sorted(global_by_year)
    ym=[];yw=[]
    for w in yrs:
      a=[s["y"] for s in samples if s["window"]==w]
      gm,gw=global_by_year[w]
      if not a:
        ym.append(gm);yw.append(gw);continue
      m=statistics.mean(a);q=sum(y>0 for y in a)/len(a)
      ym.append((m*len(a)+gm*shrink)/(len(a)+shrink))
      yw.append((q*len(a)+gw*shrink)/(len(a)+shrink))
    rm=.45*pm+.55*min(ym);rw=.45*pw+.55*min(yw)
    sg=statistics.stdev(ys) if len(ys)>1 else 10.0
    return {"n":len(ys),"mean":rm,"win":rw,"sigma":max(.05,sg)}

def fit_admission(samples,cfg):
    idx=stable_idx(samples,cfg["kfeat"]);yrs=sorted({s["window"] for s in samples})
    gy={}
    for w in yrs:
      a=[s["y"] for s in samples if s["window"]==w]
      gy[w]=(statistics.mean(a),sum(v>0 for v in a)/len(a))
    all_y=[s["y"] for s in samples];gm=statistics.mean(all_y);gw=sum(v>0 for v in all_y)/len(all_y)
    global_stat=robust_stat(samples,gy,gm,gw,cfg["shrink"])
    edges={}
    for j in idx:
      vv=sorted(s["x"][j] for s in samples)
      edges[str(j)]=[qtile(vv,q/cfg["bins"]) for q in range(1,cfg["bins"])]
    prior_levels={}
    keyf={
      "exact":lambda s:(s["family"],s["action"],s["base"]),
      "fam_base":lambda s:(s["family"],s["base"]),
      "family":lambda s:s["family"],
      "base":lambda s:s["base"],
    }
    for name,fn in keyf.items():
      d=defaultdict(list)
      for s in samples:d[str(fn(s))].append(s)
      prior_levels[name]={k:robust_stat(v,gy,gm,gw,cfg["shrink"]) for k,v in d.items() if len(v)>=10}
    generic=defaultdict(list);fam_bin=defaultdict(list)
    for s in samples:
      for j in idx:
        b=bin_of(s["x"][j],edges[str(j)])
        generic[(j,b)].append(s);fam_bin[(s["family"],j,b)].append(s)
    ge={};fe={}
    for k,v in generic.items():
      if len(v)>=24:
        z=robust_stat(v,gy,gm,gw,cfg["shrink"])
        ge[str(k)]={"n":z["n"],"dm":z["mean"]-global_stat["mean"],"dw":z["win"]-global_stat["win"]}
    for k,v in fam_bin.items():
      if len(v)>=18:
        z=robust_stat(v,gy,gm,gw,cfg["shrink"])
        # family baseline makes this conditional effect more stable
        fs=prior_levels["family"].get(str(k[0]),global_stat)
        fe[str(k)]={"n":z["n"],"dm":z["mean"]-fs["mean"],"dw":z["win"]-fs["win"]}
    return {"cfg":cfg,"idx":idx,"edges":edges,"global":global_stat,
            "priors":prior_levels,"generic":ge,"family_bin":fe}

def predict(model,s):
    g=model["global"];p=None
    for lvl,k in (
      ("exact",str((s["family"],s["action"],s["base"]))),
      ("fam_base",str((s["family"],s["base"]))),
      ("family",str(s["family"])),
      ("base",str(s["base"])),
    ):
      z=model["priors"][lvl].get(k)
      if z is not None and z["n"]>=12:p=z;break
    if p is None:p=g
    dm=[];dw=[];supports=[p["n"]]
    for j in model["idx"]:
      b=bin_of(s["x"][j],model["edges"][str(j)])
      z=model["family_bin"].get(str((s["family"],j,b)))
      if z is None:z=model["generic"].get(str((j,b)))
      if z is not None:
        dm.append(z["dm"]);dw.append(z["dw"]);supports.append(z["n"])
    # Median aggregation prevents one unstable feature cell dominating admission.
    mu=p["mean"]+model["cfg"]["effect_w"]*med(dm)
    wi=max(0.0,min(1.0,p["win"]+model["cfg"]["effect_w"]*med(dw)))
    sup=max(1,min(supports));sig=max(.05,p.get("sigma",g["sigma"]))
    lc=mu-Z*sig/math.sqrt(sup)
    score=mu+model["cfg"]["win_w"]*wi+model["cfg"]["lcb_w"]*lc
    return {"score":score,"mean":mu,"win":wi,"lcb":lc,"support":sup}

def scored_events(samples,model):
    book=defaultdict(list)
    for s in samples:
      z=predict(model,s)
      if not math.isfinite(z["score"]):continue
      book[(s["window"],s["setup"])].append((z,s))
    out=[]
    for _,a in book.items():
      a.sort(key=lambda q:(q[0]["score"],q[0]["lcb"],q[0]["win"],q[1]["route"]),reverse=True)
      z,s=a[0];out.append({"score":z["score"],"pred":z,"s":s})
    return out

def metric_selected(events,th):
    rr=[]
    for e in events:
      if e["score"]+1e-12<th:continue
      s=e["s"];q=dict(s["row"]);q["r"]=s["y"];q["bars"]=s["route_bars"];q["sequential_key"]=s["route"];rr.append(q)
    return metrics(rr),rr

def choose_config(train_rows,train_years):
    cache={}
    # inner year predictions and training-score distributions; never use outer test
    for mask in MASKS:
      cache[mask]={}
      for val in train_years:
        tr=[r for r in train_rows if r["window"]!=val];va=[r for r in train_rows if r["window"]==val]
        rp=fit_route_policy(tr,mask);ts=make_samples(tr,rp);vs=make_samples(va,rp)
        cache[mask][val]=(ts,vs)
    best=None
    for ci,cfg in enumerate(CONFIGS):
      inner={}
      for val in train_years:
        ts,vs=cache[cfg["mask"]][val]
        if len(ts)<300 or len(vs)<100:inner={};break
        md=fit_admission(ts,cfg)
        tr_events=scored_events(ts,md);va_events=scored_events(vs,md)
        inner[val]=(tr_events,va_events)
      if not inner:continue
      for q in QGRID:
        ym=[];ok=True
        for val in train_years:
          tr_events,va_events=inner[val]
          th=qtile([e["score"] for e in tr_events],q)
          m,_=metric_selected(va_events,th)
          if m["n"]<MIN_N:ok=False
          ym.append((val,m))
        if not ok:continue
        ms=[m for _,m in ym];marg=[margin(m) for m in ms]
        obj=min(marg)+.18*med(marg)+.08*min(m["lcb_r"] for m in ms)+.05*min(m["mean_r"] for m in ms)
        tie=(obj,min(marg),med(marg),-q,-ci)
        if best is None or tie>best[0]:
          best=(tie,{"cfg":cfg,"q":q,"objective":obj,"inner_metrics":dict(ym)})
    if best is None:
      raise SystemExit("V74 nested crossfit found no configuration preserving N>=250 in every training year")
    return best[1]

def fit_final(train_rows,choice):
    rp=fit_route_policy(train_rows,choice["cfg"]["mask"])
    ss=make_samples(train_rows,rp);md=fit_admission(ss,choice["cfg"])
    ev=scored_events(ss,md);th=qtile([e["score"] for e in ev],choice["q"])
    return rp,md,th

checks=telemetry_guard()
summary={
 "version":"HarmonyBot V74 Robust Nested Crossfit Causal Auction",
 "architecture":"ROBUST_NESTED_CROSSFIT_ROUTE_AWARE_ADMISSION",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"route_choice":"TRAINING_ONLY_ROBUST_FAMILY_ACTION_BASE_ROUTE_CONTRACT",
           "admission":"ENTRY_BAR_ONLY_HIERARCHICAL_HISTOGRAM_ENSEMBLE",
           "hyperparameters":"NESTED_LEAVE_ONE_YEAR_OUT_TRAINING_ONLY",
           "no_future_state":True,"canonical_family_blanket_blacklist":False,"grid":False},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks
}
models={"architecture":summary["architecture"],"folds":{}}
t0=time.perf_counter();allpass=True
for test in BURNED:
    ft=time.perf_counter()
    tw=RESEARCH+[w for w in BURNED if w!=test]
    tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
    choice=choose_config(tr,tw)
    rp,md,th=fit_final(tr,choice)
    tes=make_samples(te,rp);events=scored_events(tes,md);m,mr=metric_selected(events,th)
    routes=Counter(r.get("sequential_key","NONE") for r in mr)
    fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
    ps=gate(m);allpass=allpass and ps
    summary["folds"][test]={**m,"pass":ps,"training_windows":tw,"selected_config":choice["cfg"],
      "accept_quantile":choice["q"],"entry_threshold":th,"nested_training_objective":choice["objective"],
      "nested_training_year_metrics":choice["inner_metrics"],
      "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),"selected_action_counts":dict(acts),
      "runtime_seconds":round(time.perf_counter()-ft,3)}
    models["folds"][test]={"route_policy":rp,"admission":md,"threshold":th,"choice":choice}
    print("[V74-ROBUST-CROSSFIT]",test,json.dumps({k:summary["folds"][test][k] for k in
      ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)

alpha=bool(allpass)
champ="ROBUST_NESTED_CROSSFIT_ROUTE_AWARE_ADMISSION" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3)
summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="ROBUST_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="ROBUST_CAUSAL_ALPHA_OOF" if alpha else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false")
(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,
                  "promotion_blocker":summary["promotion_blocker"],
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
