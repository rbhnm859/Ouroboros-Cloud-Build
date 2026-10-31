#!/usr/bin/env python3
"""V74 causal per-opportunity two-stage action arbitration. Validation/Fresh are never loaded."""
import json,math,pathlib,statistics,sys
from collections import defaultdict
from v74_model_lib import load_rows,metrics
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
RESEARCH=[f"Y{y}" for y in range(2016,2021)];BURNED=["Y2021","Y2022","Y2023"];ALL=RESEARCH+BURNED
MIN_N=250;MIN_MEAN=.90;MIN_PF=3.30;MIN_WR=.70;MIN_RR=2.30;Z=1.645
PRE_IDXS=(0,1,2,6,7,9,25,26,27,28,29,34,35,36,37,38,39)
Q_GRID=(0.0,.05,.10,.15,.20,.25,.30,.35,.40,.45,.50);WIN_GRID=(0.0,.35,.45,.55,.60,.65)
BASES=[f"R{r}_{m}_RR{rr}" for r in ("025","050") for m in ("H","D") for rr in ("35","40")]
rows=load_rows(root,ALL)
if not rows:raise SystemExit("no V74 action-arbitration rows")
def logged_key(base,frac):return "P_"+base+"_F"+frac
def level_of(base):return "025" if base.startswith("R025") else "050"
def synth_actions(r,base):
    k20=logged_key(base,"20");k30=logged_key(base,"30");y20=r.get("sequential",{}).get(k20);y30=r.get("sequential",{}).get(k30);rr=r.get("sequential_rr",{}).get(k20)
    if y20 is None or y30 is None or rr is None:return []
    d=float(y30)-float(y20);vals={"F00":float(y20)-2*d,"F10":float(y20)-d,"F20":float(y20),"F30":float(y30)}
    entry=r.get("sequential_entry_state",{}).get(k20);trigger=r.get("sequential_trigger_state",{}).get(k20);decision=r.get("sequential_decision_state",{}).get(k20)
    bars=r.get("sequential_bars",{}).get(k20,r.get("bars",180));m=r.get("sequential_state",{}).get(level_of(base))
    if m is None or entry is None:return []
    return [{"window":r["window"],"setup":r["setup"],"family":r["family"],"direction_action":r["action"],"base":base,"fraction":f,
             "r":v,"rr":float(rr),"bars":max(1,int(bars)),"features":r.get("features",[]),"milestone":list(m),"entry":list(entry),
             "trigger":None if trigger is None else list(trigger),"decision":None if decision is None else list(decision)} for f,v in vals.items()]
def action_rows(xs):
    z=[]
    for r in xs:
        for b in BASES:z.extend(synth_actions(r,b))
    return z
def vec_entry(z):
    f=z["features"];return [f[i] if i<len(f) else 0.0 for i in PRE_IDXS]+z["milestone"]+z["entry"]
def vec_decision(z):
    if z["decision"] is None:return None
    f=z["features"];return [f[i] if i<len(f) else 0.0 for i in PRE_IDXS]+z["milestone"]+z["entry"]+(z["trigger"] or [0.0]*12)+z["decision"]
def sstat(xs):
    if not xs:return {"n":0,"mean":0.0,"win":0.0,"sigma":10.0,"hold":180.0}
    v=[x["r"] for x in xs];n=len(v);sd=statistics.stdev(v) if n>1 else 10.0
    return {"n":n,"mean":sum(v)/n,"win":sum(a>0 for a in v)/n,"sigma":max(.05,sd),"hold":float(statistics.median(max(1,x["bars"]) for x in xs))}
def train_value(xs,vecfn):
    pairs=[(x,vecfn(x)) for x in xs];pairs=[p for p in pairs if p[1] is not None]
    if len(pairs)<80:return {"medians":[],"global":sstat([]),"famact":{},"bins":[]}
    q=[p[0] for p in pairs];vv=[p[1] for p in pairs];p=len(vv[0]);med=[statistics.median(v[j] for v in vv) for j in range(p)];g=sstat(q);fa={}
    for key in sorted({x["family"]+"|"+x["direction_action"] for x in q}):fa[key]=sstat([x for x in q if x["family"]+"|"+x["direction_action"]==key])
    bins=[]
    for j in range(p):bins.append({"lo":sstat([x for x,v in pairs if v[j]<med[j]]),"hi":sstat([x for x,v in pairs if v[j]>=med[j]])})
    return {"medians":med,"global":g,"famact":fa,"bins":bins}
