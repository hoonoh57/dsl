"""Immutable experience ledger for evolving micro-warrior generations."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping, Optional

from core.db import DB_PATH


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _json(value: Any) -> str:
    return json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class TacticalEvolutionStore:
    """Append-only profiles/failures/generations/decisions plus explicit family head."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path is not None else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS evolution_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                run_hash TEXT NOT NULL UNIQUE,
                candidate_hash TEXT NOT NULL,
                case_set_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evolution_failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                failure_hash TEXT NOT NULL UNIQUE,
                profile_run_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evolution_generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                generation_hash TEXT NOT NULL UNIQUE,
                generation_index INTEGER NOT NULL,
                parent_generation_hash TEXT NOT NULL,
                candidate_hash TEXT NOT NULL,
                profile_run_hash TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(family_id, generation_index)
            );
            CREATE TABLE IF NOT EXISTS evolution_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                decision_hash TEXT NOT NULL UNIQUE,
                parent_generation_hash TEXT NOT NULL,
                child_candidate_hash TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evolution_heads (
                family_id TEXT PRIMARY KEY,
                generation_hash TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )
        conn.commit()
        conn.close()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _require_text(value: Any, label: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"{label}가 필요합니다.")
        return text

    def record_profile(self, family_id: str, profile: Mapping[str, Any]) -> dict:
        family_id = self._require_text(family_id, "family_id")
        if str(profile.get("schema") or "") != "tactical_discovery/v1":
            raise ValueError("evolution profile은 tactical_discovery/v1이어야 합니다.")
        run_hash = self._require_text(profile.get("run_hash"), "profile.run_hash")
        candidate_hash = self._require_text((profile.get("candidate") or {}).get("candidate_hash"), "profile.candidate_hash")
        case_set_hash = self._require_text(profile.get("case_set_hash"), "profile.case_set_hash")
        payload = _json(profile)
        conn = self.connect()
        existing = conn.execute("SELECT * FROM evolution_profiles WHERE run_hash=?", (run_hash,)).fetchone()
        if existing:
            item = dict(existing); conn.close()
            if item["family_id"] != family_id or item["payload_json"] != payload:
                raise ValueError("동일 run_hash에 다른 evolution profile을 저장할 수 없습니다.")
            return self._row(item)
        cur = conn.execute(
            "INSERT INTO evolution_profiles(family_id,run_hash,candidate_hash,case_set_hash,payload_json,created_at) VALUES (?,?,?,?,?,?)",
            (family_id, run_hash, candidate_hash, case_set_hash, payload, time.time()),
        )
        conn.commit(); row_id = int(cur.lastrowid); conn.close()
        return self.get_profile(row_id)

    def record_failure(self, family_id: str, report: Mapping[str, Any]) -> dict:
        family_id = self._require_text(family_id, "family_id")
        if str(report.get("schema") or "") != "tactical_failure/v1":
            raise ValueError("evolution failure는 tactical_failure/v1이어야 합니다.")
        failure_hash = self._require_text(report.get("failure_hash"), "failure_hash")
        run_hash = self._require_text(report.get("profile_run_hash"), "profile_run_hash")
        conn = self.connect()
        parent = conn.execute("SELECT family_id FROM evolution_profiles WHERE run_hash=?", (run_hash,)).fetchone()
        if not parent:
            conn.close(); raise ValueError("failure의 parent profile이 먼저 저장되어야 합니다.")
        if str(parent["family_id"]) != family_id:
            conn.close(); raise ValueError("failure family_id가 parent profile과 다릅니다.")
        payload = _json(report)
        existing = conn.execute("SELECT * FROM evolution_failures WHERE failure_hash=?", (failure_hash,)).fetchone()
        if existing:
            item = dict(existing); conn.close()
            if item["payload_json"] != payload or item["family_id"] != family_id:
                raise ValueError("동일 failure_hash에 다른 report를 저장할 수 없습니다.")
            return self._row(item)
        cur = conn.execute(
            "INSERT INTO evolution_failures(family_id,failure_hash,profile_run_hash,payload_json,created_at) VALUES (?,?,?,?,?)",
            (family_id, failure_hash, run_hash, payload, time.time()),
        )
        conn.commit(); row_id = int(cur.lastrowid); conn.close()
        return self.get_failure(row_id)

    def record_generation(self, generation: Any) -> dict:
        payload_obj = asdict(generation) if is_dataclass(generation) else dict(generation)
        family_id = self._require_text(payload_obj.get("family_id"), "generation.family_id")
        generation_hash = self._require_text(payload_obj.get("generation_hash"), "generation_hash")
        candidate_hash = self._require_text(payload_obj.get("candidate_hash"), "candidate_hash")
        run_hash = self._require_text(payload_obj.get("profile_run_hash"), "profile_run_hash")
        generation_index = int(payload_obj.get("generation_index"))
        parent_hash = str(payload_obj.get("parent_generation_hash") or "")
        payload = _json(payload_obj)
        conn = self.connect()
        profile = conn.execute("SELECT family_id,candidate_hash FROM evolution_profiles WHERE run_hash=?", (run_hash,)).fetchone()
        if not profile:
            conn.close(); raise ValueError("generation profile이 먼저 저장되어야 합니다.")
        if str(profile["family_id"]) != family_id or str(profile["candidate_hash"]) != candidate_hash:
            conn.close(); raise ValueError("generation identity가 저장된 profile과 다릅니다.")
        if generation_index == 0 and parent_hash:
            conn.close(); raise ValueError("Generation 0은 parent_generation_hash가 없어야 합니다.")
        if generation_index > 0:
            parent = conn.execute(
                "SELECT family_id,generation_index FROM evolution_generations WHERE generation_hash=?",
                (parent_hash,),
            ).fetchone()
            if not parent or str(parent["family_id"]) != family_id or int(parent["generation_index"]) != generation_index - 1:
                conn.close(); raise ValueError("generation parent lineage가 올바르지 않습니다.")
        existing = conn.execute("SELECT * FROM evolution_generations WHERE generation_hash=?", (generation_hash,)).fetchone()
        if existing:
            item = dict(existing); conn.close()
            if item["payload_json"] != payload:
                raise ValueError("동일 generation_hash에 다른 generation을 저장할 수 없습니다.")
            return self._row(item)
        cur = conn.execute(
            "INSERT INTO evolution_generations(family_id,generation_hash,generation_index,parent_generation_hash,candidate_hash,profile_run_hash,payload_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (family_id, generation_hash, generation_index, parent_hash, candidate_hash, run_hash, payload, time.time()),
        )
        conn.commit(); row_id = int(cur.lastrowid); conn.close()
        return self.get_generation(row_id)

    def record_decision(self, family_id: str, decision: Mapping[str, Any]) -> dict:
        family_id = self._require_text(family_id, "family_id")
        if str(decision.get("schema") or "") != "tactical_evolution/v1":
            raise ValueError("decision은 tactical_evolution/v1이어야 합니다.")
        decision_hash = self._require_text(decision.get("decision_hash"), "decision_hash")
        parent_hash = self._require_text(decision.get("parent_generation_hash"), "parent_generation_hash")
        child_candidate_hash = self._require_text(decision.get("child_candidate_hash"), "child_candidate_hash")
        skill_id = self._require_text(decision.get("skill_id"), "skill_id")
        status = self._require_text(decision.get("decision"), "decision")
        if status not in {"ACCEPT", "REJECT", "REVIEW"}:
            raise ValueError(f"알 수 없는 evolution decision: {status}")
        payload = _json(decision)
        conn = self.connect()
        parent = conn.execute("SELECT family_id FROM evolution_generations WHERE generation_hash=?", (parent_hash,)).fetchone()
        if not parent or str(parent["family_id"]) != family_id:
            conn.close(); raise ValueError("decision parent generation이 저장되어 있지 않습니다.")
        existing = conn.execute("SELECT * FROM evolution_decisions WHERE decision_hash=?", (decision_hash,)).fetchone()
        if existing:
            item = dict(existing); conn.close()
            if item["payload_json"] != payload:
                raise ValueError("동일 decision_hash에 다른 decision을 저장할 수 없습니다.")
            return self._row(item)
        cur = conn.execute(
            "INSERT INTO evolution_decisions(family_id,decision_hash,parent_generation_hash,child_candidate_hash,skill_id,decision,payload_json,created_at) VALUES (?,?,?,?,?,?,?,?)",
            (family_id, decision_hash, parent_hash, child_candidate_hash, skill_id, status, payload, time.time()),
        )
        conn.commit(); row_id = int(cur.lastrowid); conn.close()
        return self.get_decision(row_id)

    def promote(self, family_id: str, generation_hash: str) -> dict:
        family_id = self._require_text(family_id, "family_id")
        generation_hash = self._require_text(generation_hash, "generation_hash")
        conn = self.connect()
        row = conn.execute(
            "SELECT family_id FROM evolution_generations WHERE generation_hash=?", (generation_hash,)
        ).fetchone()
        if not row or str(row["family_id"]) != family_id:
            conn.close(); raise ValueError("promote할 generation이 family에 존재하지 않습니다.")
        conn.execute(
            "INSERT INTO evolution_heads(family_id,generation_hash,updated_at) VALUES (?,?,?) "
            "ON CONFLICT(family_id) DO UPDATE SET generation_hash=excluded.generation_hash, updated_at=excluded.updated_at",
            (family_id, generation_hash, time.time()),
        )
        conn.commit(); conn.close()
        return self.get_head(family_id)

    def get_head(self, family_id: str) -> Optional[dict]:
        conn = self.connect()
        row = conn.execute("SELECT * FROM evolution_heads WHERE family_id=?", (str(family_id),)).fetchone()
        conn.close()
        if not row:
            return None
        item = dict(row)
        item["generation"] = self.get_generation_by_hash(item["generation_hash"])
        return item

    def get_profile(self, row_id: int) -> dict:
        return self._get("evolution_profiles", row_id)

    def get_failure(self, row_id: int) -> dict:
        return self._get("evolution_failures", row_id)

    def get_generation(self, row_id: int) -> dict:
        return self._get("evolution_generations", row_id)

    def get_decision(self, row_id: int) -> dict:
        return self._get("evolution_decisions", row_id)

    def get_generation_by_hash(self, generation_hash: str) -> dict:
        conn = self.connect()
        row = conn.execute("SELECT * FROM evolution_generations WHERE generation_hash=?", (str(generation_hash),)).fetchone()
        conn.close()
        if not row:
            raise KeyError(f"evolution generation not found: {generation_hash}")
        return self._row(dict(row))

    def _get(self, table: str, row_id: int) -> dict:
        if table not in {"evolution_profiles", "evolution_failures", "evolution_generations", "evolution_decisions"}:
            raise ValueError("invalid evolution table")
        conn = self.connect()
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (int(row_id),)).fetchone()
        conn.close()
        if not row:
            raise KeyError(f"{table} not found: {row_id}")
        return self._row(dict(row))

    @staticmethod
    def _row(row: dict) -> dict:
        item = dict(row)
        if "payload_json" in item:
            item["payload"] = json.loads(item.pop("payload_json"))
        return item
