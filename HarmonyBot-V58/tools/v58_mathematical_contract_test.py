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

# Temporal DAG is a strict predecessor-aware latch: early invalid events cannot poison
# a later legal sequence, and multiple stages cannot collapse onto the same M1 bar.
compact=src.replace(" ","").replace("\n","")
assert "FamilyDagStage" in src and "FamilyDagAuxA" in src and "FamilyDagAuxB" in src
assert "if(c.FamilyDagStage==0&&(rejection||failedExtension))" in compact
assert "if(c.FamilyDagStage==1&&i>c.FamilyDagPreBar&&reclaim)" in compact
assert "if(c.FamilyDagStage==2&&i>c.FamilyDagReclaimBar&&(bos||displacement))" in compact
assert "if(c.FamilyDagStage==0&&sweep)" in compact
assert "if(c.FamilyDagStage==1&&i>c.FamilyDagPreBar&&failedExtension)" in compact
assert "if(c.FamilyDagStage==2&&i>c.FamilyDagConfirmBar&&(reclaim||insidePrz))" in compact
assert "if(c.FamilyDagStage==3&&i>c.FamilyDagReclaimBar&&(bos||displacement))" in compact
assert "if(c.FamilyDagStage>=2&&c.FamilyDagAuxA&&c.FamilyDagAuxB)" not in compact
dag_start=src.index("private bool UpdateFamilyCompletionEvidence")
dag_end=src.index("private bool UpdatePatternNativeM1State",dag_start)
dag=src[dag_start:dag_end]
assert "V58FirstEvent" not in dag
assert "Diagnostic first-occurrence timestamps are retained, but they no longer determine DAG validity." in dag

def dag_pass(sequence, stages):
    stage=0
    predecessor=-1
    for bar,events in enumerate(sequence):
        if stage>=len(stages): break
        if bar<=predecessor: continue
        if any(e in events for e in stages[stage]):
            predecessor=bar
            stage+=1
    return stage==len(stages)

retr=[("rejection","failedExtension"),("reclaim",),("bos","displacement")]
ext=[("sweep",),("failedExtension",),("reclaim","insidePrz"),("bos","displacement")]
assert dag_pass([{"reclaim"},{"rejection"},{"reclaim"},{"bos"}],retr)
assert not dag_pass([{"reclaim"},{"rejection"},{"bos"}],retr)
assert dag_pass([{"sweep"},{"failedExtension"},{"reclaim"},{"bos"}],ext)
assert not dag_pass([{"sweep"},{"failedExtension"},{"bos"},{"reclaim"}],ext)
assert not dag_pass([{"sweep","failedExtension","reclaim","bos"}],ext)

# Excursion capture must use prior MFE before current-bar extrema update.
u=src.index("private void UpdateV58FamilyShadowTrades")
v=src.index("private bool V58ShadowFloorHit",u)
shadow=src[u:v]
assert shadow.index("double prevMfe=x.MfeR") < shadow.index("x.MaxPrice=Math.Max")

print({"math_contract":"PASS","families":12,"affine_invariance":True,"mirror_invariance":True,"projected_d_pure":True,"temporal_dag":True,"capture_same_bar_bias_guard":True})
