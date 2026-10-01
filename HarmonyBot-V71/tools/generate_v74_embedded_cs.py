#!/usr/bin/env python3
import json,pathlib,sys
tm=json.load(open(sys.argv[1])); mb=json.load(open(sys.argv[2])); out=pathlib.Path(sys.argv[3])
champ=tm.get("champion")
if not champ: raise SystemExit("no V74 champion")
m=mb["models"][champ]["final"]

def csnum(x):
    x=float(x)
    if x!=x or x in (float("inf"),float("-inf")): raise SystemExit("non-finite model literal")
    s=format(x,".17g")
    if "e" not in s.lower() and "." not in s: s+=".0"
    return s

def arr(xs): return "new double[]{"+",".join(csnum(x) for x in xs)+"}"
def q(s): return '"'+str(s).replace("\\","\\\\").replace('"','\\"')+'"'
lines=[]
lines += [
"using System;",
"using System.Collections.Generic;",
"using System.Linq;",
"",
"namespace cAlgo.Robots",
"{",
"    public partial class HarmonyBotV71",
"    {",
f"        private const string V74EmbeddedChampionName = {q(champ)};"
]

if champ=="A_HIERARCHICAL_COMPETING_RISK":
    lines += [
"        private sealed class V74AStat { public int N; public double Mean,Win,Sigma,Hold; public V74AStat(int n,double m,double w,double s,double h){N=n;Mean=m;Win=w;Sigma=s;Hold=h;} }",
"        private sealed class V74AModel { public double[] Med; public V74AStat Global; public Dictionary<string,V74AStat> Family,State,FamilyState; }"
    ]
    for action,key in [("REVERSAL","Rev"),("CONTINUATION","Cont")]:
        a=m["actions"][action]
        def stat(z): return f"new V74AStat({int(z['n'])},{csnum(z['mean'])},{csnum(z['win'])},{csnum(z['sigma'])},{csnum(z['hold'])})"
        fam="new Dictionary<string,V74AStat>(StringComparer.Ordinal){"+",".join("{"+q(k)+","+stat(v)+"}" for k,v in a["family"].items())+"}"
        st="new Dictionary<string,V74AStat>(StringComparer.Ordinal){"+",".join("{"+q(k)+","+stat(v)+"}" for k,v in a["state"].items())+"}"
        fs="new Dictionary<string,V74AStat>(StringComparer.Ordinal){"+",".join("{"+q(k)+","+stat(v)+"}" for k,v in a["family_state"].items())+"}"
        lines.append(f"        private static readonly V74AModel V74A{key}=new V74AModel{{Med={arr(a['medians'])},Global={stat(a['global'])},Family={fam},State={st},FamilyState={fs}}};")
    lines += [
"        private void V74AShrink(V74AStat z,double pm,double pw,double k,out double mean,out double win,out int n,out double hold){n=z==null?0:z.N; double zm=z==null?pm:z.Mean, zw=z==null?pw:z.Win; hold=z==null?180.0:z.Hold; mean=(zm*n+pm*k)/(n+k); win=(zw*n+pw*k)/(n+k);}",
"        private void V74AScore(V72HcogOpportunity o,ref bool selected,ref double mean,ref double lcb,ref double hold){",
"            var x=V72HcapRawFeatures(o); bool cont=o.Lane==\"HCOG_FAILURE_CONTINUATION\"; var mm=cont?V74ACont:V74ARev;",
"            int[] idx={0,6,7,9,11}; string state=string.Concat(idx.Select(i=>x[i]>=mm.Med[i]?\"1\":\"0\"));",
"            V74AStat f=null,st=null,cell=null; mm.Family.TryGetValue(o.Family,out f); mm.State.TryGetValue(state,out st); mm.FamilyState.TryGetValue(o.Family+\"|\"+state,out cell);",
"            double fm,fw,fh,sm,sw,sh; int fn,sn; V74AShrink(f,mm.Global.Mean,mm.Global.Win,30.0,out fm,out fw,out fn,out fh); V74AShrink(st,mm.Global.Mean,mm.Global.Win,30.0,out sm,out sw,out sn,out sh);",
"            double pm=(fm+sm)/2.0,pw=(fw+sw)/2.0; int support;",
"            if(cell!=null){int n; V74AShrink(cell,pm,pw,40.0,out mean,out var win,out n,out hold); support=cell.N; double se=Math.Max(.05,mm.Global.Sigma)/Math.Sqrt(Math.Max(1,support)); lcb=mean-1.645*se; selected=support>=12&&mean>=.90&&win>=.70&&lcb>.15;}",
"            else {mean=pm; double win=pw; support=Math.Min(fn,sn); hold=(fh+sh)/2.0; double se=Math.Max(.05,mm.Global.Sigma)/Math.Sqrt(Math.Max(1,support)); lcb=mean-1.645*se; selected=support>=12&&mean>=.90&&win>=.70&&lcb>.15;}",
"        }"
    ]

