import math
import unittest
from datetime import datetime, timedelta

import numpy as np

from core.backtest import BacktestEngine
from core.strategy_factory import stable_hash


LONG_TREND = '''strategy "RepresentativeLongTrend" {
    timeframe = "1d"
    fast = ta.sma(close, 3)
    slow = ta.sma(close, 12)
    enter = ta.crossover(fast, slow)
    leave = ta.crossunder(fast, slow)
    on(enter) { order.buy(type = "MARKET") }
    on(leave) { order.close_long() }
}'''

SHORT_REVERSAL = '''strategy "RepresentativeShortReversal" {
    timeframe = "1d"
    mean = ta.sma(close, 8)
    enter = ta.crossunder(close, mean)
    leave = ta.crossover(close, mean)
    on(enter) { order.sell_short(type = "MARKET") }
    on(leave) { order.close_short() }
}'''

STATE_MTF = '''strategy "RepresentativeStateMtf" {
    timeframe = "1d"
    weekly_close = mtf.close("1w")
    state bullish = false
    on_bar {
        if (close > weekly_close) {
            bullish = true
        } else {
            if (close < weekly_close) {
                bullish = false
            }
        }
    }
    on(bullish) { order.buy(type = "MARKET") }
    on(not bullish) { order.close_long() }
}'''

PENDING_OCO = '''strategy "RepresentativePendingOco" {
    timeframe = "1d"
    fast = ta.sma(close, 3)
    slow = ta.sma(close, 10)
    trigger = ta.crossover(fast, slow)
    buy_stop = close * 1.005
    buy_limit = close * 1.015
    short_stop = close * 0.995
    short_limit = close * 0.985
    on(trigger) {
        order.buy(type = "STOP_LIMIT", stop = buy_stop, limit = buy_limit, tif = "GTC", oco = "entry-pair")
        order.sell_short(type = "STOP_LIMIT", stop = short_stop, limit = short_limit, tif = "GTC", oco = "entry-pair")
    }
}'''


def representative_market(size=180):
    t = np.arange(size, dtype=float)
    close = 100.0 + 0.03 * t + 6.0 * np.sin(t / 4.0) + 2.0 * np.sin(t / 11.0)
    open_ = close + 0.4 * np.sin(t / 3.0)
    high = np.maximum(open_, close) + 2.0
    low = np.minimum(open_, close) - 2.0
    volume = 100_000.0 + (t % 17) * 2_500.0
    start = datetime(2025, 1, 1)
    return {
        "time": [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(size)],
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
        "_meta": {"source": "representative_regression", "timeframe": "1d"},
    }


def fingerprint(result):
    return stable_hash({
        "metrics": result["metrics_numeric"],
        "executions": result["trades"],
        "closed_trades": result["closed_trades"],
        "signals": result["diagnostics"]["signal_counts"],
        "rejections": result["diagnostics"]["rejections"],
        "broker_history": result["diagnostics"]["broker_history"],
    })


class Stage1RepresentativeRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.market = representative_market()

    def run_twice(self, dsl, *, signal_mode="bar_close"):
        settings = {
            "signal_mode": signal_mode,
            "allocation_pct": 40.0,
            "commission_pct": 0.015,
            "sell_tax_pct": 0.18,
            "slippage_pct": 0.02,
            "stop_loss_pct": 0.0,
            "take_profit_pct": 0.0,
        }
        first = BacktestEngine.run(dsl, market=self.market, settings=settings, data_timeframe="1d")
        second = BacktestEngine.run(dsl, market=self.market, settings=settings, data_timeframe="1d")
        self.assertEqual(fingerprint(first), fingerprint(second))
        self.assertEqual(first["diagnostics"]["execution_authority"], "BrokerEmulator")
        self.assertTrue(math.isfinite(float(first["metrics_numeric"]["final_equity"])))
        self.assertIn(int(first["metrics_numeric"]["open_position"]), {-1, 0, 1})
        self.assertEqual(first["diagnostics"]["rejections"]["broker_fill_while_occupied"], 0)
        self.assertGreater(len(first["diagnostics"]["broker_history"]), 0)

        by_order = {}
        for row in first["diagnostics"]["broker_history"]:
            by_order.setdefault(row["order_id"], []).append(row)
        for execution in first["trades"]:
            rows = by_order.get(execution["order_id"], [])
            self.assertTrue(rows, execution)
            self.assertEqual(rows[-1]["status"], "FILLED")
            self.assertAlmostEqual(float(rows[-1]["fill_price"]), float(execution["price"]), places=12)
            self.assertAlmostEqual(float(rows[-1]["quantity"]), float(execution["quantity"]), places=12)
        return first

    def test_long_trend_market_strategy_is_deterministic(self):
        result = self.run_twice(LONG_TREND)
        self.assertGreater(sum(1 for row in result["trades"] if row["side"] == "BUY"), 0)

    def test_short_reversal_market_strategy_is_deterministic(self):
        result = self.run_twice(SHORT_REVERSAL)
        self.assertGreater(sum(1 for row in result["trades"] if row["side"] == "SHORT"), 0)

    def test_confirmed_mtf_plus_on_bar_state_strategy_is_deterministic(self):
        result = self.run_twice(STATE_MTF)
        self.assertGreater(result["diagnostics"]["signal_counts"].get("__long_entry", 0), 0)

    def test_pending_stop_limit_oco_strategy_preserves_single_position_authority(self):
        result = self.run_twice(PENDING_OCO)
        pending = result["diagnostics"]["pending_order_history"]
        self.assertGreater(len(pending), 0)
        statuses = {row["status"] for row in pending}
        self.assertIn("FILLED", statuses)
        self.assertIn("CANCELED", statuses)
        self.assertEqual(result["diagnostics"]["rejections"]["broker_fill_while_occupied"], 0)


if __name__ == "__main__":
    unittest.main()
