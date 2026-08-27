"""Exact root-provider orchestration for precomputed parent-context frames.

PCTX2C runs explicitly configured root Parent Feature Providers *before* tactic
execution.  It materializes one PCTX1 assembly for every exact target bar time
and returns a PCTX2B ParentContextFrame plus the matching feature registry.

The orchestrator never performs nearest-time lookup, fill-forward, universe
selection, deployment scoring, Broker actions, or provider calls from Backtest.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureProvider,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
)


SCHEMA_VERSION = "parent_context_frame_build/v1"
BUILD_POLICY = "PRECOMPUTE_ROOT_PROVIDERS_FOR_EVERY_EXACT_TARGET_BAR_NO_FILL_FORWARD"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"parent context target time은 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


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


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _target_timeline(target_market: Mapping[str, Any]) -> tuple[str, str, str, tuple[str, ...], str]:
    if not isinstance(target_market, Mapping):
        raise ValueError("target_market은 Mapping이어야 합니다.")
    raw_times = target_market.get("time")
    if not isinstance(raw_times, Sequence) or isinstance(raw_times, (str, bytes)):
        raise ValueError("target_market time 배열이 필요합니다.")
    times = tuple(_time_key(item) for item in raw_times)
    if not times:
        raise ValueError("target_market time 배열이 비어 있습니다.")
    if len(set(times)) != len(times):
        raise ValueError("target_market timestamp에 중복이 있습니다.")
    if any(times[index] >= times[index + 1] for index in range(len(times) - 1)):
        raise ValueError("target_market timestamp는 엄격 오름차순이어야 합니다.")

    meta = target_market.get("_meta") or {}
    if not isinstance(meta, Mapping):
        raise ValueError("target_market _meta는 Mapping이어야 합니다.")
    instrument = _text(meta.get("instrument"), "target_market instrument")
    timeframe = _text(meta.get("timeframe"), "target_market timeframe")
    source = _text(meta.get("source"), "target_market source")
    timeline_hash = _stable_hash(
        {
            "schema": SCHEMA_VERSION,
            "instrument": instrument,
            "timeframe": timeframe,
            "source": source,
            "times": times,
        }
    )
    return instrument, timeframe, source, times, timeline_hash


def _provider_identity(provider: ParentFeatureProvider) -> tuple[str, str, str]:
    manifest = getattr(provider, "manifest", None)
    if manifest is None:
        raise ValueError("parent context provider manifest가 필요합니다.")
    manifest.validate()
    return (
        str(manifest.provider_id).strip(),
        str(manifest.provider_version).strip(),
        manifest.manifest_hash,
    )


@dataclass(frozen=True)
class ParentContextFrameBuild:
    """Immutable evidence bundle produced by one exact orchestration run."""

    registry: ParentFeatureRegistry
    frame: ParentContextFrame
    target_times: tuple[str, ...]
    target_timeline_hash: str
    provider_ids: tuple[str, ...]
    mode: str

    def validate(self) -> None:
        self.registry.validate()
        self.frame.validate()
        if self.frame.registry_hash != self.registry.registry_hash:
            raise ValueError("frame build registry_hash가 frame과 다릅니다.")
        normalized_times = tuple(_time_key(item) for item in self.target_times)
        frame_times = tuple(_time_key(point.target_time) for point in self.frame.points)
        if normalized_times != frame_times:
            raise ValueError("frame build target_times가 frame exact points와 다릅니다.")
        if not str(self.target_timeline_hash).strip():
            raise ValueError("frame build target_timeline_hash가 필요합니다.")
        if not self.provider_ids or any(not str(item).strip() for item in self.provider_ids):
            raise ValueError("frame build provider_ids가 필요합니다.")
        if len(set(self.provider_ids)) != len(self.provider_ids):
            raise ValueError("frame build provider_ids에 중복이 있습니다.")
        if str(self.mode).strip().upper() != str(self.frame.mode).strip().upper():
            raise ValueError("frame build mode가 frame mode와 다릅니다.")

    @property
    def build_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "schema": SCHEMA_VERSION,
                "policy": BUILD_POLICY,
                "registry_hash": self.registry.registry_hash,
                "frame_hash": self.frame.frame_hash,
                "target_times": self.target_times,
                "target_timeline_hash": self.target_timeline_hash,
                "provider_ids": self.provider_ids,
                "mode": str(self.mode).strip().upper(),
            }
        )

    def public_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": SCHEMA_VERSION,
            "policy": BUILD_POLICY,
            "registry_hash": self.registry.registry_hash,
            "frame_hash": self.frame.frame_hash,
            "target_symbol": self.frame.target_symbol,
            "target_times": self.target_times,
            "target_timeline_hash": self.target_timeline_hash,
            "provider_ids": self.provider_ids,
            "mode": str(self.mode).strip().upper(),
            "build_hash": self.build_hash,
        }


class RootParentContextFrameBuilder:
    """Precompute exact PCTX1/PCTX2B context from independent root providers.

    PCTX2C v1 intentionally passes ``dependencies=None`` to every provider.  A
    future Sector/Group tranche may introduce an explicit dependency DAG, but a
    child provider cannot be smuggled into this root-only builder because it is
    required to succeed without dependencies and to return its declared
    manifest at the exact requested timestamp.
    """

    @classmethod
    def build(
        cls,
        *,
        frame_id: str,
        target_market: Mapping[str, Any],
        providers: Sequence[ParentFeatureProvider],
        mode: str = "OBSERVED",
    ) -> ParentContextFrameBuild:
        frame_id = _text(frame_id, "parent context frame_id")
        target_symbol, timeframe, target_source, target_times, timeline_hash = _target_timeline(target_market)
        normalized_mode = str(mode).strip().upper()
        if normalized_mode not in {"OBSERVED", "DEPLOYMENT"}:
            raise ValueError("parent context orchestration mode는 OBSERVED 또는 DEPLOYMENT여야 합니다.")

        items = tuple(providers)
        if not items:
            raise ValueError("parent context root providers가 비어 있습니다.")
        ordered = tuple(sorted(items, key=_provider_identity))
        identities = tuple(_provider_identity(provider) for provider in ordered)
        provider_ids = tuple(item[0] for item in identities)
        if len(set((item[0], item[1]) for item in identities)) != len(identities):
            raise ValueError("parent context root provider/version에 중복이 있습니다.")

        registry = ParentFeatureRegistry(tuple(provider.manifest for provider in ordered))
        registry.validate()
        assemblies = []
        for target_time in target_times:
            results: list[ParentFeatureProviderResult] = []
            for provider in ordered:
                result = provider.build(
                    as_of=target_time,
                    knowledge_cutoff=target_time,
                    dependencies=None,
                )
                if not isinstance(result, ParentFeatureProviderResult):
                    raise ValueError("root provider는 ParentFeatureProviderResult를 반환해야 합니다.")
                result.validate()
                if result.manifest.manifest_hash != provider.manifest.manifest_hash:
                    raise ValueError("root provider result manifest가 provider 선언과 다릅니다.")
                if _time_key(result.as_of) != target_time:
                    raise ValueError("root provider result as_of가 exact target_time과 다릅니다.")
                if _time_key(result.knowledge_cutoff) != target_time:
                    raise ValueError("root provider result knowledge_cutoff가 exact target_time과 다릅니다.")
                if result.dependency_result_hashes:
                    raise ValueError("PCTX2C root provider result는 dependencies를 가질 수 없습니다.")
                results.append(result)

            assemblies.append(
                ParentContextAssembler.assemble(
                    as_of=target_time,
                    knowledge_cutoff=target_time,
                    results=tuple(results),
                    mode=normalized_mode,
                    metadata={
                        "orchestration_policy": BUILD_POLICY,
                        "target_symbol": target_symbol,
                        "target_timeframe": timeframe,
                        "target_source": target_source,
                        "target_timeline_hash": timeline_hash,
                    },
                )
            )

        frame = ParentContextFrame.create(
            frame_id=frame_id,
            target_symbol=target_symbol,
            registry=registry,
            assemblies=tuple(assemblies),
            mode=normalized_mode,
            metadata={
                "orchestration_policy": BUILD_POLICY,
                "target_timeframe": timeframe,
                "target_source": target_source,
                "target_timeline_hash": timeline_hash,
                "provider_ids": provider_ids,
            },
        )
        bundle = ParentContextFrameBuild(
            registry=registry,
            frame=frame,
            target_times=target_times,
            target_timeline_hash=timeline_hash,
            provider_ids=provider_ids,
            mode=normalized_mode,
        )
        bundle.validate()
        return bundle
