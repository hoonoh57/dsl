"""Application service for deterministic multi-layer tactical scenario runs."""
from __future__ import annotations

from typing import Mapping, Optional, Sequence, Any

from core.multi_symbol import (
    CommonPolicySpec,
    InstrumentTask,
    MissionSpec,
    MultiSymbolAnalysisEngine,
    RegimeContext,
    TacticalUnitSpec,
)
from core.tactical_store import TacticalScenarioStore


class TacticalScenarioService:
    """Run a complete tactical scenario and persist immutable evidence.

    Persistence is explicit at this service boundary.  Promotion remains a
    separate operation so a completed run never becomes the tactical head just
    because it was executed.
    """

    def __init__(self, store: Optional[TacticalScenarioStore] = None):
        self.store = store or TacticalScenarioStore()

    def analyze(
        self,
        *,
        regime: RegimeContext,
        unit: TacticalUnitSpec,
        tasks: Sequence[InstrumentTask],
        mission: Optional[MissionSpec] = None,
        common_policy: Optional[CommonPolicySpec] = None,
        benchmark_market: Optional[Mapping[str, Any]] = None,
        max_workers: int = 4,
        persist: bool = True,
    ) -> dict:
        result = MultiSymbolAnalysisEngine.run(
            regime=regime,
            unit=unit,
            tasks=tasks,
            mission=mission,
            common_policy=common_policy,
            benchmark_market=benchmark_market,
            max_workers=max_workers,
        )
        if not persist:
            return {"result": result, "scenario_record": None, "run_record": None}
        scenario = self.store.create_scenario(result["scenario_definition"])
        run = self.store.record_run(scenario["id"], result)
        return {"result": result, "scenario_record": scenario, "run_record": run}

    def promote(self, run_id: int) -> dict:
        return self.store.promote(run_id)

    def head(self, unit_id: str):
        return self.store.get_head(unit_id)
