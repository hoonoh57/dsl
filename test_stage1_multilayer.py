import unittest

from core.backtest import BacktestEngine
from core.multi_symbol import (
    CommonPolicySpec,
    InstrumentTask,
    MissionSpec,
    MultiSymbolAnalysisEngine,
    OpportunityWindow,
    RegimeContext,
    TacticalUnitSpec,
)


DSL = '''strategy "MultiLayerFixture" {
    timeframe = "5m"
    up = close > open
    down = close < open
    long_entry = up
    long_exit = down
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def market(close=None, open_=None, highs=None, lows=None, times=None, symbol="X"):
    times = times or [
        "20260825080000",
        "20260825085500",
        "20260825090000",
        "20260825090500",
        "20260825091000",
        "20260825091500",
        "20260825092000",
    ]
    close = close or [100, 99, 101, 102, 101, 103, 102]
    open_ = open_ or [99, 100, 100, 101, 102, 102, 103]
    highs = highs or [max(o, c) + 1 for o, c in zip(open_, close)]
    lows = lows or [min(o, c) - 1 for o, c in zip(open_, close)]
    return {
        "time": list(times),
        "open": list(open_),
        "high": list(highs),
        "low": list(lows),
        "close": list(close),
        "volume": [1000 + i * 10 for i in range(len(times))],
        "_meta": {"source": "fixture", "timeframe": "5m", "instrument": symbol},
    }


class Stage1MultiLayerTest(unittest.TestCase):
    def test_common_entry_policy_enforces_time_and_daily_count(self):
        result = BacktestEngine.run(
            DSL,
            market=market(),
            data_timeframe="5m",
            settings={"entry_start_time": 90500, "entry_end_time": 92000, "max_entries_per_day": 1},
        )
        entries = [row for row in result["trades"] if row["kind"] == "ENTRY"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["time"], "20260825090500")
        rejections = result["diagnostics"]["rejections"]
        self.assertGreaterEqual(rejections["entry_time_blocked"], 1)
        self.assertGreaterEqual(rejections["entry_count_blocked"], 1)

    def test_scenario_common_policy_overrides_each_task_consistently(self):
        tasks = [
            InstrumentTask("A", DSL, market(symbol="A")),
            InstrumentTask("B", DSL, market(symbol="B"), settings={"entry_start_time": 0}),
        ]
        regime = RegimeContext("risk-on")
        unit = TacticalUnitSpec("HIGH_BETA", "HIGH_BETA", ("A", "B"), rank_by="strategy_return_pct")
        policy = CommonPolicySpec(entry_start_time=90500, entry_end_time=92000, max_entries_per_day=1)
        result = MultiSymbolAnalysisEngine.run(
            regime=regime, unit=unit, tasks=tasks, common_policy=policy, max_workers=2
        )
        for item in result["results"]:
            entries = [row for row in item["backtest"]["trades"] if row["kind"] == "ENTRY"]
            self.assertEqual([row["time"] for row in entries], ["20260825090500"])
            self.assertEqual(item["backtest"]["settings"]["entry_start_time"], 90500)
            self.assertEqual(item["backtest"]["settings"]["max_entries_per_day"], 1)
        self.assertEqual(result["common_policy"]["entry_start_time"], 90500)

    def test_higher_layer_opportunity_window_gates_entries_without_truncating_warmup(self):
        task = InstrumentTask("A", DSL, market(symbol="A"))
        regime = RegimeContext(
            regime_id="risk-on-1",
            state="RISK_ON",
            eligible_units=("HIGH_BETA",),
            windows=(OpportunityWindow("20260825090500", "20260825091000", "fight"),),
        )
        unit = TacticalUnitSpec("HIGH_BETA", "HIGH_BETA", ("A",), rank_by="strategy_return_pct")
        result = MultiSymbolAnalysisEngine.run(regime=regime, unit=unit, tasks=[task], max_workers=1)
        backtest = result["results"][0]["backtest"]
        entries = [row for row in backtest["trades"] if row["kind"] == "ENTRY"]
        self.assertEqual(len(backtest["candles"]), len(task.market["time"]))
        self.assertEqual([row["time"] for row in entries], ["20260825090500"])
        self.assertGreater(backtest["diagnostics"]["rejections"]["higher_layer_gate_blocked"], 0)

    def test_ineligible_tactical_unit_is_blocked_before_execution_and_is_hashable(self):
        task = InstrumentTask("A", DSL, market(symbol="A"))
        regime = RegimeContext("risk-on", active=True, eligible_units=("HIGH_BETA",))
        unit = TacticalUnitSpec("1516_0905", "CONDITION_SEARCH", ("A",), rank_by="strategy_return_pct")
        result = MultiSymbolAnalysisEngine.run(regime=regime, unit=unit, tasks=[task])
        self.assertEqual(result["status"], "REGIME_BLOCKED")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["cohort"]["executed"], 0)
        self.assertTrue(result["run_hash"])
        self.assertEqual(result["scenario_definition"]["scenario_hash"], result["scenario_hash"])

    def test_parallel_multi_symbol_result_is_deterministic_and_ranked_relative_to_benchmark(self):
        times = [
            "20260825090000", "20260825090500", "20260825091000",
            "20260825091500", "20260825092000", "20260825092500",
        ]
        bench_close = [100, 101, 102, 103, 104, 105]
        strong_close = [100, 102, 104, 108, 112, 116]
        weak_close = [100, 100.5, 101, 101.5, 102, 102.5]

        def trend_market(values, symbol):
            opens = [value - 0.2 for value in values]
            return market(
                close=values,
                open_=opens,
                highs=[value + 1 for value in values],
                lows=[value - 1 for value in values],
                times=times,
                symbol=symbol,
            )

        benchmark = trend_market(bench_close, "KOSPI")
        tasks = [
            InstrumentTask("WEAK", DSL, trend_market(weak_close, "WEAK")),
            InstrumentTask("STRONG", DSL, trend_market(strong_close, "STRONG")),
        ]
        regime = RegimeContext("risk-on", evidence={"source": "market-regime"})
        unit = TacticalUnitSpec(
            "HIGH_BETA",
            "HIGH_BETA",
            ("WEAK", "STRONG"),
            reference_symbol="KOSPI",
            rank_by="relative_strength_pct",
            metadata={"cohort": "point-in-time"},
        )
        one = MultiSymbolAnalysisEngine.run(
            regime=regime, unit=unit, tasks=tasks, benchmark_market=benchmark, max_workers=1
        )
        two = MultiSymbolAnalysisEngine.run(
            regime=regime, unit=unit, tasks=tasks, benchmark_market=benchmark, max_workers=2
        )
        self.assertEqual([row["symbol"] for row in two["results"]], ["WEAK", "STRONG"])
        self.assertEqual(two["ranking"][0]["symbol"], "STRONG")
        self.assertEqual(one["scenario_hash"], two["scenario_hash"])
        self.assertEqual(one["run_hash"], two["run_hash"])
        self.assertTrue(two["benchmark"]["market_hash"])
        self.assertEqual(two["scenario_definition"]["regime"]["evidence"]["source"], "market-regime")

        changed_benchmark = trend_market([100, 99, 101, 98, 102, 97], "KOSPI")
        changed = MultiSymbolAnalysisEngine.run(
            regime=regime, unit=unit, tasks=tasks, benchmark_market=changed_benchmark, max_workers=2
        )
        self.assertNotEqual(two["scenario_hash"], changed["scenario_hash"])

    def test_reference_symbol_mismatch_fails_closed(self):
        task = InstrumentTask("A", DSL, market(symbol="A"))
        unit = TacticalUnitSpec(
            "HIGH_BETA", "HIGH_BETA", ("A",), reference_symbol="KOSPI", rank_by="relative_strength_pct"
        )
        with self.assertRaisesRegex(ValueError, "reference_symbol"):
            MultiSymbolAnalysisEngine.run(
                regime=RegimeContext("risk-on"),
                unit=unit,
                tasks=[task],
                benchmark_market=market(symbol="KOSDAQ"),
            )

    def test_capture_mfe_is_a_post_capture_label_not_an_input(self):
        times = [
            "20260825090000", "20260825090500", "20260825091000", "20260825091500"
        ]
        item_market = market(
            close=[99, 100, 105, 108],
            open_=[98, 99, 101, 106],
            highs=[100, 101, 112, 110],
            lows=[97, 98, 99, 104],
            times=times,
            symbol="A",
        )
        task = InstrumentTask("A", DSL, item_market)
        regime = RegimeContext("condition-search")
        unit = TacticalUnitSpec(
            "1516_0905",
            "CONDITION_SEARCH",
            ("A",),
            capture_times={"A": "20260825090500"},
            rank_by="capture_mfe_pct",
        )
        mission = MissionSpec(mfe_threshold_pct=10.0, include_capture_bar=False)
        result = MultiSymbolAnalysisEngine.run(regime=regime, unit=unit, tasks=[task], mission=mission)
        capture = result["results"][0]["capture"]
        self.assertAlmostEqual(capture["mfe_pct"], 12.0, places=9)
        self.assertTrue(capture["mission_success"])
        self.assertEqual(capture["future_bars"], 2)
        self.assertEqual(result["cohort"]["mission_positive_symbols"], 1)

    def test_capture_time_requires_exact_bar_no_nearest_time_fallback(self):
        task = InstrumentTask("A", DSL, market(symbol="A"))
        regime = RegimeContext("condition-search")
        unit = TacticalUnitSpec(
            "1516_0905",
            "CONDITION_SEARCH",
            ("A",),
            capture_times={"A": "20260825090600"},
            rank_by="capture_mfe_pct",
        )
        with self.assertRaisesRegex(ValueError, "정확히 1개 bar"):
            MultiSymbolAnalysisEngine.run(regime=regime, unit=unit, tasks=[task])


if __name__ == "__main__":
    unittest.main()
