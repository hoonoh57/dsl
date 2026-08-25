import unittest
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.capabilities import capability_markdown
from core.dsl_parser import DSLParseError, DSLParser
from core.dsl_runtime import DSLRuntimeError, ExpressionEvaluator
from core.function_registry import FUNCTION_SPECS
from core.prompt_template import generate_full_llm_prompt, playbook_hash


ROOT = Path(__file__).resolve().parent
PLAYBOOK = ROOT / "QUANT_DSL_PLAYBOOK.md"


class Stage1CapabilityBoundaryTest(unittest.TestCase):
    def evaluator(self):
        size = 12
        close = np.arange(size, dtype=float) + 100.0
        values = {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.ones(size, dtype=float),
            "amount": close,
            "open_interest": np.zeros(size, dtype=float),
            "date": np.arange(20260101, 20260101 + size, dtype=float),
            "time": np.zeros(size, dtype=float),
        }
        return ExpressionEvaluator(values, size)

    def test_manifest_is_generated_from_exact_runtime_registry(self):
        evaluator = self.evaluator()
        self.assertEqual(set(FUNCTION_SPECS), set(evaluator.functions))
        manifest = capability_markdown()
        for spec in FUNCTION_SPECS.values():
            self.assertIn(spec.signature, manifest)
        self.assertNotIn("ta.bbands", manifest)
        self.assertNotIn("request.security", manifest)
        self.assertNotIn("plot(", manifest)

    def test_playbook_explicitly_withholds_future_dsl20_capabilities(self):
        text = PLAYBOOK.read_text(encoding="utf-8")
        self.assertIn("## Stage 1 명시적 비지원 기능", text)
        for token in (
            "quantity",
            "부분 체결",
            "피라미딩",
            "on_tick",
            "on_fill",
            "사용자 함수",
            "for",
            "while",
            "tuple",
            "request.security",
            "multi-symbol",
            "lookahead",
            "plot",
            "line",
            "box",
            "label",
            "Chart SSOT",
        ):
            self.assertIn(token, text)

    def test_parser_and_semantic_fail_closed_on_withheld_syntax(self):
        quantity = '''strategy "NoQuantity" {
            timeframe = "1d"
            signal = close > 0
            on(signal) { order.buy(type = "MARKET", quantity = 2) }
        }'''
        with self.assertRaisesRegex(DSLParseError, "quantity"):
            DSLParser.parse(quantity)

        on_tick = '''strategy "NoTick" {
            timeframe = "1d"
            on_tick { close > 0 }
        }'''
        with self.assertRaisesRegex(DSLParseError, "인식할 수 없는 문장"):
            DSLParser.parse(on_tick)

        drawing = '''strategy "NoDirectDrawing" {
            timeframe = "1d"
            plot(close)
        }'''
        with self.assertRaisesRegex(DSLParseError, "인식할 수 없는 문장"):
            DSLParser.parse(drawing)

        tuple_output = '''strategy "NoTuple" {
            timeframe = "1d"
            a, b = ta.macd(close)
        }'''
        with self.assertRaisesRegex(DSLParseError, "인식할 수 없는 문장"):
            DSLParser.parse(tuple_output)

        external_symbol = '''strategy "NoExternalSymbol" {
            timeframe = "1d"
            other = request.security("005930", "1d", close)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "지원하지 않는 함수"):
            BacktestEngine.run(external_symbol)

    def test_published_scalar_parameter_values_fail_closed(self):
        zero_period = '''strategy "ZeroPeriod" {
            timeframe = "1d"
            input period = 0
            x = ta.sma(close, period)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "ta.sma period은 1 이상의 정수"):
            BacktestEngine.run(zero_period)

        fractional_period = '''strategy "FractionalPeriod" {
            timeframe = "1d"
            input period = 2.5
            x = ta.ema(close, period)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "ta.ema period은 1 이상의 정수"):
            BacktestEngine.run(fractional_period)

        bad_method = '''strategy "BadMethod" {
            timeframe = "1d"
            x = ta.ma(close, 5, "typo")
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "ta.ma method"):
            BacktestEngine.run(bad_method)

        bad_phase = '''strategy "BadPhase" {
            timeframe = "1d"
            x = ta.jma(close, 7, 150, 2)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "phase는 -100~100"):
            BacktestEngine.run(bad_phase)

        zero_persist = '''strategy "ZeroPersist" {
            timeframe = "1d"
            signal = state.persist(close > open, 0)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "state.persist bars은 1 이상의 정수"):
            BacktestEngine.run(zero_persist)

        zero_mtf = '''strategy "ZeroMtf" {
            timeframe = "1d"
            x = mtf.close("0d")
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "MTF 주기는 1 이상"):
            BacktestEngine.run(zero_mtf)

    def test_llm_prompt_carries_playbook_hash_manifest_and_withholding_boundary(self):
        prompt = generate_full_llm_prompt("테스트 전략", artifact_type="strategy")
        self.assertIn(playbook_hash(), prompt)
        self.assertIn("## 실행기 Capability Manifest", prompt)
        self.assertIn("## Stage 1 명시적 비지원 기능", prompt)
        self.assertIn("현재 Capability가 아니다. LLM은 생성하지 않는다.", prompt)


if __name__ == "__main__":
    unittest.main()
