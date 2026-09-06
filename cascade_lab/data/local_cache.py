from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .cache_contract import (
    CacheAssessment,
    CacheContractError,
    CacheDatasetManifest,
    SourceDatasetStatus,
    assess_cache,
)


def _safe_relative_file(value: Any, cache_root: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CacheContractError("partition.file must be a non-empty string")
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts:
        raise CacheContractError("partition.file must be a safe relative path")
    root = PurePosixPath(cache_root)
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise CacheContractError("partition.file must live under cache.root") from exc
    return path.as_posix()


def manifest_partition_files(raw: Mapping[str, Any], manifest: CacheDatasetManifest) -> tuple[str, ...]:
    partitions = raw.get("partitions")
    if not isinstance(partitions, Mapping):
        raise CacheContractError("partitions must be an object")
    if manifest.source.row_count > 0 and not partitions:
        raise CacheContractError("non-empty source requires cache partitions")

    files: list[str] = []
    row_total = 0
    for partition_id, item in partitions.items():
        if not isinstance(partition_id, str) or not partition_id.strip():
            raise CacheContractError("partition id must be a non-empty string")
        if not isinstance(item, Mapping):
            raise CacheContractError("partition entry must be an object")
        row_count = item.get("row_count")
        if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count < 0:
            raise CacheContractError("partition.row_count must be a non-negative integer")
        revision = item.get("revision")
        if not isinstance(revision, str) or not revision.strip():
            raise CacheContractError("partition.revision must be a non-empty string")
        files.append(_safe_relative_file(item.get("file"), manifest.cache_root))
        row_total += row_count

    if row_total != manifest.source.row_count:
        raise CacheContractError("partition row total must match source row_count")
    if len(set(files)) != len(files):
        raise CacheContractError("partition files must be unique")
    return tuple(files)


def assess_local_cache(data_root: str | Path, current: SourceDatasetStatus) -> CacheAssessment:
    root = Path(data_root)
    manifest_path = root / "manifest" / f"{current.dataset_id}.json"
    if not manifest_path.is_file():
        return CacheAssessment(current.dataset_id, False, ("MANIFEST_MISSING",))

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = CacheDatasetManifest.from_mapping(raw)
        base = assess_cache(manifest, current)
        if not base.ready:
            return base
        files = manifest_partition_files(raw, manifest)
    except (OSError, json.JSONDecodeError, CacheContractError, TypeError, ValueError):
        return CacheAssessment(current.dataset_id, False, ("MANIFEST_INVALID",))

    missing = [relative for relative in files if not (root / Path(*PurePosixPath(relative).parts)).is_file()]
    if missing:
        return CacheAssessment(current.dataset_id, False, ("PARTITION_FILE_MISSING",))
    return CacheAssessment(current.dataset_id, True, ())
