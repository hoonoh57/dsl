"""Stage 1 Strategy Factory application.

Run:
    python stage1_main.py
Then open:
    http://127.0.0.1:8000/stage1

The existing application remains available at /. This module layers the Stage 1
single-symbol research workflow on the same FastAPI process without rewriting
the legacy UI during the continuous build.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from main import app
from core.backtest import synthetic_market
from core.kiwoom_rest import KiwoomRESTClient, KiwoomAPIError
from core.strategy_factory import DataContract, StrategyFactory, discover_dsl_parameters
from core.stage1_data_store import load_market_snapshot, save_market_snapshot
from core.stage1_target_loop import TargetLoopService
from core.stage1_llm_memory import LLMExchangeMemory

factory = StrategyFactory()
target_loops = TargetLoopService(factory)
llm_memory = LLMExchangeMemory(factory.store)
ROOT = Path(__file__).resolve().parent


class MarketSpec(BaseModel):
    source: str = "synthetic_fixture"
    instrument: str = "005930"
    timeframe: str = "1d"
    bars: int = 600
    market: Optional[Dict[str, Any]] = None
    adjustment_policy: str = "unspecified"
    session: str = "regular"
    knowledge_cutoff: str = ""


class BaselineRequest(BaseModel):
    intent: str
    dsl_code: str
    market_spec: MarketSpec = Field(default_factory=MarketSpec)
    settings: Dict[str, Any] = Field(default_factory=dict)


class DiscoverRequest(BaseModel):
    dsl_code: str


class SeekRequest(BaseModel):
    experiment_id: int
    parameters: List[Dict[str, Any]]
    method: str = "grid"
    objective: str = "MAX_RETURN"
    seed: int = 42
    max_candidates: int = 5000
    promote: bool = False


class FeedbackRequest(BaseModel):
    experiment_id: int
    target_return: Optional[float] = None


class ApplyLLMRequest(BaseModel):
    experiment_id: int
    llm_response: str
    prompt_text: str = ""
    hypothesis: str = ""
    expected_effect: str = ""
    promote: bool = False


class PromoteRequest(BaseModel):
    experiment_id: int


class StopRequest(BaseModel):
    experiment_id: int
    target_return: float
    iteration: int = 0
    iteration_limit: int = 20
    backtests_used: int = 0
    backtest_budget: int = 50000
    consecutive_no_improvement: int = 0
    no_improvement_limit: int = 5
    plateau: bool = False
    engine_blocked: bool = False


class TargetLoopCreateRequest(BaseModel):
    root_id: int
    target_return: float
    iteration_limit: int = 20
    backtest_budget: int = 50000
    no_improvement_limit: int = 5


class TargetLoopObserveRequest(BaseModel):
    experiment_id: int
    backtests_used_delta: int = 1
    accepted: Optional[bool] = None
    plateau: bool = False
    engine_blocked: bool = False


def _market_from_spec(spec: MarketSpec):
    source = spec.source.lower().strip()
    if spec.market is not None:
        market = spec.market
        source = source or "inline"
    elif source == "synthetic_fixture":
        market = synthetic_market(spec.bars)
    elif source == "kiwoom":
        client = KiwoomRESTClient()
        market = client.normalize_chart(client.chart(spec.instrument, spec.timeframe))
    else:
        raise ValueError("Stage 1 data source는 inline/synthetic_fixture/kiwoom을 지원합니다.")
    normalized, provenance = DataContract.normalize(
        market,
        instrument=spec.instrument,
        timeframe=spec.timeframe,
        source=source,
        adjustment_policy=spec.adjustment_policy,
        session=spec.session,
        knowledge_cutoff=spec.knowledge_cutoff,
    )
    save_market_snapshot(normalized)
    return normalized, provenance


def _market_for_experiment(experiment_id: int):
    experiment = factory.store.get_experiment(experiment_id)
    return load_market_snapshot(experiment["provenance"]["data_hash"]), experiment


@app.get("/stage1", response_class=HTMLResponse)
def stage1_ui():
    return (ROOT / "core" / "templates" / "stage1.html").read_text(encoding="utf-8")


@app.get("/api/stage1/health")
def stage1_health():
    return {"status": "ready", "schema": "stage1_factory/v1", "execution_policy": "continuous-build-then-stress-test"}


@app.post("/api/stage1/parameters/discover")
def stage1_discover(req: DiscoverRequest):
    try:
        return {"parameters": discover_dsl_parameters(req.dsl_code)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/baseline")
def stage1_baseline(req: BaselineRequest):
    try:
        market, provenance = _market_from_spec(req.market_spec)
        experiment = factory.baseline(
            intent=req.intent,
            dsl_code=req.dsl_code,
            market=market,
            instrument=provenance.instrument,
            timeframe=provenance.timeframe,
            source=provenance.source,
            settings=req.settings,
            adjustment_policy=provenance.adjustment_policy,
            session=provenance.session,
            knowledge_cutoff=provenance.knowledge_cutoff,
        )
        return {"status": "success", "experiment": experiment, "chart": factory.chart_audit(experiment)}
    except KiwoomAPIError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/seeker")
def stage1_seeker(req: SeekRequest):
    try:
        market, _ = _market_for_experiment(req.experiment_id)
        result = factory.seek(
            experiment_id=req.experiment_id,
            market=market,
            parameter_specs=req.parameters,
            method=req.method,
            objective=req.objective,
            seed=req.seed,
            max_candidates=req.max_candidates,
            promote=req.promote,
        )
        return {"status": "success", **result, "chart": factory.chart_audit(result["experiment"])}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/feedback")
def stage1_feedback(req: FeedbackRequest):
    try:
        package = factory.feedback_package(req.experiment_id, target_return=req.target_return)
        history = llm_memory.prompt_history_context(package["root_id"])
        package["previous_raw_exchanges"] = history
        package["prompt"] += "\n\n[이전 raw LLM Prompt/Response 기록]\n" + history
        return package
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/apply-llm")
def stage1_apply_llm(req: ApplyLLMRequest):
    before = None
    try:
        _, before = _market_for_experiment(req.experiment_id)
        market = load_market_snapshot(before["provenance"]["data_hash"])
        result = factory.apply_llm_response(
            experiment_id=req.experiment_id,
            llm_response=req.llm_response,
            market=market,
            hypothesis=req.hypothesis,
            expected_effect=req.expected_effect,
            promote=req.promote,
        )
        exchange_id = llm_memory.record(
            before_experiment_id=req.experiment_id,
            after_experiment_id=result["experiment"]["id"],
            prompt_text=req.prompt_text,
            response_text=req.llm_response,
            hypothesis=req.hypothesis,
            status=result["verdict"],
        )
        return {"status": "success", **result, "exchange_id": exchange_id,
                "chart": factory.chart_audit(result["experiment"])}
    except Exception as exc:
        if before is not None:
            try:
                llm_memory.record(before_experiment_id=req.experiment_id, after_experiment_id=None,
                                  prompt_text=req.prompt_text, response_text=req.llm_response,
                                  hypothesis=req.hypothesis, status="REJECTED_VALIDATION")
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/promote")
def stage1_promote(req: PromoteRequest):
    try:
        experiment = factory.store.promote(req.experiment_id)
        return {"status": "success", "head": experiment}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/stop-state")
def stage1_stop(req: StopRequest):
    try:
        experiment = factory.store.get_experiment(req.experiment_id)
        state = factory.stop_state(
            experiment,
            target_return=req.target_return,
            iteration=req.iteration,
            iteration_limit=req.iteration_limit,
            backtests_used=req.backtests_used,
            backtest_budget=req.backtest_budget,
            consecutive_no_improvement=req.consecutive_no_improvement,
            no_improvement_limit=req.no_improvement_limit,
            plateau=req.plateau,
            engine_blocked=req.engine_blocked,
        )
        return {"state": state}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/target-loops")
def stage1_target_loop_create(req: TargetLoopCreateRequest):
    try:
        return target_loops.create(root_id=req.root_id, target_return=req.target_return,
                                   iteration_limit=req.iteration_limit, backtest_budget=req.backtest_budget,
                                   no_improvement_limit=req.no_improvement_limit)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/target-loops/{loop_id}")
def stage1_target_loop_get(loop_id: int):
    try:
        return target_loops.get(loop_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/stage1/target-loops/{loop_id}/observe")
def stage1_target_loop_observe(loop_id: int, req: TargetLoopObserveRequest):
    try:
        return target_loops.observe(loop_id=loop_id, experiment_id=req.experiment_id,
                                    backtests_used_delta=req.backtests_used_delta, accepted=req.accepted,
                                    plateau=req.plateau, engine_blocked=req.engine_blocked)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/experiments")
def stage1_experiments(root_id: Optional[int] = None, limit: int = 200):
    try:
        return {"experiments": factory.store.list_experiments(root_id=root_id, limit=min(max(limit, 1), 1000))}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/experiments/{experiment_id}")
def stage1_experiment(experiment_id: int):
    try:
        experiment = factory.store.get_experiment(experiment_id)
        return {"experiment": experiment, "lineage": factory.store.lineage(experiment_id),
                "chart": factory.chart_audit(experiment)}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/stage1/methodology/{root_id}")
def stage1_methodology(root_id: int):
    try:
        summary = factory.methodology_summary(root_id)
        summary["raw_llm_exchanges"] = llm_memory.recent(root_id, 100)
        return summary
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("stage1_main:app", host="127.0.0.1", port=8000, reload=False)
