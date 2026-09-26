#!/usr/bin/env python3
import pathlib,sys,json
s=pathlib.Path(sys.argv[1]).read_text(errors="ignore")
families=["Gartley","Bat","Alt Bat","Butterfly","Crab","Deep Crab","Deep Gartley","Rat","Cypher","Shark","5-0","AB=CD"]
checks={
 "all_families":all(('"' + x + '"') in s for x in families),
 "family_topology":"TryFamilyTopology" in s,
 "family_joint_geometry":"FamilyNativeJointGeometryScore" in s,
 "projected_prz_context":"FamilyProjectedPrzCenter" in s,
 "family_completion":"UpdateFamilyCompletionEvidence" in s,
 "abcd_confluence":"V67HasAbcdConfluence" in s,
}
o={"contract":"V67_FAMILY_GEOMETRY","checks":checks,"pass":all(checks.values())}
print(json.dumps(o,indent=2)); raise SystemExit(0 if o["pass"] else 68)
