"""Offline, scoped workflow drift check; does not execute Actions or strategy code."""
import argparse
import copy
import json
from pathlib import Path
import re
import yaml


class Loader(yaml.SafeLoader):
    pass


Loader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for key, values in Loader.yaml_implicit_resolvers.items():
    Loader.yaml_implicit_resolvers[key] = [(tag, pattern) for tag, pattern in values
                                         if tag != "tag:yaml.org,2002:bool"]
Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$", re.I), list("tTfF"))


def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def read(path):
    return yaml.load(Path(path).read_text(), Loader=Loader)


def contract(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        raise ValueError("workflow must define jobs")
    fields = ("needs", "if", "runs-on", "permissions", "environment", "concurrency", "strategy", "timeout-minutes", "uses")
    return {"on": doc.get("on"), "concurrency": doc.get("concurrency"),
            "permissions": doc.get("permissions"),
            "jobs": {name: {key: job[key] for key in fields if key in job}
                     for name, job in doc["jobs"].items()}}


def check(root, manifest):
    errors = []
    groups = {}
    for path, expected in manifest["workflows"].items():
        try:
            doc = read(root / path)
            actual = contract(doc)
            for field in ("on", "concurrency", "permissions", "jobs"):
                if actual[field] != expected["contract"][field]:
                    errors.append(f"{path}: {field} contract drift")
            concurrency = actual["concurrency"]
            if not isinstance(concurrency, dict):
                raise ValueError("explicit concurrency mapping required")
            group = concurrency.get("group")
            if not isinstance(group, str) or not group.strip():
                raise ValueError("nonempty concurrency.group required")
            if type(concurrency.get("cancel-in-progress")) is not bool:
                raise ValueError("cancel-in-progress must be boolean")
            # Identical groups across these independently scoped pipelines require evidence review.
            folded = group.casefold()
            if folded in groups:
                errors.append(f"{path}: shared group with {groups[folded]}; review resource ownership first")
            groups[folded] = path
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(f"{path}: {exc}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    manifest = json.loads((args.root / "engineering/m3/workflow-contract.json").read_text())
    errors = check(args.root, manifest)
    for error in errors:
        print(error)
    if errors:
        raise SystemExit(1)
    print(f"PASS: {len(manifest['workflows'])} scoped YAML/concurrency/trigger/permission/job contracts")
    print("M3 identity and live Actions scheduling: NOT_VERIFIED")


if __name__ == "__main__":
    main()
