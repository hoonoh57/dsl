import argparse
import unittest
from pathlib import Path

from tools.backtest_realdata1_strategy1 import (
    DEFAULT_STRATEGY_PATH,
    EXPECTED_DERIVED_MANIFEST_HASH,
    EXPECTED_RECORD_COUNT,
    EXPECTED_ROW_BUNDLE_HASH,
    build_settings,
    market_from_causal_bytes,
)


ROOT = Path(__file__).resolve().parent
TOOL = ROOT / "tools" / "backtest_realdata1_strategy1.py"
STRATEGY = ROOT / "examples" / "jma_cross.dsl"


class RealData1Strategy1BacktestContractTests(unittest.TestCase):
    def test_runner_reuses_trusted_realdata1_derivation_and_existing_backtest_engine(self):
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn("derive_realdata1_bytes", text)
        self.assertIn("BacktestEngine.run", text)
        self.assertIn(EXPECTED_DERIVED_MANIFEST_HASH, text)
        self.assertIn(EXPECTED_ROW_BUNDLE_HASH, text)
        self.assertIn(f"EXPECTED_RECORD_COUNT = {EXPECTED_RECORD_COUNT}", text)
        self.assertNotIn("yfinance", text.lower())
        self.assertNotIn("requests.", text.lower())
        self.assertNotIn("urllib", text.lower())

    def test_strategy1_is_existing_jma_trend_filter_not_new_core_semantics(self):
        self.assertEqual(DEFAULT_STRATEGY_PATH, STRATEGY)
        text = STRATEGY.read_text(encoding="utf-8")
        self.assertIn('strategy "JMA_7_50_Cross"', text)
        self.assertIn("close_sma60 = ta.sma(close, 60)", text)
        self.assertIn("jma_fast = ta.jma(close, 7, 50, 2)", text)
        self.assertIn("jma_slow = ta.jma(close, 50, 50, 4)", text)
        self.assertIn("ta.crossover(jma_fast, jma_slow)", text)
        self.assertIn("ta.crossunder(jma_fast, jma_slow)", text)

    def test_causal_market_projection_accepts_only_date_ohlcv(self):
        causal = (
            b"date,open,high,low,close,volume\n"
            b"2024-04-15,100,105,99,104,1000\n"
            b"2024-04-16,104,108,103,107,1200\n"
        )
        market = market_from_causal_bytes(causal, manifest_hash="manifest")
        self.assertEqual(market["time"], ["2024-04-15", "2024-04-16"])
        self.assertEqual(market["close"], [104.0, 107.0])
        self.assertEqual(market["_meta"]["timeframe"], "1d")
        self.assertEqual(market["_meta"]["dataset_manifest_hash"], "manifest")
        self.assertNotIn("next_close", market)
        self.assertNotIn("direction", market)
        self.assertNotIn("return", market)

    def test_baseline_defaults_to_next_open_and_existing_cost_model(self):
        args = argparse.Namespace(
            total_capital=10_000_000.0,
            allocation_pct=100.0,
            signal_mode="next_open",
            stop_loss_pct=0.0,
            take_profit_pct=0.0,
            trailing_enabled=False,
            trailing_activation_pct=0.0,
            trailing_distance_pct=0.0,
            commission_pct=0.015,
            sell_tax_pct=0.18,
            slippage_pct=0.0,
        )
        settings = build_settings(args)
        self.assertEqual(settings["signal_mode"], "next_open")
        self.assertEqual(settings["commission_pct"], 0.015)
        self.assertEqual(settings["sell_tax_pct"], 0.18)
        self.assertEqual(settings["stop_loss_pct"], 0.0)
        self.assertEqual(settings["take_profit_pct"], 0.0)
        self.assertFalse(settings["trailing_enabled"])
        self.assertEqual(settings["trailing_activation_pct"], 0.0)
        self.assertEqual(settings["trailing_distance_pct"], 0.0)

    def test_runner_passes_existing_trailing_settings_without_new_core_logic(self):
        args = argparse.Namespace(
            total_capital=10_000_000.0,
            allocation_pct=100.0,
            signal_mode="next_open",
            stop_loss_pct=0.0,
            take_profit_pct=0.0,
            trailing_enabled=True,
            trailing_activation_pct=10.0,
            trailing_distance_pct=6.0,
            commission_pct=0.015,
            sell_tax_pct=0.18,
            slippage_pct=0.1,
        )
        settings = build_settings(args)
        self.assertTrue(settings["trailing_enabled"])
        self.assertEqual(settings["trailing_activation_pct"], 10.0)
        self.assertEqual(settings["trailing_distance_pct"], 6.0)
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn('parser.add_argument("--trailing-enabled", action="store_true")', text)
        self.assertIn('parser.add_argument("--trailing-activation-pct", type=float, default=0.0)', text)
        self.assertIn('parser.add_argument("--trailing-distance-pct", type=float, default=0.0)', text)

    def test_report_exposes_existing_trade_diagnostics_without_new_core_logic(self):
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn('"closed_trades": closed_trades', text)
        self.assertIn('"executions": executions', text)
        self.assertIn('"trade_diagnostics": {', text)
        self.assertIn('"average_mfe_pct"', text)
        self.assertIn('"average_mae_pct"', text)
        self.assertIn('"mfe_giveback_pct"', text)
        self.assertIn("mdd_pct=", text)
        self.assertIn("metrics.get('mdd_pct')", text)
        self.assertNotIn("metrics.get('max_drawdown_pct')", text)


if __name__ == "__main__":
    unittest.main()
