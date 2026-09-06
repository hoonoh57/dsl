from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping, Sequence

from .cache_contract import CacheContractError, SourceDatasetStatus, source_fingerprint


_DATASETS = {
    "daily": "korean-equity-daily",
    "minute": "korean-equity-minute-1m",
}


class MarketDataFactoryPortError(RuntimeError):
    pass


@dataclass(frozen=True)
class CacheSyncResult:
    dataset_id: str
    source_fingerprint: str
    partitions: int
    materialized: int
    reused: int


def _event_from_output(stdout: str, stderr: str) -> Mapping[str, Any]:
    events: list[Mapping[str, Any]] = []
    for line in [*stdout.splitlines(), *stderr.splitlines()]:
        if not line.startswith("CACHE_EVENT "):
            continue
        try:
            payload = json.loads(line[len("CACHE_EVENT ") :])
        except json.JSONDecodeError as exc:
            raise MarketDataFactoryPortError("market-data factory returned malformed CACHE_EVENT") from exc
        if isinstance(payload, Mapping):
            events.append(payload)
    if not events:
        raise MarketDataFactoryPortError("market-data factory returned no CACHE_EVENT")
    return events[-1]


class MarketDataFactoryPort:
    """Process boundary to the external market-data owner. No DB access is owned here."""

    def __init__(
        self,
        factory_root: str | Path,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        npm_command: str | None = None,
    ) -> None:
        self._root = Path(factory_root).resolve()
        self._runner = runner
        self._npm = npm_command or ("npm.cmd" if os.name == "nt" else "npm")

    def _invoke(self, command: str, dataset: str, target: str | Path | None = None) -> Mapping[str, Any]:
        expected_id = _DATASETS.get(dataset)
        if expected_id is None:
            raise MarketDataFactoryPortError("dataset must be daily or minute")
        package_json = self._root / "package.json"
        if not package_json.is_file():
            raise MarketDataFactoryPortError("market-data factory root is invalid")

        args: list[str] = [
            self._npm,
            "run",
            "data:cache",
            "--",
            "--command",
            command,
            "--dataset",
            dataset,
        ]
        if target is not None:
            args.extend(["--target", str(Path(target).resolve())])

        completed = self._runner(
            args,
            cwd=str(self._root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
            check=False,
        )
        event = _event_from_output(completed.stdout or "", completed.stderr or "")
        if completed.returncode != 0 or event.get("event") == "error":
            raise MarketDataFactoryPortError(str(event.get("message") or f"market-data factory exited {completed.returncode}"))
        if event.get("dataset_id") != expected_id:
            raise MarketDataFactoryPortError("market-data factory dataset identity mismatch")
        return event

    def status(self, dataset: str) -> SourceDatasetStatus:
        event = self._invoke("status", dataset)
        if event.get("event") != "status" or not isinstance(event.get("source"), Mapping):
            raise MarketDataFactoryPortError("market-data factory status contract mismatch")
        try:
            status = SourceDatasetStatus.from_mapping(event["source"])
        except CacheContractError as exc:
            raise MarketDataFactoryPortError("market-data factory source status is invalid") from exc
        if event.get("source_fingerprint") != source_fingerprint(status):
            raise MarketDataFactoryPortError("market-data factory source fingerprint mismatch")
        return status

    def sync(self, dataset: str, target: str | Path) -> CacheSyncResult:
        event = self._invoke("sync", dataset, target)
        if event.get("event") != "complete":
            raise MarketDataFactoryPortError("market-data factory sync contract mismatch")
        try:
            partitions = int(event["partitions"])
            materialized = int(event["materialized"])
            reused = int(event["reused"])
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataFactoryPortError("market-data factory sync counters are invalid") from exc
        if min(partitions, materialized, reused) < 0 or materialized + reused != partitions:
            raise MarketDataFactoryPortError("market-data factory sync counters are inconsistent")
        fingerprint = event.get("source_fingerprint")
        if not isinstance(fingerprint, str) or not fingerprint:
            raise MarketDataFactoryPortError("market-data factory sync fingerprint is invalid")
        return CacheSyncResult(
            dataset_id=str(event["dataset_id"]),
            source_fingerprint=fingerprint,
            partitions=partitions,
            materialized=materialized,
            reused=reused,
        )

    def statuses(self, datasets: Sequence[str] = ("daily", "minute")) -> tuple[SourceDatasetStatus, ...]:
        return tuple(self.status(dataset) for dataset in datasets)
