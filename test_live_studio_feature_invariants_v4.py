import unittest

from core.dsl_feature_invariants_v4 import (
    INVARIANT_V4_CASES,
    run_all_invariants_v4,
    run_invariant_v4,
)


class LiveStudioFeatureInvariantV4Tests(unittest.TestCase):
    def test_expected_v4_invariants_are_registered(self):
        self.assertEqual(set(INVARIANT_V4_CASES), {
            "order.limit_fill",
            "order.cancel_unknown_fail_closed",
            "execution.take_profit_precedence",
            "execution.trailing_stop",
        })

    def test_every_v4_case_has_executable_dsl_and_description(self):
        for invariant_id, case in INVARIANT_V4_CASES.items():
            with self.subTest(invariant_id=invariant_id):
                self.assertTrue(case.dsl_code.strip().startswith('strategy "'))
                self.assertTrue(case.description.strip())
                self.assertTrue(case.category.strip())

    def test_each_v4_invariant_passes(self):
        failures = []
        for invariant_id in INVARIANT_V4_CASES:
            result = run_invariant_v4(invariant_id)
            if not result.get("ok"):
                failures.append(result)
        self.assertEqual(failures, [], f"v4 invariant failures: {failures}")

    def test_run_all_v4_reports_exact_coverage(self):
        result = run_all_invariants_v4()
        self.assertEqual(result["total"], len(INVARIANT_V4_CASES))
        self.assertEqual(result["passed"] + result["failed"], result["total"])
        self.assertEqual(
            result["failed_invariant_ids"],
            [row["invariant_id"] for row in result["results"] if not row.get("ok")],
        )

    def test_unknown_v4_invariant_fails_closed(self):
        result = run_invariant_v4("does.not.exist")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "CATALOG")


if __name__ == "__main__":
    unittest.main()
