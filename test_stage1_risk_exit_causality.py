import unittest

from core.backtest import BacktestEngine


LONG_ENTRY_DSL = '''strategy "RiskExitLong" {
    timeframe = "1d"
    enter = close > close[1]
    on(enter) { order.buy(type = "MARKET") }
}'''

SHORT_ENTRY_DSL = '''strategy "RiskExitShort" {
    timeframe = "1d"
    enter = close < close[1]
    on(enter) { order.sell_short(type = "MARKET") }
}'''


class Stage1RiskExitCausalityTests(unittest.TestCase):
    def test_long_stop_gap_fills_at_open_not_unreachable_stop_price(self):
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [90.0, 100.0, 90.0],
            "high": [91.0, 101.0, 92.0],
            "low": [89.0, 99.0, 88.0],
            "close": [90.0, 100.0, 89.0],
            "volume": [1000.0] * 3,
        }
        result = BacktestEngine.run(
            LONG_ENTRY_DSL,
            market=market,
            settings={
                "stop_loss_pct": 5.0,
                "commission_pct": 0.0,
                "sell_tax_pct": 0.0,
                "slippage_pct": 0.0,
            },
        )
        exit_row = [row for row in result["trades"] if row["kind"] == "EXIT"][0]
        self.assertEqual(exit_row["reason"], "STOP_LOSS")
        self.assertEqual(exit_row["origin"], "RISK_EXIT")
        self.assertEqual(exit_row["price"], 90.0)

    def test_short_stop_gap_fills_at_open_not_unreachable_stop_price(self):
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [110.0, 100.0, 110.0],
            "high": [111.0, 101.0, 112.0],
            "low": [109.0, 99.0, 108.0],
            "close": [110.0, 100.0, 111.0],
            "volume": [1000.0] * 3,
        }
        result = BacktestEngine.run(
            SHORT_ENTRY_DSL,
            market=market,
            settings={
                "stop_loss_pct": 5.0,
                "commission_pct": 0.0,
                "sell_tax_pct": 0.0,
                "slippage_pct": 0.0,
            },
        )
        exit_row = [row for row in result["trades"] if row["kind"] == "EXIT"][0]
        self.assertEqual(exit_row["reason"], "STOP_LOSS")
        self.assertEqual(exit_row["origin"], "RISK_EXIT")
        self.assertEqual(exit_row["price"], 110.0)

    def test_trailing_uses_only_prior_completed_bar_extreme_and_gap_aware_fill(self):
        market = {
            "time": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
            "open": [90.0, 100.0, 100.0, 112.0],
            "high": [91.0, 101.0, 120.0, 115.0],
            "low": [89.0, 99.0, 90.0, 110.0],
            "close": [90.0, 100.0, 115.0, 111.0],
            "volume": [1000.0] * 4,
        }
        result = BacktestEngine.run(
            LONG_ENTRY_DSL,
            market=market,
            settings={
                "trailing_enabled": True,
                "trailing_activation_pct": 10.0,
                "trailing_distance_pct": 5.0,
                "commission_pct": 0.0,
                "sell_tax_pct": 0.0,
                "slippage_pct": 0.0,
            },
        )
        exits = [row for row in result["trades"] if row["kind"] == "EXIT"]
        self.assertEqual(len(exits), 1)
        self.assertEqual(exits[0]["reason"], "TRAILING_STOP")
        self.assertEqual(exits[0]["time"], "2026-01-04")
        self.assertEqual(exits[0]["price"], 112.0)


if __name__ == "__main__":
    unittest.main()
