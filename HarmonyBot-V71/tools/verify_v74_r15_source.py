#!/usr/bin/env python3
"""Content-addressed research-only replay custody. Any C# drift is fatal."""
import hashlib,json,pathlib,subprocess,sys

def semantic_fingerprint(root):
    root=pathlib.Path(root)
    files=list((root/'HarmonyBot-V71/src').rglob('*.cs'))
    files += [root/p for p in ('HarmonyBot-V71/HarmonyBotV71.csproj','HarmonyBot-V71/tools/run_window.sh',
                              'HarmonyBot-V71/tools/run_backtest.sh','HarmonyBot-V71/tools/resolve_window.sh',
                              'HarmonyBot-V73/V73_RESEARCH_CUSTODY.json')]
    records=''.join(str(p.relative_to(root))+'  '+hashlib.sha256(p.read_bytes()).hexdigest()+'\n' for p in sorted(files,key=lambda p:str(p.relative_to(root))))
    return hashlib.sha256(records.encode()).hexdigest()

def verify(root,manifest):
    d=json.loads(pathlib.Path(manifest).read_text())
    expected=[f'v74-r15-research-Y{y}' for y in range(2016,2021)]
    if d.get('research_only') is not True or d.get('required_artifacts')!=expected:
        raise ValueError('research custody schema/year boundary')
    if d['semantic_fingerprint']!=semantic_fingerprint(root):raise ValueError('R15 semantic drift: regenerate research universe')
    return d
if __name__=='__main__':
    print(json.dumps(verify(sys.argv[1],sys.argv[2]),indent=2))
