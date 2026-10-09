"""Fixed causal temporal kernels; no test-year fit or random feature search.
ROCKET-like, not an implementation claim of published MiniRocket.
"""
import numpy as np
from v74_r15_contract import LENGTH,CHANNELS,ContractError
KERNELS=np.array([[1,-2,1],[-1,0,1],[1,1,-2],[-2,1,1]],dtype=float)
DILATIONS=(1,2,4,8)

def encode(observation,sequence=True):
    v=np.asarray(observation['values'],dtype=float)
    if v.shape!=(LENGTH,CHANNELS) or not np.isfinite(v).all(): raise ContractError('encoder input')
    features=[v[-1],v.mean(0),v.std(0),v.min(0),v.max(0)]
    if sequence:
        for d in DILATIONS:
            for kernel in KERNELS:
                z=sum(kernel[k]*v[k*d:LENGTH-(2-k)*d] for k in range(3))
                # PPV with fixed zero bias, signed terminal response and extremum.
                # No bias/normalization is learned from the held-out year.
                features.extend([(z>0).mean(0),z[-1],z.max(0),z.min(0)])
        signs=np.sign(v[:,0]);run=1
        for j in range(LENGTH-2,-1,-1):
            if signs[j]!=signs[-1]:break
            run+=1
        features.extend([np.array([run/LENGTH,observation['bar']/180]),v[-8:].mean(0)-v[:8].mean(0)])
    else:
        # Matched OHLC summary ablation on exactly the same action opportunities.
        features.append(np.array([observation['bar']/180]))
    features.append(np.asarray(observation['static'],dtype=float))
    result=np.concatenate(features)
    if not np.isfinite(result).all():raise ContractError('nonfinite encoding')
    return result
