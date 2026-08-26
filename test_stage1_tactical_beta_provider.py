import os
import unittest
from unittest.mock import patch

from core.tactical_beta_provider import HighBetaDailyCohortProvider, HighBetaSpec


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def fetchall(self, database, sql, params=()):
        self.calls.append((database, sql, tuple(params)))
        if sql.startswith("SHOW COLUMNS"):
            return [{"Field": name} for name in ("code", "date", "close")]
        dates = ["2026-08-19", "2026-08-20", "2026-08-21", "2026-08-24", "2026-08-25"]
        rows = []
        values = {
            "KOSPI": [100, 101, 102, 103, 104],
            "A": [100, 102, 104, 107, 110],
            "B": [100, 100.5, 101, 101.5, 102],
        }
        for code, closes in values.items():
            for day, close in zip(dates, closes):
                rows.append({"code": code, "trade_date": day, "close": close})
        return rows


class HighBetaProviderTests(unittest.TestCase):
    def test_high_beta_uses_only_exact_asof_history_and_ranks_by_beta(self):
        executor = FakeExecutor()
        provider = HighBetaDailyCohortProvider(
            executor,
            database="master_db",
            table="daily_candles",
        )
        snapshot = provider.load(
            as_of="20260825",
            spec=HighBetaSpec(
                benchmark_symbol="KOSPI",
                lookback_sessions=4,
                min_overlap_sessions=3,
                top_n=2,
                calendar_lookback_days=20,
            ),
        )
        self.assertEqual(snapshot.as_of, "20260825235959")
        self.assertEqual(snapshot.symbols[0], "A")
        self.assertGreater(
            snapshot.members[0].features["beta"],
            snapshot.members[1].features["beta"],
        )
        data_call = executor.calls[-1]
        self.assertIn("<=%s", data_call[1])
        self.assertEqual(data_call[2][1], "2026-08-25")

    def test_missing_exact_benchmark_asof_fails_closed(self):
        class MissingBenchmark(FakeExecutor):
            def fetchall(self, database, sql, params=()):
                rows = super().fetchall(database, sql, params)
                if sql.startswith("SHOW COLUMNS"):
                    return rows
                return [row for row in rows if not (row["code"] == "KOSPI" and row["trade_date"] == "2026-08-25")]

        provider = HighBetaDailyCohortProvider(
            MissingBenchmark(), database="master_db", table="daily_candles"
        )
        with self.assertRaisesRegex(ValueError, "exact as_of"):
            provider.load(
                as_of="20260825",
                spec=HighBetaSpec(
                    benchmark_symbol="KOSPI",
                    lookback_sessions=4,
                    min_overlap_sessions=3,
                    top_n=2,
                    calendar_lookback_days=20,
                ),
            )

    def test_high_beta_database_is_not_guessed(self):
        with patch.dict(os.environ, {"TACTICAL_DAILY_DATABASE": ""}, clear=False):
            with self.assertRaisesRegex(ValueError, "TACTICAL_DAILY_DATABASE"):
                HighBetaDailyCohortProvider(FakeExecutor())


if __name__ == "__main__":
    unittest.main()
