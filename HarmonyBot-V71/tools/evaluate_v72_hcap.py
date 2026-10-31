#!/usr/bin/env python3
import json, math, pathlib, re, statistics, sys

root=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
WINDOWS=["Y2021","Y2022","Y2023"]
FAMILIES=["Gartley","Bat","AltBat","Butterfly","Crab","DeepCrab","DeepGartley","Rat","Cypher","Shark","FiveZero","ABCD"]
FEATURES=["geometry","prz","confidence","time_symmetry","pivot_quality","net_rr_scaled",
          "efficiency","atr_fit","extension_scaled","trend_strength","adx_slope_norm","mtf_score"]
Z=1.645
MIN_SELECTED=60
GLOBAL_RIDGE=8.0
FAMILY_RIDGE=24.0
INTERCEPT_RIDGE=.01

rx=re.compile(
 r"\[V72-HCOG-OUTCOME\]\s+id=(\S+)\s+setup=(\S+)\s+family=(\S+)\s+lane=(\S+)\s+"
 r"abcd=(True|False)\s+coreOverlap=(True|False)\s+r=([-0-9.]+)\s+mfeR=([-0-9.]+)\s+"
 r"maeR=([-0-9.]+)\s+bars=(\d+)\s+result=(\S+)\s+hcapSelected=(True|False)\s+"
 r"q=([-0-9.]+)\s+lcb=([-0-9.]+)\s+hold=([-0-9.]+)\s+features=(\S+)"
)

def window_of(path):
    s=str(path)
    for w in WINDOWS:
        if w in s:return w
    return None

rows=[]
for p in root.rglob("*.log"):
    w=window_of(p)
    if not w: continue
    txt=p.read_text(errors="ignore")
    for m in rx.finditer(txt):
        lane=m.group(4)
        if lane not in ("HCOG_REVERSAL","HCOG_FAILURE_CONTINUATION"): continue
        feats=[float(x) for x in m.group(16).split(",")]
        if len(feats)!=len(FEATURES): raise SystemExit(f"bad HCAP feature count {len(feats)} in {p}")
        rows.append({"window":w,"id":m.group(1),"setup":m.group(2),"family":m.group(3),"lane":lane,
                     "action":"REVERSAL" if lane=="HCOG_REVERSAL" else "CONTINUATION",
                     "abcd":m.group(5)=="True","core_overlap":m.group(6)=="True",
                     "r":float(m.group(7)),"mfe":float(m.group(8)),"mae":float(m.group(9)),
                     "bars":int(m.group(10)),"result":m.group(11),"features":feats})
if not rows: raise SystemExit("no HCAP action outcome rows")

def solve(A,b):
    n=len(b); M=[list(A[i])+[b[i]] for i in range(n)]
    for c in range(n):
        pivot=max(range(c,n),key=lambda r:abs(M[r][c]))
        if abs(M[pivot][c])<1e-12: raise SystemExit("singular HCAP normal equation")
        M[c],M[pivot]=M[pivot],M[c]
        v=M[c][c]
        for j in range(c,n+1): M[c][j]/=v
        for r in range(n):
            if r==c: continue
            q=M[r][c]
            if q==0: continue
            for j in range(c,n+1): M[r][j]-=q*M[c][j]
    return [M[i][n] for i in range(n)]

def stats(v):
    n=len(v); gp=sum(x for x in v if x>0); gl=-sum(x for x in v if x<0)
    mean=sum(v)/n if n else 0.0
    pf=gp/gl if gl else (999.0 if gp else 0.0)
    wr=sum(x>0 for x in v)/n if n else 0.0
    if n>1:
        var=sum((x-mean)**2 for x in v)/(n-1)
        lcb=mean-Z*math.sqrt(max(0,var)/n)
    else:lcb=-999.0
    return {"n":n,"mean_r":mean,"pf_r":pf,"lcb_r":lcb,"win_rate":wr,
            "gross_profit_r":gp,"gross_loss_r":gl}

def train(action, train_rows):
    rr=[r for r in train_rows if r["action"]==action]
    p=1+len(FEATURES)+len(FAMILIES)
    if len(rr)<max(20,p): raise SystemExit(f"insufficient HCAP training rows for {action}: {len(rr)}")
    means=[]; scales=[]
    for j in range(len(FEATURES)):
        col=[r["features"][j] for r in rr]
        mu=sum(col)/len(col)
        sd=statistics.stdev(col) if len(col)>1 else 1.0
        if not math.isfinite(sd) or sd<1e-9: sd=1.0
        means.append(mu); scales.append(sd)
    def vec(r):
        x=[1.0]+[(r["features"][j]-means[j])/scales[j] for j in range(len(FEATURES))]
        x += [1.0 if r["family"]==f else 0.0 for f in FAMILIES]
        return x
    X=[vec(r) for r in rr]; y=[r["r"] for r in rr]
    A=[[0.0]*p for _ in range(p)]; b=[0.0]*p
    for x,t in zip(X,y):
        for i in range(p):
            b[i]+=x[i]*t
            for j in range(p): A[i][j]+=x[i]*x[j]
    for i in range(p):
        A[i][i]+=INTERCEPT_RIDGE if i==0 else (GLOBAL_RIDGE if i<=len(FEATURES) else FAMILY_RIDGE)
    beta=solve(A,b)
    residual=[t-sum(beta[i]*x[i] for i in range(p)) for x,t in zip(X,y)]
    sigma=math.sqrt(sum(e*e for e in residual)/max(1,len(residual)-1))
    hold=statistics.median([max(1,r["bars"]) for r in rr])
    info=[max(1e-9,A[i][i]) for i in range(p)]
    model={"n":len(rr),"sigma":max(1e-9,sigma),"hold_bars":float(hold),
           "mean":means,"scale":scales,"beta":beta,"info_diag":info}
    model["string"]=",".join(format(x,".17g") for x in
        [model["n"],model["sigma"],model["hold_bars"]]+means+scales+beta+info)
    return model

