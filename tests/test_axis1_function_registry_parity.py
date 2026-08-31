from __future__ import annotations

import inspect
import unittest

from core import function_registry as legacy
from axes.axis1_dsl.core import function_registry as axis1


class Axis1FunctionRegistryParityTests(unittest.TestCase):
    def test_legacy_function_specs_are_preserved(self):
        self.assertTrue(set(legacy.FUNCTION_SPECS).issubset(axis1.FUNCTION_SPECS))
        for name, expected in legacy.FUNCTION_SPECS.items():
            actual = axis1.FUNCTION_SPECS[name]
            self.assertEqual(
                (actual.name, actual.minimum, actual.maximum, actual.returns, actual.signature, actual.category),
                (expected.name, expected.minimum, expected.maximum, expected.returns, expected.signature, expected.category),
                name,
            )

    def test_legacy_category_order_is_preserved(self):
        categories = {spec.category for spec in legacy.FUNCTION_SPECS.values()}
        legacy_names = set(legacy.FUNCTION_SPECS)
        for category in categories:
            expected = [spec.name for spec in legacy.specs_by_category(category)]
            actual = [
                spec.name
                for spec in axis1.specs_by_category(category)
                if spec.name in legacy_names
            ]
            self.assertEqual(actual, expected, category)

    def test_legacy_manifest_lines_are_preserved(self):
        categories = {spec.category for spec in legacy.FUNCTION_SPECS.values()}
        legacy_signatures = {spec.signature for spec in legacy.FUNCTION_SPECS.values()}
        for category in categories:
            expected = legacy.manifest_lines(category)
            actual = [
                line
                for line in axis1.manifest_lines(category)
                if line in legacy_signatures
            ]
            self.assertEqual(actual, expected, category)

    def test_axis1_registry_has_no_legacy_core_runtime_import(self):
        source = inspect.getsource(axis1)
        self.assertNotIn("from core", source)
        self.assertNotIn("import core", source)


if __name__ == "__main__":
    unittest.main()
