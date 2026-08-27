import unittest

from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntimeError
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


TIMES = (
    "20260827090000",
    "20260827090500",
    "20260827091000",
    "20260827091500",
)


def manifest():
    return ParentFeatureManifest(
        provider_id="market_ctx_backtest_fixture",
        provider_version="v1",
        layer="MARKET",
        context_id="KOSPI_REGIME",
        features=(
            ParentFeatureSpec(
                feature_id="market.kospi_slope",
                feature_key="kospi_slope",
                value_type="NUMBER",
            ),
            ParentFeatureSpec(
                feature_id="market.regime_state",
                feature_key="regime_state",
                value_type="STRING",
            ),
            ParentFeatureSpec(
                feature_id="market.entry_permitted",
                feature_key="entry_permitted",
                value_type="BOOLEAN",
            ),
        ),
    )


def assembly(timestamp, slope, state, permitted, *, mode="DEPLOYMENT"):
    result = ParentFeatureProviderResult(
        manifest=manifest(),
        as_of=timestamp,
        knowledge_cutoff=timestamp,
        source="fixture://ctxbt1/market",
        features={
            "kospi_slope": slope,
            "regime_state": state,
            "entry_permitted": permitted,
        },
    )
    return ParentContextAssembler.assemble(
        as_of=timestamp,
        knowledge_cutoff=timestamp,
        results=(result,),
        mode=mode,
    )


def context_frame(*, mode="DEPLOYMENT", include_last=True, symbol="005930"):
    registry = ParentFeatureRegistry((manifest(),))
    rows = (
        assembly(TIMES[0], -0.2, "RISK_OFF", False, mode=mode),
        assembly(TIMES[1], 0.4, "RISK_ON", True, mode=mode),
        assembly(TIMES[2], 0.8, "RISK_ON", True, mode=mode),
        assembly(TIMES[3], -0.1, "RISK_OFF", False, mode=mode),
    )
    if not include_last:
        rows = rows[:-1]
    frame = ParentContextFrame.create(
        frame_id="CTXBT1_FIXTURE",
        target_symbol=symbol,
        registry=registry,
        assemblies=rows,
        mode=mode,
    )
    return registry, frame


def market(*, symbol="005930"):
    close = [100.0, 101.0, 102.0, 103.0]
    return {
        "time": list(TIMES),
        "open": close.copy(),
        "high": [value + 1.0 for value in close],
        "low": [value - 1.0 for value in close],
        "close": close,
        "volume": [1000.0, 1100.0, 1200.0, 1300.0],
        "_meta": {
            "source": "fixture://ctxbt1/market-bars",
            "timeframe": "5m",
            "instrument": symbol,
        },
    }


CTX_DSL = '''strategy "CtxBacktest" {
    timeframe = "5m"
    market_ok = ctx.market.entry_permitted and ctx.market.kospi_slope > 0 and ctx.market.regime_state == "RISK_ON"
    long_entry = market_ok
    long_exit = not ctx.market.entry_permitted
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''

PLAIN_DSL = '''strategy "PlainBacktest" {
    timeframe = "5m"
    long_entry = close > 100
    long_exit = close >= 103
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


class BacktestParentContextTests(unittest.TestCase):
    def test_backtest_consumes_exact_deployment_context_without_broker_changes(self):
        registry, frame = context_frame()
        result = BacktestEngine.run(
            CTX_DSL,
            market=market(),
            parent_context_frame=frame,
            parent_feature_registry=registry,
        )
        entries = [item for item in result["trades"] if item["kind"] == "ENTRY"]
        exits = [item for item in result["trades"] if item["kind"] == "EXIT"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(exits), 1)
        self.assertEqual(str(entries[0]["signal_time"]), TIMES[1])
        self.assertEqual(str(exits[0]["signal_time"]), TIMES[3])
        diagnostics = result["diagnostics"]["parent_context"]
        self.assertTrue(diagnostics["supplied"])
        self.assertEqual(diagnostics["target_symbol"], "005930")
        self.assertEqual(diagnostics["bar_count"], 4)
        self.assertTrue(diagnostics["binding_hash"])
        self.assertEqual(result["diagnostics"]["execution_authority"], "BrokerEmulator")

    def test_external_entry_gate_remains_separate_and_can_only_restrict(self):
        registry, frame = context_frame()
        result = BacktestEngine.run(
            CTX_DSL,
            market=market(),
            parent_context_frame=frame,
            parent_feature_registry=registry,
            entry_gate=[False, False, False, False],
        )
        self.assertFalse([item for item in result["trades"] if item["kind"] == "ENTRY"])
        self.assertGreater(result["diagnostics"]["rejections"]["higher_layer_gate_blocked"], 0)
        self.assertTrue(result["diagnostics"]["entry_policy"]["higher_layer_gate_supplied"])

    def test_context_is_not_an_implicit_entry_gate_when_dsl_does_not_reference_it(self):
        registry, frame = context_frame()
        baseline = BacktestEngine.run(PLAIN_DSL, market=market())
        contextual = BacktestEngine.run(
            PLAIN_DSL,
            market=market(),
            parent_context_frame=frame,
            parent_feature_registry=registry,
        )
        self.assertEqual(baseline["trades"], contextual["trades"])
        self.assertEqual(baseline["closed_trades"], contextual["closed_trades"])
        self.assertEqual(baseline["metrics_numeric"], contextual["metrics_numeric"])
        self.assertFalse(baseline["diagnostics"]["parent_context"]["supplied"])
        self.assertTrue(contextual["diagnostics"]["parent_context"]["supplied"])

    def test_frame_registry_symbol_and_exact_time_mismatches_fail_closed(self):
        registry, frame = context_frame()
        with self.assertRaisesRegex(ValueError, "함께 제공"):
            BacktestEngine.run(CTX_DSL, market=market(), parent_context_frame=frame)
        with self.assertRaisesRegex(ValueError, "instrument"):
            BacktestEngine.run(
                CTX_DSL,
                market=market(symbol="000660"),
                parent_context_frame=frame,
                parent_feature_registry=registry,
            )

        short_registry, short_frame = context_frame(include_last=False)
        with self.assertRaisesRegex(ValueError, "exact binding"):
            BacktestEngine.run(
                CTX_DSL,
                market=market(),
                parent_context_frame=short_frame,
                parent_feature_registry=short_registry,
            )

    def test_observed_context_and_unbound_ctx_dsl_fail_closed(self):
        registry, observed = context_frame(mode="OBSERVED")
        with self.assertRaisesRegex(ValueError, "DEPLOYMENT"):
            BacktestEngine.run(
                CTX_DSL,
                market=market(),
                parent_context_frame=observed,
                parent_feature_registry=registry,
            )
        with self.assertRaisesRegex(DSLRuntimeError, "binding"):
            BacktestEngine.run(CTX_DSL, market=market())


if __name__ == "__main__":
    unittest.main()
