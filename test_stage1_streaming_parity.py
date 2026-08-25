import unittest
from datetime import date, timedelta

import numpy as np

from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntime


DSL = '''strategy "StreamingParity" {
    timeframe = "1d"
    fast = ta.sma(close, 3)
    slow = ta.sma(close, 8)
    weekly = mtf.sma("1w", 2)
    raw_up = ta.crossover(fast, slow)
    raw_down = ta.crossunder(fast, slow)
    entry_seed = raw_up and close > weekly
    exit_seed = raw_down or close < weekly
    state armed = false
    on_bar {
        if (entry_seed) {
            armed = true
        } else {
            if (exit_seed) {
                armed = false
            }
        }
    }
    on(armed and entry_seed) { order.buy(type = "MARKET") }
    on(exit_seed) { order.close_long() }
}'''


def market(size=72):
    t = np.arange(size, dtype=float)
    close = 100.0 + np.sin(t / 2.3) * 7.0 + np.sin(t / 7.0) * 3.0 + t * 0.04
    open_ = close + np.sin(t / 3.1) * 0.35
    high = np.maximum(open_, close) + 1.25
    low = np.minimum(open_, close) - 1.25
    start = date(2026, 1, 1)
    return {
        "time": [(start + timedelta(days=int(i))).isoformat() for i in range(size)],
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": (1000.0 + (t % 11) * 80.0).tolist(),
    }


def numeric_market(source):
    values = {key: np.asarray(source[key], dtype=float) for key in ("open", "high", "low", "close", "volume")}
    digits = ["".join(ch for ch in value if ch.isdigit()) for value in source["time"]]
    values["date"] = np.asarray([float(value[:8]) for value in digits])
    values["time"] = np.zeros(len(digits), dtype=float)
    return values


def prefix(source, size):
    return {key: list(value[:size]) for key, value in source.items()}


def execution_projection(rows):
    keys = ("order_id", "kind", "time", "signal_time", "side", "price", "quantity", "fee", "reason", "origin")
    return [{key: row.get(key) for key in keys} for row in rows]


class Stage1StreamingParityTest(unittest.TestCase):
    def test_compiled_series_match_every_confirmed_prefix(self):
        source = market()
        full = DSLRuntime.compile(DSL, numeric_market(source))
        names = ("fast", "slow", "weekly", "raw_up", "raw_down", "entry_seed", "exit_seed", "armed")
        for size in range(16, len(source["close"]) + 1):
            current = DSLRuntime.compile(DSL, numeric_market(prefix(source, size)))
            for name in names:
                expected = np.asarray(full.values[name])[:size]
                actual = np.asarray(current.values[name])
                self.assertEqual(len(actual), size, f"{name} length mismatch at prefix {size}")
                if expected.dtype == bool or actual.dtype == bool:
                    np.testing.assert_array_equal(actual.astype(bool), expected.astype(bool), err_msg=f"{name} prefix={size}")
                else:
                    np.testing.assert_allclose(actual.astype(float), expected.astype(float), equal_nan=True,
                                               rtol=0.0, atol=1e-12, err_msg=f"{name} prefix={size}")

    def test_broker_executions_match_full_history_for_each_prefix(self):
        source = market()
        settings_base = {
            "total_capital": 1_000_000.0,
            "allocation_pct": 50.0,
            "commission_pct": 0.015,
            "sell_tax_pct": 0.18,
            "slippage_pct": 0.02,
        }
        for signal_mode in ("bar_close", "next_open"):
            settings = {**settings_base, "signal_mode": signal_mode}
            full = BacktestEngine.run(DSL, market=source, settings=settings)
            full_rows = full["trades"]
            for size in range(16, len(source["close"]) + 1):
                current = BacktestEngine.run(DSL, market=prefix(source, size), settings=settings)
                cutoff = source["time"][size - 1]
                expected = [row for row in full_rows if str(row["time"]) <= cutoff]
                actual = current["trades"]
                self.assertEqual(
                    execution_projection(actual),
                    execution_projection(expected),
                    f"execution history diverged for {signal_mode} prefix={size}",
                )
                history_ids = {row["order_id"] for row in current["diagnostics"]["broker_history"]}
                execution_ids = {row["order_id"] for row in actual}
                self.assertTrue(execution_ids.issubset(history_ids))

    def test_prefix_replay_never_changes_already_closed_trade_accounting(self):
        source = market()
        settings = {
            "signal_mode": "next_open",
            "total_capital": 1_000_000.0,
            "allocation_pct": 50.0,
            "commission_pct": 0.015,
            "sell_tax_pct": 0.18,
            "slippage_pct": 0.02,
        }
        full = BacktestEngine.run(DSL, market=source, settings=settings)
        for size in range(20, len(source["close"]) + 1):
            cutoff = source["time"][size - 1]
            expected = [row for row in full["closed_trades"] if str(row["exit_time"]) <= cutoff]
            current = BacktestEngine.run(DSL, market=prefix(source, size), settings=settings)
            actual = current["closed_trades"]
            self.assertEqual(len(actual), len(expected), f"closed trade count prefix={size}")
            for left, right in zip(actual, expected):
                for key in ("trade_id", "signal_time", "entry_time", "exit_signal_time", "exit_time", "exit_reason"):
                    self.assertEqual(left.get(key), right.get(key), f"{key} prefix={size}")
                for key in ("entry_price", "exit_price", "entry_fee", "exit_fee", "net_pnl", "return_pct", "mfe_pct", "mae_pct"):
                    self.assertAlmostEqual(float(left.get(key, 0.0)), float(right.get(key, 0.0)), places=9,
                                           msg=f"{key} prefix={size}")


if __name__ == "__main__":
    unittest.main()
