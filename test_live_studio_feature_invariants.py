import unittest

from core.dsl_feature_invariants import INVARIANT_CASES, run_all_invariants, run_invariant


class LiveStudioFeatureInvariantTests(unittest.TestCase):
    def test_required_v2_invariants_are_registered(self):
        required = {
            "context.exact_binding",
            "context.missing_fail_closed",
            "execution.entry_gate_suppression",
            "execution.next_open_timing",
            "execution.entry_time_window",
            "execution.max_entries_per_day",
            "order.stop_fill",
            "order.stop_limit_fill",
            "order.day_expiry",
            "order.stable_client_cancel",
            "mtf.confirmed_only",
        }
        self.assertTrue(required.issubset(INVARIANT_CASES))

    def test_every_invariant_has_executable_dsl_and_description(self):
        for invariant_id, case in INVARIANT_CASES.items():
            with self.subTest(invariant_id=invariant_id):
                self.assertTrue(case.dsl_code.strip().startswith('strategy "'))
                self.assertTrue(case.description.strip())
                self.assertTrue(case.category.strip())

    def test_each_v2_invariant_passes_declared_contract(self):
        failures = []
        for invariant_id in INVARIANT_CASES:
            result = run_invariant(invariant_id)
            if not result.get("ok"):
                failures.append({
                    "invariant_id": invariant_id,
                    "stage": result.get("stage"),
                    "message": result.get("message"),
                    "details": result.get("details"),
                })
        self.assertEqual(failures, [], f"DSL invariant failures: {failures}")

    def test_run_all_reports_exact_invariant_coverage(self):
        result = run_all_invariants()
        self.assertEqual(result["total"], len(INVARIANT_CASES))
        self.assertEqual(result["passed"] + result["failed"], result["total"])
        self.assertEqual(
            result["failed_invariant_ids"],
            [item["invariant_id"] for item in result["results"] if not item.get("ok")],
        )

    def test_unknown_invariant_fails_closed(self):
        result = run_invariant("does.not.exist")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "CATALOG")


if __name__ == "__main__":
    unittest.main()
