import unittest
from r18_family_baseline import parse_outcome, FAMILIES
class BaselineTests(unittest.TestCase):
    def test_each_family_readable(self):
        for fam in FAMILIES:
            with self.subTest(family=fam):
                s=f"[V72-HCOG-OUTCOME] setup=Buy|202001010000|1490.00 family={fam} lane=L"
                self.assertEqual(parse_outcome(s),(fam,"Buy|202001010000|1490.00"))
    def test_other_logs_not_counted(self):
        self.assertIsNone(parse_outcome("[V74-R18-OUTCOME] family=Shark"))
    def test_unknown_family_rejected(self):
        with self.assertRaises(ValueError):parse_outcome("[V72-HCOG-OUTCOME] family=UNKNOWN setup=A")
    def test_missing_setup_rejected(self):
        with self.assertRaises(ValueError):parse_outcome("[V72-HCOG-OUTCOME] family=Shark")
if __name__=="__main__":unittest.main()
