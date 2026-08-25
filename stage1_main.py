"""Stage 1 Strategy Factory application.

Run ``python stage1_main.py`` and open http://127.0.0.1:8000/stage1.
The existing DSL Lab remains available at /.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import uvicorn

from main import app
from core.backtest import synthetic_market
from core.dsl_parser import DSLParseError
from core.dsl_runtime import DSLRuntimeError
from core.kiwoom_rest import KiwoomRESTClient, KiwoomAPIError
from core.multi_symbol import (
    InstrumentTask,
    MissionSpec,
    MultiSymbolAnalysisEngine,
    OpportunityWindow,
    RegimeContext,
    TacticalUnitSpec,
)
from core.strategy_factory import DataContract, StrategyFactory, discover_dsl_parameters
from core.stage1_data_store import load_market_snapshot, save_market_snapshot
from core.stage1_target_loop import TargetLoopService
from core.stage1_llm_memory import LLMExchangeMemory
from core.stage1_resumable_seeker import ResumableSeekerService
from core.stage1_evidence import EvidenceBuilder
from core.stage1_hypothesis_memory import HypothesisMemory
from core.stage1_diff import summarize_dsl_change
from core.stage1_methodology import MethodologyValidator
from core.stage1_oos import OOSRegistry, _json_safe
from core.stage1_chart_document import build_chart_document

factory = StrategyFactory()
target_loops = TargetLoopService(factory)
llm_memory = LLMExchangeMemory(factory.store)
resumable_seeker = ResumableSeekerService(factory)
hypothesis_memory = HypothesisMemory(factory.store)
methodology = MethodologyValidator(factory.store)
oos_registry = OOSRegistry(factory)
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
    holdout_fraction: float = 0.0


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


class SeekSessionCreateRequest(BaseModel):
    experiment_id: int
    parameters: List[Dict[str, Any]]
    method: str = "grid"
    objective: str = "MAX_RETURN"
    seed: int = 42
    max_candidates: int = 5000


class SeekSessionProcessRequest(BaseModel):
    batch_size: int = 25


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
    oos_degradation_limit_pct: float = 5.0
    duplicate_hypothesis_limit: int = 2
    parameter_spike_limit: float = 3.0


class TargetLoopObserveRequest(BaseModel):
    experiment_id: int
    backtests_used_delta: int = 1
    accepted: Optional[bool] = None
    plateau: bool = False
    engine_blocked: bool = False
    oos_return_pct: Optional[float] = None
    duplicate_hypothesis: bool = False
    parameter_spike_ratio: Optional[float] = None


class OpportunityWindowRequest(BaseModel):
    start: str
    end: str
    label: str = ""


class RegimeRequest(BaseModel):
    regime_id: str
    state: str = "UNKNOWN"
    active: bool = True
    eligible_units: List[str] = Field(default_factory=list)
    windows: List[OpportunityWindowRequest] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class MissionRequest(BaseModel):
    name: str = "MFE_GTE"
    mfe_threshold_pct: Optional[float] = None
    capture_price_field: str = "close"
    include_capture_bar: bool = False


class TacticalUnitRequest(BaseModel):
    unit_id: str
    unit_type: str
    symbols: List[str]
    capture_times: Dict[str, str] = Field(default_factory=dict)
    reference_symbol: str = ""
    rank_by: str = "relative_strength_pct"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InstrumentTaskRequest(BaseModel):
    symbol: str
    dsl_code: str
    market: Dict[str, Any]
    settings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultiSymbolAnalyzeRequest(BaseModel):
    regime: RegimeRequest
    unit: TacticalUnitRequest
    instruments: List[InstrumentTaskRequest]
    mission: MissionRequest = Field(default_factory=MissionRequest)
    benchmark_market: Optional[Dict[str, Any]] = None
    max_workers: int = 4


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


def _chart_document_for_experiment(experiment: dict):
    market = load_market_snapshot(experiment["provenance"]["data_hash"])
    return build_chart_document(experiment, market)


def _record_failed_llm_episode(before: dict, req: ApplyLLMRequest, verdict: str, reason: str):
    try:
        return factory.store.create_episode(
            before_id=before["id"],
            after_id=None,
            observation=json.dumps(before.get("analysis", {}).get("findings", []), ensure_ascii=False),
            hypothesis=req.hypothesis,
            proposal=req.llm_response,
            expected_effect=req.expected_effect,
            verdict=verdict,
            reason=reason,
        )
    except Exception:
        return None


@app.get("/stage1", response_class=HTMLResponse)
def stage1_ui():
    return (ROOT / "core" / "templates" / "stage1.html").read_text(encoding="utf-8")


@app.get("/api/stage1/health")
def stage1_health():
    return {
        "status": "ready",
        "schema": "stage1_factory/v1",
        "execution_policy": "continuous-build-then-stress-test",
        "execution_authority": "BrokerEmulator",
        "chart_contract": "chart-document/v1",
        "multi_symbol_contract": "multi_symbol_tactical/v1",
    }


@app.post("/api/stage1/multi-symbol/analyze")
def stage1_multi_symbol_analyze(req: MultiSymbolAnalyzeRequest):
    try:
        regime = RegimeContext(
            regime_id=req.regime.regime_id,
            state=req.regime.state,
            active=req.regime.active,
            eligible_units=tuple(req.regime.eligible_units),
            windows=tuple(
                OpportunityWindow(start=item.start, end=item.end, label=item.label)
                for item in req.regime.windows
            ),
            evidence=req.regime.evidence,
        )
        unit = TacticalUnitSpec(
            unit_id=req.unit.unit_id,
            unit_type=req.unit.unit_type,
            symbols=tuple(req.unit.symbols),
            capture_times=req.unit.capture_times,
            reference_symbol=req.unit.reference_symbol,
            rank_by=req.unit.rank_by,
            metadata=req.unit.metadata,
        )
        mission = MissionSpec(
            name=req.mission.name,
            mfe_threshold_pct=req.mission.mfe_threshold_pct,
            capture_price_field=req.mission.capture_price_field,
            include_capture_bar=req.mission.include_capture_bar,
        )
        tasks = [
            InstrumentTask(
                symbol=item.symbol,
                dsl_code=item.dsl_code,
                market=item.market,
                settings=item.settings,
                metadata=item.metadata,
            )
            for item in req.instruments
        ]
        result = MultiSymbolAnalysisEngine.run(
            regime=regime,
            unit=unit,
            tasks=tasks,
            mission=mission,
            benchmark_market=req.benchmark_market,
            max_workers=req.max_workers,
        )
        return _json_safe(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/parameters/discover")
def stage1_discover(req: DiscoverRequest):
    try:
        return {"parameters": discover_dsl_parameters(req.dsl_code)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/baseline")
def stage1_baseline(req: BaselineRequest):
    try:
        full_market, provenance = _market_from_spec(req.market_spec)
        run_market = full_market
        run_source = provenance.source
        split_payload = None
        fraction = float(req.market_spec.holdout_fraction or 0.0)
        if fraction > 0:
            train_market, holdout_market, split_index = oos_registry.split_market(full_market, fraction)
            run_market = train_market
            run_source = str(train_market.get("_meta", {}).get("source", provenance.source + "#train"))
        experiment = factory.baseline(
            intent=req.intent,
            dsl_code=req.dsl_code,
            market=run_market,
            instrument=provenance.instrument,
            timeframe=provenance.timeframe,
            source=run_source,
            settings=req.settings,
            adjustment_policy=provenance.adjustment_policy,
            session=provenance.session,
            knowledge_cutoff=provenance.knowledge_cutoff,
        )
        if fraction > 0:
            split_payload = oos_registry.bind_split(
                experiment["root_id"], full_market, train_market, holdout_market, fraction, split_index
            )
        return {
            "status": "success",
            "experiment": experiment,
            "chart": factory.chart_audit(experiment),
            "chart_document": _chart_document_for_experiment(experiment),
            "evidence": EvidenceBuilder.build(experiment),
            "oos_split": split_payload,
        }
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
        return {
            "status": "success",
            **result,
            "chart": factory.chart_audit(result["experiment"]),
            "chart_document": _chart_document_for_experiment(result["experiment"]),
            "evidence": EvidenceBuilder.build(result["experiment"], result["study"]),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/seeker-sessions")
def stage1_seek_session_create(req: SeekSessionCreateRequest):
    try:
        return resumable_seeker.create(
            parent_experiment_id=req.experiment_id,
            parameter_specs=req.parameters,
            method=req.method,
            objective=req.objective,
            seed=req.seed,
            max_candidates=req.max_candidates,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/seeker-sessions/{session_id}")
def stage1_seek_session_get(session_id: int):
    try:
        return {"session": resumable_seeker.get(session_id), "top": resumable_seeker.candidates(session_id)}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/stage1/seeker-sessions/{session_id}/process")
def stage1_seek_session_process(session_id: int, req: SeekSessionProcessRequest):
    try:
        result = resumable_seeker.process(session_id, req.batch_size)
        if result.get("experiment"):
            result["chart"] = factory.chart_audit(result["experiment"])
            result["chart_document"] = _chart_document_for_experiment(result["experiment"])
            result["evidence"] = EvidenceBuilder.build(result["experiment"], result["session"])
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/seeker-sessions/{session_id}/cancel")
def stage1_seek_session_cancel(session_id: int):
    try:
        return resumable_seeker.cancel(session_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/seeker-sessions/{session_id}/resume")
def stage1_seek_session_resume(session_id: int):
    try:
        return resumable_seeker.resume(session_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/feedback")
def stage1_feedback(req: FeedbackRequest):
    try:
        package = factory.feedback_package(req.experiment_id, target_return=req.target_return)
        current = factory.store.get_experiment(req.experiment_id)
        evidence = EvidenceBuilder.build(current)
        raw_history = llm_memory.prompt_history_context(package["root_id"])
        rejected = hypothesis_memory.rejected_memory(package["root_id"], 30)
        package["evidence"] = evidence
        package["previous_raw_exchanges"] = raw_history
        package["rejected_hypotheses"] = rejected
        package["prompt"] += "\n\n[구조화 Evidence Bundle]\n" + json.dumps(evidence, ensure_ascii=False, indent=2)
        package["prompt"] += "\n\n[이전 raw LLM Prompt/Response 기록]\n" + raw_history
        package["prompt"] += "\n\n[이전 실패/거절 가설]\n" + json.dumps(rejected, ensure_ascii=False, indent=2)
        return package
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/apply-llm")
def stage1_apply_llm(req: ApplyLLMRequest):
    before = None
    try:
        market, before = _market_for_experiment(req.experiment_id)
        similar = hypothesis_memory.similar_prior(before["root_id"], req.hypothesis) if req.hypothesis else []
        result = factory.apply_llm_response(
            experiment_id=req.experiment_id,
            llm_response=req.llm_response,
            market=market,
            hypothesis=req.hypothesis,
            expected_effect=req.expected_effect,
            promote=req.promote,
        )
        structural_diff = summarize_dsl_change(before["dsl_code"], result["experiment"]["dsl_code"])
        exchange_id = llm_memory.record(
            before_experiment_id=req.experiment_id,
            after_experiment_id=result["experiment"]["id"],
            prompt_text=req.prompt_text,
            response_text=req.llm_response,
            hypothesis=req.hypothesis,
            status=result["verdict"],
        )
        return {
            "status": "success",
            **result,
            "exchange_id": exchange_id,
            "structural_diff": structural_diff,
            "similar_prior_hypotheses": similar,
            "chart": factory.chart_audit(result["experiment"]),
            "chart_document": _chart_document_for_experiment(result["experiment"]),
            "evidence": EvidenceBuilder.build(result["experiment"]),
        }
    except (DSLParseError, DSLRuntimeError, ValueError) as exc:
        if before is not None:
            verdict = (
                "INVALID_DSL"
                if isinstance(exc, (DSLParseError, DSLRuntimeError)) or "DSL" in str(exc) or "strategy" in str(exc)
                else "ENGINE_BLOCKED"
            )
            _record_failed_llm_episode(before, req, verdict, str(exc))
            try:
                llm_memory.record(
                    before_experiment_id=req.experiment_id,
                    after_experiment_id=None,
                    prompt_text=req.prompt_text,
                    response_text=req.llm_response,
                    hypothesis=req.hypothesis,
                    status=verdict,
                )
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        if before is not None:
            _record_failed_llm_episode(before, req, "ENGINE_BLOCKED", str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/stage1/promote")
def stage1_promote(req: PromoteRequest):
    try:
        return {"status": "success", "head": factory.store.promote(req.experiment_id)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/stop-state")
def stage1_stop(req: StopRequest):
    try:
        experiment = factory.store.get_experiment(req.experiment_id)
        return {
            "state": factory.stop_state(
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
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/target-loops")
def stage1_target_loop_create(req: TargetLoopCreateRequest):
    try:
        return target_loops.create(
            root_id=req.root_id,
            target_return=req.target_return,
            iteration_limit=req.iteration_limit,
            backtest_budget=req.backtest_budget,
            no_improvement_limit=req.no_improvement_limit,
            oos_degradation_limit_pct=req.oos_degradation_limit_pct,
            duplicate_hypothesis_limit=req.duplicate_hypothesis_limit,
            parameter_spike_limit=req.parameter_spike_limit,
        )
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
        return target_loops.observe(
            loop_id=loop_id,
            experiment_id=req.experiment_id,
            backtests_used_delta=req.backtests_used_delta,
            accepted=req.accepted,
            plateau=req.plateau,
            engine_blocked=req.engine_blocked,
            oos_return_pct=req.oos_return_pct,
            duplicate_hypothesis=req.duplicate_hypothesis,
            parameter_spike_ratio=req.parameter_spike_ratio,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/stage1/oos/{experiment_id}")
def stage1_oos_evaluate(experiment_id: int):
    try:
        evaluation = oos_registry.evaluate(experiment_id)
        return {
            "status": "success",
            "experiment_id": experiment_id,
            "split": evaluation["split"],
            "result": evaluation["result"],
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/stage1/oos/{experiment_id}")
def stage1_oos_result(experiment_id: int):
    try:
        experiment = factory.store.get_experiment(experiment_id)
        return {
            "split": oos_registry.get_split(experiment["root_id"]),
            "evaluation": oos_registry.result(experiment_id),
        }
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/stage1/chart-document/{experiment_id}")
def stage1_chart_document(experiment_id: int):
    try:
        experiment = factory.store.get_experiment(experiment_id)
        return {"experiment_id": experiment_id, "document": _chart_document_for_experiment(experiment)}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


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
        return {
            "experiment": experiment,
            "lineage": factory.store.lineage(experiment_id),
            "chart": factory.chart_audit(experiment),
            "chart_document": _chart_document_for_experiment(experiment),
            "evidence": EvidenceBuilder.build(experiment),
            "oos": oos_registry.result(experiment_id),
        }
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/stage1/methodology/{root_id}")
def stage1_methodology(root_id: int):
    try:
        summary = methodology.summarize(root_id)
        summary["raw_llm_exchanges"] = llm_memory.recent(root_id, 100)
        summary["rejected_hypotheses"] = hypothesis_memory.rejected_memory(root_id, 100)
        return summary
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("stage1_main:app", host="127.0.0.1", port=8000, reload=False)
