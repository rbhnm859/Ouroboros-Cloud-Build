#!/usr/bin/env python3
"""V74 reaction-proven pullback re-entry causal auction.

Capital remains zero through harmonic completion, reaction and pullback.
Only a later completed-bar reclaim/micro-BOS may create a legal ENTER action.
V75 exit/profit-capture mechanics are intentionally excluded. Validation/Fresh
are never loaded. Burned OOF years are evaluated once after training-only
route/frontier/admission choices are frozen.
"""
import json,math,pathlib,statistics,sys,time
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,FAMILIES,_stump_train,_stump_pred

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)];BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
FRACTIONS=("20","30");MSTAGES=("05","10","15")
BASES=[f"R{r}_{h}_RR{rr}" for r in ("025","050") for h in ("H","D") for rr in ("35","40")]
MASKS={
 "ALL":lambda b:True,
 "H_ONLY":lambda b:"_H_" in b,
 "RR40_ONLY":lambda b:b.endswith("RR40"),
 "H_RR40":lambda b:"_H_" in b and b.endswith("RR40"),
}
CONFIGS=[{"mask":mask,"effect_w":ew,"bins":4,"shrink":24.0,"kfeat":18,"win_w":1.10,"lcb_w":0.55}
         for mask in MASKS for ew in (0.65,1.00)]
QGRID=[i/100.0 for i in (0,5,10,15,20,25,30,35,40,45,50)]
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")
if sum(len(r.get("sequential_entry_bar",{}))+len(r.get("late_auction_entry_bars",{})) for r in rows)==0:
    raise SystemExit("V74 unified exact-event telemetry missing")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def margin(m):
    if m["n"]<=0:return -999.0
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,
               m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25)
