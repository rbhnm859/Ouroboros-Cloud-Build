import json
from pathlib import Path
import tempfile
import unittest
import yaml
from workflow_guard import Loader, check

ROOT = Path(__file__).resolve().parents[2]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'engineering/m3/workflow-contract.json').read_text())
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in self.manifest['workflows']:
            out = self.root / path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes((ROOT / path).read_bytes())
        self.path = next(iter(self.manifest['workflows']))

    def mutate(self, fn):
        path = self.root / self.path
        doc = yaml.load(path.read_text(), Loader=Loader)
        fn(doc)
        path.write_text(yaml.safe_dump(doc, sort_keys=False))
        return check(self.root, self.manifest)

    def test_baseline(self):
        self.assertEqual(check(self.root, self.manifest), [])

    def test_group_drift(self):
        self.assertTrue(self.mutate(lambda d: d['concurrency'].update(group='unexpected')))

    def test_cancel_drift(self):
        self.assertTrue(self.mutate(lambda d: d['concurrency'].update({'cancel-in-progress': False})))

    def test_string_false_rejected(self):
        self.assertTrue(self.mutate(lambda d: d['concurrency'].update({'cancel-in-progress': 'false'})))

    def test_permission_escalation(self):
        self.assertTrue(self.mutate(lambda d: d['permissions'].update({'contents': 'write', 'id-token': 'write'})))

    def test_dispatch_removed(self):
        self.assertTrue(self.mutate(lambda d: d['on'].pop('workflow_dispatch')))

    def test_job_condition_drift(self):
        self.assertTrue(self.mutate(lambda d: next(iter(d['jobs'].values())).update({'if': '${{ always() }}'})))

    def test_missing_workflow(self):
        (self.root / self.path).unlink()
        self.assertTrue(check(self.root, self.manifest))

    def test_invalid_yaml(self):
        (self.root / self.path).write_text('jobs: [')
        self.assertTrue(check(self.root, self.manifest))

    def test_duplicate_key(self):
        with self.assertRaisesRegex(ValueError, 'duplicate YAML key'):
            yaml.load('concurrency: 1\nconcurrency: 2\n', Loader=Loader)

    def test_case_insensitive_group_collision(self):
        first, second = list(self.manifest['workflows'])[:2]
        group = self.manifest['workflows'][second]['contract']['concurrency']['group']
        errors = self.mutate(lambda d: d['concurrency'].update(group=group.upper()))
        self.assertTrue(any('shared group' in e for e in errors))

    def test_r17_r18_are_isolated(self):
        # Static contract only. This is not a live GitHub scheduler test.
        contracts = self.manifest['workflows']
        prefix = '.github/workflows/harmonybot-v74-'
        a = contracts[prefix + 'r17-research.yml']['contract']
        b = contracts[prefix + 'r18-semantic.yml']['contract']
        for ref in ('refs/heads/main', 'refs/heads/harmonybot/v73-opportunity-universe'):
            groups = [c['concurrency']['group'].replace('${{ github.ref }}', ref).casefold() for c in (a, b)]
            self.assertNotEqual(*groups)
        for c in (a, b):
            self.assertIs(c['concurrency']['cancel-in-progress'], True)

    def test_yaml_on_is_not_boolean(self):
        self.assertIn('on', yaml.load('on:\n  workflow_dispatch:\n', Loader=Loader))


if __name__ == '__main__':
    unittest.main()
