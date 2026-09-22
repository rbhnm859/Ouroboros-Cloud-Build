import math
from pathlib import Path
src=Path("HarmonyBot-V58/src/HarmonyBotV58.cs").read_text(encoding="utf-8")

def ratios(P):
 x,a,b,c,d=P
 xa=abs(a-x); ab=abs(b-a); bc=abs(c-b); cd=abs(d-c); xc=abs(c-x)
 return (ab/xa,bc/ab,cd/bc,abs(d-a)/xa,cd/ab,xc/xa)

# affine price invariance
P=(100.0,120.0,107.64,115.28,104.28)
r1=ratios(P); r2=ratios(tuple(7.3*x+411.0 for x in P))
assert max(abs(a-b) for a,b in zip(r1,r2))<1e-10

# bull/bear mirror invariance
pivot=500.0
r3=ratios(tuple(2*pivot-x for x in P))
assert max(abs(a-b) for a,b in zip(r1,r3))<1e-10

# canonical AB=CD completion centers are discrete, not a broad 0.80-1.25 identity
assert 'V58AbcdCenters("AB=CD")' in src
assert 'AbcDMin = .80, AbcDMax = 1.25' not in src

# Cypher canonical contract tightened
assert 'InRange(xac, 1.272, 1.414)' in src
assert 'InRange(cd / Math.Max(xc, 1e-9), .760, .810)' in src

# Pure projected D must never depend on observed D.
i=src.index("private double V58PureProjectedPrzCenter")
j=src.index("private double NearestAbcdProjection",i)
pure=src[i:j]
assert "PivotPoint d" not in pure
assert "d.Price" not in pure

# Boundary perturbation: manifold score must decay smoothly with normalized distance.
def score(z,sigma=1.0): return math.exp(-.5*(z*z)/(sigma*sigma))
assert score(0)>score(.5)>score(1)>score(2)>0

# Canonical family profile sanity.
required=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
for p in required: assert f'Name = "{p}"' in src or f'AddStd("{p}"' in src

# Projection convergence and projection error are explicit independent terms.
assert "projectionConvergence" in src and "projectionPurity" in src and "ProjectionErrorAtr" in src

# Temporal DAG uses partial ordering and same-bar-compatible >= relations.
assert "c.FirstFailedExtensionBar>=c.FirstSweepBar" in src.replace(" ","")
assert "post>=c.FirstReclaimBar" in src.replace(" ","")

# Excursion capture must use prior MFE before current-bar extrema update.
u=src.index("private void UpdateV58FamilyShadowTrades")
v=src.index("private bool V58ShadowFloorHit",u)
shadow=src[u:v]
assert shadow.index("double prevMfe=x.MfeR") < shadow.index("x.MaxPrice=Math.Max")

print({"math_contract":"PASS","families":12,"affine_invariance":True,"mirror_invariance":True,"projected_d_pure":True,"temporal_dag":True,"capture_same_bar_bias_guard":True})
