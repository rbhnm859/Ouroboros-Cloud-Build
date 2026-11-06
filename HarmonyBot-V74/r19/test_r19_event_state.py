import datetime as dt
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from r19_event_state import DecisionSnapshot, ResearchEventMachine, canonical_event_id, ContractViolation

Z = dt.timezone.utc
T = dt.datetime(2020, 1, 1, tzinfo=Z)
S = '0' * 64
def snap(state, offset=0, action='NONE', observed=None, available=None, source=S, event_id='Buy|20200101000000|1500.01'):
    t = T + dt.timedelta(minutes=offset)
    return DecisionSnapshot(event_id, state, T, observed or t, available or t, t, source, action)

class CausalTests(unittest.TestCase):
    def test_event_key_rounds_to_actual_tick(self):
        self.assertEqual(canonical_event_id('Buy',T,1500.012,0.01),canonical_event_id('Buy',T,1500.014,0.01))
    def test_event_id_direction_not_collapsed(self):
        self.assertNotEqual(canonical_event_id('Buy',T,1500,0.01),canonical_event_id('Sell',T,1500,0.01))
    def test_reject_naive_time(self):
        with self.assertRaises(ContractViolation):
            canonical_event_id('Buy',T.replace(tzinfo=None),1500,0.01)
    def test_future_available_information_rejected(self):
        with self.assertRaises(ContractViolation):
            snap('DETECTED',0,available=T+dt.timedelta(minutes=1))
    def test_bad_digest_rejected(self):
        with self.assertRaises(ContractViolation):
            snap('DETECTED',source='unverified')
    def test_simulated_policy_and_expiry(self):
        m = ResearchEventMachine(snap('DETECTED'))
        m.advance(snap('PRZ_OBSERVED',1))
        m.advance(snap('REACTION_OBSERVED',2))
        m.advance(snap('CONFIRMABLE',3))
        m.advance(snap('ENTRY_ELIGIBLE',4))
        m.advance(snap('ENTRY_ELIGIBLE',5,'DEFER'))
        m.advance(snap('ACTIVE',6,'ENTER'))
        m.advance(snap('EXITED',7,'EXIT'))
        self.assertEqual(m.state,'EXITED')
        self.assertEqual(len(m.snapshots),8)
        with self.assertRaises(ContractViolation):
            m.advance(snap('ENTRY_ELIGIBLE',8))
    def test_duplicate_snapshot_time_rejected(self):
        m = ResearchEventMachine(snap('DETECTED'))
        with self.assertRaises(ContractViolation):
            m.advance(snap('PRZ_OBSERVED'))
    def test_event_identity_cannot_change(self):
        m = ResearchEventMachine(snap('DETECTED'))
        with self.assertRaises(ContractViolation):
            m.advance(snap('PRZ_OBSERVED',1,event_id='Sell|20200101000000|1500.01'))
    def test_skip_confirmation_rejected(self):
        m = ResearchEventMachine(snap('DETECTED'))
        with self.assertRaises(ContractViolation):
            m.advance(snap('ACTIVE',1,'ENTER'))
    def test_active_must_be_enter_action(self):
        with self.assertRaises(ContractViolation):
            snap('ACTIVE',1)

if __name__ == '__main__':
    unittest.main()
