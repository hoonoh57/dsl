"""Persistent human-mediated target-return improvement loop state."""
from __future__ import annotations

import json
import time
from typing import Optional

from core.strategy_factory import StrategyFactory, StrategyFactoryStore


class TargetLoopService:
    """Track research progress without mutating the applied strategy implicitly.

    The loop may identify/recommend a better candidate, but the Experiment Store
    current head is changed only by the dedicated explicit Promote action.  This
    prevents Seeker/LLM iteration from silently overwriting the applied best.
    """

    def __init__(self, factory: Optional[StrategyFactory] = None):
        self.factory = factory or StrategyFactory()
        self.store: StrategyFactoryStore = self.factory.store

    def create(
        self,
        *,
        root_id: int,
        target_return: float,
        iteration_limit: int = 20,
        backtest_budget: int = 50000,
        no_improvement_limit: int = 5,
        oos_degradation_limit_pct: float = 5.0,
        duplicate_hypothesis_limit: int = 2,
        parameter_spike_limit: float = 3.0,
    ) -> dict:
        head = self.store.current_head(root_id)
        head_return = float(head["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        state = {
            "status": "CONTINUE",
            "root_id": root_id,
            "current_experiment_id": head["id"],
            "applied_head_experiment_id": head["id"],
            "best_experiment_id": head["id"],
            "iteration": 0,
            "backtests_used": 0,
            "consecutive_no_improvement": 0,
            "duplicate_hypothesis_count": 0,
            "last_return_pct": head_return,
            "best_return_pct": head_return,
            "last_oos_return_pct": None,
            "best_oos_return_pct": None,
            "last_parameter_spike_ratio": None,
            "guards": {
                "oos_degradation_limit_pct": float(oos_degradation_limit_pct),
                "duplicate_hypothesis_limit": int(duplicate_hypothesis_limit),
                "parameter_spike_limit": float(parameter_spike_limit),
            },
            "pending_action": "RUN_SEEKER_OR_GENERATE_FEEDBACK",
        }
        conn = self.store.connect()
        cur = conn.execute(
            """INSERT INTO stage1_target_loops(root_id,target_return,iteration_limit,backtest_budget,
               no_improvement_limit,state_json,created_at) VALUES (?,?,?,?,?,?,?)""",
            (
                root_id,
                float(target_return),
                int(iteration_limit),
                int(backtest_budget),
                int(no_improvement_limit),
                json.dumps(state, ensure_ascii=False),
                time.time(),
            ),
        )
        loop_id = int(cur.lastrowid)
        conn.commit()
        conn.close()
        return self.get(loop_id)

    def get(self, loop_id: int) -> dict:
        conn = self.store.connect()
        row = conn.execute("SELECT * FROM stage1_target_loops WHERE id=?", (loop_id,)).fetchone()
        conn.close()
        if not row:
            raise ValueError(f"target loop가 없습니다: {loop_id}")
        item = dict(row)
        item["state"] = json.loads(item.pop("state_json"))
        # Applied head is a mutable pointer owned by stage1_heads, not historical
        # loop evidence.  Always project the live pointer when reading loop state
        # so explicit Promote is visible immediately without requiring another
        # observe iteration.
        try:
            head_id = int(self.store.current_head(int(item["root_id"]))["id"])
            item["state"]["applied_head_experiment_id"] = head_id
            if isinstance(item["state"].get("last_observation"), dict):
                observation = dict(item["state"]["last_observation"])
                observation["promotion_required"] = int(observation.get("experiment_id", -1)) != head_id
                item["state"]["last_observation"] = observation
        except Exception:
            pass
        return item

    def _save(self, loop: dict, state: dict):
        conn = self.store.connect()
        conn.execute(
            "UPDATE stage1_target_loops SET state_json=? WHERE id=?",
            (json.dumps(state, ensure_ascii=False), loop["id"]),
        )
        conn.commit()
        conn.close()
        return self.get(loop["id"])

    def observe(
        self,
        *,
        loop_id: int,
        experiment_id: int,
        backtests_used_delta: int = 1,
        accepted: Optional[bool] = None,
        plateau: bool = False,
        engine_blocked: bool = False,
        oos_return_pct: Optional[float] = None,
        duplicate_hypothesis: bool = False,
        parameter_spike_ratio: Optional[float] = None,
    ) -> dict:
        loop = self.get(loop_id)
        state = dict(loop["state"])
        experiment = self.store.get_experiment(experiment_id)
        if experiment["root_id"] != loop["root_id"]:
            raise ValueError("target loop와 experiment root가 다릅니다.")

        current_return = float(experiment["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        improved = current_return > float(state.get("best_return_pct", float("-inf")))
        state["current_experiment_id"] = experiment_id
        state["last_return_pct"] = current_return
        state["iteration"] = int(state.get("iteration", 0)) + 1
        state["backtests_used"] = int(state.get("backtests_used", 0)) + max(0, int(backtests_used_delta))

        if improved:
            state["best_return_pct"] = current_return
            state["best_experiment_id"] = experiment_id
            state["consecutive_no_improvement"] = 0
        else:
            state["consecutive_no_improvement"] = int(state.get("consecutive_no_improvement", 0)) + 1

        try:
            state["applied_head_experiment_id"] = self.store.current_head(loop["root_id"])["id"]
        except Exception:
            pass

        if duplicate_hypothesis:
            state["duplicate_hypothesis_count"] = int(state.get("duplicate_hypothesis_count", 0)) + 1
        else:
            state["duplicate_hypothesis_count"] = 0

        prior_best_oos = state.get("best_oos_return_pct")
        if oos_return_pct is not None:
            state["last_oos_return_pct"] = float(oos_return_pct)
            if prior_best_oos is None or float(oos_return_pct) > float(prior_best_oos):
                state["best_oos_return_pct"] = float(oos_return_pct)
        if parameter_spike_ratio is not None:
            state["last_parameter_spike_ratio"] = float(parameter_spike_ratio)

        guards = dict(state.get("guards") or {})
        status = self.factory.stop_state(
            experiment,
            target_return=float(loop["target_return"]),
            iteration=state["iteration"],
            iteration_limit=int(loop["iteration_limit"]),
            backtests_used=state["backtests_used"],
            backtest_budget=int(loop["backtest_budget"]),
            consecutive_no_improvement=state["consecutive_no_improvement"],
            no_improvement_limit=int(loop["no_improvement_limit"]),
            plateau=plateau,
            engine_blocked=engine_blocked,
        )

        if status == "CONTINUE" and oos_return_pct is not None and prior_best_oos is not None:
            degradation = float(prior_best_oos) - float(oos_return_pct)
            if degradation > float(guards.get("oos_degradation_limit_pct", 5.0)):
                status = "OOS_DEGRADED"
        if status == "CONTINUE" and int(state.get("duplicate_hypothesis_count", 0)) >= int(
            guards.get("duplicate_hypothesis_limit", 2)
        ):
            status = "NO_NEW_HYPOTHESIS"
        if status == "CONTINUE" and parameter_spike_ratio is not None and float(parameter_spike_ratio) >= float(
            guards.get("parameter_spike_limit", 3.0)
        ):
            status = "PARAMETER_INSTABILITY"

        state["status"] = status
        state["pending_action"] = "STOP" if status != "CONTINUE" else "RUN_SEEKER_OR_GENERATE_FEEDBACK"
        state["last_observation"] = {
            "experiment_id": experiment_id,
            "improved_is": improved,
            "candidate_recommended": accepted is True,
            "promotion_required": experiment_id != state.get("applied_head_experiment_id"),
            "oos_return_pct": oos_return_pct,
            "duplicate_hypothesis": bool(duplicate_hypothesis),
            "parameter_spike_ratio": parameter_spike_ratio,
        }
        return self._save(loop, state)
