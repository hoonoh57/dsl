"""Persistent human-mediated target-return improvement loop state."""
from __future__ import annotations
import json
import sqlite3
import time
from typing import Optional

from core.strategy_factory import StrategyFactory, StrategyFactoryStore


class TargetLoopService:
    def __init__(self, factory: Optional[StrategyFactory] = None):
        self.factory = factory or StrategyFactory()
        self.store: StrategyFactoryStore = self.factory.store

    def create(self, *, root_id: int, target_return: float, iteration_limit: int = 20,
               backtest_budget: int = 50000, no_improvement_limit: int = 5) -> dict:
        head = self.store.current_head(root_id)
        state = {
            "status": "CONTINUE",
            "root_id": root_id,
            "current_experiment_id": head["id"],
            "best_experiment_id": head["id"],
            "iteration": 0,
            "backtests_used": 0,
            "consecutive_no_improvement": 0,
            "last_return_pct": float(head["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0),
            "best_return_pct": float(head["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0),
            "pending_action": "RUN_SEEKER_OR_GENERATE_FEEDBACK",
        }
        conn = self.store.connect()
        cur = conn.execute("""INSERT INTO stage1_target_loops(root_id,target_return,iteration_limit,backtest_budget,
                            no_improvement_limit,state_json,created_at) VALUES (?,?,?,?,?,?,?)""",
                           (root_id, float(target_return), int(iteration_limit), int(backtest_budget),
                            int(no_improvement_limit), json.dumps(state, ensure_ascii=False), time.time()))
        loop_id = int(cur.lastrowid); conn.commit(); conn.close()
        return self.get(loop_id)

    def get(self, loop_id: int) -> dict:
        conn = self.store.connect(); row = conn.execute("SELECT * FROM stage1_target_loops WHERE id=?", (loop_id,)).fetchone(); conn.close()
        if not row: raise ValueError(f"target loop가 없습니다: {loop_id}")
        item = dict(row); item["state"] = json.loads(item.pop("state_json")); return item

    def _save(self, loop: dict, state: dict):
        conn = self.store.connect(); conn.execute("UPDATE stage1_target_loops SET state_json=? WHERE id=?",
            (json.dumps(state, ensure_ascii=False), loop["id"])); conn.commit(); conn.close(); return self.get(loop["id"])

    def observe(self, *, loop_id: int, experiment_id: int, backtests_used_delta: int = 1,
                accepted: Optional[bool] = None, plateau: bool = False, engine_blocked: bool = False) -> dict:
        loop = self.get(loop_id); state = dict(loop["state"]); experiment = self.store.get_experiment(experiment_id)
        if experiment["root_id"] != loop["root_id"]: raise ValueError("target loop와 experiment root가 다릅니다.")
        current_return = float(experiment["result"].get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        improved = current_return > float(state.get("best_return_pct", float("-inf")))
        state["current_experiment_id"] = experiment_id
        state["last_return_pct"] = current_return
        state["iteration"] = int(state.get("iteration", 0)) + 1
        state["backtests_used"] = int(state.get("backtests_used", 0)) + max(0, int(backtests_used_delta))
        if improved:
            state["best_return_pct"] = current_return; state["best_experiment_id"] = experiment_id
            state["consecutive_no_improvement"] = 0
            if accepted is not False: self.store.promote(experiment_id)
        else:
            state["consecutive_no_improvement"] = int(state.get("consecutive_no_improvement", 0)) + 1
        status = self.factory.stop_state(experiment,
            target_return=float(loop["target_return"]), iteration=state["iteration"], iteration_limit=int(loop["iteration_limit"]),
            backtests_used=state["backtests_used"], backtest_budget=int(loop["backtest_budget"]),
            consecutive_no_improvement=state["consecutive_no_improvement"], no_improvement_limit=int(loop["no_improvement_limit"]),
            plateau=plateau, engine_blocked=engine_blocked)
        state["status"] = status
        state["pending_action"] = "STOP" if status != "CONTINUE" else "RUN_SEEKER_OR_GENERATE_FEEDBACK"
        return self._save(loop, state)
