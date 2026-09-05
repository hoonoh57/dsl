import unittest

from core.function_registry import FUNCTION_SPECS
from core.indicator_catalog import (
    INDICATOR_CATALOG_SCHEMA,
    get_indicator_spec,
    indicator_catalog_payload,
    indicator_specs,
)


class IndicatorCatalogTests(unittest.TestCase):
    def test_catalog_is_small_and_deterministic(self):
        self.assertEqual(tuple(item.id for item in indicator_specs()), ("jma", "supertrend", "atr"))
        payload = indicator_catalog_payload()
        self.assertEqual(payload["schema"], INDICATOR_CATALOG_SCHEMA)
        self.assertEqual([item["id"] for item in payload["indicators"]], ["jma", "supertrend", "atr"])

    def test_every_indicator_uses_registered_dsl_capability(self):
        for item in indicator_specs():
            with self.subTest(item=item.id):
                self.assertIn(item.capability, FUNCTION_SPECS)
                self.assertEqual(FUNCTION_SPECS[item.capability].category, "ta")
                self.assertEqual(item.public_dict()["signature"], FUNCTION_SPECS[item.capability].signature)
                self.assertEqual(get_indicator_spec(item.id), item)

    def test_renderer_contract_is_catalog_owned(self):
        self.assertEqual(
            get_indicator_spec("jma").public_dict()["renderer"],
            {"kind": "line", "pane": "price", "color_by_direction": True},
        )
        self.assertEqual(
            get_indicator_spec("supertrend").public_dict()["renderer"],
            {"kind": "line", "pane": "price", "color_by_direction": True},
        )
        self.assertEqual(
            get_indicator_spec("atr").public_dict()["renderer"],
            {"kind": "line", "pane": "separate", "color_by_direction": False},
        )

    def test_default_expressions_are_exact_dsl(self):
        self.assertEqual(get_indicator_spec("jma").expression(), "ta.jma(close, 20, 0, 2)")
        self.assertEqual(get_indicator_spec("supertrend").expression(), "ta.supertrend(10, 3)")
        self.assertEqual(get_indicator_spec("atr").expression(), "ta.atr(14)")

    def test_custom_parameters_emit_exact_dsl(self):
        self.assertEqual(
            get_indicator_spec("jma").expression({"length": 7, "phase": -25, "power": 3}),
            "ta.jma(close, 7, -25, 3)",
        )
        self.assertEqual(
            get_indicator_spec("supertrend").expression({"period": 14, "multiplier": 2.5}),
            "ta.supertrend(14, 2.5)",
        )
        self.assertEqual(get_indicator_spec("atr").expression({"period": 21}), "ta.atr(21)")

    def test_parameter_contract_fails_closed(self):
        invalid_cases = (
            ("jma", {"length": 0}),
            ("jma", {"length": 2.5}),
            ("jma", {"phase": 101}),
            ("jma", {"power": 0}),
            ("supertrend", {"period": 0}),
            ("supertrend", {"multiplier": 0}),
            ("atr", {"period": 1.5}),
            ("atr", {"unknown": 1}),
        )
        for indicator_id, params in invalid_cases:
            with self.subTest(indicator=indicator_id, params=params):
                with self.assertRaises(ValueError):
                    get_indicator_spec(indicator_id).expression(params)

    def test_unknown_indicator_fails_closed(self):
        with self.assertRaises(KeyError):
            get_indicator_spec("does-not-exist")


if __name__ == "__main__":
    unittest.main()
