#!/usr/bin/env python3
"""V74 exact-event fitted-Q causal auction. Validation/Fresh are never loaded."""
import json,math,pathlib,statistics,sys,time
from v74_model_lib import load_rows,metrics,SEQUENTIAL_STATE_FEATURE_COUNT,FAMILIES,_stump_train,_stump_pred

root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)];BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
FRACTIONS=("00","10","20","30");MSTAGES=("05","10","15")
BASES=[f"R{r}_{m}_RR{rr}" for r in ("025","050") for m in ("H","D") for rr in ("35","40")]
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 rows")
if sum(len(r.get("sequential_entry_bar",{})) for r in rows)==0:raise SystemExit("V74 exact-event telemetry missing")

def gate(m):
    return bool(m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0)
def margin(m):
    if m["n"]<=0:return -999.0
    return min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR,1.0+m["lcb_r"]/.25)
def qtile(v,q):
    if not v:return math.inf
    x=sorted(float(z) for z in v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p))
    return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def key(m,b,f):return f"M{m}_{b}_F{f}"
def src(m,b):return key(m,b,"20")
def lev(b):return "025" if b.startswith("R025_") else "050"

def out_r(r,m,b,f):
    k20=key(m,b,"20");k30=key(m,b,"30")
    a=r.get("sequential",{}).get(k20);c=r.get("sequential",{}).get(k30);rr=r.get("sequential_rr",{}).get(k20)
    if a is None or c is None or rr is None:return None
    a=float(a);c=float(c);rr=float(rr)
    if not all(math.isfinite(x) for x in (a,c,rr)) or rr+1e-9<MIN_RR:return None
    if f=="20":return a
    if f=="30":return c
    d=c-a
    return a-(2.0 if f=="00" else 1.0)*d

def st(r,m,b,kind):
    fld={"entry":"sequential_entry_state","trigger":"sequential_trigger_state","decision":"sequential_decision_state"}[kind]
    v=r.get(fld,{}).get(src(m,b))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None
def bar(r,m,b,kind):
    fld={"reaction":"sequential_reaction_bar","entry":"sequential_entry_bar","trigger":"sequential_trigger_bar","decision":"sequential_decision_bar"}[kind]
    try:return int(r.get(fld,{}).get(src(m,b),-1))
    except:return -1
def rs(r,b):
    v=r.get("sequential_state",{}).get(lev(b))
    return list(v) if v is not None and len(v)==SEQUENTIAL_STATE_FEATURE_COUNT else None

def cats(r,b):
    return [1.0 if r["family"]==f else 0.0 for f in FAMILIES]+[
        1.0 if r["action"]=="CONTINUATION" else 0.0,1.0 if b.startswith("R050_") else 0.0,
        1.0 if "_D_" in b else 0.0,1.0 if b.endswith("RR40") else 0.0]

