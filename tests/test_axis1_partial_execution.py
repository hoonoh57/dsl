from __future__ import annotations

from pathlib import Path
import unittest

from axes.axis1_dsl.execution.broker import BrokerEmulator, BrokerOrder
from axes.axis1_dsl.execution.partial_execution import (
    PartialExecutionError,
    PartialExecutionSession,
    PartialFillBroker,
    PartialFillOrder,
    PartialOrderStatus,
)
from axes.axis1_dsl.runtime.intrabar_lifecycle import extract_intrabar_handlers


class Axis1PartialExecutionTests(unittest.TestCase):
    def test_full_fill_preserves_existing_lifecycle_shape(self):
        legacy = BrokerEmulator()
        old = legacy.submit(BrokerOrder(id="legacy", side="BUY", quantity=10), event="t0")
        legacy.fill(old.id, 101.5, quantity=10, event="t1")

        broker = PartialFillBroker()
        new = broker.submit(PartialFillOrder(id="new", side="BUY", quantity=10), event="t0")
        fill = broker.fill(new.id, 101.5, 10, event="t1")

        self.assertEqual(
            [row["status"] for row in legacy.snapshot_history()],
            [row["status"] for row in broker.snapshot_history()],
        )
        self.assertEqual(new.status, PartialOrderStatus.FILLED)
        self.assertEqual(fill.cumulative_quantity, 10.0)
        self.assertEqual(fill.remaining_quantity, 0.0)
        self.assertEqual(new.average_fill_price, 101.5)

    def test_partial_fills_track_cumulative_remaining_and_weighted_price(self):
        broker = PartialFillBroker()
        order = broker.submit(PartialFillOrder(id="p1", side="BUY", quantity=10))

        first = broker.fill(order.id, 100.0, 4.0, event="f1")
        self.assertEqual(order.status, PartialOrderStatus.PARTIALLY_FILLED)
        self.assertEqual(first.cumulative_quantity, 4.0)
        self.assertEqual(first.remaining_quantity, 6.0)
        self.assertAlmostEqual(first.average_fill_price, 100.0)
        self.assertIn(order, broker.active_orders())

        second = broker.fill(order.id, 102.0, 6.0, event="f2")
        self.assertEqual(order.status, PartialOrderStatus.FILLED)
        self.assertEqual(second.cumulative_quantity, 10.0)
        self.assertEqual(second.remaining_quantity, 0.0)
        self.assertAlmostEqual(second.average_fill_price, 101.2)
        self.assertEqual(len(order.fills), 2)
        self.assertNotIn(order, broker.active_orders())

    def test_partial_cancel_preserves_executed_quantity_and_cancels_only_remainder(self):
        broker = PartialFillBroker()
        order = broker.submit(PartialFillOrder(id="p2", side="BUY", quantity=8))
        broker.fill(order.id, 100.0, 3.0)
        broker.cancel(order.id, reason="stop remainder")

        self.assertEqual(order.status, PartialOrderStatus.CANCELED)
        self.assertEqual(order.filled_quantity, 3.0)
        self.assertEqual(order.remaining_quantity, 5.0)
        self.assertEqual(len(order.fills), 1)
        with self.assertRaises(PartialExecutionError) as ctx:
            broker.fill(order.id, 101.0, 1.0)
        self.assertEqual(ctx.exception.code, "BAD_FILL_TRANSITION")

    def test_overfill_is_rejected_without_mutating_order(self):
        broker = PartialFillBroker()
        order = broker.submit(PartialFillOrder(id="p3", side="BUY", quantity=5))
        broker.fill(order.id, 100.0, 2.0)
        before = order.public_dict()
        history_size = len(broker.history)

        with self.assertRaises(PartialExecutionError) as ctx:
            broker.fill(order.id, 101.0, 4.0)
        self.assertEqual(ctx.exception.code, "ORDER_OVERFILL")
        self.assertEqual(order.public_dict(), before)
        self.assertEqual(len(broker.history), history_size)

    def test_partial_entry_and_multiple_partial_exit_orders_account_exact_quantity(self):
        session = PartialExecutionSession(initial_cash=10_000.0)
        entry = session.submit_entry("entry-1", "BUY", 10)
        session.fill(entry.id, 100.0, 4.0, event="e1")
        second = session.fill(entry.id, 102.0, 6.0, event="e2")
        self.assertEqual(second["position"]["quantity"], 10.0)
        self.assertAlmostEqual(second["position"]["average_entry_price"], 101.2)

        exit1 = session.submit_exit("exit-1", 4)
        first_exit = session.fill(exit1.id, 110.0, 2.0, event="x1")
        self.assertEqual(first_exit["position"]["quantity"], 8.0)
        second_exit = session.fill(exit1.id, 90.0, 2.0, event="x2")
        self.assertEqual(second_exit["position"]["quantity"], 6.0)
        self.assertEqual(session.broker.orders[exit1.id].status, PartialOrderStatus.FILLED)

        exit2 = session.submit_exit("exit-2")
        session.fill(exit2.id, 105.0, 3.0, event="x3")
        final = session.fill(exit2.id, 105.0, 3.0, event="x4")
        self.assertEqual(final["position"]["position"], 0)
        self.assertEqual(final["position"]["quantity"], 0.0)
        self.assertEqual(final["position"]["closed_position_count"], 1)

        # 4@100 + 6@102 = average 101.2.  Realized gross:
        # 4 shares split 2@110 + 2@90 => -4.8; remaining 6@105 => +22.8; total +18.
        self.assertAlmostEqual(final["position"]["realized_pnl"], 18.0)
        self.assertEqual([item["quantity"] for item in session.snapshot()["realized_exits"]], [2.0, 2.0, 3.0, 3.0])

    def test_entry_fee_is_allocated_proportionally_across_partial_exits(self):
        session = PartialExecutionSession(initial_cash=10_000.0, commission_pct=1.0, sell_tax_pct=0.0)
        entry = session.submit_entry("entry-fee", "BUY", 10)
        session.fill(entry.id, 100.0, 10.0)
        self.assertAlmostEqual(session.ledger.entry_fee_remaining, 10.0)

        exit_order = session.submit_exit("exit-fee", 10)
        first = session.fill(exit_order.id, 110.0, 4.0)
        self.assertAlmostEqual(first["realized"]["allocated_entry_fee"], 4.0)
        self.assertAlmostEqual(first["position"]["entry_fee_remaining"], 6.0)
        second = session.fill(exit_order.id, 110.0, 6.0)
        self.assertAlmostEqual(second["realized"]["allocated_entry_fee"], 6.0)
        self.assertAlmostEqual(second["position"]["entry_fee_remaining"], 0.0)

        # Gross 100, entry commission 10, exit commission 11 => net 79.
        self.assertAlmostEqual(second["position"]["realized_pnl"], 79.0)

    def test_position_overexit_and_pyramiding_fail_before_broker_mutation(self):
        session = PartialExecutionSession(initial_cash=10_000.0)
        entry = session.submit_entry("entry", "BUY", 10)
        session.fill(entry.id, 100.0, 5.0)

        with self.assertRaises(PartialExecutionError) as ctx:
            session.submit_entry("entry-2", "BUY", 1)
        self.assertEqual(ctx.exception.code, "PYRAMIDING_NOT_SUPPORTED")
        self.assertNotIn("entry-2", session.broker.orders)

        exit_order = session.submit_exit("exit", 5)
        history_size = len(session.broker.history)
        with self.assertRaises(PartialExecutionError) as ctx:
            session.fill(exit_order.id, 101.0, 6.0)
        self.assertEqual(ctx.exception.code, "POSITION_OVEREXIT")
        self.assertEqual(session.broker.orders[exit_order.id].filled_quantity, 0.0)
        self.assertEqual(len(session.broker.history), history_size)

    def test_each_partial_fill_can_drive_existing_on_fill_provisional_state(self):
        source = '''strategy "PartialFillState" {
    timeframe = "5m"
    state filled = 0
    on_fill {
        set filled = filled + fill.quantity
    }
}'''
        lowered = extract_intrabar_handlers(source)
        intrabar = lowered.program.new_session({"filled": 0.0})
        intrabar.begin_bar("bar-1")

        session = PartialExecutionSession(initial_cash=10_000.0)
        entry = session.submit_entry("entry", "BUY", 5)
        first = session.fill(entry.id, 100.0, 2.0, event="09:00:01")
        intrabar.on_fill(**session.intrabar_fill_event(first))
        second = session.fill(entry.id, 101.0, 3.0, event="09:00:02")
        intrabar.on_fill(**session.intrabar_fill_event(second))

        self.assertEqual(intrabar.provisional_state()["filled"], 5.0)
        self.assertEqual(intrabar.committed_state()["filled"], 0.0)
        intrabar.rollback_bar()
        self.assertEqual(intrabar.committed_state()["filled"], 0.0)
        # Actual exchange fills remain authoritative even when strategy state rolls back.
        self.assertEqual(session.ledger.quantity, 5.0)

    def test_partial_execution_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.execution.partial_execution as partial

        text = Path(partial.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", text)
        self.assertNotIn("import core", text)


if __name__ == "__main__":
    unittest.main()
