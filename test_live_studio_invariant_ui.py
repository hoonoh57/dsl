import unittest

import live_studio_main
from core.dsl_feature_invariants import INVARIANT_CASES


class LiveStudioInvariantUITests(unittest.TestCase):
    def test_capabilities_expose_invariant_catalog_count(self):
        caps = live_studio_main.capabilities()
        self.assertEqual(caps["invariant_catalog_count"], len(INVARIANT_CASES))

    def test_invariant_catalog_exposes_all_cases(self):
        payload = live_studio_main.invariant_catalog()
        ids = {
            item["feature_id"]
            for category in payload["categories"]
            for item in category["features"]
        }
        self.assertEqual(ids, set(INVARIANT_CASES))

    def test_run_all_invariants_is_wired_to_live_studio(self):
        result = live_studio_main.run_all_catalog_invariants()
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["total"], len(INVARIANT_CASES))
        self.assertEqual(result["failed"], 0)

    def test_ui_contains_feature_and_invariant_modes(self):
        html = live_studio_main.LIVE_HTML
        self.assertIn("실행 계약", html)
        self.assertIn("/api/invariants", html)
        self.assertIn("실행 invariant PASS", html)


if __name__ == "__main__":
    unittest.main()
