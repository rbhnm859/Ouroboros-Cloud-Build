#!/usr/bin/env python3
import json,pathlib,sys,math,collections,hashlib

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
W=["Y2021","Y2022","Y2023"]
EDGE_F=["atr","atp","adx1"]
PATH_F=["rr","atr","atp","adx1"]
SLOT_F=["rr","atr","atp","adx1","ses"]
HAZARD_F=["ses","atr","atp","adx1"]
RUNNER_F=["rr","atr","atp","adx1"]
SUPPORT_F=["rr","atr","atp","adx1","ses"]
FRONTIERS=[200,150,100,60]
Z=1.645
MIN_N=60
MIN_PF=1.10
PAIR_SHRINK=25.0
FAMILY_SHRINK=40.0
ARCH_SHRINK=60.0
CORE_OPPORTUNITY_COST_R=0.10
RUNNER_GATE=0.50
CAPITAL_EXCLUDED_FAMILIES={"ABCD"}

rows=[]; coverage={}; oracle_coverage={}; reject_coverage={}
for w in W:
    xs=list(root.rglob(f"SHADOW_PREPASS-{w}.json"))
    if len(xs)!=1: raise SystemExit(f"missing shadow {w}: {len(xs)}")
    doc=json.load(open(xs[0]))
    coverage[w]=doc.get("family_census",{})
    oracle_coverage[w]=doc.get("oracle_census",{})
    reject_coverage[w]=doc.get("reject_attribution",{})
    seen=set()
    for r in doc.get("shadow_outcomes",[]):
        k=(r["setup"],r["family"],r["route"])
        if k in seen: continue
        seen.add(k)
        q=dict(r); q["window"]=w
        q["cost_r"]=max(0.0,float(q.get("cost_r",0.0) or 0.0))
        rows.append(q)

if len(rows)<60: raise SystemExit(f"insufficient rows {len(rows)}")
raw_rows=list(rows)
hazard_rows=[r for r in rows if r["family"] not in CAPITAL_EXCLUDED_FAMILIES and int(r.get("path_state",0))!=-2]
rows=[r for r in rows if r.get("capital_eligible",False) and r["family"] not in CAPITAL_EXCLUDED_FAMILIES and int(r.get("path_state",0))!=-2]
if len(rows)<60: raise SystemExit(f"insufficient capital-eligible structural rows {len(rows)}")

def mean(v): return sum(v)/len(v) if v else 0.0
def sd(v):
    if len(v)<2:return 0.0
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))
def pct(v,q):
    z=sorted(v)
    if not z:return 0.0
    p=(len(z)-1)*q; a=int(math.floor(p)); b=int(math.ceil(p))
    return z[a] if a==b else z[a]*(b-p)+z[b]*(p-a)
def pf(v):
    gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
    return gp/gl if gl else (999.0 if gp else 0.0)
def lcb(v):
    return mean(v)-Z*sd(v)/math.sqrt(len(v)) if len(v)>1 else -999.0
def clamp(x,a,b): return max(a,min(b,x))
def wilson_lcb(k,n,z=Z):
    if n<=0:return 0.0
    p=k/n; d=1.0+z*z/n
    center=p+z*z/(2*n)
    radius=z*math.sqrt(max(0.0,p*(1-p)/n+z*z/(4*n*n)))
    return max(0.0,(center-radius)/d)

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

def ridge(data,target,features,lam):
    if not data:
        return 0.0,[0.0]*len(features),{k:0.0 for k in features},{k:1.0 for k in features},0.0
    mu={k:mean([float(r.get(k,0.0)) for r in data]) for k in features}
    ss={k:max(1e-6,sd([float(r.get(k,0.0)) for r in data])) for k in features}
    ym=mean([float(r[target]) for r in data]); p=len(features)
    xx=[[0.0]*p for _ in range(p)]; xy=[0.0]*p
    for r in data:
        x=[(float(r.get(k,0.0))-mu[k])/ss[k] for k in features]; y=float(r[target])-ym
        for i in range(p):
            xy[i]+=x[i]*y
            for j in range(p):xx[i][j]+=x[i]*x[j]
    for i in range(p):xx[i][i]+=lam
    bz=solve(xx,xy)
    beta=[bz[i]/ss[k] for i,k in enumerate(features)]
    intercept=ym-sum(beta[i]*mu[k] for i,k in enumerate(features))
    pred=[intercept+sum(beta[i]*float(r.get(k,0.0)) for i,k in enumerate(features)) for r in data]
    resid=[float(r[target])-pred[i] for i,r in enumerate(data)]
    return intercept,beta,mu,ss,sd(resid)