def predict_value(m,z,vecfn):
    v=vecfn(z);g=m.get("global",{})
    if v is None or not m.get("medians") or int(g.get("n",0))<80:return {"mean":0.0,"win":0.0,"lcb":-999.0,"hold":180.0,"support":0,"utility":-999.0}
    gm=g["mean"];gw=g["win"];gs=g["sigma"];gh=g["hold"];fa=m["famact"].get(z["family"]+"|"+z["direction_action"],g)
    wf=fa["n"]/(fa["n"]+80.0);pm=gm+wf*(fa["mean"]-gm);pw=gw+wf*(fa["win"]-gw);ph=gh+wf*(fa["hold"]-gh);ms=[];ws=[];hs=[];supp=[]
    for j,x in enumerate(v):
        b=m["bins"][j]["hi" if x>=m["medians"][j] else "lo"];n=b["n"];sh=n/(n+60.0);ms.append(pm+sh*(b["mean"]-gm));ws.append(pw+sh*(b["win"]-gw));hs.append(ph+sh*(b["hold"]-gh));supp.append(n)
    mean=(pm+sum(ms)/len(ms))/2;win=max(0,min(1,(pw+sum(ws)/len(ws))/2));hold=max(1,(ph+sum(hs)/len(hs))/2);support=max(1,min([fa["n"] if fa["n"] else g["n"]]+supp))
    lcb=mean-Z*max(.05,(gs+fa["sigma"])/2)/math.sqrt(support);return {"mean":mean,"win":win,"lcb":lcb,"hold":hold,"support":support,"utility":lcb/max(.25,hold/60)}
def train_fraction_models(ar):return {b+"|"+f:train_value([x for x in ar if x["base"]==b and x["fraction"]==f and x["decision"] is not None],vec_decision) for b in BASES for f in ("F00","F10","F20","F30")}
def choose_fraction_actions(ar,models):
    by=defaultdict(list)
    for x in ar:by[(x["window"],x["setup"],x["base"])].append(x)
    out=[]
    for _,lst in by.items():
        dec=[x for x in lst if x["decision"] is not None]
        if not dec:
            q=dict(next((x for x in lst if x["fraction"]=="F00"),lst[0]));q["fraction_pred"]={"utility":0.0};out.append(q);continue
        sc=[]
        for x in dec:q=dict(x);q["fraction_pred"]=predict_value(models.get(x["base"]+"|"+x["fraction"],{}),x,vec_decision);sc.append(q)
        out.append(max(sc,key=lambda x:(x["fraction_pred"]["utility"],x["fraction_pred"].get("mean",0),x["fraction"])))
    return out
def train_base_models(xs):return {b:train_value([x for x in xs if x["base"]==b],vec_entry) for b in BASES}
def choose_base(xs,models):
    by=defaultdict(list)
    for x in xs:by[(x["window"],x["setup"])].append(x)
    out=[]
    for _,lst in by.items():
        sc=[]
        for x in lst:q=dict(x);q["base_pred"]=predict_value(models.get(x["base"],{}),x,vec_entry);sc.append(q)
        if sc:out.append(max(sc,key=lambda x:(x["base_pred"]["utility"],x["base_pred"]["mean"],x["base_pred"]["win"],x["rr"])))
    return out
def gate(m):return m["n"]>=MIN_N and m["mean_r"]>=MIN_MEAN and m["pf_r"]>=MIN_PF and m["win_rate"]>=MIN_WR and m["average_rr"]>=MIN_RR and m["lcb_r"]>0
def gm(m):return -999 if not m["n"] else min(m["n"]/MIN_N,m["mean_r"]/MIN_MEAN,m["pf_r"]/MIN_PF,m["win_rate"]/MIN_WR,m["average_rr"]/MIN_RR,1+m["lcb_r"]/.25)
def quantile(v,q):
    if not v:return math.inf
    x=sorted(v);p=(len(x)-1)*q;a=int(math.floor(p));b=int(math.ceil(p));return x[a] if a==b else x[a]*(b-p)+x[b]*(p-a)
def choose_threshold(cf,windows):
    vals=[x["base_pred"]["utility"] for x in cf if x["base_pred"]["utility"]>-900];cand=[]
    for q in Q_GRID:
        th=quantile(vals,q)
        for wf in WIN_GRID:
            sel=[x for x in cf if x["base_pred"]["utility"]>=th and x["base_pred"]["win"]>=wf];ym=[];ok=True
            for w in windows:
                m=metrics([x for x in sel if x["window"]==w])
                if m["n"]<MIN_N:ok=False;break
                ym.append(m)
            if ok:
                margins=[gm(m) for m in ym];minn=min(m["n"] for m in ym);cand.append((min(margins)+.25*statistics.median(margins)+.15*min(1,minn/325),q,wf,th,minn))
    cand.sort(reverse=True);return cand[0] if cand else None
