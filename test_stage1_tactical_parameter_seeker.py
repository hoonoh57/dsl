import unittest
from datetime import datetime, timedelta

from core.strategy_factory import ParameterSpec
from core.tactical_discovery import BattleCase, TacticCandidate
from core.tactical_parameter_seeker import MultiBattleParameterSeeker


DSL = '''strategy "MultiBattleSeekFixture" {
    timeframe = "5m"
    input fast_len = 2
    trend = ta.sma(close, fast_len)
    long_entry = close > trend
    long_exit = close < trend
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(symbol: str, *, phase: float) -> dict:
    start = datetime(2026, 8, 26, 9, 0, 0)
    times = []
    open_ = []
    high = []
    low = []
    close = []
    volume = []
    previous = 100.0 + phase
    for index in range(48):
        stamp = start + timedelta(minutes=5 * index)
        wave = ((index % 8) - 3.5) * 0.18
        drift = index * (0.035 + phase * 0.002)
        current = 100.0 + phase + drift + wave
        times.append(stamp.strftime("%Y%m%d%H%M%S"))
        open_.append(previous)
        close.append(current)
        high.append(max(previous, current) + 0.25)
        low.append(min(previous, current) - 0.25)
        volume.append(1000.0 + index * 12.0 + phase * 10.0)
        previous = current
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "_meta": {
            "source": "test://multi-battle-seeker",
            "instrument": symbol,
            "timeframe": "5m",
        },
    }


def cases():
    settings = {"signal_mode": "bar_close", "total_capital": 1_000_000.0}
    return tuple(
        BattleCase(
            case_id=f"20260826:{symbol}",
            symbol=symbol,
            session_date="20260826",
            market=market(symbol, phase=phase),
            settings=settings,
            knowledge_cutoff="20260826125500",
            metadata={"fixture_only": True},
        )
        for symbol, phase in (("A000001", 0.0), ("A000002", 2.0), ("A000003", 4.0))
    )


class MultiBattleParameterSeekerTests(unittest.TestCase):
    def test_grid_search_keeps_one_case_set_and_uses_pareto_competition(self):
        result = MultiBattleParameterSeeker.run(
            base_candidate=TacticCandidate("PARAM_BASE", DSL, complexity_units=2),
            cases=cases(),
            specs=(ParameterSpec("fast_len", (2.0, 3.0, 5.0), "dsl"),),
            method="grid",
            max_workers=2,
        )

        self.assertEqual(result["schema"], "tactical_parameter_seek/v1")
        self.assertEqual(result["evaluated"], 3)
        self.assertEqual(result["selection_policy"], "PARETO_NO_HIDDEN_UNIVERSAL_SCORE")
        self.assertTrue(result["pareto_parameters"])
        self.assertEqual(
            {profile["case_set_hash"] for profile in result["profiles"]},
            {result["case_set_hash"]},
        )
        self.assertEqual(
            result["competition"]["selection_policy"],
            "PARETO_NO_HIDDEN_UNIVERSAL_SCORE",
        )
        self.assertNotIn("best_score", result)
        self.assertNotIn("score", result["candidates"][0])

    def test_worker_count_cannot_change_seek_identity(self):
        kwargs = dict(
            base_candidate=TacticCandidate("PARAM_BASE", DSL, complexity_units=2),
            cases=cases(),
            specs=(ParameterSpec("fast_len", (2.0, 4.0, 6.0), "dsl"),),
            method="grid",
        )
        one = MultiBattleParameterSeeker.run(max_workers=1, **kwargs)
        many = MultiBattleParameterSeeker.run(max_workers=3, **kwargs)
        self.assertEqual(one["seek_hash"], many["seek_hash"])
        self.assertEqual(one["competition"]["comparison_hash"], many["competition"]["comparison_hash"])
        self.assertEqual(
            [row["candidate_hash"] for row in one["candidates"]],
            [row["candidate_hash"] for row in many["candidates"]],
        )

    def test_random_plan_is_deterministic_for_same_seed(self):
        kwargs = dict(
            base_candidate=TacticCandidate("PARAM_BASE", DSL, complexity_units=2),
            cases=cases(),
            specs=(
                ParameterSpec("fast_len", (2.0, 3.0, 4.0, 5.0), "dsl"),
            ),
            method="random",
            seed=17,
            max_candidates=3,
            max_workers=1,
        )
        first = MultiBattleParameterSeeker.run(**kwargs)
        second = MultiBattleParameterSeeker.run(**kwargs)
        self.assertEqual(first["seek_hash"], second["seek_hash"])
        self.assertEqual(
            [row["parameters"] for row in first["candidates"]],
            [row["parameters"] for row in second["candidates"]],
        )

    def test_execution_setting_parameter_is_rejected_to_preserve_frozen_cases(self):
        with self.assertRaisesRegex(ValueError, "DSL input"):
            MultiBattleParameterSeeker.run(
                base_candidate=TacticCandidate("PARAM_BASE", DSL, complexity_units=2),
                cases=cases(),
                specs=(ParameterSpec("slippage_bps", (0.0, 5.0), "setting"),),
            )


if __name__ == "__main__":
    unittest.main()
