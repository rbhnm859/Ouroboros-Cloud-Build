"""CTRSTA small-data learner: soft regime, competing commits, mechanism value,
explicit duration, family partial pooling and year-DRO top-tail objective.
Training targets are isolated; prediction never receives sample outcomes.
"""
import numpy as np
from collections import Counter
from sklearn.linear_model import Ridge

REGIMES=('REVERSAL','CONTINUATION','NOEDGE')

def softmax(a):
    e=np.exp(np.clip(a-a.max(axis=1,keepdims=True),-40,0));return e/e.sum(axis=1,keepdims=True)

class Head:
    def fit(self,x,target,weight):
        self.model=Ridge(alpha=120.,solver='lsqr',tol=1e-5).fit(x,target,sample_weight=weight)
        return self
    def predict(self,x):return self.model.predict(x)

class CTRSTA:
    def fit(self,x,targets,years,families,events):
        x=np.asarray(x,dtype=np.float32);y=np.asarray(targets,dtype=np.float32)
        self.mean=x.mean(0);self.scale=x.std(0);self.scale[self.scale<.05]=1
        z=np.clip((x-self.mean)/self.scale,-8,8)
        groups=np.asarray(years);cnt=Counter(events)
        weights=np.array([1/cnt[e] for e in events]);weights/=weights.mean()
        yw={g:1/len(set(e for e,gg in zip(events,years) if gg==g)) for g in set(years)}
        weights*=np.array([yw[g] for g in years]);weights/=weights.mean()
        weights*=.25+.75*np.max(y[:,:3],axis=1) # ambiguous soft regimes downweighted
        # Target columns: soft R/C/NOEDGE; commit hazards R/C; action R;
        # future wait value; action winner; event-relative top-tail soft target.
        # Fixed DRO rounds, no architecture or threshold choices on test years.
        group_weights={g:1. for g in set(years)}
        for _ in range(4):
            w=weights*np.array([group_weights[g] for g in years])
            self.regime=Head().fit(z,y[:,:3],w)
            self.hazard=Head().fit(z,y[:,3:5],w)
            self.wait=Head().fit(z,y[:,6],w)
            self.experts={}
            for m in (0,1):
                ix=y[:,9]==m
                if ix.sum()<20:raise ValueError('mechanism training support missing')
                self.experts[m]=Head().fit(z[ix],y[ix][:,[5,7,8]],w[ix])
            predictions=np.zeros((len(z),3))
            for m in (0,1):
                ix=y[:,9]==m;predictions[ix]=self.experts[m].predict(z[ix])
            loss=(predictions[:,0]-y[:,5])**2+4*(predictions[:,2]-y[:,8])**2
            for g in group_weights:
                ix=groups==g;group_weights[g]*=np.exp(.15*min(5,float(np.average(loss[ix],weights=weights[ix]))))
            norm=sum(group_weights.values())/len(group_weights)
            group_weights={g:min(4,max(.25,v/norm)) for g,v in group_weights.items()}
        self.dro_weights=group_weights
        # Empirical Bayes style intercept pooling: small family deltas shrink.
        # Never separate sparse family models; every sample retains global expert.
        self.family_delta={}
        for m in (0,1):
            for f in set(families):
                ix=(y[:,9]==m)&(np.asarray(families)==f)
                n=len(set(e for e,b in zip(events,ix) if b))
                if not ix.any():continue
                residual=y[ix,5]-predictions[ix,0]
                self.family_delta[(m,f)]=float(np.average(residual,weights=weights[ix]))*n/(n+80)
        self.error={m:1. for m in (0,1)}
        return self

    def predict(self,x,mechanisms,families):
        # Explicit inputs only, no row/setup/label dictionary or future decisions.
        z=np.clip((np.asarray(x)-self.mean)/self.scale,-8,8)
        regime=softmax(self.regime.predict(z)*2)
        hazards=np.clip(self.hazard.predict(z),0,1)
        total=hazards.sum(1);hazards/=np.maximum(1,total)[:,None]
        wait=self.wait.predict(z)
        q=np.empty(len(z));p=np.empty(len(z));rank=np.empty(len(z))
        for m in (0,1):
            ix=np.asarray(mechanisms)==m
            if not ix.any():continue
            v=self.experts[m].predict(z[ix]);q[ix]=v[:,0];p[ix]=np.clip(v[:,1],0,1);rank[ix]=v[:,2]
        q+=np.array([self.family_delta.get((m,f),0) for m,f in zip(mechanisms,families)])
        errors=np.array([self.error[m] for m in mechanisms])
        # Conservative predictive lower-tail proxies. These are NOT statistical
        # confidence bounds on E[R]; no claim of calibrated P(win)_LCB is made.
        enter=q-.5*errors;wait_lower=wait-.5*errors
        score=rank+.25*p+.15*regime[np.arange(len(z)),mechanisms]+.10*hazards[np.arange(len(z)),mechanisms]-.10*regime[:,2]
        return {'q':q,'p':p,'score':score,'enter':enter,'wait':wait_lower,'regime':regime,'hazard':hazards}
