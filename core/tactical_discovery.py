"""Micro-first tactical discovery across many independent symbol/date battles.

This layer deliberately evaluates tactics before macro filtering.  Each BattleCase
may carry an immutable BattlefieldContext so future market/sector attribution can
be added without rewriting historical tactical evidence.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import hashlib
import json
import math
from statistics import mean, median
from typing import Any, Mapping, Optional, Sequence

from core.backtest import BacktestEngine
from core.battlefield_context import BattlefieldContext


SCHEMA_VERSION = "tactical_discovery/v1"


def _digits(value: Any) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def _session_date(value: Any) -> str:
    digits = _digits(value)
    if len(digits) < 8:
        raise ValueError(f"session_date는 YYYYMMDD 형식이어야 합니다: {value!r}")
    return digits[:8]


def _time_key(value: Any) -> str:
    digits = _digits(value)
    if len(digits) == 8:
        return digits + "235959"
    if len(digits) >= 14:
        return digits[:14]
    raise ValueError(f"knowledge_cutoff은 YYYYMMDD 또는 YYYYMMDDHHMMSS 형식이어야 합니다: {value!r}")


def _safe_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _safe_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _market_identity(market: Mapping[str, Any]) -> dict:
    required = ("time", "open", "high", "low", "close", "volume")
    missing = [key for key in required if key not in market]
    if missing:
        raise ValueError(f"BattleCase market 필드 누락: {missing}")
    lengths = {key: len(market[key]) for key in required}
    if len(set(lengths.values())) != 1 or next(iter(lengths.values()), 0) < 2:
        raise ValueError(f"BattleCase market 길이가 올바르지 않습니다: {lengths}")
    rows = []
    previous = None
    for index in range(lengths["time"]):
        timestamp = str(market["time"][index])
        if previous is not None and timestamp <= previous:
            raise ValueError("BattleCase market 시간은 중복 없이 엄격 오름차순이어야 합니다.")
        previous = timestamp
        values = [float(market[key][index]) for key in ("open", "high", "low", "close", "volume")]
        if not all(math.isfinite(item) for item in values):
            raise ValueError("BattleCase market에 NaN/Infinity가 있습니다.")
        o, h, l, c, v = values
        if h < max(o, c) or l > min(o, c) or h < l or v < 0:
            raise ValueError(f"BattleCase market OHLCV가 올바르지 않습니다: index={index}")
        rows.append((timestamp, o, h, l, c, v))
    return {
        "rows_hash": _stable_hash(rows),
        "bars": len(rows),
        "first_time": rows[0][0],
        "last_time": rows[-1][0],
        "timeframe": (market.get("_meta") or {}).get("timeframe"),
        "source": (market.get("_meta") or {}).get("source"),
        "instrument": (market.get("_meta") or {}).get("instrument"),
    }


@dataclass(frozen=True)
class TacticCandidate:
    candidate_id: str
    dsl_code: str
    complexity_units: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.candidate_id).strip():
            raise ValueError("candidate_id가 필요합니다.")
        if not str(self.dsl_code).strip():
            raise ValueError("tactic DSL이 비어 있습니다.")
        if int(self.complexity_units) < 1:
            raise ValueError("complexity_units는 1 이상이어야 합니다.")

    @property
    def candidate_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "candidate_id": self.candidate_id,
                "dsl_code": self.dsl_code,
                "complexity_units": int(self.complexity_units),
                "metadata": dict(self.metadata),
            }
        )


@dataclass(frozen=True)
class BattleCase:
    case_id: str
    symbol: str
    session_date: str
    market: Mapping[str, Any]
    settings: Mapping[str, Any] = field(default_factory=dict)
    knowledge_cutoff: str = ""
    battlefield_context: Optional[BattlefieldContext] = None
    entry_gate: Optional[Sequence[bool]] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def resolved_cutoff(self) -> str:
        if str(self.knowledge_cutoff).strip():
            return _time_key(self.knowledge_cutoff)
        return _session_date(self.session_date) + "235959"

    def resolved_context(self) -> BattlefieldContext:
        return self.battlefield_context or BattlefieldContext.neutral(self.resolved_cutoff())

    def validate(self) -> None:
        if not str(self.case_id).strip():
            raise ValueError("BattleCase case_id가 필요합니다.")
        if not str(self.symbol).strip():
            raise ValueError("BattleCase symbol이 필요합니다.")
        session = _session_date(self.session_date)
        market_identity = _market_identity(self.market)
        market_dates = {_digits(value)[:8] for value in self.market["time"] if len(_digits(value)) >= 8}
        if session not in market_dates:
            raise ValueError(
                f"BattleCase session_date({session})가 market에 없습니다: {self.case_id}"
            )
        context = self.resolved_context()
        context.validate_for(self.resolved_cutoff())
        if self.entry_gate is not None and len(self.entry_gate) != market_identity["bars"]:
            raise ValueError(
                f"BattleCase entry_gate 길이가 market bars와 다릅니다: {len(self.entry_gate)} != {market_identity['bars']}"
            )

    @property
    def case_hash(self) -> str:
        self.validate()
        return _stable_hash(
            {
                "case_id": self.case_id,
                "symbol": self.symbol,
                "session_date": _session_date(self.session_date),
                "market": _market_identity(self.market),
                "settings": dict(self.settings),
                "knowledge_cutoff": self.resolved_cutoff(),
                "battlefield_context_hash": self.resolved_context().context_hash,
                "entry_gate": list(self.entry_gate) if self.entry_gate is not None else None,
                "metadata": dict(self.metadata),
            }
        )


class TacticalDiscoveryEngine:
    """Evaluate one tactic over a frozen set of independent BattleCases."""

    @staticmethod
    def _run_case(candidate: TacticCandidate, case: BattleCase) -> dict:
        candidate.validate()
        case.validate()
        timeframe = (case.market.get("_meta") or {}).get("timeframe")
        backtest = BacktestEngine.run(
            candidate.dsl_code,
            settings=dict(case.settings),
            market=dict(case.market),
            data_timeframe=timeframe,
            entry_gate=case.entry_gate,
        )
        metrics = dict(backtest.get("metrics_numeric") or {})
        diagnostics = dict(backtest.get("diagnostics") or {})
        return {
            "case_id": case.case_id,
            "case_hash": case.case_hash,
            "symbol": case.symbol,
            "session_date": _session_date(case.session_date),
            "knowledge_cutoff": case.resolved_cutoff(),
            "context": case.resolved_context().public_dict(),
            "return_pct": float(metrics.get("total_return_pct") or 0.0),
            "mdd_pct": float(metrics.get("mdd_pct") or 0.0),
            "profit_factor": metrics.get("profit_factor", 0.0),
            "trade_count": int(metrics.get("trade_count") or 0),
            "closed_trade_count": int(metrics.get("closed_trade_count") or 0),
            "win_rate_pct": float(metrics.get("win_rate_pct") or 0.0),
            "total_cost": float(metrics.get("total_cost") or 0.0),
            "average_mfe_pct": float(diagnostics.get("average_mfe_pct") or 0.0),
            "average_mae_pct": float(diagnostics.get("average_mae_pct") or 0.0),
            "mfe_giveback_pct": float(diagnostics.get("mfe_giveback_pct") or 0.0),
            "backtest": backtest,
        }

    @classmethod
    def evaluate(
        cls,
        *,
        candidate: TacticCandidate,
        cases: Sequence[BattleCase],
        max_workers: int = 4,
        require_neutral_context: bool = True,
        require_uniform_settings: bool = True,
    ) -> dict:
        candidate.validate()
        frozen_cases = tuple(cases)
        if not frozen_cases:
            raise ValueError("Tactical discovery cases가 비어 있습니다.")
        if len({case.case_id for case in frozen_cases}) != len(frozen_cases):
            raise ValueError("BattleCase case_id에 중복이 있습니다.")
        max_workers = int(max_workers)
        if max_workers < 1:
            raise ValueError("max_workers는 1 이상이어야 합니다.")

        case_hashes = []
        settings_hashes = set()
        for case in frozen_cases:
            case.validate()
            case_hashes.append(case.case_hash)
            settings_hashes.add(_stable_hash(dict(case.settings)))
            if require_neutral_context and case.resolved_context().mode.upper() != "NEUTRAL":
                raise ValueError(
                    f"micro discovery baseline은 NEUTRAL BattlefieldContext만 허용합니다: {case.case_id}"
                )
        if require_uniform_settings and len(settings_hashes) != 1:
            raise ValueError("micro discovery baseline은 모든 BattleCase의 execution settings가 같아야 합니다.")

        with ThreadPoolExecutor(max_workers=min(max_workers, len(frozen_cases))) as pool:
            rows = list(pool.map(lambda case: cls._run_case(candidate, case), frozen_cases))

        returns = [float(row["return_pct"]) for row in rows]
        mdds = [float(row["mdd_pct"]) for row in rows]
        costs = [float(row["total_cost"]) for row in rows]
        trades = [int(row["closed_trade_count"]) for row in rows]
        mfe = [float(row["average_mfe_pct"]) for row in rows]
        mae = [float(row["average_mae_pct"]) for row in rows]
        giveback = [float(row["mfe_giveback_pct"]) for row in rows]
        profitable = [value for value in returns if value > 0.0]
        losing = [value for value in returns if value < 0.0]
        no_trade = sum(1 for count in trades if count == 0)
        finite_pf = []
        infinite_pf_cases = 0
        for row in rows:
            pf = float(row["profit_factor"])
            if math.isfinite(pf):
                finite_pf.append(pf)
            elif pf > 0:
                infinite_pf_cases += 1

        positive_sum = sum(profitable)
        sorted_positive = sorted(profitable, reverse=True)
        top1_concentration = (sorted_positive[0] / positive_sum) if positive_sum > 0 else None
        top3_concentration = (sum(sorted_positive[:3]) / positive_sum) if positive_sum > 0 else None

        context_groups: dict[str, list[dict]] = {}
        for row in rows:
            context_hash = row["context"]["context_hash"]
            context_groups.setdefault(context_hash, []).append(row)
        context_strata = []
        for context_hash, group in sorted(context_groups.items()):
            group_returns = [float(row["return_pct"]) for row in group]
            context_strata.append(
                {
                    "context_hash": context_hash,
                    "mode": group[0]["context"]["mode"],
                    "cases": len(group),
                    "average_return_pct": float(mean(group_returns)),
                    "profitable_case_rate": sum(1 for value in group_returns if value > 0.0) / len(group_returns),
                }
            )

        case_set_hash = _stable_hash(
            {
                "case_ids": [case.case_id for case in frozen_cases],
                "case_hashes": case_hashes,
                "require_neutral_context": bool(require_neutral_context),
                "require_uniform_settings": bool(require_uniform_settings),
            }
        )
        aggregate = {
            "cases": len(rows),
            "active_cases": len(rows) - no_trade,
            "no_trade_cases": no_trade,
            "profitable_cases": len(profitable),
            "losing_cases": len(losing),
            "profitable_case_rate": len(profitable) / len(rows),
            "average_return_pct": float(mean(returns)),
            "median_return_pct": float(median(returns)),
            "best_case_return_pct": float(max(returns)),
            "worst_case_return_pct": float(min(returns)),
            "average_mdd_pct": float(mean(mdds)),
            "worst_mdd_pct": float(min(mdds)),
            "total_closed_trades": int(sum(trades)),
            "average_closed_trades_per_case": float(mean(trades)),
            "total_cost": float(sum(costs)),
            "average_mfe_pct": float(mean(mfe)),
            "average_mae_pct": float(mean(mae)),
            "average_mfe_giveback_pct": float(mean(giveback)),
            "median_finite_profit_factor": float(median(finite_pf)) if finite_pf else None,
            "infinite_profit_factor_cases": infinite_pf_cases,
            "top1_positive_return_concentration": top1_concentration,
            "top3_positive_return_concentration": top3_concentration,
            "complexity_units": int(candidate.complexity_units),
        }
        run_identity = {
            "schema": SCHEMA_VERSION,
            "candidate_hash": candidate.candidate_hash,
            "case_set_hash": case_set_hash,
            "per_case": [
                {
                    key: _safe_json(row[key])
                    for key in (
                        "case_id",
                        "case_hash",
                        "return_pct",
                        "mdd_pct",
                        "profit_factor",
                        "closed_trade_count",
                        "total_cost",
                    )
                }
                for row in rows
            ],
            "aggregate": aggregate,
        }
        return {
            "schema": SCHEMA_VERSION,
            "candidate": {
                "candidate_id": candidate.candidate_id,
                "candidate_hash": candidate.candidate_hash,
                "complexity_units": int(candidate.complexity_units),
                "metadata": dict(candidate.metadata),
            },
            "case_set_hash": case_set_hash,
            "context_policy": {
                "require_neutral_context": bool(require_neutral_context),
                "require_uniform_settings": bool(require_uniform_settings),
            },
            "aggregate": aggregate,
            "context_strata": context_strata,
            "results": rows,
            "run_hash": _stable_hash(run_identity),
            "worker_count": min(max_workers, len(frozen_cases)),
        }
