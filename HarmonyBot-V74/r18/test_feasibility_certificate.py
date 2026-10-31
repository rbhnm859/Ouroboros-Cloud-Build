"""Fail-closed unit tests for the standalone R18 research-only certificate."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import zipfile
from feasibility_certificate import IntegrityError, audit_year, parse_line


def line(setup='Buy|201801020945|1312.27', source='REACTION', route='R01',
         cause='TP_FIRST', executed='true', net_r='2.10', exit='2018-01-02T11:04:00.000Z',
         min_cap='true'):
    return (f'[V74-R18-OUTCOME] schema=V74_R18_OUTCOME_V1 setup={setup} family=Bat '
      f'source={source} route={route} dir=BUY decision=2018-01-02T11:03:00.000Z '
      f'exit={exit} cause={cause} executed={executed} planned_entry=100 '
      f'fill=100 stop=99 target=102.5 exit_px=102.1 risk=1 '
      f'gross_r=2.1 net_r={net_r} planned_rr=2.5 entry_spread_pips=1 '
      f'extra_cost_pips=0.8 min_cap_feasible={min_cap}')


class FeasibilityContract(unittest.TestCase):
    def test_target_net_rr_from_recorded_cost(self):
        z=parse_line(line())
        self.assertAlmostEqual(z['net_target_rr'],2.5)
        self.assertEqual(z['event'],'Buy|201801020945|1312.27')

    def test_fail_closed_invalid_order(self):
        with self.assertRaises(IntegrityError):
            parse_line(line(exit='2018-01-02T11:02:00.000Z'))

    def test_fail_closed_nofill_contradiction(self):
        with self.assertRaises(IntegrityError):
            parse_line(line(cause='NO_FILL_SESSION',executed='true'))

    def test_deduplicates_routes_not_events(self):
        with TemporaryDirectory() as root:
            p=Path(root)/'source.zip'
            rows=[line(route='R01'),line(route='R02',net_r='-1.00'),
                  line(setup='Buy|201801021045|1313.99',route='R01')]
            with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr('R18_SEMANTIC_CUSTODY.json',json.dumps({
                    'window':'Y2018','schema':'V74_R18_SEMANTIC_CUSTODY_V1',
                    'burned_used':False,'fresh_used':False,'validation_used':False}))
                z.writestr('raw-logs/test-R15.log','\n'.join(rows))
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            output=audit_year(p,2018,digest,n_required=2,win_rate=.5)
            self.assertEqual(output['shadow_eligible_events'],2)
            self.assertEqual(output['shadow_positive_events_event_oracle'],2)
            self.assertTrue(output['can_meet_necessary_count_conditions'])
            with self.assertRaises(IntegrityError):
                audit_year(p,2018,'0'*64)

    def test_reject_duplicate_exact_action(self):
        with TemporaryDirectory() as root:
            p=Path(root)/'source.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('R18_SEMANTIC_CUSTODY.json',json.dumps({
                    'window':'Y2018','schema':'V74_R18_SEMANTIC_CUSTODY_V1'}))
                z.writestr('raw-logs/test-R15.log',line()+'\n'+line())
            with self.assertRaises(IntegrityError):
                audit_year(p,2018,hashlib.sha256(p.read_bytes()).hexdigest())


if __name__=='__main__': unittest.main()
