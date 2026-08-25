"""Production point-in-time cohort providers for tactical research.

Provider responsibilities are intentionally narrow:
- freeze who was observable at an explicit cutoff;
- keep post-cutoff outcomes out of cohort features;
- fail closed when a requested cohort cannot be proven;
- expose source evidence without leaking credentials.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
import hashlib
import json
import math
import os
import re
from typing import Any, Mapping, Optional, Protocol, Sequence

from core.tactical_cohort import CohortMember, CohortSnapshot


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not _IDENTIFIER.fullmatch(text):
        raise ValueError(f"{label}에 허용되지 않는 식별자가 있습니다: {value!r}")
    return text


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _scalar(value: Any):
    if value is None:
        return None
    if isinstance(value, Decimal):
        number = float(value)
        return int(number) if number.is_integer() else number
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")
    if isinstance(value, time):
        return value.strftime("%H%M%S")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("DB cohort 값에 NaN/Infinity를 사용할 수 없습니다.")
        return value
    return value


def _date_key(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) < 8:
        raise ValueError(f"search_date는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return digits[:8]


def _time_key(value: Any) -> str:
    if isinstance(value, (time, datetime)):
        return value.strftime("%H%M%S")
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) == 3:
        digits = digits.zfill(4) + "00"
    elif len(digits) == 4:
        digits += "00"
    elif len(digits) == 5:
        digits = digits.zfill(6)
    if len(digits) < 6:
        raise ValueError(f"search_time은 HHMMSS 또는 HHMM 형식이어야 합니다: {value!r}")
    return digits[:6]


def _sql_time(value: Any) -> str:
    key = _time_key(value)
    return f"{key[:2]}:{key[2:4]}:{key[4:6]}"


@dataclass(frozen=True)
class MySQLSettings:
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    charset: str = "utf8mb4"

    @classmethod
    def from_env(cls) -> "MySQLSettings":
        return cls(
            host=os.getenv("MYSQL_HOST", os.getenv("DB_HOST", "127.0.0.1")),
            port=int(os.getenv("MYSQL_PORT", os.getenv("DB_PORT", "3306"))),
            user=os.getenv("MYSQL_USER", os.getenv("DB_USER", "root")),
            password=os.getenv(
                "MYSQL_PASSWORD",
                os.getenv("DB_PASS", os.getenv("DB_PASSWORD", "")),
            ),
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
        )


class QueryExecutor(Protocol):
    def fetchall(
        self,
        database: str,
        sql: str,
        params: Sequence[Any] = (),
    ) -> list[dict]:
        ...


class MySQLQueryExecutor:
    """Small PyMySQL adapter with no product-level fallback."""

    def __init__(self, settings: Optional[MySQLSettings] = None):
        self.settings = settings or MySQLSettings.from_env()

    def fetchall(
        self,
        database: str,
        sql: str,
        params: Sequence[Any] = (),
    ) -> list[dict]:
        database = _safe_identifier(database, "database")
        try:
            import pymysql
        except Exception as exc:  # pragma: no cover - environment-specific
            raise RuntimeError(
                "PyMySQL이 필요합니다. requirements.txt를 설치하세요."
            ) from exc
        conn = pymysql.connect(
            host=self.settings.host,
            port=int(self.settings.port),
            user=self.settings.user,
            password=self.settings.password,
            database=database,
            charset=self.settings.charset,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()


@dataclass(frozen=True)
class TacticalCohortBundle:
    snapshot: CohortSnapshot
    outcomes: Mapping[str, Mapping[str, Any]]
    source_evidence: Mapping[str, Any]

    @property
    def outcome_hash(self) -> str:
        return _stable_hash(self.outcomes)

    def public_snapshot(self) -> dict:
        return {
            "unit_id": self.snapshot.unit_id,
            "as_of": self.snapshot.as_of,
            "source": self.snapshot.source,
            "knowledge_cutoff": self.snapshot.knowledge_cutoff,
            "snapshot_hash": self.snapshot.snapshot_hash,
            "metadata": dict(self.snapshot.metadata),
            "members": [
                {
                    "symbol": member.symbol,
                    "capture_time": member.capture_time,
                    "features": dict(member.features),
                }
                for member in self.snapshot.members
            ],
            "source_evidence": dict(self.source_evidence),
        }

    def to_evaluation_payload(self) -> dict:
        return {
            **self.public_snapshot(),
            "outcomes": {key: dict(value) for key, value in self.outcomes.items()},
            "outcome_hash": self.outcome_hash,
        }


class Performance1516CohortProvider:
    """Load one exact Kiwoom 1516 performance group from performance_result.

    The cohort is frozen from fields observable at search time. Return fields
    and labels are stored only in ``outcomes`` and are never copied into
    ``CohortMember.features``.
    """

    OUTCOME_FIELDS = (
        "ret_1m",
        "ret_3m",
        "ret_7h",
        "max_ret_in_period",
        "label_3",
        "label_5",
        "label_10",
        "actual_rank_by_max_ret",
    )

    def __init__(
        self,
        executor: Optional[QueryExecutor] = None,
        *,
        database: Optional[str] = None,
    ):
        self.executor = executor or MySQLQueryExecutor()
        self.database = _safe_identifier(
            database or os.getenv("PERFORMANCE_DB_NAME", "performance_db"),
            "performance database",
        )

    def load_group(
        self,
        *,
        search_date: Any,
        search_time: Any = "09:05:00",
        condition_name: str = "1516",
        hold_period: str = "7시간",
    ) -> TacticalCohortBundle:
        date_key = _date_key(search_date)
        time_key = _time_key(search_time)
        condition_name = str(condition_name or "").strip()
        hold_period = str(hold_period or "").strip()
        if not condition_name:
            raise ValueError("condition_name이 필요합니다.")
        if not hold_period:
            raise ValueError("hold_period가 필요합니다.")

        sql = """
