"""V74-R17 small-data competing-risk learner with hierarchical shrinkage."""
from collections import Counter,defaultdict
import math
import numpy as np
from sklearn.linear_model import LogisticRegression,Ridge

def _logit(p):
    p=min(.999,max(.001,float(p)))
    return math.log(p/(1-p))

def _sigmoid(x):
    if x>=0:
        z=math.exp(-x);return 1/(1+z)
    z=math.exp(x);return z/(1+z)

class TickCompetingRisk:
    def __init__(self):
        self.mean=None;self.scale=None

    def fit(self,x,cause,rvalue,years,events,families):
        x=np.asarray(x,dtype=np.float32)
        y=np.asarray(cause,dtype=int)
        rv=np.asarray(rvalue,dtype=float)
        years=np.asarray(years)
        self.mean=x.mean(0);self.scale=x.std(0);self.scale[self.scale<.05]=1.0
        z=np.clip((x-self.mean)/self.scale,-8,8)

        event_count=Counter(events)
        year_event_count={g:len(set(e for e,yy in zip(events,years) if yy==g)) for g in set(years)}
        w=np.array([1.0/event_count[e] for e in events],dtype=float)
        w*=np.array([1.0/max(1,year_event_count[yy]) for yy in years],dtype=float)
        w/=max(1e-12,w.mean())

        self.classes=np.array(sorted(set(int(v) for v in y)),dtype=int)
        if len(self.classes)<2:
            raise ValueError('R17 competing-risk needs at least two causes')

        group_weight={g:1.0 for g in sorted(set(years))}
        for _ in range(3):
            ww=w*np.array([group_weight[g] for g in years],dtype=float)
            ww/=max(1e-12,ww.mean())
            self.clf=LogisticRegression(
                C=.035,solver='lbfgs',max_iter=450,tol=1e-6
            ).fit(z,y,sample_weight=ww)
            self.value=Ridge(alpha=160.0,solver='lsqr',tol=1e-5).fit(z,rv,sample_weight=ww)
            proba=self.clf.predict_proba(z)
            class_to_col={int(c):i for i,c in enumerate(self.clf.classes_)}
            loss={}
            for g in group_weight:
                ix=np.where(years==g)[0]
                if not len(ix): continue
                p=np.array([max(1e-6,proba[i,class_to_col[int(y[i])]]) for i in ix])
                loss[g]=float(np.mean(-np.log(p)))
            avg=max(1e-9,float(np.mean(list(loss.values()))))
            group_weight={g:min(2.5,max(.4,group_weight[g]*math.sqrt(loss[g]/avg))) for g in group_weight}
        self.dro_weights=group_weight

        counts=Counter(int(v) for v in y)
        total=sum(counts.values())
        self.global_tp=(counts.get(0,0)+1.0)/(total+3.0)
        fam=defaultdict(lambda:[0,0])
        for f,c in zip(families,y):
            fam[str(f)][1]+=1
            if int(c)==0:fam[str(f)][0]+=1
        self.family_tp={}
        k=35.0
        for f,(wins,n) in fam.items():
            self.family_tp[f]=(wins+k*self.global_tp)/(n+k)
        return self

    def predict(self,x,families):
        x=np.asarray(x,dtype=np.float32)
        z=np.clip((x-self.mean)/self.scale,-8,8)
        raw=self.clf.predict_proba(z)
        cols={int(c):i for i,c in enumerate(self.clf.classes_)}

        def col(c):
            if c in cols:return raw[:,cols[c]]
            return np.zeros(len(z),dtype=float)

        p_tp=col(0);p_sl=col(1);p_exp=col(2)
        if 2 not in cols:
            p_exp=np.maximum(0.0,1.0-p_tp-p_sl)

        adjusted=[]
        for i,f in enumerate(families):
            fp=self.family_tp.get(str(f),self.global_tp)
            delta=.35*(_logit(fp)-_logit(self.global_tp))
            a=_sigmoid(_logit(p_tp[i])+delta)
            rem=max(1e-9,1.0-p_tp[i])
            scale=(1.0-a)/rem
            adjusted.append((a,p_sl[i]*scale,p_exp[i]*scale))
        adj=np.asarray(adjusted,dtype=float)
        p_tp,p_sl,p_exp=adj[:,0],adj[:,1],adj[:,2]
        q=self.value.predict(z)
        support=np.mean(np.abs(z)<=6.0,axis=1)
        score=np.log((p_tp+1e-6)/(p_sl+1e-6))+.12*np.tanh(q)-.20*p_exp-.40*np.maximum(0,.90-support)
        return {'p_tp':p_tp,'p_sl':p_sl,'p_exp':p_exp,'q':q,'support':support,'score':score}