elif champ=="B_BOUNDED_GRADIENT_STUMPS":
    lines += [
"        private readonly struct V74Stump { public readonly int J,LN,RN; public readonly double T,L,R; public V74Stump(int j,double t,double l,double r,int ln,int rn){J=j;T=t;L=l;R=r;LN=ln;RN=rn;} }",
"        private sealed class V74BAction { public double RBase,WBase,RSigma,Hold; public V74Stump[] R,W; public Dictionary<string,double[]> Fam; }"
    ]
    for action,key in [("REVERSAL","Rev"),("CONTINUATION","Cont")]:
        a=m["actions"][action]
        def stumps(z):
            return "new V74Stump[]{"+",".join(f"new V74Stump({int(v['j'])},{csnum(v['t'])},{csnum(v['l'])},{csnum(v['r'])},{int(v['ln'])},{int(v['rn'])})" for v in z["stumps"] )+"}"
        fam="new Dictionary<string,double[]>(StringComparer.Ordinal){"+",".join("{"+q(k)+","+arr([v["n"],v["delta"],v["hold"]])+"}" for k,v in a["family"].items())+"}"
        lines.append(f"        private static readonly V74BAction V74B{key}=new V74BAction{{RBase={csnum(a['r']['base'])},WBase={csnum(a['w']['base'])},RSigma={csnum(a['r']['sigma'])},Hold={csnum(a['hold'])},R={stumps(a['r'])},W={stumps(a['w'])},Fam={fam}}};")
    lines += [
"        private double V74BPred(double b,V74Stump[] ss,double[] x,out int support){double v=b; support=int.MaxValue; foreach(var s in ss){bool left=x[s.J]<=s.T; v+=left?s.L:s.R; support=Math.Min(support,left?s.LN:s.RN);} if(support==int.MaxValue)support=0; return v;}",
"        private void V74BScore(V72HcogOpportunity o,ref bool selected,ref double mean,ref double lcb,ref double hold){var x=V72HcapRawFeatures(o); bool cont=o.Lane==\"HCOG_FAILURE_CONTINUATION\"; var m=cont?V74BCont:V74BRev; int s1,s2; mean=V74BPred(m.RBase,m.R,x,out s1); double win=V74BPred(m.WBase,m.W,x,out s2); win=Math.Max(0,Math.Min(1,win)); double[] f; int fs=0; if(m.Fam.TryGetValue(o.Family,out f)){fs=(int)Math.Round(f[0]);mean+=f[1];hold=f[2];}else hold=m.Hold; int support=Math.Max(1,Math.Min(Math.Min(s1==0?1:s1,s2==0?1:s2),fs==0?int.MaxValue:fs)); double se=Math.Max(.05,m.RSigma)/Math.Sqrt(support); lcb=mean-1.645*se; selected=support>=15&&mean>=.90&&win>=.70&&lcb>.10;}"
    ]

