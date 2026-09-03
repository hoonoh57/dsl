"""Admit pinned REALDATA1 CSV rows through the existing LFREAL3 producer.

This is an edge adapter. It owns explicit local file I/O and source-specific CSV
shape only. Dataset identity remains owned by the existing LFREAL2 freezer, and
row validation / causal research authority remains owned by ``CausalRowProducer``.
No provider/network access, DSL parsing, strategy logic, order authority, or
future-facing source columns are admitted here.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import io
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.multi_symbol_follower_causal_rows import (  # noqa: E402
    CausalMarketRow,
    CausalRowProducer,
)
from tools.freeze_realdata1_dataset import freeze_realdata1_bytes  # noqa: E402

CAUSAL_COLUMNS = ("date", "open", "high", "low", "close", "volume")
EXCLUDED_FUTURE_COLUMNS = ("return", "next_close", "direction")


def _json_identity(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def validate_manifest_identity(*, raw_bytes: bytes, manifest: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, Mapping):
        raise ValueError("REALDATA1 manifest must be a mapping.")
    canonical = freeze_realdata1_bytes(raw_bytes)
    if _json_identity(dict(manifest)) != _json_identity(canonical):
        raise ValueError("REALDATA1 manifest does not match the LFREAL2 identity frozen from these exact source bytes.")
    return canonical


def _daily_time_key(value: str, *, row_number: int) -> str:
    text = str(value or "").strip()
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"REALDATA1 row {row_number} date must be YYYY-MM-DD.") from exc
    if parsed.strftime("%Y-%m-%d") != text:
        raise ValueError(f"REALDATA1 row {row_number} date must be canonical YYYY-MM-DD.")
    return parsed.strftime("%Y%m%d000000")


def _number(value: str, *, column: str, row_number: int) -> float:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"REALDATA1 row {row_number} {column} is required.")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"REALDATA1 row {row_number} {column} must be numeric.") from exc


def parse_causal_rows(*, raw_bytes: bytes, symbol: str) -> tuple[CausalMarketRow, ...]:
    if not isinstance(raw_bytes, (bytes, bytearray)) or not raw_bytes:
        raise ValueError("REALDATA1 CSV payload must be non-empty bytes.")
    symbol_text = str(symbol or "").strip()
    if not symbol_text:
        raise ValueError("REALDATA1 symbol is required.")

    try:
        text = bytes(raw_bytes).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("REALDATA1 CSV must decode as UTF-8/UTF-8-BOM.") from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    fieldnames = tuple(reader.fieldnames or ())
    if not fieldnames:
        raise ValueError("REALDATA1 CSV header is required.")
    if len(set(fieldnames)) != len(fieldnames):
        raise ValueError("REALDATA1 CSV header contains duplicate columns.")
    missing = [name for name in CAUSAL_COLUMNS if name not in fieldnames]
    if missing:
        raise ValueError(f"REALDATA1 CSV missing causal columns: {','.join(missing)}")

    rows: list[CausalMarketRow] = []
    for row_number, source in enumerate(reader, start=2):
        if None in source:
            raise ValueError(f"REALDATA1 row {row_number} contains unexpected extra fields.")
        rows.append(
            CausalMarketRow(
                symbol=symbol_text,
                time=_daily_time_key(source.get("date", ""), row_number=row_number),
                open=_number(source.get("open", ""), column="open", row_number=row_number),
                high=_number(source.get("high", ""), column="high", row_number=row_number),
                low=_number(source.get("low", ""), column="low", row_number=row_number),
                close=_number(source.get("close", ""), column="close", row_number=row_number),
                volume=_number(source.get("volume", ""), column="volume", row_number=row_number),
            )
        )
    if not rows:
        raise ValueError("REALDATA1 CSV contains no data rows.")
    return tuple(rows)


def admit_realdata1_bytes(*, raw_bytes: bytes, manifest: Mapping[str, Any]) -> dict[str, Any]:
    canonical_manifest = validate_manifest_identity(raw_bytes=raw_bytes, manifest=manifest)
    symbols: Sequence[str] = tuple(canonical_manifest.get("symbols") or ())
    if len(symbols) != 1:
        raise ValueError("REALDATA1 manifest must declare exactly one symbol.")
    rows = parse_causal_rows(raw_bytes=raw_bytes, symbol=str(symbols[0]))
    return CausalRowProducer.admit(manifest=canonical_manifest, rows=rows)


def admit_source_file(*, source_path: Path, manifest_path: Path, row_bundle_path: Path) -> dict[str, Any]:
    if not source_path.is_file():
        raise FileNotFoundError(f"REALDATA1 source file not found: {source_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"REALDATA1 manifest file not found: {manifest_path}")
    if not row_bundle_path.parent.is_dir():
        raise FileNotFoundError(f"REALDATA1 row-bundle parent directory not found: {row_bundle_path.parent}")

    raw_bytes = source_path.read_bytes()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("REALDATA1 manifest must be valid UTF-8 JSON.") from exc

    bundle = admit_realdata1_bytes(raw_bytes=raw_bytes, manifest=manifest)
    text = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    row_bundle_path.write_text(text, encoding="utf-8", newline="\n")
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse only causal REALDATA1 OHLCV columns and admit them through existing LFREAL3."
    )
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--row-bundle-path", type=Path, required=True)
    args = parser.parse_args()

    bundle = admit_source_file(
        source_path=args.source_path,
        manifest_path=args.manifest_path,
        row_bundle_path=args.row_bundle_path,
    )
    print(
        "[PASS] REALDATA1 LFREAL3 causal rows admitted; "
        f"rows={bundle['record_count']}; "
        f"first={bundle['first_observation']}; "
        f"last={bundle['last_observation']}; "
        f"row_bundle_hash={bundle['row_bundle_hash']}; "
        f"path={args.row_bundle_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
