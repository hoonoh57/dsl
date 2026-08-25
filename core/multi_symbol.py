"""Deterministic multi-symbol tactical analysis for the Quant DSL factory.

This module is deliberately an orchestration layer around the existing single-
instrument DSL/backtest engine.  It does not introduce a second execution
language or bypass BrokerEmulator.  Higher layers decide *where* and *which
unit* may trade; the existing DSL remains the per-instrument tactical SSOT.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np

from core.backtest import BacktestEngine


SCHEMA_VERSION = "multi_symbol_tactical/v1"


def _stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _time_key(value: Any, *, end_of_day: bool = False) -> str:
    text = _digits(value)
    if len(text) == 8:
        return text + ("235959" if end_of_day else "000000")
    if len(text) >= 14:
        return text[:14]
    raise ValueError(f"시간값은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value}")


def _canonical_rows(market: Mapping[str, Any]) -> list:
    required = ("time", "open", "high", "low", "close", "volume")
    missing = [key for key in required if key not in market]
    if missing:
        raise ValueError(f"시장 데이터 필드 누락: {', '.join(missing)}")
    lengths = {key: len(market[key]) for key in required}
    if len(set(lengths.values())) != 1 or next(iter(lengths.values()), 0) < 2:
        raise ValueError(f"시장 데이터 길이가 올바르지 않습니다: {lengths}")
    rows = []
    previous = None
    for index in range(lengths["time"]):
        timestamp = str(market["time"][index])
        if previous is not None and timestamp <= previous:
            raise ValueError("시장 데이터 시간은 중복 없이 오름차순이어야 합니다.")
        previous = timestamp
        o, h, l, c, v = (float(market[key][index]) for key in ("open", "high", "low", "close", "volume"))
        if not all(math.isfinite(item) for item in (o, h, l, c, v)):
            raise ValueError("시장 데이터에 NaN/Infinity가 있습니다.")
        if h < max(o, c) or l > min(o, c) or h < l or v < 0:
            raise ValueError(f"잘못된 OHLCV: index={index}")
        rows.append((timestamp, o, h, l, c, v))
    return rows


@dataclass(frozen=True)
class OpportunityWindow:
    """Higher-layer market opportunity window.

    Bars before the window remain available to indicators for warm-up, but
    entries are only allowed while this window is active.
    """

    start: str
    end: str
    label: str = ""

    def validate(self) -> None:
        if _time_key(self.start) > _time_key(self.end, end_of_day=True):
            raise ValueError(f"OpportunityWindow start가 end보다 늦습니다: {self.start} > {self.end}")


@dataclass(frozen=True)
class RegimeContext:
    regime_id: str
    state: str = "UNKNOWN"
    active: bool = True
    eligible_units: tuple[str, ...] = ()
    windows: tuple[OpportunityWindow, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def allows(self, unit_id: str) -> bool:
        if not self.active:
            return False
        return not self.eligible_units or unit_id in self.eligible_units


@dataclass(frozen=True)
class MissionSpec:
    """Outcome label contract for a tactical cohort.

    The mission label is measured *after* the capture time and is evidence, not
    an input feature.  The default MFE label uses the capture-bar close as the
    reference and starts from the next bar so the capture bar cannot leak its
    already-completed high/low into future MFE.
    """

    name: str = "MFE_GTE"
    mfe_threshold_pct: Optional[float] = None
    capture_price_field: str = "close"
    include_capture_bar: bool = False

    def validate(self) -> None:
        if self.capture_price_field not in {"open", "high", "low", "close"}:
            raise ValueError("capture_price_field는 open/high/low/close 중 하나여야 합니다.")
        if self.mfe_threshold_pct is not None and not math.isfinite(float(self.mfe_threshold_pct)):
            raise ValueError("mfe_threshold_pct는 유한한 숫자여야 합니다.")


@dataclass(frozen=True)
class TacticalUnitSpec:
    unit_id: str
    unit_type: str
    symbols: tuple[str, ...]
    capture_times: Mapping[str, str] = field(default_factory=dict)
    reference_symbol: str = ""
    rank_by: str = "relative_strength_pct"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.unit_id.strip():
            raise ValueError("unit_id가 필요합니다.")
        if not self.symbols:
            raise ValueError("전투부대 symbols가 비어 있습니다.")
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("전투부대 symbols에 중복이 있습니다.")
        unknown_capture = set(self.capture_times) - set(self.symbols)
        if unknown_capture:
            raise ValueError(f"capture_times에 unit 외 종목이 있습니다: {sorted(unknown_capture)}")


@dataclass(frozen=True)
class InstrumentTask:
    symbol: str
    dsl_code: str
    market: Mapping[str, Any]
    settings: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.symbol.strip():
            raise ValueError("InstrumentTask symbol이 비어 있습니다.")
        if not self.dsl_code.strip():
            raise ValueError(f"{self.symbol}: DSL이 비어 있습니다.")
        _canonical_rows(self.market)


class MultiSymbolAnalysisEngine:
    """Parallel, deterministic orchestration over independent instrument DSLs."""

    RANK_FIELDS = {
        "relative_strength_pct",
        "beta",
        "correlation",
        "strategy_return_pct",
        "capture_mfe_pct",
    }

    @staticmethod
    def _entry_gate(market: Mapping[str, Any], windows: Sequence[OpportunityWindow]) -> Optional[np.ndarray]:
        if not windows:
            return None
        validated = []
        for window in windows:
            window.validate()
            validated.append((_time_key(window.start), _time_key(window.end, end_of_day=True)))
        gate = []
        for value in market["time"]:
            key = _time_key(value)
            gate.append(any(start <= key <= end for start, end in validated))
        return np.asarray(gate, dtype=bool)

    @staticmethod
    def _aligned_relative(market: Mapping[str, Any], benchmark: Optional[Mapping[str, Any]]) -> dict:
        if benchmark is None:
            return {
                "available": False,
                "reason": "benchmark market not supplied",
                "relative_strength_pct": None,
                "beta": None,
                "correlation": None,
                "lead_lag_bars": None,
                "lead_lag_class": None,
                "lead_lag_correlation": None,
            }
        rows = {str(t): float(c) for t, c in zip(market["time"], market["close"])}
        bench_rows = {str(t): float(c) for t, c in zip(benchmark["time"], benchmark["close"])}
        common = sorted(set(rows).intersection(bench_rows))
        if len(common) < 4:
            return {
                "available": False,
                "reason": "exact timestamp overlap requires at least 4 bars",
                "relative_strength_pct": None,
                "beta": None,
                "correlation": None,
                "lead_lag_bars": None,
                "lead_lag_class": None,
                "lead_lag_correlation": None,
            }
        stock = np.asarray([rows[t] for t in common], dtype=float)
        bench = np.asarray([bench_rows[t] for t in common], dtype=float)
        if np.any(stock <= 0) or np.any(bench <= 0):
            raise ValueError("relative analysis에는 양수 close가 필요합니다.")
        sr = np.diff(stock) / stock[:-1]
        br = np.diff(bench) / bench[:-1]
        bench_var = float(np.var(br))
        stock_std = float(np.std(sr))
        bench_std = float(np.std(br))
        beta = float(np.cov(sr, br, ddof=0)[0, 1] / bench_var) if bench_var > 0 else None
        correlation = float(np.corrcoef(sr, br)[0, 1]) if stock_std > 0 and bench_std > 0 else None
        stock_total = (stock[-1] / stock[0] - 1.0) * 100.0
        bench_total = (bench[-1] / bench[0] - 1.0) * 100.0

        best_lag = None
        best_corr = None
        max_lag = min(5, max(0, len(sr) - 3))
        for lag in range(-max_lag, max_lag + 1):
            if lag > 0:
                left, right = sr[:-lag], br[lag:]
            elif lag < 0:
                left, right = sr[-lag:], br[:lag]
            else:
                left, right = sr, br
            if len(left) < 3 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
                continue
            corr = float(np.corrcoef(left, right)[0, 1])
            if best_corr is None or corr > best_corr:
                best_corr, best_lag = corr, lag
        lead_class = None
        if best_lag is not None:
            lead_class = "LEADS" if best_lag > 0 else ("LAGS" if best_lag < 0 else "COINCIDENT")
        return {
            "available": True,
            "overlap_bars": len(common),
            "relative_strength_pct": float(stock_total - bench_total),
            "beta": beta,
            "correlation": correlation,
            "lead_lag_bars": best_lag,
            "lead_lag_class": lead_class,
            "lead_lag_correlation": best_corr,
        }

    @staticmethod
    def _capture_evidence(
        market: Mapping[str, Any], capture_time: Optional[str], mission: MissionSpec
    ) -> dict:
        if not capture_time:
            return {"available": False, "reason": "capture time not supplied"}
        mission.validate()
        times = [str(value) for value in market["time"]]
        exact_matches = [index for index, value in enumerate(times) if value == str(capture_time)]
        if len(exact_matches) != 1:
            raise ValueError(f"capture time은 정확히 1개 bar와 일치해야 합니다: {capture_time}")
        index = exact_matches[0]
        capture_price = float(market[mission.capture_price_field][index])
        if capture_price <= 0:
            raise ValueError("capture price는 0보다 커야 합니다.")
        start = index if mission.include_capture_bar else index + 1
        capture_date = _digits(capture_time)[:8]
        session_indices = [
            i for i in range(start, len(times)) if _digits(times[i])[:8] == capture_date
        ]
        if not session_indices:
            return {
                "available": True,
                "capture_time": str(capture_time),
                "capture_price": capture_price,
                "future_bars": 0,
                "mfe_pct": 0.0,
                "mae_pct": 0.0,
                "mission_success": False if mission.mfe_threshold_pct is not None else None,
            }
        future_high = max(float(market["high"][i]) for i in session_indices)
        future_low = min(float(market["low"][i]) for i in session_indices)
        mfe = (future_high / capture_price - 1.0) * 100.0
        mae = (future_low / capture_price - 1.0) * 100.0
        success = None if mission.mfe_threshold_pct is None else mfe >= float(mission.mfe_threshold_pct)
        return {
            "available": True,
            "capture_time": str(capture_time),
            "capture_price": capture_price,
            "capture_price_field": mission.capture_price_field,
            "include_capture_bar": mission.include_capture_bar,
            "future_bars": len(session_indices),
            "mfe_pct": float(mfe),
            "mae_pct": float(mae),
            "mission_success": success,
            "mission_threshold_pct": mission.mfe_threshold_pct,
        }

    @staticmethod
    def _run_one(task: InstrumentTask, entry_gate: Optional[np.ndarray]) -> dict:
        task.validate()
        result = BacktestEngine.run(
            task.dsl_code,
            settings=dict(task.settings),
            market=dict(task.market),
            data_timeframe=(task.market.get("_meta") or {}).get("timeframe"),
            entry_gate=entry_gate,
        )
        return result

    @classmethod
    def run(
        cls,
        *,
        regime: RegimeContext,
        unit: TacticalUnitSpec,
        tasks: Sequence[InstrumentTask],
        mission: Optional[MissionSpec] = None,
        benchmark_market: Optional[Mapping[str, Any]] = None,
        max_workers: int = 4,
    ) -> dict:
        unit.validate()
        mission = mission or MissionSpec()
        mission.validate()
        if max_workers < 1:
            raise ValueError("max_workers는 1 이상이어야 합니다.")
        task_by_symbol = {task.symbol: task for task in tasks}
        if len(task_by_symbol) != len(tasks):
            raise ValueError("InstrumentTask symbol 중복이 있습니다.")
        missing = [symbol for symbol in unit.symbols if symbol not in task_by_symbol]
        extra = [symbol for symbol in task_by_symbol if symbol not in set(unit.symbols)]
        if missing or extra:
            raise ValueError(f"unit/tasks symbol 불일치: missing={missing}, extra={extra}")

        scenario_payload = {
            "schema": SCHEMA_VERSION,
            "regime": {
                "regime_id": regime.regime_id,
                "state": regime.state,
                "active": regime.active,
                "eligible_units": list(regime.eligible_units),
                "windows": [asdict(item) for item in regime.windows],
            },
            "unit": {
                "unit_id": unit.unit_id,
                "unit_type": unit.unit_type,
                "symbols": list(unit.symbols),
                "capture_times": dict(unit.capture_times),
                "reference_symbol": unit.reference_symbol,
                "rank_by": unit.rank_by,
            },
            "mission": asdict(mission),
            "tasks": [
                {
                    "symbol": task_by_symbol[symbol].symbol,
                    "dsl_hash": _stable_hash(task_by_symbol[symbol].dsl_code),
                    "market_hash": _stable_hash(_canonical_rows(task_by_symbol[symbol].market)),
                    "settings": dict(task_by_symbol[symbol].settings),
                }
                for symbol in unit.symbols
            ],
        }
        scenario_hash = _stable_hash(scenario_payload)
        if not regime.allows(unit.unit_id):
            return {
                "schema": SCHEMA_VERSION,
                "status": "REGIME_BLOCKED",
                "scenario_hash": scenario_hash,
                "regime": scenario_payload["regime"],
                "unit": scenario_payload["unit"],
                "mission": scenario_payload["mission"],
                "results": [],
                "ranking": [],
                "cohort": {"symbols": len(unit.symbols), "executed": 0},
            }

        ordered_tasks = [task_by_symbol[symbol] for symbol in unit.symbols]
        gates = [cls._entry_gate(task.market, regime.windows) for task in ordered_tasks]
        worker_count = min(int(max_workers), len(ordered_tasks))
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="dsl-multi") as executor:
            futures = [executor.submit(cls._run_one, task, gate) for task, gate in zip(ordered_tasks, gates)]
            backtests = []
            for task, future in zip(ordered_tasks, futures):
                try:
                    backtests.append(future.result())
                except Exception as exc:
                    for pending in futures:
                        pending.cancel()
                    raise ValueError(f"{task.symbol} multi-symbol 실행 실패: {exc}") from exc

        rows = []
        for task, result in zip(ordered_tasks, backtests):
            relative = cls._aligned_relative(task.market, benchmark_market)
            capture = cls._capture_evidence(task.market, unit.capture_times.get(task.symbol), mission)
            metrics = result.get("metrics_numeric", {})
            rows.append({
                "symbol": task.symbol,
                "metadata": dict(task.metadata),
                "strategy_return_pct": float(metrics.get("total_return_pct", 0.0) or 0.0),
                "mdd_pct": float(metrics.get("mdd_pct", 0.0) or 0.0),
                "profit_factor": metrics.get("profit_factor"),
                "closed_trades": int(metrics.get("closed_trade_count", 0) or 0),
                "total_cost": float(metrics.get("total_cost", 0.0) or 0.0),
                "relative": relative,
                "capture": capture,
                "backtest": result,
            })

        rank_by = unit.rank_by
        if rank_by not in cls.RANK_FIELDS:
            raise ValueError(f"지원하지 않는 rank_by: {rank_by}")

        def rank_value(item: dict) -> float:
            if rank_by == "strategy_return_pct":
                value = item["strategy_return_pct"]
            elif rank_by == "capture_mfe_pct":
                value = item["capture"].get("mfe_pct") if item["capture"].get("available") else None
            else:
                value = item["relative"].get(rank_by) if item["relative"].get("available") else None
            return float(value) if value is not None and math.isfinite(float(value)) else float("-inf")

        ranked_rows = sorted(rows, key=lambda item: (-rank_value(item), unit.symbols.index(item["symbol"])))
        ranking = [
            {
                "rank": index + 1,
                "symbol": item["symbol"],
                "rank_by": rank_by,
                "score": None if rank_value(item) == float("-inf") else rank_value(item),
            }
            for index, item in enumerate(ranked_rows)
        ]

        returns = [item["strategy_return_pct"] for item in rows]
        mission_rows = [item for item in rows if item["capture"].get("available")]
        mission_positive = [item for item in mission_rows if item["capture"].get("mission_success") is True]
        retained = [item for item in mission_positive if item["strategy_return_pct"] > 0.0]
        cohort = {
            "symbols": len(rows),
            "executed": len(rows),
            "worker_count": worker_count,
            "average_strategy_return_pct": float(mean(returns)) if returns else 0.0,
            "median_strategy_return_pct": float(median(returns)) if returns else 0.0,
            "profitable_symbols": sum(item["strategy_return_pct"] > 0.0 for item in rows),
            "mission_labeled_symbols": len(mission_rows),
            "mission_positive_symbols": len(mission_positive),
            "mission_positive_rate": (len(mission_positive) / len(mission_rows)) if mission_rows else None,
            "mission_positive_profitable_retention": (len(retained) / len(mission_positive)) if mission_positive else None,
        }
        run_hash = _stable_hash({
            "scenario_hash": scenario_hash,
            "rows": [
                {
                    "symbol": item["symbol"],
                    "strategy_return_pct": item["strategy_return_pct"],
                    "mdd_pct": item["mdd_pct"],
                    "relative": item["relative"],
                    "capture": item["capture"],
                }
                for item in rows
            ],
        })
        return {
            "schema": SCHEMA_VERSION,
            "status": "COMPLETED",
            "scenario_hash": scenario_hash,
            "run_hash": run_hash,
            "regime": scenario_payload["regime"],
            "unit": scenario_payload["unit"],
            "mission": scenario_payload["mission"],
            "results": rows,
            "ranking": ranking,
            "cohort": cohort,
        }