elif champ=="C_CONFORMAL_STATE_MANIFOLD":
    lines += [
"        private sealed class V74Point { public string F,A; public double[] X; public double R,Bars; public V74Point(string f,string a,double[] x,double r,double b){F=f;A=a;X=x;R=r;Bars=b;} }"
    ]
    pts="new V74Point[]{"+",".join("new V74Point("+q(p["f"])+","+q(p["a"])+","+arr(p["x"])+","+csnum(p["r"])+","+csnum(p["bars"])+")" for p in m["points"] )+"}"
    lines.append(f"        private static readonly double[] V74CMean={arr(m['means'])};")
    lines.append(f"        private static readonly double[] V74CScale={arr(m['scales'])};")
    lines.append(f"        private static readonly V74Point[] V74CPoints={pts};")
    lines += [
"        private void V74CScore(V72HcogOpportunity o,ref bool selected,ref double mean,ref double lcb,ref double hold){",
"            var raw=V72HcapRawFeatures(o); var x=new double[raw.Length]; for(int i=0;i<x.Length;i++)x[i]=(raw[i]-V74CMean[i])/V74CScale[i]; string action=o.Lane==\"HCOG_FAILURE_CONTINUATION\"?\"CONTINUATION\":\"REVERSAL\";",
"            int same=V74CPoints.Count(p=>p.A==action&&p.F==o.Family); bool familyOnly=same>=31; var ds=new List<Tuple<double,V74Point>>();",
"            foreach(var p in V74CPoints){if(p.A!=action)continue;if(familyOnly&&p.F!=o.Family)continue;double d=0;for(int j=0;j<x.Length;j++){double z=x[j]-p.X[j];d+=z*z;}if(p.F!=o.Family)d+=.75;ds.Add(Tuple.Create(d,p));}",
"            var q=ds.OrderBy(z=>z.Item1).Take(31).Select(z=>z.Item2).ToList(); if(q.Count<12){selected=false;mean=0;lcb=-999;hold=180;return;}",
"            var rv=q.Select(p=>p.R).ToList(); mean=rv.Average(); double win=rv.Count(v=>v>0)/(double)rv.Count; double sd=Math.Sqrt(rv.Sum(v=>(v-mean)*(v-mean))/Math.Max(1,rv.Count-1)); lcb=mean-1.645*sd/Math.Sqrt(rv.Count); double gp=rv.Where(v=>v>0).Sum(),gl=-rv.Where(v=>v<0).Sum(); double pf=gl>0?gp/gl:(gp>0?999:0); var wins=rv.Where(v=>v>0).ToList();var losses=rv.Where(v=>v<0).Select(v=>-v).ToList();double rr=wins.Count>0&&losses.Count>0?wins.Average()/losses.Average():0;hold=q.Select(p=>p.Bars).OrderBy(v=>v).ElementAt(q.Count/2);selected=mean>=.90&&win>=.70&&pf>=3.30&&rr>=2.30&&lcb>0;",
"        }"
    ]
else:
    raise SystemExit("unsupported champion "+champ)

lines += [
"        partial void V74EmbeddedScore(V72HcogOpportunity o, ref bool handled, ref bool selected, ref double mean, ref double lcb, ref double holdBars)",
"        {",
"            handled=true; selected=false; mean=0; lcb=-999; holdBars=180;",
]
if champ=="A_HIERARCHICAL_COMPETING_RISK": lines.append("            V74AScore(o,ref selected,ref mean,ref lcb,ref holdBars);")
elif champ=="B_BOUNDED_GRADIENT_STUMPS": lines.append("            V74BScore(o,ref selected,ref mean,ref lcb,ref holdBars);")
else: lines.append("            V74CScore(o,ref selected,ref mean,ref lcb,ref holdBars);")
lines += ["        }","    }","}"]
out.parent.mkdir(parents=True,exist_ok=True); out.write_text("\n".join(lines)+"\n")
print(json.dumps({"champion":champ,"output":str(out),"lines":len(lines),"bytes":out.stat().st_size},indent=2))
