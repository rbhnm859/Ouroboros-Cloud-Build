import unittest
from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
from dataclasses import replace
from family_projection import (FAMILY_BANDS,FAMILIES,KnownPivots,PatternContractError,
                               predict,review_completion,all_family_predictions)
T=datetime(2020,1,2,tzinfo=timezone.utc)
def make(r,s):
    x=D('100');a=D('110'); b=a-D(r)*D('10'); c=b+D(s)*D(r)*D('10')
    return KnownPivots(x,a,b,c,T,T+timedelta(minutes=1),T+timedelta(minutes=2),
            T+timedelta(minutes=3),T+timedelta(minutes=5),T+timedelta(minutes=6),D('1'))
def make_witness(f):
    if f=='Cypher':return make('0.5','1.6')
    if f=='Shark':return make('0.6','1.3')
    if f=='FiveZero':return make('1.3','1.9')
    if f=='ABCD':return make('0.6','0.618')
    r,s,_,_=FAMILY_BANDS[f]
    for i in range(51):
        rv=D(str(r[0]))+(D(str(r[1]))-D(str(r[0])))*D(i)/D(50)
        for j in range(51):
            sv=D(str(s[0]))+(D(str(s[1]))-D(str(s[0])))*D(j)/D(50)
            p=make(rv,sv)
            if predict(f,p) is not None:return p
    raise AssertionError('no geometrically realizable witness: '+f)

class ProjectionTests(unittest.TestCase):
    def test_complete_twelve_families(self):
        self.assertEqual(len(FAMILIES),12)
        self.assertEqual(len(set(FAMILIES)),12)
        for fam in FAMILIES:
            with self.subTest(fam=fam):
                p=make_witness(fam);z=predict(fam,p)
                self.assertIsNotNone(z)
                self.assertTrue(z.core_low<=z.core_high)
                d=(z.core_low+z.core_high)/D('2')
                r=review_completion(p,z,d,p.decision_at+timedelta(seconds=1))
                self.assertTrue(r['canonical_identity'])
                self.assertTrue(r['observed_prz_touch'])
                self.assertFalse(r['trade_authorized'])
    def test_no_lookahead_d_cannot_move_projection(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        first=(z.core_low,z.core_high)
        review_completion(p,z,z.core_low-D('0.2'),p.decision_at+timedelta(seconds=1),0.20)
        self.assertEqual(first,(z.core_low,z.core_high))
    def test_preregistered_buffer_only_and_no_identity_relaxation(self):
        p=make_witness('ABCD');z=predict('ABCD',p)
        obs=review_completion(p,z,z.core_low-D('.05'),p.decision_at+timedelta(seconds=1),0.10)
        self.assertTrue(obs['observed_prz_touch'])
        self.assertFalse(obs['canonical_identity'])
        with self.assertRaises(PatternContractError):z.observational_band(p.atr_at_decision,0.30)
    def test_bull_bear_mirror(self):
        for f in FAMILIES:
            with self.subTest(f=f):
                p=make_witness(f);z=predict(f,p)
                q=KnownPivots(*[D('1000')-D(v) for v in (p.x,p.a,p.b,p.c)],
                       p.x_at,p.a_at,p.b_at,p.c_at,p.c_confirmed_at,p.decision_at,p.atr_at_decision)
                w=predict(f,q)
                self.assertIsNotNone(w)
                self.assertEqual(w.side,'SELL')
                self.assertEqual(z.core_low,D('1000')-w.core_high)
                self.assertEqual(z.core_high,D('1000')-w.core_low)
                d=(w.core_low+w.core_high)/2
                self.assertTrue(review_completion(q,w,d,q.decision_at+timedelta(seconds=1))['canonical_identity'])
    def test_future_confirmation_fails(self):
        p=make('0.6','0.618')
        with self.assertRaises(PatternContractError):
            KnownPivots(p.x,p.a,p.b,p.c,p.x_at,p.a_at,p.b_at,p.c_at,
                         p.decision_at+timedelta(minutes=1),p.decision_at,p.atr_at_decision)
    def test_observation_must_be_future(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        with self.assertRaises(PatternContractError):review_completion(p,z,z.core_low,p.decision_at)
    def test_unavailable_family_does_not_fake_signal(self):
        p=make('0.3','1.6')
        self.assertIsNone(predict('Gartley',p))
        self.assertLessEqual(len(all_family_predictions(p)),12)
    def test_wrong_known_pivot_direction(self):
        with self.assertRaises(PatternContractError):
            KnownPivots(D('100'),D('110'),D('111'),D('112'),T,T+timedelta(minutes=1),
                         T+timedelta(minutes=2),T+timedelta(minutes=3),
                         T+timedelta(minutes=4),T+timedelta(minutes=5),D('1'))
    def test_cross_pivot_prediction_reuse_rejected(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        changed=replace(p,x=p.x+D('0.001'))
        with self.assertRaises(PatternContractError):
            review_completion(changed,z,(z.core_low+z.core_high)/2,p.decision_at+timedelta(seconds=1))

    def test_forged_price_zone_rejected(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        with self.assertRaises(PatternContractError):
            review_completion(p,replace(z,core_low=z.core_low+D('0.00001')),(z.core_low+z.core_high)/2,p.decision_at+timedelta(seconds=1))

    def test_forged_direction_rejected(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        with self.assertRaises(PatternContractError):
            review_completion(p,replace(z,side='SELL'),(z.core_low+z.core_high)/2,p.decision_at+timedelta(seconds=1))

    def test_forged_cutoff_rejected(self):
        p=make_witness('Gartley');z=predict('Gartley',p)
        with self.assertRaises(PatternContractError):
            review_completion(p,replace(z,source_cutoff=z.source_cutoff-timedelta(seconds=1)),(z.core_low+z.core_high)/2,p.decision_at+timedelta(seconds=1))

    def test_nonfinite_price_fails(self):
        with self.assertRaises(PatternContractError):make('NaN','0.7')
if __name__=='__main__':unittest.main()
