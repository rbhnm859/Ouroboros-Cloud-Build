import pathlib,sys,unittest
import numpy as np

HERE=pathlib.Path(__file__).resolve().parent
HB=HERE.parent
REPO=HB.parent
sys.path.insert(0,str(HERE))

from v74_r17_contract import action_native_encode,MINUTES,CHANNELS

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

    def test_source_reads_only_predecision_server_ticks(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R17TickState.cs').read_text()
        self.assertIn('MarketData.GetTicks(SymbolName)',text)
        self.assertIn('LoadMoreHistory()',text)
        self.assertIn('if (t >= endUtc) continue;',text)
        self.assertIn('if (t < openUtc) break;',text)
        for forbidden in ('MfeR','MaeR','OutcomeR'):
            self.assertNotIn(forbidden,text)

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
