from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional

from core import db
from core.backtest import BacktestEngine
from core.capabilities import DSL_VERSION
from core.strategy_validation_fixture import strategy_validation_market


VALIDATION_SCHEMA = "strategy_workspace_validation/v1"


def _dsl_hash(dsl_code: str) -> str:
    return hashlib.sha256(str(dsl_code).encode("utf-8")).hexdigest()


def _json_object(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


class StrategyWorkspace:
    """WYSIWYG strategy draft/validation workspace outside the DSL core.

    Draft CRUD delegates to ``core.db``. A strategy is considered currently
    validated only when an immutable artifact version contains the exact same
    DSL bytes and a positive strategy-workspace validation record. This lets a
    new UI/session recover validation state without trusting ephemeral client
    state.
    """

    @staticmethod
    def _strategy_category_id() -> int:
        categories = db.get_categories()
        for item in categories:
            if item.get("artifact_type") == "strategy" and item.get("parent_id") is None:
                return int(item["id"])
        raise ValueError("전략 루트 카테고리를 찾을 수 없습니다.")

    @staticmethod
    def _validation_state(strategy: Dict[str, Any]) -> Dict[str, Any]:
        strategy_id = strategy.get("id")
        dsl_code = str(strategy.get("dsl_code") or "")
        current_hash = _dsl_hash(dsl_code)
        if not strategy_id:
            return {"valid": False, "dsl_sha256": current_hash, "version": None}
        for version in db.get_artifact_versions(int(strategy_id)):
            if str(version.get("dsl_code") or "") != dsl_code:
                continue
            validation = _json_object(version.get("validation_json"))
            if validation.get("schema") != VALIDATION_SCHEMA or validation.get("valid") is not True:
                continue
            if validation.get("dsl_sha256") != current_hash:
                continue
            return {
                "valid": True,
                "dsl_sha256": current_hash,
                "version": int(version.get("version") or 0),
                "validation": validation,
            }
        return {"valid": False, "dsl_sha256": current_hash, "version": None}

    @classmethod
    def list_strategies(cls) -> list[Dict[str, Any]]:
        result = []
        for strategy in db.get_all_strategies():
            row = dict(strategy)
            row["current_validation"] = cls._validation_state(row)
            result.append(row)
        return result

    @classmethod
    def get_strategy(cls, strategy_id: int) -> Dict[str, Any]:
        for strategy in cls.list_strategies():
            if int(strategy.get("id") or 0) == int(strategy_id):
                return strategy
        raise KeyError(f"strategy not found: {strategy_id}")

    @classmethod
    def save_draft(
        cls,
        *,
        strategy_id: Optional[int],
        name: str,
        description: str = "",
        dsl_code: str = "",
    ) -> Dict[str, Any]:
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("전략 이름은 비어 있을 수 없습니다.")
        if strategy_id is None:
            strategy_id = db.insert_strategy(clean_name, str(description), str(dsl_code), "DSL", str(dsl_code))
        else:
            db.update_strategy(int(strategy_id), clean_name, str(description), str(dsl_code), "DSL", str(dsl_code))
        return cls.get_strategy(int(strategy_id))

    @staticmethod
    def delete_strategy(strategy_id: int) -> None:
        db.delete_strategy(int(strategy_id))

    @classmethod
    def validate_and_commit(
        cls,
        *,
        strategy_id: Optional[int],
        name: str,
        description: str,
        dsl_code: str,
    ) -> Dict[str, Any]:
        clean_name = str(name).strip()
        exact_dsl = str(dsl_code)
        if not clean_name:
            raise ValueError("전략 이름은 비어 있을 수 없습니다.")
        if not exact_dsl.strip():
            raise ValueError("DSL 코드는 비어 있을 수 없습니다.")

        # Authoritative syntax/semantic/runtime validation path. No parallel parser.
        # The validation fixture intentionally makes no 1d/5m/etc. market claim;
        # real backtests keep BacktestEngine's strict market timeframe check.
        preview = BacktestEngine.run(exact_dsl, market=strategy_validation_market())
        validation = {
            "schema": VALIDATION_SCHEMA,
            "valid": True,
            "dsl_sha256": _dsl_hash(exact_dsl),
            "dsl_version": DSL_VERSION,
            "strategy": dict(preview.get("strategy") or {}),
            "bars": int((preview.get("diagnostics") or {}).get("bars") or 0),
            "indicator_count": len(preview.get("indicators") or []),
            "execution_authority": str((preview.get("diagnostics") or {}).get("execution_authority") or ""),
        }
        artifact_id = db.commit_artifact(
            int(strategy_id) if strategy_id is not None else None,
            name=clean_name,
            description=str(description),
            category_id=cls._strategy_category_id(),
            artifact_type="strategy",
            source_type="DSL",
            source_code=exact_dsl,
            dsl_code=exact_dsl,
            user_request="WYSIWYG Strategy Manager validation",
            prompt_text="",
            llm_response="",
            validation_json=json.dumps(validation, ensure_ascii=False, sort_keys=True),
            playbook_version=DSL_VERSION,
            playbook_hash="",
        )
        event_id = db.record_validation(
            artifact_id=artifact_id,
            artifact_type="strategy",
            user_request="WYSIWYG Strategy Manager validation",
            prompt_text="",
            llm_response="",
            extracted_dsl=exact_dsl,
            status="validated",
            diagnostic_json=json.dumps(validation, ensure_ascii=False, sort_keys=True),
            playbook_version=DSL_VERSION,
            playbook_hash="",
        )
        saved = cls.get_strategy(int(artifact_id))
        return {
            "strategy": saved,
            "validation": validation,
            "validation_event_id": int(event_id),
        }