def xvec(r,b,stage,m="15"):
    a=rs(r,b);e=st(r,m,b,"entry")
    if a is None or e is None:return None
    x=list(r.get("features",[]))+cats(r,b)+a+e+[e[i]-a[i] for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    if stage in ("trigger","decision"):
        t=st(r,m,b,"trigger")
        if t is None:return None
        x+=t+[t[i]-e[i] for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    if stage=="decision":
        d=st(r,m,b,"decision")
        if d is None:return None
        x+=d+[d[i]-t[i] for i in range(SEQUENTIAL_STATE_FEATURE_COUNT)]
    return x

def telemetry_guard():
    n=0
    for r in rows:
        for b in BASES:
            for m in MSTAGES:
                k20=key(m,b,"20");k30=key(m,b,"30")
                for fld in ("sequential_entry_bar","sequential_trigger_bar","sequential_decision_bar","sequential_entry_state","sequential_trigger_state","sequential_decision_state"):
                    a=r.get(fld,{}).get(k20);c=r.get(fld,{}).get(k30)
                    if a is not None and c is not None and a!=c:raise SystemExit(f"V74 F20/F30 predecision mismatch {fld} {r['setup']} {m} {b}")
            eb=[bar(r,m,b,"entry") for m in MSTAGES if bar(r,m,b,"entry")>=0]
            if eb and len(set(eb))!=1:raise SystemExit(f"V74 M-stage entry bar mismatch {r['setup']} {b} {eb}")
            n+=1
    return n

def stable_idx(samples,k=22):
    if not samples:return []
    p=len(samples[0]["x"]);yrs=sorted({s["window"] for s in samples});med=[statistics.median(s["x"][j] for s in samples) for j in range(p)]
    d=[]
    for j in range(p):
        ef=[];mn=10**9
        for w in yrs:
            q=[s for s in samples if s["window"]==w];lo=[s["y"] for s in q if s["x"][j]<med[j]];hi=[s["y"] for s in q if s["x"][j]>=med[j]]
            if len(lo)<24 or len(hi)<24:continue
            ef.append(statistics.mean(hi)-statistics.mean(lo));mn=min(mn,len(lo),len(hi))
        if len(ef)<4:continue
        cons=abs(sum(1 if z>0 else -1 for z in ef))/len(ef);fl=min(abs(z) for z in ef);me=statistics.median(ef)
        sc=(.65*abs(me)+.35*fl)*cons*min(1.0,math.sqrt(max(1,mn)/100.0))
        if sc>0:d.append((sc,j))
    d.sort(reverse=True);return [j for _,j in d[:k]] or list(range(min(k,p)))

def fit(samples,rounds=8,k=22):
    if len(samples)<80:return {"valid":False}
    idx=stable_idx(samples,k);X=[[s["x"][j] for j in idx] for s in samples];y=[float(s["y"]) for s in samples];w=[1.0 if z>0 else 0.0 for z in y]
    return {"valid":True,"idx":idx,"mean":_stump_train(X,y,rounds=rounds,lr=.08),"win":_stump_train(X,w,rounds=rounds,lr=.08),"n":len(samples)}

def pred(m,x):
    if not m.get("valid") or x is None:return {"score":-999.0,"mean":0.0,"win":0.0,"lcb":-999.0,"support":0}
    z=[x[j] for j in m["idx"]];mu,s1=_stump_pred(m["mean"],z);wi,s2=_stump_pred(m["win"],z);wi=max(0.0,min(1.0,wi))
    sup=max(1,min(s1 or 1,s2 or 1));lc=mu-Z*max(.05,float(m["mean"].get("sigma",10.0)))/math.sqrt(sup)
    return {"score":lc+.70*mu+1.35*wi,"mean":mu,"win":wi,"lcb":lc,"support":sup}

def frac_samples(xs,m,f):
    z=[]
    for r in xs:
        for b in BASES:
            x=xvec(r,b,"decision",m);y=out_r(r,m,b,f)
            if x is not None and y is not None:z.append({"window":r["window"],"x":x,"y":y})
    return z

def choose_frac(r,b,m,mods):
    y0=out_r(r,m,b,"00")
    if y0 is None:return None
    if bar(r,m,b,"decision")<0:return {"r":y0,"key":key(m,b,"00"),"m":m,"f":"00"}
    x=xvec(r,b,"decision",m);c=[]
    for f in FRACTIONS:
        y=out_r(r,m,b,f)
        if y is None:continue
        p=pred(mods[m][f],x);c.append((p["score"],p["lcb"],p["win"],f,y))
    if not c:return None
    c.sort(reverse=True);_,_,_,f,y=c[0];return {"r":y,"key":key(m,b,f),"m":m,"f":f}

def adv_threshold(samples,model):
    if not samples:return math.inf
    sc=[(pred(model,s["x"])["score"],s) for s in samples];v=[a for a,_ in sc if math.isfinite(a) and a>-900];yrs=sorted({s["window"] for s in samples})
    best=(0.0,math.inf)
    for th in [math.inf]+[qtile(v,i*.05) for i in range(19)]:
        gm=[]
        for w in yrs:
            q=[s["y"] if a>=th else 0.0 for a,s in sc if s["window"]==w]
            if len(q)<20:gm=[];break
            gm.append(statistics.mean(q))
        if not gm:continue
        o=min(gm)+.25*statistics.median(gm)
        if o>best[0]+1e-12:best=(o,th)
    return best[1]

def fit_fold(tr):
    fm={m:{f:fit(frac_samples(tr,m,f),8,22) for f in FRACTIONS} for m in MSTAGES}
    def p15(r,b):return choose_frac(r,b,"15",fm)
    s10=[]
    for r in tr:
        for b in BASES:
            if bar(r,"10",b,"trigger")<0:continue
            a=choose_frac(r,b,"10",fm);d=p15(r,b);x=xvec(r,b,"trigger","10")
            if a and d and x is not None:s10.append({"window":r["window"],"x":x,"y":a["r"]-d["r"]})
    m10=fit(s10);t10=adv_threshold(s10,m10)
    def p10(r,b):
        d=p15(r,b)
        if bar(r,"10",b,"trigger")<0:return d
        a=choose_frac(r,b,"10",fm);x=xvec(r,b,"trigger","10")
        return a if a and x is not None and pred(m10,x)["score"]>=t10 else d
    s05=[]
    for r in tr:
        for b in BASES:
            if bar(r,"05",b,"trigger")<0:continue
            a=choose_frac(r,b,"05",fm);d=p10(r,b);x=xvec(r,b,"trigger","05")
            if a and d and x is not None:s05.append({"window":r["window"],"x":x,"y":a["r"]-d["r"]})
    m05=fit(s05);t05=adv_threshold(s05,m05)
    def pol(r,b):
        d=p10(r,b)
        if bar(r,"05",b,"trigger")<0:return d
        a=choose_frac(r,b,"05",fm);x=xvec(r,b,"trigger","05")
        return a if a and x is not None and pred(m05,x)["score"]>=t05 else d
    es=[]
    for r in tr:
        for b in BASES:
            x=xvec(r,b,"entry","15");res=pol(r,b)
            if bar(r,"15",b,"entry")>=0 and x is not None and res:es.append({"window":r["window"],"x":x,"y":res["r"]})
    em=fit(es,10,28)
    return {"frac":fm,"m10":m10,"t10":t10,"m05":m05,"t05":t05,"entry":em},pol

def test_policy(model,r,b):
    fm=model["frac"];d=choose_frac(r,b,"15",fm)
    if bar(r,"10",b,"trigger")>=0:
        a=choose_frac(r,b,"10",fm);x=xvec(r,b,"trigger","10")
        if a and x is not None and pred(model["m10"],x)["score"]>=model["t10"]:d=a
    if bar(r,"05",b,"trigger")>=0:
        a=choose_frac(r,b,"05",fm);x=xvec(r,b,"trigger","05")
        if a and x is not None and pred(model["m05"],x)["score"]>=model["t05"]:d=a
    return d

def event_book(xs,model,policy):
    bk={}
    for r in xs:
        ev=[]
        for b in BASES:
            eb=bar(r,"15",b,"entry");x=xvec(r,b,"entry","15");res=policy(r,b)
            if eb<0 or x is None or not res:continue
            p=pred(model["entry"],x)
            if p["support"]<20 or p["score"]<=-900:continue
            rb=int(r.get("sequential_bars",{}).get(src(res["m"],b),r.get("bars",1)))
            ev.append({"bar":eb,"score":p["score"],"lcb":p["lcb"],"win":p["win"],"base":b,"r":res["r"],"key":res["key"],"bars":rb,"row":r})
        ev.sort(key=lambda z:(z["bar"],-z["score"],z["base"]));bk[(r["window"],r["setup"])]=ev
    return bk

def simulate(bk,th):
    out=[]
    for ev in bk.values():
        i=0
        while i<len(ev):
            b=ev[i]["bar"];g=[]
            while i<len(ev) and ev[i]["bar"]==b:g.append(ev[i]);i+=1
            x=max(g,key=lambda z:(z["score"],z["lcb"],z["win"],z["base"]))
            if x["score"]+1e-12>=th:out.append(x);break
    return out

def metric_rows(sel):
    z=[]
    for x in sel:
        q=dict(x["row"]);q["r"]=x["r"];q["bars"]=max(1,x["bars"]);q["sequential_key"]=x["key"];z.append(q)
    return z

def opt_threshold(bk,tw):
    vals=[e["score"] for v in bk.values() for e in v if math.isfinite(e["score"]) and e["score"]>-900];best=None
    for qi in range(33):
        q=qi*.025;th=qtile(vals,q);sel=simulate(bk,th);mr=metric_rows(sel);ym=[metrics([r for r in mr if r["window"]==w]) for w in tw]
        if not all(x["n"]>=MIN_N for x in ym):continue
        ma=[margin(x) for x in ym];obj=min(ma)+.20*statistics.median(ma);tie=(obj,min(x["lcb_r"] for x in ym),min(x["mean_r"] for x in ym),min(x["win_rate"] for x in ym),-len(sel))
        if best is None or tie>best[0]:best=(tie,{"q":q,"th":th,"sel":sel,"ym":ym,"obj":obj})
    return best[1] if best else {"q":None,"th":math.inf,"sel":[],"ym":[],"obj":-999.0}

checks=telemetry_guard();summary={"version":"HarmonyBot V74 Exact Event Fitted-Q","architecture":"EXACT_EVENT_FITTED_Q_OPTIMAL_STOPPING",
"gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,"min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
"research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
"policy":{"entry":"REAL_ENTRY_BAR_ORDERED_ACCEPT_OR_DEFER","post_entry":"M05_DEFER_M10_DEFER_M15","fraction":"DECISION_STATE_ONLY_F00_F10_F20_F30",
"no_future_state":True,"canonical_family_blanket_blacklist":False,"grid":False},
"folds":{},"validation_used":False,"fresh_used":False,"telemetry_contract_checks":checks}
models={"architecture":"EXACT_EVENT_FITTED_Q_OPTIMAL_STOPPING","folds":{}}
t0=time.perf_counter();allpass=True
for test in BURNED:
    ft=time.perf_counter();tw=RESEARCH+[w for w in BURNED if w!=test];tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test]
    model,pol=fit_fold(tr);tb=event_book(tr,model,pol);opt=opt_threshold(tb,tw)
    testpol=lambda r,b:test_policy(model,r,b);sel=simulate(event_book(te,model,testpol),opt["th"]);mr=metric_rows(sel);m=metrics(mr)
    routes={};fams={};acts={}
    for z in sel:
        routes[z["key"]]=routes.get(z["key"],0)+1;f=z["row"]["family"];a=z["row"]["action"];fams[f]=fams.get(f,0)+1;acts[a]=acts.get(a,0)+1
    ps=gate(m);allpass=allpass and ps
    summary["folds"][test]={**m,"pass":ps,"training_windows":tw,"entry_threshold":opt["th"],"entry_quantile":opt["q"],"training_objective":opt["obj"],
      "training_year_metrics":dict(zip(tw,opt["ym"])),"selected_route_counts":routes,"selected_family_counts":fams,"selected_action_counts":acts,
      "m05_threshold":model["t05"],"m10_threshold":model["t10"],"runtime_seconds":round(time.perf_counter()-ft,3)}
    models["folds"][test]=model
    print("[V74-FITTED-Q]",test,json.dumps({k:summary["folds"][test][k] for k in ("n","mean_r","pf_r","win_rate","average_rr","lcb_r","pass")}),flush=True)
alpha=bool(allpass);champ="EXACT_EVENT_FITTED_Q_OPTIMAL_STOPPING" if alpha else None
summary["evaluator_runtime_seconds"]=round(time.perf_counter()-t0,3);summary["alpha_gate"]=alpha;summary["alpha_champion"]=champ
summary["execution_semantics_ready"]=False;summary["v74_gate"]=False;summary["champion"]=None
summary["promotion_blocker"]="SEQUENTIAL_RUNTIME_POLICY_NOT_FROZEN" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["positive_asset"]="EXACT_EVENT_CAUSAL_ALPHA_OOF" if alpha else "NO_MODEL_EARNED_VERSION_PROMOTION"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2));(out/"V74_MODELS.json").write_text(json.dumps(models,indent=2))
(out/"alpha_pass.txt").write_text("true" if alpha else "false");(out/"alpha_champion.txt").write_text(champ or "NONE")
(out/"pass.txt").write_text("false");(out/"champion.txt").write_text("NONE")
print(json.dumps({"alpha_gate":alpha,"alpha_champion":champ,"v74_gate":False,"promotion_blocker":summary["promotion_blocker"],"evaluator_runtime_seconds":summary["evaluator_runtime_seconds"]},indent=2))
