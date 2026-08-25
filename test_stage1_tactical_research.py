import unittest

from core.tactical_cohort import CohortMember, CohortSnapshot
from core.tactical_providers import TacticalCohortBundle
from core.tactical_research import TacticalResearchService


class FakeMarketProvider:
    def __init__(self):
        self.calls = []

    def load_session(self, *, symbol, session_date, timeframe, required_bars, end_time="153000"):
        self.calls.append((symbol, session_date, timeframe, required_bars, end_time))
        return {
            "time": ["20260715090000", "20260715090500", "20260715091000"],
            "open": [100, 100, 101],
            "high": [101, 102, 103],
            "low": [99, 99, 100],
            "close": [100, 101, 102],
            "volume": [1000, 1100, 1200],
            "_meta": {"timeframe": timeframe, "instrument": symbol, "source": "fake"},
        }


class FakeScenarioService:
    def __init__(self):
        self.kwargs = None

    def analyze(self, **kwargs):
        self.kwargs = kwargs
        symbols = list(kwargs["unit"].symbols)
        result = {
            "status": "COMPLETED",
            "scenario_hash": "scenario",
            "run_hash": "run",
            "unit": {
                "unit_id": kwargs["unit"].unit_id,
                "metadata": dict(kwargs["unit"].metadata),
            },
            "regime": {"windows": []},
            "results": [
                {
                    "symbol": symbols[0],
                    "metadata": dict(kwargs["tasks"][0].metadata),
                    "strategy_return_pct": 3.0,
                    "backtest": {"markers": []},
                },
                {
                    "symbol": symbols[1],
                    "metadata": dict(kwargs["tasks"][1].metadata),
                    "strategy_return_pct": -1.0,
                    "backtest": {"markers": []},
                },
            ],
            "ranking": [
                {"rank": 1, "symbol": symbols[0], "score": None},
                {"rank": 2, "symbol": symbols[1], "score": None},
            ],
        }
        return {"result": result, "scenario_record": {"id": 1}, "run_record": {"id": 2}}


class TacticalResearchTests(unittest.TestCase):
    def _bundle(self):
        snapshot = CohortSnapshot.create(
            unit_id="1516:1516:7h:20260715:090500",
            as_of="20260715090500",
            members=(
                CohortMember("000001", "20260715090500", {"name": "A", "search_volume": 100}),
                CohortMember("000002", "20260715090500", {"name": "B", "search_volume": 80}),
            ),
            source="fixture",
            knowledge_cutoff="20260715090500",
        )
        return TacticalCohortBundle(
            snapshot=snapshot,
            outcomes={
                "000001": {"label_10": 1, "max_ret_in_period": 12.0},
                "000002": {"label_10": 0, "max_ret_in_period": 4.0},
            },
            source_evidence={"table": "performance_result"},
        )

    def test_1516_outcomes_are_merged_only_after_engine_execution(self):
        scenario = FakeScenarioService()
        service = TacticalResearchService(scenario)
        response = service.run_1516(
            bundle=self._bundle(),
            dsl_code='strategy "x" { timeframe = "5m" long_entry = close > 999999 on(long_entry) { order.buy(type = "MARKET") } }',
            market_provider=FakeMarketProvider(),
            timeframe="5m",
            required_bars=3,
            entry_end_time=151000,
        )
        kwargs = scenario.kwargs
        self.assertEqual(kwargs["common_policy"].entry_start_time, 90501)
        self.assertEqual(kwargs["unit"].metadata["capture_as_of"], "20260715090500")
        self.assertEqual(kwargs["unit"].capture_times, {})
        for task in kwargs["tasks"]:
            self.assertNotIn("label_10", task.metadata)
            self.assertNotIn("max_ret_in_period", task.metadata)
        self.assertEqual(
            response["result"]["results"][0]["official_outcome"]["label_10"], 1
        )
        self.assertEqual(
            response["evaluation"]["mission_positive_profitable_retention"], 1.0
        )
        self.assertEqual(response["result"]["ranking"][0]["rank_by"], "feature:search_volume")
        self.assertEqual(response["result"]["ranking"][0]["symbol"], "000001")

    def test_outcome_symbol_set_mismatch_fails_closed(self):
        bundle = self._bundle()
        broken = TacticalCohortBundle(
            snapshot=bundle.snapshot,
            outcomes={"000001": bundle.outcomes["000001"]},
            source_evidence=bundle.source_evidence,
        )
        with self.assertRaisesRegex(ValueError, "종목 집합"):
            TacticalResearchService(FakeScenarioService()).run_1516(
                bundle=broken,
                dsl_code="x",
                market_provider=FakeMarketProvider(),
                required_bars=3,
            )


if __name__ == "__main__":
    unittest.main()
