from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.execution.full_engine_parity import (
    Axis1EventTapeSession,
    verify_backtest_prefix_parity,
    verify_event_tape_batch_stream_parity,
    verify_runtime_prefix_parity,
)
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime


def runtime_market(size=18):
    index = np.arange(size, dtype=float)
    close = 100.0 + np.sin(index * 1.15) * 4.2 + np.cos(index * 0.37) * 1.3 + index * 0.08
    high = close + 1.1 + (index % 3) * 0.1
    low = close - 1.0 - (index % 4) * 0.1
    base = datetime(2026, 9, 1, 9, 0, 0)
    stamps = [base + timedelta(minutes=5 * i) for i in range(size)]
    return {
        "open": close - 0.25,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000.0 + index * 17.0,
        "date": np.asarray([float(item.strftime("%Y%m%d")) for item in stamps]),
        "time": np.asarray([float(item.strftime("%H%M%S")) for item in stamps]),
    }


def backtest_market(size=22):
    values = runtime_market(size)
    base = datetime(2026, 9, 1, 9, 0, 0)
    return {
        "time": [(base + timedelta(minutes=5 * i)).strftime("%Y%m%d%H%M%S") for i in range(size)],
        "open": values["open"],
        "high": values["high"],
        "low": values["low"],
        "close": values["close"],
        "volume": values["volume"],
        "_meta": {"source": "full-engine-parity-test", "timeframe": "5m", "instrument": "TEST"},
    }


class Axis1FullEngineParityTests(unittest.TestCase):
    def test_runtime_prefix_parity_covers_state_mtf_multi_output_and_events(self):
        code = '''strategy "RuntimePrefixParity" {
    timeframe = "5m"
    function mean3(source) {
        total = 0
        for i in range(0, 3) {
            total = total + source[i]
        }
        return total / 3
    }
    basis = mean3(close)
    upper, middle, lower = ta.bbands(basis, 4, 2)
    jma = ta.jma(close, 5, 0, 2)
    parent_close = mtf.close("15m")
    state streak = 0
    on_bar {
        if (close > jma) {
            set streak = streak + 1
        }
        else {
            set streak = 0
        }
    }
    enter = (streak >= 2) and (close > middle)
    exit = ta.crossunder(close, middle)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''
        report = verify_runtime_prefix_parity(code, runtime_market())
        self.assertEqual(report.prefixes_checked, report.bars)
        self.assertEqual(report.event_count, 2)
        self.assertTrue({"basis", "upper", "middle", "lower", "jma", "parent_close", "streak"}.issubset(report.series_checked))

    def test_backtest_prefix_replay_matches_batch_equity_trades_and_broker_history(self):
        code = '''strategy "BacktestPrefixParity" {
    timeframe = "5m"
    fast = ta.sma(close, 2)
    slow = ta.sma(close, 5)
    enter = ta.crossover(fast, slow)
    exit = ta.crossunder(fast, slow)
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_long() }
}'''
        report = verify_backtest_prefix_parity(
            code,
            backtest_market(),
            data_timeframe="5m",
            settings={"commission_pct": 0.0, "sell_tax_pct": 0.0, "slippage_pct": 0.0},
        )
        self.assertEqual(report.prefixes_checked, report.bars - 1)
        self.assertGreater(report.trade_count, 0)
        self.assertGreater(report.broker_history_count, 0)

    def test_event_tape_grouped_and_one_by_one_replay_match(self):
        code = '''strategy "EventTapeParity" {
    timeframe = "5m"
    state filled = 0
    state peak = 0
    on_tick {
        if (tick.price > peak) {
            set peak = tick.price
        }
    }
    on_fill {
        set filled = filled + fill.quantity
    }
}'''
        compiled = Axis1DSLRuntime.compile(code, runtime_market(4))
        tape = (
            {"op": "BEGIN_BAR", "bar_id": "bar-1"},
            {"op": "TICK", "price": 101.0, "volume": 5.0, "time": "09:15:01"},
            {"op": "SUBMIT_ENTRY", "order_id": "entry-1", "side": "BUY", "quantity": 4.0},
            {"op": "FILL", "order_id": "entry-1", "price": 100.0, "quantity": 2.0, "time": "09:15:02"},
            {"op": "FILL", "order_id": "entry-1", "price": 101.0, "quantity": 2.0, "time": "09:15:03"},
            {"op": "SUBMIT_ENTRY", "order_id": "entry-2", "side": "BUY", "quantity": 3.0},
            {"op": "FILL", "order_id": "entry-2", "price": 102.0, "quantity": 3.0, "time": "09:15:04"},
            {"op": "SUBMIT_EXIT", "order_id": "exit-1", "quantity": 5.0},
            {"op": "FILL", "order_id": "exit-1", "price": 103.0, "quantity": 5.0, "time": "09:15:05"},
            {"op": "COMMIT_BAR"},
            {"op": "BEGIN_BAR", "bar_id": "bar-2"},
            {"op": "TICK", "price": 110.0, "volume": 2.0, "time": "09:20:01"},
            {"op": "SUBMIT_EXIT", "order_id": "exit-2", "quantity": 2.0},
            {"op": "FILL", "order_id": "exit-2", "price": 104.0, "quantity": 2.0, "time": "09:20:02"},
            {"op": "ROLLBACK_BAR"},
        )
        report = verify_event_tape_batch_stream_parity(
            compiled,
            tape,
            initial_cash=100_000.0,
            commission_pct=0.0,
            sell_tax_pct=0.0,
        )
        final = report["final"]
        self.assertEqual(report["events"], len(tape))
        self.assertEqual(final["intrabar"]["revision"], 1)
        self.assertFalse(final["intrabar"]["bar_open"])
        self.assertEqual(final["intrabar"]["committed"]["filled"], 12.0)
        self.assertEqual(final["intrabar"]["committed"]["peak"], 101.0)
        # The second-bar strategy state was rolled back, but exchange/accounting
        # execution facts remain authoritative: the remaining 2 shares were exited.
        self.assertEqual(final["execution"]["position"]["position"], 0)
        self.assertEqual(final["execution"]["position"]["quantity"], 0.0)
        self.assertEqual(len(final["execution"]["realized_slices"]), 3)

    def test_event_tape_session_can_be_consumed_incrementally(self):
        code = '''strategy "IncrementalTape" {
    timeframe = "5m"
    state fills = 0
    on_fill {
        set fills = fills + fill.quantity
    }
}'''
        compiled = Axis1DSLRuntime.compile(code, runtime_market(3))
        session = Axis1EventTapeSession(compiled, initial_cash=10_000.0)
        session.apply({"op": "BEGIN_BAR", "bar_id": "live-1"})
        session.apply({"op": "SUBMIT_ENTRY", "order_id": "entry", "side": "BUY", "quantity": 2.0})
        session.apply({"op": "FILL", "order_id": "entry", "price": 100.0, "quantity": 1.0, "time": "t1"})
        self.assertEqual(session.intrabar.provisional_state()["fills"], 1.0)
        self.assertEqual(session.intrabar.committed_state()["fills"], 0.0)
        session.apply({"op": "FILL", "order_id": "entry", "price": 101.0, "quantity": 1.0, "time": "t2"})
        session.apply({"op": "COMMIT_BAR"})
        self.assertEqual(session.intrabar.committed_state()["fills"], 2.0)
        self.assertEqual(session.execution.ledger.quantity, 2.0)

    def test_parity_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.execution.full_engine_parity as parity

        source = Path(parity.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
