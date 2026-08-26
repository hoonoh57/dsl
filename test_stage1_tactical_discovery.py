import unittest

from core.battlefield_context import BattlefieldContext, ContextLayerSnapshot
from core.tactical_discovery import BattleCase, TacticCandidate, TacticalDiscoveryEngine


DSL = '''strategy "MicroDiscovery" {
    timeframe = "5m"
    up = close > open
    down = close < open
    long_entry = up
    long_exit = down
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(symbol, day, closes):
    times = [f"{day}090000", f"{day}090500", f"{day}091000", f"{day}091500", f"{day}092000"]
    opens = [100.0] + [float(value) for value in closes[:-1]]
    closes = [float(value) for value in closes]
    highs = [max(o, c) + 0.5 for o, c in zip(opens, closes)]
    lows = [min(o, c) - 0.5 for o, c in zip(opens, closes)]
    return {
        "time": times,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": [1000, 1200, 1300, 1400, 1500],
        "_meta": {"source": "fixture", "instrument": symbol, "timeframe": "5m"},
    }


SETTINGS = {"signal_mode": "bar_close", "total_capital": 1000000.0}


class TacticalDiscoveryTests(unittest.TestCase):
    def cases(self):
        return (
            BattleCase(
                case_id="20260825:A",
                symbol="A",
                session_date="20260825",
                knowledge_cutoff="20260825090000",
                market=market("A", "20260825", [101, 102, 103, 102, 101]),
                settings=SETTINGS,
            ),
            BattleCase(
                case_id="20260826:A",
                symbol="A",
                session_date="20260826",
                knowledge_cutoff="20260826090000",
                market=market("A", "20260826", [100.5, 101, 100.5, 101.5, 100.8]),
                settings=SETTINGS,
            ),
            BattleCase(
                case_id="20260826:B",
                symbol="B",
                session_date="20260826",
                knowledge_cutoff="20260826090000",
                market=market("B", "20260826", [99.5, 100.5, 101.5, 102, 101]),
                settings=SETTINGS,
            ),
        )

    def test_same_symbol_can_appear_on_multiple_dates_as_distinct_battles(self):
        candidate = TacticCandidate("UP_DOWN", DSL, complexity_units=2)
        result = TacticalDiscoveryEngine.evaluate(
            candidate=candidate,
            cases=self.cases(),
            max_workers=2,
        )
        self.assertEqual(result["aggregate"]["cases"], 3)
        self.assertEqual([row["case_id"] for row in result["results"]], [
            "20260825:A", "20260826:A", "20260826:B"
        ])
        self.assertEqual(result["candidate"]["complexity_units"], 2)
        # Neutral context is still timestamped point-in-time evidence, so the
        # two session dates form two immutable neutral strata.
        self.assertEqual(len(result["context_strata"]), 2)
        self.assertTrue(all(row["context"]["mode"] == "NEUTRAL" for row in result["results"]))

    def test_worker_count_does_not_change_run_or_case_set_hash(self):
        candidate = TacticCandidate("UP_DOWN", DSL, complexity_units=2)
        one = TacticalDiscoveryEngine.evaluate(candidate=candidate, cases=self.cases(), max_workers=1)
        many = TacticalDiscoveryEngine.evaluate(candidate=candidate, cases=self.cases(), max_workers=3)
        self.assertEqual(one["case_set_hash"], many["case_set_hash"])
        self.assertEqual(one["run_hash"], many["run_hash"])
        self.assertEqual(one["aggregate"], many["aggregate"])

    def test_neutral_baseline_rejects_macro_filtered_context(self):
        observed = BattlefieldContext(
            as_of="20260825090000",
            mode="OBSERVED",
            layers=(
                ContextLayerSnapshot(
                    layer="MARKET",
                    context_id="KOSDAQ",
                    as_of="20260825090000",
                    source="fixture://market",
                    features={"state": "RISK_ON"},
                ),
            ),
        )
        case = BattleCase(
            case_id="OBSERVED",
            symbol="A",
            session_date="20260825",
            knowledge_cutoff="20260825090000",
            market=market("A", "20260825", [101, 102, 103, 102, 101]),
            settings=SETTINGS,
            battlefield_context=observed,
        )
        with self.assertRaisesRegex(ValueError, "NEUTRAL"):
            TacticalDiscoveryEngine.evaluate(
                candidate=TacticCandidate("UP_DOWN", DSL),
                cases=(case,),
            )

    def test_observed_context_is_allowed_only_when_explicitly_requested(self):
        observed = BattlefieldContext(
            as_of="20260825090000",
            mode="OBSERVED",
            layers=(
                ContextLayerSnapshot(
                    layer="MARKET",
                    context_id="KOSDAQ",
                    as_of="20260825090000",
                    source="fixture://market",
                    features={"state": "RISK_ON"},
                ),
            ),
        )
        case = BattleCase(
            case_id="OBSERVED",
            symbol="A",
            session_date="20260825",
            knowledge_cutoff="20260825090000",
            market=market("A", "20260825", [101, 102, 103, 102, 101]),
            settings=SETTINGS,
            battlefield_context=observed,
        )
        result = TacticalDiscoveryEngine.evaluate(
            candidate=TacticCandidate("UP_DOWN", DSL),
            cases=(case,),
            require_neutral_context=False,
        )
        self.assertEqual(result["context_strata"][0]["mode"], "OBSERVED")

    def test_execution_settings_are_frozen_by_default(self):
        cases = list(self.cases())
        cases[1] = BattleCase(
            case_id=cases[1].case_id,
            symbol=cases[1].symbol,
            session_date=cases[1].session_date,
            knowledge_cutoff=cases[1].knowledge_cutoff,
            market=cases[1].market,
            settings={**SETTINGS, "commission_pct": 0.1},
        )
        with self.assertRaisesRegex(ValueError, "execution settings"):
            TacticalDiscoveryEngine.evaluate(
                candidate=TacticCandidate("UP_DOWN", DSL),
                cases=tuple(cases),
            )

    def test_malformed_single_case_fails_whole_discovery(self):
        cases = list(self.cases())
        broken_market = dict(cases[-1].market)
        broken_market["high"] = list(broken_market["high"])
        broken_market["high"][1] = broken_market["low"][1] - 1.0
        cases[-1] = BattleCase(
            case_id=cases[-1].case_id,
            symbol=cases[-1].symbol,
            session_date=cases[-1].session_date,
            knowledge_cutoff=cases[-1].knowledge_cutoff,
            market=broken_market,
            settings=SETTINGS,
        )
        with self.assertRaisesRegex(ValueError, "OHLCV"):
            TacticalDiscoveryEngine.evaluate(
                candidate=TacticCandidate("UP_DOWN", DSL),
                cases=tuple(cases),
                max_workers=3,
            )


if __name__ == "__main__":
    unittest.main()
