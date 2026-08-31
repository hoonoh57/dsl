from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine
from axes.axis1_dsl.runtime.axis1_runtime import Axis1DSLRuntime
from axes.axis1_dsl.runtime.dsl_runtime import DSLRuntimeError
from axes.axis1_dsl.runtime.intrabar_lifecycle import (
    IntrabarLifecycleError,
    extract_intrabar_handlers,
)


def runtime_market():
    close = np.asarray([100.0, 101.0, 102.0, 103.0], dtype=float)
    return {
        "open": close.copy(),
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.asarray([1000.0, 1100.0, 1200.0, 1300.0]),
        "date": np.full(len(close), 20260901.0),
        "time": np.asarray([90000.0, 90500.0, 91000.0, 91500.0]),
    }


def backtest_market():
    market = runtime_market()
    return {
        "time": ["20260901090000", "20260901090500", "20260901091000", "20260901091500"],
        "open": market["open"],
        "high": market["high"],
        "low": market["low"],
        "close": market["close"],
        "volume": market["volume"],
        "_meta": {"source": "intrabar-test", "timeframe": "5m", "instrument": "TEST"},
    }


CODE = '''strategy "IntrabarLifecycle" {
    timeframe = "5m"
    state peak = 100
    state fill_count = 0
    state last_fill = 0
    on_tick {
        if (tick.price > peak) {
            set peak = tick.price
        }
    }
    on_fill {
        set fill_count = fill_count + 1
        set last_fill = fill.price
    }
}'''


class Axis1IntrabarLifecycleTests(unittest.TestCase):
    def test_tick_and_fill_are_provisional_until_commit_and_rollback_restores_exactly(self):
        compiled = Axis1DSLRuntime.compile(CODE, runtime_market())
        self.assertEqual(tuple(item["kind"] for item in compiled.intrabar_handlers), ("on_tick", "on_fill"))
        session = Axis1DSLRuntime.open_intrabar_session(compiled)

        self.assertEqual(session.committed_state(), {"peak": 100.0, "fill_count": 0.0, "last_fill": 0.0})
        session.begin_bar("20260901092000")
        session.on_tick(price=105, volume=20, time="20260901092100")
        self.assertEqual(session.provisional_state()["peak"], 105.0)
        self.assertEqual(session.committed_state()["peak"], 100.0)
        session.on_fill(price=104.5, quantity=2, side="BUY", order_id="A1")
        provisional = session.provisional_state()
        self.assertEqual(provisional["fill_count"], 1.0)
        self.assertEqual(provisional["last_fill"], 104.5)

        rolled_back = session.rollback_bar()
        self.assertEqual(rolled_back, {"peak": 100.0, "fill_count": 0.0, "last_fill": 0.0})
        self.assertEqual(session.revision, 0)

        session.begin_bar("20260901092500")
        session.on_tick(price=106, volume=10)
        session.on_fill(price=105.5, quantity=1, side="BUY", order_id="A2")
        committed = session.commit_bar()
        self.assertEqual(committed, {"peak": 106.0, "fill_count": 1.0, "last_fill": 105.5})
        self.assertEqual(session.revision, 1)

    def test_fill_observes_prior_tick_provisional_state_and_events_are_ordered(self):
        code = '''strategy "OrderedIntrabar" {
    timeframe = "5m"
    state peak = 100
    state fill_above_peak = false
    on_tick {
        if (tick.price > peak) {
            set peak = tick.price
        }
    }
    on_fill {
        set fill_above_peak = fill.price >= peak
    }
}'''
        compiled = Axis1DSLRuntime.compile(code, runtime_market())
        session = Axis1DSLRuntime.open_intrabar_session(compiled)
        session.begin_bar("B1")
        session.on_tick(price=110)
        session.on_fill(price=109, quantity=1, side="BUY")
        self.assertFalse(session.provisional_state()["fill_above_peak"])
        session.on_fill(price=111, quantity=1, side="BUY")
        self.assertTrue(session.provisional_state()["fill_above_peak"])
        session.commit_bar()
        events = [item["event"] for item in session.audit]
        self.assertEqual(events, ["BEGIN", "ON_TICK", "ON_FILL", "ON_FILL", "COMMIT"])

    def test_failed_event_is_atomic_and_does_not_corrupt_open_bar(self):
        code = '''strategy "AtomicIntrabar" {
    timeframe = "5m"
    state mode = "READY"
    on_fill {
        if (fill.side == "BUY") {
            set mode = fill.quantity
        }
    }
}'''
        lowered = extract_intrabar_handlers(code)
        session = lowered.program.new_session({"mode": "READY"})
        session.begin_bar("B1")
        with self.assertRaises(IntrabarLifecycleError) as ctx:
            session.on_fill(price=100, quantity=2, side="BUY")
        self.assertEqual(ctx.exception.code, "INTRABAR_STATE_TYPE_CHANGE")
        self.assertEqual(session.provisional_state(), {"mode": "READY"})
        self.assertEqual(session.committed_state(), {"mode": "READY"})
        session.rollback_bar()

    def test_fail_closed_for_unsafe_handler_contracts(self):
        cases = (
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_tick {\n        set y = tick.price\n    }\n}''', "INTRABAR_TARGET_NOT_STATE"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_tick {\n        set x = unknown + 1\n    }\n}''', "INTRABAR_FREE_VARIABLE"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_tick {\n        set x = fill.price\n    }\n}''', "BAD_TICK_FIELD"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_fill {\n        set x = tick.price\n    }\n}''', "BAD_FILL_FIELD"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_tick {\n        set x = math.abs(x)\n    }\n}''', "BAD_INTRABAR_EXPRESSION_NODE"),
            ('''strategy "Bad" {\n    timeframe = "5m"\n    state x = 0\n    on_tick {\n        set x = tick.price\n    }\n    on_tick {\n        set x = tick.price\n    }\n}''', "DUPLICATE_INTRABAR_HANDLER"),
        )
        for source, error_code in cases:
            with self.subTest(error_code=error_code):
                with self.assertRaises(IntrabarLifecycleError) as ctx:
                    extract_intrabar_handlers(source)
                self.assertEqual(ctx.exception.code, error_code)

    def test_bar_transaction_lifecycle_is_fail_closed(self):
        program = extract_intrabar_handlers(CODE).program
        session = program.new_session({"peak": 100.0, "fill_count": 0.0, "last_fill": 0.0})
        with self.assertRaises(IntrabarLifecycleError):
            session.on_tick(price=101)
        session.begin_bar("B1")
        with self.assertRaises(IntrabarLifecycleError):
            session.begin_bar("B2")
        session.commit_bar()
        with self.assertRaises(IntrabarLifecycleError):
            session.commit_bar()
        with self.assertRaises(IntrabarLifecycleError):
            session.rollback_bar()

    def test_batch_backtest_rejects_intrabar_strategy_without_event_tape(self):
        with self.assertRaises(DSLRuntimeError) as ctx:
            Axis1BacktestEngine.run(
                CODE,
                market=backtest_market(),
                data_timeframe="5m",
                settings={"commission_pct": 0.0, "sell_tax_pct": 0.0},
            )
        self.assertIn("event tape", str(ctx.exception))

    def test_intrabar_feature_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.runtime.intrabar_lifecycle as lifecycle
        import axes.axis1_dsl.runtime.axis1_runtime as runtime
        import axes.axis1_dsl.execution.axis1_backtest as backtest

        for module in (lifecycle, runtime, backtest):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
