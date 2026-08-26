"""Point-in-time High-Beta cohort construction from canonical daily candles.

The calculation mirrors the legacy leader/follower beta convention: benchmark
returns are the independent series and symbol beta is covariance(benchmark,
symbol) / variance(benchmark). Only bars at or before ``as_of`` are queried.
The daily table contract is ``daily_candles`` unless explicitly overridden,
but the production database must be explicitly supplied or configured.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
import os
from typing import Any, Optional, Sequence

import numpy as np

from core.tactical_cohort import CohortMember, CohortSnapshot
from core.tactical_providers import MySQLQueryExecutor, QueryExecutor, _safe_identifier


def _date_key(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) < 8:
        raise ValueError(f"as_of는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return digits[:8]


def _sql_date(value: str) -> str:
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def _row_date(value: Any) -> str:
    return _date_key(value)


@dataclass(frozen=True)
class HighBetaSpec:
    benchmark_symbol: str
    lookback_sessions: int = 60
    min_overlap_sessions: int = 40
    top_n: int = 50
    calendar_lookback_days: int = 180

    def validate(self) -> None:
        if not str(self.benchmark_symbol).strip():
            raise ValueError("High-Beta benchmark_symbol이 필요합니다.")
        if self.lookback_sessions < 3:
            raise ValueError("lookback_sessions는 3 이상이어야 합니다.")
        if self.min_overlap_sessions < 3 or self.min_overlap_sessions > self.lookback_sessions:
            raise ValueError("min_overlap_sessions 범위가 올바르지 않습니다.")
        if self.top_n < 1:
            raise ValueError("top_n은 1 이상이어야 합니다.")
        if self.calendar_lookback_days < self.lookback_sessions:
            raise ValueError("calendar_lookback_days는 lookback_sessions 이상이어야 합니다.")


class HighBetaDailyCohortProvider:
    CODE_CANDIDATES = ("code", "stock_code", "symbol", "ticker")
    DATE_CANDIDATES = ("date", "trade_date", "candle_date", "ymd")
    CLOSE_CANDIDATES = ("close", "close_price", "closing_price", "c")

    def __init__(
        self,
        executor: Optional[QueryExecutor] = None,
        *,
        database: Optional[str] = None,
        table: Optional[str] = None,
    ):
        self.executor = executor or MySQLQueryExecutor()
        resolved_database = str(
            database or os.getenv("TACTICAL_DAILY_DATABASE", "") or ""
        ).strip()
        if not resolved_database:
            raise ValueError(
                "High-Beta daily database가 필요합니다. 명시적으로 지정하거나 "
                "TACTICAL_DAILY_DATABASE 환경변수를 설정하세요."
            )
        self.database = _safe_identifier(resolved_database, "daily database")
        self.table = _safe_identifier(
            table or os.getenv("TACTICAL_DAILY_TABLE", "daily_candles"),
            "daily table",
        )
        self._columns: Optional[dict[str, str]] = None

    @staticmethod
    def _pick(columns: Sequence[str], candidates: Sequence[str], label: str) -> str:
        lowered = {str(item).lower(): str(item) for item in columns}
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        raise ValueError(
            f"daily table에서 {label} 컬럼을 찾지 못했습니다. "
            f"후보={list(candidates)}, 실제={sorted(columns)}"
        )

    def _discover(self) -> dict[str, str]:
        if self._columns is not None:
            return dict(self._columns)
        rows = self.executor.fetchall(
            self.database,
            f"SHOW COLUMNS FROM `{self.table}`",
            (),
        )
        columns = [
            str(row.get("Field") or row.get("field") or "").strip()
            for row in rows
            if str(row.get("Field") or row.get("field") or "").strip()
        ]
        if not columns:
            raise ValueError(f"{self.database}.{self.table} 컬럼을 읽지 못했습니다.")
        self._columns = {
            "code": self._pick(columns, self.CODE_CANDIDATES, "종목코드"),
            "date": self._pick(columns, self.DATE_CANDIDATES, "일자"),
            "close": self._pick(columns, self.CLOSE_CANDIDATES, "종가"),
        }
        return dict(self._columns)

    def load(
        self,
        *,
        as_of: Any,
        spec: HighBetaSpec,
        unit_id: str = "",
        universe_symbols: Optional[Sequence[str]] = None,
    ) -> CohortSnapshot:
        spec.validate()
        as_of_key = _date_key(as_of)
        as_of_dt = datetime.strptime(as_of_key, "%Y%m%d")
        start_key = (as_of_dt - timedelta(days=int(spec.calendar_lookback_days))).strftime("%Y%m%d")
        cols = self._discover()
        q = lambda name: f"`{name}`"
        params: list[Any] = [_sql_date(start_key), _sql_date(as_of_key)]
        where = (
            f"{q(cols['date'])}>=%s AND {q(cols['date'])}<=%s"
        )
        universe = [str(item).strip() for item in (universe_symbols or []) if str(item).strip()]
        benchmark = str(spec.benchmark_symbol).strip()
        if universe:
            selected = []
            for symbol in [*universe, benchmark]:
                if symbol not in selected:
                    selected.append(symbol)
            placeholders = ",".join(["%s"] * len(selected))
            where += f" AND {q(cols['code'])} IN ({placeholders})"
            params.extend(selected)
        sql = (
            f"SELECT {q(cols['code'])} AS code, {q(cols['date'])} AS trade_date, "
            f"{q(cols['close'])} AS close FROM `{self.table}` "
            f"WHERE {where} ORDER BY {q(cols['code'])}, {q(cols['date'])}"
        )
        rows = self.executor.fetchall(self.database, sql, tuple(params))
        if not rows:
            raise ValueError(f"High-Beta daily rows가 없습니다: as_of={as_of_key}")

        by_symbol: dict[str, dict[str, float]] = {}
        for row in rows:
            symbol = str(row.get("code") or "").strip()
            day = _row_date(row.get("trade_date"))
            close = float(row.get("close"))
            if close <= 0 or not math.isfinite(close):
                raise ValueError(f"{symbol}: High-Beta daily close가 유효하지 않습니다: {day}")
            target = by_symbol.setdefault(symbol, {})
            if day in target:
                raise ValueError(f"{symbol}: daily candle 일자 중복: {day}")
            target[day] = close
        if benchmark not in by_symbol or as_of_key not in by_symbol[benchmark]:
            raise ValueError(
                f"High-Beta benchmark가 exact as_of에 없습니다: {benchmark} {as_of_key}"
            )

        bench_map = by_symbol[benchmark]
        candidates = []
        for symbol, stock_map in by_symbol.items():
            if symbol == benchmark:
                continue
            if universe and symbol not in universe:
                continue
            if as_of_key not in stock_map:
                continue
            common = sorted(set(stock_map).intersection(bench_map))
            common = common[-(int(spec.lookback_sessions) + 1):]
            if len(common) < int(spec.min_overlap_sessions) + 1:
                continue
            stock = np.asarray([stock_map[day] for day in common], dtype=float)
            bench = np.asarray([bench_map[day] for day in common], dtype=float)
            sr = np.diff(stock) / stock[:-1]
            br = np.diff(bench) / bench[:-1]
            if len(sr) < int(spec.min_overlap_sessions):
                continue
            bench_var = float(np.var(br))
            if bench_var <= 0.0:
                raise ValueError("High-Beta benchmark return variance가 0입니다.")
            beta = float(np.cov(br, sr, ddof=0)[0, 1] / bench_var)
            stock_std = float(np.std(sr))
            bench_std = float(np.std(br))
            corr = float(np.corrcoef(br, sr)[0, 1]) if stock_std > 0 and bench_std > 0 else None
            stock_total = (stock[-1] / stock[0] - 1.0) * 100.0
            bench_total = (bench[-1] / bench[0] - 1.0) * 100.0
            rs = float(stock_total - bench_total)
            if not math.isfinite(beta) or not math.isfinite(rs):
                continue
            candidates.append(
                {
                    "symbol": symbol,
                    "beta": beta,
                    "correlation": corr,
                    "relative_strength_pct": rs,
                    "overlap_sessions": len(sr),
                    "as_of_close": float(stock[-1]),
                }
            )
        candidates.sort(key=lambda item: (-item["beta"], item["symbol"]))
        selected = candidates[: int(spec.top_n)]
        if not selected:
            raise ValueError(
                f"High-Beta 기준을 충족하는 exact-as-of 후보가 없습니다: {as_of_key}"
            )
        capture = as_of_key + "235959"
        members = tuple(
            CohortMember(
                symbol=item["symbol"],
                capture_time=capture,
                features={
                    "beta": item["beta"],
                    "correlation": item["correlation"],
                    "relative_strength_pct": item["relative_strength_pct"],
                    "overlap_sessions": item["overlap_sessions"],
                    "as_of_close": item["as_of_close"],
                    "beta_rank": index + 1,
                },
            )
            for index, item in enumerate(selected)
        )
        resolved_unit_id = unit_id.strip() or f"HIGH_BETA:{benchmark}:{as_of_key}"
        return CohortSnapshot.create(
            unit_id=resolved_unit_id,
            as_of=capture,
            members=members,
            source=f"mysql://{self.database}/{self.table}",
            knowledge_cutoff=capture,
            metadata={
                "provider": "HighBetaDailyCohortProvider",
                "benchmark_symbol": benchmark,
                "lookback_sessions": int(spec.lookback_sessions),
                "min_overlap_sessions": int(spec.min_overlap_sessions),
                "top_n": int(spec.top_n),
                "rank_by": "beta",
                "beta_convention": "cov(benchmark_return,symbol_return)/var(benchmark_return)",
                "as_of": as_of_key,
            },
        )