def qtile(v,q):
    if not v:return math.inf
    x=sorted(float(z) for z in v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def med(v,d=0.0):return statistics.median(v) if v else d
def key(m,b,f):return f"M{m}_{b}_F{f}"
def lev(b):return "025" if b.startswith("R025_") else "050"
def parse_route(rid):
    src,k=rid.split("|",1);base,frac=k.rsplit("_F",1);m=base[1:3];b=base[4:]
    return src,m,b,frac

def source_maps(r,src):
    if src=="EARLY":
        return (r.get("sequential",{}),r.get("sequential_rr",{}),r.get("sequential_bars",{}),
                r.get("sequential_entry_bar",{}),r.get("sequential_entry_state",{}))
    return (r.get("late_auction",{}),r.get("late_auction_rr",{}),r.get("late_auction_bars",{}),
            r.get("late_auction_entry_bars",{}),r.get("late_auction_entry_state",{}))

def outcome(r,src,m,b,f):
    om,rrm,_,_,_=source_maps(r,src);k=key(m,b,f)
    v=om.get(k);rr=rrm.get(k)
    if v is None or rr is None:return None
    v=float(v);rr=float(rr)
    if not all(math.isfinite(x) for x in (v,rr)) or rr+1e-9<MIN_RR:return None
    return v

def entry_bar(r,src,m,b,f):
    _,_,_,bm,_=source_maps(r,src)
    try:return int(bm.get(key(m,b,f),-1))
    except:return -1
def hold_bars(r,src,m,b,f):
    _,_,hm,_,_=source_maps(r,src)
    try:return max(1,int(hm.get(key(m,b,f),r.get("bars",1)) or 1))
    except:return max(1,int(r.get("bars",1) or 1))
def maturity_state(r,src,m,b,f):
    if src=="EARLY":
        v=r.get("sequential_state",{}).get(lev(b))
    else:
        v=r.get("late_auction_maturity_state",{}).get(key(m,b,f))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None
def entry_state(r,src,m,b,f):
    _,_,_,_,em=source_maps(r,src);v=em.get(key(m,b,f))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None

def route_cats(r,src,b,m,f):
    return [1.0 if r["family"]==ff else 0.0 for ff in FAMILIES]+[
      1.0 if r["action"]=="CONTINUATION" else 0.0,
      1.0 if src=="LATE" else 0.0,
      1.0 if b.startswith("R050_") else 0.0,1.0 if "_D_" in b else 0.0,1.0 if b.endswith("RR40") else 0.0]+[
      1.0 if m==mm else 0.0 for mm in MSTAGES]+[1.0 if f==ff else 0.0 for ff in FRACTIONS]

def xvec(r,src,m,b,f):
    a=maturity_state(r,src,m,b,f);e=entry_state(r,src,m,b,f)
    if a is None or e is None:return None
    # No trigger/post-trigger/lock state is admitted.
    return list(r.get("features",[]))+route_cats(r,src,b,m,f)+a+e+[e[i]-a[i] for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]

def telemetry_guard():
    n=0
    for r in rows:
      for b in BASES:
        for m in MSTAGES:
          for f in FRACTIONS:
            k=key(m,b,f)
            eb=r.get("late_auction_entry_bars",{}).get(k)
            if eb is None or int(eb)<0:continue
            ms=r.get("late_auction_maturity_state",{}).get(k)
            es=r.get("late_auction_entry_state",{}).get(k)
            if ms is None or es is None or len(ms)!=SEQUENTIAL_STATE_FEATURE_COUNT or len(es)!=SEQUENTIAL_STATE_FEATURE_COUNT:
                raise SystemExit(f"V74 incomplete reaction-proven state {r['setup']} {k}")
            n+=1
    if n==0:raise SystemExit("V74 no legal reaction-proven entries")
    return n

_OPTION_CACHE={}
def all_options(r,b):
    # Final V74 action space is LATE-only: harmonic completion cannot own capital.
    # Each option is a real completed-bar reaction->pullback->reclaim re-entry.
    ck=(r["window"],r["setup"],b)
    hit=_OPTION_CACHE.get(ck)
    if hit is not None:return hit
    z=[]
    src="LATE"
    for m in MSTAGES:
      for f in FRACTIONS:
        eb=entry_bar(r,src,m,b,f)
        if eb<0:continue
        y=outcome(r,src,m,b,f)
        if y is None:continue
        rid=src+"|"+key(m,b,f);x=xvec(r,src,m,b,f)
        if x is None:continue
        z.append({"rid":rid,"src":src,"m":m,"b":b,"f":f,"y":float(y),"bar":eb,
                  "bars":hold_bars(r,src,m,b,f),"x":x})
    _OPTION_CACHE[ck]=z
    return z

def robust_route_score(vals,years,shrink=18.0):
    if not vals:return -999.0
    ys=[v for _,v in vals];pm=statistics.mean(ys);pw=sum(v>0 for v in ys)/len(ys);ym=[];yw=[]
    for w in years:
      a=[v for ww,v in vals if ww==w]
      if not a:continue
      mm=statistics.mean(a);ww=sum(v>0 for v in a)/len(a)
      ym.append((mm*len(a)+pm*shrink)/(len(a)+shrink));yw.append((ww*len(a)+pw*shrink)/(len(a)+shrink))
    if not ym:return -999.0
    return .55*min(ym)+.25*med(ym)+.20*pm+1.15*min(yw)+.35*med(yw)

def fit_frontier(xs,mask,topk=2):
    yrs=sorted({r["window"] for r in xs});mf=MASKS[mask]
    tabs={lvl:defaultdict(lambda:defaultdict(list)) for lvl in ("exact","fam_base","base")}
    for r in xs:
      for b in BASES:
        if not mf(b):continue
        for o in all_options(r,b):
          tabs["exact"][(r["family"],r["action"],b)][o["rid"]].append((r["window"],o["y"]))
          tabs["fam_base"][(r["family"],b)][o["rid"]].append((r["window"],o["y"]))
          tabs["base"][b][o["rid"]].append((r["window"],o["y"]))
    outp={}
    for lvl,t in tabs.items():
      outp[lvl]={}
      for cell,rr in t.items():
        q=[]
        for rid,v in rr.items():
          sc=robust_route_score(v,yrs)
          if sc>-900:q.append((sc,len(v),rid))
        q.sort(reverse=True)
        if q:outp[lvl][str(cell)]=[rid for _,_,rid in q[:topk]]
    return {"mask":mask,"topk":topk,"choices":outp}

def frontier_routes(r,b,fr):
    if not MASKS[fr["mask"]](b):return []
    opts={o["rid"]:o for o in all_options(r,b)};seen=[]
    for lvl,cell in (
      ("exact",str((r["family"],r["action"],b))),
      ("fam_base",str((r["family"],b))),
      ("base",str(b)),
    ):
      for rid in fr["choices"].get(lvl,{}).get(cell,[]):
        if rid in opts and rid not in seen:seen.append(rid)
      if seen:break
    return [opts[rid] for rid in seen]

def make_samples(xs,fr):
    out=[]
    for r in xs:
      for b in BASES:
        for o in frontier_routes(r,b,fr):
          out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                      "base":b,"route":o["rid"],"bar":o["bar"],"bars":o["bars"],"x":o["x"],"y":o["y"],"row":r})
    return out

