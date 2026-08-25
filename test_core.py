import unittest
import json
from unittest.mock import patch
import os
import inspect
import tempfile
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntime
from core.dsl_runtime import DSLRuntimeError
from core.dsl_parser import DSLParseError, DSLParser
from core.indicators import CoreTALib
from core.state import CoreStateLib
from core.transpiler import CodeTranspiler
from core.kiwoom_rest import KiwoomAPIError, KiwoomRESTClient, load_env
from core.db import get_all_strategies, init_db
from core.capabilities import TA_FUNCTIONS
from core.prompt_template import generate_full_llm_prompt, playbook_hash
from main import (BacktestRequest, PromptPackageRequest, SourceValidateRequest, TranspileRequest,
                  ValidateChartRequest, artifact_tree, build_llm_prompt, run_backtest, transpile,
                  validate_llm_chart, validate_source, extract_dsl, analyze_strategy_result)


KIWOOM = """[변수]
fast=3; slow=5
[매수진입]
A=Avg(C,fast); B=Avg(C,slow); CrossUp(A,B)
[매수청산]
A=Avg(C,fast); B=Avg(C,slow); CrossDown(A,B)
[매도진입]
[매도청산]
"""


class StrategyPipelineTest(unittest.TestCase):
    def test_dsl_parser_fails_closed_on_unknown_statement(self):
        dsl = '''strategy "FailClosed" {
            timeframe = "1d"
            if close > open
            long_entry = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "인식할 수 없는 문장"):
            BacktestEngine.run(dsl)

    def test_order_blocks_are_parsed_and_validated(self):
        bad_order = '''strategy "BadOrder" {
            timeframe = "1d"
            signal = close > open
            on(signal) { order.teleport() }
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "지원하지 않는 주문 명령"):
            BacktestEngine.run(bad_order)
        numeric_condition = '''strategy "BadCondition" {
            timeframe = "1d"
            value = ta.sma(close, 5)
            on(value) { order.buy(type = "MARKET") }
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "boolean"):
            BacktestEngine.run(numeric_condition)

    def test_static_series_type_and_function_arity(self):
        bad_boolean = '''strategy "BadType" {
            timeframe = "1d"
            signal = close and true
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "and/or는 boolean"):
            BacktestEngine.run(bad_boolean)
        bad_arity = '''strategy "BadArity" {
            timeframe = "1d"
            value = ta.sma(close)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "인수 개수 오류"):
            BacktestEngine.run(bad_arity)
        series_input = '''strategy "BadInput" {
            timeframe = "1d"
            input period = close
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "input은 scalar"):
            BacktestEngine.run(series_input)

    def test_causal_state_primitives_and_cascading_strategy(self):
        condition=np.array([False,True,True,False,False,True,False])
        np.testing.assert_array_equal(CoreStateLib.edge(condition),
                                      [False,True,False,False,False,True,False])
        np.testing.assert_array_equal(CoreStateLib.ready_after(condition,2),
                                      [True,False,False,False,False,False,False])
        np.testing.assert_array_equal(CoreStateLib.persist(condition,2),
                                      [False,False,True,False,False,False,False])
        dsl='''strategy "CascadingState" {
            timeframe = "1d"
            fast = ta.sma(close, 3)
            slow = ta.sma(close, 8)
            raw_entry = ta.crossover(fast, slow)
            raw_exit = ta.crossunder(fast, slow)
            regime = state.regime(raw_entry, raw_exit, 0)
            cooldown_ok = state.ready_after(raw_exit, 3)
            trend_held = state.persist(regime == 1, 2)
            long_entry = state.edge(raw_entry and cooldown_ok and trend_held)
            long_exit = raw_exit
            on(long_entry) { order.buy(type = "MARKET") }
            on(long_exit) { order.close_long() }
        }'''
        result=BacktestEngine.run(dsl,bars_count=500)
        self.assertIn("metrics",result)
        self.assertIn("regime",{item["name"] for item in result["indicators"]})

    def test_state_batch_matches_streaming_prefixes(self):
        up=np.array([False,True,False,False,True,False,False,False])
        down=np.array([False,False,False,True,False,False,True,False])
        checks=[lambda a,b:CoreStateLib.latch(a,b),lambda a,b:CoreStateLib.count(a,b),
                lambda a,b:CoreStateLib.regime(a,b),lambda a,b:CoreStateLib.ready_after(a,2),
                lambda a,b:CoreStateLib.hold(a,2),lambda a,b:CoreStateLib.persist(a,2)]
        for function in checks:
            complete=function(up,down)
            streamed=np.array([function(up[:i+1],down[:i+1])[-1] for i in range(len(up))])
            np.testing.assert_array_equal(complete,streamed)

    def test_backtest_uses_parsed_event_not_magic_signal_name(self):
        dsl = '''strategy "EventDriven" {
            timeframe = "1d"
            custom_buy = close > close[1]
            custom_sell = close < close[1]
            on(custom_buy) { order.buy(type = "MARKET") }
            on(custom_sell) { order.close_long() }
        }'''
        result = BacktestEngine.run(dsl)
        self.assertTrue(result["trades"])

    def test_next_open_fill_and_ohlc_stop_policy(self):
        dsl = '''strategy "ExecutionPolicy" {
            timeframe = "1d"
            enter = close > 0
            leave = false
            on(enter) { order.buy(type = "MARKET") }
            on(leave) { order.close_long() }
        }'''
        market = {"time":["2026-01-01","2026-01-02","2026-01-03"],
                  "open":[100,102,99],"high":[101,103,100],"low":[99,96,98],
                  "close":[100,100,99],"volume":[1000,1000,1000]}
        next_open = BacktestEngine.run(dsl, market=market, settings={"signal_mode":"next_open"})
        self.assertAlmostEqual(next_open["trades"][0]["price"], 102.0)
        stopped = BacktestEngine.run(dsl, market=market, settings={"stop_loss_pct":3})
        exit_trade = next(item for item in stopped["trades"] if item["side"] == "SELL")
        self.assertAlmostEqual(exit_trade["price"], 97.0)
        self.assertEqual(exit_trade["reason"], "STOP_LOSS")

    def test_kiwoom_four_tab_conversion(self):
        dsl = CodeTranspiler.from_kiwoom(KIWOOM, "Cross")
        self.assertIn("long_entry_A = ta.sma(close,fast)", dsl)
        self.assertIn("long_exit = ta.crossunder(long_exit_A,long_exit_B)", dsl)
        self.assertIn("short_entry = false", dsl)

    def test_dsl_is_actually_compiled(self):
        dsl = CodeTranspiler.from_kiwoom(KIWOOM, "Cross")
        close = np.array([10, 9, 8, 9, 10, 11, 10, 9, 8], dtype=float)
        market = {"open": close, "high": close + 1, "low": close - 1,
                  "close": close, "volume": np.ones(len(close))}
        compiled = DSLRuntime.compile(dsl, market)
        self.assertTrue(compiled.signal("long_entry", len(close)).any())
        self.assertTrue(compiled.signal("long_exit", len(close)).any())

    def test_risk_settings_reach_backtest(self):
        dsl = CodeTranspiler.from_kiwoom(KIWOOM, "Cross")
        result = BacktestEngine.run(dsl, settings={"stop_loss_pct": 2, "take_profit_pct": 4})
        self.assertEqual(result["settings"]["stop_loss_pct"], 2)
        self.assertIn("metrics", result)

    def test_http_pipeline(self):
        converted = transpile(TranspileRequest(source_type="KIWOOM", source_code=KIWOOM, name="HTTP"))
        tested = run_backtest(BacktestRequest(dsl_code=converted["dsl_code"], settings={"total_capital": 5000000}))
        self.assertEqual(tested["settings"]["total_capital"], 5000000)

    def test_unified_source_validation_pipeline(self):
        converted = validate_source(SourceValidateRequest(
            source_type="KIWOOM", source_code=KIWOOM, name="Unified"))
        self.assertTrue(converted["valid"])
        self.assertEqual(converted["status"], "success")
        self.assertIn('strategy "Unified"', converted["dsl_code"])
        prompt = validate_source(SourceValidateRequest(
            source_type="PROMPT", source_code="이평선 교차 전략", name="Prompt"))
        self.assertEqual(prompt["status"], "llm_required")
        self.assertTrue(prompt["prompt"])

    def test_playbook_is_single_prompt_attachment_and_matches_runtime(self):
        prompt = generate_full_llm_prompt("횡보 신호를 줄여줘", artifact_type="signal")
        self.assertIn("[공식 별첨 시작]", prompt)
        self.assertIn(playbook_hash(), prompt)
        runtime_source = inspect.getsource(DSLRuntime.compile) + inspect.getsource(__import__(
            "core.dsl_runtime", fromlist=["ExpressionEvaluator"]).ExpressionEvaluator.__init__)
        for function_name in TA_FUNCTIONS:
            self.assertIn(function_name, runtime_source)

    def test_tree_and_manual_llm_validation_flow(self):
        tree = artifact_tree()
        self.assertTrue({"indicator", "signal", "strength", "strategy", "drawing"}.issubset(
            {item["artifact_type"] for item in tree["categories"]}))
        package = build_llm_prompt(PromptPackageRequest(
            artifact_type="strategy", user_request="현재 전략을 유지"))
        self.assertEqual(package["playbook_hash"], playbook_hash())
        dsl = (Path(__file__).parent / "examples" / "jma_cross.dsl").read_text(encoding="utf-8")
        validated = validate_llm_chart(ValidateChartRequest(
            artifact_type="strategy", user_request="JMA 전략 생성",
            llm_response=f"설명\n```dsl\n{dsl}\n```"))
        self.assertTrue(validated["valid"])
        self.assertIn("chart", validated)
        failed = validate_llm_chart(ValidateChartRequest(
            artifact_type="signal", user_request="잘못된 결과 수정", llm_response="코드가 없습니다"))
        self.assertFalse(failed["valid"])
        self.assertEqual(failed["diagnostic"]["stage"], "extractor")
        self.assertIn("[이전 검증 오류]", failed["repair_prompt"])
        invalid = '''strategy "Broken" {
            timeframe = "1d"
            value = ta.not_registered(close, 10)
            long_entry = false
        }'''
        parser_failed = validate_llm_chart(ValidateChartRequest(
            artifact_type="indicator", user_request="오류 위치 보존",
            llm_response=f"```dsl\n{invalid}\n```"))
        self.assertFalse(parser_failed["valid"])
        self.assertEqual(parser_failed["diagnostic"]["line"], 3)
        self.assertIn("ta.not_registered", parser_failed["diagnostic"]["expression"])

    def test_official_builtin_families(self):
        source = """[매수진입]
A=WAvg(C,3); B=If(C>O, Highest(C,3), Lowest(C,3));
CrossUp(A,B) Or BarsSince(CrossUp(C,Avg(C,2)))==0 Or ValueWhen(1,C>O,C)>0
[매수청산]
WilliamsR(3)<-20 Or VHF(3)>1 Or sqrt(abs(C-O))>0
"""
        dsl = CodeTranspiler.from_kiwoom(source, "Builtins")
        result = BacktestEngine.run(dsl)
        self.assertIn("metrics", result)

    def test_documented_indicator_names(self):
        source = """[매수진입]
RSI(14)<70 And ATR(14)>0 And ADX(14)>=0 And TRIX(5)>-100 And CCI(14)>-500
[매수청산]
CrossDown(MACD(C,3,7,지수),0)
"""
        result = BacktestEngine.run(CodeTranspiler.from_kiwoom(source, "Indicators"))
        self.assertIn("metrics", result)

    def test_dotenv_loader(self):
        key = "KIWOOM_TEST_ONLY_KEY"
        os.environ.pop(key, None)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text(f'{key}="loaded"\n', encoding="utf-8")
            self.assertTrue(load_env(path))
            self.assertEqual(os.environ.get(key), "loaded")
        os.environ.pop(key, None)

    def test_kiwoom_minute_chart_shape(self):
        payload = {"data": {"return_code": 0, "stk_min_pole_chart_qry": [
            {"cntr_tm": "20260825100500", "cur_prc": "+70100", "open_pric": "+70000",
             "high_pric": "+70200", "low_pric": "+69900", "trde_qty": "1234"}
        ]}}
        market = KiwoomRESTClient.normalize_chart(payload)
        self.assertEqual(market["time"], ["20260825100500"])
        self.assertEqual(market["close"], [70100.0])

    def test_intraday_chart_time_is_unix_timestamp(self):
        dsl = CodeTranspiler.from_kiwoom("C > C(1)", "Intraday")
        market = {"time": ["20260806120000", "20260806120500"],
                  "open": [70000, 70100], "high": [70200, 70300], "low": [69900, 70000],
                  "close": [70100, 70200], "volume": [100, 120]}
        result = BacktestEngine.run(dsl, market=market)
        self.assertIsInstance(result["candles"][0]["time"], int)
        self.assertEqual(result["candles"][1]["time"] - result["candles"][0]["time"], 300)

    def test_strategy_indicators_are_returned_and_deduplicated(self):
        result = BacktestEngine.run(CodeTranspiler.from_kiwoom(KIWOOM, "Indicators"))
        names = [item["name"] for item in result["indicators"]]
        self.assertIn("long_entry_A", names)
        self.assertIn("long_entry_B", names)
        self.assertNotIn("long_exit_A", names)

    def test_jma_cross_strategy_end_to_end(self):
        dsl = (Path(__file__).parent / "examples" / "jma_cross.dsl").read_text(encoding="utf-8")
        result = BacktestEngine.run(dsl, bars_count=600)
        names = {item["name"] for item in result["indicators"]}
        self.assertTrue({"close_sma60", "jma_fast", "jma_slow"}.issubset(names))
        self.assertTrue(result["trades"], "JMA 교차 전략에서 체결이 생성되어야 합니다.")
        self.assertTrue(all(np.isfinite(point["value"])
                            for item in result["indicators"] for point in item["data"]))

    def test_kiwoom_three_argument_jma_uses_close(self):
        source = """[매수진입]
A=Avg(C,60); F=JMA(7,50,2); S=JMA(50,50,4); C>=A And CrossUp(F,S)
[매수청산]
F=JMA(7,50,2); S=JMA(50,50,4); CrossDown(F,S)
"""
        dsl = CodeTranspiler.from_kiwoom(source, "Kiwoom_JMA")
        result = BacktestEngine.run(dsl, bars_count=600)
        self.assertTrue(result["indicators"])
        self.assertTrue(result["trades"])

    def test_jma_matches_chart_base_trading_reference(self):
        values = np.array([100, 102, 101, 105, 103, 108, 110, 107, 112, 115, 111, 118], dtype=float)

        def reference(source, length, phase, power):
            length = max(1, int(length)); phase = max(-100.0, min(100.0, float(phase))); power = max(1, int(power))
            phase_ratio = phase / 100.0 + 1.5
            beta = .45 * (length - 1) / (.45 * (length - 1) + 2.0)
            alpha = beta ** power
            result = np.empty(len(source)); result[0] = e0 = source[0]
            e1 = e2 = 0.0; price_sum = source[0]
            for index in range(1, len(source)):
                close = source[index]
                e0 = (1-alpha)*close + alpha*e0
                e1 = (close-e0)*(1-beta) + beta*e1
                e2 = ((e0 + phase_ratio*e1 - result[index-1])*(1-alpha)**2) + alpha**2*e2
                result[index] = ((price_sum+close)/(index+1) if index < length
                                 else round((result[index-1]+e2)*10.0)/10.0)
                price_sum += close
            return result

        actual = CoreTALib.jma(values, 7, 50, 2)
        np.testing.assert_array_equal(actual, reference(values, 7, 50, 2))
        np.testing.assert_array_equal(CoreTALib.jma(values, 50, 50, 4), reference(values, 50, 50, 4))

    def test_jma_example_is_in_strategy_repository(self):
        init_db()
        names = {item["name"] for item in get_all_strategies()}
        self.assertIn("JMA_7_50_Cross", names)
        self.assertTrue(all("source_code" in item for item in get_all_strategies()))

    def test_jma_chart_points_have_rising_and_falling_colors(self):
        dsl = (Path(__file__).parent / "examples" / "jma_cross.dsl").read_text(encoding="utf-8")
        result = BacktestEngine.run(dsl)
        jma = next(item for item in result["indicators"] if item["name"] == "jma_fast")
        self.assertTrue(jma["direction_colored"])
        self.assertTrue({"#10b981", "#ef5350"}.issubset({point["color"] for point in jma["data"]}))

    def test_jma_stores_precomputed_color_array(self):
        values = np.array([100, 101, 103, 102, 99, 98, 104, 108, 103, 97, 95, 101], dtype=float)
        jma = CoreTALib.jma(values, 3, 50, 2)
        self.assertTrue(hasattr(jma, "trend_colors"))
        self.assertEqual(jma.shape, jma.trend_colors.shape)
        expected = np.sign(np.diff(np.asarray(jma), prepend=jma[0])).astype(np.int8)
        for i in range(1, len(expected)):
            if expected[i] == 0:
                expected[i] = expected[i - 1]
        np.testing.assert_array_equal(jma.trend_colors, expected)

    def test_supertrend_returns_state_and_chart_colors(self):
        dsl = '''strategy "Supertrend_Color" {
            timeframe = "1d"
            supertrend = ta.supertrend(10, 3)
            long_entry = close > supertrend
            long_exit = close < supertrend
        }'''
        result = BacktestEngine.run(dsl)
        item = next(item for item in result["indicators"] if item["name"] == "supertrend")
        self.assertTrue(item["direction_colored"])
        self.assertTrue(all(point["color"] in {"#10b981", "#ef5350"} for point in item["data"]))

    def test_on_bar_persistent_state_and_conditional_output(self):
        market = {
            "open": np.arange(1, 7, dtype=float), "high": np.arange(1, 7, dtype=float),
            "low": np.arange(1, 7, dtype=float), "close": np.arange(1, 7, dtype=float),
            "volume": np.ones(6),
        }
        dsl = '''strategy "Stateful" {
            timeframe = "1d"
            trigger = close == 2
            state cooldown = 0
            on_bar {
                if (trigger) {
                    cooldown = 2
                } else {
                    if (cooldown > 0) {
                        cooldown = cooldown - 1
                    }
                }
                allow_entry = cooldown == 0
            }
            on(allow_entry) { order.buy(type = "MARKET") }
        }'''
        compiled = DSLRuntime.compile(dsl, market)
        np.testing.assert_array_equal(compiled.values["cooldown"], [0, 2, 1, 0, 0, 0])
        np.testing.assert_array_equal(compiled.values["allow_entry"], [True, False, False, True, True, True])

    def test_mtf_exposes_only_previous_confirmed_higher_timeframe_bar(self):
        market = {"open":np.arange(1,7,dtype=float),"high":np.arange(1,7,dtype=float),
                  "low":np.arange(1,7,dtype=float),"close":np.arange(1,7,dtype=float),"volume":np.ones(6),
                  "date":np.asarray([20260102]*3+[20260105]*3,dtype=float),
                  "time":np.asarray([90000,90100,90200]*2,dtype=float)}
        dsl='''strategy "MTF" {
            timeframe = "1m"
            prior_day_close = mtf.close("1d")
            long_entry = close > prior_day_close
        }'''
        compiled=DSLRuntime.compile(dsl,market)
        self.assertTrue(np.all(np.isnan(compiled.values["prior_day_close"][:3])))
        np.testing.assert_array_equal(compiled.values["prior_day_close"][3:], [3,3,3])

    def test_broker_order_lifecycle_limit_stop_oco_and_day_expiry(self):
        from core.broker import BrokerEmulator, BrokerOrder, OrderStatus
        broker=BrokerEmulator()
        limit=broker.submit(BrokerOrder("entry","BUY","LIMIT",limit_price=99,oco="pair"))
        stop=broker.submit(BrokerOrder("guard","BUY","STOP",stop_price=110,oco="pair"))
        self.assertEqual(limit.status,OrderStatus.ACCEPTED)
        fills=broker.process_bar(100,105,98,102)
        self.assertEqual(fills[0].fill_price,99)
        self.assertEqual(stop.status,OrderStatus.CANCELED)
        day=broker.submit(BrokerOrder("day","BUY","LIMIT",limit_price=50,tif="DAY"))
        broker.process_bar(100,101,99,100,end_of_session=True)
        self.assertEqual(day.status,OrderStatus.EXPIRED)

    def test_dsl_accepts_valid_limit_order_and_rejects_missing_price(self):
        valid='''strategy "Limit" { signal = close > 0
            on(signal) { order.buy(type="LIMIT", limit=close[1], tif="DAY") }
        }'''
        self.assertEqual(DSLParser.parse(valid).events[0].orders[0].command,"order.buy")
        with self.assertRaises(DSLParseError):
            DSLParser.parse('''strategy "Bad" { signal = close > 0
                on(signal) { order.buy(type="LIMIT") }
            }''')

    def test_limit_order_is_filled_by_backtest_on_later_ohlc_bar(self):
        market={"time":["2026-01-01","2026-01-02","2026-01-03"],
                "open":[100,99,102],"high":[101,103,104],"low":[99,98,101],"close":[100,102,103],"volume":[1,1,1]}
        dsl='''strategy "LimitFill" {
            signal = state.edge(close > 0)
            on(signal) { order.buy(type="LIMIT", limit=close, tif="GTC") }
        }'''
        result=BacktestEngine.run(dsl,market=market)
        self.assertEqual(result["trades"][0]["reason"],"PENDING_ORDER_FILL")
        self.assertEqual(result["trades"][0]["price"],99.0)

    def test_wilder_rma_atr_and_rsi_reference_seed(self):
        series=np.asarray([1,2,3,4,5,6],float)
        np.testing.assert_allclose(CoreTALib.rma(series,3),[np.nan,np.nan,2,8/3,31/9,116/27],equal_nan=True)
        high=series+1;low=series-1
        np.testing.assert_allclose(CoreTALib.atr(high,low,series,3)[2:],2.0)
        rsi=CoreTALib.rsi(series,3)
        self.assertTrue(np.allclose(rsi[3:],100.0))

    def test_default_category_migration_is_idempotent_and_ui_has_visible_workflow(self):
        init_db();init_db()
        tree=artifact_tree()
        roots=[item for item in tree["categories"] if item["parent_id"] is None]
        self.assertEqual({item["artifact_type"] for item in roots},{"indicator","signal","strength","strategy","drawing"})
        self.assertEqual(len(roots),5)
        html=(Path(__file__).parent/"core"/"templates"/"index.html").read_text(encoding="utf-8")
        ui=(Path(__file__).parent/"core"/"static"/"ui.js").read_text(encoding="utf-8")
        self.assertIn('/static/ui.js',html)
        self.assertIn('DSL 검증 · 차트 적용',ui)
        for kind in ("indicator","signal","strength","strategy","drawing"):
            self.assertIn(f'value="{kind}"',ui)

    def test_value_when_uses_zero_based_occurrence_and_handles_no_hits(self):
        condition=np.asarray([False,True,False,True,False])
        values=np.asarray([10,20,30,40,50],float)
        np.testing.assert_allclose(CoreTALib.value_when(0,condition,values),[np.nan,20,20,40,40],equal_nan=True)
        np.testing.assert_allclose(CoreTALib.value_when(1,condition,values),[np.nan,np.nan,np.nan,20,20],equal_nan=True)
        no_hits=CoreTALib.value_when(0,np.zeros(5,dtype=bool),values)
        self.assertTrue(np.all(np.isnan(no_hits)))

    def test_sideways_reference_strategy_compiles_before_first_reference_bar(self):
        dsl='''strategy "Sideways_Breakout_Reference_Cooldown" {
            timeframe = "5m"
            range_period = 20
            atr_period = 14
            range_atr_multiplier = 1.5
            cooldown_bars = 6
            range_high = ta.highest(high, range_period)
            range_low = ta.lowest(low, range_period)
            range_width = range_high - range_low
            atr_value = ta.atr(atr_period)
            sideways_raw = range_width <= atr_value * range_atr_multiplier
            sideways = state.persist(sideways_raw, 3)
            previous_range_high = ta.highest(high[1], range_period)
            upward_escape = close > previous_range_high
            reference_bar = state.falling_edge(sideways) and upward_escape
            reference_high = ta.value_when(0, reference_bar, high)
            reference_low = ta.value_when(0, reference_bar, low)
            breakout = ta.crossover(close, reference_high)
            long_exit = ta.crossunder(close, reference_low)
            reentry_ready = state.ready_after(long_exit, cooldown_bars)
            long_entry = not sideways and reentry_ready and breakout
            on(long_entry) { order.buy(type = "MARKET") }
            on(long_exit) { order.close_long() }
        }'''
        result=BacktestEngine.run(dsl,bars_count=80)
        self.assertIn("metrics",result)

    def test_extractor_removes_misplaced_markdown_fences_inside_strategy(self):
        response='''strategy "Fence" {
```makefile
signal = close > close[1]
```
}'''
        self.assertNotIn("```",extract_dsl(response))

    def test_kiwoom_connection_failure_is_not_reported_as_dsl_repair(self):
        request=ValidateChartRequest(artifact_type="strategy",user_request="test",prompt_text="prompt",
            llm_response='''strategy "Connection" { signal = close > 0 }''',data_source="kiwoom")
        with patch("main.load_market",side_effect=KiwoomAPIError("키움 API 연결 실패: socket denied")):
            result=validate_llm_chart(request)
        self.assertEqual(result["status"],"data_error")
        self.assertEqual(result["repair_prompt"],"")
        self.assertEqual(result["diagnostic"]["stage"],"market_data")

    def test_successful_backtest_analysis_feeds_next_improvement_prompt(self):
        result={"metrics":{"total_return":"+4.95%","mdd":"-4.92%","trade_count":"6회",
                           "closed_trade_count":"6회","win_rate":"50.0%"},
                "diagnostics":{"signal_counts":{"sideways_raw":20,"long_entry":6}}}
        analysis=analyze_strategy_result(result)
        self.assertEqual(analysis["verdict"],"needs_improvement")
        self.assertTrue(any("6회" in issue for issue in analysis["issues"]))
        self.assertEqual(analysis["schema"],"strategy_agnostic_evidence/v1")
        self.assertEqual(analysis["evidence_quality"],"insufficient")
        self.assertIn("독립적인 true 봉 수",analysis["signal_count_semantics"])
        self.assertIn("execution_settings",analysis["evaluation_context"])
        serialized=json.dumps(analysis,ensure_ascii=False)
        self.assertNotIn("거짓 돌파",serialized)
        self.assertNotIn("추세 확인",serialized)
        prompt=generate_full_llm_prompt("개선",current_dsl='strategy "A" { signal = false }',
                                        validation_error=json.dumps(analysis,ensure_ascii=False))
        self.assertIn("전략 비종속 성과 증거",prompt)
        self.assertIn("수익률/MDD",prompt)
        self.assertIn("병목 가설을 하나만 선택",prompt)


if __name__ == "__main__":
    unittest.main()
