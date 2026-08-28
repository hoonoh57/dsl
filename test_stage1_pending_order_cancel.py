import unittest

from core.broker import BrokerEmulator, BrokerOrder, OrderStatus


class PendingOrderCancelTests(unittest.TestCase):
    def _submit(self, *, order_id, client_order_id, order_type, limit_price=None, stop_price=None):
        broker = BrokerEmulator()
        order = broker.submit(
            BrokerOrder(
                id=order_id,
                client_order_id=client_order_id,
                side="BUY",
                type=order_type,
                quantity=1.0,
                limit_price=limit_price,
                stop_price=stop_price,
                tif="GTC",
                origin="DSL_PENDING",
            ),
            event="t0",
        )
        self.assertEqual(OrderStatus.ACCEPTED, order.status)
        return broker, order

    def test_limit_cancel_by_client_identity_is_terminal_and_prevents_fill(self):
        broker, order = self._submit(
            order_id="broker-1",
            client_order_id="entry-1",
            order_type="LIMIT",
            limit_price=100.0,
        )

        canceled = broker.cancel_client_order("entry-1", reason="setup invalidated", event="t1")
        fills = broker.process_bar(99.0, 102.0, 98.0, 101.0, event="t2")

        self.assertIs(order, canceled)
        self.assertEqual(OrderStatus.CANCELED, order.status)
        self.assertEqual("setup invalidated", order.reason)
        self.assertEqual([], fills)
        self.assertEqual("CANCELED", order.history[-1]["status"])
        self.assertEqual("entry-1", order.history[-1]["client_order_id"])

    def test_stop_cancel_by_client_identity_prevents_later_trigger(self):
        broker, order = self._submit(
            order_id="broker-2",
            client_order_id="entry-2",
            order_type="STOP",
            stop_price=110.0,
        )

        broker.cancel_client_order("entry-2", event="t1")
        fills = broker.process_bar(100.0, 120.0, 99.0, 115.0, event="t2")

        self.assertEqual(OrderStatus.CANCELED, order.status)
        self.assertEqual([], fills)

    def test_triggered_stop_limit_can_be_canceled_by_client_identity(self):
        broker, order = self._submit(
            order_id="broker-3",
            client_order_id="entry-3",
            order_type="STOP_LIMIT",
            stop_price=110.0,
            limit_price=100.0,
        )

        first_fills = broker.process_bar(105.0, 111.0, 104.0, 109.0, event="t1")
        self.assertEqual([], first_fills)
        self.assertEqual(OrderStatus.TRIGGERED, order.status)

        broker.cancel_client_order("entry-3", reason="context invalidated", event="t2")
        second_fills = broker.process_bar(99.0, 105.0, 95.0, 101.0, event="t3")

        self.assertEqual(OrderStatus.CANCELED, order.status)
        self.assertEqual([], second_fills)
        self.assertEqual(
            ["CREATED", "ACCEPTED", "TRIGGERED", "CANCELED"],
            [row["status"] for row in order.history],
        )

    def test_unknown_client_identity_fails_closed_without_history_mutation(self):
        broker, order = self._submit(
            order_id="broker-4",
            client_order_id="entry-4",
            order_type="LIMIT",
            limit_price=100.0,
        )
        history_before = broker.snapshot_history()

        with self.assertRaises(KeyError):
            broker.cancel_client_order("missing")

        self.assertEqual(OrderStatus.ACCEPTED, order.status)
        self.assertEqual(history_before, broker.snapshot_history())

    def test_ambiguous_client_identity_fails_closed(self):
        broker = BrokerEmulator()
        first = broker.submit(
            BrokerOrder(id="broker-5a", client_order_id="same", side="BUY", type="LIMIT", limit_price=100.0),
            event="t0",
        )
        second = broker.submit(
            BrokerOrder(id="broker-5b", client_order_id="same", side="BUY", type="STOP", stop_price=110.0),
            event="t0",
        )

        with self.assertRaises(ValueError):
            broker.cancel_client_order("same")

        self.assertEqual(OrderStatus.ACCEPTED, first.status)
        self.assertEqual(OrderStatus.ACCEPTED, second.status)


if __name__ == "__main__":
    unittest.main()
