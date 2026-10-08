import pathlib,sys,unittest
HERE=pathlib.Path(__file__).resolve().parent
HB=HERE.parent
REPO=HB.parent
sys.path.insert(0,str(HERE))
from v74_r18_outcome import parse_outcome,semantic_class

class R18SemanticContract(unittest.TestCase):
    def test_explicit_first_passage_label(self):
        line=(
            '[V74-R18-OUTCOME] schema=V74_R18_OUTCOME_V1 setup=S family=Bat source=EARLY '
            'route=M05_R025_H_RR35_F00 dir=BUY decision=2020-01-02T10:00:00.000Z '
            'exit=2020-01-02T10:07:00.000Z cause=TP_FIRST executed=true '
            'planned_entry=1500 fill=1500.1 stop=1499 target=1502.5 exit_px=1502.6 risk=1.1 '
            'gross_r=2.2727272727 net_r=2.2 planned_rr=2.3 entry_spread_pips=1 '
            'extra_cost_pips=0.8 min_cap_feasible=true'
        )
        z=parse_outcome(line)
        self.assertEqual(z['cause'],'TP_FIRST')
        self.assertEqual(semantic_class(z['cause']),0)
        self.assertTrue(z['executed'])

    def test_outcome_engine_uses_quote_side_not_ohlc_proxy(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R18OutcomeEngine.cs').read_text()
        self.assertIn('_symbol.Bid',text)
        self.assertIn('_symbol.Ask',text)
        self.assertIn('TP_FIRST',text)
        self.assertIn('SL_FIRST',text)
        self.assertNotIn('ModeledCostPips',text)
        self.assertNotIn('MfeR',text)
        self.assertNotIn('MaeR',text)

    def test_tick_work_is_active_only(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R18OutcomeEngine.cs').read_text()
        # Keep event+route lifetime deduplication without scanning settled
        # historical trackers on every server tick.
        self.assertIn('_v74R18Seen.Add(key)',text)
        self.assertIn('_v74R18Active.Add(t)',text)
        self.assertIn('for(int j=_v74R18Active.Count-1;j>=0;j--)',text)
        self.assertIn('if(t.Resolved)_v74R18Active.RemoveAt(j);',text)
        self.assertNotIn('_v74R18Outcome',text)
        self.assertNotIn('.Values.Where(x=>!x.Resolved).ToList()',text)

    def test_tick_exit_semantics_non_regression(self):
        text=(HB/'src/Architecture/HarmonyBotV74.R18OutcomeEngine.cs').read_text()
        for invariant in (
            'if(now>=t.DeadlineUtc)',
            'else if(!IsInstitutionalSession(now))',
            'bool sl=t.Direction==TradeDirection.Buy?bid<=t.Stop:ask>=t.Stop;',
            'bool tp=t.Direction==TradeDirection.Buy?bid>=t.Target:ask<=t.Target;',
            'if(sl)V74R18Emit(t,"SL_FIRST"',
            'else if(tp)V74R18Emit(t,"TP_FIRST"',
            'if(!t.Resolved)V74R18Emit(t,"CENSORED"',
            '[V74-R18-SUMMARY]',
        ):
            self.assertIn(invariant,text)

    def test_on_tick_shadow_hook_is_gated(self):
        text=(HB/'src/Architecture/HarmonyBotV71.ProtectedCore.cs').read_text()
        self.assertIn('if (EnableV74R18OutcomeResearch) V74R18OnTick();',text)

    def test_evaluator_never_infers_semantic_cause_from_r(self):
        text=(HERE/'evaluate_v74_r18_semantics.py').read_text()
        self.assertNotIn('def cause_of(',text)
        self.assertIn('semantic_class(o[\'cause\'])',text)
        self.assertIn("'burned_authorized':False",text)
        self.assertIn("'sequential_policy_ready':sequential_ready",text)

    def test_runner_is_server_tick_research_only(self):
        text=(HERE/'run_r18_semantic_window.sh').read_text()
        self.assertIn('BACKTEST_DATA_MODE=ticks',text)
        self.assertIn('V74R17TICK=true V74R18OUTCOME=true',text)

    def test_workflow_has_only_research_years(self):
        text=(REPO/'.github/workflows/harmonybot-v74-r18-semantic.yml').read_text()
        self.assertIn('[Y2016, Y2017, Y2018, Y2019, Y2020]',text)
        for y in ('Y2021','Y2022','Y2023'):
            self.assertNotIn(y,text)

if __name__=='__main__':
    unittest.main()
