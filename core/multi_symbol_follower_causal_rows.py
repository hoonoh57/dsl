"""Research-only causal row admission for an LFREAL2 frozen dataset manifest.

LFREAL3 accepts caller-parsed rows plus a trusted-form LFREAL2 manifest and emits
only deterministic research snapshots. It performs no file I/O, provider access,
strategy replay, leader/follower selection, execution, allocation, or deployment.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "multi_symbol_follower_causal_rows/v1"
SNAPSHOT_SCHEMA_VERSION = "multi_symbol_follower_causal_snapshot/v1"
POLICY = "LFREAL2_MANIFEST_EXACT_ROWS_CAUSAL_PREFIX_NO_FUTURE_LEAKAGE_RESEARCH_ONLY"


def _text(value: Any, label: str) -> str:
    result = str(value or "").strip()
    if not result:
        raise ValueError(f"{label}가 필요합니다.")
    return result


def _time_key(value: Any, label: str) -> str:
    text = _text(value, label)
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 14:
        raise ValueError(f"{label}은 YYYYMMDDHHMMSS 이상이어야 합니다.")
    return digits[:14]


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label}은 유한 NUMBER여야 합니다.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}은 유한 NUMBER여야 합니다.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label}에 NaN/Infinity를 사용할 수 없습니다.")
    return result


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CausalMarketRow:
    symbol: str
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def normalized(self) -> dict[str, Any]:
        symbol = _text(self.symbol, "LFREAL3 symbol")
        timestamp = _time_key(self.time, "LFREAL3 time")
        o = _finite(self.open, "LFREAL3 open")
        h = _finite(self.high, "LFREAL3 high")
        l = _finite(self.low, "LFREAL3 low")
        c = _finite(self.close, "LFREAL3 close")
        v = _finite(self.volume, "LFREAL3 volume")
        if h < max(o, c) or l > min(o, c) or h < l:
            raise ValueError("LFREAL3 OHLC 관계가 올바르지 않습니다.")
        if v < 0.0:
            raise ValueError("LFREAL3 volume은 0 이상이어야 합니다.")
        return {
            "symbol": symbol,
            "time": timestamp,
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        }


class CausalRowProducer:
    @staticmethod
    def _validate_manifest(manifest: Mapping[str, Any]) -> None:
        if not isinstance(manifest, Mapping):
            raise ValueError("LFREAL3 manifest는 Mapping이어야 합니다.")
        if str(manifest.get("schema") or "") != "multi_symbol_follower_external_dataset/v1":
            raise ValueError("LFREAL3은 LFREAL2 v1 manifest만 허용합니다.")
        if str(manifest.get("mode") or "") != "RESEARCH_DATASET_ONLY":
            raise ValueError("LFREAL3 manifest mode가 올바르지 않습니다.")
        for key in ("operational_authority", "execution_authority", "deployment_authority", "provider_authority", "file_io_authority"):
            if bool(manifest.get(key)):
                raise ValueError(f"LFREAL3 manifest에 {key}가 있으면 안 됩니다.")
        if not bool(manifest.get("content_hash_verified")):
            raise ValueError("LFREAL3은 content_hash_verified LFREAL2 manifest만 허용합니다.")
        _text(manifest.get("dataset_manifest_hash"), "LFREAL3 dataset_manifest_hash")
        _text(manifest.get("content_sha256"), "LFREAL3 content_sha256")
        _text(manifest.get("timeframe"), "LFREAL3 timeframe")
        symbols = tuple(str(item or "").strip() for item in (manifest.get("symbols") or ()))
        if not symbols or any(not item for item in symbols) or len(set(symbols)) != len(symbols):
            raise ValueError("LFREAL3 manifest symbols가 올바르지 않습니다.")
        _time_key(manifest.get("first_observation"), "LFREAL3 first_observation")
        _time_key(manifest.get("last_observation"), "LFREAL3 last_observation")
        count = manifest.get("record_count")
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("LFREAL3 manifest record_count가 올바르지 않습니다.")

    @classmethod
    def admit(cls, *, manifest: Mapping[str, Any], rows: Sequence[CausalMarketRow]) -> dict[str, Any]:
        cls._validate_manifest(manifest)
        frozen = tuple(rows)
        if not frozen:
            raise ValueError("LFREAL3 rows가 비어 있습니다.")
        normalized = []
        for row in frozen:
            if not isinstance(row, CausalMarketRow):
                raise ValueError("LFREAL3 row 타입이 올바르지 않습니다.")
            normalized.append(row.normalized())
        if len(normalized) != int(manifest["record_count"]):
            raise ValueError("LFREAL3 row count가 LFREAL2 manifest record_count와 다릅니다.")

        declared_symbols = set(str(item) for item in manifest["symbols"])
        observed_symbols = {row["symbol"] for row in normalized}
        if not observed_symbols.issubset(declared_symbols):
            raise ValueError("LFREAL3 row에 manifest 밖의 symbol이 있습니다.")

        identities = [(row["symbol"], row["time"]) for row in normalized]
        if len(set(identities)) != len(identities):
            raise ValueError("LFREAL3 (symbol,time) identity에 중복이 있습니다.")

        first = _time_key(manifest["first_observation"], "LFREAL3 first_observation")
        last = _time_key(manifest["last_observation"], "LFREAL3 last_observation")
        if any(row["time"] < first or row["time"] > last for row in normalized):
            raise ValueError("LFREAL3 row 시간이 manifest observation 범위를 벗어났습니다.")
        if min(row["time"] for row in normalized) != first or max(row["time"] for row in normalized) != last:
            raise ValueError("LFREAL3 rows의 첫/마지막 시간이 manifest 경계와 정확히 일치해야 합니다.")

        ordered = tuple(sorted(normalized, key=lambda row: (row["time"], row["symbol"])))
        payload = {
            "schema": SCHEMA_VERSION,
            "row_policy": POLICY,
            "mode": "RESEARCH_ROWS_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "deployment_authority": False,
            "provider_authority": False,
            "file_io_authority": False,
            "strategy_authority": False,
            "dataset_manifest_hash": str(manifest["dataset_manifest_hash"]),
            "content_sha256": str(manifest["content_sha256"]),
            "timeframe": str(manifest["timeframe"]),
            "declared_symbols": tuple(sorted(declared_symbols)),
            "observed_symbols": tuple(sorted(observed_symbols)),
            "first_observation": first,
            "last_observation": last,
            "record_count": len(ordered),
            "rows": ordered,
            "market_data_authenticity_verified": False,
            "real_data_claim": False,
        }
        payload["row_bundle_hash"] = _stable_hash(payload)
        return payload

    @classmethod
    def snapshot(cls, *, row_bundle: Mapping[str, Any], cutoff: str) -> dict[str, Any]:
        if not isinstance(row_bundle, Mapping) or str(row_bundle.get("schema") or "") != SCHEMA_VERSION:
            raise ValueError("LFREAL3 snapshot은 LFREAL3 row bundle만 허용합니다.")
        if bool(row_bundle.get("operational_authority")) or bool(row_bundle.get("execution_authority")) or bool(row_bundle.get("deployment_authority")):
            raise ValueError("LFREAL3 row bundle에 authority가 있으면 안 됩니다.")
        cutoff_key = _time_key(cutoff, "LFREAL3 cutoff")
        first = _time_key(row_bundle.get("first_observation"), "LFREAL3 first_observation")
        last = _time_key(row_bundle.get("last_observation"), "LFREAL3 last_observation")
        if cutoff_key < first or cutoff_key > last:
            raise ValueError("LFREAL3 cutoff은 dataset observation 범위 안이어야 합니다.")
        rows = tuple(dict(row) for row in (row_bundle.get("rows") or ()))
        visible = tuple(row for row in rows if str(row["time"]) <= cutoff_key)
        if not visible:
            raise ValueError("LFREAL3 cutoff까지 관측 가능한 row가 없습니다.")
        if any(str(row["time"]) > cutoff_key for row in visible):
            raise ValueError("LFREAL3 causal snapshot에 future row가 포함될 수 없습니다.")
        payload = {
            "schema": SNAPSHOT_SCHEMA_VERSION,
            "snapshot_policy": POLICY,
            "mode": "CAUSAL_RESEARCH_SNAPSHOT_ONLY",
            "operational_authority": False,
            "execution_authority": False,
            "deployment_authority": False,
            "dataset_manifest_hash": _text(row_bundle.get("dataset_manifest_hash"), "LFREAL3 dataset_manifest_hash"),
            "row_bundle_hash": _text(row_bundle.get("row_bundle_hash"), "LFREAL3 row_bundle_hash"),
            "knowledge_cutoff": cutoff_key,
            "row_count": len(visible),
            "rows": visible,
            "future_rows_excluded": True,
            "market_data_authenticity_verified": False,
            "real_data_claim": False,
        }
        payload["snapshot_hash"] = _stable_hash(payload)
        return payload
