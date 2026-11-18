from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
import unittest
from dual_horizon_research import Proposal, assess, ContractError, FAMILIES
T=datetime(2020,1,2,tzinfo=timezone.utc)
def scenario(**kwargs):
    v=dict(event_id="BUY|20200102T000000|1500.0",family="Bat",side="BUY",horizon="DAY",
      available_at=T,decision_at=T,expires_at=T+timedelta(hours=2),
      broker_horizon_close_at=T+timedelta(hours=12),
      bid=D("1500"),ask=D("1500.1"),stop=D("1499"),target=D("1504.1"),
      equity_usd=D("1000"),available_margin_usd=D("1000"),
      broker_margin_usd_per_unit=D("10"),broker_min_units=D("1"),
      broker_unit_step=D("1"),roundtrip_fee_usd_per_unit=D("0.08"),
      swap_usd_per_unit=D("0.00"),entry_slippage_usd_per_unit=D("0.01"),
      exit_slippage_usd_per_unit=D("0.01"),
      broker_spec_sha256="0"*64,used_event=False,active_basket=False)
    v.update(kwargs)
    return Proposal(**v)
class FamilyHorizonTests(unittest.TestCase):
    def test_every_family_eligible_hypothesis(self):
        for f in FAMILIES:
            with self.subTest(f=f):
                x=assess(scenario(family=f))
                self.assertEqual(x["status"],"ELIGIBLE_FOR_RESEARCH")
                self.assertFalse(x["order_enabled"])
    def test_day_plan_roi(self):
        x=assess(scenario())
        self.assertGreaterEqual(D(x["planned_equity_gain_fraction"]),D("0.0115"))
        self.assertLessEqual(D(x["planned_loss_usd"]),D("5"))
    def test_week_plan_roi(self):
        x=assess(scenario(horizon="WEEK",broker_horizon_close_at=T+timedelta(days=3)))
        self.assertEqual(x["status"],"ELIGIBLE_FOR_RESEARCH")
        self.assertGreaterEqual(D(x["planned_equity_gain_fraction"]),D("0.023"))
    def test_broker_min_units_reject(self):
        self.assertEqual(assess(scenario(broker_min_units=D("10")))["reason"],"BROKER_MIN_SIZE_INFEASIBLE")
    def test_not_fabricated_return_if_min_lot_weak(self):
        self.assertEqual(assess(scenario(broker_min_units=D("3"),broker_unit_step=D("3"),
            target=D("1503.8")))["reason"],"TARGET_EQUITY_PERCENT_NOT_FEASIBLE")
    def test_target_rr_reject(self):
        self.assertEqual(assess(scenario(target=D("1501.6")))["reason"],"PLANNED_NET_RR_TOO_LOW")
    def test_buy_geometry(self):
        self.assertEqual(assess(scenario(stop=D("1501")))["reason"],"INVALID_PRICE_GEOMETRY")
    def test_sell_side_uses_bid(self):
        x=assess(scenario(side="SELL",stop=D("1501.5"),target=D("1495.0")))
        self.assertEqual(x["status"],"ELIGIBLE_FOR_RESEARCH")
    def test_wrong_side_geometry(self):
        self.assertEqual(assess(scenario(side="SELL"))["reason"],"INVALID_PRICE_GEOMETRY")
    def test_margin_limit(self):
        self.assertEqual(assess(scenario(available_margin_usd=D("1")))["reason"],"BROKER_MIN_SIZE_INFEASIBLE")
    def test_used_event(self):
        self.assertEqual(assess(scenario(used_event=True))["reason"],"DUPLICATE_OR_BASKET")
    def test_active_basket(self):
        self.assertEqual(assess(scenario(active_basket=True))["reason"],"DUPLICATE_OR_BASKET")
    def test_future_feature_rejected(self):
        with self.assertRaises(ContractError):scenario(available_at=T+timedelta(seconds=1))
    def test_session_termination_rejected(self):
        with self.assertRaises(ContractError):scenario(expires_at=T+timedelta(days=4))
    def test_naive_datetime_rejected(self):
        with self.assertRaises(ContractError):scenario(decision_at=T.replace(tzinfo=None))
    def test_missing_broker_spec_rejected(self):
        with self.assertRaises(ContractError):scenario(broker_spec_sha256="")
    def test_zero_broker_price_rejected(self):
        with self.assertRaises(ContractError):scenario(bid=0)
    def test_crossed_quote_rejected(self):
        with self.assertRaises(ContractError):scenario(ask=D("1499"))
    def test_unsupported_horizon(self):
        with self.assertRaises(ContractError):scenario(horizon="OVERNIGHT_FOREVER")
    def test_broker_grid_min_offset(self):
        x=assess(scenario(broker_min_units=D("0.5"),broker_unit_step=D("0.4")))
        self.assertEqual(x["status"],"ELIGIBLE_FOR_RESEARCH")
        self.assertEqual((D(x["units"])-D("0.5"))%D("0.4"),0)
    def test_no_false_positive_on_100_dollars(self):
        self.assertEqual(assess(scenario(equity_usd=D("100")))["reason"],"BROKER_MIN_SIZE_INFEASIBLE")
    def test_day_maximum_holding_duration(self):
        with self.assertRaises(ContractError):
            scenario(broker_horizon_close_at=T+timedelta(hours=25))

    def test_week_maximum_holding_duration(self):
        with self.assertRaises(ContractError):
            scenario(horizon="WEEK",broker_horizon_close_at=T+timedelta(days=8))

    def test_rejected_roi_has_observable_shortfall_but_no_order(self):
        x=assess(scenario(broker_min_units=D("3"),broker_unit_step=D("3"),
            target=D("1503.8")))
        self.assertEqual(x["reason"],"TARGET_EQUITY_PERCENT_NOT_FEASIBLE")
        self.assertGreater(D(x["shortfall_usd"]),D("0"))
        self.assertFalse(x["order_enabled"])

    def test_equivalent_timezone_offsets(self):
        from datetime import timezone as Zone
        x=assess(scenario(decision_at=T.astimezone(Zone(timedelta(hours=8)))))
        self.assertEqual(x["status"],"ELIGIBLE_FOR_RESEARCH")

if __name__=="__main__":unittest.main()
