import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.dsl_parser import DSLParseError, DSLParser
from core.dsl_runtime import DSLRuntimeError, ExpressionEvaluator
from core.function_registry import FUNCTION_SPECS
from core.stage1_data_store import save_market_snapshot
from core.stage1_methodology import MethodologyValidator
from core.stage1_resumable_seeker import ResumableSeekerService
from core.stage1_target_loop import TargetLoopService
from core.strategy_factory import DataContract, StrategyFactory, StrategyFactoryStore


DSL = '''strategy "Completion" {
    timeframe = "1d"
    input fast = 3
    input slow = 8
    f = ta.sma(close, fast)
    s = ta.sma(close, slow)
    long_entry = ta.crossover(f, s)
    long_exit = ta.crossunder(f, s)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(size=160):
    t = np.arange(size, dtype=float)
    close = 100 + 0.12 * t + 7 * np.sin(t / 5.0) + 2 * np.sin(t / 17.0)
    open_ = close + 0.4 * np.sin(t / 3.0)
    high = np.maximum(open_, close) + 1.5
    low = np.minimum(open_, close) - 1.5
    times = []
    year, month, day = 2024, 1, 1
    for _ in range(size):
        times.append(f"{year:04d}-{month:02d}-{day:02d}")
        day += 1
        if day > 28:
            day = 1; month += 1
            if month > 12:
                month = 1; year += 1
    return {"time": times, "open": open_.tolist(), "high": high.tolist(), "low": low.tolist(),
            "close": close.tolist(), "volume": (1000 + (t % 19) * 50).tolist()}


class Stage1CompletionContractsTest(unittest.TestCase):
    def make_factory(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return StrategyFactory(StrategyFactoryStore(Path(temp.name) / "completion.db"))

    def normalized(self, size=160):
        return DataContract.normalize(market(size), instrument="CMP", timeframe="1d", source="unit")[0]

    def test_order_price_argument_applicability_is_fail_closed(self):
        market_with_limit = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "MARKET", limit = close)')
        with self.assertRaisesRegex(DSLParseError, "MARKET 주문에는 limit/stop"):
            DSLParser.parse(market_with_limit)
        limit_with_stop = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "LIMIT", limit = close, stop = close)')
        with self.assertRaisesRegex(DSLParseError, "LIMIT 주문에는 stop"):
            DSLParser.parse(limit_with_stop)
        stop_with_limit = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "STOP", stop = close, limit = close)')
        with self.assertRaisesRegex(DSLParseError, "STOP 주문에는 limit"):
            DSLParser.parse(stop_with_limit)

    def test_limit_and_stop_prices_are_statically_numeric(self):
        bad = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "LIMIT", limit = long_entry)')
        with self.assertRaisesRegex(DSLRuntimeError, "주문 limit 가격은 숫자형"):
            BacktestEngine.run(bad, market=market(80))
        good = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "STOP_LIMIT", stop = s, limit = f)')
        result = BacktestEngine.run(good, market=market(80))
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")

    def test_function_registry_and_runtime_dispatch_have_exact_name_parity(self):
        size = 16
        close = np.arange(size, dtype=float) + 100
        values = {"open": close, "high": close + 1, "low": close - 1, "close": close,
                  "volume": np.ones(size), "amount": close, "open_interest": np.zeros(size),
                  "date": np.arange(size, dtype=float), "time": np.zeros(size)}
        evaluator = ExpressionEvaluator(values, size)
        self.assertEqual(set(FUNCTION_SPECS), set(evaluator.functions))
        self.assertTrue(all(spec.minimum <= spec.maximum for spec in FUNCTION_SPECS.values()))

    def test_target_loop_never_promotes_implicitly_and_has_stability_guards(self):
        factory = self.make_factory(); normalized = self.normalized(); save_market_snapshot(normalized)
        baseline = factory.baseline(intent="loop", dsl_code=DSL, market=normalized,
                                    instrument="CMP", timeframe="1d", source="unit")
        child = factory.store.create_experiment(parent_id=baseline["id"], operation="CANDIDATE",
            strategy_name=baseline["strategy_name"], intent=baseline["intent"], dsl_code=baseline["dsl_code"],
            parameters={}, execution=baseline["execution"], provenance=baseline["provenance"],
            result={**baseline["result"], "metrics_numeric": {**baseline["result"]["metrics_numeric"], "total_return_pct": 999.0}},
            analysis=baseline["analysis"])
        service = TargetLoopService(factory)
        loop = service.create(root_id=baseline["root_id"], target_return=5000,
                              iteration_limit=20, no_improvement_limit=10,
                              duplicate_hypothesis_limit=2, parameter_spike_limit=3.0)
        observed = service.observe(loop_id=loop["id"], experiment_id=child["id"], accepted=True,
                                   parameter_spike_ratio=3.5)
        self.assertEqual(factory.store.current_head(baseline["root_id"])["id"], baseline["id"])
        self.assertEqual(observed["state"]["status"], "PARAMETER_INSTABILITY")
        self.assertTrue(observed["state"]["last_observation"]["promotion_required"])

        loop2 = service.create(root_id=baseline["root_id"], target_return=5000,
                               iteration_limit=20, no_improvement_limit=10,
                               duplicate_hypothesis_limit=2, parameter_spike_limit=99.0)
        first = service.observe(loop_id=loop2["id"], experiment_id=baseline["id"], duplicate_hypothesis=True)
        self.assertEqual(first["state"]["status"], "CONTINUE")
        second = service.observe(loop_id=loop2["id"], experiment_id=baseline["id"], duplicate_hypothesis=True)
        self.assertEqual(second["state"]["status"], "NO_NEW_HYPOTHESIS")

    def test_post_seeker_episode_and_parameter_sensitivity_are_persisted(self):
        factory = self.make_factory(); normalized = self.normalized(); save_market_snapshot(normalized)
        baseline = factory.baseline(intent="improve", dsl_code=DSL, market=normalized,
                                    instrument="CMP", timeframe="1d", source="unit")
        revised = DSL.replace("input fast = 3", "input fast = 4")
        structural = factory.apply_llm_response(experiment_id=baseline["id"],
            llm_response=f"```dsl\n{revised}\n```", market=normalized,
            hypothesis="fast smoothing 구조를 조정", expected_effect="noise reduction")["experiment"]
        seeker = ResumableSeekerService(factory)
        session = seeker.create(parent_experiment_id=structural["id"], parameter_specs=[
            {"name":"fast","values":[2,3,4]}, {"name":"slow","values":[7,8,9]}
        ], method="grid", objective="MAX_RETURN", seed=3, max_candidates=20)
        completed = seeker.process(session["id"], batch_size=20)
        self.assertEqual(completed["session"]["status"], "COMPLETED")
        self.assertIn("finalized_episode_id", completed["experiment"])
        episodes = factory.store.episodes_for_root(baseline["root_id"], 100)
        self.assertTrue(any(str(item.get("reason", "")).startswith("after_seeker return") for item in episodes))
        method = MethodologyValidator(factory.store).summarize(baseline["root_id"])
        self.assertEqual(method["episode_rate_basis"], "POST_SEEKER_FINAL")
        self.assertEqual(method["finalized_post_seeker_episodes"], 1)
        sensitivity = method["parameter_sensitivity"]
        self.assertTrue(sensitivity["available"])
        self.assertEqual(sensitivity["candidate_count"], 9)
        self.assertIn("fast", sensitivity["parameters"])
        self.assertIn("slow", sensitivity["parameters"])


if __name__ == "__main__":
    unittest.main()
