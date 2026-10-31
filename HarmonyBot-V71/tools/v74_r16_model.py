"""V74-R16 fixed small-data first-passage residual learner."""
from collections import Counter
import numpy as np
from sklearn.linear_model import Ridge

class FirstPassageResidual:
    def __init__(self,use_physics=True):
        self.use_physics=use_physics

    def fit(self,x,ywin,rvalue,prior,years,events):
        x=np.asarray(x,dtype=np.float32);y=np.asarray(ywin,dtype=float);rv=np.asarray(rvalue,dtype=float)
        prior=np.asarray(prior,dtype=float)
        self.mean=x.mean(0);self.scale=x.std(0);self.scale[self.scale<.05]=1.0
        z=np.clip((x-self.mean)/self.scale,-8,8)
        cnt=Counter(events)
        w=np.array([1.0/cnt[e] for e in events],dtype=float)
        unique_by_year={g:len(set(e for e,gg in zip(events,years) if gg==g)) for g in set(years)}
        w*=np.array([1.0/max(1,unique_by_year[g]) for g in years]);w/=w.mean()
        self.base_prior=float(np.average(y,weights=w))
        gp={g:1.0 for g in set(years)}
        years_a=np.asarray(years)
        for _ in range(4):
            ww=w*np.array([gp[g] for g in years]);ww/=ww.mean()
            p0=prior if self.use_physics else np.full(len(y),self.base_prior)
            self.win=Ridge(alpha=90.0,solver='lsqr',tol=1e-5).fit(z,y-p0,sample_weight=ww)
            self.value=Ridge(alpha=140.0,solver='lsqr',tol=1e-5).fit(z,rv,sample_weight=ww)
            pred=np.clip(p0+self.win.predict(z),.001,.999)
            loss={}
            for g in gp:
                ix=years_a==g
                loss[g]=float(np.mean((pred[ix]-y[ix])**2))
            avg=max(1e-9,float(np.mean(list(loss.values()))))
            gp={g:min(2.5,max(.4,gp[g]*np.sqrt(loss[g]/avg))) for g in gp}
        self.dro_weights=gp
        resid=np.clip((prior if self.use_physics else self.base_prior)+self.win.predict(z),0,1)-y
        self.resid_std=float(np.sqrt(np.average(resid*resid,weights=w)))
        return self

    def predict(self,x,prior):
        x=np.asarray(x,dtype=np.float32);z=np.clip((x-self.mean)/self.scale,-8,8)
        p0=np.asarray(prior,dtype=float) if self.use_physics else np.full(len(z),self.base_prior)
        p=np.clip(p0+self.win.predict(z),.001,.999)
        q=self.value.predict(z)
        support=np.mean(np.abs(z)<=6.0,axis=1)
        score=np.log(p/(1-p))+.10*np.tanh(q)-.35*np.maximum(0,.90-support)
        return {'p':p,'q':q,'score':score,'support':support}
