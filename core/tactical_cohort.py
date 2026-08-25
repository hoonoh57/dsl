"""Point-in-time cohort contracts for tactical-unit research.

Outcome labels deliberately live outside the cohort snapshot.  A cohort answers
"who was eligible/observed at this time?"; later market outcomes answer "what
happened afterward?".
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Iterable, Mapping, Protocol, Sequence


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any) -> str:
    text = _digits(value)
    if len(text) == 8:
        return text + "235959"
    if len(text) >= 14:
        return text[:14]
    raise ValueError(f"시간값은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value}")


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CohortMember:
    symbol: str
    capture_time: str
    features: Mapping[str, Any] = field(default_factory=dict)

    def validate(self, *, as_of: str) -> None:
        if not self.symbol.strip():
            raise ValueError("cohort member symbol이 비어 있습니다.")
        if _time_key(self.capture_time) > _time_key(as_of):
            raise ValueError(
                f"capture_time이 snapshot as_of보다 미래입니다: {self.symbol} {self.capture_time} > {as_of}"
            )
        forbidden = {key for key in self.features if str(key).lower() in {
            "future_mfe", "future_mae", "mfe_label", "mission_success", "future_return"
        }}
        if forbidden:
            raise ValueError(f"point-in-time cohort feature에 사후 outcome 키를 넣을 수 없습니다: {sorted(forbidden)}")


@dataclass(frozen=True)
class CohortSnapshot:
    unit_id: str
    as_of: str
    members: tuple[CohortMember, ...]
    source: str
    knowledge_cutoff: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    snapshot_hash: str = ""

    @classmethod
    def create(
        cls,
        *,
        unit_id: str,
        as_of: str,
        members: Sequence[CohortMember],
        source: str,
        knowledge_cutoff: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> "CohortSnapshot":
        if not unit_id.strip():
            raise ValueError("unit_id가 필요합니다.")
        if not source.strip():
            raise ValueError("cohort source가 필요합니다.")
        if not members:
            raise ValueError("cohort members가 비어 있습니다.")
        seen = set()
        for member in members:
            member.validate(as_of=as_of)
            if member.symbol in seen:
                raise ValueError(f"cohort symbol 중복: {member.symbol}")
            seen.add(member.symbol)
        payload = {
            "unit_id": unit_id,
            "as_of": as_of,
            "source": source,
            "knowledge_cutoff": knowledge_cutoff,
            "members": [
                {
                    "symbol": member.symbol,
                    "capture_time": member.capture_time,
                    "features": dict(member.features),
                }
                for member in members
            ],
            "metadata": dict(metadata or {}),
        }
        return cls(
            unit_id=unit_id,
            as_of=as_of,
            members=tuple(members),
            source=source,
            knowledge_cutoff=knowledge_cutoff,
            metadata=dict(metadata or {}),
            snapshot_hash=_hash(payload),
        )

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(member.symbol for member in self.members)

    @property
    def capture_times(self) -> dict[str, str]:
        return {member.symbol: member.capture_time for member in self.members}


class CohortProvider(Protocol):
    def load(self, *, unit_id: str, as_of: str) -> CohortSnapshot:
        ...


class StaticCohortProvider:
    """Deterministic provider for API/fixture supplied point-in-time rows.

    It is not a product data fallback; callers must explicitly provide rows.
    """

    def __init__(self, rows: Iterable[Mapping[str, Any]], *, source: str = "explicit_rows"):
        self.rows = [dict(row) for row in rows]
        self.source = source

    def load(self, *, unit_id: str, as_of: str) -> CohortSnapshot:
        selected = []
        for row in self.rows:
            if str(row.get("unit_id", unit_id)) != unit_id:
                continue
            if str(row.get("as_of", as_of)) != as_of:
                continue
            symbol = str(row.get("symbol") or "").strip()
            capture_time = str(row.get("capture_time") or as_of)
            features = dict(row.get("features") or {})
            selected.append(CohortMember(symbol=symbol, capture_time=capture_time, features=features))
        if not selected:
            raise ValueError(f"명시적 cohort rows에서 unit/as_of를 찾지 못했습니다: {unit_id} {as_of}")
        return CohortSnapshot.create(
            unit_id=unit_id,
            as_of=as_of,
            members=selected,
            source=self.source,
            knowledge_cutoff=as_of,
        )
