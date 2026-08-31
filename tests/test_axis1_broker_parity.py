from __future__ import annotations

from pathlib import Path
import unittest

from core import broker as legacy
from axes.axis1_dsl.execution import broker as axis1


def order_snapshot(order):
    return {
        "id": order.id,
        "side": order.side,
        "type": order.type,
        "quantity": order.quantity,
        "limit_price": order.limit_price,
        "stop_price": order.stop_price,
        "tif": order.tif,
        "oco": order.oco,
        "status": order.status.value,
        "fill_price": order.fill_price,
        "reason": order.reason,
        "history": order.history,
        "origin": order.origin,
        "signal_time": order.signal_time,
        "client_order_id": order.client_order_id,
    }


def broker_snapshot(broker):
    return {
        "orders": {key: order_snapshot(value) for key, value in broker.orders.items()},
        "history": broker.snapshot_history(),
        "active": [order.id for order in broker.active_orders()],
    }


def run_market_case(module):
    broker = module.BrokerEmulator()
    order = module.BrokerOrder(
        id="m1",
        side="buy",
        type="market",
        quantity=2,
        origin="strategy",
        client_order_id="entry-1",
    )
    broker.submit(order, event="20260831090000")
    broker.process_bar(101, 103, 99, 102, event="20260831090500")
    return broker_snapshot(broker)


def run_order_type_case(module):
    broker = module.BrokerEmulator()
    broker.submit(module.BrokerOrder(id="limit", side="BUY", type="LIMIT", limit_price=99))
    broker.submit(module.BrokerOrder(id="stop", side="SELL", type="STOP", stop_price=95))
    broker.submit(module.BrokerOrder(id="stop_limit", side="BUY", type="STOP_LIMIT", stop_price=105, limit_price=103))
    broker.process_bar(100, 106, 94, 101, event="bar1")
    broker.process_bar(102, 104, 102, 103, event="bar2")
    return broker_snapshot(broker)


def run_cancel_expiry_case(module):
    broker = module.BrokerEmulator()
    broker.submit(module.BrokerOrder(id="oco-a", side="BUY", type="LIMIT", limit_price=99, oco="g1"))
    broker.submit(module.BrokerOrder(id="oco-b", side="BUY", type="STOP", stop_price=105, oco="g1"))
    broker.fill("oco-a", 99, event="manual-fill")

    broker.submit(module.BrokerOrder(id="client", side="SELL", type="LIMIT", limit_price=110, client_order_id="exit-1"))
    broker.cancel_client_order("exit-1", event="cancel-by-client")

    broker.submit(module.BrokerOrder(id="day", side="BUY", type="LIMIT", limit_price=80, tif="DAY"))
    broker.expire_day_orders(event="session-end")
    return broker_snapshot(broker)


def run_resolver_case(module):
    broker = module.BrokerEmulator()
    broker.submit(module.BrokerOrder(id="sized", side="BUY", type="MARKET", quantity=10))
    broker.process_bar(100, 101, 99, 100, fill_resolver=lambda order, raw: (raw + 0.25, 3.5), event="resolved")
    broker.submit(module.BrokerOrder(id="held", side="SELL_SHORT", type="MARKET", quantity=4))
    broker.process_bar(100, 101, 99, 100, fill_resolver=lambda order, raw: None, event="held")
    return broker_snapshot(broker)


class Axis1BrokerParityTests(unittest.TestCase):
    def test_market_lifecycle_history_matches_legacy(self):
        self.assertEqual(run_market_case(axis1), run_market_case(legacy))

    def test_limit_stop_and_stop_limit_matching_matches_legacy(self):
        self.assertEqual(run_order_type_case(axis1), run_order_type_case(legacy))

    def test_oco_client_cancel_and_day_expiry_match_legacy(self):
        self.assertEqual(run_cancel_expiry_case(axis1), run_cancel_expiry_case(legacy))

    def test_fill_resolver_behavior_matches_legacy(self):
        self.assertEqual(run_resolver_case(axis1), run_resolver_case(legacy))

    def test_reject_and_fail_closed_errors_match_legacy(self):
        cases = (
            lambda module, broker: broker.submit(module.BrokerOrder(id="bad-type", side="BUY", type="ICEBERG")),
            lambda module, broker: broker.submit(module.BrokerOrder(id="bad-qty", side="BUY", quantity=0)),
            lambda module, broker: broker.submit(module.BrokerOrder(id="bad-limit", side="BUY", type="LIMIT")),
        )
        for case in cases:
            with self.subTest(case=case):
                lb, ab = legacy.BrokerEmulator(), axis1.BrokerEmulator()
                lo, ao = case(legacy, lb), case(axis1, ab)
                self.assertEqual(order_snapshot(ao), order_snapshot(lo))

        for module in (legacy, axis1):
            broker = module.BrokerEmulator()
            broker.submit(module.BrokerOrder(id="filled", side="BUY"))
            broker.fill("filled", 100)
            with self.assertRaisesRegex(ValueError, "order cannot fill"):
                broker.fill("filled", 101)
            with self.assertRaisesRegex(KeyError, "unknown client_order_id"):
                broker.cancel_client_order("missing")

    def test_axis1_broker_has_no_frozen_core_runtime_import(self):
        source = Path(axis1.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
