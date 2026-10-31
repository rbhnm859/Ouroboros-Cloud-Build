import pathlib,sys,unittest
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
HB=HERE.parent
REPO=HB.parent
sys.path.insert(0,str(HERE))
from v74_r16_contract import first_passage_prior,LENGTH,CHANNELS

class R16Contract(unittest.TestCase):
    def test_first_passage_zero_drift_geometry(self):
        native=np.zeros((LENGTH,CHANNELS));state=np.zeros(80);state[57]=.25
        self.assertAlmostEqual(first_passage_prior(native,state,3.0),.25,places=6)

    def test_first_passage_positive_drift_is_monotone(self):
        state=np.zeros(80);state[57]=.25
        a=np.zeros((LENGTH,CHANNELS));b=np.zeros((LENGTH,CHANNELS))
        a[:,0]=-.05;b[:,0]=.05
        self.assertGreater(first_passage_prior(b,state,2.3),first_passage_prior(a,state,2.3))

    def test_workflow_never_opens_burned(self):
        text=(REPO/'.github/workflows/harmonybot-v74-r16-research.yml').read_text()
        for y in ('Y2021','Y2022','Y2023'): self.assertNotIn(y,text)
        self.assertIn('Y2016, Y2017, Y2018, Y2019, Y2020',text)

    def test_micro_source_is_completed_bar_and_tick_volume(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R16FirstPassage.cs').read_text()
        self.assertIn('LastClosedIndex(_m1Bars)',text)
        self.assertIn('_m1Bars.TickVolumes',text)
        self.assertNotIn('MfeR',text);self.assertNotIn('MaeR',text);self.assertNotIn('OutcomeR',text)

    def test_r16_is_cofrozen_before_r15_frame(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R15Trajectory.cs').read_text()
        self.assertLess(text.index('V74R16EmitMicrostructure(o,i)'),text.index('string frozen='))

    def test_evaluator_has_required_controls(self):
        text=(HERE/'evaluate_v74_r16.py').read_text()
        for y in ('Y2021','Y2022','Y2023'): self.assertNotIn(y,text)
        self.assertIn('permutation_control',text)
        self.assertIn('ablation_lift',text)
        self.assertIn("'precision':.72",text)

if __name__=='__main__': unittest.main()
