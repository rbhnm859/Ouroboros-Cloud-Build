import copy,datetime as dt,math,unittest
import numpy as np
from v74_r15_contract import parse_trajectory,ContractError,observation,MARKER
from v74_r15_encoder import encode

class CausalBoundary(unittest.TestCase):
    def line(self):
        decision=dt.datetime(2020,1,1,12,0,tzinfo=dt.timezone.utc)
        times=[(decision-dt.timedelta(minutes=31-j)).strftime('%Y-%m-%dT%H:%M:%SZ') for j in range(32)]
        values=';'.join(','.join(str((j+1)*(c+1)/100) for c in range(18)) for j in range(32))
        return f'{MARKER} schema=V74_R15_TRAJECTORY_V1 setup=Buy|2020-01-01T00:00:00|1500|1510|1520|1530|1540 bar=5 anchor=100 index=105 decision={times[-1]} times={",".join(times)} spread=0.01 sin=0 cos=-1 values={values}'
    def frame(self):
        import gzip,base64,hashlib
        raw=self.line().encode();z=parse_trajectory(self.line())
        return '[V74-R15-FRAME] schema=V74_R15_TRAJECTORY_V2 setup='+z['setup']+' bar=5 sha256='+hashlib.sha256(raw).hexdigest()+' data='+base64.b64encode(gzip.compress(raw)).decode()
    def test_transport_checksum(self):
        from v74_r15_contract import parse_frame
        self.assertEqual(parse_frame(self.frame())['bar'],5)
        with self.assertRaises(ContractError):parse_frame(self.frame().replace('bar=5','bar=6'))
        with self.assertRaises(ContractError):parse_frame(self.frame().replace('sha256=','sha256=0'))
    def test_missing_frame_count_rejected(self):
        from v74_r15_contract import load_trajectories
        import tempfile,pathlib
        with tempfile.TemporaryDirectory() as root:
            p=pathlib.Path(root)/'Y2016-R15.log';p.write_text(self.frame()+'\n[V74-R15-TRANSPORT] setup='+parse_trajectory(self.line())['setup']+' count=2')
            with self.assertRaises(ContractError):load_trajectories(root,['Y2016'])
    def test_valid_ordered_contract(self):self.assertEqual(len(parse_trajectory(self.line())['values']),32)
    def test_fail_closed_corruptions(self):
        line=self.line()
        bad=[line.replace('schema=V74_R15_TRAJECTORY_V1','schema=OLD'),line.replace(' spread=0.01',''),
             line.replace('bar=5','bar=6'),line.replace('index=105','index=31'),
             line.replace('spread=0.01','spread=NaN'),line.replace('spread=0.01','spread=-1'),
             line.replace('sin=0','sin=.1'),line+' outcome=3',line+' bar=5',
             line.replace('values=0.01','values=NaN',1),line.replace('2020-01-01T11:29:00Z,','',1),
             line.replace('decision=2020-01-01T12:00:00Z','decision=2020-01-01T12:01:00Z')]
        for value in bad:
            with self.subTest(value=value[-80:]),self.assertRaises(ContractError):parse_trajectory(value)
    def test_temporal_order_changes_encoding(self):
        z=parse_trajectory(self.line());obs=observation(z,[0]*53);other=copy.deepcopy(obs);other['values']=other['values'][::-1]
        self.assertFalse(np.array_equal(encode(obs),encode(other)))
    def test_future_labels_are_ignored(self):
        z=parse_trajectory(self.line());a=encode(observation(z,[0]*53))
        z.update({'r':999,'mfe':999,'mae':999,'future_target':999,'label':1})
        np.testing.assert_array_equal(a,encode(observation(z,[0]*53)))
    def test_suffix_outcomes_cannot_enter_model(self):
        from v74_r15_model import CTRSTA
        self.assertEqual(list(__import__('inspect').signature(CTRSTA.predict).parameters),['self','x','mechanisms','families'])
    def test_legacy_cache_is_rejected(self):
        import tempfile
        from v74_r15_contract import load_trajectories
        with tempfile.TemporaryDirectory() as root,self.assertRaises(ContractError):load_trajectories(root,['Y2016'])
    def test_oos_not_opened(self):
        import tempfile,pathlib
        from v74_r15_contract import load_trajectories
        with tempfile.TemporaryDirectory() as root:
            p=pathlib.Path(root);(p/'Y2016-R15.log').write_text(self.frame()+'\n[V74-R15-TRANSPORT] setup='+parse_trajectory(self.line())['setup']+' count=1\n[V72-HCOG-OUTCOME] test\n[V74-R15-EVIDENCE-END] schema=V74_R15_EVIDENCE_V3 outcomes=1 frames=1');(p/'Y2021-R15.log').write_bytes(b'\xff')
            self.assertEqual(len(load_trajectories(root,['Y2016'])),1)
    def test_trajectory_source_has_no_outcomes(self):
        from pathlib import Path
        src=(Path(__file__).parents[1]/'src/Architecture/HarmonyBotV74.R15Trajectory.cs').read_text()
        for token in ('o.MfeR','o.MaeR','OutcomeR','o.Result','o.V74FailureOutcome'):
            self.assertNotIn(token,src)
        self.assertIn('i>LastClosedIndex(_m1Bars)',src)
        self.assertIn('Atr(_m1Bars,14,j)',src)
    def test_route_identity_does_not_depend_on_outcome(self):
        import inspect
        from v74_r15_supply import all_options
        src=inspect.getsource(all_options)
        self.assertIn('sig = (b, f, int(eb))',src)
        self.assertNotIn('round(float(y)',src)
    def test_failure_direction_is_relative_to_native_action(self):
        from v74_r15_supply import make_samples
        for native,expected in [('REVERSAL','CONTINUATION'),('CONTINUATION','REVERSAL')]:
            r={'window':'Y2016','setup':'Buy|201601010000|1200','family':'ABCD','action':native,
               'features':[0.]*53,'failure_continuation':{'FC230':2.3},
               'failure_continuation_rr':{'FC230':2.3},'failure_continuation_entry_bar':{'FC230':5},
               'failure_continuation_bars':{'FC230':10}}
            samples=make_samples([r]);self.assertEqual(len(samples),1)
            self.assertEqual(samples[0]['action'],expected)
    def test_research_workflow_has_no_burned_matrix(self):
        from pathlib import Path
        workflow=(Path(__file__).parents[2]/'.github/workflows/harmonybot-v74-r15-research.yml').read_text()
        for year in ('Y2021','Y2022','Y2023'):
            self.assertNotIn(year,workflow)
        self.assertNotIn('evaluate_v74_sequential.py merged',workflow)
        self.assertNotIn('gh workflow run',workflow)
    def test_semantic_cache_detects_source_change(self):
        from verify_v74_r15_source import semantic_fingerprint,verify
        import tempfile,pathlib,json
        with tempfile.TemporaryDirectory() as root:
            p=pathlib.Path(root)
            files=['HarmonyBot-V71/src/robot.cs','HarmonyBot-V71/HarmonyBotV71.csproj','HarmonyBot-V71/tools/run_window.sh',
                   'HarmonyBot-V71/tools/run_backtest.sh','HarmonyBot-V71/tools/resolve_window.sh','HarmonyBot-V73/V73_RESEARCH_CUSTODY.json']
            for path in files:
                f=p/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('fixed')
            m=p/'pin.json';m.write_text(json.dumps({'research_only':True,'required_artifacts':[f'v74-r15-research-Y{y}' for y in range(2016,2021)],'semantic_fingerprint':semantic_fingerprint(p)}))
            verify(p,m)
            (p/files[0]).write_text('semantic change')
            with self.assertRaises(ValueError):verify(p,m)
    def test_sidecar_census_rejects_lossy_stdout(self):
        from v74_r15_contract import validate_sidecar
        import tempfile,pathlib
        with tempfile.TemporaryDirectory() as root:
            p=pathlib.Path(root)/'Y2016-R15.log'
            p.write_text('[V72-HCOG-OUTCOME] record\n[V74-R15-EVIDENCE-END] schema=V74_R15_EVIDENCE_V3 outcomes=2 frames=0')
            with self.assertRaises(ContractError):validate_sidecar(p)
            p.write_text('[V72-HCOG-OUTCOME] record')
            with self.assertRaises(ContractError):validate_sidecar(p)
if __name__=='__main__':unittest.main()