def oracle(xs,windows):
    by=defaultdict(list)
    for x in action_rows(xs):by[(x["window"],x["setup"])].append(x["r"])
    per={}
    for w in windows:
        best=sorted([max(v) for (ww,_),v in by.items() if ww==w],reverse=True);m=metrics([{"r":v,"bars":1} for v in best[:MIN_N]])
        per[w]={"available":len(best),"top250":m,"hard_gate":gate(m)}
    bw=[w for w in windows if w in BURNED];return {"pass":all(per[w]["available"]>=300 and per[w]["hard_gate"] for w in bw),"per_window":per,"scope":"BURNED_TRAIN_LABEL_FORENSIC_ONLY"}

summary={"version":"HarmonyBot V74 Candidate","architecture":"CAUSAL_PER_OPPORTUNITY_TWO_STAGE_ACTION_ARBITRATION","research_training_windows":RESEARCH,"burned_oof_windows":BURNED,
"gate":{"min_selected_per_year":MIN_N,"min_mean_r":MIN_MEAN,"min_pf_r":MIN_PF,"min_win_rate":MIN_WR,"min_average_rr":MIN_RR,"lcb95_gt":0.0},
"governance":{"base_route_choice_time":"COMPLETED_ENTRY_STATE_ONLY","fraction_choice_time":"POST_ENTRY_0P25R_THEN_LATER_COMPLETED_0P10R_HOLD","nested_temporal_crossfit":True,
"test_year_outcomes_never_select_route_fraction_threshold":True,"route_utility":"LCB_EXPECTED_NET_R_PER_EXPECTED_SLOT_HOUR","frequency_buffer_target":"300_TO_350_NOT_TEST_GATE",
"validation_used":False,"fresh_used":False,"execution_semantics_ready":False},"folds":{},"validation_used":False,"fresh_used":False}
mb={"architecture":"V74_TWO_STAGE_ACTION_ARBITRATION","folds":{}};passes=[]
for test in BURNED:
    tw=RESEARCH+[w for w in BURNED if w!=test];tr=[r for r in rows if r["window"] in tw];te=[r for r in rows if r["window"]==test];feas=oracle(tr,tw)
    cf=[]
    for w in tw:
        fm=train_fraction_models(action_rows([r for r in tr if r["window"]!=w]));cf.extend(choose_fraction_actions(action_rows([r for r in tr if r["window"]==w]),fm))
    cfb=[]
    for w in tw:
        bm=train_base_models([x for x in cf if x["window"]!=w]);cfb.extend(choose_base([x for x in cf if x["window"]==w],bm))
    pol=choose_threshold(cfb,tw);ff=train_fraction_models(action_rows(tr));tb=choose_fraction_actions(action_rows(te),ff);fb=train_base_models(cf);tc=choose_base(tb,fb)
    if pol is None:sel=[];q=wf=th=None
    else:_,q,wf,th,_=pol;sel=[x for x in tc if x["base_pred"]["utility"]>=th and x["base_pred"]["win"]>=wf]
    m=metrics(sel);p=gate(m);passes.append(p);m.update({"pass":p,"training_windows":tw,"selection_quantile":q,"predicted_win_floor":wf,"selection_threshold":th,"feasibility_pre_gate":feas,
      "selected_base_routes":{b:sum(x["base"]==b for x in sel) for b in BASES},"selected_fraction_actions":{f:sum(x["fraction"]==f for x in sel) for f in ("F00","F10","F20","F30")},
      "median_planned_route_rr":statistics.median([x["rr"] for x in sel]) if sel else 0.0})
    summary["folds"][test]=m;mb["folds"][test]={"fraction_models":ff,"base_models":fb,"selection_quantile":q,"predicted_win_floor":wf,"selection_threshold":th,"feasibility_pre_gate":feas}
alpha=all(passes);champ="AK_CAUSAL_PER_OPPORTUNITY_ACTION_ARBITRATION" if alpha else None
summary["alpha_gate"]=alpha;summary["v74_gate"]=False;summary["champion"]=champ;summary["promotion_blocker"]="EXECUTION_SEMANTICS_NOT_YET_FROZEN_IN_V75_RUNTIME" if alpha else "ALPHA_OOF_GATE_FAIL"
summary["gate_semantics"]="UNCHANGED_N250_MEAN0P90_PF3P30_WR70_RR2P30_LCBPOS__NESTED_TEMPORAL_OOF__NO_LOOKAHEAD"
(out/"V74_TOURNAMENT_MANIFEST.json").write_text(json.dumps(summary,indent=2));(out/"V74_MODELS.json").write_text(json.dumps(mb,separators=(",",":")))
(out/"champion.txt").write_text(champ or "");(out/"alpha_pass.txt").write_text("true" if alpha else "false");(out/"pass.txt").write_text("false");print(json.dumps(summary,indent=2))
