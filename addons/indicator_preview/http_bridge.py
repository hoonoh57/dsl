from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.indicator_preview import evaluate_indicator


router = APIRouter(prefix="/api/indicator-preview", tags=["indicator-preview"])


class IndicatorPreviewRequest(BaseModel):
    indicator_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeframe: str
    bars: list[dict[str, Any]]


@router.post("")
def preview_indicator(request: IndicatorPreviewRequest):
    try:
        return evaluate_indicator(
            request.indicator_id,
            parameters=request.parameters,
            timeframe=request.timeframe,
            bars=request.bars,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown indicator: {request.indicator_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
