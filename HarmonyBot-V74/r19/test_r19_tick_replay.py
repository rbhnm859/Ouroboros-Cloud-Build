from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
import tempfile
import unittest
from r19_tick_replay import Tick, TickTape, TradeIntent, replay, read_tick_csv, ReplayContractError

T=datetime(2020,1,2,0,0,tzinfo=timezone.utc)
D=Decimal
H='a'*64

def tick(seconds, bid, ask, seq=0, tradable=True):
    return Tick(T+timedelta(seconds=seconds),seq,D(str(bid)),D(str(ask)),tradable)

def intent(**kw):
    args=dict(event_id='Buy|20200102000000|1500',side='BUY',decision_at=T,
        available_at=T, last_entry_at=T+timedelta(seconds=10),
        expires_at=T+timedelta(seconds=25),stop=D('1499'),target=D('1503.6'),
        units=D('1'),equity_usd=D('100'),free_margin_usd=D('100'),
        margin_per_unit_usd=D('5'),roundtrip_commission_per_unit_usd=D('0.10'),
        modeled_swap_per_unit_usd=D('0.01'),entry_slippage_usd=D('0.01'),
        exit_slippage_usd=D('0.01'),max_entry_spread_usd=D('0.30'),
        minimum_stop_distance_usd=D('0.50'),max_basket_risk_fraction=D('0.05'),
        min_net_reward_risk=D('2'),cost_source_sha256=H,already_active_basket=False,
        used_event_before=False)
    args.update(kw)
    return TradeIntent(**args)

def tape(*ticks,max_gap=20):
    return TickTape(tuple(ticks),H,max_gap)

class TickReplayTests(unittest.TestCase):
    def test_buy_ask_entry_bid_target_exit(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(1,1500,1500.1),tick(2,1503.8,1504)))
        self.assertEqual(x.cause,'TP_FIRST')
        self.assertEqual(x.entry_price,D('1500.11'))
        self.assertEqual(x.exit_price,D('1503.59'))
        self.assertTrue(x.planned_net_rr>=2)
        self.assertEqual(x.realized_net_r,D('3.37')/D('1.23'))
    def test_sell_bid_entry_ask_stop_and_gap(self):
        x=replay(intent(side='SELL',stop=D('1502'),target=D('1495'),units=D('1')),
                 tape(tick(0,1500,1500.1),tick(1,1500,1500.1),tick(2,1503,1503.4)))
        self.assertEqual(x.cause,'SL_FIRST')
        self.assertEqual(x.entry_price,D('1499.99'))
        self.assertEqual(x.exit_price,D('1503.41'))
        self.assertLess(x.realized_net_r,D('-1'))
    def test_trade_cannot_enter_on_decision_tick(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(0,1503,1503.1,seq=1),tick(1,1500,1500.1),tick(2,1503.8,1504)))
        self.assertEqual(x.entry_at,T+timedelta(seconds=1))
    def test_no_future_feature(self):
        with self.assertRaises(ReplayContractError): intent(available_at=T+timedelta(seconds=1))
    def test_excessive_risk_rejected(self):
        x=replay(intent(units=D('10')),
                 tape(tick(0,1500,1500.1),tick(1,1500,1500.1)))
        self.assertEqual(x.cause,'REJECT_BASKET_RISK')
    def test_margin_rejected(self):
        x=replay(intent(free_margin_usd=D('1')),
                 tape(tick(0,1500,1500.1),tick(1,1500,1500.1)))
        self.assertEqual(x.cause,'REJECT_MARGIN')
    def test_never_use_duplicated_basket_or_event(self):
        x=replay(intent(already_active_basket=True),tape(tick(0,1500,1500.1)))
        self.assertEqual(x.cause,'REJECT_DUPLICATE_OR_BASKET')
    def test_spread_rejection(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(1,1500,1500.9),tick(11,1500,1500.1)))
        self.assertEqual(x.cause,'NO_FILL_SPREAD')
    def test_future_end_without_tick_is_censored(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(1,1500,1500.1)))
        self.assertEqual(x.cause,'CENSORED')
        self.assertTrue(x.entered)
    def test_data_gap_censored_not_winner(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(1,1500,1500.1),tick(15,1503.9,1504),max_gap=4))
        self.assertEqual(x.cause,'CENSORED')
    def test_no_fill_before_expiry_requires_coverage(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(11,1500,1500.1)))
        self.assertEqual(x.cause,'NO_FILL_TIMEOUT')
    def test_below_net_rr_is_rejected(self):
        x=replay(intent(target=D('1502')),
                 tape(tick(0,1500,1500.1),tick(1,1500,1500.1)))
        self.assertEqual(x.cause,'REJECT_NET_RR')
    def test_expiry_is_not_hindsight_target(self):
        x=replay(intent(),tape(tick(0,1500,1500.1),tick(1,1500,1500.1),tick(25,1503.8,1504),max_gap=30))
        self.assertEqual(x.cause,'TIME_EXPIRE')
        self.assertAlmostEqual(float(x.realized_net_r),float(D('3.57')/D('1.23')),places=5)
    def test_crossed_quote_fails(self):
        with self.assertRaises(ReplayContractError):tick(0,1500.1,1500)
    def test_reversed_tick_sequence_fails(self):
        with self.assertRaises(ReplayContractError):tape(tick(2,1500,1500.1),tick(1,1500,1500.1))
    def test_broker_cost_mandatory(self):
        with self.assertRaises(TypeError):
            a=intent().__dict__.copy();a.pop('roundtrip_commission_per_unit_usd');TradeIntent(**a)
    def test_sha256_exact_file_bytes(self):
        text='time_utc,seq,bid,ask,tradable\n2020-01-02T00:00:00Z,0,1500,1500.1,true\n'
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'ticks.csv';path.write_bytes(text.encode())
            obj=read_tick_csv(path,20)
            self.assertEqual(obj.bytes_sha256,hashlib.sha256(text.encode()).hexdigest())
            self.assertEqual(len(obj.ticks),1)
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ReplayContractError):tick(0,1500,1500.1).__class__(T.replace(tzinfo=None),0,D('1'),D('2'),True)
    def test_side_stop_geometry_rejected(self):
        x=replay(intent(stop=D('1501')),
                 tape(tick(0,1500,1500.1),tick(1,1500,1500.1)))
        self.assertEqual(x.cause,'REJECT_GEOMETRY')

if __name__=='__main__':unittest.main()
