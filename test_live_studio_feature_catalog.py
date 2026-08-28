import unittest

from core.function_registry import FUNCTION_SPECS
from core.dsl_feature_catalog import FEATURE_CASES, cases_by_category
import live_studio_main


class LiveStudioFeatureCatalogTests(unittest.TestCase):
    def test_every_registered_function_has_executable_case(self):
        missing = sorted(set(FUNCTION_SPECS) - set(FEATURE_CASES))
        self.assertEqual(missing, [])

    def test_catalog_has_core_non_function_cases(self):
        for feature_id in (
            "grammar.input",
            "grammar.history",
            "grammar.on_bar_state",
            "order.long_market",
            "order.short_market",
            "order.limit_cancel",
            "execution.next_open",
            "risk.stop_take_trailing",
        ):
            self.assertIn(feature_id, FEATURE_CASES)

    def test_catalog_categories_are_nonempty(self):
        categories = cases_by_category()
        for required in ("ta", "math", "logic", "state", "session", "mtf", "grammar", "orders", "execution"):
            self.assertIn(required, categories)
            self.assertTrue(categories[required])

    def test_all_catalog_features_parser_semantic_and_backtest_pass(self):
        failures = []
        for feature_id in FEATURE_CASES:
            result = live_studio_main.run_feature_case(feature_id)
            if not result.get("ok"):
                failures.append({
                    "feature_id": feature_id,
                    "stage": result.get("stage"),
                    "error_type": result.get("error_type"),
                    "message": result.get("message") or (result.get("validation") or {}).get("message"),
                })
        self.assertEqual(failures, [], f"DSL feature failures: {failures}")

    def test_run_all_reports_exact_catalog_coverage(self):
        result = live_studio_main.run_all_catalog_features()
        self.assertEqual(result["total"], len(FEATURE_CASES))
        self.assertEqual(result["passed"] + result["failed"], result["total"])
        self.assertEqual(result["failed_feature_ids"], [
            item["feature_id"] for item in result["results"] if not item.get("ok")
        ])


if __name__ == "__main__":
    unittest.main()
