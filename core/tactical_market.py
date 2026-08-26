"""Fail-closed market providers for tactical-unit execution."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
import os
from typing import Any, Optional, Protocol, Sequence

from core.tactical_providers import MySQLQueryExecutor, QueryExecutor, _safe_identifier


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _date_key(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y%m%d")
    digits = _digits(value)
    if len(digits) < 8:
        raise ValueError(f"날짜는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return digits[:8]


def _time_key(value: Any) -> str:
    if isinstance(value, (time, datetime)):
        return value.strftime("%H%M%S")
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds())
        if seconds < 0 or seconds >= 24 * 3600:
            raise ValueError(f"TIME 값이 하루 범위를 벗어납니다: {value!r}")
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}{m:02d}{s:02d}"
    digits = _digits(value)
    if len(digits) == 3:
        digits = digits.zfill(4) + "00"
    elif len(digits) == 4:
        digits += "00"
    elif len(digits) == 5:
        digits = digits.zfill(6)
    if len(digits) < 6:
        raise ValueError(f"시간은 HHMM 또는 HHMMSS 형식이어야 합니다: {value!r}")
    return digits[:6]


def _timestamp(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d%H%M%S")
    digits = _digits(value)
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"timestamp를 YYYYMMDDHHMMSS로 해석할 수 없습니다: {value!r}")


def _combine_date_time(date_value: Any, time_value: Any) -> str:
    return _date_key(date_value) + _time_key(time_value)


def _number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except Exception as exc:
        raise ValueError(f"{label} 숫자 변환 실패: {value!r}") from exc
    if not (-float("inf") < number < float("inf")):
        raise ValueError(f"{label}에 NaN/Infinity가 있습니다.")
    return number


def _required_source_value(explicit: Optional[str], env_name: str, label: str) -> str:
    value = str(explicit or os.getenv(env_name, "") or "").strip()
    if not value:
        raise ValueError(
            f"{label}이 필요합니다. 명시적으로 지정하거나 {env_name} 환경변수를 설정하세요."
        )
    return value


class SessionMarketProvider(Protocol):
    def load_session(
        self,
        *,
        symbol: str,
        session_date: str,
        timeframe: str,
        required_bars: int,
        end_time: str = "153000",
    ) -> dict:
        ...


class MySQLBarProvider:
    """Schema-adaptive reader for one explicitly configured OHLCV table.

    The adapter supports either one datetime-like timestamp column or separate
    date/time columns. It never generates dummy bars, guesses a production
    database/table, or substitutes another timeframe/table. The concrete
    source must be supplied by constructor arguments or TACTICAL_MINUTE_* env.
    """

    CODE_CANDIDATES = ("code", "stock_code", "symbol", "ticker")
    DATETIME_CANDIDATES = ("datetime", "timestamp", "candle_time", "trade_datetime", "dt")
    DATE_CANDIDATES = ("date", "trade_date", "candle_date", "ymd")
    TIME_CANDIDATES = ("time", "trade_time", "candle_hhmm", "hhmm", "hhmmss")
    OPEN_CANDIDATES = ("open", "open_price", "o")
    HIGH_CANDIDATES = ("high", "high_price", "h")
    LOW_CANDIDATES = ("low", "low_price", "l")
    CLOSE_CANDIDATES = ("close", "close_price", "c")
    VOLUME_CANDIDATES = ("volume", "vol", "qty", "trade_volume")

    def __init__(
        self,
        executor: Optional[QueryExecutor] = None,
        *,
        database: Optional[str] = None,
        table: Optional[str] = None,
        table_timeframe: Optional[str] = None,
    ):
        self.executor = executor or MySQLQueryExecutor()
        resolved_database = _required_source_value(
            database, "TACTICAL_MINUTE_DATABASE", "tactical minute database"
        )
        resolved_table = _required_source_value(
            table, "TACTICAL_MINUTE_TABLE", "tactical minute table"
        )
        self.database = _safe_identifier(resolved_database, "market database")
        self.table = _safe_identifier(resolved_table, "market table")
        self.table_timeframe = str(
            table_timeframe or os.getenv("TACTICAL_MINUTE_TIMEFRAME", "5m")
        ).strip()
        if not self.table_timeframe:
            raise ValueError("table_timeframe이 필요합니다.")
        self._columns: Optional[dict[str, str]] = None

    @staticmethod
    def _pick(columns: Sequence[str], candidates: Sequence[str], label: str) -> str:
        lowered = {str(item).lower(): str(item) for item in columns}
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        raise ValueError(
            f"시장 테이블에서 {label} 컬럼을 찾지 못했습니다. "
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
            raise ValueError(f"{self.database}.{self.table} 컬럼 메타데이터를 읽지 못했습니다.")
        mapping = {
            "code": self._pick(columns, self.CODE_CANDIDATES, "종목코드"),
            "open": self._pick(columns, self.OPEN_CANDIDATES, "시가"),
            "high": self._pick(columns, self.HIGH_CANDIDATES, "고가"),
            "low": self._pick(columns, self.LOW_CANDIDATES, "저가"),
            "close": self._pick(columns, self.CLOSE_CANDIDATES, "종가"),
            "volume": self._pick(columns, self.VOLUME_CANDIDATES, "거래량"),
        }
        lowered = {item.lower(): item for item in columns}
        dt = next((lowered[c] for c in self.DATETIME_CANDIDATES if c in lowered), "")
        if dt:
            mapping["datetime"] = dt
        else:
            mapping["date"] = self._pick(columns, self.DATE_CANDIDATES, "일자")
            mapping["time"] = self._pick(columns, self.TIME_CANDIDATES, "시간")
        self._columns = mapping
        return dict(mapping)

    def load_session(
        self,
        *,
        symbol: str,
        session_date: str,
        timeframe: str,
        required_bars: int,
        end_time: str = "153000",
    ) -> dict:
        symbol = str(symbol or "").strip()
        if not symbol:
            raise ValueError("symbol이 필요합니다.")
        if str(timeframe) != self.table_timeframe:
            raise ValueError(
                f"요청 timeframe({timeframe})과 테이블 timeframe({self.table_timeframe})이 다릅니다."
            )
        required_bars = int(required_bars)
        if required_bars < 2:
            raise ValueError("required_bars는 2 이상이어야 합니다.")
        session_date = _date_key(session_date)
        end_time = _time_key(end_time)
        mapping = self._discover()
        q = lambda name: f"`{name}`"
        projection = [
            f"{q(mapping['open'])} AS open",
            f"{q(mapping['high'])} AS high",
            f"{q(mapping['low'])} AS low",
            f"{q(mapping['close'])} AS close",
            f"{q(mapping['volume'])} AS volume",
        ]
        params: tuple[Any, ...]
        if "datetime" in mapping:
            projection.insert(0, f"{q(mapping['datetime'])} AS source_time")
            end_stamp = (
                f"{session_date[:4]}-{session_date[4:6]}-{session_date[6:8]} "
                f"{end_time[:2]}:{end_time[2:4]}:{end_time[4:6]}"
            )
            sql = (
                f"SELECT {', '.join(projection)} FROM `{self.table}` "
                f"WHERE {q(mapping['code'])}=%s AND {q(mapping['datetime'])}<=%s "
                f"ORDER BY {q(mapping['datetime'])} DESC LIMIT %s"
            )
            params = (symbol, end_stamp, required_bars)
        else:
            projection.insert(0, f"{q(mapping['date'])} AS source_date")
            projection.insert(1, f"{q(mapping['time'])} AS source_clock")
            date_sql = f"{session_date[:4]}-{session_date[4:6]}-{session_date[6:8]}"
            clock_sql = f"{end_time[:2]}:{end_time[2:4]}:{end_time[4:6]}"
            sql = (
                f"SELECT {', '.join(projection)} FROM `{self.table}` "
                f"WHERE {q(mapping['code'])}=%s AND "
                f"({q(mapping['date'])}<%s OR "
                f"({q(mapping['date'])}=%s AND {q(mapping['time'])}<=%s)) "
                f"ORDER BY {q(mapping['date'])} DESC, {q(mapping['time'])} DESC LIMIT %s"
            )
            params = (symbol, date_sql, date_sql, clock_sql, required_bars)
        rows = self.executor.fetchall(self.database, sql, params)
        if len(rows) < required_bars:
            raise ValueError(
                f"{symbol}: warm-up/history coverage 부족: "
                f"rows={len(rows)}, required={required_bars}, "
                f"source={self.database}.{self.table}"
            )
        normalized = []
        seen = set()
        for row in rows:
            if "source_time" in row:
                ts = _timestamp(row["source_time"])
            else:
                ts = _combine_date_time(row.get("source_date"), row.get("source_clock"))
            if ts in seen:
                raise ValueError(f"{symbol}: 시장 데이터 timestamp 중복: {ts}")
            seen.add(ts)
            o = _number(row.get("open"), "open")
            h = _number(row.get("high"), "high")
            l = _number(row.get("low"), "low")
            c = _number(row.get("close"), "close")
            v = _number(row.get("volume"), "volume")
            if h < max(o, c) or l > min(o, c) or h < l or v < 0:
                raise ValueError(f"{symbol}: 잘못된 OHLCV: {ts}")
            normalized.append((ts, o, h, l, c, v))
        normalized.sort(key=lambda item: item[0])
        if any(normalized[i][0] >= normalized[i + 1][0] for i in range(len(normalized) - 1)):
            raise ValueError(f"{symbol}: 시장 데이터 시간이 엄격 오름차순이 아닙니다.")
        market = {key: [] for key in ("time", "open", "high", "low", "close", "volume")}
        for ts, o, h, l, c, v in normalized:
            market["time"].append(ts)
            market["open"].append(o)
            market["high"].append(h)
            market["low"].append(l)
            market["close"].append(c)
            market["volume"].append(v)
        market["_meta"] = {
            "source": f"mysql://{self.database}/{self.table}",
            "instrument": symbol,
            "timeframe": self.table_timeframe,
            "session": "stored_market_data",
            "coverage": {
                "bars": len(normalized),
                "actual_start": normalized[0][0],
                "actual_end": normalized[-1][0],
                "required_bars": required_bars,
                "requested_session_date": session_date,
                "requested_end_time": end_time,
            },
        }
        return market
