from __future__ import annotations

import unittest
import numpy as np

from core.transition_shock_guard import TransitionShockGuard, TransitionShockConfig


def market_from_close(close, *, opens=None, spread=0.2):
    close = np.asarray(close, dtype=float)
    if opens is None:
        opens = np.concatenate(([close[0]], close[:-1]))
    open_ = np.asarray(opens, dtype=float)
    high = np.maximum(open_, close) + float(spread)
    low = np.minimum(open_, close) - float(spread)
    return {"open": open_, "high": high, "low": low, "close": close, "volume": np.full(len(close), 1000.0)}


class TransitionShockGuardTests(unittest.TestCase):
    def test_gap_shock_blocks_cooldown_without_lookahead(self):
        close = np.r_[np.linspace(100, 101, 30), np.linspace(108, 109, 20)]
        opens = np.concatenate(([close[0]], close[:-1]))
        opens[30] = 108.0
        market = market_from_close(close, opens=opens)
        cfg = TransitionShockConfig(gap_threshold_pct=3.0, gap_cooldown_bars=3, large_bar_threshold_pct=99.0)
        result = TransitionShockGuard.evaluate(market, cfg)
        self.assertTrue(result.gap_shock[30])
        np.testing.assert_array_equal(result.blocked["gap_shock"][30:34], np.ones(4, dtype=bool))
        self.assertFalse(result.blocked["gap_shock"][29])

    def test_false_breakout_is_detected_when_intrabar_escape_closes_back_inside(self):
        base = np.full(35, 100.0)
        market = market_from_close(base, spread=0.1)
        market["high"][30] = 103.0
        market["close"][30] = 100.05
        market["open"][30] = 100.0
        market["low"][30] = 99.9
        cfg = TransitionShockConfig(lookback=10, false_breakout_cooldown_bars=2, large_bar_threshold_pct=99.0)
        result = TransitionShockGuard.evaluate(market, cfg)
        self.assertTrue(result.false_breakout[30])
        self.assertFalse(result.trade_permitted[30])
        self.assertFalse(result.trade_permitted[31])
        self.assertFalse(result.trade_permitted[32])

    def test_confirmed_breakout_that_returns_inside_marks_post_failure(self):
        close = np.r_[np.full(25, 100.0), 103.0, 103.2, 100.1, np.full(10, 100.0)]
        market = market_from_close(close, spread=0.1)
        cfg = TransitionShockConfig(
            lookback=10, failure_window_bars=4,
            gap_threshold_pct=99.0, large_bar_threshold_pct=99.0,
            post_breakout_failure_cooldown_bars=3,
        )
        result = TransitionShockGuard.evaluate(market, cfg)
        self.assertTrue(np.any(result.post_breakout_failure))
        failure_i = int(np.flatnonzero(result.post_breakout_failure)[0])
        self.assertGreaterEqual(failure_i, 27)
        self.assertFalse(result.trade_permitted[failure_i])

    def test_smooth_trend_is_not_materially_blocked(self):
        t = np.arange(160, dtype=float)
        market = market_from_close(100 + 0.15*t + 0.02*np.sin(t/7.0), spread=0.05)
        result = TransitionShockGuard.evaluate(market)
        warmup = 35
        allow = float(np.mean(result.trade_permitted[warmup:]))
        self.assertGreater(allow, 0.90, msg={"trend_allow": allow})

    def test_deterministic(self):
        t = np.arange(120, dtype=float)
        market = market_from_close(100 + np.sin(t/3.0))
        a = TransitionShockGuard.evaluate(market)
        b = TransitionShockGuard.evaluate(market)
        np.testing.assert_array_equal(a.trade_permitted, b.trade_permitted)
        for key in a.blocked:
            np.testing.assert_array_equal(a.blocked[key], b.blocked[key])


if __name__ == "__main__":
    unittest.main()
