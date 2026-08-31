from __future__ import annotations

from dataclasses import asdict, fields
from pathlib import Path
import unittest

from core import dsl_parser as legacy
from axes.axis1_dsl.core import dsl_parser as axis1


SUCCESS_CASES = (
    '''strategy "Basic" {
        timeframe = "5m"
        fast = ta.sma(close, 5)
        slow = ta.sma(close, 20)
        enter = ta.crossover(fast, slow)
        on(enter) { order.buy(type = "MARKET") }
    }''',
    '''strategy "Stateful" {
        timeframe = "1d"
        input period = 7
        state armed = false
        trigger = close > open
        on_bar {
            if (trigger) {
                set armed = true
            }
            else {
                set armed = false
            }
        }
        enter = armed
        on(enter) { order.buy(type = "LIMIT", limit = close, tif = "DAY", id = "entry") }
    }''',
    '''// comment before strategy is stripped
    strategy "Orders" {
        timeframe = "15m"
        enter = close > open
        leave = close < open
        on(enter) {
            order.buy(type = "STOP_LIMIT", stop = high, limit = high, id = "e", oco = "g")
        }
        on(leave) { order.close_position() }
    }''',
)

FAILURE_CASES = (
    "",
    'timeframe = "1d"',
    '''strategy "Unknown" {
        timeframe = "1d"
        if close > open
    }''',
    '''strategy "Reserved" {
        timeframe = "1d"
        ctx = close
    }''',
    '''strategy "BadOrder" {
        timeframe = "1d"
        enter = close > open
        on(enter) { order.buy(type = "TELEPORT") }
    }''',
    '''strategy "Cancel" {
        timeframe = "1d"
        cancel = close > open
        on(cancel) { order.cancel() }
    }''',
)


class Axis1ParserParityTests(unittest.TestCase):
    def test_ast_contract_fields_match_legacy(self):
        node_names = (
            "AssignmentNode",
            "OrderNode",
            "EventNode",
            "StateNode",
            "SetNode",
            "IfNode",
            "StrategyNode",
        )
        for name in node_names:
            legacy_fields = tuple(item.name for item in fields(getattr(legacy, name)))
            axis1_fields = tuple(item.name for item in fields(getattr(axis1, name)))
            self.assertEqual(axis1_fields, legacy_fields, name)

    def test_successful_parse_results_match_legacy(self):
        for source in SUCCESS_CASES:
            with self.subTest(strategy=source.split('"', 2)[1] if '"' in source else "unknown"):
                expected = legacy.DSLParser.parse(source)
                actual = axis1.DSLParser.parse(source)
                self.assertEqual(asdict(actual), asdict(expected))

    def test_fail_closed_diagnostics_match_legacy(self):
        for source in FAILURE_CASES:
            with self.subTest(source=source[:40]):
                with self.assertRaises(legacy.DSLParseError) as legacy_ctx:
                    legacy.DSLParser.parse(source)
                with self.assertRaises(axis1.DSLParseError) as axis1_ctx:
                    axis1.DSLParser.parse(source)
                expected = legacy_ctx.exception
                actual = axis1_ctx.exception
                self.assertEqual(str(actual), str(expected))
                self.assertEqual(actual.code, expected.code)
                self.assertEqual(actual.line, expected.line)
                self.assertEqual(actual.column, expected.column)

    def test_axis1_parser_has_no_legacy_core_runtime_import(self):
        source = Path(axis1.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
