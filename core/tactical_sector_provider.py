"""Exact point-in-time sector membership provider.

The legacy sector UI in the sibling research repository contains a static
leader/follower catalog and dummy fallback. That artifact is useful as research
history but is not accepted as production point-in-time membership authority.
This provider therefore requires an explicit snapshot table and exact cutoff.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from core.tactical_cohort import CohortMember, CohortSnapshot
from core.tactical_providers import MySQLQueryExecutor, QueryExecutor, _safe_identifier, _scalar


class SectorMembershipSnapshotProvider:
    def __init__(
        self,
        executor: Optional[QueryExecutor] = None,
        *,
        database: str,
        table: str,
        as_of_column: str = "as_of",
        sector_id_column: str = "sector_id",
        sector_name_column: str = "sector_name",
        symbol_column: str = "code",
        name_column: str = "name",
        role_column: str = "role",
        feature_columns: Sequence[str] = (),
    ):
        self.executor = executor or MySQLQueryExecutor()
        self.database = _safe_identifier(database, "sector database")
        self.table = _safe_identifier(table, "sector table")
        self.as_of_column = _safe_identifier(as_of_column, "as_of column")
        self.sector_id_column = _safe_identifier(sector_id_column, "sector_id column")
        self.sector_name_column = _safe_identifier(sector_name_column, "sector_name column")
        self.symbol_column = _safe_identifier(symbol_column, "symbol column")
        self.name_column = _safe_identifier(name_column, "name column")
        self.role_column = _safe_identifier(role_column, "role column") if role_column else ""
        self.feature_columns = tuple(
            _safe_identifier(item, "sector feature column") for item in feature_columns
        )

    def load(
        self,
        *,
        as_of: str,
        sector_id: str,
        unit_id: str = "",
    ) -> CohortSnapshot:
        as_of = str(as_of or "").strip()
        sector_id = str(sector_id or "").strip()
        if not as_of or not sector_id:
            raise ValueError("sector as_of와 sector_id가 필요합니다.")
        columns = [
            self.symbol_column,
            self.name_column,
            self.sector_name_column,
            *self.feature_columns,
        ]
        if self.role_column:
            columns.append(self.role_column)
        projection = ", ".join(f"`{name}`" for name in columns)
        sql = (
            f"SELECT {projection} FROM `{self.table}` "
            f"WHERE `{self.as_of_column}`=%s AND `{self.sector_id_column}`=%s "
            f"ORDER BY `{self.symbol_column}`"
        )
        rows = self.executor.fetchall(self.database, sql, (as_of, sector_id))
        if not rows:
            raise ValueError(
                f"정확한 sector membership snapshot이 없습니다: sector={sector_id}, as_of={as_of}"
            )
        members = []
        sector_names = set()
        for row in rows:
            symbol = str(row.get(self.symbol_column) or "").strip()
            if not symbol:
                raise ValueError("sector snapshot에 빈 symbol이 있습니다.")
            sector_name = str(row.get(self.sector_name_column) or "").strip()
            if sector_name:
                sector_names.add(sector_name)
            features = {
                "name": str(row.get(self.name_column) or "").strip(),
                "sector_id": sector_id,
                "sector_name": sector_name,
            }
            if self.role_column:
                features["role"] = str(row.get(self.role_column) or "").strip()
            for column in self.feature_columns:
                features[column] = _scalar(row.get(column))
            members.append(CohortMember(symbol=symbol, capture_time=as_of, features=features))
        if len(sector_names) > 1:
            raise ValueError(
                f"동일 sector_id에 여러 sector_name이 있습니다: {sorted(sector_names)}"
            )
        resolved_unit_id = unit_id.strip() or f"LEADING_SECTOR:{sector_id}:{as_of}"
        return CohortSnapshot.create(
            unit_id=resolved_unit_id,
            as_of=as_of,
            members=members,
            source=f"mysql://{self.database}/{self.table}",
            knowledge_cutoff=as_of,
            metadata={
                "provider": "SectorMembershipSnapshotProvider",
                "sector_id": sector_id,
                "sector_name": next(iter(sector_names), ""),
                "table": self.table,
                "membership_contract": "EXACT_AS_OF",
            },
        )
