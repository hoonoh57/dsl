"""Derive a causal-only REALDATA1 dataset while quarantining known invalid rows.

This edge tool preserves the original pinned source and LFREAL2 manifest. It
projects only date/open/high/low/close/volume, delegates OHLCV validity to the
existing CausalMarketRow.normalized() contract, quarantines only the explicitly
known invalid observation, freezes the derived bytes through ExternalDatasetFreezer,
and admits the result through CausalRowProducer. Core semantics are unchanged.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.multi_symbol_follower_causal_rows import CausalRowProducer  # noqa: E402
from core.multi_symbol_follower_external_dataset import (  # noqa: E402
    ExternalDatasetDeclaration,
    ExternalDatasetFreezer,
)
from tools.admit_realdata1_causal_rows import (  # noqa: E402
    CAUSAL_COLUMNS,
    EXCLUDED_FUTURE_COLUMNS,
    parse_causal_rows,
)
from tools.freeze_realdata1_dataset import freeze_realdata1_bytes  # noqa: E402

EXPECTED_PARENT_MANIFEST_HASH = "8b06c3a4871666771343df7eee074abc176fd2cf68fce3768848f2342c57f982"
EXPECTED_QUARANTINED_TIMES = ("20241014000000",)
DERIVATION_POLICY = "CAUSAL_COLUMNS_ONLY_QUARANTINE_LFREAL3_INVALID_ROWS_V1"
SYMBOL = "000660.KS"


def derive_causal_projection(*, raw_bytes: bytes, symbol: str) -> tuple[bytes, tuple[Any, ...], tuple[dict[str, Any], ...]]:
    rows = parse_causal_rows(raw_bytes=raw_bytes, symbol=symbol)
    text = bytes(raw_bytes).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    source_rows = tuple(reader)
    if len(source_rows) != len(rows):
        raise ValueError("REALDATA1 source row count changed during causal projection.")

    kept_source_rows: list[dict[str, str]] = []
    kept_rows: list[Any] = []
    quarantined: list[dict[str, Any]] = []

    for row_number, (source, row) in enumerate(zip(source_rows, rows), start=2):
        try:
            row.normalized()
        except ValueError as exc:
            quarantined.append(
                {
                    "row_number": row_number,
                    "date": str(source.get("date") or "").strip(),
                    "time": row.time,
                    "reason": str(exc),
                    "open": str(source.get("open") or "").strip(),
                    "high": str(source.get("high") or "").strip(),
                    "low": str(source.get("low") or "").strip(),
                    "close": str(source.get("close") or "").strip(),
                    "volume": str(source.get("volume") or "").strip(),
                }
            )
            continue
        kept_source_rows.append({name: str(source.get(name) or "").strip() for name in CAUSAL_COLUMNS})
        kept_rows.append(row)

    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(CAUSAL_COLUMNS)
    for source in kept_source_rows:
        writer.writerow([source[name] for name in CAUSAL_COLUMNS])
    derived_bytes = output.getvalue().encode("utf-8")

    return derived_bytes, tuple(kept_rows), tuple(quarantined)


def derive_realdata1_bytes(raw_bytes: bytes) -> tuple[bytes, dict[str, Any], dict[str, Any], tuple[dict[str, Any], ...]]:
    parent_manifest = freeze_realdata1_bytes(raw_bytes)
    if parent_manifest["dataset_manifest_hash"] != EXPECTED_PARENT_MANIFEST_HASH:
        raise ValueError("REALDATA1 parent LFREAL2 manifest hash does not match the trusted checkpoint.")

    derived_bytes, rows, quarantined = derive_causal_projection(raw_bytes=raw_bytes, symbol=SYMBOL)
    quarantined_times = tuple(item["time"] for item in quarantined)
    if quarantined_times != EXPECTED_QUARANTINED_TIMES:
        raise ValueError(
            "REALDATA1 quarantine set changed. "
            f"expected={EXPECTED_QUARANTINED_TIMES} actual={quarantined_times}"
        )
    if not rows:
        raise ValueError("REALDATA1 causal derivation produced no admitted rows.")

    declaration = ExternalDatasetDeclaration(
        source_id=f"derived:realdata1:{DERIVATION_POLICY.lower()}:{EXPECTED_PARENT_MANIFEST_HASH}",
        source_kind="DERIVED_EXTERNAL_HISTORICAL",
        media_format="CSV",
        timeframe=str(parent_manifest["timeframe"]),
        symbols=tuple(parent_manifest["symbols"]),
        first_observation=rows[0].time,
        last_observation=rows[-1].time,
        record_count=len(rows),
        metadata={
            "derivation_policy": DERIVATION_POLICY,
            "parent_dataset_manifest_hash": EXPECTED_PARENT_MANIFEST_HASH,
            "parent_content_sha256": str(parent_manifest["content_sha256"]),
            "causal_columns": CAUSAL_COLUMNS,
            "excluded_future_columns": EXCLUDED_FUTURE_COLUMNS,
            "quarantined_row_count": len(quarantined),
            "quarantined_rows": quarantined,
            "source_values_corrected": False,
        },
    )
    manifest = ExternalDatasetFreezer.freeze(raw_bytes=derived_bytes, declaration=declaration)
    bundle = CausalRowProducer.admit(manifest=manifest, rows=rows)
    return derived_bytes, manifest, bundle, quarantined


def derive_source_file(
    *,
    source_path: Path,
    causal_path: Path,
    manifest_path: Path,
    row_bundle_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], tuple[dict[str, Any], ...]]:
    if not source_path.is_file():
        raise FileNotFoundError(f"REALDATA1 source file not found: {source_path}")
    for output_path in (causal_path, manifest_path, row_bundle_path):
        if not output_path.parent.is_dir():
            raise FileNotFoundError(f"REALDATA1 output parent directory not found: {output_path.parent}")

    derived_bytes, manifest, bundle, quarantined = derive_realdata1_bytes(source_path.read_bytes())
    causal_path.write_bytes(derived_bytes)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    row_bundle_path.write_text(
        json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest, bundle, quarantined


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive causal-only REALDATA1 bytes, quarantine the known invalid candle, freeze LFREAL2 identity, and admit LFREAL3 rows."
    )
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--causal-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--row-bundle-path", type=Path, required=True)
    args = parser.parse_args()

    manifest, bundle, quarantined = derive_source_file(
        source_path=args.source_path,
        causal_path=args.causal_path,
        manifest_path=args.manifest_path,
        row_bundle_path=args.row_bundle_path,
    )
    print(
        "[PASS] REALDATA1 causal dataset derived and admitted; "
        f"rows={bundle['record_count']}; "
        f"quarantined={len(quarantined)}; "
        f"derived_bytes={manifest['byte_count']}; "
        f"derived_sha256={manifest['content_sha256']}; "
        f"manifest_hash={manifest['dataset_manifest_hash']}; "
        f"row_bundle_hash={bundle['row_bundle_hash']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