def route_key(x):
    return "T" if x=="TREND_ALIGNED_REVERSAL" else "E" if x=="EXHAUSTION_REVERSAL" else "X"

def archetype(f):
    if f in {"AltBat","Butterfly","Crab","DeepCrab"}: return "EXTENSION"
    if f in {"Gartley","Bat","DeepGartley","Rat"}: return "RETRACEMENT"
    if f in {"Cypher","Shark","FiveZero"}: return "SPECIAL"
    return "OTHER"

def hierarchical_priors(data,target):
    vals=[float(r[target]) for r in data]; gm=mean(vals)
    arch=collections.defaultdict(list); fam=collections.defaultdict(list); pair=collections.defaultdict(list)
    for r in data:
        v=float(r[target]); a=archetype(r["family"])
        arch[a].append(v); fam[r["family"]].append(v); pair[(r["family"],r["route"])].append(v)
    ap={a:(sum(v)+ARCH_SHRINK*gm)/(len(v)+ARCH_SHRINK) for a,v in arch.items()}
    fp={}
    for f,v in fam.items():
        base=ap.get(archetype(f),gm)
        fp[f]=(sum(v)+FAMILY_SHRINK*base)/(len(v)+FAMILY_SHRINK)
    pp={}
    nn={}
    for k,v in pair.items():
        base=fp.get(k[0],gm)
        posterior=(sum(v)+PAIR_SHRINK*base)/(len(v)+PAIR_SHRINK)
        pp[k]=posterior-gm
        nn[k]=len(v)
    return gm,ap,fp,pp,nn

def support_model(data):
    c={k:mean([float(r.get(k,0.0)) for r in data]) for k in SUPPORT_F}
    s={k:max(.05,sd([float(r.get(k,0.0)) for r in data])) for k in SUPPORT_F}
    d=[math.sqrt(sum(((float(r.get(k,0.0))-c[k])/s[k])**2 for k in SUPPORT_F)/len(SUPPORT_F)) for r in data]
    return c,s,max(.50,pct(d,.90))

def distance(r,m):
    return math.sqrt(sum(((float(r.get(k,0.0))-m["support_c"][k])/m["support_s"][k])**2 for k in SUPPORT_F)/len(SUPPORT_F))

def pair_key_token(f,route): return f"{f}_{route_key(route)}"

