from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cascade_lab.data.local_cache import assess_local_cache
from cascade_lab.data.market_data_factory_port import MarketDataFactoryPort, MarketDataFactoryPortError


DATASET_CHOICES = ("daily", "minute")


def _datasets(value: str) -> tuple[str, ...]:
    if value == "all":
        return DATASET_CHOICES
    return (value,)


def _factory_root(explicit: str | None) -> Path:
    value = explicit or os.environ.get("MARKET_DATA_FACTORY_ROOT")
    if not value:
        raise MarketDataFactoryPortError("MARKET_DATA_FACTORY_ROOT or --factory-root is required")
    return Path(value).resolve()


def verify(port: MarketDataFactoryPort, data_root: Path, datasets: tuple[str, ...]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for dataset in datasets:
        status = port.status(dataset)
        assessment = assess_local_cache(data_root, status)
        if not assessment.ready:
            failures.append(f"{assessment.dataset_id}: {','.join(assessment.reasons)}")
    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify or synchronize rebuildable local market-data Parquet cache.")
    parser.add_argument("--command", choices=("verify", "sync"), default="verify")
    parser.add_argument("--dataset", choices=("all", *DATASET_CHOICES), default="all")
    parser.add_argument("--factory-root")
    parser.add_argument("--data-root", default=str(ROOT / "DATA"))
    args = parser.parse_args()

    datasets = _datasets(args.dataset)
    data_root = Path(args.data_root).resolve()

    try:
        port = MarketDataFactoryPort(_factory_root(args.factory_root))
        materialized = 0
        reused = 0
        if args.command == "sync":
            for dataset in datasets:
                result = port.sync(dataset, data_root)
                materialized += result.materialized
                reused += result.reused

        ready, failures = verify(port, data_root, datasets)
        if not ready:
            print(f"[ERROR] market data cache verification failed ({len(failures)}).")
            for failure in failures:
                print(f"[FAIL] {failure}")
            return 1

        if args.command == "sync":
            print(
                f"[PASS] market data cache synchronized ({len(datasets)} datasets, "
                f"materialized={materialized}, reused={reused})."
            )
        else:
            print(f"[PASS] market data cache ready ({len(datasets)} datasets).")
        return 0
    except (MarketDataFactoryPortError, OSError, ValueError) as exc:
        print("[ERROR] market data cache command failed (1).")
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
