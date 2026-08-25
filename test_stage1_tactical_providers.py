import unittest

from core.tactical_providers import (
    Performance1516CohortProvider,
    PointInTimeMetricCohortProvider,
)


class FakeExecutor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def fetchall(self, database, sql, params=()):
        self.calls.append((database, sql, tuple(params)))
        return [dict(row) for row in self.rows]


class TacticalProviderContractTests(unittest.TestCase):
    def test_1516_freezes_input_features_and_separates_future_outcomes(self):
        rows = [
            {
                "code": "000001",
                "name": "A",
                "search_volume": 100,
                "ret_1m": 1.2,
                "ret_3m": 2.4,
                "ret_7h": 9.0,
                "max_ret_in_period": 12.5,
                "label_3": 1,
                "label_5": 1,
                "label_10": 1,
                "actual_rank_by_max_ret": 1,
            },
            {
                "code": "000002",
                "name": "B",
                "search_volume": 80,
                "ret_1m": -0.2,
                "ret_3m": 0.5,
                "ret_7h": 2.0,
                "max_ret_in_period": 4.5,
                "label_3": 1,
                "label_5": 0,
                "label_10": 0,
                "actual_rank_by_max_ret": 2,
            },
        ]
        provider = Performance1516CohortProvider(FakeExecutor(rows), database="performance_db")
        bundle = provider.load_group(
            search_date="2026-07-15",
            search_time="09:05",
            condition_name="1516",
            hold_period="7시간",
        )
        self.assertEqual(bundle.snapshot.as_of, "20260715090500")
        self.assertEqual(bundle.snapshot.symbols, ("000001", "000002"))
        self.assertEqual(
            set(bundle.snapshot.members[0].features),
            {"name", "search_volume"},
        )
        leaked = {
            "ret_1m",
            "ret_3m",
            "ret_7h",
            "max_ret_in_period",
            "label_3",
            "label_5",
            "label_10",
            "actual_rank_by_max_ret",
        }
        self.assertFalse(leaked.intersection(bundle.snapshot.members[0].features))
        self.assertEqual(bundle.outcomes["000001"]["label_10"], 1)
        self.assertEqual(bundle.source_evidence["query_contract"], "EXACT_GROUP")

    def test_1516_inconsistent_label_fails_closed(self):
        rows = [{
            "code": "000001",
            "name": "A",
            "search_volume": 1,
            "ret_1m": 0,
            "ret_3m": 0,
            "ret_7h": 0,
            "max_ret_in_period": 11.0,
            "label_3": 1,
            "label_5": 1,
            "label_10": 0,
            "actual_rank_by_max_ret": 1,
        }]
        provider = Performance1516CohortProvider(FakeExecutor(rows), database="performance_db")
        with self.assertRaisesRegex(ValueError, "label_10"):
            provider.load_group(search_date="20260715", search_time="0905")

    def test_metric_snapshot_never_substitutes_missing_asof(self):
        provider = PointInTimeMetricCohortProvider(
            FakeExecutor([]),
            database="research_db",
            table="beta_snapshot",
            symbol_column="code",
            as_of_column="as_of",
            feature_columns=("beta", "rank_no"),
            unit_type="HIGH_BETA",
        )
        with self.assertRaisesRegex(ValueError, "정확한 point-in-time"):
            provider.load(unit_id="HB:20260715", as_of="20260715090000")


if __name__ == "__main__":
    unittest.main()
