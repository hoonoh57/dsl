from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from core.indicators import CoreTALib


@dataclass(frozen=True)
class RangeDetectorConfig:
    period: int = 14
    jma_length: int = 14
    vhf_min_trend: float = 0.35
    adx_min_trend: float = 20.0
    normalized_range_min_trend_pct: float = 2.0
    jma_slope_min_trend_pct: float = 0.08


@dataclass(frozen=True)
class RangeDetectorResult:
    vhf: np.ndarray
    adx: np.ndarray
    normalized_range_pct: np.ndarray
    jma_abs_slope_pct: np.ndarray
    permits: Mapping[str, np.ndarray]


class RangeDetectorEquipment:
    """Pure deterministic OHLC range/trend sensor pack.

    This equipment does not place orders and does not own DSL semantics. It only
    emits independent sensor series and candidate trade-permission booleans for
    competition testing. Integration with BacktestEngine.entry_gate is separate.
    """

    @staticmethod
    def evaluate(market: Mapping[str, object], config: RangeDetectorConfig | None = None) -> RangeDetectorResult:
        cfg = config or RangeDetectorConfig()
        if cfg.period < 2 or cfg.jma_length < 2:
            raise ValueError("range detector periods must be >= 2")
        high = np.asarray(market["high"], dtype=float)
        low = np.asarray(market["low"], dtype=float)
        close = np.asarray(market["close"], dtype=float)
        if not (len(high) == len(low) == len(close)) or len(close) < 2:
            raise ValueError("range detector OHLC lengths must match and contain at least 2 bars")
        if not (np.all(np.isfinite(high)) and np.all(np.isfinite(low)) and np.all(np.isfinite(close))):
            raise ValueError("range detector OHLC must be finite")

        vhf = CoreTALib.vhf(close, cfg.period)
        adx = CoreTALib.adx(high, low, close, cfg.period)
        raw_range = CoreTALib.nrange(high, low, cfg.period)
        base = CoreTALib.sma(close, cfg.period)
        normalized_range_pct = np.divide(raw_range, base, out=np.full_like(raw_range, np.nan), where=base != 0) * 100.0

        jma = np.asarray(CoreTALib.jma(close, cfg.jma_length, 0, 2), dtype=float)
        previous = CoreTALib.shift(jma, 1)
        jma_abs_slope_pct = np.divide(np.abs(jma - previous), np.abs(previous), out=np.full_like(jma, np.nan), where=previous != 0) * 100.0

        permits = {
            "vhf": np.isfinite(vhf) & (vhf >= cfg.vhf_min_trend),
            "adx": np.isfinite(adx) & (adx >= cfg.adx_min_trend),
            "normalized_range": np.isfinite(normalized_range_pct) & (normalized_range_pct >= cfg.normalized_range_min_trend_pct),
            "jma_slope": np.isfinite(jma_abs_slope_pct) & (jma_abs_slope_pct >= cfg.jma_slope_min_trend_pct),
        }
        return RangeDetectorResult(
            vhf=vhf,
            adx=adx,
            normalized_range_pct=normalized_range_pct,
            jma_abs_slope_pct=jma_abs_slope_pct,
            permits=permits,
        )
