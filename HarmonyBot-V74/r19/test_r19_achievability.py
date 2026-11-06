import datetime as dt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r19_achievability import max_nonoverlap_relaxed, IntegrityError

T = dt.datetime(2020, 1, 2)
def a(start, end):
    return {'decision': T + dt.timedelta(minutes=start), 'exit': T + dt.timedelta(minutes=end)}

class OverlapBoundTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(max_nonoverlap_relaxed([]), 0)
    def test_half_open_touch_is_allowed(self):
        self.assertEqual(max_nonoverlap_relaxed([a(0, 1), a(1, 2), a(2, 3)]), 3)
    def test_overlap_reduces_bound(self):
        self.assertEqual(max_nonoverlap_relaxed([a(0, 4), a(1, 2), a(2, 3), a(3, 5)]), 3)
    def test_unsorted_input(self):
        self.assertEqual(max_nonoverlap_relaxed([a(5, 8), a(1, 5), a(0, 9)]), 2)
    def test_negative_interval_rejected(self):
        with self.assertRaises(IntegrityError):
            max_nonoverlap_relaxed([a(3, 2)])
    def test_upper_bound_does_not_claim_event_uniqueness(self):
        self.assertEqual(max_nonoverlap_relaxed([a(0, 1), a(1, 2)]), 2)
        self.assertEqual(min(1, max_nonoverlap_relaxed([a(0, 1), a(1, 2)])), 1)

if __name__ == '__main__':
    unittest.main()
