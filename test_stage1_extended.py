import tempfile
import unittest
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.broker import BrokerEmulator, BrokerOrder
from core.dsl_parser import DSLParseError, DSLParser
from core.dsl_runtime import DSLRuntimeError
from core.stage1_data_store import save_market_snapshot
from core.stage1_diff import summarize_dsl_change
from core.stage1_evidence import EvidenceBuilder
from core.stage1_methodology import MethodologyValidator
from core.stage1_oos import OOSRegistry
from core.stage1_resumable_seeker import ResumableSeekerService
from core.strategy_factory import DataContract, StrategyFactory, StrategyFactoryStore


DSL = '''strategy "Extended" {
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


def market(size=140):
    t = np.arange(size, dtype=float)
    close = 100.0 + 0.08 * t + np.sin(t / 4.0) * 8.0 + np.sin(t / 13.0) * 3.0
    open_ = close + np.sin(t / 3.0) * 0.5
    high = np.maximum(open_, close) + 1.5
    low = np.minimum(open_, close) - 1.5
    volume = 1000.0 + (t % 17) * 50.0
    year, month, day = 2025, 1, 1
    times = []
    for _ in range(size):
        times.append(f"{year:04d}-{month:02d}-{day:02d}")
        day += 1
        if day > 28:
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1
    return {
        "time": times,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
    }


class Stage1ExtendedTest(unittest.TestCase):
    def make_factory(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return StrategyFactory(StrategyFactoryStore(Path(temp.name) / "extended.db"))

    def normalized(self, size=140):
        return DataContract.normalize(market(size), instrument="EXT", timeframe="1d", source="unit")[0]

    def test_order_quantity_is_not_a_published_or_hidden_dsl_capability(self):
        bad = DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "MARKET", quantity = 3)')
        with self.assertRaisesRegex(DSLParseError, "지원하지 않는 주문 인수: quantity"):
            DSLParser.parse(bad)

    def test_broker_submit_event_is_preserved_across_created_and_accepted(self):
        broker = BrokerEmulator()
        order = broker.submit(BrokerOrder("m1", "BUY", quantity=2), event="2026-01-02-close")
        broker.process_bar(101, 101, 101, 101, event="2026-01-03-open")
        history = order.history
        self.assertEqual([item["status"] for item in history], ["CREATED", "ACCEPTED", "FILLED"])
        self.assertEqual(history[0]["event"], "2026-01-02-close")
        self.assertEqual(history[1]["event"], "2026-01-02-close")
        self.assertEqual(history[2]["event"], "2026-01-03-open")
        self.assertEqual(history[2]["quantity"], 2.0)

    def test_registry_aligned_static_types_reject_bad_macd_and_sum(self):
        bad_macd = '''strategy "BadMacd" {
            timeframe = "1d"
            x = ta.macd(close, 3, 7, true)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "method는 string"):
            BacktestEngine.run(bad_macd, market=market(80))
        bad_sum = '''strategy "BadSum" {
            timeframe = "1d"
            x = ta.sum(close, true)
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "period는 scalar number"):
            BacktestEngine.run(bad_sum, market=market(80))

    def test_structural_diff_identifies_parameter_and_event_changes(self):
        revised = DSL.replace("input fast = 3", "input fast = 4").replace(
            'on(long_exit) { order.close_long() }',
            'on(long_exit) { order.close_position() }',
        )
        diff = summarize_dsl_change(DSL, revised)
        self.assertEqual(diff["changed_assignments"]["fast"]["after"], "4")
        self.assertTrue(diff["events_changed"])
        self.assertGreaterEqual(diff["changed_assignment_count"], 1)
        self.assertTrue(diff["unified_diff"])

    def test_evidence_v3_contains_costs_worst_trades_and_market_lifecycle(self):
        factory = self.make_factory()
        normalized = self.normalized(140)
        experiment = factory.baseline(
            intent="evidence",
            dsl_code=DSL,
            market=normalized,
            instrument="EXT",
            timeframe="1d",
            source="unit",
            settings={"commission_pct": 0.015, "sell_tax_pct": 0.18, "slippage_pct": 0.02},
        )
        evidence = EvidenceBuilder.build(experiment)
        self.assertEqual(evidence["schema"], "stage1_evidence/v3")
        account = evidence["account"]
        self.assertIn("commission_cost", account)
        self.assertIn("tax_cost", account)
        self.assertIn("slippage_cost", account)
        self.assertIn("execution_cost_total", account)
        self.assertIn("worst_trades", evidence["trade_summary"])
        self.assertIn("largest_mfe_givebacks", evidence["trade_summary"])
        lifecycle = evidence["order_lifecycle"]["strategy_market"]
        self.assertTrue(lifecycle)
        by_order = {}
        for item in lifecycle:
            by_order.setdefault(item["order_id"], []).append(item)
        self.assertTrue(all([row["status"] for row in rows] == ["CREATED", "ACCEPTED", "FILLED"]
                            for rows in by_order.values()))

    def test_resumable_seeker_cancel_resume_and_cross_session_cache(self):
        factory = self.make_factory()
        normalized = self.normalized(120)
        save_market_snapshot(normalized)
        baseline = factory.baseline(
            intent="resume",
            dsl_code=DSL,
            market=normalized,
            instrument="EXT",
            timeframe="1d",
            source="unit",
        )
        service = ResumableSeekerService(factory)
        specs = [
            {"name": "fast", "values": [2, 3]},
            {"name": "slow", "values": [7, 8]},
        ]
        first = service.create(parent_experiment_id=baseline["id"], parameter_specs=specs,
                               method="grid", objective="MAX_RETURN", seed=7, max_candidates=10)
        partial = service.process(first["id"], batch_size=1)
        self.assertEqual(partial["session"]["cursor"], 1)
        canceled = service.cancel(first["id"])
        self.assertEqual(canceled["status"], "CANCELED")
        resumed = service.resume(first["id"])
        self.assertEqual(resumed["status"], "READY")
        complete = None
        for _ in range(10):
            complete = service.process(first["id"], batch_size=2)
            if complete["session"]["status"] == "COMPLETED":
                break
        self.assertEqual(complete["session"]["status"], "COMPLETED")
        self.assertEqual(complete["session"]["cursor"], 4)
        self.assertEqual(complete["experiment"]["operation"], "SEEKER_BEST")

        second = service.create(parent_experiment_id=baseline["id"], parameter_specs=specs,
                                method="grid", objective="MAX_RETURN", seed=7, max_candidates=10)
        second_result = service.process(second["id"], batch_size=10)
        rows = service.candidates(second["id"], limit=10)
        self.assertEqual(second_result["session"]["status"], "COMPLETED")
        self.assertTrue(rows)
        self.assertTrue(all(int(item["cache_hit"]) == 1 for item in rows))

    def test_immutable_train_holdout_split_and_fixed_oos_evaluation(self):
        factory = self.make_factory()
        full = self.normalized(140)
        registry = OOSRegistry(factory)
        train, holdout, split_index = registry.split_market(full, 0.2)
        save_market_snapshot(train)
        baseline = factory.baseline(
            intent="oos",
            dsl_code=DSL,
            market=train,
            instrument="EXT",
            timeframe="1d",
            source=train["_meta"]["source"],
        )
        split = registry.bind_split(baseline["root_id"], full, train, holdout, 0.2, split_index)
        self.assertEqual(baseline["provenance"]["data_hash"], split["train_data_hash"])
        self.assertNotEqual(split["train_data_hash"], split["holdout_data_hash"])
        evaluation = registry.evaluate(baseline["id"])
        self.assertEqual(evaluation["result"]["diagnostics"]["bars"], len(holdout["close"]))
        self.assertEqual(registry.result(baseline["id"])["holdout_data_hash"], split["holdout_data_hash"])

        other_train, other_holdout, other_index = registry.split_market(full, 0.25)
        with self.assertRaisesRegex(ValueError, "OOS split은 변경할 수 없습니다"):
            registry.bind_split(baseline["root_id"], full, other_train, other_holdout, 0.25, other_index)

        method = MethodologyValidator(factory.store).summarize(baseline["root_id"])
        self.assertTrue(method["oos"]["available"])
        self.assertEqual(method["oos"]["evaluated_experiments"], 1)
        self.assertEqual(method["claim"], "descriptive_only_until_OOS_and_multi_strategy_methodology_validation")


if __name__ == "__main__":
    unittest.main()
