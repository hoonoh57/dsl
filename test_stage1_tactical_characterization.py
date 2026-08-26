import copy
import unittest
from datetime import datetime, timedelta

from core.tactical_characterization import (
    CharacterizationPolicy,
    TacticalFailureOpportunityCharacterizer,
)
from core.tactical_discovery import BattleCase, TacticCandidate, TacticalDiscoveryEngine


DSL = '''strategy "CharacterizationFixture" {
    timeframe = "5m"
    fast = ta.sma(close, 2)
    slow = ta.sma(close, 5)
    long_entry = ta.crossover(fast, slow)
    long_exit = ta.crossunder(fast, slow)
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(symbol: str, *, phase: float) -> dict:
    start = datetime(2026, 8, 26, 8, 0, 0)
    times = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    previous = 100.0 + phase
    # 08:00 through 15:30 inclusive.  The pre-13:00 portion is deterministic
    # warm-up; entries are blocked until 13:00 by execution settings.
    for index in range(91):
        stamp = start + timedelta(minutes=5 * index)
        wave_step = index % 12
        wave = (wave_step if wave_step <= 6 else 12 - wave_step) * 0.45
        if (index // 12) % 2:
            wave = -wave
        drift = index * 0.018
        current = 100.0 + phase + drift + wave
        times.append(stamp.strftime("%Y%m%d%H%M%S"))
        open_.append(previous)
        close.append(current)
        high.append(max(previous, current) + 0.28)
        low.append(min(previous, current) - 0.28)
        volume.append(1200.0 + index * 9.0 + phase * 20.0)
        previous = current
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "_meta": {
            "source": "test://characterization",
            "instrument": symbol,
            "timeframe": "5m",
        },
    }


def cases():
    settings = {
        "signal_mode": "bar_close",
        "total_capital": 1_000_000.0,
        "entry_start_time": 130000,
        "entry_end_time": 152500,
    }
    return tuple(
        BattleCase(
            case_id=f"20260826:{symbol}",
            symbol=symbol,
            session_date="20260826",
            market=market(symbol, phase=phase),
            settings=settings,
            knowledge_cutoff="20260826153000",
            metadata={"fixture_only": True},
        )
        for symbol, phase in (("A000001", 0.0), ("A000002", 1.7))
    )


def profile_and_cases():
    frozen = cases()
    profile = TacticalDiscoveryEngine.evaluate(
        candidate=TacticCandidate("CHARACTERIZE_BASE", DSL, complexity_units=2),
        cases=frozen,
        max_workers=2,
    )
    return profile, frozen


class TacticalCharacterizationTests(unittest.TestCase):
    def test_entry_signal_observation_is_separate_from_future_outcome_labels(self):
        profile, frozen = profile_and_cases()
        result = TacticalFailureOpportunityCharacterizer.characterize(
            profile=profile,
            cases=frozen,
            family_id="CHARACTERIZE_TEST_FAMILY",
            generation_hash="generation-0",
            resolution_mode="JMA_TCR_5M",
        )

        self.assertEqual(result["schema"], "tactical_characterization/v1")
        self.assertEqual(result["selection_policy"], "DESCRIPTIVE_NO_HIDDEN_UNIVERSAL_SCORE")
        self.assertEqual(
            result["causality_policy"],
            "SIGNAL_TIME_FEATURES_FUTURE_OUTCOMES_LABEL_ONLY",
        )
        self.assertGreater(result["summary"]["trade_records"], 0)
        record = result["records"][0]
        self.assertEqual(set(record["causal_features"]), set(CharacterizationPolicy().feature_names))
        self.assertIn("return_pct", record["future_outcome"])
        self.assertIn("mfe_pct", record["future_outcome"])
        self.assertIn("mae_pct", record["future_outcome"])
        self.assertNotIn("return_pct", record["causal_features"])
        self.assertNotIn("mfe_pct", record["causal_features"])
        self.assertNotIn("mae_pct", record["causal_features"])
        self.assertNotIn("score", result)
        self.assertTrue(result["feature_strata"])

    def test_changing_only_future_trade_label_cannot_change_causal_dataset_hash(self):
        profile, frozen = profile_and_cases()
        before = TacticalFailureOpportunityCharacterizer.characterize(
            profile=profile,
            cases=frozen,
            family_id="CHARACTERIZE_TEST_FAMILY",
            generation_hash="generation-0",
        )

        mutated = copy.deepcopy(profile)
        first_trade = None
        for row in mutated["results"]:
            trades = row["backtest"].get("closed_trades") or []
            if trades:
                first_trade = trades[0]
                break
        self.assertIsNotNone(first_trade)
        first_trade["return_pct"] = float(first_trade["return_pct"]) - 7.5
        first_trade["mfe_pct"] = float(first_trade["mfe_pct"]) + 3.0

        after = TacticalFailureOpportunityCharacterizer.characterize(
            profile=mutated,
            cases=frozen,
            family_id="CHARACTERIZE_TEST_FAMILY",
            generation_hash="generation-0",
        )
        self.assertEqual(before["causal_dataset_hash"], after["causal_dataset_hash"])
        self.assertNotEqual(before["labeled_dataset_hash"], after["labeled_dataset_hash"])
        self.assertNotEqual(before["characterization_hash"], after["characterization_hash"])

    def test_profile_case_identity_mismatch_fails_closed(self):
        profile, frozen = profile_and_cases()
        changed = list(frozen)
        original = changed[0]
        changed[0] = BattleCase(
            case_id=original.case_id,
            symbol=original.symbol,
            session_date=original.session_date,
            market=original.market,
            settings=original.settings,
            knowledge_cutoff=original.knowledge_cutoff,
            metadata={"fixture_only": True, "identity_changed": True},
        )
        with self.assertRaisesRegex(ValueError, "identity"):
            TacticalFailureOpportunityCharacterizer.characterize(
                profile=profile,
                cases=tuple(changed),
                family_id="CHARACTERIZE_TEST_FAMILY",
                generation_hash="generation-0",
            )

    def test_same_evidence_produces_same_characterization_identity(self):
        profile, frozen = profile_and_cases()
        kwargs = dict(
            profile=profile,
            cases=frozen,
            family_id="CHARACTERIZE_TEST_FAMILY",
            generation_hash="generation-0",
        )
        first = TacticalFailureOpportunityCharacterizer.characterize(**kwargs)
        second = TacticalFailureOpportunityCharacterizer.characterize(**kwargs)
        self.assertEqual(first["causal_dataset_hash"], second["causal_dataset_hash"])
        self.assertEqual(first["labeled_dataset_hash"], second["labeled_dataset_hash"])
        self.assertEqual(first["characterization_hash"], second["characterization_hash"])
        self.assertEqual(first["feature_strata"], second["feature_strata"])


if __name__ == "__main__":
    unittest.main()
