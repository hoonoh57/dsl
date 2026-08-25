"""Immutable scenario/run persistence for multi-layer tactical research."""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from core.db import DB_PATH


def _json_safe(value: Any):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class TacticalScenarioStore:
    """Append-only scenario/run store with a separate explicit mutable head."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path is not None else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tactical_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_hash TEXT NOT NULL UNIQUE,
                unit_id TEXT NOT NULL,
                regime_id TEXT NOT NULL,
                definition_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tactical_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                run_hash TEXT NOT NULL UNIQUE,
                result_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY(scenario_id) REFERENCES tactical_scenarios(id)
            );
            CREATE TABLE IF NOT EXISTS tactical_heads (
                unit_id TEXT PRIMARY KEY,
                run_id INTEGER NOT NULL,
                updated_at REAL NOT NULL,
                FOREIGN KEY(run_id) REFERENCES tactical_runs(id)
            );
            """
        )
        conn.commit()
        conn.close()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_scenario(self, definition: dict) -> dict:
        if not isinstance(definition, dict):
            raise ValueError("scenario definition은 dict여야 합니다.")
        unit = definition.get("unit") or {}
        regime = definition.get("regime") or {}
        unit_id = str(unit.get("unit_id") or "").strip()
        regime_id = str(regime.get("regime_id") or "").strip()
        if not unit_id or not regime_id:
            raise ValueError("scenario definition에는 unit.unit_id와 regime.regime_id가 필요합니다.")
        hash_payload = {key: value for key, value in definition.items() if key != "scenario_hash"}
        expected_hash = _hash(hash_payload)
        claimed_hash = str(definition.get("scenario_hash") or "").strip()
        if claimed_hash and claimed_hash != expected_hash:
            raise ValueError("scenario_hash가 definition 내용과 일치하지 않습니다.")
        scenario_hash = expected_hash
        stored_definition = dict(hash_payload)
        stored_definition["scenario_hash"] = scenario_hash
        payload = _canonical_json(stored_definition)
        conn = self.connect()
        existing = conn.execute(
            "SELECT * FROM tactical_scenarios WHERE scenario_hash=?", (scenario_hash,)
        ).fetchone()
        if existing:
            current = dict(existing)
            conn.close()
            if current["definition_json"] != payload:
                raise ValueError("동일 scenario_hash에 다른 definition을 저장할 수 없습니다.")
            return self._scenario_row(current)
        cur = conn.execute(
            "INSERT INTO tactical_scenarios(scenario_hash,unit_id,regime_id,definition_json,created_at) VALUES (?,?,?,?,?)",
            (scenario_hash, unit_id, regime_id, payload, time.time()),
        )
        conn.commit()
        scenario_id = int(cur.lastrowid)
        conn.close()
        return self.get_scenario(scenario_id)

    def record_run(self, scenario_id: int, result: dict) -> dict:
        scenario = self.get_scenario(scenario_id)
        if str(result.get("scenario_hash") or "") != scenario["scenario_hash"]:
            raise ValueError("run의 scenario_hash가 저장된 scenario와 일치하지 않습니다.")
        run_hash = str(result.get("run_hash") or "").strip()
        if not run_hash:
            raise ValueError("COMPLETED tactical run에는 run_hash가 필요합니다.")
        payload = _canonical_json(result)
        conn = self.connect()
        existing = conn.execute("SELECT * FROM tactical_runs WHERE run_hash=?", (run_hash,)).fetchone()
        if existing:
            current = dict(existing)
            conn.close()
            if int(current["scenario_id"]) != int(scenario_id) or current["result_json"] != payload:
                raise ValueError("동일 run_hash에 다른 tactical result를 저장할 수 없습니다.")
            return self._run_row(current)
        cur = conn.execute(
            "INSERT INTO tactical_runs(scenario_id,run_hash,result_json,created_at) VALUES (?,?,?,?)",
            (int(scenario_id), run_hash, payload, time.time()),
        )
        conn.commit()
        run_id = int(cur.lastrowid)
        conn.close()
        return self.get_run(run_id)

    def promote(self, run_id: int) -> dict:
        run = self.get_run(run_id)
        scenario = self.get_scenario(run["scenario_id"])
        conn = self.connect()
        conn.execute(
            "INSERT INTO tactical_heads(unit_id,run_id,updated_at) VALUES (?,?,?) "
            "ON CONFLICT(unit_id) DO UPDATE SET run_id=excluded.run_id, updated_at=excluded.updated_at",
            (scenario["unit_id"], int(run_id), time.time()),
        )
        conn.commit()
        conn.close()
        return self.get_head(scenario["unit_id"])

    def get_head(self, unit_id: str) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute("SELECT * FROM tactical_heads WHERE unit_id=?", (str(unit_id),)).fetchone()
        conn.close()
        if not row:
            return None
        item = dict(row)
        item["run"] = self.get_run(int(item["run_id"]))
        return item

    def get_scenario(self, scenario_id: int) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT * FROM tactical_scenarios WHERE id=?", (int(scenario_id),)).fetchone()
        conn.close()
        if not row:
            raise KeyError(f"tactical scenario not found: {scenario_id}")
        return self._scenario_row(dict(row))

    def get_run(self, run_id: int) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT * FROM tactical_runs WHERE id=?", (int(run_id),)).fetchone()
        conn.close()
        if not row:
            raise KeyError(f"tactical run not found: {run_id}")
        return self._run_row(dict(row))

    def list_scenarios(self, *, unit_id: Optional[str] = None, limit: int = 200) -> list[dict]:
        limit = min(max(int(limit), 1), 10000)
        conn = self.connect()
        if unit_id:
            rows = conn.execute(
                "SELECT * FROM tactical_scenarios WHERE unit_id=? ORDER BY id DESC LIMIT ?",
                (str(unit_id), limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tactical_scenarios ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [self._scenario_row(dict(row)) for row in rows]

    @staticmethod
    def _scenario_row(row: dict) -> dict:
        item = dict(row)
        item["definition"] = json.loads(item.pop("definition_json"))
        return item

    @staticmethod
    def _run_row(row: dict) -> dict:
        item = dict(row)
        item["result"] = json.loads(item.pop("result_json"))
        return item