def fit(data, hazard_data=None):
    edge_i,edge_b,_,_,edge_resid=ridge(data,"outcome_r",EDGE_F,12.0)
    resolved=[]
    for r in data:
        q=dict(r); q["p2_target"]=1.0 if int(r.get("path_state",0))==1 else 0.0
        q["runner_target"]=1.0 if int(r.get("path_state",0))==1 and float(r.get("mfe",0.0))>=3.0 else 0.0
        resolved.append(q)
    p2_i,p2_b,_,_,p2_resid=ridge(resolved,"p2_target",PATH_F,16.0)
    runner_i,runner_b,_,_,runner_resid=ridge(resolved,"runner_target",RUNNER_F,18.0)
    slot=[]
    for r in data:
        q=dict(r); q["slot_log"]=math.log(max(.5,min(12.0,float(r.get("bars",60))/60.0))); slot.append(q)
    slot_i,slot_b,_,_,slot_resid=ridge(slot,"slot_log",SLOT_F,16.0)
    hz=[]
    for r in (hazard_data if hazard_data is not None else data):
        q=dict(r); q["hazard_target"]=1.0 if r.get("core_overlap",False) else 0.0; hz.append(q)
    haz_i,haz_b,_,_,haz_resid=ridge(hz,"hazard_target",HAZARD_F,18.0)
    egm,eap,efp,epri,enn=hierarchical_priors(data,"outcome_r")
    pgm,pap,pfp,ppri,pnn=hierarchical_priors(resolved,"p2_target")
    rgm,rap,rfp,rpri,rnn=hierarchical_priors(resolved,"runner_target")
    c,s,sref=support_model(data)
    base_edge=max(.015,Z*max(.05,edge_resid)/math.sqrt(max(MIN_N,len(data))))
    base_p2=max(.015,Z*max(.05,p2_resid)/math.sqrt(max(MIN_N,len(data))))
    base_runner=max(.02,Z*max(.05,runner_resid)/math.sqrt(max(MIN_N,len(data))))
    soft_edge=max(.01,.08*max(.05,edge_resid))
    soft_prob=max(.01,.06*max(.05,p2_resid))
    pair_edge={k:Z*max(.05,edge_resid)/math.sqrt(max(1.0,enn.get(k,0)+PAIR_SHRINK)) for k in epri}
    pair_p2={k:Z*max(.05,p2_resid)/math.sqrt(max(1.0,pnn.get(k,0)+PAIR_SHRINK)) for k in ppri}
    pair_runner={k:Z*max(.05,runner_resid)/math.sqrt(max(1.0,rnn.get(k,0)+PAIR_SHRINK)) for k in rpri}
    return {
        "edge_i":edge_i,"edge_b":edge_b,"edge_resid":edge_resid,
        "p2_i":p2_i,"p2_b":p2_b,"p2_resid":p2_resid,
        "runner_i":runner_i,"runner_b":runner_b,"runner_resid":runner_resid,
        "slot_i":slot_i,"slot_b":slot_b,"slot_margin":Z*max(.05,slot_resid),
        "haz_i":haz_i,"haz_b":haz_b,"haz_margin":Z*max(.02,haz_resid),
        "edge_pri":epri,"p2_pri":ppri,"runner_pri":rpri,
        "pair_edge_unc":pair_edge,"pair_p2_unc":pair_p2,"pair_runner_unc":pair_runner,
        "support_c":c,"support_s":s,"support_ref":sref,
        "base_edge_margin":base_edge,"base_p2_margin":base_p2,"base_runner_margin":base_runner,
        "soft_edge":soft_edge,"soft_prob":soft_prob
    }

def linear(r,i,b,features): return i+sum(b[j]*float(r.get(k,0.0)) for j,k in enumerate(features))

def scored(r,m):
    pair=(r["family"],r["route"])
    dist=distance(r,m)
    extra=max(0.0,dist-m["support_ref"])
    edge=linear(r,m["edge_i"],m["edge_b"],EDGE_F)+m["edge_pri"].get(pair,0.0)
    edge_lcb=edge-m["base_edge_margin"]-m["pair_edge_unc"].get(pair,m["base_edge_margin"])-m["soft_edge"]*extra
    p2=clamp(linear(r,m["p2_i"],m["p2_b"],PATH_F)+m["p2_pri"].get(pair,0.0),.01,.99)
    p2_lcb=clamp(p2-m["base_p2_margin"]-m["pair_p2_unc"].get(pair,m["base_p2_margin"])-m["soft_prob"]*extra,0.0,.99)
    runner=clamp(linear(r,m["runner_i"],m["runner_b"],RUNNER_F)+m["runner_pri"].get(pair,0.0),.01,.99)
    runner_lcb=clamp(runner-m["base_runner_margin"]-m["pair_runner_unc"].get(pair,m["base_runner_margin"])-m["soft_prob"]*extra,0.0,.99)
    lh=linear(r,m["slot_i"],m["slot_b"],SLOT_F)
    hours=max(.5,min(12.0,math.exp(max(-2.0,min(3.0,lh)))))
    hours_ucb=max(.5,min(12.0,hours*math.exp(min(1.5,m["slot_margin"]))))
    hazard=clamp(linear(r,m["haz_i"],m["haz_b"],HAZARD_F)+m["haz_margin"],.0,.95)
    be=clamp((1.0+max(0.0,float(r.get("cost_r",0.0))))/3.0,.333333,.60)
    score=edge_lcb/hours_ucb-hazard*CORE_OPPORTUNITY_COST_R
    gates=edge_lcb>0 and p2_lcb>be and pair in m["edge_pri"]
    return {"edge":edge,"edge_lcb":edge_lcb,"p2":p2,"p2_lcb":p2_lcb,"runner":runner,"runner_lcb":runner_lcb,
            "hours":hours,"hours_ucb":hours_ucb,"hazard":hazard,"be":be,"score":score,"distance":dist,"gates":gates}

