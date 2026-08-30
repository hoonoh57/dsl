from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from core.indicators import CoreTALib


@dataclass(frozen=True)
class TransitionShockConfig:
    lookback: int = 20
    gap_threshold_pct: float = 3.0
    large_bar_threshold_pct: float = 4.0
    breakout_margin_pct: float = 0.0
    failure_window_bars: int = 5
    gap_cooldown_bars: int = 8
    large_bar_cooldown_bars: int = 5
    false_breakout_cooldown_bars: int = 8
    post_breakout_failure_cooldown_bars: int = 10


@dataclass(frozen=True)
class TransitionShockResult:
    gap_shock: np.ndarray
    large_bar_shock: np.ndarray
    false_breakout: np.ndarray
    post_breakout_failure: np.ndarray
    blocked: Mapping[str, np.ndarray]
    trade_permitted: np.ndarray


def _cooldown_mask(events: np.ndarray, bars: int) -> np.ndarray:
    events = np.asarray(events, dtype=bool)
    out = np.zeros(len(events), dtype=bool)
    remaining = 0
    for i, hit in enumerate(events):
        if hit:
            remaining = max(remaining, int(bars) + 1)
        if remaining > 0:
            out[i] = True
            remaining -= 1
    return out


class TransitionShockGuard:
    """Pure, causal OHLC transition/shock permission equipment.

    The guard owns no strategy or order semantics. It detects already-observed
    price shocks/failures and returns deterministic block masks suitable for a
    higher-layer entry gate. No future bar is inspected when deciding bar i.
    """

    @staticmethod
    def evaluate(market: Mapping[str, object], config: TransitionShockConfig | None = None) -> TransitionShockResult:
        cfg = config or TransitionShockConfig()
        if cfg.lookback < 2 or cfg.failure_window_bars < 1:
            raise ValueError("transition shock lookback/failure window are invalid")
        for name in (
            "gap_cooldown_bars", "large_bar_cooldown_bars",
            "false_breakout_cooldown_bars", "post_breakout_failure_cooldown_bars",
        ):
            if getattr(cfg, name) < 0:
                raise ValueError(f"{name} must be >= 0")

        open_ = np.asarray(market["open"], dtype=float)
        high = np.asarray(market["high"], dtype=float)
        low = np.asarray(market["low"], dtype=float)
        close = np.asarray(market["close"], dtype=float)
        if not (len(open_) == len(high) == len(low) == len(close)) or len(close) < 2:
            raise ValueError("transition shock OHLC lengths must match and contain at least 2 bars")
        if not all(np.all(np.isfinite(x)) for x in (open_, high, low, close)):
            raise ValueError("transition shock OHLC must be finite")

        previous_close = CoreTALib.shift(close, 1)
        gap_pct = np.divide(
            np.abs(open_ - previous_close), np.abs(previous_close),
            out=np.zeros_like(close), where=np.isfinite(previous_close) & (previous_close != 0),
        ) * 100.0
        gap_shock = gap_pct >= float(cfg.gap_threshold_pct)

        true_range = CoreTALib.true_range(high, low, close)
        large_bar_pct = np.divide(
            true_range, np.abs(previous_close),
            out=np.zeros_like(close), where=np.isfinite(previous_close) & (previous_close != 0),
        ) * 100.0
        large_bar_shock = large_bar_pct >= float(cfg.large_bar_threshold_pct)

        prior_high = CoreTALib.shift(CoreTALib.highest(high, cfg.lookback), 1)
        prior_low = CoreTALib.shift(CoreTALib.lowest(low, cfg.lookback), 1)
        upper = prior_high * (1.0 + float(cfg.breakout_margin_pct) / 100.0)
        lower = prior_low * (1.0 - float(cfg.breakout_margin_pct) / 100.0)
        ready = np.isfinite(upper) & np.isfinite(lower)

        false_up = ready & (high > upper) & (close <= upper)
        false_down = ready & (low < lower) & (close >= lower)
        false_breakout = false_up | false_down

        post_failure = np.zeros(len(close), dtype=bool)
        active_side = 0
        boundary = np.nan
        age = 0
        for i in range(len(close)):
            if active_side:
                age += 1
                failed = (active_side == 1 and close[i] <= boundary) or (active_side == -1 and close[i] >= boundary)
                if failed:
                    post_failure[i] = True
                    active_side = 0
                    boundary = np.nan
                    age = 0
                elif age > cfg.failure_window_bars:
                    active_side = 0
                    boundary = np.nan
                    age = 0
            if active_side == 0 and ready[i]:
                if close[i] > upper[i]:
                    active_side = 1
                    boundary = float(upper[i])
                    age = 0
                elif close[i] < lower[i]:
                    active_side = -1
                    boundary = float(lower[i])
                    age = 0

        blocked = {
            "gap_shock": _cooldown_mask(gap_shock, cfg.gap_cooldown_bars),
            "large_bar_shock": _cooldown_mask(large_bar_shock, cfg.large_bar_cooldown_bars),
            "false_breakout": _cooldown_mask(false_breakout, cfg.false_breakout_cooldown_bars),
            "post_breakout_failure": _cooldown_mask(post_failure, cfg.post_breakout_failure_cooldown_bars),
        }
        combined = np.zeros(len(close), dtype=bool)
        for mask in blocked.values():
            combined |= mask
        return TransitionShockResult(
            gap_shock=gap_shock,
            large_bar_shock=large_bar_shock,
            false_breakout=false_breakout,
            post_breakout_failure=post_failure,
            blocked=blocked,
            trade_permitted=~combined,
        )
