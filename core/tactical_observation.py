"""Causal local-battlefield observations for adaptive micro-warrior learning.

This module does not make trading decisions and does not mutate DSL.  It freezes
point-in-time features from a BattleCase market prefix so later memory/learning
layers can be trained without future leakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np

from core.indicators import CoreTALib
from core.tactical_discovery import BattleCase


SCHEMA_VERSION = "tactical_observation/jma_local_v1"


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _timestamp(value: Any) -> str:
    digits = _digits(value)
    if len(digits) < 14:
        raise ValueError(f"observation timestamp는 YYYYMMDDHHMMSS여야 합니다: {value!r}")
    return digits[:14]


def _clock_seconds(hhmmss: str) -> int:
    text = _digits(hhmmss)
    if len(text) < 6:
        raise ValueError(f"clock은 HHMMSS여야 합니다: {hhmmss!r}")
    h, m, s = int(text[:2]), int(text[2:4]), int(text[4:6])
    if h > 23 or m > 59 or s > 59:
        raise ValueError(f"유효하지 않은 clock입니다: {hhmmss!r}")
    return h * 3600 + m * 60 + s


def _finite(name: str, value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"TacticalObservation feature가 유한하지 않습니다: {name}={value!r}")
    return number


def _safe_ratio(numerator: float, denominator: float, *, default: float = 0.0) -> float:
    if not math.isfinite(float(denominator)) or abs(float(denominator)) <= 1e-12:
        return float(default)
    return float(numerator) / float(denominator)


def _pct_change(current: float, previous: float) -> float:
    return _safe_ratio(float(current) - float(previous), abs(float(previous))) * 100.0


@dataclass(frozen=True)
class JmaLocalObservationConfig:
    expected_timeframe: str = "5m"
    session_open: str = "090000"
    session_close: str = "153000"
    fast_length: int = 7
    fast_phase: float = 50.0
    fast_power: int = 2
    slow_length: int = 50
    slow_phase: float = 50.0
    slow_power: int = 4
    sma_length: int = 60
    atr_length: int = 14
    slope_lookback: int = 3
    structure_lookback: int = 6
    volume_lookback: int = 20
    recent_return_windows: tuple[int, ...] = (3, 6, 12)

    def validate(self) -> None:
        if not str(self.expected_timeframe or "").strip():
            raise ValueError("observation expected_timeframe이 필요합니다.")
        open_seconds = _clock_seconds(self.session_open)
        close_seconds = _clock_seconds(self.session_close)
        if open_seconds >= close_seconds:
            raise ValueError("session_open은 session_close보다 빨라야 합니다.")
        for name in (
            "fast_length",
            "fast_power",
            "slow_length",
            "slow_power",
            "sma_length",
            "atr_length",
            "slope_lookback",
            "structure_lookback",
            "volume_lookback",
        ):
            if int(getattr(self, name)) < 1:
                raise ValueError(f"{name}은 1 이상이어야 합니다.")
        if not self.recent_return_windows or any(int(item) < 1 for item in self.recent_return_windows):
            raise ValueError("recent_return_windows는 1 이상의 lookback을 가져야 합니다.")

    @property
    def required_history(self) -> int:
        self.validate()
        return max(
            int(self.slow_length),
            int(self.sma_length),
            int(self.atr_length) + 1,
            int(self.slope_lookback) + 2,
            int(self.structure_lookback) + 1,
            int(self.volume_lookback) + 1,
            max(int(item) for item in self.recent_return_windows) + 1,
        )


@dataclass(frozen=True)
class TacticalObservation:
    case_id: str
    case_hash: str
    symbol: str
    session_date: str
    timestamp: str
    knowledge_cutoff: str
    family_id: str
    generation_hash: str
    resolution_mode: str
    feature_schema_version: str
    features: Mapping[str, float] = field(default_factory=dict)
    observation_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        case: BattleCase,
        timestamp: str,
        family_id: str,
        generation_hash: str,
        resolution_mode: str,
        features: Mapping[str, float],
    ) -> "TacticalObservation":
        case.validate()
        timestamp = _timestamp(timestamp)
        family_id = str(family_id or "").strip()
        generation_hash = str(generation_hash or "").strip()
        resolution_mode = str(resolution_mode or "").strip()
        if not family_id or not generation_hash or not resolution_mode:
            raise ValueError("family_id/generation_hash/resolution_mode가 필요합니다.")
        normalized = {str(key): _finite(str(key), value) for key, value in dict(features).items()}
        if not normalized:
            raise ValueError("TacticalObservation features가 비어 있습니다.")
        identity = {
            "schema": SCHEMA_VERSION,
            "case_id": case.case_id,
            "case_hash": case.case_hash,
            "symbol": case.symbol,
            "session_date": _digits(case.session_date)[:8],
            "timestamp": timestamp,
            "knowledge_cutoff": timestamp,
            "family_id": family_id,
            "generation_hash": generation_hash,
            "resolution_mode": resolution_mode,
            "features": normalized,
        }
        return cls(
            case_id=case.case_id,
            case_hash=case.case_hash,
            symbol=case.symbol,
            session_date=_digits(case.session_date)[:8],
            timestamp=timestamp,
            knowledge_cutoff=timestamp,
            family_id=family_id,
            generation_hash=generation_hash,
            resolution_mode=resolution_mode,
            feature_schema_version=SCHEMA_VERSION,
            features=normalized,
            observation_hash=_stable_hash(identity),
        )


class JmaLocalObservationBuilder:
    """Freeze causal JMA/local-price features from one BattleCase prefix."""

    def __init__(self, config: JmaLocalObservationConfig | None = None):
        self.config = config or JmaLocalObservationConfig()
        self.config.validate()

    def _prefix(self, case: BattleCase, timestamp: str) -> tuple[dict[str, np.ndarray], int]:
        case.validate()
        timestamp = _timestamp(timestamp)
        session = _digits(case.session_date)[:8]
        if timestamp[:8] != session:
            raise ValueError("observation timestamp 거래일이 BattleCase session_date와 다릅니다.")
        market = case.market
        times = [_timestamp(item) for item in market["time"]]
        matches = [index for index, value in enumerate(times) if value == timestamp]
        if len(matches) != 1:
            raise ValueError(f"observation timestamp가 market에 정확히 1개 있어야 합니다: {timestamp}")
        end = matches[0]
        if end + 1 < self.config.required_history:
            raise ValueError(
                f"observation warm-up 부족: bars={end + 1}, required={self.config.required_history}"
            )
        meta = dict(market.get("_meta") or {})
        actual_timeframe = str(meta.get("timeframe") or "").strip()
        if actual_timeframe != self.config.expected_timeframe:
            raise ValueError(
                f"observation timeframe({actual_timeframe or 'missing'})과 "
                f"expected({self.config.expected_timeframe})가 다릅니다."
            )
        current_clock = timestamp[8:14]
        current_seconds = _clock_seconds(current_clock)
        open_seconds = _clock_seconds(self.config.session_open)
        close_seconds = _clock_seconds(self.config.session_close)
        if current_seconds < open_seconds or current_seconds > close_seconds:
            raise ValueError("observation timestamp가 선언된 정규장 범위를 벗어납니다.")
        prefix: dict[str, np.ndarray] = {}
        for key in ("open", "high", "low", "close", "volume"):
            prefix[key] = np.asarray(market[key][: end + 1], dtype=float)
        prefix["time"] = np.asarray(times[: end + 1], dtype=object)
        return prefix, end

    def build(
        self,
        *,
        case: BattleCase,
        timestamp: str,
        family_id: str,
        generation_hash: str,
        resolution_mode: str = "JMA_TCR_5M",
    ) -> TacticalObservation:
        data, _ = self._prefix(case, timestamp)
        timestamp = _timestamp(timestamp)
        cfg = self.config
        o, h, l, c, v = (data[key] for key in ("open", "high", "low", "close", "volume"))
        if not all(np.all(np.isfinite(values)) for values in (o, h, l, c, v)):
            raise ValueError("observation market prefix에 NaN/Infinity가 있습니다.")
        if c[-1] <= 0:
            raise ValueError("observation close는 0보다 커야 합니다.")

        fast = np.asarray(CoreTALib.jma(c, cfg.fast_length, cfg.fast_phase, cfg.fast_power), dtype=float)
        slow = np.asarray(CoreTALib.jma(c, cfg.slow_length, cfg.slow_phase, cfg.slow_power), dtype=float)
        trend = np.asarray(CoreTALib.sma(c, cfg.sma_length), dtype=float)
        atr = np.asarray(CoreTALib.atr(h, l, c, cfg.atr_length), dtype=float)
        look = int(cfg.slope_lookback)
        structure = int(cfg.structure_lookback)
        close_now = float(c[-1])

        cross_up = (fast > slow) & (CoreTALib.shift(fast, 1) <= CoreTALib.shift(slow, 1))
        cross_down = (fast < slow) & (CoreTALib.shift(fast, 1) >= CoreTALib.shift(slow, 1))
        bars_since_cross = np.asarray(CoreTALib.bars_since(cross_up), dtype=float)
        spread = fast - slow
        spread_velocity = float(spread[-1] - spread[-1 - look]) / float(look)
        fast_acceleration = float(fast[-1] - (2.0 * fast[-2]) + fast[-3])

        recent_high = h[-(structure + 1) :]
        recent_low = l[-(structure + 1) :]
        higher_high_ratio = float(np.mean(recent_high[1:] > recent_high[:-1]))
        higher_low_ratio = float(np.mean(recent_low[1:] > recent_low[:-1]))
        lower_high_ratio = float(np.mean(recent_high[1:] < recent_high[:-1]))
        lower_low_ratio = float(np.mean(recent_low[1:] < recent_low[:-1]))
        ranges = h - l
        previous_ranges = ranges[-(structure + 1) : -1]
        mean_previous_range = float(np.mean(previous_ranges))
        current_range = float(ranges[-1])
        body_up_ratio = float(np.mean(c[-structure:] > o[-structure:]))
        close_location = _safe_ratio(float(c[-1] - l[-1]), current_range, default=0.5)
        upper_wick = float(h[-1] - max(o[-1], c[-1]))
        lower_wick = float(min(o[-1], c[-1]) - l[-1])
        wick_asymmetry = _safe_ratio(upper_wick - lower_wick, current_range)
        prior_structure_high = float(np.max(h[-(structure + 1) : -1]))

        session_mask = np.asarray([str(item)[:8] == _digits(case.session_date)[:8] for item in data["time"]], dtype=bool)
        if not np.any(session_mask):
            raise ValueError("observation prefix에 현재 session bar가 없습니다.")
        session_open_price = float(o[np.flatnonzero(session_mask)[0]])
        session_high = float(np.max(h[session_mask]))
        session_low = float(np.min(l[session_mask]))

        volume_window = min(int(cfg.volume_lookback), len(v) - 1)
        previous_volume_mean = float(np.mean(v[-(volume_window + 1) : -1]))
        previous_close = float(c[-2])

        current_seconds = _clock_seconds(timestamp[8:14])
        open_seconds = _clock_seconds(cfg.session_open)
        close_seconds = _clock_seconds(cfg.session_close)
        session_span = close_seconds - open_seconds

        features: dict[str, float] = {
            "jma_fast": float(fast[-1]),
            "jma_slow": float(slow[-1]),
            "jma_spread_pct": _safe_ratio(float(spread[-1]), close_now) * 100.0,
            "jma_fast_slope_pct": _safe_ratio(float(fast[-1] - fast[-1 - look]), close_now) * 100.0 / look,
            "jma_slow_slope_pct": _safe_ratio(float(slow[-1] - slow[-1 - look]), close_now) * 100.0 / look,
            "jma_spread_velocity_pct": _safe_ratio(spread_velocity, close_now) * 100.0,
            "jma_fast_acceleration_pct": _safe_ratio(fast_acceleration, close_now) * 100.0,
            "jma_cross_up_now": 1.0 if bool(cross_up[-1]) else 0.0,
            "jma_cross_down_now": 1.0 if bool(cross_down[-1]) else 0.0,
            "bars_since_jma_cross_up": float(bars_since_cross[-1]) if math.isfinite(float(bars_since_cross[-1])) else -1.0,
            "jma_spread_atr": _safe_ratio(float(spread[-1]), float(atr[-1])),
            "sma60": float(trend[-1]),
            "sma60_slope_pct": _safe_ratio(float(trend[-1] - trend[-1 - look]), close_now) * 100.0 / look,
            "price_to_sma60_pct": _safe_ratio(close_now - float(trend[-1]), float(trend[-1])) * 100.0,
            "price_to_sma60_atr": _safe_ratio(close_now - float(trend[-1]), float(atr[-1])),
            "atr_pct": _safe_ratio(float(atr[-1]), close_now) * 100.0,
            "current_range_pct": _safe_ratio(current_range, close_now) * 100.0,
            "range_vs_recent": _safe_ratio(current_range, mean_previous_range),
            "volume_ratio": _safe_ratio(float(v[-1]), previous_volume_mean),
            "volume_change_vs_recent_pct": _safe_ratio(float(v[-1] - previous_volume_mean), previous_volume_mean) * 100.0,
            "bar_gap_pct": _safe_ratio(float(o[-1] - previous_close), previous_close) * 100.0,
            "higher_high_ratio": higher_high_ratio,
            "higher_low_ratio": higher_low_ratio,
            "lower_high_ratio": lower_high_ratio,
            "lower_low_ratio": lower_low_ratio,
            "swing_high_slope_pct": _safe_ratio(float(recent_high[-1] - recent_high[0]), close_now) * 100.0 / structure,
            "swing_low_slope_pct": _safe_ratio(float(recent_low[-1] - recent_low[0]), close_now) * 100.0 / structure,
            "body_up_ratio": body_up_ratio,
            "close_location_in_range": close_location,
            "wick_asymmetry": wick_asymmetry,
            "breakout_distance_pct": _safe_ratio(close_now - prior_structure_high, close_now) * 100.0,
            "return_from_session_open_pct": _pct_change(close_now, session_open_price),
            "distance_from_session_high_pct": _safe_ratio(close_now - session_high, session_high) * 100.0,
            "distance_from_session_low_pct": _safe_ratio(close_now - session_low, session_low) * 100.0,
            "minutes_from_open": float(current_seconds - open_seconds) / 60.0,
            "minutes_to_close": float(close_seconds - current_seconds) / 60.0,
            "session_progress_ratio": _safe_ratio(current_seconds - open_seconds, session_span),
        }
        for window in cfg.recent_return_windows:
            window = int(window)
            features[f"recent_return_{window}bar_pct"] = _pct_change(close_now, float(c[-1 - window]))

        return TacticalObservation.create(
            case=case,
            timestamp=timestamp,
            family_id=family_id,
            generation_hash=generation_hash,
            resolution_mode=resolution_mode,
            features=features,
        )
