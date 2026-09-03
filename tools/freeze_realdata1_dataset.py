"""Freeze pinned REALDATA1 caller bytes through the existing LFREAL2 freezer.

This is an edge tool. It owns only explicit local file input/output needed by an
operator workflow. Dataset identity, validation, authority flags, and manifest
hashing remain owned by ``ExternalDatasetFreezer``. No provider/network access or
market-row parsing is performed here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.multi_symbol_follower_external_dataset import (  # noqa: E402
    ExternalDatasetDeclaration,
    ExternalDatasetFreezer,
)

SOURCE_REPOSITORY = "hyekong/sk-hynix-news-dataset"
SOURCE_COMMIT = "339f0b6dc15531f374c51f715f12555153054009"
SOURCE_FILE = "sk_hynix_price.csv"
SOURCE_GIT_BLOB_SHA1 = "84fb250326def7148cce6466026aaecf057e2013"
EXPECTED_BYTE_COUNT = 57541
EXPECTED_CONTENT_SHA256 = "fffbeaece7a769e063c3803ad184265aa751d9f417e3e72e2862045cad10f5ba"


def build_declaration() -> ExternalDatasetDeclaration:
    return ExternalDatasetDeclaration(
        source_id=f"github:{SOURCE_REPOSITORY}@{SOURCE_COMMIT}:{SOURCE_FILE}",
        source_kind="EXTERNAL_HISTORICAL",
        media_format="CSV",
        timeframe="1d",
        symbols=("000660.KS",),
        first_observation="20240415000000",
        last_observation="20260413000000",
        record_count=483,
        metadata={
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": SOURCE_COMMIT,
            "source_file": SOURCE_FILE,
            "source_git_blob_sha1": SOURCE_GIT_BLOB_SHA1,
            "provider_path_stated_by_source": "yfinance -> Yahoo Finance",
        },
    )


def freeze_realdata1_bytes(raw_bytes: bytes) -> dict[str, Any]:
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise ValueError("REALDATA1 caller payload must be bytes.")
    frozen = bytes(raw_bytes)
    if len(frozen) != EXPECTED_BYTE_COUNT:
        raise ValueError(
            f"REALDATA1 byte count mismatch. expected={EXPECTED_BYTE_COUNT} actual={len(frozen)}"
        )
    return ExternalDatasetFreezer.freeze(
        raw_bytes=frozen,
        declaration=build_declaration(),
        expected_sha256=EXPECTED_CONTENT_SHA256,
    )


def freeze_source_file(*, source_path: Path, manifest_path: Path) -> dict[str, Any]:
    if not source_path.is_file():
        raise FileNotFoundError(f"REALDATA1 source file not found: {source_path}")
    if not manifest_path.parent.is_dir():
        raise FileNotFoundError(f"REALDATA1 manifest parent directory not found: {manifest_path.parent}")

    raw_bytes = source_path.read_bytes()
    manifest = freeze_realdata1_bytes(raw_bytes)
    text = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    manifest_path.write_text(text, encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Freeze pinned REALDATA1 exact bytes through LFREAL2 without adding Core file/provider authority."
    )
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    args = parser.parse_args()

    manifest = freeze_source_file(source_path=args.source_path, manifest_path=args.manifest_path)
    print(
        "[PASS] REALDATA1 LFREAL2 manifest frozen; "
        f"bytes={manifest['byte_count']}; "
        f"sha256={manifest['content_sha256']}; "
        f"manifest_hash={manifest['dataset_manifest_hash']}; "
        f"path={args.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
