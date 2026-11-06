#!/usr/bin/env python3
"""HBXAU V1 protected-branch change-scope verifier.

Checks the exact *commit diff*, not an informal repository-name convention.
Runs offline in GitHub Actions: no network, credentials, API or cTrader calls.
This is CI evidence, not a substitute for server-side branch protection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

BASE_SHA = "c3283e6f61741a5a9a3d2fc7ea31a066b64f7806"
V1_BRANCH = "feat/harmonybot-xauusd-core-v1-20261106"
V1_PREFIX = "HarmonyBot-XAUUSD-V1/"
WORKFLOW = ".github/workflows/harmonybot-xauusd-v1-domain.yml"


def allowed_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path:
        return False
    if any(part in ("", ".", "..") for part in path.split("/")):
        return False
    return path.startswith(V1_PREFIX) or path == WORKFLOW


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=True,
                            text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    return result.stdout.strip()


def project_refs_safe(root: Path) -> list[str]:
    violations: list[str] = []
    v1root = (root / V1_PREFIX).resolve()
    for project in (v1root / "src").rglob("*.csproj"):
        try:
            parsed = ET.parse(project)
        except ET.ParseError:
            violations.append("INVALID_CSPROJ_XML:" + str(project))
            continue
        for node in parsed.findall(".//ProjectReference"):
            include = node.attrib.get("Include", "")
            resolved = (project.parent / include).resolve()
            if not include or not resolved.is_relative_to(v1root) or not resolved.is_file():
                violations.append("CROSS_PROJECT_REFERENCE:" + str(project) + ":" + include)
    return violations


def audit(root: Path, base: str, head: str, expected_branch: str | None) -> dict:
    errors: list[str] = []
    if base != BASE_SHA:
        errors.append("BASE_SHA_CHANGED")
    try:
        actual_head = git(root, "rev-parse", head)
        git(root, "cat-file", "-e", base + "^{commit}")
        git(root, "merge-base", "--is-ancestor", base, actual_head)
        changes = git(root, "diff", "--no-renames", "--name-only",
                      base, actual_head).splitlines()
    except (subprocess.CalledProcessError, OSError) as exc:
        actual_head = "UNKNOWN"
        changes = []
        errors.append("GIT_ANCESTRY_OR_DIFF_UNAVAILABLE:" + type(exc).__name__)
    if expected_branch and expected_branch != V1_BRANCH:
        errors.append("UNEXPECTED_BRANCH:" + expected_branch)
    if expected_branch and os.environ.get("GITHUB_REF_NAME", expected_branch) != expected_branch:
        errors.append("CI_REF_BRANCH_MISMATCH")
    rejected_paths = sorted(path for path in changes if not allowed_path(path))
    if rejected_paths:
        errors.append("PROTECTED_PATHS_CHANGED")
    if not changes:
        errors.append("EMPTY_OR_UNVERIFIED_DIFF")
    errors += project_refs_safe(root)

    workflow = root / WORKFLOW
    if not workflow.is_file():
        errors.append("ISOLATED_WORKFLOW_MISSING")
    else:
        text = workflow.read_text(encoding="utf-8")
        if not re.search(r"(?m)^\s*contents:\s*read\s*$", text):
            errors.append("CI_READ_ONLY_PERMISSION_MISSING")
        if V1_BRANCH not in text:
            errors.append("CI_BRANCH_FILTER_MISSING")
        # Fail closed on any secret, live order dispatch or workflow privilege expansion.
        unsafe = ("secrets.", "CTRADER_PASSWORD", "CTRADER_CTID",
                  "pull_request_target:", "schedule:", "workflow_run:",
                  "contents: write", "actions: write", "git push", "gh workflow run")
        if any(value in text for value in unsafe):
            errors.append("UNSAFE_V1_CI_TOKEN")
    diff_digest = hashlib.sha256(
        ("\n".join(sorted(changes)) + "\n").encode("utf-8")
    ).hexdigest()
    return {
        "schema": "HBXAU_V1_BRANCH_ISOLATION_V1",
        "status": "PASS" if not errors else "FAIL",
        "source_baseline": BASE_SHA,
        "verified_base": base,
        "head": actual_head,
        "branch": expected_branch or "LOCAL_UNSPECIFIED",
        "allowed_prefix": V1_PREFIX,
        "allowed_workflow": WORKFLOW,
        "changed_paths": sorted(changes),
        "changed_paths_sha256": diff_digest,
        "blocked_paths": rejected_paths,
        "errors": errors,
        "interpretation": "CI diff & project references checked; branch rulesets and runtime isolation not attested",
    }


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--root", type=Path, default=Path("."))
    cli.add_argument("--base", default=BASE_SHA)
    cli.add_argument("--head", default="HEAD")
    cli.add_argument("--branch", default=None)
    cli.add_argument("--output", type=Path, required=True)
    options = cli.parse_args()
    record = audit(options.root.resolve(), options.base, options.head, options.branch)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    options.output.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8")
    print("[HBXAU-ISOLATION]", record["status"], "head=" + record["head"],
          "paths=" + str(len(record["changed_paths"])), "errors=" + repr(record["errors"]))
    return 0 if record["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
