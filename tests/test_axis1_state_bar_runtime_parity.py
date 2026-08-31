from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np

from core import bar_runtime as legacy_bar
from core import dsl_parser as legacy_parser
from core import state as legacy_state
from axes.axis1_dsl.core import dsl_parser as axis1_parser
from axes.axis1_dsl.runtime import bar_runtime as axis1_bar
from axes.axis1_dsl.runtime import state as axis1_state


class Axis1StateBarRuntimeParityTests(unittest.TestCase):
    def assert_array_equal_nan(self, actual, expected):
        actual = np.asarray(actual)
        expected = np.asarray(expected)
        self.assertEqual(actual.dtype, expected.dtype)
        self.assertEqual(actual.shape, expected.shape)
        np.testing.assert_array_equal(actual, expected)

    def test_state_primitives_match_legacy(self):
        condition = np.array([False, True, True, False, False, True, False], dtype=bool)
        reset = np.array([False, False, False, True, False, False, False], dtype=bool)
        bullish = np.array([False, True, False, False, True, False, False], dtype=bool)
        bearish = np.array([False, False, False, True, False, False, True], dtype=bool)

        calls = (
            ("edge", (condition,)),
            ("falling_edge", (condition,)),
            ("ready_after", (condition, 2)),
            ("hold", (condition, 2)),
            ("persist", (condition, 2)),
            ("latch", (condition, reset, False)),
            ("count", (condition, reset)),
            ("regime", (bullish, bearish, 0)),
        )
        for name, args in calls:
            with self.subTest(name=name):
                expected = getattr(legacy_state.CoreStateLib, name)(*args)
                actual = getattr(axis1_state.CoreStateLib, name)(*args)
                self.assert_array_equal_nan(actual, expected)

    def test_state_fail_closed_errors_match_legacy(self):
        cases = (
            ("latch", (np.array([True]), np.array([False, True]), False)),
            ("count", (np.array([True]), np.array([False, True]))),
            ("regime", (np.array([True]), np.array([False]), 2)),
        )
        for name, args in cases:
            with self.subTest(name=name):
                with self.assertRaises(ValueError) as legacy_ctx:
                    getattr(legacy_state.CoreStateLib, name)(*args)
                with self.assertRaises(ValueError) as axis1_ctx:
                    getattr(axis1_state.CoreStateLib, name)(*args)
                self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_persistent_on_bar_execution_matches_legacy(self):
        source = '''strategy "StateParity" {
            timeframe = "1m"
            state armed = false
            state count = 0
            trigger = close > open
            on_bar {
                if (trigger) {
                    set armed = true
                    set count = count + 1
                }
                else {
                    set armed = false
                }
            }
            enter = armed
            on(enter) { order.buy() }
        }'''
        legacy_doc = legacy_parser.DSLParser.parse(source)
        axis1_doc = axis1_parser.DSLParser.parse(source)
        open_values = np.array([10.0, 11.0, 10.0, 13.0, 12.0])
        close_values = np.array([11.0, 10.0, 12.0, 12.0, 14.0])
        trigger = close_values > open_values
        legacy_values = {"open": open_values.copy(), "close": close_values.copy(), "trigger": trigger.copy()}
        axis1_values = {"open": open_values.copy(), "close": close_values.copy(), "trigger": trigger.copy()}

        expected_state = legacy_bar.execute_on_bar(
            legacy_values,
            legacy_doc.states,
            legacy_doc.on_bar,
            len(close_values),
        )
        actual_state = axis1_bar.execute_on_bar(
            axis1_values,
            axis1_doc.states,
            axis1_doc.on_bar,
            len(close_values),
        )

        self.assertEqual(actual_state, expected_state)
        self.assertEqual(set(axis1_values), set(legacy_values))
        for name in legacy_values:
            expected = legacy_values[name]
            actual = axis1_values[name]
            if isinstance(expected, np.ndarray):
                self.assert_array_equal_nan(actual, expected)
            else:
                self.assertEqual(actual, expected)

    def test_bar_expression_context_and_errors_match_legacy(self):
        values = {"close": np.array([10.0, 11.0, 12.0])}
        context = {"ctx.market.regime": np.array([-1.0, 1.0, 1.0])}
        for index in range(3):
            legacy_eval = legacy_bar.BarExpression(values, {}, index, context_values=context)
            axis1_eval = axis1_bar.BarExpression(values, {}, index, context_values=context)
            self.assertEqual(
                axis1_eval.evaluate("ctx.market.regime > 0 and close >= 11"),
                legacy_eval.evaluate("ctx.market.regime > 0 and close >= 11"),
            )

        for expression in ("missing > 0", "ctx.market.unknown > 0", "close[-1] > 0"):
            with self.subTest(expression=expression):
                with self.assertRaises(legacy_bar.BarRuntimeError) as legacy_ctx:
                    legacy_bar.BarExpression(values, {}, 1, context_values=context).evaluate(expression)
                with self.assertRaises(axis1_bar.BarRuntimeError) as axis1_ctx:
                    axis1_bar.BarExpression(values, {}, 1, context_values=context).evaluate(expression)
                self.assertEqual(str(axis1_ctx.exception), str(legacy_ctx.exception))

    def test_axis1_runtime_has_no_legacy_core_runtime_import(self):
        for module in (axis1_state, axis1_bar):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core.", source)
            self.assertNotIn("import core.", source)


if __name__ == "__main__":
    unittest.main()
