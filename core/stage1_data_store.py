"""Immutable canonical market-data snapshots for Stage 1 experiments."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

from core.db import HISTORY_DIR

DATA_DIR = HISTORY_DIR / "stage1_data"


def _path(data_hash: str) -> Path:
    value = str(data_hash or "").strip().lower()
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("data_hash는 SHA-256 hex여야 합니다.")
    return DATA_DIR / f"{value}.json"


def save_market_snapshot(market: Dict[str, Any]) -> str:
    meta = dict(market.get("_meta") or {})
    data_hash = str(meta.get("data_hash") or "")
    target = _path(data_hash)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {key: market[key] for key in ("time", "open", "high", "low", "close", "volume")}
    payload["_meta"] = meta
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if existing != encoded:
            raise ValueError("동일 data_hash에 다른 market payload가 존재합니다.")
        return data_hash
    target.write_text(encoded, encoding="utf-8")
    return data_hash


def load_market_snapshot(data_hash: str) -> Dict[str, Any]:
    target = _path(data_hash)
    if not target.is_file():
        raise FileNotFoundError(f"market snapshot이 없습니다: {data_hash}")
    return json.loads(target.read_text(encoding="utf-8"))


def has_market_snapshot(data_hash: str) -> bool:
    try:
        return _path(data_hash).is_file()
    except ValueError:
        return False
