import io
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from r18_tick_custody_guard import check_archive, file_sha256


def create(p, *, ver='V74_R17_TICK_V4', forward=True, include_outcome=True, protected=False, extra_frames=''):
    custody={'data_mode':'ticks','tick_time_semantics':'FORWARD' if forward else None,
             'burned_used':protected,'validation_used':False,'fresh_used':False}
    lines=[f'[V74-R17-FRAME] schema={ver} source=synthetic\n']
    if include_outcome:
        lines.append('[V74-R18-OUTCOME] schema=V74_R18_OUTCOME_V1 id=1\n')
    if extra_frames:
        lines.append(f'[V74-R17-FRAME] schema={extra_frames} source=synthetic\n')
    with ZipFile(p,'w') as z:
        z.writestr('R18_SEMANTIC_CUSTODY.json',json.dumps(custody))
        z.writestr('raw-logs/TEST-R15.log',''.join(lines))

class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'sample.zip'
    def tearDown(self):self.tmp.cleanup()
    def test_legacy_v2_is_quarantined(self):
        create(self.path,ver='V74_R17_TICK_V2')
        x=check_archive(self.path)
        self.assertEqual(x['reason'],'FORBIDDEN_TICK_FRAME')
        self.assertEqual(x['observed_schema'],'V74_R17_TICK_V2')
        self.assertFalse(x['trading_allowed'])
    def test_mixed_old_and_new_quarantined(self):
        create(self.path,extra_frames='V74_R17_TICK_V2')
        self.assertEqual(check_archive(self.path)['reason'],'FORBIDDEN_TICK_FRAME')
    def test_unknown_future_frame_quarantined(self):
        create(self.path,ver='V74_R17_TICK_V5')
        self.assertEqual(check_archive(self.path)['reason'],'FORBIDDEN_TICK_FRAME')
    def test_missing_forward_custody(self):
        create(self.path,forward=False)
        self.assertEqual(check_archive(self.path)['reason'],'MISSING_FORWARD_CUSTODY')
    def test_missing_outcome(self):
        create(self.path,include_outcome=False)
        self.assertEqual(check_archive(self.path)['reason'],'MISSING_REQUIRED_FRAME_OR_OUTCOME')
    def test_protected_data_flag(self):
        create(self.path,protected=True)
        self.assertEqual(check_archive(self.path)['reason'],'PROTECTED_DATA_USED')
    def test_bad_digest(self):
        create(self.path)
        self.assertEqual(check_archive(self.path,expected_sha256='0'*64)['reason'],'ARCHIVE_SHA256_MISMATCH')
    def test_good_synthetic_preflight_is_not_final_validation(self):
        create(self.path)
        r=check_archive(self.path,expected_sha256=file_sha256(self.path))
        self.assertEqual(r['state'],'PREFLIGHT_ONLY')
        self.assertFalse(r['trading_allowed'])
        self.assertFalse(r['new_strategy_backtest'])
    def test_missing_archive(self):
        self.assertEqual(check_archive(self.path)['reason'],'UNREADABLE')

if __name__=='__main__':unittest.main()
