"""Production-oriented tactical research orchestration.

This service composes a frozen cohort, canonical market provider and the
validated multi-symbol engine. Outcome labels are merged only after execution.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import math
from statistics import mean
from typing import Any, Mapping, Optional

from core.multi_symbol import (
    CommonPolicySpec,
    InstrumentTask,
    MissionSpec,
    RegimeContext,
    TacticalUnitSpec,
)
from core.tactical_market import SessionMarketProvider
from core.tactical_providers import TacticalCohortBundle
from core.tactical_service import TacticalScenarioService


def _session_date(snapshot_as_of: str) -> str:
    digits = "".join(ch for ch in str(snapshot_as_of) if ch.isdigit())
    if len(digits) < 8:
        raise ValueError(f"snapshot as_of에서 거래일을 읽지 못했습니다: {snapshot_as_of}")
    return digits[:8]


def _after_capture_hhmmss(snapshot_as_of: str) -> int:
    digits = "".join(ch for ch in str(snapshot_as_of) if ch.isdigit())
    if len(digits) < 14:
        raise ValueError(f"snapshot as_of는 YYYYMMDDHHMMSS여야 합니다: {snapshot_as_of}")
    dt = datetime.strptime(digits[:14], "%Y%m%d%H%M%S") + timedelta(seconds=1)
    if dt.strftime("%Y%m%d") != digits[:8]:
        raise ValueError("capture 직후가 다음 거래일로 넘어가는 cohort는 지원하지 않습니다.")
    return int(dt.strftime("%H%M%S"))


def _evaluate_official_outcomes(result: Mapping[str, Any], bundle: TacticalCohortBundle) -> dict:
    rows = list(result.get("results") or [])
    official_positive = 0
    profitable = 0
    positive_profitable = 0
    retained_move_ratios = []
    strategy_returns = []
    by_symbol = {}
    for row in rows:
        symbol = str(row["symbol"])
        outcome = dict(bundle.outcomes.get(symbol) or {})
        if not outcome:
            raise ValueError(f"{symbol}: 공식 outcome이 누락되었습니다.")
        strategy_return = float(row.get("strategy_return_pct") or 0.0)
        strategy_returns.append(strategy_return)
        is_profitable = strategy_return > 0.0
        is_positive = int(outcome.get("label_10") or 0) == 1
        profitable += int(is_profitable)
        official_positive += int(is_positive)
        positive_profitable += int(is_positive and is_profitable)
        max_ret = outcome.get("max_ret_in_period")
        ratio = None
        if is_positive and max_ret is not None and float(max_ret) > 0:
            ratio = max(0.0, strategy_return) / float(max_ret)
            retained_move_ratios.append(ratio)
        by_symbol[symbol] = {
            "official": outcome,
            "strategy_return_pct": strategy_return,
            "strategy_profitable": is_profitable,
            "mission_positive": is_positive,
            "retained_move_ratio": ratio,
        }
    return {
        "schema": "tactical_1516_evaluation/v1",
        "cohort_symbols": len(rows),
        "official_mission_positive": official_positive,
        "strategy_profitable_symbols": profitable,
        "positive_and_profitable": positive_profitable,
        "mission_positive_profitable_retention": (
            positive_profitable / official_positive if official_positive else None
        ),
        "profitable_precision_against_mission": (
            positive_profitable / profitable if profitable else None
        ),
        "average_positive_retained_move_ratio": (
            float(mean(retained_move_ratios)) if retained_move_ratios else None
        ),
        "average_strategy_return_pct": (
            float(mean(strategy_returns)) if strategy_returns else 0.0
        ),
        "by_symbol": by_symbol,
        "cohort_snapshot_hash": bundle.snapshot.snapshot_hash,
        "outcome_hash": bundle.outcome_hash,
    }


def _feature_ranking(result: Mapping[str, Any], feature_name: str) -> list[dict]:
    rows = list(result.get("results") or [])
    original = {str(item.get("symbol")): index for index, item in enumerate(rows)}

    def score(item: Mapping[str, Any]) -> float:
        features = (item.get("metadata") or {}).get("point_in_time_features") or {}
        value = features.get(feature_name)
        if value is None:
            return float("-inf")
        try:
            number = float(value)
        except Exception:
            return float("-inf")
        return number if math.isfinite(number) else float("-inf")

    ordered = sorted(
        rows,
        key=lambda item: (-score(item), original.get(str(item.get("symbol")), 10**9)),
    )
    ranking = []
    for index, item in enumerate(ordered):
        value = score(item)
        ranking.append(
            {
                "rank": index + 1,
                "symbol": str(item.get("symbol")),
                "rank_by": f"feature:{feature_name}",
                "score": None if value == float("-inf") else value,
            }
        )
    return ranking


class TacticalResearchService:
    def __init__(self, scenario_service: Optional[TacticalScenarioService] = None):
        self.scenario_service = scenario_service or TacticalScenarioService()

    def run_1516(
        self,
        *,
        bundle: TacticalCohortBundle,
        dsl_code: str,
        market_provider: SessionMarketProvider,
        timeframe: str = "5m",
        required_bars: int = 180,
        entry_end_time: int = 151000,
        max_workers: int = 4,
        settings: Optional[Mapping[str, Any]] = None,
        benchmark_symbol: str = "",
        rank_by: str = "feature:search_volume",
        persist: bool = True,
    ) -> dict:
        if not dsl_code.strip():
            raise ValueError("1516 tactical run DSL이 비어 있습니다.")
        snapshot = bundle.snapshot
        if not snapshot.members:
            raise ValueError("1516 cohort가 비어 있습니다.")
        snapshot_symbols = tuple(member.symbol for member in snapshot.members)
        if set(bundle.outcomes) != set(snapshot_symbols):
            raise ValueError("1516 cohort와 official outcome 종목 집합이 일치하지 않습니다.")
        capture_times = {member.capture_time for member in snapshot.members}
        if len(capture_times) != 1 or next(iter(capture_times)) != snapshot.as_of:
            raise ValueError(
                "1516 exact-group run은 모든 종목의 capture_time이 snapshot as_of와 같아야 합니다."
            )
        session_date = _session_date(snapshot.as_of)
        entry_start_time = _after_capture_hhmmss(snapshot.as_of)
        if int(entry_end_time) <= entry_start_time:
            raise ValueError(
                f"entry_end_time({entry_end_time})은 capture 직후({entry_start_time})보다 커야 합니다."
            )

        rank_by = str(rank_by or "").strip()
        if not (rank_by.startswith("feature:") and rank_by.split(":", 1)[1].strip()):
            engine_rank_by = rank_by or "relative_strength_pct"
        else:
            # Feature ranking is computed after deterministic execution from the
            # frozen point-in-time metadata only. The instrument engine keeps
            # its existing validated rank contract unchanged.
            engine_rank_by = "relative_strength_pct"

        markets: dict[str, dict] = {}
        tasks = []
        common_settings = dict(settings or {})
        for member in snapshot.members:
            market = market_provider.load_session(
                symbol=member.symbol,
                session_date=session_date,
                timeframe=timeframe,
                required_bars=int(required_bars),
                end_time="153000",
            )
            markets[member.symbol] = market
            task_metadata = {
                "cohort_snapshot_hash": snapshot.snapshot_hash,
                "capture_time": member.capture_time,
                "point_in_time_features": dict(member.features),
            }
            tasks.append(
                InstrumentTask(
                    symbol=member.symbol,
                    dsl_code=dsl_code,
                    market=market,
                    settings=common_settings,
                    metadata=task_metadata,
                )
            )

        benchmark_market = None
        benchmark_symbol = str(benchmark_symbol or "").strip()
        if benchmark_symbol:
            benchmark_market = market_provider.load_session(
                symbol=benchmark_symbol,
                session_date=session_date,
                timeframe=timeframe,
                required_bars=int(required_bars),
                end_time="153000",
            )
            markets[benchmark_symbol] = benchmark_market

        unit = TacticalUnitSpec(
            unit_id=snapshot.unit_id,
            unit_type="1516_CONDITION_COHORT",
            symbols=snapshot_symbols,
            capture_times={},
            reference_symbol=benchmark_symbol,
            rank_by=engine_rank_by,
            metadata={
                "cohort_snapshot_hash": snapshot.snapshot_hash,
                "capture_as_of": snapshot.as_of,
                "cohort_source": snapshot.source,
                "selection_rank_by": rank_by,
                "outcome_authority": "external_post_execution",
            },
        )
        regime = RegimeContext(
            regime_id=f"1516_SESSION:{session_date}",
            state="OBSERVED_SESSION",
            active=True,
            eligible_units=(snapshot.unit_id,),
            windows=(),
            evidence={
                "cohort_snapshot_hash": snapshot.snapshot_hash,
                "capture_as_of": snapshot.as_of,
            },
        )
        common_policy = CommonPolicySpec(
            entry_start_time=entry_start_time,
            entry_end_time=int(entry_end_time),
        )
        mission = MissionSpec(
            name="1516_OFFICIAL_LABEL10_POST_EXECUTION",
            mfe_threshold_pct=None,
            capture_price_field="close",
            include_capture_bar=False,
        )

        # Engine input contains cohort features/capture identity only. Official
        # return labels remain in ``bundle.outcomes`` and are merged afterward.
        response = self.scenario_service.analyze(
            regime=regime,
            unit=unit,
            tasks=tasks,
            mission=mission,
            common_policy=common_policy,
            benchmark_market=benchmark_market,
            max_workers=int(max_workers),
            persist=bool(persist),
        )
        engine_result = response["result"]
        evaluation = _evaluate_official_outcomes(engine_result, bundle)
        enriched = deepcopy(engine_result)
        enriched["engine_ranking"] = deepcopy(engine_result.get("ranking") or [])
        if rank_by.startswith("feature:"):
            enriched["ranking"] = _feature_ranking(
                enriched, rank_by.split(":", 1)[1].strip()
            )
        for row in enriched.get("results", []):
            symbol = str(row["symbol"])
            row["official_outcome"] = dict(bundle.outcomes[symbol])
        enriched["official_evaluation"] = evaluation
        enriched["cohort_snapshot"] = bundle.public_snapshot()
        return {
            "result": enriched,
            "evaluation": evaluation,
            "scenario_record": response.get("scenario_record"),
            "run_record": response.get("run_record"),
            "markets": markets,
        }
