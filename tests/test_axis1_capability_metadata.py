from __future__ import annotations

from pathlib import Path
import unittest

from axes.axis1_dsl.core.capability_metadata import (
    FUNCTION_CAPABILITIES,
    INCREMENTAL_NOT_CERTIFIED,
    MULTI_OUTPUT_CAPABILITIES,
    capability_for,
    capability_manifest,
)
from axes.axis1_dsl.core.function_registry import FUNCTION_SPECS
from axes.axis1_dsl.core.multi_output import MULTI_OUTPUT_SPECS


class Axis1CapabilityMetadataTests(unittest.TestCase):
    def test_every_registered_function_has_complete_metadata(self):
        self.assertEqual(set(FUNCTION_CAPABILITIES), set(FUNCTION_SPECS))
        for name, spec in FUNCTION_SPECS.items():
            with self.subTest(name=name):
                item = FUNCTION_CAPABILITIES[name]
                item.validate()
                self.assertEqual(item.name, name)
                self.assertEqual(item.mode, "single_output")
                self.assertEqual(item.category, spec.category)
                self.assertEqual(item.signature, spec.signature)
                self.assertEqual(item.output_names, ("value",))
                self.assertEqual(item.output_types, (spec.returns,))
                self.assertEqual(item.incremental_identity, INCREMENTAL_NOT_CERTIFIED)

    def test_every_multi_output_contract_has_component_metadata(self):
        self.assertEqual(set(MULTI_OUTPUT_CAPABILITIES), set(MULTI_OUTPUT_SPECS))
        for name, spec in MULTI_OUTPUT_SPECS.items():
            with self.subTest(name=name):
                item = MULTI_OUTPUT_CAPABILITIES[name]
                item.validate()
                self.assertEqual(item.name, name)
                self.assertEqual(item.mode, "multi_output")
                self.assertEqual(item.signature, spec.signature)
                self.assertEqual(item.output_names, spec.components)
                self.assertEqual(item.output_types, spec.component_types)
                self.assertEqual(item.incremental_identity, INCREMENTAL_NOT_CERTIFIED)

    def test_causality_and_missing_value_policies_are_explicit(self):
        mtf = capability_for("mtf.close")
        self.assertIn("confirmed parent", mtf.causality)
        self.assertIn("no nearest-time", mtf.nan_policy)

        jma = capability_for("ta.jma")
        self.assertIn("current and past", jma.causality)
        self.assertIn("kernel", jma.nan_policy)

        state = capability_for("state.latch")
        self.assertIn("ordered", state.causality)
        self.assertIn("state", state.warmup)

        macd_all = capability_for("user.macd_normalized_all", mode="multi_output")
        self.assertEqual(macd_all.output_names, ("macd", "signal", "hist", "hist_abs_pct"))
        self.assertIn("zero denominator", macd_all.nan_policy)

    def test_manifest_is_deterministic_and_mode_disambiguates_same_function_name(self):
        first = capability_manifest()
        second = capability_manifest()
        self.assertEqual(first, second)
        identities = [(item["name"], item["mode"]) for item in first]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertIn(("ta.supertrend", "single_output"), identities)
        self.assertIn(("ta.supertrend", "multi_output"), identities)

    def test_new_metadata_layer_does_not_import_frozen_core(self):
        import axes.axis1_dsl.core.capability_metadata as metadata

        source = Path(metadata.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
