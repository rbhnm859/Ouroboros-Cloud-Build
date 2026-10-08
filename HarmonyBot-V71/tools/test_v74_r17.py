import base64
import datetime as dt
import gzip
import hashlib
import pathlib
import random
import sys
import tempfile
import unittest

import numpy as np

HERE=pathlib.Path(__file__).resolve().parent
HB=HERE.parent
REPO=HB.parent
sys.path.insert(0,str(HERE))

from v74_r17_contract import action_native_encode,MINUTES,CHANNELS
from v74_r17_contract import TICK_ORDER_FORWARD,TICK_ORDER_LEGACY
from v74_r17_contract import ContractError,load_tick_frames,parse_frame,parse_inner
from v74_r17_tickminute import BINS,accumulate,forward_window

SRC=HB/'src/Architecture/HarmonyBotV74.R17TickState.cs'
PIP=0.01
OPEN=dt.datetime(2020,1,2,10,0,0,tzinfo=dt.timezone.utc)
FIXTURE=[(0.0,1500.00,1500.10),(7.5,1500.20,1500.30),(10.0,1500.30,1500.40),
         (15.0,1500.10,1500.20),(22.5,1500.40,1500.50),(52.0,1500.50,1500.60)]

def source():
    return SRC.read_text()

def synth_inner(schema,order=None):
    static='0,0.2,0,0.3,-0.4,0.5,0.2,0.1,5.0'
    row=','.join(['0']*CHANNELS)
    values=';'.join([row]*MINUTES)
    head='[V74-R17-TICK] schema='+schema+' '
    if order is not None:head+='tick_order='+order+' '
    return (head+'setup=S bar=1 decision=2020-01-02T10:01:00Z minutes=%d channels=%d static=%s values=%s'
            %(MINUTES,CHANNELS,static,values))

def synth_frame(envelope,inner_schema,order=None):
    raw=synth_inner(inner_schema,order).encode('utf-8')
    data=base64.b64encode(gzip.compress(raw)).decode('ascii')
    return ('[V74-R17-FRAME] schema='+envelope+' setup=S bar=1 sha256='
            +hashlib.sha256(raw).hexdigest()+' data='+data)

