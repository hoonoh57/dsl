import unittest

from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


def market_manifest(version="v1", *, staleness=300):
    return ParentFeatureManifest(
        provider_id="market_feature_provider",
        provider_version=version,
        layer="MARKET",
        context_id="KOSPI_REGIME",
        max_staleness_seconds=staleness,
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


def market_result(version="v1"):
    return ParentFeatureProviderResult(
        manifest=market_manifest(version),
        as_of="20260827092900",
        knowledge_cutoff="20260827093000",
        source="fixture://market/kospi",
        features={"kospi_slope": 0.47, "regime_state": "RISK_ON"},
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


class ParentFeatureProviderTests(unittest.TestCase):
    def test_manifest_registry_is_typed_discoverable_and_order_independent(self):
        market = market_manifest()
        sector = sector_manifest()
        registry_a = ParentFeatureRegistry((market, sector))
        registry_b = ParentFeatureRegistry((sector, market))
        self.assertEqual(registry_a.registry_hash, registry_b.registry_hash)
        resolved = registry_a.resolve("market.kospi_slope")
        self.assertEqual(resolved["feature"]["value_type"], "NUMBER")
        self.assertEqual(resolved["manifest"]["provider_id"], "market_feature_provider")
        self.assertEqual(resolved["manifest"]["layer"], "MARKET")
        with self.assertRaises(KeyError):
            registry_a.resolve("market.not_registered")

    def test_provider_result_fails_closed_on_future_stale_missing_unknown_and_type_mismatch(self):
        manifest = market_manifest(staleness=60)
        with self.assertRaisesRegex(ValueError, "미래"):
            ParentFeatureProviderResult(
                manifest=manifest,
                as_of="20260827093100",
                knowledge_cutoff="20260827093000",
                source="fixture://market",
                features={"kospi_slope": 0.4, "regime_state": "RISK_ON"},
            ).validate()
        with self.assertRaisesRegex(ValueError, "staleness"):
            ParentFeatureProviderResult(
                manifest=manifest,
                as_of="20260827092800",
                knowledge_cutoff="20260827093000",
                source="fixture://market",
                features={"kospi_slope": 0.4, "regime_state": "RISK_ON"},
            ).validate()
        with self.assertRaisesRegex(ValueError, "required"):
            ParentFeatureProviderResult(
                manifest=manifest,
                as_of="20260827092930",
                knowledge_cutoff="20260827093000",
                source="fixture://market",
                features={"regime_state": "RISK_ON"},
            ).validate()
        with self.assertRaisesRegex(ValueError, "선언되지 않은"):
            ParentFeatureProviderResult(
                manifest=manifest,
                as_of="20260827092930",
                knowledge_cutoff="20260827093000",
                source="fixture://market",
                features={
                    "kospi_slope": 0.4,
                    "regime_state": "RISK_ON",
                    "secret_future_score": 99.0,
                },
            ).validate()
        with self.assertRaisesRegex(ValueError, "NUMBER"):
            ParentFeatureProviderResult(
                manifest=manifest,
                as_of="20260827092930",
                knowledge_cutoff="20260827093000",
                source="fixture://market",
                features={"kospi_slope": "UP", "regime_state": "RISK_ON"},
            ).validate()

    def test_optional_feature_may_be_absent_but_is_never_silently_defaulted(self):
        result = market_result()
        result.validate()
        public = result.public_dict()
        self.assertNotIn("breadth_confirmed", public["features"])
        self.assertEqual(public["manifest"]["features"][0]["causality_policy"], "CONFIRMED_ONLY")

    def test_cascading_assembly_is_order_independent_and_carries_provenance(self):
        market = market_result()
        sector = ParentFeatureProviderResult(
            manifest=sector_manifest(),
            as_of="20260827092930",
            knowledge_cutoff="20260827093000",
            source="fixture://sector/semiconductor",
            features={"relative_strength": 1.35},
            dependency_result_hashes=(market.result_hash,),
        )
        first = ParentContextAssembler.assemble(
            as_of="20260827093000",
            knowledge_cutoff="20260827093000",
            results=(market, sector),
            mode="OBSERVED",
        )
        second = ParentContextAssembler.assemble(
            as_of="20260827093000",
            knowledge_cutoff="20260827093000",
            results=(sector, market),
            mode="OBSERVED",
        )
        self.assertEqual(first.assembly_hash, second.assembly_hash)
        self.assertEqual(first.context.context_hash, second.context.context_hash)
        self.assertEqual(first.context.mode, "OBSERVED")
        self.assertEqual(len(first.context.layers), 2)
        self.assertEqual(
            first.context.metadata["assembly_policy"],
            "PRECOMPUTED_IMMUTABLE_CAUSAL_PROVIDER_RESULTS_ONLY",
        )
        self.assertIn(market.result_hash, first.context.metadata["parent_feature_result_hashes"])
        self.assertIn(sector.result_hash, first.context.metadata["parent_feature_result_hashes"])

    def test_assembly_rejects_missing_or_future_dependency(self):
        market = market_result()
        missing_dependency = ParentFeatureProviderResult(
            manifest=sector_manifest(),
            as_of="20260827092930",
            knowledge_cutoff="20260827093000",
            source="fixture://sector",
            features={"relative_strength": 1.2},
            dependency_result_hashes=("missing-parent-result",),
        )
        with self.assertRaisesRegex(ValueError, "dependency"):
            ParentContextAssembler.assemble(
                as_of="20260827093000",
                knowledge_cutoff="20260827093000",
                results=(market, missing_dependency),
            )

        late_market = ParentFeatureProviderResult(
            manifest=market_manifest(staleness=300),
            as_of="20260827092950",
            knowledge_cutoff="20260827093000",
            source="fixture://market",
            features={"kospi_slope": 0.5, "regime_state": "RISK_ON"},
        )
        early_sector = ParentFeatureProviderResult(
            manifest=sector_manifest(),
            as_of="20260827092940",
            knowledge_cutoff="20260827093000",
            source="fixture://sector",
            features={"relative_strength": 1.2},
            dependency_result_hashes=(late_market.result_hash,),
        )
        with self.assertRaisesRegex(ValueError, "dependency.*미래"):
            ParentContextAssembler.assemble(
                as_of="20260827093000",
                knowledge_cutoff="20260827093000",
                results=(late_market, early_sector),
            )

    def test_provider_version_is_part_of_context_provenance(self):
        v1 = ParentContextAssembler.assemble(
            as_of="20260827093000",
            knowledge_cutoff="20260827093000",
            results=(market_result("v1"),),
        )
        v2 = ParentContextAssembler.assemble(
            as_of="20260827093000",
            knowledge_cutoff="20260827093000",
            results=(market_result("v2"),),
        )
        self.assertNotEqual(v1.context.context_hash, v2.context.context_hash)
        self.assertNotEqual(v1.assembly_hash, v2.assembly_hash)

    def test_assembler_never_accepts_neutral_mode_with_parent_results(self):
        with self.assertRaisesRegex(ValueError, "OBSERVED 또는 DEPLOYMENT"):
            ParentContextAssembler.assemble(
                as_of="20260827093000",
                knowledge_cutoff="20260827093000",
                results=(market_result(),),
                mode="NEUTRAL",
            )


if __name__ == "__main__":
    unittest.main()
