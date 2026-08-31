from __future__ import annotations

from pathlib import Path
import unittest

from axes.axis1_dsl.execution.partial_execution import PartialExecutionError, PartialExecutionSession
from axes.axis1_dsl.execution.pyramiding_execution import PyramidingExecutionSession
from axes.axis1_dsl.runtime.intrabar_lifecycle import extract_intrabar_handlers


class Axis1PyramidingExecutionTests(unittest.TestCase):
    def test_same_direction_entry_orders_create_distinct_lots_and_weight_aggregate(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=3)
        first = session.submit_entry("entry-1", "BUY", 4)
        session.fill(first.id, 100.0, 2.0, event="e1")
        session.fill(first.id, 102.0, 2.0, event="e2")

        second = session.submit_entry("entry-2", "BUY", 6)
        result = session.fill(second.id, 110.0, 6.0, event="e3")

        position = result["position"]
        self.assertEqual(position["position"], 1)
        self.assertEqual(position["quantity"], 10.0)
        self.assertEqual(position["active_lot_count"], 2)
        self.assertAlmostEqual(position["average_entry_price"], 106.4)
        lots = position["lots"]
        self.assertEqual([item["lot_id"] for item in lots], ["lot-1", "lot-2"])
        self.assertAlmostEqual(lots[0]["average_entry_price"], 101.0)
        self.assertAlmostEqual(lots[1]["average_entry_price"], 110.0)
        self.assertEqual(lots[0]["cumulative_entry_quantity"], 4.0)

    def test_fifo_partial_exit_allocates_across_lots_deterministically(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=3)
        first = session.submit_entry("entry-1", "BUY", 4)
        session.fill(first.id, 100.0, 4.0)
        second = session.submit_entry("entry-2", "BUY", 6)
        session.fill(second.id, 110.0, 6.0)

        exit_order = session.submit_exit("exit-1", 5)
        first_slice = session.fill(exit_order.id, 120.0, 2.0, event="x1")
        self.assertEqual([item["lot_id"] for item in first_slice["realized"]], ["lot-1"])
        self.assertEqual(first_slice["position"]["quantity"], 8.0)

        second_slice = session.fill(exit_order.id, 120.0, 3.0, event="x2")
        self.assertEqual([item["lot_id"] for item in second_slice["realized"]], ["lot-1", "lot-2"])
        self.assertEqual([item["quantity"] for item in second_slice["realized"]], [2.0, 1.0])
        self.assertEqual(second_slice["position"]["quantity"], 5.0)
        self.assertEqual(second_slice["position"]["active_lot_count"], 1)
        self.assertAlmostEqual(second_slice["position"]["average_entry_price"], 110.0)
        # Gross: 4*(120-100) + 1*(120-110) = 90.
        self.assertAlmostEqual(second_slice["position"]["realized_pnl"], 90.0)

    def test_targeted_exit_changes_only_selected_lot(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=3)
        first = session.submit_entry("entry-1", "BUY", 4)
        session.fill(first.id, 100.0, 4.0)
        second = session.submit_entry("entry-2", "BUY", 6)
        session.fill(second.id, 110.0, 6.0)

        exit_order = session.submit_exit("exit-lot2", 2, lot_id="lot-2")
        result = session.fill(exit_order.id, 120.0, 2.0)
        self.assertEqual(len(result["realized"]), 1)
        self.assertEqual(result["realized"][0]["lot_id"], "lot-2")
        lots = {item["lot_id"]: item for item in result["position"]["lots"]}
        self.assertEqual(lots["lot-1"]["quantity"], 4.0)
        self.assertEqual(lots["lot-2"]["quantity"], 4.0)
        self.assertAlmostEqual(result["position"]["realized_pnl"], 20.0)

    def test_entry_and_exit_fees_are_allocated_per_lot(self):
        session = PyramidingExecutionSession(
            initial_cash=20_000.0,
            commission_pct=1.0,
            sell_tax_pct=0.0,
            max_lots=3,
        )
        first = session.submit_entry("entry-1", "BUY", 4)
        session.fill(first.id, 100.0, 4.0)
        second = session.submit_entry("entry-2", "BUY", 6)
        session.fill(second.id, 110.0, 6.0)
        self.assertAlmostEqual(session.ledger.entry_fee_remaining, 10.6)

        exit_order = session.submit_exit("exit", 5)
        result = session.fill(exit_order.id, 120.0, 5.0)
        realized = result["realized"]
        self.assertEqual([item["lot_id"] for item in realized], ["lot-1", "lot-2"])
        self.assertAlmostEqual(sum(item["allocated_entry_fee"] for item in realized), 5.1)
        self.assertAlmostEqual(sum(item["exit_fee"] for item in realized), 6.0)
        self.assertAlmostEqual(result["position"]["entry_fee_remaining"], 5.5)
        self.assertAlmostEqual(result["position"]["realized_pnl"], 78.9)

    def test_pyramiding_limit_and_opposite_direction_fail_before_broker_mutation(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=2)
        first = session.submit_entry("entry-1", "BUY", 1)
        session.fill(first.id, 100.0, 1.0)
        second = session.submit_entry("entry-2", "BUY", 1)
        session.fill(second.id, 101.0, 1.0)

        history_size = len(session.broker.history)
        with self.assertRaises(PartialExecutionError) as ctx:
            session.submit_entry("entry-3", "BUY", 1)
        self.assertEqual(ctx.exception.code, "PYRAMIDING_LIMIT")
        self.assertNotIn("entry-3", session.broker.orders)
        self.assertEqual(len(session.broker.history), history_size)

        with self.assertRaises(PartialExecutionError) as ctx:
            session.submit_entry("short-while-long", "SELL_SHORT", 1)
        self.assertEqual(ctx.exception.code, "HEDGING_NOT_SUPPORTED")
        self.assertNotIn("short-while-long", session.broker.orders)

    def test_flatten_then_opposite_direction_starts_new_cycle(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=2)
        first = session.submit_entry("long-1", "BUY", 2)
        session.fill(first.id, 100.0, 2.0)
        second = session.submit_entry("long-2", "BUY", 3)
        session.fill(second.id, 101.0, 3.0)
        exit_order = session.submit_exit("flatten")
        flat = session.fill(exit_order.id, 105.0, 5.0)
        self.assertEqual(flat["position"]["position"], 0)
        self.assertEqual(flat["position"]["closed_cycle_count"], 1)

        short = session.submit_entry("short-1", "SELL_SHORT", 2)
        result = session.fill(short.id, 104.0, 2.0)
        self.assertEqual(result["position"]["position"], -1)
        self.assertEqual(result["position"]["active_lot_count"], 1)

    def test_target_lot_overexit_is_atomic(self):
        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=2)
        entry = session.submit_entry("entry", "BUY", 4)
        session.fill(entry.id, 100.0, 4.0)
        exit_order = session.submit_exit("exit", 4, lot_id="lot-1")
        before_order = exit_order.public_dict()
        before_position = session.ledger.position_snapshot()
        history_size = len(session.broker.history)

        with self.assertRaises(PartialExecutionError) as ctx:
            session.fill(exit_order.id, 101.0, 5.0)
        self.assertEqual(ctx.exception.code, "LOT_OVEREXIT")
        self.assertEqual(exit_order.public_dict(), before_order)
        self.assertEqual(session.ledger.position_snapshot(), before_position)
        self.assertEqual(len(session.broker.history), history_size)

    def test_each_pyramiding_fill_can_drive_existing_on_fill_state(self):
        source = '''strategy "PyramidFillState" {
    timeframe = "5m"
    state filled = 0
    on_fill {
        set filled = filled + fill.quantity
    }
}'''
        program = extract_intrabar_handlers(source).program
        intrabar = program.new_session({"filled": 0.0})
        intrabar.begin_bar("bar-1")

        session = PyramidingExecutionSession(initial_cash=20_000.0, max_lots=2)
        first = session.submit_entry("entry-1", "BUY", 2)
        first_fill = session.fill(first.id, 100.0, 2.0, event="09:00:01")
        intrabar.on_fill(**session.intrabar_fill_event(first_fill))
        second = session.submit_entry("entry-2", "BUY", 3)
        second_fill = session.fill(second.id, 101.0, 3.0, event="09:00:02")
        intrabar.on_fill(**session.intrabar_fill_event(second_fill))

        self.assertEqual(intrabar.provisional_state()["filled"], 5.0)
        self.assertEqual(intrabar.committed_state()["filled"], 0.0)
        intrabar.rollback_bar()
        self.assertEqual(session.ledger.quantity, 5.0)

    def test_step5_7_single_position_session_still_rejects_pyramiding(self):
        session = PartialExecutionSession(initial_cash=10_000.0)
        first = session.submit_entry("entry-1", "BUY", 2)
        session.fill(first.id, 100.0, 2.0)
        with self.assertRaises(PartialExecutionError) as ctx:
            session.submit_entry("entry-2", "BUY", 1)
        self.assertEqual(ctx.exception.code, "PYRAMIDING_NOT_SUPPORTED")

    def test_pyramiding_layer_does_not_import_frozen_core_or_backtest(self):
        import axes.axis1_dsl.execution.pyramiding_execution as pyramiding

        text = Path(pyramiding.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", text)
        self.assertNotIn("import core", text)
        self.assertNotIn("BacktestEngine", text)


if __name__ == "__main__":
    unittest.main()
