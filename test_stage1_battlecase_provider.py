import unittest

from core.battlecase_provider import (
    BattleCaseRequest,
    ExplicitBattleCaseProvider,
    KoreanRegularSessionBattleCaseProvider,
)


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


class RegularSessionMarketProvider:
    def __init__(self):
        self.calls = []

    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        self.calls.append((symbol, session_date, timeframe, required_bars, end_time))
        return {
            "time": [
                f"{session_date}090000",
                f"{session_date}090500",
                f"{session_date}091000",
                f"{session_date}091500",
            ],
            "open": [100, 100, 101, 102],
            "high": [101, 102, 103, 104],
            "low": [99, 99, 100, 101],
            "close": [100, 101, 102, 103],
            "volume": [1000, 1100, 1200, 1300],
            "_meta": {"instrument": symbol, "timeframe": timeframe, "source": "mysql://research/minute"},
        }


class InsufficientCurrentSessionProvider:
    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        return {
            "time": [
                "20260825152000",
                "20260825152500",
                "20260825153000",
                f"{session_date}090000",
            ],
            "open": [98, 99, 100, 100],
            "high": [99, 100, 101, 101],
            "low": [97, 98, 99, 99],
            "close": [98, 99, 100, 100],
            "volume": [800, 900, 1000, 1100],
            "_meta": {"instrument": symbol, "timeframe": timeframe, "source": "mysql://research/minute"},
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
        self.assertEqual(batch.source_authority, "")

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

    def test_korean_regular_session_provider_records_authority_and_policy(self):
        market = RegularSessionMarketProvider()
        provider = KoreanRegularSessionBattleCaseProvider(
            market,
            source_authority="deployment:mysql-minute-v1",
            timeframe="5m",
            required_bars=4,
            minimum_session_bars=2,
        )
        batch = provider.load((
            BattleCaseRequest(
                "20260826:A",
                "A",
                "20260826",
                "20260826090000",
                metadata={"battlecase_source_authority": "spoofed"},
            ),
        ))
        self.assertEqual(batch.source_authority, "deployment:mysql-minute-v1")
        self.assertTrue(batch.session_policy_hash)
        self.assertEqual(batch.cases[0].metadata["battlecase_session"], "KRX_REGULAR")
        self.assertEqual(
            batch.cases[0].metadata["battlecase_source_authority"],
            "deployment:mysql-minute-v1",
        )
        self.assertEqual(
            batch.cases[0].metadata["battlecase_session_policy_hash"],
            batch.session_policy_hash,
        )

    def test_korean_regular_session_provider_rejects_preopen_bar(self):
        provider = KoreanRegularSessionBattleCaseProvider(
            FakeMarketProvider(),
            source_authority="deployment:mysql-minute-v1",
            timeframe="5m",
            required_bars=4,
        )
        with self.assertRaisesRegex(ValueError, "regular-session"):
            provider.load((
                BattleCaseRequest("20260826:A", "A", "20260826", "20260826090000"),
            ))

    def test_korean_regular_session_provider_requires_current_session_coverage(self):
        provider = KoreanRegularSessionBattleCaseProvider(
            InsufficientCurrentSessionProvider(),
            source_authority="deployment:mysql-minute-v1",
            timeframe="5m",
            required_bars=4,
            minimum_session_bars=2,
        )
        with self.assertRaisesRegex(ValueError, "당일 bar coverage"):
            provider.load((
                BattleCaseRequest("20260826:A", "A", "20260826", "20260826090000"),
            ))

    def test_korean_regular_session_provider_rejects_out_of_session_end_time(self):
        with self.assertRaisesRegex(ValueError, "regular-session"):
            KoreanRegularSessionBattleCaseProvider(
                RegularSessionMarketProvider(),
                source_authority="deployment:mysql-minute-v1",
                timeframe="5m",
                required_bars=4,
                end_time="154000",
            )

    def test_korean_regular_session_provider_requires_explicit_source_authority(self):
        with self.assertRaisesRegex(ValueError, "authority_id"):
            KoreanRegularSessionBattleCaseProvider(
                RegularSessionMarketProvider(),
                source_authority="",
                timeframe="5m",
                required_bars=4,
            )


if __name__ == "__main__":
    unittest.main()
