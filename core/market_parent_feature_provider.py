"""Concrete deterministic MARKET parent-feature provider for PCTX2A.

The provider consumes one explicitly configured SessionMarketProvider and one
explicit KRX benchmark symbol.  It never discovers a universe or production
source, never emits order/gate decisions, and only publishes descriptive,
point-in-time market features through the trusted PCTX1 contracts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any, Mapping

import numpy as np

from core.parent_feature_provider import (
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureSpec,
)
from core.tactical_market import SessionMarketProvider


PROVIDER_VERSION = "v1"
CALCULATION_POLICY = "EXACT_SOURCE_BAR_PREFIX_DETERMINISTIC_NO_GATE_DECISION"
REGIME_POLICY = "SMA_LEVEL_AND_SLOPE_THREE_STATE"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"market parent feature time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 숫자여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 숫자여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return number


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


def _namespace(value: str) -> str:
    result = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", result):
        raise ValueError("market parent feature namespace는 소문자 영문자로 시작하는 식별자여야 합니다.")
    return result


@dataclass(frozen=True)
class MarketParentFeatureConfig:
    timeframe: str = "5m"
    short_return_bars: int = 3
    long_return_bars: int = 12
    sma_period: int = 20
    slope_bars: int = 3
    atr_period: int = 14
    volume_period: int = 20

    def validate(self) -> None:
        if not str(self.timeframe or "").strip():
            raise ValueError("market parent feature timeframe이 필요합니다.")
        for name in (
            "short_return_bars",
            "long_return_bars",
            "sma_period",
            "slope_bars",
            "atr_period",
            "volume_period",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"{name}은 1 이상의 정수여야 합니다.")
        if self.short_return_bars >= self.long_return_bars:
            raise ValueError("short_return_bars는 long_return_bars보다 작아야 합니다.")

    @property
    def required_bars(self) -> int:
        self.validate()
        return max(
            self.long_return_bars + 1,
            self.sma_period + self.slope_bars,
            self.atr_period + 1,
            self.volume_period + 1,
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "timeframe": self.timeframe,
            "short_return_bars": self.short_return_bars,
            "long_return_bars": self.long_return_bars,
            "sma_period": self.sma_period,
            "slope_bars": self.slope_bars,
            "atr_period": self.atr_period,
            "volume_period": self.volume_period,
            "required_bars": self.required_bars,
        }


class KrxBenchmarkMarketParentFeatureProvider:
    """Causal descriptive MARKET provider for one explicitly named benchmark.

    The class is reusable for KOSPI/KOSDAQ-like benchmark instruments, but each
    instance owns an immutable namespace/symbol manifest.  No benchmark symbol
    or source is guessed by this module.
    """

    def __init__(
        self,
        market_provider: SessionMarketProvider,
        *,
        benchmark_symbol: str,
        feature_namespace: str,
        source_authority: str,
        config: MarketParentFeatureConfig | None = None,
    ):
        self.market_provider = market_provider
        self.benchmark_symbol = str(benchmark_symbol or "").strip()
        self.feature_namespace = _namespace(feature_namespace)
        self.source_authority = str(source_authority or "").strip()
        self.config = config or MarketParentFeatureConfig()
        self.config.validate()
        if not self.benchmark_symbol:
            raise ValueError("benchmark_symbol이 필요합니다.")
        if not self.source_authority:
            raise ValueError("market parent feature source_authority가 필요합니다.")

        ns = self.feature_namespace
        prefix = f"market.{ns}_"
        self._manifest = ParentFeatureManifest(
            provider_id=f"krx_benchmark_market_{ns}",
            provider_version=PROVIDER_VERSION,
            layer="MARKET",
            context_id=f"{ns.upper()}_BENCHMARK",
            max_staleness_seconds=0,
            features=(
                ParentFeatureSpec(prefix + "return_short_pct", "return_short_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "return_long_pct", "return_long_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "sma_slope_pct", "sma_slope_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "price_to_sma_pct", "price_to_sma_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "atr_pct", "atr_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "volume_ratio", "volume_ratio", "NUMBER"),
                ParentFeatureSpec(prefix + "regime_state", "regime_state", "STRING"),
            ),
            metadata={
                "benchmark_symbol": self.benchmark_symbol,
                "source_authority": self.source_authority,
                "calculation_policy": CALCULATION_POLICY,
                "regime_policy": REGIME_POLICY,
                "config": self.config.public_dict(),
            },
        )
        self._manifest.validate()

    @property
    def manifest(self) -> ParentFeatureManifest:
        return self._manifest

    def _validate_market(self, market: Mapping[str, Any], *, as_of: str) -> dict[str, Any]:
        required = ("time", "open", "high", "low", "close", "volume")
        missing = [key for key in required if key not in market]
        if missing:
            raise ValueError(f"market parent source 필드가 누락되었습니다: {missing}")
        lengths = {key: len(market[key]) for key in required}
        if len(set(lengths.values())) != 1:
            raise ValueError(f"market parent source 길이가 일치하지 않습니다: {lengths}")
        size = lengths["close"]
        if size < self.config.required_bars:
            raise ValueError(
                f"market parent source history가 부족합니다: {size} < {self.config.required_bars}"
            )

        meta = market.get("_meta") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("market parent source _meta는 Mapping이어야 합니다.")
        source = str(meta.get("source") or "").strip()
        instrument = str(meta.get("instrument") or "").strip()
        timeframe = str(meta.get("timeframe") or "").strip()
        if not source:
            raise ValueError("market parent source metadata source가 필요합니다.")
        if instrument != self.benchmark_symbol:
            raise ValueError(
                f"market parent benchmark instrument 불일치: {instrument!r} != {self.benchmark_symbol!r}"
            )
        if timeframe != self.config.timeframe:
            raise ValueError(
                f"market parent timeframe 불일치: {timeframe!r} != {self.config.timeframe!r}"
            )

        times = tuple(_time_key(item) for item in market["time"])
        if len(set(times)) != len(times):
            raise ValueError("market parent source timestamp에 중복이 있습니다.")
        if any(times[index] >= times[index + 1] for index in range(len(times) - 1)):
            raise ValueError("market parent source timestamp는 엄격 오름차순이어야 합니다.")
        requested = _time_key(as_of)
        if any(item > requested for item in times):
            raise ValueError("market parent source에 as_of 이후 미래 bar가 있습니다.")
        if times[-1] != requested:
            raise ValueError(
                f"market parent source 마지막 bar가 exact as_of가 아닙니다: {times[-1]} != {requested}"
            )

        arrays: dict[str, np.ndarray] = {}
        for key in ("open", "high", "low", "close", "volume"):
            try:
                values = np.asarray(market[key], dtype=float)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"market parent source {key} 숫자 변환 실패") from exc
            if not np.all(np.isfinite(values)):
                raise ValueError(f"market parent source {key}에 NaN/Infinity가 있습니다.")
            arrays[key] = values
        if np.any(arrays["high"] < np.maximum(arrays["open"], arrays["close"])):
            raise ValueError("market parent source high가 open/close보다 낮은 bar가 있습니다.")
        if np.any(arrays["low"] > np.minimum(arrays["open"], arrays["close"])):
            raise ValueError("market parent source low가 open/close보다 높은 bar가 있습니다.")
        if np.any(arrays["high"] < arrays["low"]):
            raise ValueError("market parent source high < low bar가 있습니다.")
        if np.any(arrays["close"] <= 0) or np.any(arrays["volume"] < 0):
            raise ValueError("market parent source close/volume 범위가 올바르지 않습니다.")

        return {
            "times": times,
            "source": source,
            **arrays,
        }

    @staticmethod
    def _sma(close: np.ndarray, period: int, end_index: int) -> float:
        start = end_index - period + 1
        if start < 0:
            raise ValueError("market parent SMA history가 부족합니다.")
        return float(np.mean(close[start:end_index + 1]))

    def _features(self, validated: Mapping[str, Any]) -> dict[str, Any]:
        cfg = self.config
        close = np.asarray(validated["close"], dtype=float)
        high = np.asarray(validated["high"], dtype=float)
        low = np.asarray(validated["low"], dtype=float)
        volume = np.asarray(validated["volume"], dtype=float)
        last = len(close) - 1

        short_base = close[last - cfg.short_return_bars]
        long_base = close[last - cfg.long_return_bars]
        return_short_pct = (close[last] / short_base - 1.0) * 100.0
        return_long_pct = (close[last] / long_base - 1.0) * 100.0

        sma_now = self._sma(close, cfg.sma_period, last)
        sma_then = self._sma(close, cfg.sma_period, last - cfg.slope_bars)
        sma_slope_pct = (sma_now / sma_then - 1.0) * 100.0
        price_to_sma_pct = (close[last] / sma_now - 1.0) * 100.0

        true_ranges = []
        start = last - cfg.atr_period + 1
        for index in range(start, last + 1):
            previous_close = close[index - 1]
            true_ranges.append(
                max(
                    high[index] - low[index],
                    abs(high[index] - previous_close),
                    abs(low[index] - previous_close),
                )
            )
        atr = float(np.mean(true_ranges))
        atr_pct = atr / close[last] * 100.0

        volume_baseline = float(np.mean(volume[last - cfg.volume_period:last]))
        if volume_baseline <= 0:
            raise ValueError("market parent volume baseline이 0 이하입니다.")
        volume_ratio = float(volume[last] / volume_baseline)

        if close[last] > sma_now and sma_slope_pct > 0:
            regime_state = "UPTREND"
        elif close[last] < sma_now and sma_slope_pct < 0:
            regime_state = "DOWNTREND"
        else:
            regime_state = "MIXED"

        features = {
            "return_short_pct": _number(return_short_pct, "return_short_pct"),
            "return_long_pct": _number(return_long_pct, "return_long_pct"),
            "sma_slope_pct": _number(sma_slope_pct, "sma_slope_pct"),
            "price_to_sma_pct": _number(price_to_sma_pct, "price_to_sma_pct"),
            "atr_pct": _number(atr_pct, "atr_pct"),
            "volume_ratio": _number(volume_ratio, "volume_ratio"),
            "regime_state": regime_state,
        }
        return features

    def build(
        self,
        *,
        as_of: str,
        knowledge_cutoff: str,
        dependencies: Mapping[str, ParentFeatureProviderResult] | None = None,
    ) -> ParentFeatureProviderResult:
        target = _time_key(as_of)
        cutoff = _time_key(knowledge_cutoff)
        if target != cutoff:
            raise ValueError("PCTX2A market provider는 exact as_of == knowledge_cutoff를 요구합니다.")
        if dependencies:
            raise ValueError("MARKET root provider는 parent dependencies를 받지 않습니다.")

        market = self.market_provider.load_session(
            symbol=self.benchmark_symbol,
            session_date=target[:8],
            timeframe=self.config.timeframe,
            required_bars=self.config.required_bars,
            end_time=target[8:14],
        )
        if not isinstance(market, Mapping):
            raise ValueError("market parent source provider는 Mapping market을 반환해야 합니다.")
        validated = self._validate_market(market, as_of=target)
        features = self._features(validated)
        prefix_hash = _stable_hash(
            {
                "benchmark_symbol": self.benchmark_symbol,
                "timeframe": self.config.timeframe,
                "times": validated["times"],
                "open": tuple(float(item) for item in validated["open"]),
                "high": tuple(float(item) for item in validated["high"]),
                "low": tuple(float(item) for item in validated["low"]),
                "close": tuple(float(item) for item in validated["close"]),
                "volume": tuple(float(item) for item in validated["volume"]),
            }
        )
        result = ParentFeatureProviderResult(
            manifest=self.manifest,
            as_of=target,
            knowledge_cutoff=cutoff,
            source=str(validated["source"]),
            features=features,
            metadata={
                "source_authority": self.source_authority,
                "benchmark_symbol": self.benchmark_symbol,
                "feature_namespace": self.feature_namespace,
                "source_prefix_hash": prefix_hash,
                "source_start": validated["times"][0],
                "source_end": validated["times"][-1],
                "source_bar_count": len(validated["times"]),
                "calculation_policy": CALCULATION_POLICY,
                "regime_policy": REGIME_POLICY,
                "config": self.config.public_dict(),
            },
        )
        result.validate()
        return result
