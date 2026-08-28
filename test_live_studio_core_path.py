import unittest

import live_studio_main


SAMPLE = '''strategy "T" {
    timeframe = "1d"
    ma_fast = ta.sma(close, 5)
    ma_slow = ta.sma(close, 20)
    entry_cond = ta.crossover(ma_fast, ma_slow)
    exit_cond = ta.crossunder(ma_fast, ma_slow)
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}'''


class LiveStudioCorePathTests(unittest.TestCase):
    def test_does_not_reuse_legacy_app(self):
        source = open("live_studio_main.py", "r", encoding="utf-8").read()
        self.assertNotIn("from app_ui import", source)
        self.assertNotIn("Engine.run_backtest", source)

    def test_capabilities_expose_direct_core_path(self):
        caps = live_studio_main.capabilities()
        self.assertFalse(caps["legacy_ui_reused"])
        self.assertFalse(caps["legacy_demo_engine_reused"])
        self.assertIn("BacktestEngine", caps["engine_path"])

    def test_validate_uses_current_parser_and_semantic(self):
        result = live_studio_main.validate_dsl(live_studio_main.ValidateRequest(dsl_code=SAMPLE))
        self.assertTrue(result["ok"])
        self.assertEqual(result["parser"], "PASS")
        self.assertEqual(result["semantic"], "PASS")

    def test_evaluate_runs_real_core_backtest_engine(self):
        result = live_studio_main.evaluate(live_studio_main.EvaluateRequest(dsl_code=SAMPLE, bars_count=120))
        self.assertEqual(result["evaluation"]["engine"], "core.backtest.BacktestEngine")
        self.assertFalse(result["evaluation"]["legacy_demo_engine"])
        self.assertEqual(result["evaluation"]["data_claim"], "SYNTHETIC_ENGINE_FIXTURE")
        self.assertIn("metrics_numeric", result)
        self.assertIn("diagnostics", result)
        self.assertIn("closed_trades", result)

    def test_caller_market_is_distinguished_from_fixture(self):
        market = {
            "time": ["20200101", "20200102", "20200103", "20200104", "20200105", "20200106", "20200107", "20200108", "20200109", "20200110", "20200111", "20200112", "20200113", "20200114", "20200115", "20200116", "20200117", "20200118", "20200119", "20200120", "20200121"],
            "open": [100.0] * 21,
            "high": [101.0] * 21,
            "low": [99.0] * 21,
            "close": [100.0] * 21,
            "volume": [1000.0] * 21,
            "_meta": {"source": "test_external", "timeframe": "1d"},
        }
        result = live_studio_main.evaluate(live_studio_main.EvaluateRequest(dsl_code=SAMPLE, market=market, data_timeframe="1d"))
        self.assertEqual(result["evaluation"]["data_claim"], "CALLER_SUPPLIED_MARKET")
        self.assertEqual(result["evaluation"]["data_meta"]["source"], "test_external")


if __name__ == "__main__":
    unittest.main()
