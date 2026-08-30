import unittest

import live_studio_main
from core.dsl_feature_invariants import INVARIANT_CASES
from core.dsl_feature_invariants_v3 import INVARIANT_V3_CASES
from core.dsl_feature_invariants_v4 import INVARIANT_V4_CASES


class LiveStudioInvariantUITests(unittest.TestCase):
    def test_capabilities_expose_combined_invariant_catalog_count(self):
        caps = live_studio_main.capabilities()
        expected = len(INVARIANT_CASES) + len(INVARIANT_V3_CASES) + len(INVARIANT_V4_CASES)
        self.assertEqual(caps["invariant_catalog_count"], expected)

    def test_invariant_catalog_exposes_v2_v3_and_v4_cases(self):
        payload = live_studio_main.invariant_catalog()
        ids = {
            item["feature_id"]
            for category in payload["categories"]
            for item in category["features"]
        }
        expected = set(INVARIANT_CASES) | set(INVARIANT_V3_CASES) | set(INVARIANT_V4_CASES)
        self.assertEqual(ids, expected)
        self.assertEqual(payload["count"], len(ids))

    def test_v3_invariant_dispatch_is_wired_to_live_studio(self):
        result = live_studio_main.run_catalog_invariant("order.close_short")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["invariant_id"], "order.close_short")

    def test_v4_invariant_dispatch_is_wired_to_live_studio(self):
        result = live_studio_main.run_catalog_invariant("order.limit_fill")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["invariant_id"], "order.limit_fill")

    def test_run_all_invariants_combines_v2_v3_and_v4(self):
        result = live_studio_main.run_all_catalog_invariants()
        expected = len(INVARIANT_CASES) + len(INVARIANT_V3_CASES) + len(INVARIANT_V4_CASES)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["total"], expected)
        self.assertEqual(result["passed"], expected)
        self.assertEqual(result["failed"], 0)

    def test_ui_contains_feature_invariant_and_chart_modes(self):
        html = live_studio_main.LIVE_HTML
        self.assertIn("실행 계약", html)
        self.assertIn("차트 검증", html)
        self.assertIn("/api/invariants", html)
        self.assertIn("실행 invariant PASS", html)
        self.assertIn("id='chart-frame'", html)
        self.assertIn("http://127.0.0.1:3032/", html)
        self.assertIn("Chart Core", html)
        self.assertIn("Bridge/Runtime", html)
        self.assertIn("Add-on", html)
        self.assertIn("JSON Persistence", html)


if __name__ == "__main__":
    unittest.main()
