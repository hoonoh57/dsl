from __future__ import annotations

from pathlib import Path
import unittest

from core import assignment_flow as legacy_flow
from core import dsl_parser as legacy_parser
from core import dsl_semantic as legacy_semantic
from axes.axis1_dsl.core import assignment_flow as axis1_flow
from axes.axis1_dsl.core import dsl_parser as axis1_parser
from axes.axis1_dsl.core import dsl_semantic as axis1_semantic


VALID_CASES = (
    (
        '''strategy "BasicSemantic" {
            timeframe = "5m"
            input period = 5
            fast = ta.sma(close, period)
            slow = ta.ema(close, 20)
            enter = ta.crossover(fast, slow)
            on(enter) { order.buy(type = "MARKET") }
        }''',
        None,
    ),
    (
        '''strategy "StateSemantic" {
            timeframe = "1d"
            state level = 0
            base = ta.sma(close, 5)
            on_bar {
                if (close > open) {
                    set level = close
                }
                else {
                    set level = open
                }
            }
            dynamic = level + base
            enter = dynamic > close
            on(enter) { order.buy(type = "LIMIT", limit = dynamic) }
        }''',
        None,
    ),
    (
        '''strategy "ContextSemantic" {
            timeframe = "15m"
            regime_ok = ctx.market.regime > 0
            strength_ok = ctx.selection.strength >= 5
            enter = regime_ok and strength_ok
            on(enter) { order.buy(type = "MARKET") }
        }''',
        {"market.regime": "NUMBER", "selection.strength": "NUMBER"},
    ),
)

FAILURE_CASES = (
    (
        '''strategy "Undefined" {
            timeframe = "1d"
            enter = missing_value > 0
            on(enter) { order.buy() }
        }''',
        None,
    ),
    (
        '''strategy "BadArity" {
            timeframe = "1d"
            x = ta.sma(close)
            enter = close > open
            on(enter) { order.buy() }
        }''',
        None,
    ),
    (
        '''strategy "BadType" {
            timeframe = "1d"
            x = ta.sma(close, "five")
            enter = close > open
            on(enter) { order.buy() }
        }''',
        None,
    ),
    (
        '''strategy "OnBarCall" {
            timeframe = "1d"
            state level = 0
            on_bar {
                set level = ta.sma(close, 5)
            }
            enter = level > 0
            on(enter) { order.buy() }
        }''',
        None,
    ),
    (
        '''strategy "MissingContext" {
            timeframe = "1d"
            enter = ctx.market.regime > 0
            on(enter) { order.buy() }
        }''',
        None,
    ),
)

FLOW_CASE = '''strategy "Flow" {
    timeframe = "1d"
    state level = 0
    base = ta.sma(close, 5)
    on_bar {
        if (close > open) {
            set level = close
        }
        else {
            set level = open
        }
    }
    dynamic = level + base
    downstream = dynamic + 1
    enter = downstream > close
    on(enter) { order.buy() }
}'''


def normalize_symbols(values):
    return {
        name: getattr(value, "value", str(value))
        for name, value in values.items()
    }


class Axis1SemanticParityTests(unittest.TestCase):
    def test_assignment_partition_matches_legacy(self):
        legacy_doc = legacy_parser.DSLParser.parse(FLOW_CASE)
        axis1_doc = axis1_parser.DSLParser.parse(FLOW_CASE)
        legacy_before, legacy_after = legacy_flow.partition_assignments(legacy_doc)
        axis1_before, axis1_after = axis1_flow.partition_assignments(axis1_doc)
        self.assertEqual([item.name for item in axis1_before], [item.name for item in legacy_before])
        self.assertEqual([item.name for item in axis1_after], [item.name for item in legacy_after])
        self.assertEqual(
            axis1_flow.collect_bar_output_names(axis1_doc.on_bar),
            legacy_flow.collect_bar_output_names(legacy_doc.on_bar),
        )

    def test_valid_semantic_results_match_legacy(self):
        for source, context_types in VALID_CASES:
            with self.subTest(strategy=source.split('"', 2)[1]):
                legacy_doc = legacy_parser.DSLParser.parse(source)
                axis1_doc = axis1_parser.DSLParser.parse(source)
                expected = legacy_semantic.DSLSemanticAnalyzer.analyze(
                    legacy_doc, context_feature_types=context_types
                )
                actual = axis1_semantic.DSLSemanticAnalyzer.analyze(
                    axis1_doc, context_feature_types=context_types
                )
                self.assertEqual(normalize_symbols(actual), normalize_symbols(expected))

    def test_fail_closed_diagnostics_match_legacy(self):
        for source, context_types in FAILURE_CASES:
            with self.subTest(strategy=source.split('"', 2)[1]):
                legacy_doc = legacy_parser.DSLParser.parse(source)
                axis1_doc = axis1_parser.DSLParser.parse(source)
                with self.assertRaises(legacy_semantic.DSLSemanticError) as legacy_ctx:
                    legacy_semantic.DSLSemanticAnalyzer.analyze(
                        legacy_doc, context_feature_types=context_types
                    )
                with self.assertRaises(axis1_semantic.DSLSemanticError) as axis1_ctx:
                    axis1_semantic.DSLSemanticAnalyzer.analyze(
                        axis1_doc, context_feature_types=context_types
                    )
                expected = legacy_ctx.exception
                actual = axis1_ctx.exception
                self.assertEqual(str(actual), str(expected))
                self.assertEqual(actual.code, expected.code)
                self.assertEqual(actual.line, expected.line)
                self.assertEqual(actual.column, expected.column)

    def test_axis1_semantic_boundary_has_no_legacy_core_runtime_import(self):
        for module in (axis1_flow, axis1_semantic):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
