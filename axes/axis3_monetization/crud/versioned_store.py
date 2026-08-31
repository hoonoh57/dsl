"""AXIS 3 versioned Condition/Strategy CRUD with immutable content.

The store owns product-artifact identity, lineage and lifecycle only.  It does
not evaluate AXIS 2 conditions and does not compile or execute AXIS 1 DSL.
Updates create new immutable versions; mutable lifecycle state is stored
separately and audited.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import sqlite3
from typing import Any, Mapping, Sequence


AXIS3_CONDITION_SCHEMA = "axis3_condition_version/v1"
AXIS3_STRATEGY_SCHEMA = "axis3_strategy_version/v1"
ARTIFACT_STATES = frozenset({"DRAFT", "PROMOTED", "REJECTED", "ARCHIVED"})


class Axis3StoreError(ValueError):
    def __init__(self, message: str, code: str = "AXIS3_STORE_ERROR"):
        self.code = str(code)
        super().__init__(message)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Axis3StoreError(f"{label} must be a non-empty string", "BAD_TEXT")
    return value.strip()


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 14 or not value.isdigit():
        raise Axis3StoreError(f"{label} must be YYYYMMDDHHMMSS", "BAD_TIMESTAMP")
    return value


def _version(value: Any, label: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Axis3StoreError(f"{label} must be a positive integer", "BAD_VERSION")
    return int(value)


def _json_safe(value: Any, path: str = "$") -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise Axis3StoreError(f"non-finite value at {path}", "NONFINITE_VALUE")
        return float(value)
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise Axis3StoreError(f"mapping key must be non-empty string at {path}", "BAD_MAPPING_KEY")
            result[key] = _json_safe(item, f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, f"{path}[]") for item in value]
    raise Axis3StoreError(f"opaque value is not allowed at {path}", "OPAQUE_VALUE")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _condition_ref(value: Mapping[str, Any]) -> tuple[str, int]:
    if not isinstance(value, Mapping) or set(value) != {"condition_id", "version"}:
        raise Axis3StoreError("condition_ref requires condition_id/version only", "BAD_CONDITION_REF")
    return _text(value["condition_id"], "condition_ref.condition_id"), _version(
        value["version"], "condition_ref.version"
    )


@dataclass(frozen=True)
class ArtifactState:
    artifact_type: str
    artifact_id: str
    version: int
    status: str
    reason: str
    updated_at: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "status": self.status,
            "reason": self.reason,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ConditionVersion:
    condition_id: str
    version: int
    name: str
    selection_spec: Mapping[str, Any]
    parent_version: int | None
    created_at: str
    schema_version: str = AXIS3_CONDITION_SCHEMA

    def canonical_dict(self) -> dict[str, Any]:
        if self.schema_version != AXIS3_CONDITION_SCHEMA:
            raise Axis3StoreError("bad condition schema", "BAD_SCHEMA")
        _text(self.condition_id, "condition_id")
        _version(self.version)
        _text(self.name, "name")
        _timestamp(self.created_at, "created_at")
        if self.parent_version is not None:
            parent = _version(self.parent_version, "parent_version")
            if parent >= self.version:
                raise Axis3StoreError("parent_version must be older than version", "BAD_LINEAGE")
        selection = _json_safe(self.selection_spec, "$.selection_spec")
        if not isinstance(selection, dict):
            raise Axis3StoreError("selection_spec must be a mapping", "BAD_SELECTION_SPEC")
        if selection.get("schema_version") != "axis2_selection_spec/v1":
            raise Axis3StoreError(
                "Condition artifact must preserve axis2_selection_spec/v1 data",
                "BAD_SELECTION_SPEC_SCHEMA",
            )
        if not isinstance(selection.get("selection_hash"), str) or not selection["selection_hash"]:
            raise Axis3StoreError("selection_spec.selection_hash is required", "SELECTION_HASH_REQUIRED")
        return {
            "schema_version": self.schema_version,
            "condition_id": self.condition_id,
            "version": self.version,
            "name": self.name,
            "selection_spec": selection,
            "parent_version": self.parent_version,
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return _hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "artifact_hash": self.artifact_hash}


@dataclass(frozen=True)
class StrategyVersion:
    strategy_id: str
    version: int
    name: str
    timeframe: str
    dsl_code: str
    settings: Mapping[str, Any]
    condition_refs: tuple[tuple[str, int], ...]
    parent_version: int | None
    created_at: str
    schema_version: str = AXIS3_STRATEGY_SCHEMA

    def canonical_dict(self) -> dict[str, Any]:
        if self.schema_version != AXIS3_STRATEGY_SCHEMA:
            raise Axis3StoreError("bad strategy schema", "BAD_SCHEMA")
        _text(self.strategy_id, "strategy_id")
        _version(self.version)
        _text(self.name, "name")
        _text(self.timeframe, "timeframe")
        _text(self.dsl_code, "dsl_code")
        _timestamp(self.created_at, "created_at")
        if self.parent_version is not None:
            parent = _version(self.parent_version, "parent_version")
            if parent >= self.version:
                raise Axis3StoreError("parent_version must be older than version", "BAD_LINEAGE")
        settings = _json_safe(self.settings, "$.settings")
        if not isinstance(settings, dict):
            raise Axis3StoreError("settings must be a mapping", "BAD_SETTINGS")
        refs = tuple((str(cid), int(ver)) for cid, ver in self.condition_refs)
        if len(refs) != len(set(refs)):
            raise Axis3StoreError("duplicate condition refs", "DUPLICATE_CONDITION_REF")
        for condition_id, version in refs:
            _text(condition_id, "condition_ref.condition_id")
            _version(version, "condition_ref.version")
        refs = tuple(sorted(refs))
        return {
            "schema_version": self.schema_version,
            "strategy_id": self.strategy_id,
            "version": self.version,
            "name": self.name,
            "timeframe": self.timeframe,
            "dsl_code": self.dsl_code,
            "settings": settings,
            "condition_refs": [
                {"condition_id": condition_id, "version": version}
                for condition_id, version in refs
            ],
            "parent_version": self.parent_version,
            "created_at": self.created_at,
        }

    @property
    def artifact_hash(self) -> str:
        return _hash(self.canonical_dict())

    def public_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "artifact_hash": self.artifact_hash}


class VersionedArtifactStore:
    """SQLite-backed AXIS 3 store with immutable versions and audited lifecycle."""

    def __init__(self, path: str = ":memory:"):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS axis3_conditions (
                condition_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                document_json TEXT NOT NULL,
                artifact_hash TEXT NOT NULL,
                PRIMARY KEY (condition_id, version)
            );
            CREATE TABLE IF NOT EXISTS axis3_condition_state (
                condition_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (condition_id, version),
                FOREIGN KEY (condition_id, version)
                    REFERENCES axis3_conditions(condition_id, version)
            );
            CREATE TABLE IF NOT EXISTS axis3_strategies (
                strategy_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                document_json TEXT NOT NULL,
                artifact_hash TEXT NOT NULL,
                PRIMARY KEY (strategy_id, version)
            );
            CREATE TABLE IF NOT EXISTS axis3_strategy_state (
                strategy_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL,
                reason TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (strategy_id, version),
                FOREIGN KEY (strategy_id, version)
                    REFERENCES axis3_strategies(strategy_id, version)
            );
            CREATE TABLE IF NOT EXISTS axis3_lifecycle_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_type TEXT NOT NULL,
                artifact_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                reason TEXT NOT NULL,
                event_time TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    @staticmethod
    def _decode_condition(row: sqlite3.Row) -> ConditionVersion:
        value = json.loads(row["document_json"])
        item = ConditionVersion(
            condition_id=value["condition_id"],
            version=int(value["version"]),
            name=value["name"],
            selection_spec=value["selection_spec"],
            parent_version=value["parent_version"],
            created_at=value["created_at"],
        )
        if item.artifact_hash != row["artifact_hash"]:
            raise Axis3StoreError("stored condition hash mismatch", "STORAGE_HASH_MISMATCH")
        return item

    @staticmethod
    def _decode_strategy(row: sqlite3.Row) -> StrategyVersion:
        value = json.loads(row["document_json"])
        refs = tuple(_condition_ref(item) for item in value["condition_refs"])
        item = StrategyVersion(
            strategy_id=value["strategy_id"],
            version=int(value["version"]),
            name=value["name"],
            timeframe=value["timeframe"],
            dsl_code=value["dsl_code"],
            settings=value["settings"],
            condition_refs=refs,
            parent_version=value["parent_version"],
            created_at=value["created_at"],
        )
        if item.artifact_hash != row["artifact_hash"]:
            raise Axis3StoreError("stored strategy hash mismatch", "STORAGE_HASH_MISMATCH")
        return item

    def _next_version(self, table: str, id_column: str, artifact_id: str) -> int:
        row = self.connection.execute(
            f"SELECT MAX(version) AS v FROM {table} WHERE {id_column} = ?", (artifact_id,)
        ).fetchone()
        return 1 if row["v"] is None else int(row["v"]) + 1

    def _condition_exists(self, condition_id: str, version: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM axis3_conditions WHERE condition_id=? AND version=?",
            (condition_id, version),
        ).fetchone()
        return row is not None

    def create_condition(
        self,
        *,
        condition_id: str,
        name: str,
        selection_spec: Mapping[str, Any],
        created_at: str,
        parent_version: int | None = None,
    ) -> ConditionVersion:
        identity = _text(condition_id, "condition_id")
        version = self._next_version("axis3_conditions", "condition_id", identity)
        if version == 1 and parent_version is not None:
            raise Axis3StoreError("first condition version cannot have parent", "BAD_LINEAGE")
        if version > 1:
            if parent_version is None:
                parent_version = version - 1
            if not self._condition_exists(identity, _version(parent_version, "parent_version")):
                raise Axis3StoreError("condition parent version not found", "PARENT_NOT_FOUND")
        item = ConditionVersion(
            condition_id=identity,
            version=version,
            name=name,
            selection_spec=selection_spec,
            parent_version=parent_version,
            created_at=created_at,
        )
        document = item.canonical_dict()
        with self.connection:
            self.connection.execute(
                "INSERT INTO axis3_conditions VALUES (?,?,?,?)",
                (identity, version, _canonical_json(document), item.artifact_hash),
            )
            self.connection.execute(
                "INSERT INTO axis3_condition_state VALUES (?,?,?,?,?)",
                (identity, version, "DRAFT", "created", _timestamp(created_at, "created_at")),
            )
            self.connection.execute(
                "INSERT INTO axis3_lifecycle_events(artifact_type,artifact_id,version,from_status,to_status,reason,event_time) VALUES (?,?,?,?,?,?,?)",
                ("CONDITION", identity, version, None, "DRAFT", "created", created_at),
            )
        return item

    def get_condition(self, condition_id: str, version: int | None = None) -> ConditionVersion:
        identity = _text(condition_id, "condition_id")
        if version is None:
            row = self.connection.execute(
                "SELECT * FROM axis3_conditions WHERE condition_id=? ORDER BY version DESC LIMIT 1",
                (identity,),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT * FROM axis3_conditions WHERE condition_id=? AND version=?",
                (identity, _version(version)),
            ).fetchone()
        if row is None:
            raise Axis3StoreError("condition version not found", "NOT_FOUND")
        return self._decode_condition(row)

    def list_condition_versions(self, condition_id: str) -> tuple[ConditionVersion, ...]:
        identity = _text(condition_id, "condition_id")
        rows = self.connection.execute(
            "SELECT * FROM axis3_conditions WHERE condition_id=? ORDER BY version", (identity,)
        ).fetchall()
        return tuple(self._decode_condition(row) for row in rows)

    def create_strategy(
        self,
        *,
        strategy_id: str,
        name: str,
        timeframe: str,
        dsl_code: str,
        settings: Mapping[str, Any] | None,
        condition_refs: Sequence[Mapping[str, Any]] = (),
        created_at: str,
        parent_version: int | None = None,
    ) -> StrategyVersion:
        identity = _text(strategy_id, "strategy_id")
        refs = tuple(_condition_ref(item) for item in condition_refs)
        for condition_id, condition_version in refs:
            if not self._condition_exists(condition_id, condition_version):
                raise Axis3StoreError(
                    f"referenced condition not found: {condition_id}@{condition_version}",
                    "CONDITION_REF_NOT_FOUND",
                )
        version = self._next_version("axis3_strategies", "strategy_id", identity)
        if version == 1 and parent_version is not None:
            raise Axis3StoreError("first strategy version cannot have parent", "BAD_LINEAGE")
        if version > 1:
            if parent_version is None:
                parent_version = version - 1
            try:
                self.get_strategy(identity, parent_version)
            except Axis3StoreError as exc:
                raise Axis3StoreError("strategy parent version not found", "PARENT_NOT_FOUND") from exc
        item = StrategyVersion(
            strategy_id=identity,
            version=version,
            name=name,
            timeframe=timeframe,
            dsl_code=dsl_code,
            settings={} if settings is None else settings,
            condition_refs=refs,
            parent_version=parent_version,
            created_at=created_at,
        )
        document = item.canonical_dict()
        with self.connection:
            self.connection.execute(
                "INSERT INTO axis3_strategies VALUES (?,?,?,?)",
                (identity, version, _canonical_json(document), item.artifact_hash),
            )
            self.connection.execute(
                "INSERT INTO axis3_strategy_state VALUES (?,?,?,?,?)",
                (identity, version, "DRAFT", "created", _timestamp(created_at, "created_at")),
            )
            self.connection.execute(
                "INSERT INTO axis3_lifecycle_events(artifact_type,artifact_id,version,from_status,to_status,reason,event_time) VALUES (?,?,?,?,?,?,?)",
                ("STRATEGY", identity, version, None, "DRAFT", "created", created_at),
            )
        return item

    def get_strategy(self, strategy_id: str, version: int | None = None) -> StrategyVersion:
        identity = _text(strategy_id, "strategy_id")
        if version is None:
            row = self.connection.execute(
                "SELECT * FROM axis3_strategies WHERE strategy_id=? ORDER BY version DESC LIMIT 1",
                (identity,),
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT * FROM axis3_strategies WHERE strategy_id=? AND version=?",
                (identity, _version(version)),
            ).fetchone()
        if row is None:
            raise Axis3StoreError("strategy version not found", "NOT_FOUND")
        return self._decode_strategy(row)

    def list_strategy_versions(self, strategy_id: str) -> tuple[StrategyVersion, ...]:
        identity = _text(strategy_id, "strategy_id")
        rows = self.connection.execute(
            "SELECT * FROM axis3_strategies WHERE strategy_id=? ORDER BY version", (identity,)
        ).fetchall()
        return tuple(self._decode_strategy(row) for row in rows)

    def state(self, artifact_type: str, artifact_id: str, version: int) -> ArtifactState:
        kind = _text(artifact_type, "artifact_type").upper()
        identity = _text(artifact_id, "artifact_id")
        ver = _version(version)
        if kind == "CONDITION":
            table, id_column = "axis3_condition_state", "condition_id"
        elif kind == "STRATEGY":
            table, id_column = "axis3_strategy_state", "strategy_id"
        else:
            raise Axis3StoreError("artifact_type must be CONDITION or STRATEGY", "BAD_ARTIFACT_TYPE")
        row = self.connection.execute(
            f"SELECT * FROM {table} WHERE {id_column}=? AND version=?", (identity, ver)
        ).fetchone()
        if row is None:
            raise Axis3StoreError("artifact state not found", "NOT_FOUND")
        return ArtifactState(kind, identity, ver, row["status"], row["reason"], row["updated_at"])

    def transition(
        self,
        artifact_type: str,
        artifact_id: str,
        version: int,
        *,
        to_status: str,
        reason: str,
        event_time: str,
    ) -> ArtifactState:
        current = self.state(artifact_type, artifact_id, version)
        target = _text(to_status, "to_status").upper()
        if target not in ARTIFACT_STATES:
            raise Axis3StoreError("unsupported lifecycle state", "BAD_STATUS")
        allowed = {
            "DRAFT": {"PROMOTED", "REJECTED", "ARCHIVED"},
            "PROMOTED": {"ARCHIVED"},
            "REJECTED": {"ARCHIVED"},
            "ARCHIVED": set(),
        }
        if target not in allowed[current.status]:
            raise Axis3StoreError(
                f"invalid lifecycle transition: {current.status} -> {target}",
                "INVALID_TRANSITION",
            )
        explanation = _text(reason, "reason")
        when = _timestamp(event_time, "event_time")
        if current.artifact_type == "CONDITION":
            table, id_column = "axis3_condition_state", "condition_id"
        else:
            table, id_column = "axis3_strategy_state", "strategy_id"
        with self.connection:
            self.connection.execute(
                f"UPDATE {table} SET status=?, reason=?, updated_at=? WHERE {id_column}=? AND version=?",
                (target, explanation, when, current.artifact_id, current.version),
            )
            self.connection.execute(
                "INSERT INTO axis3_lifecycle_events(artifact_type,artifact_id,version,from_status,to_status,reason,event_time) VALUES (?,?,?,?,?,?,?)",
                (
                    current.artifact_type,
                    current.artifact_id,
                    current.version,
                    current.status,
                    target,
                    explanation,
                    when,
                ),
            )
        return self.state(current.artifact_type, current.artifact_id, current.version)

    def lifecycle_events(self, artifact_type: str, artifact_id: str, version: int) -> tuple[dict[str, Any], ...]:
        kind = _text(artifact_type, "artifact_type").upper()
        identity = _text(artifact_id, "artifact_id")
        ver = _version(version)
        rows = self.connection.execute(
            "SELECT sequence,artifact_type,artifact_id,version,from_status,to_status,reason,event_time FROM axis3_lifecycle_events WHERE artifact_type=? AND artifact_id=? AND version=? ORDER BY sequence",
            (kind, identity, ver),
        ).fetchall()
        return tuple(dict(row) for row in rows)

    def compare_strategy_versions(self, strategy_id: str, left_version: int, right_version: int) -> dict[str, Any]:
        left = self.get_strategy(strategy_id, left_version)
        right = self.get_strategy(strategy_id, right_version)
        return {
            "strategy_id": left.strategy_id,
            "left_version": left.version,
            "right_version": right.version,
            "left_hash": left.artifact_hash,
            "right_hash": right.artifact_hash,
            "same_content": left.artifact_hash == right.artifact_hash,
            "changed": {
                "name": left.name != right.name,
                "timeframe": left.timeframe != right.timeframe,
                "dsl_code": left.dsl_code != right.dsl_code,
                "settings": left.canonical_dict()["settings"] != right.canonical_dict()["settings"],
                "condition_refs": left.canonical_dict()["condition_refs"] != right.canonical_dict()["condition_refs"],
            },
        }
