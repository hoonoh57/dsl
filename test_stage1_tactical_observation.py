import copy
import unittest
from datetime import datetime, timedelta

from core.tactical_discovery import BattleCase
from core.tactical_observation import JmaLocalObservationBuilder


SESSION_DATE = "20260826"


def rising_5m_market():
    start = datetime(2026, 8, 26, 9, 0, 0)
    times = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    # 09:00 through 15:30 inclusive = 79 five-minute bars.
    for index in range(79):
        stamp = start + timedelta(minutes=5 * index)
        times.append(stamp.strftime("%Y%m%d%H%M%S"))
        base = 100.0 + (index * 0.20)
        # Candle bodies alternate weakly while highs/lows continue rising.
        o = base + (0.03 if index % 2 else -0.03)
        c = base + (-0.02 if index % 2 else 0.02)
        open_.append(o)
        close.append(c)
        high.append(max(o, c) + 0.20)
        low.append(min(o, c) - 0.20)
        volume.append(1000.0 + index * 10.0)
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "_meta": {
            "source": "test://authoritative-5m",
            "instrument": "A005930",
            "timeframe": "5m",
        },
    }


def battle_case(market=None):
    return BattleCase(
        case_id="20260826:A005930",
        symbol="A005930",
        session_date=SESSION_DATE,
        market=market or rising_5m_market(),
        settings={"signal_mode": "bar_close"},
        knowledge_cutoff="20260826153000",
        metadata={"source_authority": "test-authority"},
    )


class TacticalObservationTests(unittest.TestCase):
    def test_observation_exposes_time_jma_trend_volatility_and_price_structure(self):
        case = battle_case()
        timestamp = case.market["time"][65]  # 14:25
        observation = JmaLocalObservationBuilder().build(
            case=case,
            timestamp=timestamp,
            family_id="JMA_TREND_CROSS_RESUME_V1",
            generation_hash="generation-0",
        )
        features = observation.features
        self.assertEqual(observation.timestamp, "20260826142500")
        self.assertAlmostEqual(features["minutes_from_open"], 325.0)
        self.assertAlmostEqual(features["minutes_to_close"], 65.0)
        self.assertGreater(features["higher_high_ratio"], 0.8)
        self.assertGreater(features["higher_low_ratio"], 0.8)
        # Weak alternating bodies do not prevent the primitive structure from
        # representing a rising-high/rising-low trend pattern.
        self.assertLess(features["body_up_ratio"], 0.8)
        self.assertIn("jma_fast_slope_pct", features)
        self.assertIn("jma_spread_velocity_pct", features)
        self.assertIn("sma60_slope_pct", features)
        self.assertIn("price_to_sma60_pct", features)
        self.assertIn("atr_pct", features)
        self.assertIn("volume_ratio", features)
        self.assertIn("recent_return_12bar_pct", features)
        self.assertTrue(observation.market_prefix_hash)
        self.assertTrue(observation.observation_hash)

    def test_future_market_mutation_cannot_change_past_observation_identity(self):
        original_market = rising_5m_market()
        case = battle_case(original_market)
        timestamp = original_market["time"][65]
        builder = JmaLocalObservationBuilder()
        before = builder.build(
            case=case,
            timestamp=timestamp,
            family_id="JMA_TREND_CROSS_RESUME_V1",
            generation_hash="generation-0",
        )

        mutated_market = copy.deepcopy(original_market)
        for index in range(66, len(mutated_market["time"])):
            mutated_market["open"][index] += 1000.0
            mutated_market["high"][index] += 1000.0
            mutated_market["low"][index] += 1000.0
            mutated_market["close"][index] += 1000.0
            mutated_market["volume"][index] *= 10.0
        after = builder.build(
            case=battle_case(mutated_market),
            timestamp=timestamp,
            family_id="JMA_TREND_CROSS_RESUME_V1",
            generation_hash="generation-0",
        )

        # Full BattleCase provenance changes because later bars changed, but the
        # point-in-time observation must remain identical because its market
        # prefix and causal features are unchanged.
        self.assertNotEqual(before.case_hash, after.case_hash)
        self.assertEqual(before.market_prefix_hash, after.market_prefix_hash)
        self.assertEqual(dict(before.features), dict(after.features))
        self.assertEqual(before.observation_hash, after.observation_hash)

    def test_timeframe_mismatch_fails_closed(self):
        market = rising_5m_market()
        market["_meta"]["timeframe"] = "3m"
        case = battle_case(market)
        with self.assertRaisesRegex(ValueError, "timeframe"):
            JmaLocalObservationBuilder().build(
                case=case,
                timestamp=case.market["time"][65],
                family_id="JMA_TREND_CROSS_RESUME_V1",
                generation_hash="generation-0",
            )

    def test_insufficient_observation_warmup_fails_closed(self):
        case = battle_case()
        with self.assertRaisesRegex(ValueError, "warm-up"):
            JmaLocalObservationBuilder().build(
                case=case,
                timestamp=case.market["time"][30],
                family_id="JMA_TREND_CROSS_RESUME_V1",
                generation_hash="generation-0",
            )


if __name__ == "__main__":
    unittest.main()
