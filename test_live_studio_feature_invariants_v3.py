import unittest

from core.dsl_feature_invariants_v3 import INVARIANT_V3_CASES, run_all_invariants_v3, run_invariant_v3


class LiveStudioFeatureInvariantV3Tests(unittest.TestCase):
    def test_expected_v3_invariants_are_registered(self):
        expected = {
            "order.oco_sibling_cancel",
            "order.gtc_persistence",
            "order.close_long",
            "order.close_short",
            "order.close_position",
            "execution.pending_suppressed_position_occupied",
            "execution.same_bar_reentry",
            "execution.risk_exit_precedence",
        }
        self.assertEqual(set(INVARIANT_V3_CASES), expected)

    def test_each_v3_invariant_passes(self):
        failures = []
        for invariant_id in INVARIANT_V3_CASES:
            result = run_invariant_v3(invariant_id)
            if not result.get("ok"):
                failures.append(result)
        self.assertEqual(failures, [], f"v3 invariant failures: {failures}")

    def test_run_all_v3_reports_exact_coverage(self):
        result = run_all_invariants_v3()
        self.assertEqual(result["total"], len(INVARIANT_V3_CASES))
        self.assertEqual(result["passed"] + result["failed"], result["total"])
        self.assertEqual(result["failed_invariant_ids"], [
            row["invariant_id"] for row in result["results"] if not row.get("ok")
        ])

    def test_unknown_v3_invariant_fails_closed(self):
        result = run_invariant_v3("does.not.exist")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "CATALOG")


if __name__ == "__main__":
    unittest.main()
