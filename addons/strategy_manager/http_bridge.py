from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from addons.strategy_manager.workspace import StrategyWorkspace


router = APIRouter(prefix="/api/strategy-workspace", tags=["strategy-workspace"])


class StrategyWorkspaceRequest(BaseModel):
    strategy_id: Optional[int] = None
    name: str
    description: str = ""
    dsl_code: str = ""


def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@router.get("/strategies")
def list_strategies():
    try:
        return StrategyWorkspace.list_strategies()
    except Exception as exc:
        raise _domain_error(exc) from exc


@router.post("/draft")
def save_draft(req: StrategyWorkspaceRequest):
    try:
        return StrategyWorkspace.save_draft(
            strategy_id=req.strategy_id,
            name=req.name,
            description=req.description,
            dsl_code=req.dsl_code,
        )
    except Exception as exc:
        raise _domain_error(exc) from exc


@router.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: int):
    try:
        StrategyWorkspace.delete_strategy(strategy_id)
        return {"deleted": int(strategy_id)}
    except Exception as exc:
        raise _domain_error(exc) from exc


@router.post("/validate-commit")
def validate_and_commit(req: StrategyWorkspaceRequest):
    try:
        return StrategyWorkspace.validate_and_commit(
            strategy_id=req.strategy_id,
            name=req.name,
            description=req.description,
            dsl_code=req.dsl_code,
        )
    except Exception as exc:
        raise _domain_error(exc) from exc
