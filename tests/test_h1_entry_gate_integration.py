from __future__ import annotations

import unittest
from datetime import datetime, timedelta

import numpy as np

from core.backtest import BacktestEngine
from core.h1_entry_permission import H1EntryPermissionEquipment


DSL = r'''
strategy "H1_ADX_EntryGate_Integration" {
  timeframe = "1m"
  ma = ta.sma(close, 5)
  entry_cond = close > ma
  exit_cond = close < ma
  on(entry_cond) { order.buy(type = "MARKET") }
  on(exit_cond) { order.close_position() }
}
'''


def market_from_close(close, spread=0.2):
    close = np.asarray(close, dtype=float)
    open_ = np.concatenate(([close[0]], close[:-1]))
    high = np.maximum(open_, close) + float(spread)
    low = np.minimum(open_, close) - float(spread)
    start = datetime(2026, 8, 31, 9, 0, 0)
    times = [(start + timedelta(minutes=i)).strftime("%Y%m%d%H%M%S") for i in range(len(close))]
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.full(len(close), 1000.0),
        "_meta": {"source": "h1_entry_gate_fixture", "timeframe": "1m"},
    }


class H1EntryGateIntegrationTests(unittest.TestCase):
    def test_permission_adapter_is_deterministic_and_named(self):
        t = np.arange(160, dtype=float)
        market = market_from_close(100 + 0.2 * t)
        a = H1EntryPermissionEquipment.evaluate(market)
        b = H1EntryPermissionEquipment.evaluate(market)
        np.testing.assert_array_equal(a.trade_permitted, b.trade_permitted)
        np.testing.assert_array_equal(a.reason_code, b.reason_code)
        self.assertEqual(a.source, "range_detector.adx")
        self.assertEqual(a.detector_version, "h1_adx_gate/v1")
        self.assertFalse(a.trade_permitted.flags.writeable)
        self.assertFalse(a.reason_code.flags.writeable)

    def test_sideways_market_entries_are_materially_suppressed(self):
        t = np.arange(200, dtype=float)
        market = market_from_close(100 + 0.35 * np.sin(t / 2.0), spread=0.15)
        permission = H1EntryPermissionEquipment.evaluate(market)
        baseline = BacktestEngine.run(DSL, market=market)
        gated = BacktestEngine.run(DSL, market=market, entry_gate=permission.trade_permitted)
        base_trades = int(baseline["metrics_numeric"]["trade_count"])
        gated_trades = int(gated["metrics_numeric"]["trade_count"])
        self.assertGreater(base_trades, 2, msg={"baseline_trade_count": base_trades})
        self.assertLess(gated_trades, base_trades, msg={"baseline": base_trades, "gated": gated_trades})
        self.assertGreater(
            int(gated["diagnostics"]["rejections"]["higher_layer_gate_blocked"]),
            0,
        )
        self.assertTrue(gated["diagnostics"]["entry_policy"]["higher_layer_gate_supplied"])

    def test_clean_trend_keeps_a_legitimate_entry(self):
        t = np.arange(200, dtype=float)
        market = market_from_close(100 + 0.18 * t + 0.02 * np.sin(t / 7.0), spread=0.08)
        permission = H1EntryPermissionEquipment.evaluate(market)
        baseline = BacktestEngine.run(DSL, market=market)
        gated = BacktestEngine.run(DSL, market=market, entry_gate=permission.trade_permitted)
        base_trades = int(baseline["metrics_numeric"]["trade_count"])
        gated_trades = int(gated["metrics_numeric"]["trade_count"])
        self.assertGreaterEqual(base_trades, 1)
        self.assertEqual(gated_trades, base_trades, msg={"baseline": base_trades, "gated": gated_trades})
        warmup = 35
        self.assertGreater(float(np.mean(permission.trade_permitted[warmup:])), 0.95)


if __name__ == "__main__":
    unittest.main()