def empirical_diag(selected, frontier=None, threshold=None):
    v=[float(r["outcome_r"]) for r,_ in selected]
    succ=sum(1 for r,_ in selected if int(r.get("path_state",0))==1)
    n=len(selected)
    path_lcb=wilson_lcb(succ,n)
    be=mean([s["be"] for _,s in selected]) if selected else 1.0
    return {"selected_n":n,"selected_mean_r":mean(v),"selected_pf_r":pf(v),"selected_lcb_r":lcb(v),
            "two_r_before_stop_rate":succ/n if n else 0.0,"two_r_before_stop_lcb":path_lcb,
            "cost_adjusted_break_even_p2":be,"frontier":frontier,"score_threshold":threshold,
            "pass":n>=MIN_N and mean(v)>0 and pf(v)>=MIN_PF and lcb(v)>0 and path_lcb>be}

def threshold_for_frontier(scored_rows,frontier):
    eligible=sorted((s["score"] for r,s in scored_rows if s["gates"]),reverse=True)
    if len(eligible)<frontier:return None
    return eligible[frontier-1]

def inner_frontier_check(train_windows,frontier):
    details=[]
    a,b=train_windows
    for source,target in [(a,b),(b,a)]:
        src=[r for r in rows if r["window"]==source]
        tgt=[r for r in rows if r["window"]==target]
        hz=[r for r in hazard_rows if r["window"]==source]
        m=fit(src,hz)
        srcsc=[(r,scored(r,m)) for r in src]
        th=threshold_for_frontier(srcsc,frontier)
        if th is None:
            details.append({"source":source,"target":target,"threshold":None,"pass":False,"reason":"INSUFFICIENT_GATED_SOURCE"})
            continue
        tgtsc=[(r,scored(r,m)) for r in tgt]
        sel=[x for x in tgtsc if x[1]["gates"] and x[1]["score"]>=th]
        d=empirical_diag(sel,frontier,th); d.update({"source":source,"target":target})
        details.append(d)
    return {"frontier":frontier,"directions":details,"pass":len(details)==2 and all(x.get("pass",False) for x in details)}

def model_threshold(data,m,frontier):
    thresholds=[]
    for w in sorted(set(r["window"] for r in data)):
        sc=[(r,scored(r,m)) for r in data if r["window"]==w]
        th=threshold_for_frontier(sc,frontier)
        if th is None:return None
        thresholds.append(th)
    return max(thresholds) if thresholds else None

def fnv32(s):
    h=2166136261
    for ch in s:
        code=ord(ch)
        h ^= code & 0xff; h=(h*16777619)&0xffffffff
        if code>0xff:
            h ^= (code>>8)&0xff; h=(h*16777619)&0xffffffff
    return h

def setup_hash_spec(selected):
    vals=sorted({f"{fnv32(r['family']+'|'+r['setup']):08X}" for r,s in selected})
    return ";".join(vals)

def pair_spec(m): return ";".join(sorted(f"{f}:{route_key(rt)}" for (f,rt) in m["edge_pri"]))

def prior_spec(m): return ";".join(f"{f}:{route_key(rt)}:{clamp(v,-2,2):.10f}" for (f,rt),v in sorted(m["edge_pri"].items()))

