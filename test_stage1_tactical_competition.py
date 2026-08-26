import unittest

from core.tactical_competition import TacticalCompetitionEngine


def profile(candidate_id, candidate_hash, *, case_set="cases", avg=1.0, median=0.8, rate=0.6,
            mdd=-2.0, pf=1.5, cost=100.0, trades=2.0, complexity=2, run_hash=None):
    return {
        "schema": "tactical_discovery/v1",
        "candidate": {
            "candidate_id": candidate_id,
            "candidate_hash": candidate_hash,
            "complexity_units": complexity,
        },
        "case_set_hash": case_set,
        "context_policy": {
            "require_neutral_context": True,
            "require_uniform_settings": True,
        },
        "aggregate": {
            "cases": 10,
            "average_return_pct": avg,
            "median_return_pct": median,
            "profitable_case_rate": rate,
            "worst_mdd_pct": mdd,
            "median_finite_profit_factor": pf,
            "total_cost": cost,
            "average_closed_trades_per_case": trades,
            "complexity_units": complexity,
            "top1_positive_return_concentration": 0.25,
        },
        "run_hash": run_hash or f"run-{candidate_hash}",
    }


class TacticalCompetitionTests(unittest.TestCase):
    def test_pareto_frontier_keeps_tradeoff_candidates_and_marks_dominated(self):
        a = profile(
            "A", "hash-a", avg=2.0, median=1.5, rate=0.7,
            mdd=-2.0, pf=2.0, cost=80.0, trades=1.5, complexity=2,
        )
        b = profile(
            "B", "hash-b", avg=1.0, median=0.7, rate=0.5,
            mdd=-3.0, pf=1.2, cost=120.0, trades=2.5, complexity=3,
        )
        c = profile(
            "C", "hash-c", avg=3.2, median=2.0, rate=0.65,
            mdd=-5.0, pf=2.4, cost=150.0, trades=3.0, complexity=4,
        )
        result = TacticalCompetitionEngine.compare((a, b, c))
        self.assertEqual(result["selection_policy"], "PARETO_NO_HIDDEN_UNIVERSAL_SCORE")
        self.assertIn("hash-a", result["pareto_frontier"])
        self.assertIn("hash-c", result["pareto_frontier"])
        self.assertNotIn("hash-b", result["pareto_frontier"])
        self.assertIn("hash-a", result["dominated_by"]["hash-b"])
        self.assertEqual(result["leaderboards"]["average_return_pct"][0], "hash-c")
        self.assertEqual(result["leaderboards"]["complexity_units"][0], "hash-a")

    def test_comparison_rejects_different_opportunity_sets(self):
        with self.assertRaisesRegex(ValueError, "case_set_hash"):
            TacticalCompetitionEngine.compare((
                profile("A", "hash-a", case_set="one"),
                profile("B", "hash-b", case_set="two"),
            ))

    def test_comparison_rejects_different_context_policy(self):
        a = profile("A", "hash-a")
        b = profile("B", "hash-b")
        b["context_policy"] = {
            "require_neutral_context": False,
            "require_uniform_settings": True,
        }
        with self.assertRaisesRegex(ValueError, "context policy"):
            TacticalCompetitionEngine.compare((a, b))

    def test_comparison_hash_is_deterministic_for_frozen_input_order(self):
        a = profile("A", "hash-a")
        b = profile("B", "hash-b")
        first = TacticalCompetitionEngine.compare((a, b))
        second = TacticalCompetitionEngine.compare((a, b))
        self.assertEqual(first["comparison_hash"], second["comparison_hash"])


if __name__ == "__main__":
    unittest.main()
