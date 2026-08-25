"""Stage 1 Single-Symbol Strategy Factory.

This module intentionally keeps the LLM outside the deterministic measurement
boundary.  It owns data provenance, immutable experiments, parameter search,
result diagnostics, human-mediated feedback packages, target-loop state and
methodology summaries.  The trading semantics remain in the DSL/runtime/
backtest stack.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
import re
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import numpy as np

from core.backtest import BacktestEngine, synthetic_market
from core.db import DB_PATH
from core.dsl_parser import DSLParser
from core.dsl_runtime import DSLRuntime


FACTORY_SCHEMA_VERSION = "stage1_factory/v1"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def utc_epoch() -> float:
    return time.time()


def extract_dsl(text: str) -> str:
    blocks = re.findall(r"```(?:dsl|local-dsl)?[ \t]*\r?\n(.*?)```", text or "", flags=re.I | re.S)
    candidates = blocks or [text or ""]
    for candidate in candidates:
        start = re.search(r'''strategy\s+["'][^"']+["']\s*\{''', candidate)
        if not start:
            continue
        source = candidate[start.start():].strip()
        depth = 0
        quote = None
        escaped = False
        for index, char in enumerate(source):
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return source[:index + 1].strip()
        raise ValueError("LLM 응답의 strategy DSL 블록이 닫히지 않았습니다.")
    raise ValueError("LLM 응답에서 strategy DSL을 찾지 못했습니다.")


@dataclass(frozen=True)
class DataProvenance:
    instrument: str
    timeframe: str
    source: str
    start: str
    end: str
    bars: int
    data_hash: str
    adjustment_policy: str = "unspecified"
    session: str = "regular"
    knowledge_cutoff: str = ""


class DataContract:
    REQUIRED = ("time", "open", "high", "low", "close", "volume")

    @staticmethod
    def normalize(market: Dict[str, Any], *, instrument: str, timeframe: str, source: str,
                  adjustment_policy: str = "unspecified", session: str = "regular",
                  knowledge_cutoff: str = "") -> tuple[Dict[str, Any], DataProvenance]:
        if not isinstance(market, dict):
            raise ValueError("market은 dict여야 합니다.")
        missing = [key for key in DataContract.REQUIRED if key not in market]
        if missing:
            raise ValueError(f"시장 데이터 필드 누락: {', '.join(missing)}")
        lengths = {key: len(market[key]) for key in DataContract.REQUIRED}
        if len(set(lengths.values())) != 1 or next(iter(lengths.values()), 0) < 2:
            raise ValueError(f"시장 데이터 길이가 올바르지 않습니다: {lengths}")
        rows = []
        previous = None
        for i in range(lengths["time"]):
            timestamp = str(market["time"][i])
            if previous is not None and timestamp <= previous:
                raise ValueError("시장 데이터 시간은 중복 없이 오름차순이어야 합니다.")
            previous = timestamp
            values = [float(market[key][i]) for key in ("open", "high", "low", "close", "volume")]
            if not all(math.isfinite(value) for value in values):
                raise ValueError("시장 데이터에 NaN/Infinity가 있습니다.")
            o, h, l, c, v = values
            if h < max(o, c) or l > min(o, c) or h < l or v < 0:
                raise ValueError(f"잘못된 OHLCV: index={i}")
            rows.append((timestamp, o, h, l, c, v))
        data_hash = stable_hash(rows)
        normalized = {
            "time": [row[0] for row in rows],
            "open": [row[1] for row in rows],
            "high": [row[2] for row in rows],
            "low": [row[3] for row in rows],
            "close": [row[4] for row in rows],
            "volume": [row[5] for row in rows],
            "_meta": {
                "instrument": instrument,
                "timeframe": timeframe,
                "source": source,
                "data_hash": data_hash,
                "adjustment_policy": adjustment_policy,
                "session": session,
                "knowledge_cutoff": knowledge_cutoff,
            },
        }
        provenance = DataProvenance(
            instrument=instrument,
            timeframe=timeframe,
            source=source,
            start=rows[0][0],
            end=rows[-1][0],
            bars=len(rows),
            data_hash=data_hash,
            adjustment_policy=adjustment_policy,
            session=session,
            knowledge_cutoff=knowledge_cutoff,
        )
        return normalized, provenance

    @staticmethod
    def synthetic_fixture(*, instrument="SYNTH", timeframe="1d", bars=600):
        market = synthetic_market(bars)
        market["_meta"] = {"source": "synthetic_fixture", "timeframe": timeframe, "instrument": instrument}
        return DataContract.normalize(market, instrument=instrument, timeframe=timeframe, source="synthetic_fixture")


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    values: tuple[float, ...]
    target: str = "dsl"  # dsl | setting

    @staticmethod
    def from_payload(payload: Dict[str, Any]) -> "ParameterSpec":
        name = str(payload.get("name", "")).strip()
        target = str(payload.get("target", "dsl")).strip().lower()
        if not name or target not in {"dsl", "setting"}:
            raise ValueError("parameter name/target이 올바르지 않습니다.")
        if "values" in payload:
            values = tuple(float(item) for item in payload["values"])
        else:
            low = float(payload["min"])
            high = float(payload["max"])
            step = float(payload.get("step", 1))
            if step <= 0 or high < low:
                raise ValueError(f"잘못된 parameter 범위: {name}")
            values_list = []
            current = low
            for _ in range(1_000_000):
                if current > high + step * 1e-9:
                    break
                values_list.append(current)
                current += step
            values = tuple(values_list)
        if not values or not all(math.isfinite(value) for value in values):
            raise ValueError(f"parameter candidate가 비어 있거나 유효하지 않습니다: {name}")
        return ParameterSpec(name=name, values=values, target=target)


def discover_dsl_parameters(dsl_code: str) -> list[dict]:
    document = DSLParser.parse(dsl_code)
    output = []
    for assignment in document.assignments:
        if not assignment.is_input:
            continue
        text = assignment.expression.strip()
        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
            output.append({"name": assignment.name, "value": float(text), "target": "dsl"})
    return output


def _format_number(value: float) -> str:
    rounded = round(float(value))
    return str(int(rounded)) if abs(float(value) - rounded) < 1e-12 else format(float(value), ".12g")


def apply_dsl_parameters(dsl_code: str, values: Dict[str, float]) -> str:
    if not values:
        return dsl_code
    document = DSLParser.parse(dsl_code)
    allowed = {item.name for item in document.assignments if item.is_input}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"DSL input이 아닌 parameter를 변경할 수 없습니다: {', '.join(sorted(unknown))}")
    source = dsl_code
    for name, value in values.items():
        pattern = re.compile(rf"(?m)^(\s*input\s+{re.escape(name)}\s*=\s*)([^;\r\n]+)(\s*;?\s*)$")
        source, count = pattern.subn(lambda match: match.group(1) + _format_number(value) + match.group(3), source, count=1)
        if count != 1:
            raise ValueError(f"parameter line을 안전하게 교체하지 못했습니다: {name}")
    DSLParser.parse(source)
    return source


class StrategyFactoryStore:
    """Append-only experiment store. Mutable pointers live in separate tables."""

    def __init__(self, path: Path | str = DB_PATH):
        self.path = str(path)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS stage1_experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER,
            root_id INTEGER,
            operation TEXT NOT NULL,
            strategy_name TEXT,
            intent TEXT,
            dsl_code TEXT NOT NULL,
            dsl_hash TEXT NOT NULL,
            parameter_json TEXT NOT NULL,
            execution_json TEXT NOT NULL,
            provenance_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            analysis_json TEXT NOT NULL,
            prompt_text TEXT,
            llm_response TEXT,
            hypothesis TEXT,
            expected_effect TEXT,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_heads (
            root_id INTEGER PRIMARY KEY,
            experiment_id INTEGER NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_search_studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_experiment_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            objective TEXT NOT NULL,
            seed INTEGER NOT NULL,
            space_json TEXT NOT NULL,
            summary_json TEXT,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_search_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_id INTEGER NOT NULL,
            candidate_hash TEXT NOT NULL,
            parameter_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            score REAL NOT NULL,
            status TEXT NOT NULL,
            created_at REAL NOT NULL,
            UNIQUE(study_id, candidate_hash)
        );
        CREATE TABLE IF NOT EXISTS stage1_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            before_experiment_id INTEGER NOT NULL,
            after_experiment_id INTEGER,
            observation TEXT,
            hypothesis TEXT,
            proposal TEXT,
            expected_effect TEXT,
            verdict TEXT NOT NULL,
            reason TEXT,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage1_target_loops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_id INTEGER NOT NULL,
            target_return REAL NOT NULL,
            iteration_limit INTEGER NOT NULL,
            backtest_budget INTEGER NOT NULL,
            no_improvement_limit INTEGER NOT NULL,
            state_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        """)
        conn.commit()
        conn.close()

    def create_experiment(self, *, parent_id: Optional[int], operation: str, strategy_name: str,
                          intent: str, dsl_code: str, parameters: Dict[str, Any], execution: Dict[str, Any],
                          provenance: Dict[str, Any], result: Dict[str, Any], analysis: Dict[str, Any],
                          prompt_text: str = "", llm_response: str = "", hypothesis: str = "",
                          expected_effect: str = "") -> dict:
        conn = self.connect()
        cur = conn.cursor()
        root_id = None
        if parent_id:
            parent = cur.execute("SELECT root_id FROM stage1_experiments WHERE id=?", (parent_id,)).fetchone()
            if not parent:
                conn.close()
                raise ValueError(f"parent experiment가 없습니다: {parent_id}")
            root_id = int(parent["root_id"])
        payload = (
            parent_id, root_id, operation, strategy_name, intent, dsl_code, stable_hash(dsl_code),
            _json(parameters), _json(execution), _json(provenance), _json(result), _json(analysis),
            prompt_text, llm_response, hypothesis, expected_effect, utc_epoch(),
        )
        cur.execute("""INSERT INTO stage1_experiments(
            parent_id,root_id,operation,strategy_name,intent,dsl_code,dsl_hash,parameter_json,
            execution_json,provenance_json,result_json,analysis_json,prompt_text,llm_response,
            hypothesis,expected_effect,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", payload)
        experiment_id = int(cur.lastrowid)
        if root_id is None:
            root_id = experiment_id
            cur.execute("UPDATE stage1_experiments SET root_id=? WHERE id=?", (root_id, experiment_id))
            cur.execute("INSERT OR REPLACE INTO stage1_heads(root_id,experiment_id,updated_at) VALUES (?,?,?)",
                        (root_id, experiment_id, utc_epoch()))
        conn.commit()
        conn.close()
        return self.get_experiment(experiment_id)

    def get_experiment(self, experiment_id: int) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT * FROM stage1_experiments WHERE id=?", (experiment_id,)).fetchone()
        conn.close()
        if not row:
            raise ValueError(f"experiment가 없습니다: {experiment_id}")
        return self._decode_experiment(row)

    def list_experiments(self, root_id: Optional[int] = None, limit: int = 200) -> list[dict]:
        conn = self.connect()
        if root_id:
            rows = conn.execute("SELECT * FROM stage1_experiments WHERE root_id=? ORDER BY id DESC LIMIT ?",
                                (root_id, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM stage1_experiments ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [self._decode_experiment(row) for row in rows]

    def lineage(self, experiment_id: int) -> list[dict]:
        output = []
        current = self.get_experiment(experiment_id)
        while current:
            output.append(current)
            parent_id = current.get("parent_id")
            current = self.get_experiment(parent_id) if parent_id else None
        return list(reversed(output))

    def promote(self, experiment_id: int):
        experiment = self.get_experiment(experiment_id)
        conn = self.connect()
        conn.execute("INSERT OR REPLACE INTO stage1_heads(root_id,experiment_id,updated_at) VALUES (?,?,?)",
                     (experiment["root_id"], experiment_id, utc_epoch()))
        conn.commit()
        conn.close()
        return experiment

    def current_head(self, root_id: int) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT experiment_id FROM stage1_heads WHERE root_id=?", (root_id,)).fetchone()
        conn.close()
        if not row:
            raise ValueError(f"root head가 없습니다: {root_id}")
        return self.get_experiment(int(row["experiment_id"]))

    @staticmethod
    def _decode_experiment(row) -> dict:
        item = dict(row)
        for key in ("parameter_json", "execution_json", "provenance_json", "result_json", "analysis_json"):
            item[key[:-5] if key.endswith("_json") else key] = json.loads(item.pop(key) or "{}")
        return item

    def create_study(self, parent_experiment_id: int, method: str, objective: str, seed: int, space: list[dict]) -> int:
        conn = self.connect()
        cur = conn.execute("""INSERT INTO stage1_search_studies(parent_experiment_id,method,objective,seed,space_json,created_at)
                              VALUES (?,?,?,?,?,?)""",
                           (parent_experiment_id, method, objective, seed, _json(space), utc_epoch()))
        study_id = int(cur.lastrowid)
        conn.commit(); conn.close()
        return study_id

    def cache_candidate(self, study_id: int, candidate_hash: str, parameters: dict, result: dict, score: float, status="OK"):
        conn = self.connect()
        conn.execute("""INSERT OR IGNORE INTO stage1_search_candidates(study_id,candidate_hash,parameter_json,result_json,score,status,created_at)
                        VALUES (?,?,?,?,?,?,?)""",
                     (study_id, candidate_hash, _json(parameters), _json(result), float(score), status, utc_epoch()))
        conn.commit(); conn.close()

    def finish_study(self, study_id: int, summary: dict):
        conn = self.connect(); conn.execute("UPDATE stage1_search_studies SET summary_json=? WHERE id=?", (_json(summary), study_id)); conn.commit(); conn.close()

    def study(self, study_id: int) -> dict:
        conn = self.connect()
        study = conn.execute("SELECT * FROM stage1_search_studies WHERE id=?", (study_id,)).fetchone()
        candidates = conn.execute("SELECT * FROM stage1_search_candidates WHERE study_id=? ORDER BY score DESC,id", (study_id,)).fetchall()
        conn.close()
        if not study:
            raise ValueError(f"study가 없습니다: {study_id}")
        output = dict(study)
        output["space"] = json.loads(output.pop("space_json"))
        output["summary"] = json.loads(output.pop("summary_json") or "{}")
        output["candidates"] = [{**dict(row), "parameters": json.loads(row["parameter_json"]), "result": json.loads(row["result_json"])} for row in candidates]
        for row in output["candidates"]:
            row.pop("parameter_json", None); row.pop("result_json", None)
        return output

    def create_episode(self, *, before_id: int, after_id: Optional[int], observation: str, hypothesis: str,
                       proposal: str, expected_effect: str, verdict: str, reason: str) -> int:
        conn = self.connect()
        cur = conn.execute("""INSERT INTO stage1_episodes(before_experiment_id,after_experiment_id,observation,hypothesis,proposal,
                            expected_effect,verdict,reason,created_at) VALUES (?,?,?,?,?,?,?,?,?)""",
                           (before_id, after_id, observation, hypothesis, proposal, expected_effect, verdict, reason, utc_epoch()))
        value = int(cur.lastrowid); conn.commit(); conn.close(); return value

    def episodes_for_root(self, root_id: int, limit: int = 50) -> list[dict]:
        conn = self.connect()
        rows = conn.execute("""SELECT ep.* FROM stage1_episodes ep
             JOIN stage1_experiments ex ON ex.id=ep.before_experiment_id
             WHERE ex.root_id=? ORDER BY ep.id DESC LIMIT ?""", (root_id, limit)).fetchall()
        conn.close(); return [dict(row) for row in rows]


class ResultAnalyzer:
    @staticmethod
    def analyze(result: Dict[str, Any], search_summary: Optional[Dict[str, Any]] = None) -> dict:
        metrics = result.get("metrics_numeric", {})
        diagnostics = result.get("diagnostics", {})
        closed = result.get("closed_trades", [])
        trade_count = int(metrics.get("closed_trade_count", len(closed)) or 0)
        total_return = float(metrics.get("total_return_pct", 0.0) or 0.0)
        mdd = abs(float(metrics.get("mdd_pct", 0.0) or 0.0))
        avg_mfe = float(diagnostics.get("average_mfe_pct", 0.0) or 0.0)
        avg_realized = float(diagnostics.get("average_realized_return_pct", 0.0) or 0.0)
        findings = []

        def add(code, evidence, confidence="RULE"):
            findings.append({"code": code, "evidence": evidence, "confidence": confidence})

        if trade_count == 0:
            add("NO_TRADES", {"signal_counts": diagnostics.get("signal_counts", {})})
        elif trade_count < 20:
            add("LOW_TRADE_COUNT", {"closed_trades": trade_count})
        if avg_mfe > 0 and avg_mfe - avg_realized >= max(1.0, avg_mfe * 0.45):
            add("EXIT_MFE_GIVEBACK", {"average_mfe_pct": avg_mfe, "average_realized_return_pct": avg_realized,
                                      "giveback_pct": avg_mfe - avg_realized})
        if mdd and total_return / mdd < 1.0:
            add("LOW_RETURN_TO_DRAWDOWN", {"return_pct": total_return, "mdd_pct": mdd})
        total_cost = float(metrics.get("total_cost", 0.0) or 0.0)
        gross = float(metrics.get("gross_profit", 0.0) or 0.0)
        if gross > 0 and total_cost / gross > 0.25:
            add("COST_SENSITIVE", {"total_cost": total_cost, "gross_profit": gross})
        if search_summary and search_summary.get("spike_ratio", 0) >= 2.0:
            add("PARAMETER_SPIKE", {"spike_ratio": search_summary["spike_ratio"], "neighborhood": search_summary.get("neighborhood", [])})
        if not findings:
            add("NO_DOMINANT_RULE_BASED_BOTTLENECK", {"return_pct": total_return, "mdd_pct": mdd, "closed_trades": trade_count})
        return {
            "schema": "stage1_analysis/v1",
            "findings": findings,
            "metrics": metrics,
            "signal_counts": diagnostics.get("signal_counts", {}),
            "rejections": diagnostics.get("rejections", {}),
            "trade_distribution": {
                "best_net_pnl": max((float(item.get("net_pnl", 0)) for item in closed), default=0.0),
                "worst_net_pnl": min((float(item.get("net_pnl", 0)) for item in closed), default=0.0),
                "average_mfe_pct": avg_mfe,
                "average_mae_pct": float(diagnostics.get("average_mae_pct", 0.0) or 0.0),
                "average_realized_return_pct": avg_realized,
            },
            "warning": "진단은 관찰 근거이며 전략 변경 명령이 아니다. 한 iteration에는 하나의 주요 구조 가설만 허용한다.",
        }


class ParameterSeeker:
    def __init__(self, store: StrategyFactoryStore):
        self.store = store

    @staticmethod
    def _score(result: dict, objective: str) -> float:
        metrics = result.get("metrics_numeric", {})
        ret = float(metrics.get("total_return_pct", 0.0) or 0.0)
        if objective == "MAX_RETURN":
            return ret
        if objective == "RETURN_DRAWDOWN":
            return ret - abs(float(metrics.get("mdd_pct", 0.0) or 0.0))
        if objective == "ROBUST_SCORE":
            mdd = abs(float(metrics.get("mdd_pct", 0.0) or 0.0))
            trades = float(metrics.get("closed_trade_count", 0.0) or 0.0)
            return ret - mdd * 0.75 + min(trades, 100.0) * 0.01
        raise ValueError(f"지원하지 않는 objective: {objective}")

    @staticmethod
    def _candidate_payload(base_dsl: str, base_settings: dict, specs: list[ParameterSpec], values: tuple[float, ...]):
        dsl_values, settings = {}, dict(base_settings)
        combined = {}
        for spec, value in zip(specs, values):
            combined[spec.name] = value
            if spec.target == "dsl":
                dsl_values[spec.name] = value
            else:
                settings[spec.name] = value
        return apply_dsl_parameters(base_dsl, dsl_values), settings, combined

    def run(self, *, parent_experiment: dict, market: dict, specs: list[ParameterSpec], method="grid",
            objective="MAX_RETURN", seed=42, max_candidates=5000) -> dict:
        method = method.lower()
        if method not in {"grid", "random"}:
            raise ValueError("초기 Stage 1 Seeker는 grid/random만 지원합니다.")
        if not specs:
            raise ValueError("parameter space가 비어 있습니다.")
        total_space = math.prod(len(spec.values) for spec in specs)
        rng = random.Random(seed)
        if method == "grid":
            if total_space > max_candidates:
                raise ValueError(f"grid candidate {total_space}개가 max_candidates={max_candidates}를 초과합니다.")
            combinations = list(itertools.product(*(spec.values for spec in specs)))
        else:
            count = min(total_space, max_candidates)
            if total_space <= max_candidates:
                combinations = list(itertools.product(*(spec.values for spec in specs)))
                rng.shuffle(combinations)
            else:
                seen = set(); combinations = []
                while len(combinations) < count:
                    item = tuple(rng.choice(spec.values) for spec in specs)
                    if item not in seen:
                        seen.add(item); combinations.append(item)
        study_id = self.store.create_study(parent_experiment["id"], method, objective, seed, [asdict(spec) for spec in specs])
        results = []
        duplicate = 0
        cache = {}
        provenance = parent_experiment["provenance"]
        for values in combinations:
            candidate_dsl, settings, parameters = self._candidate_payload(parent_experiment["dsl_code"], parent_experiment["execution"], specs, values)
            key = stable_hash({"dsl": candidate_dsl, "settings": settings, "data_hash": provenance.get("data_hash")})
            if key in cache:
                duplicate += 1
                result = cache[key]
            else:
                result = BacktestEngine.run(candidate_dsl, settings=settings, market=market, data_timeframe=provenance.get("timeframe"))
                cache[key] = result
            score = self._score(result, objective)
            summary_result = {"metrics_numeric": result.get("metrics_numeric", {}), "diagnostics": result.get("diagnostics", {})}
            self.store.cache_candidate(study_id, key, parameters, summary_result, score)
            results.append({"hash": key, "parameters": parameters, "dsl_code": candidate_dsl, "settings": settings,
                            "score": score, "result": result})
        results.sort(key=lambda item: (item["score"], item["hash"]), reverse=True)
        best = results[0]
        neighborhood = [item["score"] for item in results[:min(7, len(results))]]
        second = neighborhood[1] if len(neighborhood) > 1 else neighborhood[0]
        spike_ratio = abs(best["score"]) / max(1e-9, abs(second)) if abs(best["score"]) > abs(second) else 1.0
        summary = {
            "study_id": study_id,
            "method": method,
            "objective": objective,
            "seed": seed,
            "total_space": total_space,
            "evaluated": len(results),
            "duplicate": duplicate,
            "best_score": best["score"],
            "best_parameters": best["parameters"],
            "top": [{"score": item["score"], "parameters": item["parameters"],
                     "metrics": item["result"].get("metrics_numeric", {})} for item in results[:20]],
            "neighborhood": neighborhood,
            "spike_ratio": spike_ratio,
        }
        self.store.finish_study(study_id, summary)
        return {"summary": summary, "best": best, "results": results}


class StrategyFactory:
    def __init__(self, store: Optional[StrategyFactoryStore] = None):
        self.store = store or StrategyFactoryStore()
        self.seeker = ParameterSeeker(self.store)

    def validate_dsl(self, dsl_code: str, market: dict, timeframe: str):
        document = DSLParser.parse(dsl_code)
        if document.timeframe != timeframe:
            raise ValueError(f"DSL timeframe({document.timeframe})과 데이터 timeframe({timeframe})이 일치하지 않습니다.")
        # Compile once before any experiment is written.  This also performs semantic validation.
        numeric = {key: np.asarray(market[key], dtype=float) for key in ("open", "high", "low", "close", "volume")}
        size = len(numeric["close"])
        digits = [''.join(ch for ch in str(value) if ch.isdigit()) for value in market["time"]]
        numeric["date"] = np.asarray([float(value[:8] or index) for index, value in enumerate(digits)])
        numeric["time"] = np.asarray([float(value[8:14] or 0) for value in digits])
        DSLRuntime.compile(dsl_code, numeric)
        return document

    def baseline(self, *, intent: str, dsl_code: str, market: dict, instrument: str, timeframe: str,
                 source="inline", settings: Optional[dict] = None, adjustment_policy="unspecified",
                 session="regular", knowledge_cutoff="") -> dict:
        normalized, provenance = DataContract.normalize(market, instrument=instrument, timeframe=timeframe, source=source,
                                                        adjustment_policy=adjustment_policy, session=session,
                                                        knowledge_cutoff=knowledge_cutoff)
        document = self.validate_dsl(dsl_code, normalized, timeframe)
        result = BacktestEngine.run(dsl_code, settings=settings or {}, market=normalized, data_timeframe=timeframe)
        analysis = ResultAnalyzer.analyze(result)
        experiment = self.store.create_experiment(parent_id=None, operation="BASELINE", strategy_name=document.name,
            intent=intent, dsl_code=dsl_code, parameters={}, execution=settings or {}, provenance=asdict(provenance),
            result=result, analysis=analysis)
        return experiment

    def seek(self, *, experiment_id: int, market: dict, parameter_specs: list[dict], method="grid",
             objective="MAX_RETURN", seed=42, max_candidates=5000, promote=False) -> dict:
        parent = self.store.get_experiment(experiment_id)
        normalized, provenance = DataContract.normalize(market,
            instrument=parent["provenance"]["instrument"], timeframe=parent["provenance"]["timeframe"],
            source=parent["provenance"]["source"], adjustment_policy=parent["provenance"].get("adjustment_policy", "unspecified"),
            session=parent["provenance"].get("session", "regular"), knowledge_cutoff=parent["provenance"].get("knowledge_cutoff", ""))
        if provenance.data_hash != parent["provenance"]["data_hash"]:
            raise ValueError("Experiment와 현재 market data hash가 다릅니다.")
        specs = [ParameterSpec.from_payload(item) for item in parameter_specs]
        study = self.seeker.run(parent_experiment=parent, market=normalized, specs=specs, method=method,
                                objective=objective, seed=seed, max_candidates=max_candidates)
        best = study["best"]
        analysis = ResultAnalyzer.analyze(best["result"], study["summary"])
        child = self.store.create_experiment(parent_id=parent["id"], operation="SEEKER_BEST",
            strategy_name=parent["strategy_name"], intent=parent["intent"], dsl_code=best["dsl_code"],
            parameters=best["parameters"], execution=best["settings"], provenance=parent["provenance"],
            result=best["result"], analysis=analysis)
        if promote:
            self.store.promote(child["id"])
        return {"experiment": child, "study": study["summary"]}

    def feedback_package(self, experiment_id: int, *, target_return: Optional[float] = None) -> dict:
        current = self.store.get_experiment(experiment_id)
        lineage = self.store.lineage(experiment_id)
        episodes = self.store.episodes_for_root(current["root_id"], 30)
        baseline = lineage[0]
        prompt = f"""당신은 Quant DSL 전략 개선 분석가입니다.

[절대 계약]
- 아래 DSL의 의미를 분석하고 관찰 evidence로 설명 가능한 주요 구조 가설 하나만 수정합니다.
- 숫자 brute-force 탐색은 Parameter Seeker의 책임이므로 LLM이 대신하지 않습니다.
- Parser/Backtest/Broker/검증기 변경을 제안하지 않습니다.
- 미래정보/lookahead를 사용하지 않습니다.
- 결과는 Problem observation, Hypothesis, Expected effect, 전체 revised DSL 순서로 제공합니다.

[원래 사용자 의도]
{current['intent']}

[현재 DSL]
```dsl
{current['dsl_code']}
```

[Baseline]
{_json(baseline['result'].get('metrics_numeric', {}))}

[현재 결과]
{_json(current['result'].get('metrics_numeric', {}))}

[현재 분석]
{json.dumps(current['analysis'], ensure_ascii=False, indent=2)}

[현재 파라미터]
{_json(current['parameter'])}

[최근 accepted/rejected improvement episodes]
{json.dumps(episodes, ensure_ascii=False, indent=2)}

[목표수익률]
{target_return if target_return is not None else '미지정'}
"""
        return {"schema": "stage1_feedback/v1", "experiment_id": experiment_id, "root_id": current["root_id"],
                "prompt": prompt, "analysis": current["analysis"], "target_return": target_return,
                "episodes": episodes}

    def apply_llm_response(self, *, experiment_id: int, llm_response: str, market: dict,
                           hypothesis: str = "", expected_effect: str = "", promote=False) -> dict:
        parent = self.store.get_experiment(experiment_id)
        dsl_code = extract_dsl(llm_response)
        normalized, provenance = DataContract.normalize(market,
            instrument=parent["provenance"]["instrument"], timeframe=parent["provenance"]["timeframe"],
            source=parent["provenance"]["source"], adjustment_policy=parent["provenance"].get("adjustment_policy", "unspecified"),
            session=parent["provenance"].get("session", "regular"), knowledge_cutoff=parent["provenance"].get("knowledge_cutoff", ""))
        if provenance.data_hash != parent["provenance"]["data_hash"]:
            raise ValueError("Experiment와 현재 market data hash가 다릅니다.")
        self.validate_dsl(dsl_code, normalized, parent["provenance"]["timeframe"])
        result = BacktestEngine.run(dsl_code, settings=parent["execution"], market=normalized,
                                    data_timeframe=parent["provenance"]["timeframe"])
        analysis = ResultAnalyzer.analyze(result)
        child = self.store.create_experiment(parent_id=parent["id"], operation="LLM_STRUCTURAL",
            strategy_name=parent["strategy_name"], intent=parent["intent"], dsl_code=dsl_code,
            parameters={}, execution=parent["execution"], provenance=parent["provenance"], result=result,
            analysis=analysis, llm_response=llm_response, hypothesis=hypothesis, expected_effect=expected_effect)
        before_return = float(parent["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        after_return = float(result.get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        verdict = "ACCEPTED_IMPROVEMENT" if after_return > before_return else "REJECTED_NO_GAIN"
        reason = f"return {before_return:.4f}% -> {after_return:.4f}%"
        episode_id = self.store.create_episode(before_id=parent["id"], after_id=child["id"],
            observation=json.dumps(parent["analysis"].get("findings", []), ensure_ascii=False),
            hypothesis=hypothesis, proposal=dsl_code, expected_effect=expected_effect, verdict=verdict, reason=reason)
        if promote and verdict == "ACCEPTED_IMPROVEMENT":
            self.store.promote(child["id"])
        return {"experiment": child, "episode_id": episode_id, "verdict": verdict, "reason": reason}

    @staticmethod
    def chart_audit(experiment: dict) -> dict:
        result = experiment["result"]
        return {
            "schema": "stage1_chart_audit/v1",
            "experiment_id": experiment["id"],
            "strategy_name": experiment["strategy_name"],
            "candles": result.get("candles", []),
            "equity_curve": result.get("equity_curve", []),
            "indicators": result.get("indicators", []),
            "markers": result.get("markers", []),
            "executions": result.get("trades", []),
            "closed_trades": result.get("closed_trades", []),
            "metrics": result.get("metrics", {}),
            "diagnostics": result.get("diagnostics", {}),
        }

    @staticmethod
    def stop_state(experiment: dict, *, target_return: float, iteration: int, iteration_limit: int,
                   backtests_used: int = 0, backtest_budget: int = 50000, consecutive_no_improvement: int = 0,
                   no_improvement_limit: int = 5, plateau=False, engine_blocked=False) -> str:
        if engine_blocked:
            return "DATA_OR_ENGINE_BLOCKED"
        achieved = float(experiment["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        if achieved >= target_return:
            return "TARGET_REACHED"
        if iteration >= iteration_limit or backtests_used >= backtest_budget:
            return "ITERATION_LIMIT"
        if plateau or consecutive_no_improvement >= no_improvement_limit:
            return "PLATEAU"
        return "CONTINUE"

    def methodology_summary(self, root_id: int) -> dict:
        experiments = list(reversed(self.store.list_experiments(root_id=root_id, limit=1000)))
        if not experiments:
            raise ValueError("methodology 대상 experiment가 없습니다.")
        baseline = next((item for item in experiments if item["operation"] == "BASELINE"), experiments[0])
        seeker = [item for item in experiments if item["operation"] == "SEEKER_BEST"]
        llm = [item for item in experiments if item["operation"] == "LLM_STRUCTURAL"]
        ret = lambda item: float(item["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        baseline_return = ret(baseline)
        seeker_best = max((ret(item) for item in seeker), default=baseline_return)
        llm_best = max((ret(item) for item in llm), default=seeker_best)
        episodes = self.store.episodes_for_root(root_id, 10000)
        accepted = sum(1 for item in episodes if item["verdict"] == "ACCEPTED_IMPROVEMENT")
        return {
            "schema": "stage1_methodology/v1",
            "root_id": root_id,
            "A_baseline_return_pct": baseline_return,
            "B_seeker_best_return_pct": seeker_best,
            "C_llm_loop_best_return_pct": llm_best,
            "seeker_increment_pct": seeker_best - baseline_return,
            "llm_increment_over_seeker_pct": llm_best - seeker_best,
            "structural_iterations": len(llm),
            "accepted_structural_iterations": accepted,
            "structural_success_rate": accepted / len(episodes) if episodes else 0.0,
            "episodes": len(episodes),
            "claim": "descriptive_only_until_OOS_and_multi-strategy_methodology_validation",
        }