class R17Contract(unittest.TestCase):
    def test_tick_encoder_shape_and_direction(self):
        values=np.zeros((MINUTES,CHANNELS),dtype=float)
        values[:,0]=np.log1p(20.0)
        values[:,4]=.25
        values[:,9]=.50
        values[:,11]=.30
        values[:,12]=.10
        values[:,20:28]=.20
        z={'values':values.tolist(),'static':[0,.2,0,.3,-.4,.5,.2,.1,5.0]}
        pos,_=action_native_encode(z,1)
        neg,_=action_native_encode(z,-1)
        self.assertEqual(len(pos),8*CHANNELS+9)
        self.assertTrue(np.isfinite(pos).all())
        self.assertTrue(np.isfinite(neg).all())
        self.assertNotEqual(float(pos[4]),float(neg[4]))

    def test_source_accumulates_ticks_in_forward_time_order(self):
        text=source()
        self.assertIn('for (int k = first; k < pastEnd; k++)',text)
        self.assertNotIn('for (int k = pastEnd - 1; k >= first; k--)',text)
        self.assertIn('if (t < openUtc) continue;',text)
        self.assertIn('if (t >= endUtc) break;',text)
        self.assertIn('R17_TICK_TIME_DIRECTION',text)
        self.assertIn('R17_TICK_SERIES_ORDER',text)
        self.assertIn('R17_TICK_LOWER_BOUND_CONTRACT',text)

    def test_source_reads_only_predecision_server_ticks(self):
        text=source()
        self.assertIn('MarketData.GetTicks(SymbolName)',text)
        self.assertIn('LoadMoreHistory()',text)
        self.assertIn('if (t < openUtc) continue;',text)
        self.assertIn('if (t >= endUtc) break;',text)
        self.assertIn('AddMinutes(1)',text)
        self.assertIn('R17_DECISION_ALIGNMENT',text)
        self.assertIn('i > LastClosedIndex(_m1Bars)',text)
        for forbidden in ('MfeR','MaeR','OutcomeR'):
            self.assertNotIn(forbidden,text)

    def test_tick_fingerprint_separation(self):
        text=source()
        self.assertIn('schema=V74_R17_TICK_V3 tick_order=FORWARD',text)
        self.assertIn('schema=V74_R17_TICK_V4 setup=',text)
        self.assertNotIn('schema=V74_R17_TICK_V2 setup=',text)
        self.assertNotIn('schema=V74_R17_TICK_V1 setup=',text)

    def test_tick_lower_bound_exact_parity(self):
        from bisect import bisect_left
        rng=random.Random(17074)
        text=source()
        self.assertIn('private int V74R17LowerBoundTick(DateTime utc)',text)
        for case in range(120):
            ticks=sorted(rng.randrange(-120,86400) for _ in range(rng.randrange(0,3200)))
            for minute in (-180,0,60,120,900,7200,60000,86520):
                reference=[i for i in range(len(ticks)) if minute<=ticks[i]<minute+60]
                selected=list(range(bisect_left(ticks,minute),bisect_left(ticks,minute+60)))
                self.assertEqual(reference,selected)
            older=sorted(rng.randrange(-86400,-121) for _ in range(25))
            ticks=older+ticks
            self.assertEqual(
                [i for i in range(len(ticks)) if 0<=ticks[i]<60],
                list(range(bisect_left(ticks,0),bisect_left(ticks,60))))

    def test_forward_minute_golden_fixture(self):
        m=accumulate(FIXTURE,OPEN,PIP)
        self.assertAlmostEqual(m.sum_dt,52.0,places=9)
        self.assertAlmostEqual(m.max_dt,29.5,places=9)
        self.assertAlmostEqual(m.first_mid,1500.05,places=9)
        self.assertAlmostEqual(m.last_mid,1500.55,places=9)
        self.assertAlmostEqual(m.min_mid,1500.05,places=9)
        self.assertAlmostEqual(m.max_mid,1500.55,places=9)
        self.assertAlmostEqual(m.path,0.90,places=9)
        self.assertAlmostEqual(m.sq_move,0.19,places=9)
        self.assertEqual((m.up,m.down,m.flat),(4,1,0))
        self.assertEqual(m.reversals,2)
        self.assertEqual((m.max_up_run,m.max_down_run),(2,1))
        self.assertEqual(m.count,6)

    def test_forward_minute_feature_channels_are_live(self):
        m=accumulate(FIXTURE,OPEN,PIP)
        f=m.features(PIP,PIP)
        self.assertEqual(len(f),CHANNELS)
        self.assertAlmostEqual(f[1],10.4/60.0,places=9)
        self.assertAlmostEqual(f[3],29.5/60.0,places=9)
        self.assertGreater(f[1],0.0)
        self.assertGreater(f[3],0.0)
        self.assertAlmostEqual(f[4],(1500.55-1500.05)/PIP,places=6)
        self.assertAlmostEqual(f[9],0.6,places=9)
        self.assertAlmostEqual(f[11],2.0/6.0,places=9)
        self.assertAlmostEqual(f[12],1.0/6.0,places=9)
        self.assertAlmostEqual(f[13],0.10/PIP,places=6)

    def test_bin_last_mid_is_latest_tick_in_bin(self):
        m=accumulate(FIXTURE,OPEN,PIP)
        self.assertEqual(m.bin_count,[1,2,1,1,0,0,1,0])
        self.assertEqual(m.bin_seen,[True,True,True,True,False,False,True,False])
        expected=[1500.05,1500.35,1500.15,1500.45,0.0,0.0,1500.55,0.0]
        for got,want in zip(m.bin_last_mid,expected):
            self.assertAlmostEqual(got,want,places=9)
        bins=m.filled_bin_mid()
        self.assertEqual(len(bins),BINS)
        self.assertAlmostEqual(bins[0],1500.05,places=9)
        self.assertAlmostEqual(bins[3],1500.45,places=9)
        self.assertAlmostEqual(bins[4],1500.45,places=9)
        self.assertAlmostEqual(bins[6],1500.55,places=9)

    def test_legacy_reversed_feed_is_pinned_degenerate_control(self):
        forward=accumulate(FIXTURE,OPEN,PIP,TICK_ORDER_FORWARD)
        legacy=accumulate(FIXTURE,OPEN,PIP,TICK_ORDER_LEGACY)
        self.assertAlmostEqual(legacy.sum_dt,0.0,places=12)
        self.assertAlmostEqual(legacy.max_dt,0.0,places=12)
        self.assertGreater(forward.sum_dt,0.0)
        self.assertAlmostEqual(legacy.first_mid,1500.55,places=9)
        self.assertAlmostEqual(legacy.last_mid,1500.05,places=9)
        self.assertEqual((legacy.up,legacy.down),(forward.down,forward.up))
        self.assertEqual((legacy.max_up_run,legacy.max_down_run),
                         (forward.max_down_run,forward.max_up_run))
        self.assertAlmostEqual(legacy.bin_last_mid[1],1500.25,places=9)
        self.assertAlmostEqual(forward.bin_last_mid[1],1500.35,places=9)
        self.assertAlmostEqual(legacy.path,forward.path,places=9)
        self.assertEqual(legacy.bin_count,forward.bin_count)

    def test_dt_sum_identity_property(self):
        rng=random.Random(41818)
        for _ in range(200):
            n=rng.randrange(2,300)
            secs=sorted(rng.uniform(0.0,59.9) for _ in range(n))
            series=[(s,1500.0+i*0.01,1500.10+i*0.01) for i,s in enumerate(secs)]
            m=accumulate(series,OPEN,rng.choice([0.01,0.001]))
            self.assertLessEqual(m.max_dt,59.9)
            self.assertAlmostEqual(m.sum_dt,secs[-1]-secs[0],places=6)
            self.assertGreaterEqual(m.sum_dt,0.0)
            self.assertEqual(m.count,n)

    def test_bin_assignment_property(self):
        rng=random.Random(991)
        for _ in range(120):
            n=rng.randrange(2,240)
            secs=sorted(rng.uniform(0.0,59.999) for _ in range(n))
            series=[(s,1500.0,1500.10) for s in secs]
            m=accumulate(series,OPEN,PIP)
            self.assertEqual(sum(m.bin_count),n)
            for sec in secs:
                expected=min(BINS-1,int(sec/(60.0/BINS)))
                self.assertEqual(m.bin_seen[expected],True)
            for b in range(BINS):
                inside=[s for s in secs if min(BINS-1,int(s/(60.0/BINS)))==b]
                if inside:
                    self.assertAlmostEqual(m.bin_last_mid[b],1500.05,places=9)
                    self.assertEqual(m.bin_count[b],len(inside))

    def test_forward_window_rejects_time_regression(self):
        good=[(OPEN+dt.timedelta(seconds=s),1500.0,1500.10) for s in (1.0,2.0,3.0)]
        m=forward_window(good,OPEN,OPEN+dt.timedelta(minutes=1),PIP)
        self.assertEqual(m.count,3)
        bad=list(reversed(good))
        with self.assertRaises(ValueError):
            forward_window(bad,OPEN,OPEN+dt.timedelta(minutes=1),PIP)

    def test_contract_separates_tick_order_fingerprints(self):
        z=parse_inner(synth_inner('V74_R17_TICK_V1'))
        self.assertEqual(z['tick_order'],TICK_ORDER_LEGACY)
        z=parse_inner(synth_inner('V74_R17_TICK_V3',TICK_ORDER_FORWARD))
        self.assertEqual(z['tick_order'],TICK_ORDER_FORWARD)
        for bad in (synth_inner('V74_R17_TICK_V3'),
                    synth_inner('V74_R17_TICK_V3','REVERSED_LEGACY'),
                    synth_inner('V74_R17_TICK_V1','FORWARD'),
                    synth_inner('V74_R17_TICK_V9',TICK_ORDER_FORWARD)):
            with self.assertRaises(ContractError):
                parse_inner(bad)
        z=parse_frame(synth_frame('V74_R17_TICK_V4','V74_R17_TICK_V3',TICK_ORDER_FORWARD))
        self.assertEqual(z['tick_order'],TICK_ORDER_FORWARD)
        z=parse_frame(synth_frame('V74_R17_TICK_V2','V74_R17_TICK_V1'))
        self.assertEqual(z['tick_order'],TICK_ORDER_LEGACY)
        for bad in (synth_frame('V74_R17_TICK_V2','V74_R17_TICK_V3',TICK_ORDER_FORWARD),
                    synth_frame('V74_R17_TICK_V4','V74_R17_TICK_V1'),
                    synth_frame('V74_R17_TICK_V7','V74_R17_TICK_V3',TICK_ORDER_FORWARD)):
            with self.assertRaises(ContractError):
                parse_frame(bad)

    def test_loader_rejects_legacy_frames_when_forward_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            ledger=root/'Y2018-R15.log'
            ledger.write_text('[V72-HCOG-OUTCOME] dummy\n'+'[V74-R15-FRAME] dummy\n'
                              +synth_frame('V74_R17_TICK_V2','V74_R17_TICK_V1')+'\n'
                              +'[V74-R15-EVIDENCE-END] schema=V74_R15_EVIDENCE_V3 outcomes=1 frames=1\n')
            with self.assertRaises(ContractError):
                load_tick_frames(root,['Y2018'],require_order=TICK_ORDER_FORWARD)
            frames,stats=load_tick_frames(root,['Y2018'])
            self.assertEqual(stats['Y2018']['tick_order'],TICK_ORDER_LEGACY)
            self.assertEqual(stats['Y2018']['tick_order_counts'],{TICK_ORDER_LEGACY:1})
            self.assertEqual(stats['Y2018']['coverage'],1.0)
            self.assertEqual(len(frames),1)
            ledger.write_text('[V72-HCOG-OUTCOME] dummy\n'+'[V74-R15-FRAME] dummy\n'
                              +synth_frame('V74_R17_TICK_V4','V74_R17_TICK_V3',TICK_ORDER_FORWARD)+'\n'
                              +'[V74-R15-EVIDENCE-END] schema=V74_R15_EVIDENCE_V3 outcomes=1 frames=1\n')
            frames,stats=load_tick_frames(root,['Y2018'],require_order=TICK_ORDER_FORWARD)
            self.assertEqual(stats['Y2018']['tick_order'],TICK_ORDER_FORWARD)
            self.assertEqual(len(frames),1)

    def test_tick_harnesses_fail_closed_on_non_forward_frames(self):
        for name in ('run_r18_semantic_window.sh','run_r17_tick_window.sh'):
            text=(HB/'tools'/name).read_text()
            self.assertIn('schema=V74_R17_TICK_V4',text)
            self.assertIn('schema=V74_R17_TICK_V2',text)
            self.assertIn('LEGACY_REVERSED_TICK_FRAME',text)
            self.assertIn('BACKTEST_DATA_MODE=ticks',text)

    def test_r17_does_not_modify_protected_tick_lifecycle(self):
        text=(HB/'src/Architecture/HarmonyBotV71.ProtectedCore.cs').read_text()
        self.assertNotIn('V74R17',text)

    def test_r17_freezes_before_r16_and_r15(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R15Trajectory.cs').read_text()
        a=text.index('V74R17EmitTickState(o,i)')
        b=text.index('V74R16EmitMicrostructure(o,i)')
        c=text.index('string frozen=')
        self.assertLess(a,b)
        self.assertLess(b,c)

    def test_runner_is_tick_only_but_default_runner_stays_m1(self):
        base=(HB/'tools/run_backtest.sh').read_text()
        tick=(HB/'tools/run_r17_tick_window.sh').read_text()
        self.assertIn('--data-mode="${BACKTEST_DATA_MODE:-m1}"',base)
        self.assertIn('BACKTEST_DATA_MODE=ticks',tick)
        self.assertIn('V74R17TICK=true',tick)

    def test_research_scope_never_opens_burned(self):
        wf=(REPO/'.github/workflows/harmonybot-v74-r17-research.yml').read_text()
        self.assertIn('Y2016, Y2017, Y2018, Y2019, Y2020',wf)
        for year in ('Y2021','Y2022','Y2023'):
            self.assertNotIn(year,wf)
        ev=(HERE/'evaluate_v74_r17.py').read_text()
        for year in ('Y2021','Y2022','Y2023'):
            self.assertNotIn(year,ev)
        self.assertIn("'precision':.72",ev)
        self.assertIn("'burned_authorized':False",ev)
        self.assertIn('tick_precision_lift',ev)
        self.assertIn('permutation_control',ev)

if __name__=='__main__':
    unittest.main()
