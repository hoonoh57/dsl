import unittest

from core.parent_context_frame import ParentContextBinder, ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


def market_manifest(version="v1"):
    return ParentFeatureManifest(
        provider_id="market_feature_provider",
        provider_version=version,
        layer="MARKET",
        context_id="KOSPI_REGIME",
        max_staleness_seconds=300,
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
                feature_id="market.breadth_confirmed",
                feature_key="breadth_confirmed",
                value_type="BOOLEAN",
                required=False,
                missing_policy="OPTIONAL_ABSENT",
            ),
        ),
    )


def sector_manifest():
    return ParentFeatureManifest(
        provider_id="sector_feature_provider",
        provider_version="v1",
        layer="SECTOR",
        context_id="SEMICONDUCTOR",
        max_staleness_seconds=300,
        features=(
            ParentFeatureSpec(
                feature_id="sector.relative_strength",
                feature_key="relative_strength",
                value_type="NUMBER",
            ),
        ),
    )


def assembly(cutoff, *, version="v1", context_as_of=None, slope=0.4, state="RISK_ON", mode="OBSERVED"):
    digits = "".join(ch for ch in str(cutoff) if ch.isdigit())[:14]
    minute = int(digits[-4:-2])
    result_as_of = digits[:10] + f"{max(0, minute - 1):02d}" + digits[-2:]
    result = ParentFeatureProviderResult(
        manifest=market_manifest(version),
        as_of=result_as_of,
        knowledge_cutoff=digits,
        source="fixture://market/kospi",
        features={"kospi_slope": slope, "regime_state": state},
    )
    return ParentContextAssembler.assemble(
        as_of=context_as_of or digits,
        knowledge_cutoff=digits,
        results=(result,),
        mode=mode,
    )


class ParentContextFrameTests(unittest.TestCase):
    def test_frame_is_exact_time_deterministic_and_input_order_independent(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        a0930 = assembly("20260827093000", slope=0.4)
        a0935 = assembly("20260827093500", slope=0.6)
        first = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(a0930, a0935),
        )
        second = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(a0935, a0930),
        )
        self.assertEqual(first.frame_hash, second.frame_hash)
        self.assertEqual(
            [row["target_time"] for row in first.public_dict()["points"]],
            ["20260827093000", "20260827093500"],
        )
        self.assertEqual(
            first.public_dict()["resolution_policy"],
            "EXACT_PRECOMPUTED_POINT_ONLY_NO_NEAREST_NO_FILL_FORWARD",
        )
        self.assertEqual(first.resolve_exact("2026-08-27 09:35:00").context_hash, a0935.context.context_hash)

    def test_frame_never_uses_nearest_or_fill_forward(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        frame = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(assembly("20260827093000"), assembly("20260827093500")),
        )
        with self.assertRaisesRegex(KeyError, "nearest/fill-forward"):
            frame.resolve_exact("20260827093200")

    def test_frame_requires_exact_target_cutoff_and_context_as_of(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        wrong_as_of = assembly(
            "20260827093000",
            context_as_of="20260827092900",
        )
        with self.assertRaisesRegex(ValueError, "exact context as_of"):
            ParentContextFrame.create(
                frame_id="KOSPI_INTRADAY",
                target_symbol="005930",
                registry=registry,
                assemblies=(wrong_as_of,),
            )

    def test_frame_rejects_provider_manifest_drift_mid_timeline(self):
        registry = ParentFeatureRegistry((market_manifest("v1"),))
        with self.assertRaisesRegex(ValueError, "topology"):
            ParentContextFrame.create(
                frame_id="KOSPI_INTRADAY",
                target_symbol="005930",
                registry=registry,
                assemblies=(
                    assembly("20260827093000", version="v1"),
                    assembly("20260827093500", version="v2"),
                ),
            )

    def test_binder_resolves_registered_features_and_preserves_optional_absence(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        frame = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(assembly("20260827093000", slope=0.47),),
        )
        binding = ParentContextBinder.bind(
            frame=frame,
            registry=registry,
            target_time="20260827093000",
            feature_ids=(
                "market.regime_state",
                "market.breadth_confirmed",
                "market.kospi_slope",
            ),
        )
        values = {item.feature_id: item for item in binding.values}
        self.assertTrue(values["market.kospi_slope"].present)
        self.assertEqual(values["market.kospi_slope"].value, 0.47)
        self.assertEqual(values["market.regime_state"].value, "RISK_ON")
        self.assertFalse(values["market.breadth_confirmed"].present)
        self.assertIsNone(values["market.breadth_confirmed"].public_dict()["value"])
        self.assertEqual(
            binding.public_dict()["binding_policy"],
            "REGISTERED_READ_ONLY_EXACT_TIME_NO_PROVIDER_CALL",
        )

    def test_binder_identity_is_independent_of_requested_feature_order(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        frame = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(assembly("20260827093000"),),
        )
        a = ParentContextBinder.bind(
            frame=frame,
            registry=registry,
            target_time="20260827093000",
            feature_ids=("market.kospi_slope", "market.regime_state"),
        )
        b = ParentContextBinder.bind(
            frame=frame,
            registry=registry,
            target_time="20260827093000",
            feature_ids=("market.regime_state", "market.kospi_slope"),
        )
        self.assertEqual(a.binding_hash, b.binding_hash)

    def test_binder_fails_closed_on_unknown_feature_registry_mismatch_and_missing_point(self):
        registry = ParentFeatureRegistry((market_manifest(),))
        frame = ParentContextFrame.create(
            frame_id="KOSPI_INTRADAY",
            target_symbol="005930",
            registry=registry,
            assemblies=(assembly("20260827093000"),),
        )
        with self.assertRaisesRegex(ValueError, "등록되지 않은"):
            ParentContextBinder.bind(
                frame=frame,
                registry=registry,
                target_time="20260827093000",
                feature_ids=("market.not_registered",),
            )
        other_registry = ParentFeatureRegistry((sector_manifest(),))
        with self.assertRaisesRegex(ValueError, "registry_hash"):
            ParentContextBinder.bind(
                frame=frame,
                registry=other_registry,
                target_time="20260827093000",
                feature_ids=("sector.relative_strength",),
            )
        with self.assertRaisesRegex(KeyError, "exact parent context point"):
            ParentContextBinder.bind(
                frame=frame,
                registry=registry,
                target_time="20260827093100",
                feature_ids=("market.kospi_slope",),
            )


if __name__ == "__main__":
    unittest.main()
