from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping


CACHE_MANIFEST_SCHEMA = "dsl_market_data_cache/v1"
_DATASET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class CacheContractError(ValueError):
    """Raised when an external market-data cache contract is malformed."""


def _require_nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CacheContractError(f"{field} must be a non-empty string")
    return value.strip()


def _require_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CacheContractError(f"{field} must be a non-negative integer")
    return value


def _validate_dataset_id(value: Any) -> str:
    dataset_id = _require_nonempty_text(value, "dataset_id")
    if not _DATASET_ID_RE.fullmatch(dataset_id):
        raise CacheContractError("dataset_id contains unsupported characters")
    return dataset_id


def _validate_relative_root(value: Any) -> str:
    root = _require_nonempty_text(value, "cache.root")
    path = PurePosixPath(root)
    if path.is_absolute() or ".." in path.parts:
        raise CacheContractError("cache.root must be a safe relative path")
    return path.as_posix()


@dataclass(frozen=True)
class SourceDatasetStatus:
    """Feature-blind dataset status returned by the market-data owner boundary."""

    dataset_id: str
    row_count: int
    instrument_count: int
    earliest: str | None
    latest: str | None
    revision: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SourceDatasetStatus":
        if not isinstance(raw, Mapping):
            raise CacheContractError("source status must be an object")
        dataset_id = _validate_dataset_id(raw.get("dataset_id"))
        row_count = _require_nonnegative_int(raw.get("row_count"), "row_count")
        instrument_count = _require_nonnegative_int(raw.get("instrument_count"), "instrument_count")
        earliest = raw.get("earliest")
        latest = raw.get("latest")
        if earliest is not None:
            earliest = _require_nonempty_text(earliest, "earliest")
        if latest is not None:
            latest = _require_nonempty_text(latest, "latest")
        revision = _require_nonempty_text(raw.get("revision"), "revision")
        return cls(
            dataset_id=dataset_id,
            row_count=row_count,
            instrument_count=instrument_count,
            earliest=earliest,
            latest=latest,
            revision=revision,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "row_count": self.row_count,
            "instrument_count": self.instrument_count,
            "earliest": self.earliest,
            "latest": self.latest,
            "revision": self.revision,
        }


def source_fingerprint(status: SourceDatasetStatus) -> str:
    payload = json.dumps(
        status.public_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class CacheDatasetManifest:
    """Manifest for rebuildable local Parquet derived from an external data SSOT."""

    dataset_id: str
    cache_root: str
    partition_by: tuple[str, ...]
    source: SourceDatasetStatus
    source_fingerprint: str
    generated_at_utc: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CacheDatasetManifest":
        if not isinstance(raw, Mapping):
            raise CacheContractError("cache manifest must be an object")
        if raw.get("schema") != CACHE_MANIFEST_SCHEMA:
            raise CacheContractError(f"schema must be {CACHE_MANIFEST_SCHEMA}")
        dataset_id = _validate_dataset_id(raw.get("dataset_id"))

        cache = raw.get("cache")
        if not isinstance(cache, Mapping):
            raise CacheContractError("cache must be an object")
        if cache.get("format") != "parquet":
            raise CacheContractError("cache.format must be parquet")
        cache_root = _validate_relative_root(cache.get("root"))
        partition_by_raw = cache.get("partition_by")
        if not isinstance(partition_by_raw, list) or not partition_by_raw:
            raise CacheContractError("cache.partition_by must be a non-empty array")
        partition_by = tuple(_require_nonempty_text(item, "cache.partition_by[]") for item in partition_by_raw)
        if len(set(partition_by)) != len(partition_by):
            raise CacheContractError("cache.partition_by must not contain duplicates")

        source_raw = raw.get("source")
        source = SourceDatasetStatus.from_mapping(source_raw) if isinstance(source_raw, Mapping) else None
        if source is None:
            raise CacheContractError("source must be an object")
        if source.dataset_id != dataset_id:
            raise CacheContractError("source.dataset_id must match dataset_id")

        fingerprint = _require_nonempty_text(raw.get("source_fingerprint"), "source_fingerprint")
        if fingerprint != source_fingerprint(source):
            raise CacheContractError("source_fingerprint does not match source status")

        generated_at_utc = _require_nonempty_text(raw.get("generated_at_utc"), "generated_at_utc")
        return cls(
            dataset_id=dataset_id,
            cache_root=cache_root,
            partition_by=partition_by,
            source=source,
            source_fingerprint=fingerprint,
            generated_at_utc=generated_at_utc,
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": CACHE_MANIFEST_SCHEMA,
            "dataset_id": self.dataset_id,
            "cache": {
                "format": "parquet",
                "root": self.cache_root,
                "partition_by": list(self.partition_by),
            },
            "source": self.source.public_dict(),
            "source_fingerprint": self.source_fingerprint,
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass(frozen=True)
class CacheAssessment:
    dataset_id: str
    ready: bool
    reasons: tuple[str, ...]


def assess_cache(manifest: CacheDatasetManifest, current: SourceDatasetStatus) -> CacheAssessment:
    """Fail closed when the materialized cache no longer matches source status."""

    reasons: list[str] = []
    if manifest.dataset_id != current.dataset_id:
        reasons.append("DATASET_ID_MISMATCH")
    if manifest.source_fingerprint != source_fingerprint(current):
        reasons.append("SOURCE_FINGERPRINT_CHANGED")
    return CacheAssessment(
        dataset_id=current.dataset_id,
        ready=not reasons,
        reasons=tuple(reasons),
    )
