"""Research-only external dataset freezing for future LF studies.

LFREAL2 accepts caller-provided raw bytes and emits a deterministic immutable
manifest. It performs no file I/O, provider discovery, network access, tactic
replay, execution, selection, allocation, or deployment action.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "multi_symbol_follower_external_dataset/v1"
POLICY = "CALLER_BYTES_SHA256_IMMUTABLE_MANIFEST_RESEARCH_ONLY_NO_IO_NO_PROVIDER"
_BLOCKED_SOURCE_KINDS = {"SYNTHETIC", "FIXTURE", "GENERATED", "MOCK", "TEST"}


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _time_key(value: Any, label: str) -> str:
    text = _text(value, label)
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 14:
        raise ValueError(f"{label}은 YYYYMMDDHHMMSS 이상이어야 합니다.")
    return digits[:14]


@dataclass(frozen=True)
class ExternalDatasetDeclaration:
    source_id: str
    source_kind: str
    media_format: str
    timeframe: str
    symbols: Sequence[str]
    first_observation: str
    last_observation: str
    record_count: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _text(self.source_id, "LFREAL2 source_id")
        kind = _text(self.source_kind, "LFREAL2 source_kind").upper()
        if kind in _BLOCKED_SOURCE_KINDS:
            raise ValueError(f"LFREAL2 source_kind {kind}는 실제 연구 데이터 선언으로 허용되지 않습니다.")
        _text(self.media_format, "LFREAL2 media_format")
        _text(self.timeframe, "LFREAL2 timeframe")
        symbols = tuple(str(item or "").strip() for item in self.symbols)
        if not symbols or any(not item for item in symbols):
            raise ValueError("LFREAL2 symbols는 비어 있지 않은 심볼을 최소 1개 요구합니다.")
        if len(set(symbols)) != len(symbols):
            raise ValueError("LFREAL2 symbols에 중복이 있습니다.")
        first = _time_key(self.first_observation, "LFREAL2 first_observation")
        last = _time_key(self.last_observation, "LFREAL2 last_observation")
        if last < first:
            raise ValueError("LFREAL2 last_observation은 first_observation보다 빠를 수 없습니다.")
        if isinstance(self.record_count, bool) or not isinstance(self.record_count, int) or self.record_count < 1:
            raise ValueError("LFREAL2 record_count는 1 이상의 int여야 합니다.")
        dict(self.metadata)


class ExternalDatasetFreezer:
    @classmethod
    def freeze(
        cls,
        *,
        raw_bytes: bytes,
        declaration: ExternalDatasetDeclaration,
        expected_sha256: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise ValueError("LFREAL2 raw_bytes는 bytes여야 합니다.")
        frozen_bytes = bytes(raw_bytes)
        if not frozen_bytes:
            raise ValueError("LFREAL2 raw_bytes가 비어 있습니다.")
        declaration.validate()
        content_sha256 = hashlib.sha256(frozen_bytes).hexdigest()
        if expected_sha256 is not None:
            expected = _text(expected_sha256, "LFREAL2 expected_sha256").lower()
            if expected != content_sha256:
                raise ValueError("LFREAL2 expected_sha256이 실제 content hash와 다릅니다.")

        symbols = tuple(sorted(str(item).strip() for item in declaration.symbols))
        payload = {
            "schema": SCHEMA_VERSION,
            "freeze_policy": POLICY,
            "mode": "RESEARCH_DATASET_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "deployment_authority": False,
            "provider_authority": False,
            "file_io_authority": False,
            "content_hash_verified": True,
            "market_data_authenticity_verified": False,
            "real_data_claim": False,
            "source_id": str(declaration.source_id).strip(),
            "source_kind": str(declaration.source_kind).strip().upper(),
            "media_format": str(declaration.media_format).strip().upper(),
            "timeframe": str(declaration.timeframe).strip(),
            "symbols": symbols,
            "first_observation": _time_key(declaration.first_observation, "LFREAL2 first_observation"),
            "last_observation": _time_key(declaration.last_observation, "LFREAL2 last_observation"),
            "record_count": int(declaration.record_count),
            "byte_count": len(frozen_bytes),
            "content_sha256": content_sha256,
            "metadata": dict(declaration.metadata),
        }
        payload["dataset_manifest_hash"] = _stable_hash(payload)
        return payload
