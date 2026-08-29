import unittest

from core.backtest import BacktestEngine
from core.function_registry import FUNCTION_SPECS
from core.live_validation_catalog import (
    get_live_validation_example,
    live_validation_categories,
    live_validation_examples,
)


class LiveValidationCatalogTests(unittest.TestCase):
    def test_first_category_is_small_and_deterministic(self):
        self.assertEqual(live_validation_categories(), ("TA / 이동평균",))
        self.assertEqual(
            tuple(item.id for item in live_validation_examples()),
            ("ta.sma.basic", "ta.ema.basic", "ta.wma.basic", "ta.rma.basic"),
        )

    def test_every_example_points_to_registered_capability(self):
        for item in live_validation_examples():
            with self.subTest(item=item.id):
                self.assertIn(item.capability, FUNCTION_SPECS)
                self.assertEqual(FUNCTION_SPECS[item.capability].category, "ta")
                self.assertEqual(get_live_validation_example(item.id), item)

    def test_every_example_executes_real_core_backtest(self):
        for item in live_validation_examples():
            with self.subTest(item=item.id):
                result = BacktestEngine.run(item.dsl, bars_count=240)
                self.assertIn("metrics", result)
                indicator_names = {indicator["name"] for indicator in result["indicators"]}
                self.assertIn(item.expected_indicator, indicator_names)
                self.assertGreater(result["diagnostics"]["bars"], 0)

    def test_unknown_example_fails_closed(self):
        with self.assertRaises(KeyError):
            get_live_validation_example("does.not.exist")


if __name__ == "__main__":
    unittest.main()