def predict(model,r):
    x=[1.0]+[(r["features"][j]-model["mean"][j])/model["scale"][j] for j in range(len(FEATURES))]
    x += [1.0 if r["family"]==f else 0.0 for f in FAMILIES]
    q=sum(model["beta"][i]*x[i] for i in range(len(x)))
    vf=sum(x[i]*x[i]/model["info_diag"][i] for i in range(len(x)))
    se=model["sigma"]*math.sqrt(max(0.0,vf))
    lcb=q-Z*se
    return q,lcb

folds={}
selected_all=[]
for test in WINDOWS:
    train_rows=[r for r in rows if r["window"]!=test]
    models={a:train(a,train_rows) for a in ("REVERSAL","CONTINUATION")}
    candidates=[]
    for r in [z for z in rows if z["window"]==test]:
        q,lcb=predict(models[r["action"]],r)
        z=dict(r); z["q"]=q; z["lcb"]=lcb
        if q>0 and lcb>0: candidates.append(z)
    # One geometry/setup may only consume one action. Choose the most conservative action value.
    best={}
    for r in candidates:
        k=r["setup"]
        if k not in best or (r["lcb"],r["q"])>(best[k]["lcb"],best[k]["q"]): best[k]=r
    selected=list(best.values())
    s=stats([r["r"] for r in selected])
    s["frequency_per_year"]=s["n"]
    s["action_stats"]={a:stats([r["r"] for r in selected if r["action"]==a]) for a in ("REVERSAL","CONTINUATION")}
    s["training_windows"]=[w for w in WINDOWS if w!=test]
    s["reversal_model"]=models["REVERSAL"]["string"]
    s["continuation_model"]=models["CONTINUATION"]["string"]
    s["pass"]=bool(s["n"]>=MIN_SELECTED and s["mean_r"]>0 and s["pf_r"]>1.0 and s["lcb_r"]>0)
    folds[test]=s
    selected_all += selected

final_models={a:train(a,rows) for a in ("REVERSAL","CONTINUATION")}
hcap_gate=all(folds[w]["pass"] for w in WINDOWS)
manifest={
 "architecture":"V72_HARMONIC_COUNTERFACTUAL_ACTION_POLICY",
 "stage":"ONE_SHOT_BURNED_2021_2023_TEMPORAL_OOF",
 "truth_ledger":"CAUSALLY_ELIGIBLE_ACTION_OUTCOMES_INDEPENDENT_OF_V51_CORE_OVERLAP",
 "action_space":["NO_TRADE","REVERSAL","CONTINUATION"],
 "feature_semantics":"CONTEMPORANEOUS_PRE_ENTRY_OBSERVABLES_ONLY_NO_YEAR_FEATURE",
 "model":"FIXED_RIDGE_LINEAR_ACTION_VALUE_PLUS_FAMILY_PARTIAL_POOLING",
 "ridge":{"intercept":INTERCEPT_RIDGE,"continuous":GLOBAL_RIDGE,"family":FAMILY_RIDGE},
 "uncertainty":"DIAGONAL_REGULARIZED_INFORMATION_MEAN_PREDICTION_SE",
 "lcb_z":Z,"min_selected_per_year":MIN_SELECTED,
 "features":FEATURES,"families":FAMILIES,
 "folds":folds,
 "final_models":{"reversal":final_models["REVERSAL"]["string"],
                 "continuation":final_models["CONTINUATION"]["string"],
                 "reversal_n":final_models["REVERSAL"]["n"],
                 "continuation_n":final_models["CONTINUATION"]["n"]},
 "oof_selected_total":len(selected_all),
 "hcap_gate":hcap_gate,
 "gate_semantics":"3YEAR_TEMPORAL_OOF_EACH_YEAR_N_GE_60_MEAN_R_GT_0_PF_GT_1_LCB95_GT_0__NO_THRESHOLD_TUNING",
 "capital_execution_used":False,"validation_used":False,"fresh_used":False
}
(out/"HCAP_MANIFEST.json").write_text(json.dumps(manifest,indent=2))
(out/"HCAP_OOF_SELECTED.json").write_text(json.dumps(selected_all,indent=2))
print(json.dumps(manifest,indent=2))