SELECT
    code,
    name,
    search_volume,
    ret_1m,
    ret_3m,
    ret_7h,
    max_ret_in_period,
    label_3,
    label_5,
    label_10,
    actual_rank_by_max_ret
FROM performance_result
WHERE search_date=%s
  AND search_time=%s
  AND condition_name=%s
  AND hold_period=%s
ORDER BY code
""".strip()
        rows = self.executor.fetchall(
            self.database,
            sql,
            (
                f"{date_key[:4]}-{date_key[4:6]}-{date_key[6:8]}",
                _sql_time(search_time),
                condition_name,
                hold_period,
            ),
        )
        if not rows:
            raise ValueError(
                "performance_result에서 정확한 1516 cohort를 찾지 못했습니다: "
                f"{date_key} {time_key} {condition_name} {hold_period}"
            )

        capture_time = date_key + time_key
        members: list[CohortMember] = []
        outcomes: dict[str, dict[str, Any]] = {}
        ranks: set[int] = set()
        for row in rows:
            symbol = str(row.get("code") or "").strip()
            if not re.fullmatch(r"\d{6}", symbol):
                raise ValueError(f"performance_result 종목코드가 6자리 숫자가 아닙니다: {symbol!r}")
            if symbol in outcomes:
                raise ValueError(f"performance_result cohort 종목 중복: {symbol}")

            label10 = _scalar(row.get("label_10"))
            max_ret = _scalar(row.get("max_ret_in_period"))
            if label10 not in (0, 1):
                raise ValueError(f"{symbol}: label_10은 0/1이어야 합니다: {label10!r}")
            if max_ret is not None and int(float(max_ret) >= 10.0) != int(label10):
                raise ValueError(
                    f"{symbol}: label_10과 max_ret_in_period가 일치하지 않습니다: "
                    f"max={max_ret}, label_10={label10}"
                )
            rank = _scalar(row.get("actual_rank_by_max_ret"))
            if rank is not None:
                rank = int(rank)
                if rank <= 0 or rank in ranks:
                    raise ValueError(f"{symbol}: actual_rank_by_max_ret가 유효하지 않습니다: {rank}")
                ranks.add(rank)

            features = {
                "name": str(row.get("name") or "").strip(),
                "search_volume": _scalar(row.get("search_volume")),
            }
            members.append(
                CohortMember(
                    symbol=symbol,
                    capture_time=capture_time,
                    features=features,
                )
            )
            outcomes[symbol] = {
                "ret_1m": _scalar(row.get("ret_1m")),
                "ret_3m": _scalar(row.get("ret_3m")),
                "ret_7h": _scalar(row.get("ret_7h")),
                "max_ret_in_period": max_ret,
                "label_3": int(_scalar(row.get("label_3")) or 0),
                "label_5": int(_scalar(row.get("label_5")) or 0),
                "label_10": int(label10),
                "actual_rank_by_max_ret": rank,
            }

        unit_id = f"1516:{condition_name}:{hold_period}:{date_key}:{time_key}"
        snapshot = CohortSnapshot.create(
            unit_id=unit_id,
            as_of=capture_time,
            members=members,
            source=f"mysql://{self.database}/performance_result",
            knowledge_cutoff=capture_time,
            metadata={
                "provider": "Performance1516CohortProvider",
                "search_date": date_key,
                "search_time": time_key,
                "condition_name": condition_name,
                "hold_period": hold_period,
                "outcome_authority": "performance_result",
                "outcome_fields": list(self.OUTCOME_FIELDS),
            },
        )
        return TacticalCohortBundle(
            snapshot=snapshot,
            outcomes=outcomes,
            source_evidence={
                "database": self.database,
                "table": "performance_result",
                "row_count": len(rows),
                "query_contract": "EXACT_GROUP",
            },
        )


class PointInTimeMetricCohortProvider:
    """Configurable exact-snapshot provider for High-Beta/sector research tables.

    Callers must name the table and columns explicitly. The provider never
    substitutes a nearby date or another universe.
    """

    def __init__(
        self,
        executor: QueryExecutor,
        *,
        database: str,
        table: str,
        symbol_column: str,
        as_of_column: str,
        feature_columns: Sequence[str],
        name_column: str = "",
        unit_type: str = "METRIC_SNAPSHOT",
    ):
        self.executor = executor
        self.database = _safe_identifier(database, "database")
        self.table = _safe_identifier(table, "table")
        self.symbol_column = _safe_identifier(symbol_column, "symbol column")
        self.as_of_column = _safe_identifier(as_of_column, "as_of column")
        self.feature_columns = tuple(
            _safe_identifier(item, "feature column") for item in feature_columns
        )
        self.name_column = (
            _safe_identifier(name_column, "name column") if name_column else ""
        )
        self.unit_type = str(unit_type or "METRIC_SNAPSHOT").strip()

    def load(
        self,
        *,
        unit_id: str,
        as_of: str,
    ) -> CohortSnapshot:
        if not unit_id.strip():
            raise ValueError("unit_id가 필요합니다.")
        selected_columns = [self.symbol_column, *self.feature_columns]
        if self.name_column:
            selected_columns.append(self.name_column)
        projection = ", ".join(f"`{name}`" for name in selected_columns)
        sql = (
            f"SELECT {projection} FROM `{self.table}` "
            f"WHERE `{self.as_of_column}`=%s ORDER BY `{self.symbol_column}`"
        )
        rows = self.executor.fetchall(self.database, sql, (as_of,))
        if not rows:
            raise ValueError(
                f"정확한 point-in-time metric cohort가 없습니다: {self.table} {as_of}"
            )
        members = []
        for row in rows:
            symbol = str(row.get(self.symbol_column) or "").strip()
            features = {name: _scalar(row.get(name)) for name in self.feature_columns}
            if self.name_column:
                features["name"] = str(row.get(self.name_column) or "").strip()
            members.append(CohortMember(symbol=symbol, capture_time=as_of, features=features))
        return CohortSnapshot.create(
            unit_id=unit_id,
            as_of=as_of,
            members=members,
            source=f"mysql://{self.database}/{self.table}",
            knowledge_cutoff=as_of,
            metadata={
                "provider": "PointInTimeMetricCohortProvider",
                "unit_type": self.unit_type,
                "table": self.table,
                "feature_columns": list(self.feature_columns),
            },
        )
