import unittest

from core.tactical_failure import TacticalFailureAnalyzer


class TacticalFailureTests(unittest.TestCase):
    def test_open_position_is_active_failure_not_no_trade(self):
        profile = {
            "schema": "tactical_discovery/v1",
            "candidate": {"candidate_id": "A", "candidate_hash": "hash-a", "complexity_units": 1},
            "case_set_hash": "cases",
            "context_policy": {"require_neutral_context": True, "require_uniform_settings": True},
            "aggregate": {"cases": 2},
            "results": [
                {
                    "case_id": "OPEN",
                    "trade_count": 1,
                    "closed_trade_count": 0,
                    "return_pct": -0.2,
                    "mdd_pct": -0.5,
                    "average_mfe_pct": 0.2,
                    "average_mae_pct": -0.4,
                    "mfe_giveback_pct": 0.4,
                    "backtest": {"metrics_numeric": {"open_position": 1}},
                },
                {
                    "case_id": "ABSTAIN",
                    "trade_count": 0,
                    "closed_trade_count": 0,
                    "return_pct": 0.0,
                    "mdd_pct": 0.0,
                    "average_mfe_pct": 0.0,
                    "average_mae_pct": 0.0,
                    "mfe_giveback_pct": 0.0,
                    "backtest": {"metrics_numeric": {"open_position": 0}},
                },
            ],
            "run_hash": "run-a",
        }
        report = TacticalFailureAnalyzer.analyze(profile)
        tags = {cluster["failure_tag"] for cluster in report["clusters"]}
        self.assertIn("UNRESOLVED_POSITION", tags)
        self.assertIn("LOSS", tags)
        self.assertEqual(report["active_cases"], 1)
        self.assertEqual(report["no_trade_cases"], ("ABSTAIN",))


if __name__ == "__main__":
    unittest.main()
