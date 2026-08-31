from __future__ import annotations

from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest

import numpy as np

from axes.axis1_dsl.core.capability_metadata import capability_manifest
from axes.axis1_dsl.core.capability_diagnostic_registry import (
    CapabilityRegistryError,
    REGISTRY_SCHEMA,
    capability_record,
    capability_records,
    diagnostic_record,
    diagnostic_records,
    registry_hash,
    registry_snapshot,
    require_supported,
    validate_registry,
)
from axes.axis1_dsl.execution.axis1_backtest import Axis1BacktestEngine


class Axis1CapabilityDiagnosticRegistryTests(unittest.TestCase):
    @staticmethod
    def _market(size=8):
        start = datetime(2026, 1, 2, 9, 0)
        close = np.asarray([100.0 + i * 0.5 for i in range(size)], dtype=float)
        return {
            "time": [(start + timedelta(minutes=5 * i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(size)],
            "open": close - 0.2,
            "high": close + 0.7,
            "low": close - 0.8,
            "close": close,
            "volume": np.asarray([1000.0 + i * 10.0 for i in range(size)]),
            "_meta": {"source": "registry_fixture", "timeframe": "5m"},
        }

    def test_registry_is_valid_json_serializable_and_hash_stable(self):
        validate_registry()
        first = registry_snapshot()
        second = registry_snapshot()
        self.assertEqual(first["schema"], REGISTRY_SCHEMA)
        self.assertEqual(first, second)
        self.assertEqual(first["registry_hash"], registry_hash())
        self.assertEqual(len(first["registry_hash"]), 64)
        encoded = json.dumps(first, ensure_ascii=False, sort_keys=True)
        self.assertIn(REGISTRY_SCHEMA, encoded)

    def test_every_function_capability_metadata_item_has_exact_registry_record(self):
        expected = {
            f"function:{item['mode']}:{item['name']}"
            for item in capability_manifest()
        }
        actual = {
            item["capability_id"]
            for item in capability_records()
            if item["kind"] == "function"
        }
        self.assertEqual(actual, expected)
        for item in capability_manifest():
            record = capability_record(f"function:{item['mode']}:{item['name']}")
            self.assertEqual(tuple(record["details"]["output_names"]), tuple(item["output_names"]))
            self.assertEqual(tuple(record["details"]["output_types"]), tuple(item["output_types"]))
            self.assertEqual(record["details"]["nan_policy"], item["nan_policy"])
            self.assertEqual(record["details"]["causality"], item["causality"])
            self.assertEqual(record["details"]["incremental_identity"], item["incremental_identity"])

    def test_step5_feature_boundaries_are_machine_readable_and_fail_closed(self):
        supported = {
            "dsl.multi_output",
            "dsl.user_functions",
            "dsl.bounded_loops",
            "runtime.intrabar_state",
            "execution.partial_fills",
            "execution.pyramiding",
            "projection.generic",
        }
        for identity in supported:
            with self.subTest(identity=identity):
                record = require_supported(identity)
                self.assertIn(record["status"], {"SUPPORTED", "SUPPORTED_WITH_BOUNDARY"})
                self.assertTrue(record["deterministic"])
                self.assertTrue(record["causal"])
                self.assertTrue(record["verification"])

        self.assertEqual(capability_record("execution.hedging")["status"], "NOT_SUPPORTED")
        self.assertEqual(
            capability_record("runtime.optimized_incremental_kernel")["status"],
            "NOT_CERTIFIED",
        )
        with self.assertRaises(CapabilityRegistryError) as ctx:
            require_supported("execution.hedging")
        self.assertEqual(ctx.exception.code, "CAPABILITY_NOT_SUPPORTED")
        with self.assertRaises(CapabilityRegistryError) as ctx:
            capability_record("does.not.exist")
        self.assertEqual(ctx.exception.code, "UNKNOWN_CAPABILITY")

    def test_backtest_facade_emitted_diagnostics_have_registered_contracts(self):
        code = '''strategy "RegistryFixture" {
    timeframe = "5m"
    baseline = ta.sma(close, 2)
}'''
        result = Axis1BacktestEngine.run(code, market=self._market(), data_timeframe="5m")
        diagnostics = result["diagnostics"]
        expected_paths = {
            "diagnostics.signal_counts",
            "diagnostics.rejections",
            "diagnostics.broker_history",
            "diagnostics.parent_context",
            "diagnostics.entry_policy",
            "diagnostics.bounded_loops",
            "diagnostics.user_functions",
            "diagnostics.multi_output",
            "diagnostics.projection",
        }
        registered_paths = {item["path"] for item in diagnostic_records()}
        self.assertTrue(expected_paths <= registered_paths)
        for path in expected_paths:
            key = path.split(".", 1)[1]
            self.assertIn(key, diagnostics)

        for diagnostic_id in (
            "facade.bounded_loops",
            "facade.user_functions",
            "facade.multi_output",
            "backtest.broker_history",
            "pyramiding.position",
            "parity.runtime_report",
        ):
            record = diagnostic_record(diagnostic_id)
            self.assertTrue(record["producer"])
            self.assertTrue(record["authority"])
            self.assertTrue(record["semantics"])

    def test_registry_separates_product_support_from_verification_only_capabilities(self):
        reference = capability_record("verification.reference_differential")
        parity = capability_record("verification.batch_stream_parity")
        self.assertEqual(reference["status"], "VERIFICATION_ONLY")
        self.assertEqual(parity["status"], "VERIFICATION_ONLY")
        with self.assertRaises(CapabilityRegistryError):
            require_supported("verification.reference_differential")

    def test_registry_layer_has_no_frozen_core_or_execution_kernel_import(self):
        import axes.axis1_dsl.core.capability_diagnostic_registry as registry

        source = Path(registry.__file__).read_text(encoding="utf-8")
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)
        self.assertNotIn("from axes.axis1_dsl.execution", source)
        self.assertNotIn("from axes.axis1_dsl.runtime", source)
        self.assertNotIn("from axes.axis1_dsl.indicators", source)


if __name__ == "__main__":
    unittest.main()
