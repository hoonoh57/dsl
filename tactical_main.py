"""Tactical multi-symbol research application.

This module imports the validated Stage 1 application so both /stage1 and
/tactical are served by the same FastAPI app when launched with
``python tactical_main.py``.
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from stage1_main import app, ROOT
from core.stage1_oos import _json_safe
from core.tactical_beta_provider import HighBetaDailyCohortProvider, HighBetaSpec
from core.tactical_chart_document import build_tactical_chart_document
from core.tactical_market import MySQLBarProvider
from core.tactical_providers import Performance1516CohortProvider
from core.tactical_research import TacticalResearchService


research_service = TacticalResearchService()


class Tactical1516RunRequest(BaseModel):
    search_date: str
    search_time: str = "09:05:00"
    condition_name: str = "1516"
    hold_period: str = "7시간"
    dsl_code: str
    timeframe: str = "5m"
    required_bars: int = 180
    entry_end_time: int = 151000
    max_workers: int = 4
    benchmark_symbol: str = ""
    rank_by: str = "feature:search_volume"
    performance_database: str = "performance_db"
    market_database: str = ""
    market_table: str = ""
    market_table_timeframe: str = "5m"
    settings: Dict[str, Any] = Field(default_factory=dict)


def _public_cohort_snapshot(snapshot) -> dict:
    return {
        "unit_id": snapshot.unit_id,
        "as_of": snapshot.as_of,
        "source": snapshot.source,
        "knowledge_cutoff": snapshot.knowledge_cutoff,
        "snapshot_hash": snapshot.snapshot_hash,
        "metadata": dict(snapshot.metadata),
        "members": [
            {
                "symbol": member.symbol,
                "capture_time": member.capture_time,
                "features": dict(member.features),
            }
            for member in snapshot.members
        ],
    }


@app.get("/tactical", response_class=HTMLResponse)
def tactical_ui():
    return (ROOT / "core" / "templates" / "tactical.html").read_text(encoding="utf-8")


@app.get("/api/stage1/tactical/1516/cohort")
def tactical_1516_cohort(
    search_date: str,
    search_time: str = "09:05:00",
    condition_name: str = "1516",
    hold_period: str = "7시간",
    performance_database: str = "performance_db",
):
    try:
        provider = Performance1516CohortProvider(database=performance_database)
        bundle = provider.load_group(
            search_date=search_date,
            search_time=search_time,
            condition_name=condition_name,
            hold_period=hold_period,
        )
        # Cohort inspection intentionally excludes post-search outcomes.
        return _json_safe(bundle.public_snapshot())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/tactical/high-beta/cohort")
def tactical_high_beta_cohort(
    as_of: str,
    benchmark_symbol: str,
    lookback_sessions: int = 60,
    min_overlap_sessions: int = 40,
    top_n: int = 50,
    calendar_lookback_days: int = 180,
    daily_database: str = "",
    daily_table: str = "daily_candles",
    universe_symbols: str = "",
):
    """Inspect an exact-as-of High-Beta cohort without executing a tactic.

    This endpoint intentionally stops at cohort construction. A daily snapshot
    captured at end-of-day must not be forced through the same-day 1516 entry
    gate; next-session execution will be a separate timing contract.
    """
    try:
        provider = HighBetaDailyCohortProvider(
            database=daily_database or None,
            table=daily_table or None,
        )
        universe = [
            item.strip()
            for item in str(universe_symbols or "").split(",")
            if item.strip()
        ]
        snapshot = provider.load(
            as_of=as_of,
            spec=HighBetaSpec(
                benchmark_symbol=benchmark_symbol,
                lookback_sessions=int(lookback_sessions),
                min_overlap_sessions=int(min_overlap_sessions),
                top_n=int(top_n),
                calendar_lookback_days=int(calendar_lookback_days),
            ),
            universe_symbols=universe or None,
        )
        return _json_safe(_public_cohort_snapshot(snapshot))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/tactical/1516/run")
def tactical_1516_run(req: Tactical1516RunRequest):
    try:
        cohort_provider = Performance1516CohortProvider(
            database=req.performance_database
        )
        bundle = cohort_provider.load_group(
            search_date=req.search_date,
            search_time=req.search_time,
            condition_name=req.condition_name,
            hold_period=req.hold_period,
        )
        market_provider = MySQLBarProvider(
            database=req.market_database or None,
            table=req.market_table or None,
            table_timeframe=req.market_table_timeframe,
        )
        response = research_service.run_1516(
            bundle=bundle,
            dsl_code=req.dsl_code,
            market_provider=market_provider,
            timeframe=req.timeframe,
            required_bars=req.required_bars,
            entry_end_time=req.entry_end_time,
            max_workers=req.max_workers,
            settings=req.settings,
            benchmark_symbol=req.benchmark_symbol,
            rank_by=req.rank_by,
            persist=True,
        )
        document = build_tactical_chart_document(
            response["result"],
            response["markets"],
        )
        payload = {
            "status": "success",
            "result": response["result"],
            "evaluation": response["evaluation"],
            "scenario_record": response["scenario_record"],
            "run_record": response["run_record"],
            "chart_document": document,
        }
        return _json_safe(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/tactical/health")
def tactical_health():
    return {
        "status": "ready",
        "schema": "tactical_research/v1",
        "cohort_contract": "point_in_time_cohort/v1",
        "outcome_policy": "post_execution_only",
        "chart_contract": "chart-document/v1",
        "capabilities": ["1516_run", "high_beta_cohort_inspection"],
    }


if __name__ == "__main__":
    uvicorn.run("tactical_main:app", host="127.0.0.1", port=8000, reload=False)
