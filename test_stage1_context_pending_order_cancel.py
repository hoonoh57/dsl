import unittest

from core.backtest import BacktestEngine
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


TIMES = (
    "20260828090000",
    "20260828090500",
    "20260828091000",
    "20260828091500",
)


def manifest():
    return ParentFeatureManifest(
        provider_id="context_cancel_fixture",
        provider_version="v1",
        layer="MARKET",
        context_id="ENTRY_PERMISSION",
        features=(
            ParentFeatureSpec(
                feature_id="market.entry_permitted",
                feature_key="entry_permitted",
                value_type="BOOLEAN",
            ),
        ),
    )


def assembly(timestamp, permitted):
    result = ParentFeatureProviderResult(
        manifest=manifest(),
        as_of=timestamp,
        knowledge_cutoff=timestamp,
        source="fixture://context-cancel",
        features={"entry_permitted": permitted},
    )
    return ParentContextAssembler.assemble(
        as_of=timestamp,
        knowledge_cutoff=timestamp,
        results=(result,),
        mode="DEPLOYMENT",
    )


def context_frame():
    registry = ParentFeatureRegistry((manifest(),))
    frame = ParentContextFrame.create(
        frame_id="CONTEXT_CANCEL_FIXTURE",
        target_symbol="005930",
        registry=registry,
        assemblies=(
            assembly(TIMES[0], True),
            assembly(TIMES[1], False),
            assembly(TIMES[2], False),
            assembly(TIMES[3], False),
        ),
        mode="DEPLOYMENT",
    )
    return registry, frame


def market():
    return {
        "time": list(TIMES),
        "open": [100.0, 100.0, 100.0, 100.0],
        "high": [101.0, 101.0, 101.0, 101.0],
        "low": [99.0, 95.0, 80.0, 80.0],
        "close": [100.0, 100.0, 100.0, 100.0],
        "volume": [1000.0, 1000.0, 1000.0, 1000.0],
        "_meta": {
            "source": "fixture://context-cancel-bars",
            "timeframe": "5m",
            "instrument": "005930",
        },
    }


DSL = '''strategy "ContextPendingCancel" {
    timeframe = "5m"
    local_setup = close >= 100
    context_ok = ctx.market.entry_permitted
    on(local_setup and context_ok) {
        order.buy(type="LIMIT", id="entry-1", limit=90)
    }
    on(not context_ok) {
        order.cancel(id="entry-1")
    }
}'''


class ContextPendingOrderCancelCompositionTests(unittest.TestCase):
    def run_case(self, signal_mode):
        registry, frame = context_frame()
        return BacktestEngine.run(
            DSL,
            market=market(),
            settings={"signal_mode": signal_mode},
            parent_context_frame=frame,
            parent_feature_registry=registry,
        )

    def test_bar_close_context_invalidation_cancels_pending_before_later_fill(self):
        result = self.run_case("bar_close")
        history = result["diagnostics"]["pending_order_history"]
        self.assertEqual([row["status"] for row in history], ["CREATED", "ACCEPTED", "CANCELED"])
        self.assertEqual(history[-1]["client_order_id"], "entry-1")
        self.assertEqual(history[-1]["event"], TIMES[1])
        self.assertEqual(history[-1]["reason"], "DSL cancel")
        self.assertEqual(result["metrics_numeric"]["trade_count"], 0)
        self.assertTrue(result["diagnostics"]["parent_context"]["supplied"])
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")

    def test_next_open_uses_prior_completed_context_to_cancel_before_fill_bar_matching(self):
        result = self.run_case("next_open")
        history = result["diagnostics"]["pending_order_history"]
        self.assertEqual([row["status"] for row in history], ["CREATED", "ACCEPTED", "CANCELED"])
        self.assertEqual(history[-1]["client_order_id"], "entry-1")
        self.assertEqual(history[-1]["event"], TIMES[2])
        self.assertEqual(result["metrics_numeric"]["trade_count"], 0)
        self.assertTrue(result["diagnostics"]["parent_context"]["supplied"])
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")


if __name__ == "__main__":
    unittest.main()