def model_spec(m):
    a=["h5:1.0000000000","slot_gate:1.0000000000","soft_support:1.0000000000",
       f"i:{m['edge_i']:.10f}",f"edge_base_margin:{m['base_edge_margin']:.10f}",
       f"support_ref:{m['support_ref']:.10f}",f"uncertainty_scale:{m['soft_edge']:.10f}",
       f"p2i:{m['p2_i']:.10f}",f"p2_base_margin:{m['base_p2_margin']:.10f}",f"p2_uncertainty_scale:{m['soft_prob']:.10f}",
       f"ri:{m['runner_i']:.10f}",f"runner_base_margin:{m['base_runner_margin']:.10f}",f"runner_gate:{RUNNER_GATE:.10f}",
       f"shi:{m['slot_i']:.10f}",f"slot_margin:{m['slot_margin']:.10f}",
       f"chi:{m['haz_i']:.10f}",f"core_hazard_margin:{m['haz_margin']:.10f}",f"core_cost:{CORE_OPPORTUNITY_COST_R:.10f}"]
    for k,b in zip(EDGE_F,m["edge_b"]):a.append(f"{k}:{b:.10f}")
    for k,b in zip(PATH_F,m["p2_b"]):a.append(f"p2_{k}:{b:.10f}")
    for k,b in zip(RUNNER_F,m["runner_b"]):a.append(f"r_{k}:{b:.10f}")
    for k,b in zip(SLOT_F,m["slot_b"]):a.append(f"sh_{k}:{b:.10f}")
    for k,b in zip(HAZARD_F,m["haz_b"]):a.append(f"ch_{k}:{b:.10f}")
    for k in SUPPORT_F:
        a += [f"mc_{k}:{m['support_c'][k]:.10f}",f"ms_{k}:{m['support_s'][k]:.10f}"]
    for pair,v in sorted(m["p2_pri"].items()):
        tok=pair_key_token(*pair); a.append(f"p2pr_{tok}:{v:.10f}")
    for pair,v in sorted(m["runner_pri"].items()):
        tok=pair_key_token(*pair); a.append(f"rpr_{tok}:{v:.10f}")
    for pair,v in sorted(m["pair_edge_unc"].items()):
        tok=pair_key_token(*pair); a.append(f"eu_{tok}:{v:.10f}")
    for pair,v in sorted(m["pair_p2_unc"].items()):
        tok=pair_key_token(*pair); a.append(f"pu_{tok}:{v:.10f}")
    for pair,v in sorted(m["pair_runner_unc"].items()):
        tok=pair_key_token(*pair); a.append(f"ru_{tok}:{v:.10f}")
    return ";".join(a)

folds={}; models={}; frontier_audit={}
for test in W:
    train_windows=[w for w in W if w!=test]
    audits=[inner_frontier_check(train_windows,f) for f in FRONTIERS]
    legal=[z["frontier"] for z in audits if z["pass"]]
    chosen=max(legal) if legal else None
    tr=[r for r in rows if r["window"]!=test]; ho=[r for r in rows if r["window"]==test]
    hz=[r for r in hazard_rows if r["window"]!=test]
    m=fit(tr,hz); models[test]=m
    th=model_threshold(tr,m,chosen) if chosen else None
    sc=[(r,scored(r,m)) for r in ho]
    sel=[x for x in sc if th is not None and x[1]["gates"] and x[1]["score"]>=th]
    d=empirical_diag(sel,chosen,th)
    d.update({"train_n":len(tr),"test_n":len(ho),"chosen_frontier":chosen,
              "hard_context_gate":False,"hard_support_gate":False,
              "support_penalized_not_rejected":True,
              "inner_frontiers":audits,
              "eligible_before_threshold":sum(1 for r,s in sc if s["gates"]),
              "allowed_setup_hash_count":len({fnv32(r["family"]+"|"+r["setup"]) for r,s in sel})})
    if chosen is None:d["pass"]=False
    folds[test]=d; frontier_audit[test]=audits
    json.dump({"model_id":f"V71-H5-POSTERIOR-XFIT-{test}","architecture":"H5_CAUSAL_HIERARCHICAL_POSTERIOR_ALPHA_AUCTION",
               "training_windows":train_windows,"test_window":test,"spec":model_spec(m),
               "family_prior_spec":prior_spec(m),"allowed_pair_spec":pair_spec(m),"allowed_context_spec":"",
               "allowed_setup_hash_spec":setup_hash_spec(sel),"lcb_margin":0.0,
               "selection_lcb_r":th if th is not None else 999.0,"selected_frontier":chosen,
               "diagnostic":d},open(out/f"{test}.json","w"),indent=2)