def stable_idx(samples,k):
    if not samples:return []
    # deterministic training-only subsample prevents feature-ranking from dominating runtime
    step=max(1,len(samples)//12000);ss=samples[::step];p=len(ss[0]["x"]);yrs=sorted({s["window"] for s in ss})
    ranked=[]
    for j in range(p):
      cut=med([s["x"][j] for s in ss]);eff=[]
      for w in yrs:
        q=[s for s in ss if s["window"]==w];lo=[s["y"] for s in q if s["x"][j]<cut];hi=[s["y"] for s in q if s["x"][j]>=cut]
        if len(lo)<16 or len(hi)<16:continue
        eff.append(statistics.mean(hi)-statistics.mean(lo))
      if len(eff)<max(3,len(yrs)//2):continue
      cons=abs(sum(1 if z>=0 else -1 for z in eff))/len(eff)
      sc=(.55*abs(med(eff))+.45*min(abs(z) for z in eff))*cons
      if sc>0:ranked.append((sc,j))
    ranked.sort(reverse=True);return [j for _,j in ranked[:k]] or list(range(min(k,p)))

def grouped_events(samples):
    d=defaultdict(list)
    for s in samples:d[(s["window"],s["setup"],s["bar"])].append(s)
    return d

def fit_pair_ranker(samples,kfeat=22,rounds=7):
    """Training-only counterfactual ranker for legal actions sharing one completed-bar decision event."""
    idx=stable_idx(samples,kfeat);X=[];yw=[];yd=[]
    for ev in grouped_events(samples).values():
      if len(ev)<2:continue
      a=sorted(ev,key=lambda z:(z["base"],z["route"]))
      n=len(a);pairs=set()
      offsets=sorted(set([1,max(1,n//3),max(1,(2*n)//3)]))
      for i in range(n):
        for off in offsets:
          j=(i+off)%n
          if i==j:continue
          u,v=(i,j) if i<j else (j,i)
          pairs.add((u,v))
      for i,j in sorted(pairs):
        aa,bb=a[i],a[j];delta=float(aa["y"])-float(bb["y"])
        if abs(delta)<1e-9:continue
        d=[aa["x"][q]-bb["x"][q] for q in idx]
        X.append(d);yw.append(1.0 if delta>0 else 0.0);yd.append(max(-4.0,min(4.0,delta)))
        X.append([-z for z in d]);yw.append(0.0 if delta>0 else 1.0);yd.append(max(-4.0,min(4.0,-delta)))
    # Deterministic thinning is both a runtime bound and regularizer. Pair orientation
    # is already doubled above, so 8k rows preserve broad state coverage without
    # letting repeated near-identical route comparisons dominate the learner.
    if len(X)>8000:
      step=max(1,math.ceil(len(X)/8000));X=X[::step];yw=yw[::step];yd=yd[::step]
    if len(X)<200:
      return {"valid":False,"idx":idx,"n":len(X)}
    return {"valid":True,"idx":idx,"n":len(X),
            "win":_stump_train(X,yw,rounds=rounds,lr=.10),
            "delta":_stump_train(X,yd,rounds=rounds,lr=.09)}

def pair_pref(pm,a,b):
    if not pm.get("valid"):return 0.0
    d=[a["x"][q]-b["x"][q] for q in pm["idx"]]
    pd=[-z for z in d]
    fw,_=_stump_pred(pm["win"],d);bw,_=_stump_pred(pm["win"],pd)
    fd,_=_stump_pred(pm["delta"],d);bd,_=_stump_pred(pm["delta"],pd)
    p=max(0.0,min(1.0,.5*(fw+(1.0-bw))))
    dr=.5*(fd-bd)
    return 2.0*(p-.5)+.35*math.tanh(dr/1.5)

def rank_samples(samples,pm):
    """One pairwise winner per event; exploit exact antisymmetry to halve inference work."""
    out=[]
    for ev in grouped_events(samples).values():
      if not ev:continue
      n=len(ev);sums=[0.0]*n
      # pair_pref(b,a) == -pair_pref(a,b) by construction, so evaluate each
      # unordered pair exactly once. This is semantics-preserving.
      for i in range(n):
        for j in range(i+1,n):
          p=pair_pref(pm,ev[i],ev[j]);sums[i]+=p;sums[j]-=p
      scored=[((sums[i]/(n-1)) if n>1 else 0.0,ev[i]) for i in range(n)]
      scored.sort(key=lambda z:(z[0],z[1]["route"]),reverse=True)
      best_score,best=scored[0]
      second=scored[1][0] if len(scored)>1 else 0.0
      q=dict(best);q["x"]=list(best["x"])+[best_score,best_score-second,float(len(ev))]
      q["pair_rank_score"]=best_score;q["pair_rank_margin"]=best_score-second;q["pair_event_actions"]=len(ev)
      out.append(q)
    return out

def bin_of(x,edges):
    b=0
    while b<len(edges) and x>edges[b]:b+=1
    return b

def robust_stat(samples,gy,gm,gw,shrink):
    if not samples:return {"n":0,"mean":gm,"win":gw,"sigma":10.0}
    ys=[s["y"] for s in samples];pm=statistics.mean(ys);pw=sum(y>0 for y in ys)/len(ys);ym=[];yw=[]
    for w,(gmean,gwin) in gy.items():
      a=[s["y"] for s in samples if s["window"]==w]
      if not a:ym.append(gmean);yw.append(gwin);continue
      mm=statistics.mean(a);ww=sum(y>0 for y in a)/len(a)
      ym.append((mm*len(a)+gmean*shrink)/(len(a)+shrink));yw.append((ww*len(a)+gwin*shrink)/(len(a)+shrink))
    rm=.45*pm+.55*min(ym);rw=.45*pw+.55*min(yw);sg=statistics.stdev(ys) if len(ys)>1 else 10.0
    return {"n":len(ys),"mean":rm,"win":rw,"sigma":max(.05,sg)}

def fit_admission(samples,cfg):
    idx=stable_idx(samples,cfg["kfeat"]);yrs=sorted({s["window"] for s in samples});gy={}
    for w in yrs:
      a=[s["y"] for s in samples if s["window"]==w];gy[w]=(statistics.mean(a),sum(v>0 for v in a)/len(a))
    yy=[s["y"] for s in samples];gm=statistics.mean(yy);gw=sum(v>0 for v in yy)/len(yy)
    gs=robust_stat(samples,gy,gm,gw,cfg["shrink"]);edges={}
    for j in idx:
      vv=[s["x"][j] for s in samples];edges[str(j)]=[qtile(vv,q/cfg["bins"]) for q in range(1,cfg["bins"])]
    levels={};keyf={
      "exact":lambda s:(s["family"],s["action"],s["base"],s["route"].split("|",1)[0]),
      "fam_base":lambda s:(s["family"],s["base"]),
      "family":lambda s:s["family"],"base":lambda s:s["base"]}
    for name,fn in keyf.items():
      d=defaultdict(list)
      for s in samples:d[str(fn(s))].append(s)
      levels[name]={k:robust_stat(v,gy,gm,gw,cfg["shrink"]) for k,v in d.items() if len(v)>=10}
    generic=defaultdict(list);fam_bin=defaultdict(list)
    for s in samples:
      for j in idx:
        b=bin_of(s["x"][j],edges[str(j)]);generic[(j,b)].append(s);fam_bin[(s["family"],j,b)].append(s)
    ge={};fe={}
    for k,v in generic.items():
      if len(v)>=24:
        z=robust_stat(v,gy,gm,gw,cfg["shrink"]);ge[str(k)]={"n":z["n"],"dm":z["mean"]-gs["mean"],"dw":z["win"]-gs["win"]}
    for k,v in fam_bin.items():
      if len(v)>=18:
        z=robust_stat(v,gy,gm,gw,cfg["shrink"]);fs=levels["family"].get(str(k[0]),gs)
        fe[str(k)]={"n":z["n"],"dm":z["mean"]-fs["mean"],"dw":z["win"]-fs["win"]}
    return {"cfg":cfg,"idx":idx,"edges":edges,"global":gs,"priors":levels,"generic":ge,"family_bin":fe}

def predict(md,s):
    g=md["global"];src=s["route"].split("|",1)[0];p=None
    for lvl,k in (("exact",str((s["family"],s["action"],s["base"],src))),
                  ("fam_base",str((s["family"],s["base"]))),("family",str(s["family"])),("base",str(s["base"]))):
      z=md["priors"][lvl].get(k)
      if z is not None and z["n"]>=12:p=z;break
    if p is None:p=g
    dm=[];dw=[];supports=[p["n"]]
    for j in md["idx"]:
      b=bin_of(s["x"][j],md["edges"][str(j)]);z=md["family_bin"].get(str((s["family"],j,b))) or md["generic"].get(str((j,b)))
      if z is not None:dm.append(z["dm"]);dw.append(z["dw"]);supports.append(z["n"])
    mu=p["mean"]+md["cfg"]["effect_w"]*med(dm);wi=max(0.0,min(1.0,p["win"]+md["cfg"]["effect_w"]*med(dw)))
    sup=max(1,min(supports));lc=mu-Z*max(.05,p.get("sigma",g["sigma"]))/math.sqrt(sup)
    return {"score":mu+md["cfg"]["win_w"]*wi+md["cfg"]["lcb_w"]*lc,"mean":mu,"win":wi,"lcb":lc,"support":sup}

def score_samples(samples,md):
    out=[]
    for s in samples:
      z=predict(md,s)
      if math.isfinite(z["score"]):out.append({"score":z["score"],"pred":z,"s":s})
    return out

def event_score_distribution(scored):
    # one best currently-matured action per completed bar
    d=defaultdict(lambda:defaultdict(list))
    for e in scored:d[(e["s"]["window"],e["s"]["setup"])][e["s"]["bar"]].append(e)
    z=[]
    for bars in d.values():
      for a in bars.values():z.append(max(x["score"] for x in a))
    return z

def simulate(scored,th):
    d=defaultdict(lambda:defaultdict(list))
    for e in scored:d[(e["s"]["window"],e["s"]["setup"])][e["s"]["bar"]].append(e)
    sel=[]
    for _,bars in d.items():
      for bar in sorted(bars):
        a=max(bars[bar],key=lambda x:(x["score"],x["pred"]["lcb"],x["pred"]["win"],x["s"]["route"]))
        if a["score"]+1e-12>=th:
          sel.append(a);break
    return sel

def metric_selected(sel):
    rr=[]
    for e in sel:
      s=e["s"];q=dict(s["row"]);q["r"]=s["y"];q["bars"]=s["bars"];q["sequential_key"]=s["route"];rr.append(q)
    return metrics(rr),rr

def choose_config(train_rows,train_years):
    # Nested training-only: pairwise route ranker is fit without the validation year;
    # capital admission is then fit only on the ranker's chosen legal action.
    cache={mask:{} for mask in MASKS};base_models={}
    for val in train_years:
      tr=[r for r in train_rows if r["window"]!=val];va=[r for r in train_rows if r["window"]==val]
      shared=fit_frontier(tr,"ALL",2)
      all_fr={"mask":"ALL","topk":shared["topk"],"choices":shared["choices"]}
      pm=fit_pair_ranker(make_samples(tr,all_fr))
      if not pm.get("valid"):continue
      for mask in MASKS:
        fr={"mask":mask,"topk":shared["topk"],"choices":shared["choices"]}
        ts,vs=make_samples(tr,fr),make_samples(va,fr)
        rt,rv=rank_samples(ts,pm),rank_samples(vs,pm)
        cache[mask][val]=(rt,rv)
        cfg0=next(c for c in CONFIGS if c["mask"]==mask)
        if len(rt)>=500 and len(rv)>=100:base_models[(mask,val)]=fit_admission(rt,cfg0)
    best=None
    for ci,cfg in enumerate(CONFIGS):
      inner={}
      for val in train_years:
        if val not in cache[cfg["mask"]]:inner={};break
        rt,rv=cache[cfg["mask"]][val];base=base_models.get((cfg["mask"],val))
        if base is None:inner={};break
        md=dict(base);md["cfg"]=cfg
        inner[val]=(score_samples(rt,md),score_samples(rv,md))
      if not inner:continue
      for q in QGRID:
        ym=[];ok=True
        for val in train_years:
          trsc,vsc=inner[val];th=qtile(event_score_distribution(trsc),q);m,_=metric_selected(simulate(vsc,th))
          if m["n"]<MIN_N:ok=False
          ym.append((val,m))
        if not ok:continue
        ms=[m for _,m in ym];marg=[margin(m) for m in ms]
        obj=min(marg)+.22*med(marg)+.10*min(m["lcb_r"] for m in ms)+.08*min(m["mean_r"] for m in ms)+.05*min(m["win_rate"] for m in ms)
        tie=(obj,min(marg),med(marg),min(m["win_rate"] for m in ms),-q,-ci)
        if best is None or tie>best[0]:best=(tie,{"cfg":cfg,"q":q,"objective":obj,"inner_metrics":dict(ym)})
    if best is None:raise SystemExit("V74 pairwise nested crossfit found no N>=250 configuration")
    return best[1]

def fit_final(train_rows,choice):
    shared=fit_frontier(train_rows,"ALL",2)
    all_fr={"mask":"ALL","topk":shared["topk"],"choices":shared["choices"]}
    pm=fit_pair_ranker(make_samples(train_rows,all_fr))
    if not pm.get("valid"):raise SystemExit("V74 final pairwise ranker invalid")
    fr={"mask":choice["cfg"]["mask"],"topk":shared["topk"],"choices":shared["choices"]}
    ranked=rank_samples(make_samples(train_rows,fr),pm)
    md=fit_admission(ranked,choice["cfg"])
    trsc=score_samples(ranked,md);th=qtile(event_score_distribution(trsc),choice["q"])
    return fr,pm,md,th

checks=telemetry_guard()
summary={"version":"HarmonyBot V74 Pairwise Counterfactual Selective Auction",
 "architecture":"PAIRWISE_COUNTERFACTUAL_RANKER_SELECTIVE_ADMISSION_OPTIMAL_STOPPING",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,"min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"ZERO_CAPITAL_DEFER__REACTION_PULLBACK_RECLAIM_ENTER_OR_REJECT","route_frontier":"TRAINING_ONLY_TOP2_ROBUST_CELL",
           "route_choice":"PAIRWISE_COUNTERFACTUAL_SAME_EVENT_RANKING","admission":"INDEPENDENT_SELECTED_REENTRY_HIERARCHICAL_HISTOGRAM","hyperparameters":"NESTED_LEAVE_ONE_YEAR_OUT_TRAINING_ONLY",
           "no_trigger_posttrigger_lock_future_state":True,"canonical_family_blanket_blacklist":False,"grid":False,
           "qualification_target":"FRESH_FIXED_NET_RR_2P30_OR_2P50","v75_profit_capture_used":False,
           "legacy_label_mapping":"M05/M10/M15=reaction .50/.75/1.00; R025/R050=pullback .20/.30; H/D=1bar/2bar reclaim; RR35/RR40=2.30/2.50; F20/F30=standard/strict close"},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":summary["architecture"],"folds":{}}
t0=time.perf_counter();allpass=True
for test in BURNED:
  ft=time.perf_counter();tw=RESEARCH+[w for w in BURNED if w!=test]
  tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
  choice=choose_config(tr,tw);fr,pm,md,th=fit_final(tr,choice)
  ranked_test=rank_samples(make_samples(te,fr),pm)
  sel=simulate(score_samples(ranked_test,md),th);m,mr=metric_selected(sel)
  routes=Counter(r.get("sequential_key","NONE") for r in mr);fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
  ps=gate(m);allpass=allpass and ps
  summary["folds"][test]={**m,"pass":ps,"training_windows":tw,"selected_config":choice["cfg"],"accept_quantile":choice["q"],
    "entry_threshold":th,"nested_training_objective":choice["objective"],"nested_training_year_metrics":choice["inner_metrics"],
    "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),"selected_action_counts":dict(acts),
    "runtime_seconds":round(time.perf_counter()-ft,3)}
  models["folds"][test]={"frontier":fr,"pairwise_ranker":pm,"admission":md,"threshold":th,"choice":choice}
  print("[V74-REACTION-PROVEN]",test,json.dumps({k:summary["folds"][test][k] for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)

alpha=bool(allpass);champ="REACTION_PROVEN_PULLBACK_REENTRY_SELECTIVE_OPTIMAL_STOPPING" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3);summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="REACTION_PROVEN_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="REACTION_PROVEN_CAUSAL_ALPHA_OOF" if alpha else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2));(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false");(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,"promotion_blocker":summary["promotion_blocker"],
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
