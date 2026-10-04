#!/usr/bin/env python3
"""V74 one-shot family-native causal action selector.

Final V74 Alpha architecture:
* harmonic completion remains the setup identity;
* EARLY and LATE completed-bar actions share one legal action universe;
* reaction/pullback/reclaim state is evidence, never a hard setup-level filter;
* one fixed bounded depth-3 boosted ensemble estimates Expected-R and P(R>0);
* a bounded counterfactual pair model arbitrates concurrently legal actions;
* admission is coverage-constrained from training years only;
* burned OOF years are evaluated once; Validation/Fresh are never loaded.

No post-decision trigger/lock/outcome state is admitted as a feature. V75 exit,
profit-capture and Grid/capital-capacity mechanics are intentionally excluded.
"""
import bisect,json,math,pathlib,statistics,sys,time
from collections import defaultdict,Counter
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,FAMILIES

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)]
BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;TRAIN_COVERAGE=275;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
SOURCES=("EARLY","LATE");V74_QUALIFICATION_FRACTION="30";EARLY_FRACTIONS=(V74_QUALIFICATION_FRACTION,);LATE_FRACTIONS=(V74_QUALIFICATION_FRACTION,);ALL_FRACTIONS=(V74_QUALIFICATION_FRACTION,);MSTAGES=("05","10","15");EARLY_MSTAGES=("15",);LATE_MSTAGES=MSTAGES
BASES=[f"R{r}_{h}_RR{rr}" for r in ("025","050") for h in ("H","D") for rr in ("35","40")]
TREE_KFEAT=30;PAIR_KFEAT=26;TREE_ROUNDS=10;PAIR_ROUNDS=8;TREE_DEPTH=3;TOP_PAIR=6
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and
                m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def qtile(v,q):
    if not v:return 0.0
    x=sorted(float(z) for z in v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def med(v,d=0.0):return statistics.median(v) if v else d
def key(m,b,f):return f"M{m}_{b}_F{f}"
def lev(b):return "025" if b.startswith("R025_") else "050"

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
    try:v=float(v);rr=float(rr)
    except:return None
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
    if src=="EARLY":v=r.get("sequential_state",{}).get(lev(b))
    else:v=r.get("late_auction_maturity_state",{}).get(key(m,b,f))
    if v is None or len(v)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    try:
        z=[float(x) for x in v]
        return z if all(math.isfinite(x) for x in z) else None
    except:return None

def entry_state(r,src,m,b,f):
    _,_,_,_,em=source_maps(r,src);v=em.get(key(m,b,f))
    if v is None or len(v)!=SEQUENTIAL_STATE_FEATURE_COUNT:return None
    try:
        z=[float(x) for x in v]
        return z if all(math.isfinite(x) for x in z) else None
    except:return None

def timing_state(r,src,m,b,f,eb):
    k=key(m,b,f)
    if src=="EARLY":
        rb=r.get("sequential_reaction_bar",{}).get(k,-1)
        return [max(-1.0,min(6.0,float(eb)/10.0)),
                max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
                0.0,0.0]
    rb=r.get("late_auction_reaction_bars",{}).get(k,-1)
    ab=r.get("late_auction_anchor_bars",{}).get(k,-1)
    tb=r.get("late_auction_trigger_bars",{}).get(k,-1)
    return [max(-1.0,min(6.0,float(eb)/10.0)),
            max(-1.0,min(6.0,float(rb)/10.0)) if rb is not None else -1.0,
            max(-1.0,min(6.0,float(ab)/10.0)) if ab is not None else -1.0,
            max(-1.0,min(6.0,float(tb)/10.0)) if tb is not None else -1.0]

def route_cats(r,src,b,m,f):
    return [1.0 if r["family"]==ff else 0.0 for ff in FAMILIES]+[
      1.0 if r["action"]=="CONTINUATION" else 0.0,
      1.0 if src=="LATE" else 0.0,
      1.0 if b.startswith("R050_") else 0.0,
      1.0 if "_D_" in b else 0.0,
      1.0 if b.endswith("RR40") else 0.0]+[
      1.0 if m==mm else 0.0 for mm in MSTAGES]+[
      1.0 if f==ff else 0.0 for ff in ALL_FRACTIONS]

def xvec(r,src,m,b,f,eb):
    # Missing reaction/path snapshots are explicit evidence, not a hard rejection.
    a=maturity_state(r,src,m,b,f);e=entry_state(r,src,m,b,f)
    ap=1.0 if a is not None else 0.0;ep=1.0 if e is not None else 0.0
    aa=a if a is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    ee=e if e is not None else [0.0]*SEQUENTIAL_STATE_FEATURE_COUNT
    delta=[ee[i]-aa[i] if ap and ep else 0.0 for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    return (list(r.get("features",[]))+route_cats(r,src,b,m,f)+aa+ee+delta+
            [ap,ep,1.0 if ap and ep else 0.0]+timing_state(r,src,m,b,f,eb))

def telemetry_guard():
    legal={"EARLY":0,"LATE":0};with_state={"EARLY":0,"LATE":0}
    for r in rows:
      for b in BASES:
        for src in SOURCES:
          for m in (EARLY_MSTAGES if src=="EARLY" else LATE_MSTAGES):
            for f in (EARLY_FRACTIONS if src=="EARLY" else LATE_FRACTIONS):
              eb=entry_bar(r,src,m,b,f)
              if eb<0 or outcome(r,src,m,b,f) is None:continue
              legal[src]+=1
              if maturity_state(r,src,m,b,f) is not None and entry_state(r,src,m,b,f) is not None:
                  with_state[src]+=1
    if sum(legal.values())==0:raise SystemExit("V74 no legal completed-bar actions")
    return {"legal_actions":legal,"complete_path_state":with_state,
            "missing_state_is_feature_not_veto":True,
            "future_trigger_decision_lock_state_used":False}

_OPTION_CACHE={}
def all_options(r,b):
    ck=(r["window"],r["setup"],b)
    if ck in _OPTION_CACHE:return _OPTION_CACHE[ck]
    z=[]
    for src in SOURCES:
      for m in MSTAGES:
        for f in (EARLY_FRACTIONS if src=="EARLY" else LATE_FRACTIONS):
          eb=entry_bar(r,src,m,b,f)
          if eb<0:continue
          y=outcome(r,src,m,b,f)
          if y is None:continue
          rid=("EARLY|"+b if src=="EARLY" else "LATE|M"+m+"_"+b)
          z.append({"rid":rid,"src":src,"m":m,"b":b,"f":f,"y":float(y),"bar":eb,
                    "bars":hold_bars(r,src,m,b,f),"x":xvec(r,src,m,b,f,eb)})
    _OPTION_CACHE[ck]=z
    return z

def make_samples(xs):
    out=[]
    for r in xs:
      for b in BASES:
        for o in all_options(r,b):
          out.append({"window":r["window"],"setup":r["setup"],"family":r["family"],"action":r["action"],
                      "base":b,"route":o["rid"],"bar":o["bar"],"bars":o["bars"],"x":o["x"],
                      "y":o["y"],"row":r})
    return out

def stable_idx(samples,k):
    if not samples:return []
    step=max(1,len(samples)//10000);ss=samples[::step];p=len(ss[0]["x"]);yrs=sorted({s["window"] for s in ss})
    ranked=[]
    for j in range(p):
      vals=[s["x"][j] for s in ss];cut=med(vals);eff=[]
      for w in yrs:
        q=[s for s in ss if s["window"]==w]
        lo=[s["y"] for s in q if s["x"][j]<cut];hi=[s["y"] for s in q if s["x"][j]>=cut]
        if len(lo)<12 or len(hi)<12:continue
        eff.append(statistics.mean(hi)-statistics.mean(lo))
      if len(eff)<max(2,len(yrs)//2):continue
      signs=sum(1 if z>=0 else -1 for z in eff);cons=abs(signs)/len(eff)
      sc=(.65*abs(med(eff))+.35*min(abs(z) for z in eff))*cons
      if sc>0:ranked.append((sc,j))
    ranked.sort(reverse=True)
    return [j for _,j in ranked[:k]] or list(range(min(k,p)))

def grouped_events(samples):
    d=defaultdict(list)
    for s in samples:d[(s["window"],s["setup"],s["bar"])].append(s)
    return d

def _tree_fit(X,y,idx,max_depth=TREE_DEPTH,min_leaf=28):
    # Exact same quantile split search as the reference implementation, but each
    # feature is sorted once per node and SSE is obtained from prefix sums.
    def node(ids,depth):
      n=len(ids);sy=sum(y[i] for i in ids);sy2=sum(y[i]*y[i] for i in ids);mu=sy/n
      leaf={"leaf":mu,"n":n}
      if depth<=0 or n<2*min_leaf:return leaf
      base=sy2-sy*sy/n;best=None
      for j in idx:
        ordered=sorted(ids,key=lambda i:X[i][j])
        vals=[X[i][j] for i in ordered]
        ps=[0.0];ps2=[0.0]
        for i in ordered:
          v=y[i];ps.append(ps[-1]+v);ps2.append(ps2[-1]+v*v)
        for t in sorted(set(qtile(vals,q) for q in (.20,.40,.60,.80))):
          p=bisect.bisect_right(vals,t);ln=p;rn=n-p
          if ln<min_leaf or rn<min_leaf:continue
          ls=ps[p];ls2=ps2[p];rs=sy-ls;rs2=sy2-ls2
          sse=(ls2-ls*ls/ln)+(rs2-rs*rs/rn);gain=base-sse
          if best is None or gain>best[0]:
            best=(gain,j,t,ordered[:p],ordered[p:])
      if best is None or best[0]<=1e-10:return leaf
      _,j,t,li,ri=best
      return {"j":j,"t":t,"n":n,"left":node(li,depth-1),"right":node(ri,depth-1)}
    return node(list(range(len(y))),max_depth)

def _tree_pred(t,x):
    n=t
    support=int(n.get("n",1))
    while "leaf" not in n:
      n=n["left"] if x[n["j"]]<=n["t"] else n["right"]
      support=min(support,int(n.get("n",1)))
    return float(n["leaf"]),support

def _boost_train(X,y,idx,rounds=TREE_ROUNDS,lr=.08,max_rows=6500):
    if not y:return {"base":0.0,"trees":[],"lr":lr,"sigma":10.0}
    if len(y)>max_rows:
      step=max(1,math.ceil(len(y)/max_rows));X=X[::step];y=y[::step]
    base=sum(y)/len(y);pred=[base]*len(y);trees=[]
    for _ in range(rounds):
      res=[y[i]-pred[i] for i in range(len(y))]
      tr=_tree_fit(X,res,idx)
      trees.append(tr)
      for i,x in enumerate(X):
        v,_=_tree_pred(tr,x);pred[i]+=lr*v
    resid=[y[i]-pred[i] for i in range(len(y))]
    sig=statistics.stdev(resid) if len(resid)>1 else 10.0
    return {"base":base,"trees":trees,"lr":lr,"sigma":max(.05,sig)}

def _boost_pred(m,x):
    v=float(m["base"]);support=10**9
    for tr in m["trees"]:
      z,n=_tree_pred(tr,x);v+=float(m["lr"])*z;support=min(support,n)
    return v,(0 if support==10**9 else support)

def _residual_cells(samples,pred_mean,pred_win):
    levels={}
    fns={
      "family":lambda s:s["family"],
      "family_action":lambda s:(s["family"],s["action"]),
      "family_base":lambda s:(s["family"],s["base"])}
    for name,fn in fns.items():
      d=defaultdict(list)
      for i,s in enumerate(samples):
        d[str(fn(s))].append((float(s["y"])-pred_mean[i],(1.0 if s["y"]>0 else 0.0)-pred_win[i]))
      levels[name]={}
      for k,v in d.items():
        n=len(v)
        if n<10:continue
        dm=sum(a for a,_ in v)/(n+24.0);dw=sum(b for _,b in v)/(n+24.0)
        levels[name][k]={"n":n,"dm":dm,"dw":dw}
    return levels

def fit_value(samples):
    idx=stable_idx(samples,TREE_KFEAT);X=[s["x"] for s in samples]
    ym=[float(s["y"]) for s in samples];yw=[1.0 if s["y"]>0 else 0.0 for s in samples]
    mm=_boost_train(X,ym,idx,rounds=TREE_ROUNDS,lr=.075)
    wm=_boost_train(X,yw,idx,rounds=TREE_ROUNDS,lr=.075)
    pm=[_boost_pred(mm,x)[0] for x in X];pw=[max(0.0,min(1.0,_boost_pred(wm,x)[0])) for x in X]
    return {"idx":idx,"mean":mm,"win":wm,"residuals":_residual_cells(samples,pm,pw)}

def pred_value(md,s):
    mu,s1=_boost_pred(md["mean"],s["x"]);wi,s2=_boost_pred(md["win"],s["x"])
    wi=max(0.0,min(1.0,wi));adds_m=[];adds_w=[];supports=[s1 or 1,s2 or 1]
    for lvl,k in (("family",str(s["family"])),
                  ("family_action",str((s["family"],s["action"]))),
                  ("family_base",str((s["family"],s["base"])))):
      z=md["residuals"].get(lvl,{}).get(k)
      if z:adds_m.append(z["dm"]);adds_w.append(z["dw"]);supports.append(z["n"])
    if adds_m:mu+=med(adds_m)
    if adds_w:wi=max(0.0,min(1.0,wi+med(adds_w)))
    sup=max(1,min(supports));lc=mu-Z*float(md["mean"]["sigma"])/math.sqrt(sup)
    score=mu+1.35*wi+.55*lc
    return {"mean":mu,"win":wi,"lcb":lc,"support":sup,"value_score":score}

def fit_pair(samples):
    idx=stable_idx(samples,PAIR_KFEAT);X=[];yw=[];yd=[]
    for ev in grouped_events(samples).values():
      if len(ev)<2:continue
      a=sorted(ev,key=lambda z:(z["base"],z["route"]));n=len(a)
      offs=sorted(set([1,max(1,n//4),max(1,n//2),max(1,(3*n)//4)]))
      for i in range(n):
        for off in offs:
          j=(i+off)%n
          if i>=j:continue
          aa,bb=a[i],a[j];delta=float(aa["y"])-float(bb["y"])
          if abs(delta)<1e-12:continue
          d=[aa["x"][q]-bb["x"][q] for q in idx]
          X.append(d);yw.append(1.0 if delta>0 else 0.0);yd.append(max(-4.0,min(4.0,delta)))
          X.append([-z for z in d]);yw.append(0.0 if delta>0 else 1.0);yd.append(max(-4.0,min(4.0,-delta)))
    if len(X)<200:return {"valid":False,"idx":idx,"n":len(X)}
    if len(X)>10000:
      step=max(1,math.ceil(len(X)/10000));X=X[::step];yw=yw[::step];yd=yd[::step]
    use=list(range(len(idx)))
    return {"valid":True,"idx":idx,"n":len(X),
            "win":_boost_train(X,yw,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=7000),
            "delta":_boost_train(X,yd,use,rounds=PAIR_ROUNDS,lr=.08,max_rows=7000)}

def pair_pref(pm,a,b):
    if not pm.get("valid"):return 0.0
    d=[a["x"][q]-b["x"][q] for q in pm["idx"]];rd=[-z for z in d]
    fw,_=_boost_pred(pm["win"],d);bw,_=_boost_pred(pm["win"],rd)
    fd,_=_boost_pred(pm["delta"],d);bd,_=_boost_pred(pm["delta"],rd)
    p=.5*(fw+(1.0-bw));dr=.5*(fd-bd)
    return 2.0*(max(0.0,min(1.0,p))-.5)+.40*math.tanh(dr/1.5)

def event_decisions(samples,vm,pm):
    out=[]
    for ev in grouped_events(samples).values():
      if not ev:continue
      direct=[]
      for s in ev:
        p=pred_value(vm,s);direct.append((p["value_score"],p,s))
      direct.sort(key=lambda z:(z[0],z[1]["lcb"],z[1]["win"],z[2]["route"]),reverse=True)
      cand=direct[:min(TOP_PAIR,len(direct))]
      pair=[0.0]*len(cand)
      for i in range(len(cand)):
        for j in range(i+1,len(cand)):
          z=pair_pref(pm,cand[i][2],cand[j][2]);pair[i]+=z;pair[j]-=z
      scored=[]
      for i,(base,p,s) in enumerate(cand):
        adv=pair[i]/max(1,len(cand)-1)
        score=base+.35*adv
        scored.append((score,adv,p,s))
      scored.sort(key=lambda z:(z[0],z[2]["lcb"],z[2]["win"],z[3]["route"]),reverse=True)
      score,adv,p,s=scored[0];second=scored[1][0] if len(scored)>1 else score
      q=dict(s);q["pair_advantage"]=adv;q["decision_score"]=score;q["decision_margin"]=score-second
      out.append({"score":score,"pred":dict(p,pair_advantage=adv),"s":q})
    return out

def simulate(decisions,th,window=None):
    d=defaultdict(list)
    for e in decisions:
      if window is not None and e["s"]["window"]!=window:continue
      d[(e["s"]["window"],e["s"]["setup"])].append(e)
    sel=[]
    for ev in d.values():
      ev.sort(key=lambda e:(e["s"]["bar"],-e["score"],e["s"]["route"]))
      for e in ev:
        if e["score"]+1e-12>=th:
          sel.append(e);break
    return sel

def metric_selected(sel):
    rr=[]
    for e in sel:
      s=e["s"];q=dict(s["row"]);q["r"]=s["y"];q["bars"]=s["bars"];q["sequential_key"]=s["route"];rr.append(q)
    return metrics(rr),rr

def coverage_threshold(decisions,years,target=TRAIN_COVERAGE):
    # Highest training-only threshold that preserves target unique setups in every year.
    by=defaultdict(lambda:defaultdict(lambda:-math.inf))
    for e in decisions:
      w=e["s"]["window"];setup=e["s"]["setup"]
      by[w][setup]=max(by[w][setup],float(e["score"]))
    limits={};supply={}
    for w in years:
      vals=sorted(by[w].values(),reverse=True);supply[w]=len(vals)
      if not vals:limits[w]=-math.inf;continue
      k=min(target,len(vals))
      limits[w]=vals[k-1]
    finite=[v for v in limits.values() if math.isfinite(v)]
    th=min(finite) if finite else -math.inf
    return th,limits,supply

def fit_policy(train_rows):
    samples=make_samples(train_rows)
    if len(samples)<1000:raise SystemExit("V74 insufficient legal action samples")
    vm=fit_value(samples);pm=fit_pair(samples)
    if not pm.get("valid"):raise SystemExit("V74 pairwise model invalid")
    dec=event_decisions(samples,vm,pm)
    yrs=sorted({r["window"] for r in train_rows})
    th,limits,supply=coverage_threshold(dec,yrs,TRAIN_COVERAGE)
    tm={}
    for w in yrs:
      m,_=metric_selected(simulate(dec,th,w));tm[w]=m
    return {"value_model":vm,"pairwise_ranker":pm,"threshold":th,
            "training_coverage_limits":limits,"training_supply":supply,
            "training_metrics":tm,"coverage_target":TRAIN_COVERAGE},samples

def apply_policy(policy,test_rows):
    samples=make_samples(test_rows)
    dec=event_decisions(samples,policy["value_model"],policy["pairwise_ranker"])
    sel=simulate(dec,policy["threshold"])
    return sel,samples,dec

checks=telemetry_guard()
summary={"version":"HarmonyBot V74 One-Shot Family-Native Causal Action Selector",
 "architecture":"FAMILY_NATIVE_BOUNDED_DEPTH3_CAUSAL_ENSEMBLE_COVERAGE_CONSTRAINED_OPTIMAL_STOPPING",
 "gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,
         "min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
 "research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
 "policy":{"actions":"EARLY_OR_LATE_COMPLETED_BAR_ENTRY_ACTION__FIXED_F30_QUALIFICATION",
           "harmonic_completion":"SETUP_IDENTITY_NOT_AUTOMATIC_ENTRY",
           "reaction_state":"CAUSAL_FEATURE_NOT_HARD_FILTER","physical_route_contract":"EARLY_ENTRY_IDENTITY_R_H_RR_ONLY__LATE_M_IS_ENTRY_MATURITY__FIXED_F30_QUALIFICATION","v75_management_variants_excluded":True,"early_post_entry_m_stage_excluded":True,
           "route_choice":"BOUNDED_DEPTH3_EXPECTED_R_WIN_PROB_PLUS_COUNTERFACTUAL_PAIRWISE_DELTA",
           "admission":"TRAINING_ONLY_COVERAGE_CONSTRAINED_SCORE_THRESHOLD",
           "training_coverage_target_per_year":TRAIN_COVERAGE,
           "family_hierarchy":"GLOBAL_TO_FAMILY_TO_FAMILY_ACTION_TO_FAMILY_BASE_SHRINKAGE",
           "no_trigger_posttrigger_lock_future_state":True,
           "canonical_family_blanket_blacklist":False,"grid":False,
           "v75_profit_capture_used":False},
 "folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":summary["architecture"],"folds":{}}
t0=time.perf_counter();allpass=True

for test in BURNED:
  ft=time.perf_counter();tw=RESEARCH+[w for w in BURNED if w!=test]
  tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
  policy,_=fit_policy(tr)
  sel,_,dec=apply_policy(policy,te);m,mr=metric_selected(sel)
  routes=Counter(r.get("sequential_key","NONE") for r in mr)
  fams=Counter(r["family"] for r in mr);acts=Counter(r["action"] for r in mr)
  srcs=Counter(x.split("|",1)[0] for x in routes.elements())
  ps=gate(m);allpass=allpass and ps
  summary["folds"][test]={**m,"pass":ps,"training_windows":tw,
    "entry_threshold":policy["threshold"],"training_coverage_target":TRAIN_COVERAGE,
    "training_supply":policy["training_supply"],"training_year_metrics":policy["training_metrics"],
    "test_legal_actions":sum(1 for _ in make_samples(te)),"test_decision_events":len(dec),
    "selected_route_counts":dict(routes),"selected_family_counts":dict(fams),
    "selected_action_counts":dict(acts),"selected_source_counts":dict(srcs),
    "runtime_seconds":round(time.perf_counter()-ft,3)}
  models["folds"][test]=policy
  print("[V74-ONE-SHOT]",test,json.dumps({k:summary["folds"][test][k]
        for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)

alpha=bool(allpass)
champ="FAMILY_NATIVE_BOUNDED_DEPTH3_CAUSAL_ENSEMBLE_COVERAGE_CONSTRAINED_OPTIMAL_STOPPING" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3)
summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="ONE_SHOT_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="ONE_SHOT_CAUSAL_ALPHA_OOF" if alpha else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2))
(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false")
(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,
                  "promotion_blocker":summary["promotion_blocker"],
                  "evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
