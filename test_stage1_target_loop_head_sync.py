import tempfile
import unittest
from pathlib import Path

from core.strategy_factory import StrategyFactory, StrategyFactoryStore
from core.stage1_target_loop import TargetLoopService
from test_stage1_factory import BASE_DSL, oscillating_market


class Stage1TargetLoopHeadSyncTest(unittest.TestCase):
    def test_explicit_promotion_is_visible_on_next_loop_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            factory = StrategyFactory(StrategyFactoryStore(Path(tmp) / "stage1.db"))
            market = oscillating_market(80)
            baseline = factory.baseline(
                intent="head sync",
                dsl_code=BASE_DSL,
                market=market,
                instrument="TEST",
                timeframe="1d",
                source="unit",
            )
            child = factory.store.create_experiment(
                parent_id=baseline["id"],
                operation="SEEKER_BEST",
                strategy_name=baseline["strategy_name"],
                intent=baseline["intent"],
                dsl_code=baseline["dsl_code"],
                parameters={},
                execution=baseline["execution"],
                provenance=baseline["provenance"],
                result=baseline["result"],
                analysis=baseline["analysis"],
            )
            loops = TargetLoopService(factory)
            loop = loops.create(root_id=baseline["root_id"], target_return=999)
            self.assertEqual(loop["state"]["applied_head_experiment_id"], baseline["id"])

            factory.store.promote(child["id"])

            refreshed = loops.get(loop["id"])
            self.assertEqual(refreshed["state"]["applied_head_experiment_id"], child["id"])


if __name__ == "__main__":
    unittest.main()
