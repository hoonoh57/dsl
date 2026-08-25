import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.broker import BrokerEmulator, BrokerOrder, OrderStatus
from core.dsl_parser import DSLParser, DSLParseError
from core.dsl_runtime import DSLRuntimeError, ExpressionEvaluator
from core.function_registry import FUNCTION_SPECS
from core.strategy_factory import (
    DataContract,
    ParameterSpec,
    StrategyFactory,
    StrategyFactoryStore,
    apply_dsl_parameters,
    discover_dsl_parameters,
    extract_dsl,
)
from core.stage1_target_loop import TargetLoopService


BASE_DSL = '''strategy "Stage1Test" {
    timeframe = "1d"
    input fast = 2
    input slow = 5
    f = ta.sma(close, fast)
    s = ta.sma(close, slow)
    long_entry = ta.crossover(f, s)
    long_exit = ta.crossunder(f, s)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def oscillating_market(n=80):
    times = [f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)]
    close = np.asarray([100 + (i % 12) * 3 if (i // 12) % 2 == 0 else 133 - (i % 12) * 3 for i in range(n)], dtype=float)
    open_ = close + np.where(np.arange(n) % 2 == 0, -0.5, 0.5)
    high = np.maximum(open_, close) + 2
    low = np.minimum(open_, close) - 2
    return {"time": times, "open": open_.tolist(), "high": high.tolist(), "low": low.tolist(),
            "close": close.tolist(), "volume": (1000 + np.arange(n) * 10).astype(float).tolist()}


class Stage1FactoryTest(unittest.TestCase):
    def make_factory(self):
        temp = tempfile.TemporaryDirectory()
        store = StrategyFactoryStore(Path(temp.name) / "stage1.db")
        self.addCleanup(temp.cleanup)
        return StrategyFactory(store)

    def test_broker_rejects_bad_tif_and_records_lifecycle(self):
        broker = BrokerEmulator()
        bad = broker.submit(BrokerOrder("bad", "BUY", tif="FOREVER"))
        self.assertEqual(bad.status, OrderStatus.REJECTED)
        self.assertIn("unsupported tif", bad.reason)
        good = broker.submit(BrokerOrder("ok", "BUY", type="LIMIT", limit_price=95, tif="DAY"))
        self.assertEqual(good.status, OrderStatus.ACCEPTED)
        broker.expire_day_orders()
        self.assertEqual(good.status, OrderStatus.EXPIRED)
        statuses = [row["status"] for row in broker.snapshot_history() if row["order_id"] == "ok"]
        self.assertEqual(statuses, ["CREATED", "ACCEPTED", "EXPIRED"])

    def test_parser_rejects_invalid_tif(self):
        dsl = '''strategy "BadTif" {
            timeframe = "1d"
            signal = close > 0
            on(signal) { order.buy(type = "LIMIT", limit = 1, tif = "FOREVER") }
        }'''
        with self.assertRaisesRegex(DSLParseError, "지원하지 않는 TIF"):
            DSLParser.parse(dsl)

    def test_semantic_rejects_bad_indicator_types_and_onbar_calls(self):
        bad_type = '''strategy "BadType" {
            timeframe = "1d"
            x = ta.sma(true, 20)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "numeric series"):
            BacktestEngine.run(bad_type)
        bad_onbar = '''strategy "BadOnBar" {
            timeframe = "1d"
            state armed = false
            on_bar {
                armed = ta.crossover(close, open)
            }
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "on_bar에서는 함수 호출"):
            BacktestEngine.run(bad_onbar)

    def test_capability_registry_names_match_runtime_dispatch(self):
        size = 10
        close = np.arange(size, dtype=float) + 100
        values = {"open": close, "high": close + 1, "low": close - 1, "close": close,
                  "volume": np.ones(size), "amount": close, "open_interest": np.zeros(size),
                  "date": np.arange(size, dtype=float), "time": np.zeros(size)}
        evaluator = ExpressionEvaluator(values, size)
        self.assertEqual(set(FUNCTION_SPECS), set(evaluator.functions))

    def test_next_open_applies_to_entry_and_strategy_exit(self):
        dsl = '''strategy "NextOpenBothWays" {
            timeframe = "1d"
            enter = close > close[1]
            leave = close < close[1]
            on(enter) { order.buy(type = "MARKET") }
            on(leave) { order.close_long() }
        }'''
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "open": [100, 105, 120, 70], "high": [101, 111, 125, 82], "low": [99, 104, 85, 68],
            "close": [100, 110, 90, 80], "volume": [1000, 1000, 1000, 1000],
        }
        result = BacktestEngine.run(dsl, market=market, settings={"signal_mode": "next_open"})
        entries = [row for row in result["trades"] if row["kind"] == "ENTRY"]
        exits = [row for row in result["trades"] if row["kind"] == "EXIT"]
        self.assertEqual(entries[0]["signal_time"], "2026-01-02")
        self.assertEqual(entries[0]["time"], "2026-01-03")
        self.assertAlmostEqual(entries[0]["price"], 120.0)
        self.assertEqual(exits[0]["signal_time"], "2026-01-03")
        self.assertEqual(exits[0]["time"], "2026-01-04")
        self.assertAlmostEqual(exits[0]["price"], 70.0)
        self.assertEqual(result["metrics_numeric"]["open_position"], 0)
        net = sum(row["net_pnl"] for row in result["closed_trades"])
        equity_change = result["metrics_numeric"]["final_equity"] - result["metrics_numeric"]["initial_capital"]
        self.assertAlmostEqual(net, equity_change, places=6)

    def test_day_orders_expire_in_backtest_event_loop(self):
        dsl = '''strategy "DayExpire" {
            timeframe = "1d"
            signal = close > 0
            on(signal) { order.buy(type = "LIMIT", limit = 1, tif = "DAY") }
        }'''
        market = oscillating_market(8)
        result = BacktestEngine.run(dsl, market=market)
        statuses = [row["status"] for row in result["diagnostics"]["broker_history"]]
        self.assertIn("EXPIRED", statuses)
        self.assertNotIn("FILLED", statuses)

    def test_data_contract_is_hash_stable_and_fail_closed(self):
        market = oscillating_market(12)
        first, p1 = DataContract.normalize(market, instrument="TEST", timeframe="1d", source="unit")
        second, p2 = DataContract.normalize(market, instrument="TEST", timeframe="1d", source="unit")
        self.assertEqual(p1.data_hash, p2.data_hash)
        self.assertEqual(first["_meta"]["data_hash"], p1.data_hash)
        duplicate = oscillating_market(12)
        duplicate["time"][4] = duplicate["time"][3]
        with self.assertRaisesRegex(ValueError, "오름차순"):
            DataContract.normalize(duplicate, instrument="TEST", timeframe="1d", source="unit")

    def test_input_discovery_and_safe_parameter_rewrite(self):
        params = discover_dsl_parameters(BASE_DSL)
        self.assertEqual([item["name"] for item in params], ["fast", "slow"])
        revised = apply_dsl_parameters(BASE_DSL, {"fast": 3, "slow": 7})
        self.assertIn("input fast = 3", revised)
        self.assertIn("input slow = 7", revised)
        with self.assertRaisesRegex(ValueError, "input이 아닌"):
            apply_dsl_parameters(BASE_DSL, {"missing": 3})

    def test_immutable_experiment_lineage_and_head_are_separate(self):
        factory = self.make_factory()
        market = oscillating_market(80)
        baseline = factory.baseline(intent="unit", dsl_code=BASE_DSL, market=market,
                                    instrument="TEST", timeframe="1d", source="unit")
        child = factory.store.create_experiment(parent_id=baseline["id"], operation="MANUAL_TEST",
            strategy_name=baseline["strategy_name"], intent=baseline["intent"], dsl_code=baseline["dsl_code"],
            parameters={}, execution=baseline["execution"], provenance=baseline["provenance"],
            result=baseline["result"], analysis=baseline["analysis"])
        self.assertEqual(factory.store.current_head(baseline["root_id"])["id"], baseline["id"])
        factory.store.promote(child["id"])
        self.assertEqual(factory.store.current_head(baseline["root_id"])["id"], child["id"])
        self.assertEqual([row["id"] for row in factory.store.lineage(child["id"])], [baseline["id"], child["id"]])
        self.assertEqual(factory.store.get_experiment(baseline["id"])["operation"], "BASELINE")

    def test_parameter_seeker_is_deterministic_and_creates_best_experiment(self):
        market = oscillating_market(100)
        f1 = self.make_factory()
        base1 = f1.baseline(intent="seek", dsl_code=BASE_DSL, market=market, instrument="TEST", timeframe="1d", source="unit")
        result1 = f1.seek(experiment_id=base1["id"], market=market,
                          parameter_specs=[{"name":"fast","values":[2,3,4]}, {"name":"slow","values":[5,6,7]}],
                          method="random", objective="MAX_RETURN", seed=99, max_candidates=9)
        f2 = self.make_factory()
        base2 = f2.baseline(intent="seek", dsl_code=BASE_DSL, market=market, instrument="TEST", timeframe="1d", source="unit")
        result2 = f2.seek(experiment_id=base2["id"], market=market,
                          parameter_specs=[{"name":"fast","values":[2,3,4]}, {"name":"slow","values":[5,6,7]}],
                          method="random", objective="MAX_RETURN", seed=99, max_candidates=9)
        self.assertEqual(result1["study"]["best_parameters"], result2["study"]["best_parameters"])
        self.assertAlmostEqual(result1["study"]["best_score"], result2["study"]["best_score"], places=12)
        self.assertEqual(result1["experiment"]["operation"], "SEEKER_BEST")

    def test_llm_feedback_apply_episode_and_chart_audit(self):
        factory = self.make_factory(); market = oscillating_market(80)
        baseline = factory.baseline(intent="JMA가 아니라 SMA 교차 개선", dsl_code=BASE_DSL, market=market,
                                    instrument="TEST", timeframe="1d", source="unit")
        package = factory.feedback_package(baseline["id"], target_return=25)
        self.assertIn("주요 구조 가설 하나", package["prompt"])
        with self.assertRaisesRegex(ValueError, "strategy DSL"):
            extract_dsl("설명만 있습니다")
        revised = BASE_DSL.replace("input fast = 2", "input fast = 3")
        applied = factory.apply_llm_response(experiment_id=baseline["id"], llm_response=f"```dsl\n{revised}\n```",
                                             market=market, hypothesis="fast smoothing 변경")
        self.assertEqual(applied["experiment"]["parent_id"], baseline["id"])
        self.assertTrue(factory.store.episodes_for_root(baseline["root_id"]))
        audit = factory.chart_audit(applied["experiment"])
        self.assertEqual(audit["experiment_id"], applied["experiment"]["id"])
        self.assertIn("candles", audit); self.assertIn("closed_trades", audit)

    def test_target_loop_persists_iteration_and_stop_state(self):
        factory = self.make_factory(); market = oscillating_market(80)
        baseline = factory.baseline(intent="loop", dsl_code=BASE_DSL, market=market,
                                    instrument="TEST", timeframe="1d", source="unit")
        service = TargetLoopService(factory)
        loop = service.create(root_id=baseline["root_id"], target_return=999, iteration_limit=2,
                              backtest_budget=10, no_improvement_limit=5)
        first = service.observe(loop_id=loop["id"], experiment_id=baseline["id"], accepted=False)
        self.assertEqual(first["state"]["status"], "CONTINUE")
        second = service.observe(loop_id=loop["id"], experiment_id=baseline["id"], accepted=False)
        self.assertEqual(second["state"]["status"], "ITERATION_LIMIT")

    def test_methodology_summary_labels_claim_as_descriptive(self):
        factory = self.make_factory(); market = oscillating_market(80)
        baseline = factory.baseline(intent="methodology", dsl_code=BASE_DSL, market=market,
                                    instrument="TEST", timeframe="1d", source="unit")
        summary = factory.methodology_summary(baseline["root_id"])
        self.assertIn("A_baseline_return_pct", summary)
        self.assertEqual(summary["claim"], "descriptive_only_until_OOS_and_multi-strategy_methodology_validation")


if __name__ == "__main__":
    unittest.main()
