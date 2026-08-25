"""Stage 1 methodology validation summaries.

This service reports descriptive evidence for A/B/C comparison. It does not
claim predictive edge until OOS and multi-strategy validation are available.
"""
from __future__ import annotations

import json
from statistics import mean

from core.stage1_hypothesis_memory import similarity
from core.strategy_factory import StrategyFactoryStore


class MethodologyValidator:
    def __init__(self, store: StrategyFactoryStore):
        self.store = store

    @staticmethod
    def _ret(experiment: dict) -> float:
        return float(experiment.get("result", {}).get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)

    @staticmethod
    def _table_exists(conn, name: str) -> bool:
        row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
        return bool(row)

    def summarize(self, root_id: int) -> dict:
        experiments = list(reversed(self.store.list_experiments(root_id=root_id, limit=10000)))
        if not experiments:
            raise ValueError("methodology 대상 experiment가 없습니다.")
        by_id = {int(item["id"]): item for item in experiments}
        baseline = next((item for item in experiments if item["operation"] == "BASELINE"), experiments[0])
        seeker = [item for item in experiments if item["operation"] == "SEEKER_BEST"]
        structural = [item for item in experiments if item["operation"] == "LLM_STRUCTURAL"]
        episodes = list(reversed(self.store.episodes_for_root(root_id, 10000)))

        baseline_return = self._ret(baseline)
        seeker_returns = [self._ret(item) for item in seeker]
        structural_returns = [self._ret(item) for item in structural]
        seeker_best = max(seeker_returns, default=baseline_return)
        c_best = max(structural_returns + seeker_returns + [baseline_return])

        accepted = [item for item in episodes if item.get("verdict") == "ACCEPTED_IMPROVEMENT"]
        rejected = [item for item in episodes if str(item.get("verdict", "")).startswith("REJECTED")]
        invalid = [item for item in episodes if item.get("verdict") == "INVALID_DSL"]
        inferred_regressions = []
        for item in episodes:
            before = by_id.get(int(item["before_experiment_id"])) if item.get("before_experiment_id") else None
            after = by_id.get(int(item["after_experiment_id"])) if item.get("after_experiment_id") else None
            if before and after and self._ret(after) < self._ret(before) - 1e-12:
                inferred_regressions.append(item)

        duplicate_pairs = 0
        comparable = 0
        hypotheses = [str(item.get("hypothesis") or "").strip() for item in episodes if str(item.get("hypothesis") or "").strip()]
        for index, current in enumerate(hypotheses):
            if index == 0:
                continue
            comparable += 1
            if max((similarity(current, prior) for prior in hypotheses[:index]), default=0.0) >= 0.55:
                duplicate_pairs += 1

        conn = self.store.connect()
        search_rows = conn.execute("""SELECT s.*, COUNT(c.id) AS candidate_count
            FROM stage1_search_studies s LEFT JOIN stage1_search_candidates c ON c.study_id=s.id
            JOIN stage1_experiments e ON e.id=s.parent_experiment_id
            WHERE e.root_id=? GROUP BY s.id ORDER BY s.id""", (root_id,)).fetchall()
        session_rows = []
        if self._table_exists(conn, "stage1_seek_sessions"):
            session_rows = conn.execute("""SELECT ss.* FROM stage1_seek_sessions ss
                JOIN stage1_experiments e ON e.id=ss.parent_experiment_id
                WHERE e.root_id=? ORDER BY ss.id""", (root_id,)).fetchall()
        loop_rows = conn.execute("SELECT * FROM stage1_target_loops WHERE root_id=? ORDER BY id", (root_id,)).fetchall()
        oos_rows = []
        if self._table_exists(conn, "stage1_oos_results"):
            oos_rows = conn.execute("SELECT * FROM stage1_oos_results WHERE root_id=? ORDER BY evaluated_at", (root_id,)).fetchall()
        conn.close()

        search_candidate_budget = sum(int(row["candidate_count"] or 0) for row in search_rows)
        session_budget = sum(int(row["cursor"] or 0) for row in session_rows)
        backtest_budget_used = max(search_candidate_budget, session_budget)
        loop_states = [json.loads(row["state_json"] or "{}") for row in loop_rows]
        if loop_states:
            backtest_budget_used = max(backtest_budget_used, max(int(item.get("backtests_used", 0) or 0) for item in loop_states))

        oos_returns = {}
        for row in oos_rows:
            payload = json.loads(row["result_json"] or "{}")
            oos_returns[int(row["experiment_id"])] = float(payload.get("metrics_numeric", {}).get("total_return_pct", 0.0) or 0.0)
        baseline_oos = oos_returns.get(int(baseline["id"]))
        seeker_oos = [oos_returns[int(item["id"])] for item in seeker if int(item["id"]) in oos_returns]
        structural_oos = [oos_returns[int(item["id"])] for item in structural if int(item["id"]) in oos_returns]
        overfit_rejections = 0
        for item in episodes:
            before_id = item.get("before_experiment_id")
            after_id = item.get("after_experiment_id")
            if before_id in oos_returns and after_id in oos_returns:
                before = by_id.get(int(before_id)); after = by_id.get(int(after_id))
                if before and after and self._ret(after) > self._ret(before) and oos_returns[int(after_id)] < oos_returns[int(before_id)]:
                    overfit_rejections += 1

        oos_available = bool(oos_rows)
        oos_summary = {
            "available": oos_available,
            "evaluated_experiments": len(oos_rows),
            "A_baseline_return_pct": baseline_oos,
            "B_best_seeker_return_pct": max(seeker_oos) if seeker_oos else None,
            "C_best_structural_return_pct": max(structural_oos) if structural_oos else None,
            "reason": None if oos_available else "No immutable holdout evaluation has been recorded for this root.",
        }

        return {
            "schema": "stage1_methodology_validation/v3",
            "root_id": root_id,
            "groups": {
                "A_baseline_only": {"best_return_pct": baseline_return, "experiments": 1},
                "B_baseline_plus_seeker": {"best_return_pct": seeker_best, "experiments": len(seeker)},
                "C_seeker_plus_llm_structural": {"best_return_pct": c_best, "experiments": len(structural)},
            },
            "increments": {
                "seeker_over_baseline_pct": seeker_best - baseline_return,
                "llm_loop_over_seeker_pct": c_best - seeker_best,
            },
            "structural_iterations": len(episodes),
            "accepted_structural_iterations": len(accepted),
            "rejected_structural_iterations": len(rejected),
            "invalid_dsl_iterations": len(invalid),
            "regression_iterations": len(inferred_regressions),
            "overfit_rejections": overfit_rejections,
            "structural_success_rate": len(accepted) / len(episodes) if episodes else 0.0,
            "regression_rate": len(inferred_regressions) / len(episodes) if episodes else 0.0,
            "overfit_rejection_rate": overfit_rejections / len(episodes) if episodes else 0.0,
            "duplicate_hypothesis_rate": duplicate_pairs / comparable if comparable else 0.0,
            "backtests_used_observed": backtest_budget_used,
            "search_studies": len(search_rows),
            "resumable_search_sessions": len(session_rows),
            "target_loops": len(loop_rows),
            "iterations_to_first_accepted": next((index + 1 for index, item in enumerate(episodes) if item.get("verdict") == "ACCEPTED_IMPROVEMENT"), None),
            "average_structural_return_pct": mean(structural_returns) if structural_returns else None,
            "oos": oos_summary,
            "claim": "descriptive_only_until_OOS_and_multi_strategy_methodology_validation",
        }
