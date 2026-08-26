import unittest

from core.battlecase_provider import BattleCaseRequest, ExplicitBattleCaseProvider


class FakeMarketProvider:
    def __init__(self):
        self.calls = []

    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        self.calls.append((symbol, session_date, timeframe, required_bars, end_time))
        return {
            "time": [
                f"{session_date}085500",
                f"{session_date}090000",
                f"{session_date}090500",
                f"{session_date}091000",
            ],
            "open": [100, 100, 101, 102],
            "high": [101, 102, 103, 104],
            "low": [99, 99, 100, 101],
            "close": [100, 101, 102, 103],
            "volume": [1000, 1100, 1200, 1300],
            "_meta": {"instrument": symbol, "timeframe": timeframe, "source": "fake-authoritative"},
        }


class BattleCaseProviderTests(unittest.TestCase):
    def test_explicit_requests_freeze_symbol_date_battles_without_universe_guessing(self):
        market = FakeMarketProvider()
        provider = ExplicitBattleCaseProvider(
            market,
            timeframe="5m",
            required_bars=4,
            settings={"signal_mode": "bar_close", "total_capital": 1000000.0},
        )
        batch = provider.load((
            BattleCaseRequest("20260825:A", "A", "20260825", "20260825090000"),
            BattleCaseRequest("20260826:A", "A", "20260826", "20260826090000"),
        ))
        self.assertEqual([case.case_id for case in batch.cases], ["20260825:A", "20260826:A"])
        self.assertEqual([case.symbol for case in batch.cases], ["A", "A"])
        self.assertTrue(all(case.resolved_context().mode == "NEUTRAL" for case in batch.cases))
        self.assertEqual(len(market.calls), 2)
        self.assertTrue(batch.batch_hash)

    def test_duplicate_case_id_fails_closed(self):
        provider = ExplicitBattleCaseProvider(FakeMarketProvider(), timeframe="5m", required_bars=4)
        with self.assertRaisesRegex(ValueError, "case_id"):
            provider.load((
                BattleCaseRequest("same", "A", "20260825", "20260825090000"),
                BattleCaseRequest("same", "B", "20260825", "20260825090000"),
            ))

    def test_request_cutoff_must_belong_to_session(self):
        provider = ExplicitBattleCaseProvider(FakeMarketProvider(), timeframe="5m", required_bars=4)
        with self.assertRaisesRegex(ValueError, "session_date"):
            provider.load((
                BattleCaseRequest("bad", "A", "20260825", "20260826090000"),
            ))


if __name__ == "__main__":
    unittest.main()
