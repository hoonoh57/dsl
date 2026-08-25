import unittest

from core.tactical_market import MySQLBarProvider


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def fetchall(self, database, sql, params=()):
        self.calls.append((database, sql, tuple(params)))
        if sql.startswith("SHOW COLUMNS"):
            return [{"Field": name} for name in (
                "code", "date", "time", "open", "high", "low", "close", "volume"
            )]
        rows = []
        for i in range(6):
            rows.append({
                "source_date": "2026-07-15",
                "source_clock": f"09:{30 - i*5:02d}:00",
                "open": 100 + i,
                "high": 102 + i,
                "low": 99 + i,
                "close": 101 + i,
                "volume": 1000 + i,
            })
        return rows


class TacticalMarketProviderTests(unittest.TestCase):
    def test_mysql_provider_discovers_schema_and_returns_strict_ascending_market(self):
        provider = MySQLBarProvider(
            FakeExecutor(),
            database="master_db",
            table="minute_candles_5m",
            table_timeframe="5m",
        )
        market = provider.load_session(
            symbol="005930",
            session_date="20260715",
            timeframe="5m",
            required_bars=6,
            end_time="153000",
        )
        self.assertEqual(len(market["time"]), 6)
        self.assertEqual(market["time"], sorted(market["time"]))
        self.assertEqual(market["_meta"]["timeframe"], "5m")

    def test_timeframe_mismatch_fails_closed(self):
        provider = MySQLBarProvider(
            FakeExecutor(),
            database="master_db",
            table="minute_candles_5m",
            table_timeframe="5m",
        )
        with self.assertRaisesRegex(ValueError, "timeframe"):
            provider.load_session(
                symbol="005930",
                session_date="20260715",
                timeframe="3m",
                required_bars=6,
            )


if __name__ == "__main__":
    unittest.main()
