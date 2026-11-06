import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r19_achievability import audit_pinned_year, collect_eligible_actions, IntegrityError

BASE='[V74-R18-OUTCOME] schema=V74_R18_OUTCOME_V1 setup=Buy|201801011000|1500.00 source=REACTION route=R1 cause=TP_FIRST executed=true decision=2018-01-01T10:01:00.000Z exit=2018-01-01T10:03:00.000Z dir=BUY fill=1500 stop=1499 target=1502.6 risk=1 gross_r=2.60 net_r=2.50 extra_cost_pips=0.8 min_cap_feasible=true\n'

def fixture(path, line=BASE, custody=None):
    info={'schema':'V74_R18_SEMANTIC_CUSTODY_V1','window':'Y2018','burned_used':False,'validation_used':False,'fresh_used':False}
    if custody: info.update(custody)
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('R18_SEMANTIC_CUSTODY.json',json.dumps(info))
        z.writestr('synthetic-R15.log',line)
    return hashlib.sha256(path.read_bytes()).hexdigest()

class EvidenceParityTests(unittest.TestCase):
    def test_synthetic_positive_event_parity(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'test.zip'
            digest=fixture(p)
            audit=audit_pinned_year(p,2018,digest)
            self.assertEqual(audit['unique_eligible_events'],1)
            self.assertEqual(audit['unique_oracle_positive_events'],1)
            self.assertEqual(audit['relaxed_nonoverlap_action_count'],1)
            self.assertFalse(audit['strict_gate'])
    def test_wrong_artifact_hash_must_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'test.zip'
            fixture(p)
            with self.assertRaises(IntegrityError):
                audit_pinned_year(p,2018,'f'*64)
    def test_new_action_cannot_be_inferred_from_log(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'test.zip'
            fixture(p)
            actions,best=collect_eligible_actions(p)
            self.assertEqual({a['action'][2] for a in actions},{'R1'})
            self.assertNotIn('R19_A1',{a['action'][2] for a in actions})
    def test_burned_flag_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'test.zip'
            digest=fixture(p,custody={'burned_used':True})
            with self.assertRaises(IntegrityError):
                audit_pinned_year(p,2018,digest)

if __name__=='__main__':
    unittest.main()
