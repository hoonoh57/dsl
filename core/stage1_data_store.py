"""Immutable canonical market-data snapshots for Stage 1 experiments."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from core.db import HISTORY_DIR

DATA_DIR = HISTORY_DIR / "stage1_data"
_REQUIRED = ("time", "open", "high", "low", "close", "volume")


def _path(data_hash: str) -> Path:
    value = str(data_hash or "").strip().lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("data_hash는 SHA-256 hex여야 합니다.")
    return DATA_DIR / f"{value}.json"


def _canonical_rows(market: Dict[str, Any]) -> list[tuple]:
    missing = [key for key in _REQUIRED if key not in market]
    if missing:
        raise ValueError(f"market snapshot 필드 누락: {', '.join(missing)}")
    lengths = {key: len(market[key]) for key in _REQUIRED}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"market snapshot 길이가 일치하지 않습니다: {lengths}")
    rows = []
    for i in range(lengths["time"]):
        rows.append((
            str(market["time"][i]),
            float(market["open"][i]),
            float(market["high"][i]),
            float(market["low"][i]),
            float(market["close"][i]),
            float(market["volume"][i]),
        ))
    return rows


def _rows_hash(rows: list[tuple]) -> str:
    encoded = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _payload_from_rows(rows: list[tuple], meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "time": [row[0] for row in rows],
        "open": [row[1] for row in rows],
        "high": [row[2] for row in rows],
        "low": [row[3] for row in rows],
        "close": [row[4] for row in rows],
        "volume": [row[5] for row in rows],
        "_meta": dict(meta),
    }


def save_market_snapshot(market: Dict[str, Any]) -> str:
    """Persist one immutable content-addressed OHLCV snapshot.

    ``data_hash`` is the identity of the canonical time/OHLCV rows only.  The
    instrument/source/partition metadata is contextual provenance and may
    legitimately differ for the same row payload (for example, the same
    deterministic fixture reused by independent Stage 1 roots).  Existing
    snapshots therefore compare canonical rows, not the contextual ``_meta``.
    Experiment provenance remains the authoritative context for a snapshot.
    """
    meta = dict(market.get("_meta") or {})
    data_hash = str(meta.get("data_hash") or "").strip().lower()
    target = _path(data_hash)
    rows = _canonical_rows(market)
    computed_hash = _rows_hash(rows)
    if computed_hash != data_hash:
        raise ValueError("market payload와 data_hash가 일치하지 않습니다.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = _payload_from_rows(rows, meta)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if _canonical_rows(existing) != rows:
            raise ValueError("동일 data_hash에 다른 market payload가 존재합니다.")
        return data_hash
    target.write_text(encoded, encoding="utf-8")
    return data_hash


def load_market_snapshot(data_hash: str) -> Dict[str, Any]:
    target = _path(data_hash)
    if not target.is_file():
        raise FileNotFoundError(f"market snapshot이 없습니다: {data_hash}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    rows = _canonical_rows(payload)
    if _rows_hash(rows) != str(data_hash).strip().lower():
        raise ValueError("저장된 market snapshot의 data_hash가 payload와 일치하지 않습니다.")
    return payload


def has_market_snapshot(data_hash: str) -> bool:
    try:
        return _path(data_hash).is_file()
    except ValueError:
        return False
