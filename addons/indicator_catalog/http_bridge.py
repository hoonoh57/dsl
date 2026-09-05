from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.indicator_catalog import get_indicator_spec, indicator_catalog_payload


router = APIRouter(prefix="/api/indicator-catalog", tags=["indicator-catalog"])


@router.get("")
def read_indicator_catalog():
    return indicator_catalog_payload()


@router.get("/{indicator_id}")
def read_indicator(indicator_id: str):
    try:
        return get_indicator_spec(indicator_id).public_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
