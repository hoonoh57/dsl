"""Read-only evolution lineage/evidence projection for E7.

This layer sits above ``TacticalEvolutionStore``.  It does not mutate DSL,
Backtest, Broker or family-head authority.  It adds append-only storage for E6
validation-arena evidence and projects profiles/failures/decisions/generations
into a deterministic UI-facing skill-tree document.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
import math
import time
from typing import Any, Mapping

from core.tactical_evolution_store import TacticalEvolutionStore


SCHEMA_VERSION = "tactical_evolution_lineage/v1"
VALIDATION_SCHEMA = "tactical_validation_arena/v1"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    return value


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _payload(row: Mapping[str, Any]) -> dict[str, Any]:
    value = row.get("payload")
    if not isinstance(value, Mapping):
        raise ValueError("evolution lineage row payload가 없습니다.")
    return dict(value)


def _required_text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label}가 필요합니다.")
    return text


class TacticalEvolutionLineage:
    """Append E6 evidence and expose a deterministic, read-only lineage view."""

    def __init__(self, store: TacticalEvolutionStore):
        self.store = store
        conn = self.store.connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evolution_validation_arenas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id TEXT NOT NULL,
                arena_hash TEXT NOT NULL UNIQUE,
                parent_generation_hash TEXT NOT NULL,
                child_candidate_hash TEXT NOT NULL,
                skill_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()

    def record_validation(self, family_id: str, arena: Mapping[str, Any]) -> dict[str, Any]:
        """Append one E6 validation result without promoting a family head."""
        family_id = _required_text(family_id, "family_id")
        if str(arena.get("schema") or "") != VALIDATION_SCHEMA:
            raise ValueError("validation evidence는 tactical_validation_arena/v1이어야 합니다.")
        if str(arena.get("family_id") or "") != family_id:
            raise ValueError("validation evidence family_id가 요청 family와 다릅니다.")
        arena_hash = _required_text(arena.get("arena_hash"), "arena_hash")
        parent_hash = _required_text(arena.get("parent_generation_hash"), "parent_generation_hash")
        child_hash = _required_text(arena.get("child_candidate_hash"), "child_candidate_hash")
        skill_id = _required_text(arena.get("skill_id"), "skill_id")
        decision = _required_text(arena.get("decision"), "decision")
        if decision not in {"ACCEPT", "REJECT", "REVIEW"}:
            raise ValueError(f"알 수 없는 validation decision: {decision}")
        promotion_eligible = bool(arena.get("promotion_eligible"))
        if promotion_eligible != (decision == "ACCEPT"):
            raise ValueError("promotion_eligible은 validation ACCEPT와 정확히 일치해야 합니다.")

        parent = self.store.get_generation_by_hash(parent_hash)
        if str(parent.get("family_id") or "") != family_id:
            raise ValueError("validation parent generation family_id가 다릅니다.")

        accepted = arena.get("accepted_generation")
        if decision == "ACCEPT":
            if accepted is None:
                raise ValueError("ACCEPT validation에는 accepted_generation evidence가 필요합니다.")
            accepted_payload = asdict(accepted) if is_dataclass(accepted) else dict(accepted)
            if str(accepted_payload.get("parent_generation_hash") or "") != parent_hash:
                raise ValueError("accepted_generation parent가 validation parent와 다릅니다.")
            if str(accepted_payload.get("candidate_hash") or "") != child_hash:
                raise ValueError("accepted_generation candidate가 validation child와 다릅니다.")
        elif accepted is not None:
            raise ValueError("REJECT/REVIEW validation에는 accepted_generation이 없어야 합니다.")

        payload_obj = _json_safe(dict(arena))
        payload_json = json.dumps(
            payload_obj,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        conn = self.store.connect()
        existing = conn.execute(
            "SELECT * FROM evolution_validation_arenas WHERE arena_hash=?",
            (arena_hash,),
        ).fetchone()
        if existing:
            item = dict(existing)
            conn.close()
            if item["family_id"] != family_id or item["payload_json"] != payload_json:
                raise ValueError("동일 arena_hash에 다른 validation evidence를 저장할 수 없습니다.")
            return self._validation_row(item)
        cur = conn.execute(
            "INSERT INTO evolution_validation_arenas("
            "family_id,arena_hash,parent_generation_hash,child_candidate_hash,skill_id,decision,payload_json,created_at"
            ") VALUES (?,?,?,?,?,?,?,?)",
            (family_id, arena_hash, parent_hash, child_hash, skill_id, decision, payload_json, time.time()),
        )
        conn.commit()
        row_id = int(cur.lastrowid)
        row = conn.execute("SELECT * FROM evolution_validation_arenas WHERE id=?", (row_id,)).fetchone()
        conn.close()
        return self._validation_row(dict(row))

    @staticmethod
    def _validation_row(row: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json"))
        return item

    def _table_rows(self, table: str, family_id: str, order_by: str) -> list[dict[str, Any]]:
        allowed = {
            "evolution_profiles",
            "evolution_failures",
            "evolution_generations",
            "evolution_decisions",
        }
        if table not in allowed:
            raise ValueError("invalid evolution lineage table")
        conn = self.store.connect()
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE family_id=? ORDER BY {order_by}",
            (family_id,),
        ).fetchall()
        conn.close()
        output = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            output.append(item)
        return output

    def _validation_rows(self, family_id: str) -> list[dict[str, Any]]:
        conn = self.store.connect()
        rows = conn.execute(
            "SELECT * FROM evolution_validation_arenas WHERE family_id=? ORDER BY id",
            (family_id,),
        ).fetchall()
        conn.close()
        return [self._validation_row(dict(row)) for row in rows]

    def _head_hash(self, family_id: str) -> str:
        conn = self.store.connect()
        row = conn.execute(
            "SELECT generation_hash FROM evolution_heads WHERE family_id=?",
            (family_id,),
        ).fetchone()
        conn.close()
        return str(row["generation_hash"]) if row else ""

    @staticmethod
    def _profile_summary(profile: Mapping[str, Any]) -> dict[str, Any]:
        aggregate = dict(profile.get("aggregate") or {})
        return {
            "cases": int(aggregate.get("cases") or 0),
            "active_cases": int(aggregate.get("active_cases") or 0),
            "no_trade_cases": int(aggregate.get("no_trade_cases") or 0),
            "average_return_pct": aggregate.get("average_return_pct"),
            "median_return_pct": aggregate.get("median_return_pct"),
            "profitable_case_rate": aggregate.get("profitable_case_rate"),
            "worst_mdd_pct": aggregate.get("worst_mdd_pct"),
            "worst_case_return_pct": aggregate.get("worst_case_return_pct"),
            "total_cost": aggregate.get("total_cost"),
            "average_mfe_giveback_pct": aggregate.get("average_mfe_giveback_pct"),
            "top1_positive_return_concentration": aggregate.get("top1_positive_return_concentration"),
        }

    @staticmethod
    def _validation_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
        partitions = []
        for row in payload.get("partitions") or ():
            adjudication = dict(row.get("adjudication") or {})
            partitions.append(
                {
                    "partition_id": str(row.get("partition_id") or ""),
                    "role": str(row.get("role") or ""),
                    "status": str(adjudication.get("status") or ""),
                    "violations": tuple(adjudication.get("violations") or adjudication.get("survival_violations") or ()),
                }
            )
        return {
            "decision": str(payload.get("decision") or ""),
            "promotion_eligible": bool(payload.get("promotion_eligible")),
            "holdout_failures": tuple(payload.get("holdout_failures") or ()),
            "selection_policy": str(payload.get("selection_policy") or ""),
            "partitions": tuple(partitions),
        }

    def build(self, family_id: str) -> dict[str, Any]:
        """Build one deterministic read-only family skill-tree/evidence document."""
        family_id = _required_text(family_id, "family_id")
        generations = self._table_rows("evolution_generations", family_id, "generation_index")
        profiles = self._table_rows("evolution_profiles", family_id, "id")
        failures = self._table_rows("evolution_failures", family_id, "id")
        decisions = self._table_rows("evolution_decisions", family_id, "id")
        validations = self._validation_rows(family_id)
        head_hash = self._head_hash(family_id)

        profile_by_run = {str(row["run_hash"]): row for row in profiles}
        failure_by_hash = {str(row["failure_hash"]): row for row in failures}
        generation_by_hash = {str(row["generation_hash"]): row for row in generations}
        if head_hash and head_hash not in generation_by_hash:
            raise ValueError("evolution head가 lineage generation에 존재하지 않습니다.")

        previous_payload: dict[str, Any] | None = None
        nodes: list[dict[str, Any]] = []
        for expected_index, row in enumerate(generations):
            payload = _payload(row)
            generation_index = int(payload.get("generation_index"))
            if generation_index != expected_index:
                raise ValueError("evolution generation_index가 0부터 연속이어야 합니다.")
            generation_hash = _required_text(payload.get("generation_hash"), "generation_hash")
            run_hash = _required_text(payload.get("profile_run_hash"), "profile_run_hash")
            candidate_hash = _required_text(payload.get("candidate_hash"), "candidate_hash")
            profile_row = profile_by_run.get(run_hash)
            if profile_row is None:
                raise ValueError("lineage generation profile이 없습니다.")
            profile = _payload(profile_row)
            if str((profile.get("candidate") or {}).get("candidate_hash") or "") != candidate_hash:
                raise ValueError("lineage generation candidate와 profile candidate가 다릅니다.")

            acquired = tuple(str(item) for item in payload.get("acquired_skills") or ())
            parent_hash = str(payload.get("parent_generation_hash") or "")
            new_skill = ""
            if expected_index == 0:
                if parent_hash or acquired:
                    raise ValueError("Generation 0 lineage contract가 올바르지 않습니다.")
            else:
                if previous_payload is None:
                    raise ValueError("lineage parent payload가 없습니다.")
                if parent_hash != str(previous_payload.get("generation_hash") or ""):
                    raise ValueError("lineage parent_generation_hash가 직전 generation과 다릅니다.")
                parent_skills = tuple(str(item) for item in previous_payload.get("acquired_skills") or ())
                if acquired[: len(parent_skills)] != parent_skills or len(acquired) != len(parent_skills) + 1:
                    raise ValueError("lineage accepted generation은 정확히 one-skill progression이어야 합니다.")
                new_skill = acquired[-1]

            acquired_failure_hash = str(payload.get("acquired_from_failure_hash") or "")
            failure_payload = None
            failure_tags: tuple[str, ...] = ()
            if acquired_failure_hash:
                failure_row = failure_by_hash.get(acquired_failure_hash)
                if failure_row is None:
                    raise ValueError("generation acquired failure evidence가 store에 없습니다.")
                failure_payload = _payload(failure_row)
                failure_tags = tuple(
                    str(cluster.get("failure_tag") or "")
                    for cluster in failure_payload.get("clusters") or ()
                    if str(cluster.get("failure_tag") or "")
                )

            accepted_decisions = [
                item for item in decisions
                if str(item["parent_generation_hash"]) == parent_hash
                and str(item["child_candidate_hash"]) == candidate_hash
                and str(item["decision"]) == "ACCEPT"
            ] if expected_index > 0 else []
            if len(accepted_decisions) > 1:
                raise ValueError("accepted generation에 ACCEPT decision evidence가 중복되었습니다.")
            accepted_decision = _payload(accepted_decisions[0]) if accepted_decisions else None

            accepted_validations = [
                item for item in validations
                if str(item["parent_generation_hash"]) == parent_hash
                and str(item["child_candidate_hash"]) == candidate_hash
                and str(item["decision"]) == "ACCEPT"
            ] if expected_index > 0 else []
            if len(accepted_validations) > 1:
                raise ValueError("accepted generation에 validation ACCEPT evidence가 중복되었습니다.")
            accepted_validation = _payload(accepted_validations[0]) if accepted_validations else None

            nodes.append(
                {
                    "generation_index": generation_index,
                    "generation_hash": generation_hash,
                    "parent_generation_hash": parent_hash,
                    "candidate_hash": candidate_hash,
                    "profile_run_hash": run_hash,
                    "acquired_skills": acquired,
                    "new_skill": new_skill,
                    "capability_usage": dict(payload.get("capability_usage") or {}),
                    "is_head": generation_hash == head_hash,
                    "profile_summary": self._profile_summary(profile),
                    "acquisition_evidence": {
                        "failure_hash": acquired_failure_hash,
                        "failure_tags": failure_tags,
                        "decision_hash": str(accepted_decision.get("decision_hash") or "") if accepted_decision else "",
                        "decision_improvements": tuple(accepted_decision.get("improvements") or ()) if accepted_decision else (),
                        "decision_survival_violations": tuple(accepted_decision.get("survival_violations") or ()) if accepted_decision else (),
                        "validation_arena_hash": str(accepted_validation.get("arena_hash") or "") if accepted_validation else "",
                        "validation": self._validation_summary(accepted_validation) if accepted_validation else None,
                    },
                }
            )
            previous_payload = payload

        attempts: list[dict[str, Any]] = []
        validation_by_key = {
            (str(row["parent_generation_hash"]), str(row["child_candidate_hash"]), str(row["skill_id"])): row
            for row in validations
        }
        for row in decisions:
            payload = _payload(row)
            key = (
                str(row["parent_generation_hash"]),
                str(row["child_candidate_hash"]),
                str(row["skill_id"]),
            )
            validation = validation_by_key.get(key)
            validation_payload = _payload(validation) if validation else None
            promoted = next(
                (
                    node["generation_hash"]
                    for node in nodes
                    if node["parent_generation_hash"] == key[0]
                    and node["candidate_hash"] == key[1]
                ),
                "",
            )
            attempts.append(
                {
                    "parent_generation_hash": key[0],
                    "child_candidate_hash": key[1],
                    "skill_id": key[2],
                    "train_decision": str(payload.get("decision") or ""),
                    "decision_hash": str(payload.get("decision_hash") or ""),
                    "failure_hash": str(payload.get("failure_hash") or ""),
                    "improvements": tuple(payload.get("improvements") or ()),
                    "survival_violations": tuple(payload.get("survival_violations") or ()),
                    "validation_arena_hash": str(validation_payload.get("arena_hash") or "") if validation_payload else "",
                    "validation": self._validation_summary(validation_payload) if validation_payload else None,
                    "promoted_generation_hash": promoted,
                }
            )

        # A validation may exist before its TRAIN decision is separately persisted.
        decision_keys = {
            (
                str(row["parent_generation_hash"]),
                str(row["child_candidate_hash"]),
                str(row["skill_id"]),
            )
            for row in decisions
        }
        for row in validations:
            key = (
                str(row["parent_generation_hash"]),
                str(row["child_candidate_hash"]),
                str(row["skill_id"]),
            )
            if key in decision_keys:
                continue
            payload = _payload(row)
            attempts.append(
                {
                    "parent_generation_hash": key[0],
                    "child_candidate_hash": key[1],
                    "skill_id": key[2],
                    "train_decision": str((payload.get("train_decision") or {}).get("decision") or ""),
                    "decision_hash": str((payload.get("train_decision") or {}).get("decision_hash") or ""),
                    "failure_hash": str(payload.get("failure_hash") or ""),
                    "improvements": tuple((payload.get("train_decision") or {}).get("improvements") or ()),
                    "survival_violations": tuple((payload.get("train_decision") or {}).get("survival_violations") or ()),
                    "validation_arena_hash": str(payload.get("arena_hash") or ""),
                    "validation": self._validation_summary(payload),
                    "promoted_generation_hash": "",
                }
            )

        attempts.sort(
            key=lambda item: (
                item["parent_generation_hash"],
                item["skill_id"],
                item["child_candidate_hash"],
            )
        )
        identity = {
            "schema": SCHEMA_VERSION,
            "family_id": family_id,
            "head_generation_hash": head_hash,
            "nodes": [
                {
                    "generation_hash": node["generation_hash"],
                    "parent_generation_hash": node["parent_generation_hash"],
                    "candidate_hash": node["candidate_hash"],
                    "profile_run_hash": node["profile_run_hash"],
                    "acquired_skills": node["acquired_skills"],
                    "new_skill": node["new_skill"],
                    "failure_hash": node["acquisition_evidence"]["failure_hash"],
                    "decision_hash": node["acquisition_evidence"]["decision_hash"],
                    "validation_arena_hash": node["acquisition_evidence"]["validation_arena_hash"],
                }
                for node in nodes
            ],
            "attempts": [
                {
                    "parent_generation_hash": item["parent_generation_hash"],
                    "child_candidate_hash": item["child_candidate_hash"],
                    "skill_id": item["skill_id"],
                    "decision_hash": item["decision_hash"],
                    "validation_arena_hash": item["validation_arena_hash"],
                    "promoted_generation_hash": item["promoted_generation_hash"],
                }
                for item in attempts
            ],
        }
        return {
            "schema": SCHEMA_VERSION,
            "family_id": family_id,
            "head_generation_hash": head_hash or None,
            "nodes": tuple(nodes),
            "attempts": tuple(attempts),
            "summary": {
                "generations": len(nodes),
                "attempts": len(attempts),
                "accepted_generations": max(0, len(nodes) - 1),
                "has_explicit_head": bool(head_hash),
            },
            "projection_policy": "READ_ONLY_APPEND_ONLY_EVIDENCE_NO_AUTOMATIC_PROMOTION",
            "lineage_hash": _stable_hash(identity),
        }
