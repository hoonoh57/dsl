import unittest

import numpy as np

from core.dsl_context import DSLContextSeriesBinding
from core.dsl_runtime import DSLRuntime, DSLRuntimeError
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


def manifest():
    return ParentFeatureManifest(
        provider_id="market_ctx_fixture",
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
            ParentFeatureSpec(
                feature_id="market.optional_note",
                feature_key="optional_note",
                value_type="STRING",
                required=False,
                missing_policy="OPTIONAL_ABSENT",
            ),
        ),
    )


def assembly(timestamp, slope, state, permitted, *, mode="DEPLOYMENT"):
    result = ParentFeatureProviderResult(
        manifest=manifest(),
        as_of=timestamp,
        knowledge_cutoff=timestamp,
        source="fixture://market/context",
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


def frame(mode="DEPLOYMENT"):
    registry = ParentFeatureRegistry((manifest(),))
    values = (
        assembly("20260827090000", -0.2, "RISK_OFF", False, mode=mode),
        assembly("20260827090500", 0.4, "RISK_ON", True, mode=mode),
        assembly("20260827091000", 0.8, "RISK_ON", True, mode=mode),
    )
    return registry, ParentContextFrame.create(
        frame_id="CTX_DSL_FIXTURE",
        target_symbol="005930",
        registry=registry,
        assemblies=values,
        mode=mode,
    )


def market():
    close = np.asarray([100.0, 101.0, 102.0])
    return {
        "open": close.copy(),
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.asarray([1000.0, 1100.0, 1200.0]),
        "date": np.asarray([20260827.0, 20260827.0, 20260827.0]),
        "time": np.asarray([90000.0, 90500.0, 91000.0]),
    }


TIMES = ("20260827090000", "20260827090500", "20260827091000")


class DSLParentContextTests(unittest.TestCase):
    def binding(self):
        registry, context_frame = frame()
        return DSLContextSeriesBinding.from_frame(
            frame=context_frame,
            registry=registry,
            target_times=TIMES,
        )

    def test_number_string_boolean_ctx_references_compile_as_typed_series(self):
        binding = self.binding()
        dsl = '''strategy "CtxTyped" {
            timeframe = "5m"
            scaled = ctx.market.kospi_slope * 2
            market_ok = ctx.market.kospi_slope > 0 and ctx.market.regime_state == "RISK_ON" and ctx.market.entry_permitted
            long_entry = market_ok
            long_exit = false
            on(long_entry) { order.buy(type = "MARKET") }
        }'''
        compiled = DSLRuntime.compile(
            dsl,
            market(),
            context_binding=binding,
            target_times=TIMES,
        )
        np.testing.assert_allclose(compiled.values["scaled"], [-0.4, 0.8, 1.6])
        np.testing.assert_array_equal(compiled.signal("long_entry", 3), [False, True, True])
        self.assertEqual(compiled.context_binding_hash, binding.binding_hash)

    def test_ctx_is_available_inside_causal_on_bar_without_provider_calls(self):
        binding = self.binding()
        dsl = '''strategy "CtxOnBar" {
            timeframe = "5m"
            state armed = false
            on_bar {
                if (ctx.market.entry_permitted and ctx.market.kospi_slope > 0) {
                    set armed = true
                }
            }
            long_entry = armed and ctx.market.regime_state == "RISK_ON"
            long_exit = false
        }'''
        compiled = DSLRuntime.compile(
            dsl,
            market(),
            context_binding=binding,
            target_times=TIMES,
        )
        np.testing.assert_array_equal(compiled.signal("long_entry", 3), [False, True, True])

    def test_ctx_requires_exact_deployment_binding(self):
        dsl = '''strategy "NeedsCtx" {
            timeframe = "5m"
            long_entry = ctx.market.kospi_slope > 0
            long_exit = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "binding"):
            DSLRuntime.compile(dsl, market())

        binding = self.binding()
        with self.assertRaisesRegex(DSLRuntimeError, "target_times"):
            DSLRuntime.compile(dsl, market(), context_binding=binding)
        with self.assertRaisesRegex(DSLRuntimeError, "exact"):
            DSLRuntime.compile(
                dsl,
                market(),
                context_binding=binding,
                target_times=(TIMES[0], TIMES[1], "20260827091500"),
            )

    def test_observed_frame_cannot_become_executable_ctx_binding(self):
        registry, observed = frame(mode="OBSERVED")
        with self.assertRaisesRegex(ValueError, "DEPLOYMENT"):
            DSLContextSeriesBinding.from_frame(
                frame=observed,
                registry=registry,
                target_times=TIMES,
            )

    def test_unknown_optional_history_and_ctx_reassignment_fail_closed(self):
        binding = self.binding()
        unknown = '''strategy "UnknownCtx" {
            timeframe = "5m"
            long_entry = ctx.market.not_registered > 0
            long_exit = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "등록/실행 바인딩되지 않은"):
            DSLRuntime.compile(unknown, market(), context_binding=binding, target_times=TIMES)

        optional = '''strategy "OptionalCtx" {
            timeframe = "5m"
            long_entry = ctx.market.optional_note == "GO"
            long_exit = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "등록/실행 바인딩되지 않은"):
            DSLRuntime.compile(optional, market(), context_binding=binding, target_times=TIMES)

        history = '''strategy "CtxHistory" {
            timeframe = "5m"
            prior = ctx.market.kospi_slope[1]
            long_entry = prior > 0
            long_exit = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "과거참조"):
            DSLRuntime.compile(history, market(), context_binding=binding, target_times=TIMES)

        reassignment = '''strategy "CtxReassign" {
            timeframe = "5m"
            ctx = 1
            long_entry = false
        }'''
        with self.assertRaisesRegex(DSLRuntimeError, "읽기 전용 namespace"):
            DSLRuntime.compile(reassignment, market())

    def test_binding_is_required_feature_only_and_deterministic(self):
        first = self.binding()
        second = self.binding()
        self.assertEqual(first.binding_hash, second.binding_hash)
        self.assertEqual(
            set(first.semantic_types()),
            {"market.kospi_slope", "market.regime_state", "market.entry_permitted"},
        )
        self.assertNotIn("market.optional_note", first.semantic_types())
        self.assertEqual(
            first.public_dict()["binding_policy"],
            "REGISTERED_REQUIRED_EXACT_TIME_DEPLOYMENT_ONLY_NO_PROVIDER_CALL",
        )


if __name__ == "__main__":
    unittest.main()