alpha_crossfit=all(x["pass"] for x in folds.values())
common_frontier=min((x["chosen_frontier"] for x in folds.values() if x["chosen_frontier"] is not None),default=None)
fullm=fit(rows,hazard_rows)
fullth=model_threshold(rows,fullm,common_frontier) if common_frontier else None
full={"model_id":"V71-H5-POSTERIOR-XFIT-FULL","architecture":"H5_CAUSAL_HIERARCHICAL_POSTERIOR_ALPHA_AUCTION",
      "training_windows":W,"spec":model_spec(fullm),"family_prior_spec":prior_spec(fullm),"allowed_pair_spec":pair_spec(fullm),
      "allowed_context_spec":"","allowed_setup_hash_spec":"","lcb_margin":0.0,
      "selection_lcb_r":fullth if fullth is not None else 999.0,"selected_frontier":common_frontier,
      "diagnostic":{"train_n":len(rows),"hard_context_gate":False,"hard_support_gate":False,
                    "support_penalized_not_rejected":True}}
json.dump(full,open(out/"FULL.json","w"),indent=2)

coverage_total=collections.defaultdict(lambda:{"tracked":0,"armed":0,"core_overlap":0,"shadow_closed":0})
for w,d in coverage.items():
    for fam,z in d.items():
        for k in coverage_total[fam]: coverage_total[fam][k]+=int(z.get(k,0))
oracle_total=collections.defaultdict(lambda:{"expected":0,"matched":0,"missed":0})
for w,d in oracle_coverage.items():
    for fam,z in d.items():
        oracle_total[fam]["expected"]+=int(z.get("expected",0))
        oracle_total[fam]["matched"]+=int(z.get("matched",0))
        oracle_total[fam]["missed"]+=int(z.get("missed",0))
for fam,z in oracle_total.items():z["recall"]=z["matched"]/z["expected"] if z["expected"] else 1.0
reject_total=collections.defaultdict(lambda:collections.defaultdict(int))
for w,d in reject_coverage.items():
    for fam,reasons in d.items():
        for reason,count in reasons.items():reject_total[fam][reason]+=int(count)
reject_total={fam:dict(sorted(z.items())) for fam,z in sorted(reject_total.items())}
expected_families={"Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"}
detector_recall_gate=set(oracle_total)==expected_families and sum(z["expected"] for z in oracle_total.values())>0 and all(z["missed"]==0 for z in oracle_total.values())
crossfit=alpha_crossfit and detector_recall_gate

manifest={"architecture":"H5_CAUSAL_HIERARCHICAL_POSTERIOR_ALPHA_AUCTION_PREREGISTERED",
 "rows":len(rows),"raw_rows":len(raw_rows),"capital_rows":len(rows),
 "selected_architecture":"H5","selection_objective":"NESTED_TEMPORAL_60_100_150_200_FRONTIER__DUAL_POSTERIOR_LCB",
 "frontiers":FRONTIERS,"common_frontier":common_frontier,
 "edge_features":EDGE_F,"path_features":PATH_F,"slot_features":SLOT_F,"core_hazard_features":HAZARD_F,
 "min_selected_per_fold":MIN_N,"min_pf_r":MIN_PF,"lcb_z":Z,
 "hard_context_gate":False,"hard_support_gate":False,"partial_pooling":["GLOBAL","STRUCTURAL_ARCHETYPE","FAMILY","FAMILY_ROUTE"],
 "dual_posterior_gate":True,"cost_adjusted_p2_gate":True,"core_opportunity_cost_r":CORE_OPPORTUNITY_COST_R,
 "reaction_exit":"NET_2R_FIXED","selective_runner":"P_MFE_GE_3R_POSTERIOR_LCB_GT_0_50",
 "capital_excluded_families":sorted(CAPITAL_EXCLUDED_FAMILIES),
 "family_census":dict(sorted(coverage_total.items())),"oracle_census":dict(sorted(oracle_total.items())),
 "reject_attribution":reject_total,"detector_recall_gate":detector_recall_gate,"alpha_crossfit_gate":alpha_crossfit,
 "folds":folds,"crossfit_gate":crossfit,
 "worst_fold_lcb_r":min(x["selected_lcb_r"] for x in folds.values()),
 "min_fold_pf_r":min(x["selected_pf_r"] for x in folds.values()),
 "min_fold_p2_lcb":min(x["two_r_before_stop_lcb"] for x in folds.values()),
 "full_model_sha256":hashlib.sha256((out/"FULL.json").read_bytes()).hexdigest()}
json.dump(manifest,open(out/"MODEL_MANIFEST.json","w"),indent=2)
print(json.dumps(manifest,indent=2))
