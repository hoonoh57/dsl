"""Deterministic descriptive SECTOR parent-feature provider for PCTX2D.

The provider consumes one explicitly configured sector benchmark source and one
explicit MARKET parent result.  It does not discover sector members, rank peer
symbols, issue gate decisions, or call Broker/DSL execution code.
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
CALCULATION_POLICY = "EXACT_SECTOR_SOURCE_PREFIX_PLUS_EXPLICIT_MARKET_DEPENDENCY"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"sector parent feature time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _namespace(value: str) -> str:
    result = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]*", result):
        raise ValueError("sector namespace는 소문자 영문자로 시작하는 식별자여야 합니다.")
    return result


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한한 NUMBER여야 합니다.") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return number


@dataclass(frozen=True)
class SectorParentFeatureConfig:
    timeframe: str = "5m"
    short_return_bars: int = 3
    long_return_bars: int = 12
    sma_period: int = 20
    slope_bars: int = 3

    def validate(self) -> None:
        if not str(self.timeframe or "").strip():
            raise ValueError("sector parent timeframe이 필요합니다.")
        for name in ("short_return_bars", "long_return_bars", "sma_period", "slope_bars"):
            value = getattr(self, name)
            if not isinstance(value, int) or value < 1:
                raise ValueError(f"{name}은 1 이상의 정수여야 합니다.")
        if self.short_return_bars >= self.long_return_bars:
            raise ValueError("short_return_bars는 long_return_bars보다 작아야 합니다.")

    @property
    def required_bars(self) -> int:
        self.validate()
        return max(self.long_return_bars + 1, self.sma_period + self.slope_bars)

    def public_dict(self) -> dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "short_return_bars": self.short_return_bars,
            "long_return_bars": self.long_return_bars,
            "sma_period": self.sma_period,
            "slope_bars": self.slope_bars,
            "required_bars": self.required_bars,
        }


class KrxSectorBenchmarkParentFeatureProvider:
    """One explicit sector benchmark conditioned on one explicit MARKET result."""

    def __init__(
        self,
        market_provider: SessionMarketProvider,
        *,
        sector_symbol: str,
        sector_namespace: str,
        source_authority: str,
        market_dependency_provider_id: str,
        market_return_feature_id: str,
        market_regime_feature_id: str,
        config: SectorParentFeatureConfig | None = None,
    ):
        self.market_provider = market_provider
        self.sector_symbol = str(sector_symbol or "").strip()
        self.sector_namespace = _namespace(sector_namespace)
        self.source_authority = str(source_authority or "").strip()
        self.market_dependency_provider_id = str(market_dependency_provider_id or "").strip()
        self.market_return_feature_id = str(market_return_feature_id or "").strip()
        self.market_regime_feature_id = str(market_regime_feature_id or "").strip()
        self.config = config or SectorParentFeatureConfig()
        self.config.validate()
        for value, label in (
            (self.sector_symbol, "sector_symbol"),
            (self.source_authority, "source_authority"),
            (self.market_dependency_provider_id, "market_dependency_provider_id"),
            (self.market_return_feature_id, "market_return_feature_id"),
            (self.market_regime_feature_id, "market_regime_feature_id"),
        ):
            if not value:
                raise ValueError(f"{label}가 필요합니다.")

        ns = self.sector_namespace
        prefix = f"sector.{ns}_"
        self._manifest = ParentFeatureManifest(
            provider_id=f"krx_sector_benchmark_{ns}",
            provider_version=PROVIDER_VERSION,
            layer="SECTOR",
            context_id=f"{ns.upper()}_SECTOR_BENCHMARK",
            max_staleness_seconds=0,
            features=(
                ParentFeatureSpec(prefix + "return_short_pct", "return_short_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "return_long_pct", "return_long_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "sma_slope_pct", "sma_slope_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "price_to_sma_pct", "price_to_sma_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "relative_strength_long_pct", "relative_strength_long_pct", "NUMBER"),
                ParentFeatureSpec(prefix + "regime_state", "regime_state", "STRING"),
                ParentFeatureSpec(prefix + "market_alignment", "market_alignment", "BOOLEAN"),
            ),
            metadata={
                "sector_symbol": self.sector_symbol,
                "source_authority": self.source_authority,
                "market_dependency_provider_id": self.market_dependency_provider_id,
                "market_return_feature_id": self.market_return_feature_id,
                "market_regime_feature_id": self.market_regime_feature_id,
                "calculation_policy": CALCULATION_POLICY,
                "config": self.config.public_dict(),
            },
        )
        self._manifest.validate()

    @property
    def manifest(self) -> ParentFeatureManifest:
        return self._manifest

    @staticmethod
    def _feature_value(result: ParentFeatureProviderResult, feature_id: str) -> Any:
        wanted = str(feature_id).strip()
        for spec in result.manifest.features:
            if str(spec.feature_id).strip() == wanted:
                key = str(spec.feature_key).strip()
                if key not in result.features:
                    raise ValueError(f"dependency feature value가 없습니다: {wanted}")
                return result.features[key]
        raise ValueError(f"dependency manifest에 필요한 feature_id가 없습니다: {wanted}")

    def _dependency(self, dependencies: Mapping[str, ParentFeatureProviderResult] | None, target: str) -> ParentFeatureProviderResult:
        if not dependencies or set(dependencies) != {self.market_dependency_provider_id}:
            raise ValueError("SECTOR provider는 선언된 MARKET dependency 하나만 필요합니다.")
        parent = dependencies[self.market_dependency_provider_id]
        if not isinstance(parent, ParentFeatureProviderResult):
            raise ValueError("MARKET dependency는 ParentFeatureProviderResult여야 합니다.")
        parent.validate()
        if str(parent.manifest.provider_id).strip() != self.market_dependency_provider_id:
            raise ValueError("MARKET dependency provider_id가 다릅니다.")
        if _time_key(parent.as_of) != target or _time_key(parent.knowledge_cutoff) != target:
            raise ValueError("MARKET dependency가 exact target timestamp와 다릅니다.")
        return parent

    def _validate_market(self, market: Mapping[str, Any], target: str) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], str]:
        for key in ("time", "open", "high", "low", "close", "volume"):
            if key not in market:
                raise ValueError(f"sector source 필드가 누락되었습니다: {key}")
        lengths = {key: len(market[key]) for key in ("time", "open", "high", "low", "close", "volume")}
        if len(set(lengths.values())) != 1 or lengths["close"] < self.config.required_bars:
            raise ValueError("sector source history 길이가 부족하거나 일치하지 않습니다.")
        meta = market.get("_meta") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("sector source _meta는 Mapping이어야 합니다.")
        source = str(meta.get("source") or "").strip()
        if not source:
            raise ValueError("sector source metadata source가 필요합니다.")
        if str(meta.get("instrument") or "").strip() != self.sector_symbol:
            raise ValueError("sector source instrument가 configured sector_symbol과 다릅니다.")
        if str(meta.get("timeframe") or "").strip() != self.config.timeframe:
            raise ValueError("sector source timeframe이 configured timeframe과 다릅니다.")
        times = tuple(_time_key(item) for item in market["time"])
        if len(set(times)) != len(times) or any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
            raise ValueError("sector source timestamp는 고유한 엄격 오름차순이어야 합니다.")
        if times[-1] != target or any(item > target for item in times):
            raise ValueError("sector source는 exact as_of까지의 causal prefix여야 합니다.")
        close = np.asarray(market["close"], dtype=float)
        volume = np.asarray(market["volume"], dtype=float)
        if not np.all(np.isfinite(close)) or not np.all(np.isfinite(volume)) or np.any(close <= 0) or np.any(volume < 0):
            raise ValueError("sector source close/volume이 유효하지 않습니다.")
        for key in ("open", "high", "low"):
            values = np.asarray(market[key], dtype=float)
            if not np.all(np.isfinite(values)):
                raise ValueError(f"sector source {key}가 유효하지 않습니다.")
        return close, volume, times, source

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
            raise ValueError("SECTOR provider는 exact as_of == knowledge_cutoff를 요구합니다.")
        market_parent = self._dependency(dependencies, target)
        market_return = _finite(self._feature_value(market_parent, self.market_return_feature_id), "market return")
        market_regime = self._feature_value(market_parent, self.market_regime_feature_id)
        if not isinstance(market_regime, str):
            raise ValueError("market regime dependency는 STRING이어야 합니다.")

        market = self.market_provider.load_session(
            symbol=self.sector_symbol,
            session_date=target[:8],
            timeframe=self.config.timeframe,
            required_bars=self.config.required_bars,
            end_time=target[8:14],
        )
        if not isinstance(market, Mapping):
            raise ValueError("sector source provider는 Mapping market을 반환해야 합니다.")
        close, volume, times, source = self._validate_market(market, target)
        last = len(close) - 1
        short_return = (close[last] / close[last - self.config.short_return_bars] - 1.0) * 100.0
        long_return = (close[last] / close[last - self.config.long_return_bars] - 1.0) * 100.0
        sma_now = float(np.mean(close[last - self.config.sma_period + 1:last + 1]))
        then_end = last - self.config.slope_bars
        sma_then = float(np.mean(close[then_end - self.config.sma_period + 1:then_end + 1]))
        sma_slope = (sma_now / sma_then - 1.0) * 100.0
        price_to_sma = (close[last] / sma_now - 1.0) * 100.0
        if close[last] > sma_now and sma_slope > 0:
            regime = "UPTREND"
        elif close[last] < sma_now and sma_slope < 0:
            regime = "DOWNTREND"
        else:
            regime = "MIXED"
        relative_strength = long_return - market_return
        alignment = (
            (regime == "UPTREND" and market_regime == "UPTREND")
            or (regime == "DOWNTREND" and market_regime == "DOWNTREND")
            or (regime == "MIXED" and market_regime == "MIXED")
        )
        features = {
            "return_short_pct": _finite(short_return, "sector short return"),
            "return_long_pct": _finite(long_return, "sector long return"),
            "sma_slope_pct": _finite(sma_slope, "sector sma slope"),
            "price_to_sma_pct": _finite(price_to_sma, "sector price to sma"),
            "relative_strength_long_pct": _finite(relative_strength, "sector relative strength"),
            "regime_state": regime,
            "market_alignment": bool(alignment),
        }
        prefix_hash = _stable_hash({
            "sector_symbol": self.sector_symbol,
            "timeframe": self.config.timeframe,
            "times": times,
            "close": tuple(float(item) for item in close),
            "volume": tuple(float(item) for item in volume),
        })
        result = ParentFeatureProviderResult(
            manifest=self.manifest,
            as_of=target,
            knowledge_cutoff=cutoff,
            source=source,
            features=features,
            dependency_result_hashes=(market_parent.result_hash,),
            metadata={
                "source_authority": self.source_authority,
                "sector_symbol": self.sector_symbol,
                "sector_namespace": self.sector_namespace,
                "source_prefix_hash": prefix_hash,
                "source_start": times[0],
                "source_end": times[-1],
                "source_bar_count": len(times),
                "market_dependency_result_hash": market_parent.result_hash,
                "calculation_policy": CALCULATION_POLICY,
                "config": self.config.public_dict(),
            },
        )
        result.validate()
        return result
