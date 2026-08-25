#!/usr/bin/env python3
"""Deterministic live-stack smoke test for the Stage 1 Strategy Factory.

The harness intentionally uses only public HTTP contracts. It creates a new
isolated append-only smoke root, verifies immutable rejection, exercises one
valid structural LLM iteration followed by re-Seeker, and explicitly promotes
only the final candidate inside that disposable smoke root.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DSL = '''strategy "OperationalSmoke" {
    timeframe = "1d"
    input fast = 3
    input slow = 8
    f = ta.sma(close, fast)
    s = ta.sma(close, slow)
    long_entry = ta.crossover(f, s)
    long_exit = ta.crossunder(f, s)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''

REVISED_DSL = '''strategy "OperationalSmoke" {
    timeframe = "1d"
    input fast = 3
    input slow = 8
    f = ta.sma(close, fast)
    s = ta.sma(close, slow)
    regime = close > ta.sma(close, 20)
    long_entry = ta.crossover(f, s) and regime
    long_exit = ta.crossunder(f, s)
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


class SmokeFailure(RuntimeError):
    pass


@dataclass
class HttpResult:
    status: int
    body: Any


class Client:
    def __init__(self, base: str, timeout: float):
        self.base = base.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, payload: Any = None, expected=(200,)) -> HttpResult:
        url = self.base + path
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                status = int(response.status)
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            status = int(exc.code)
            raw = exc.read().decode("utf-8", errors="replace")
        except URLError as exc:
            raise SmokeFailure(f"HTTP connection failed: {url}: {exc.reason}") from exc
        if status not in expected:
            raise SmokeFailure(f"{method} {path} returned HTTP {status}: {raw[:500]}")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError as exc:
            raise SmokeFailure(f"{method} {path} did not return JSON: {raw[:300]}") from exc
        return HttpResult(status, body)

    def get(self, path: str, expected=(200,)) -> Any:
        return self.request("GET", path, expected=expected).body

    def post(self, path: str, payload: Any, expected=(200,)) -> HttpResult:
        return self.request("POST", path, payload, expected)

    def text(self, path: str) -> str:
        url = self.base + path
        try:
            with urlopen(Request(url, headers={"Accept": "text/html"}), timeout=self.timeout) as response:
                if int(response.status) != 200:
                    raise SmokeFailure(f"GET {path} returned HTTP {response.status}")
                return response.read().decode("utf-8")
        except (HTTPError, URLError) as exc:
            raise SmokeFailure(f"HTML connection failed: {url}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def complete_session(api: Client, session_id: int, batches=12) -> dict[str, Any]:
    for _ in range(batches):
        result = api.post(f"/api/stage1/seeker-sessions/{session_id}/process", {"batch_size": 2}).body
        if (result.get("session") or {}).get("status") == "COMPLETED":
            return result
        time.sleep(0.02)
    raise SmokeFailure(f"Seeker session {session_id} did not complete")


def run(stage1_base: str, chart_base: str, timeout: float) -> dict[str, Any]:
    api = Client(stage1_base, timeout)
    chart = Client(chart_base, timeout)

    health = api.get("/api/stage1/health")
    require(health.get("status") == "ready", "Stage 1 health is not ready")
    require(health.get("schema") == "stage1_factory/v1", "Stage 1 schema mismatch")
    require(health.get("execution_authority") == "BrokerEmulator", "Broker authority mismatch")
    require(health.get("chart_contract") == "chart-document/v1", "Chart contract mismatch")

    page = api.text("/stage1")
    require("Single-Symbol Strategy Factory" in page, "Stage 1 UI route is not the expected product page")

    chart_health = chart.get("/__cascade_health")
    require(chart_health.get("app") == "cascading-feature-solution", "Shared Chart SSOT health mismatch")
    viewer = chart.text("/src/shell/chart-document-viewer.html")
    require("Chart Document Viewer" in viewer and 'id="chart-host"' in viewer, "Shared Chart Document viewer is unavailable")

    baseline = api.post(
        "/api/stage1/baseline",
        {
            "intent": "SYSTEM_SMOKE_ISOLATED_ROOT",
            "dsl_code": DSL,
            "market_spec": {
                "source": "synthetic_fixture",
                "instrument": "SYSTEM_SMOKE",
                "timeframe": "1d",
                "bars": 180,
                "holdout_fraction": 0.20,
                "session": "regular",
                "adjustment_policy": "unspecified",
            },
            "settings": {
                "signal_mode": "next_open",
                "total_capital": 1_000_000.0,
                "allocation_pct": 50.0,
                "commission_pct": 0.015,
                "sell_tax_pct": 0.18,
                "slippage_pct": 0.02,
            },
        },
    ).body
    require(baseline.get("status") == "success", "Baseline did not succeed")
    base_experiment = baseline.get("experiment") or {}
    base_id = int(base_experiment.get("id") or 0)
    root_id = int(base_experiment.get("root_id") or 0)
    require(base_id > 0 and root_id == base_id, "Baseline root identity is invalid")
    require((baseline.get("chart_document") or {}).get("version") == "chart-document/v1", "Baseline Chart Document missing")
    require((baseline.get("evidence") or {}).get("schema") == "stage1_evidence/v3", "Baseline Evidence schema mismatch")
    require(bool(baseline.get("oos_split")), "Immutable holdout split was not created")

    discovered = api.post("/api/stage1/parameters/discover", {"dsl_code": DSL}).body
    names = [item.get("name") for item in discovered.get("parameters", [])]
    require(names == ["fast", "slow"], f"Input discovery mismatch: {names}")

    session = api.post(
        "/api/stage1/seeker-sessions",
        {
            "experiment_id": base_id,
            "parameters": [
                {"name": "fast", "target": "dsl", "values": [2, 3]},
                {"name": "slow", "target": "dsl", "values": [7, 8]},
            ],
            "method": "grid",
            "objective": "MAX_RETURN",
            "seed": 42,
            "max_candidates": 16,
        },
    ).body
    session_id = int(session.get("id") or 0)
    require(session_id > 0 and session.get("total_candidates") == 4, "Seeker session plan mismatch")

    completed = complete_session(api, session_id)
    best = completed.get("experiment") or {}
    best_id = int(best.get("id") or 0)
    require(best_id > base_id, "Seeker did not create a best Experiment")
    require(int(best.get("parent_id") or 0) == base_id, "Seeker Experiment parent mismatch")
    require(best.get("operation") == "SEEKER_BEST", "Seeker Experiment operation mismatch")

    detail = api.get(f"/api/stage1/experiments/{best_id}")
    require(len(detail.get("lineage") or []) == 2, "Experiment lineage is not Baseline -> Seeker best")
    require((detail.get("evidence") or {}).get("schema") == "stage1_evidence/v3", "Best Evidence schema mismatch")
    require((detail.get("chart_document") or {}).get("version") == "chart-document/v1", "Best Chart Document mismatch")
    diagnostics = (detail.get("experiment") or {}).get("result", {}).get("diagnostics", {})
    require(diagnostics.get("execution_authority") == "BrokerEmulator", "Experiment diagnostics lost Broker authority")

    feedback = api.post("/api/stage1/feedback", {"experiment_id": best_id, "target_return": 50.0}).body
    prompt = str(feedback.get("prompt") or "")
    require("[구조화 Evidence Bundle]" in prompt, "Feedback prompt is missing structured Evidence")
    require("[이전 raw LLM Prompt/Response 기록]" in prompt, "Feedback prompt is missing raw exchange memory section")
    require("[이전 실패/거절 가설]" in prompt, "Feedback prompt is missing rejected-hypothesis memory")

    query = urlencode({"root_id": root_id, "limit": 100})
    before_reject = api.get("/api/stage1/experiments?" + query).get("experiments", [])
    rejected = api.post(
        "/api/stage1/apply-llm",
        {
            "experiment_id": best_id,
            "llm_response": "No strategy DSL is present in this intentionally invalid response.",
            "prompt_text": "SYSTEM_SMOKE invalid LLM response",
            "hypothesis": "invalid response must not replace the applied experiment",
            "expected_effect": "HTTP 400 and immutable Experiment count",
            "promote": False,
        },
        expected=(400,),
    )
    require(rejected.status == 400, "Invalid LLM response was not rejected")
    after_reject = api.get("/api/stage1/experiments?" + query).get("experiments", [])
    require(len(after_reject) == len(before_reject), "Rejected LLM response created an Experiment")

    structural = api.post(
        "/api/stage1/apply-llm",
        {
            "experiment_id": best_id,
            "llm_response": f"```dsl\n{REVISED_DSL}\n```",
            "prompt_text": prompt,
            "hypothesis": "add one fixed long-term regime gate before re-optimizing existing inputs",
            "expected_effect": "reduce entries outside the long-term positive regime without changing execution semantics",
            "promote": False,
        },
    ).body
    require(structural.get("status") == "success", "Valid structural LLM response failed")
    structural_experiment = structural.get("experiment") or {}
    structural_id = int(structural_experiment.get("id") or 0)
    require(structural_id > best_id, "Structural LLM iteration did not create an Experiment")
    require(structural_experiment.get("operation") == "LLM_STRUCTURAL", "Structural operation mismatch")
    require(int(structural_experiment.get("parent_id") or 0) == best_id, "Structural parent mismatch")
    require(structural.get("verdict") in {"ACCEPTED_IMPROVEMENT", "REJECTED_NO_GAIN"}, "Structural verdict mismatch")
    require(bool(structural.get("exchange_id")), "Raw LLM exchange was not recorded")
    require(bool(structural.get("episode_id")), "Pre-Seeker structural episode was not recorded")
    structural_diff = structural.get("structural_diff") or {}
    require(int(structural_diff.get("changed_assignment_count") or 0) > 0 or bool(structural_diff.get("events_changed")),
            "Structural diff did not detect the revised DSL")

    rediscovered = api.post("/api/stage1/parameters/discover", {"dsl_code": REVISED_DSL}).body
    revised_names = [item.get("name") for item in rediscovered.get("parameters", [])]
    require(revised_names == ["fast", "slow"], f"Revised input discovery mismatch: {revised_names}")

    reseek = api.post(
        "/api/stage1/seeker-sessions",
        {
            "experiment_id": structural_id,
            "parameters": [
                {"name": "fast", "target": "dsl", "values": [2, 3]},
                {"name": "slow", "target": "dsl", "values": [7, 8]},
            ],
            "method": "grid",
            "objective": "MAX_RETURN",
            "seed": 42,
            "max_candidates": 16,
        },
    ).body
    reseek_id = int(reseek.get("id") or 0)
    require(reseek_id > session_id, "re-Seeker session was not created")
    reseek_completed = complete_session(api, reseek_id)
    final_experiment = reseek_completed.get("experiment") or {}
    final_id = int(final_experiment.get("id") or 0)
    require(final_id > structural_id, "re-Seeker did not create final Experiment")
    require(final_experiment.get("operation") == "SEEKER_BEST", "re-Seeker final operation mismatch")
    require(int(final_experiment.get("parent_id") or 0) == structural_id, "re-Seeker final parent mismatch")
    require(bool(final_experiment.get("finalized_episode_id")), "post-Seeker finalized Improvement Episode missing")

    final_detail = api.get(f"/api/stage1/experiments/{final_id}")
    lineage = final_detail.get("lineage") or []
    require([item.get("operation") for item in lineage] == ["BASELINE", "SEEKER_BEST", "LLM_STRUCTURAL", "SEEKER_BEST"],
            "Final Experiment lineage does not preserve the full structural loop")

    oos = api.post(f"/api/stage1/oos/{final_id}", {}).body
    require(oos.get("status") == "success", "Fixed holdout evaluation failed")
    oos_metrics = (oos.get("result") or {}).get("metrics_numeric", {})
    require("total_return_pct" in oos_metrics, "OOS metrics are missing total_return_pct")

    loop = api.post(
        "/api/stage1/target-loops",
        {
            "root_id": root_id,
            "target_return": 999.0,
            "iteration_limit": 3,
            "backtest_budget": 100,
            "no_improvement_limit": 3,
            "oos_degradation_limit_pct": 50.0,
            "duplicate_hypothesis_limit": 3,
            "parameter_spike_limit": 99.0,
        },
    ).body
    loop_id = int(loop.get("id") or 0)
    require(loop_id > 0, "Target Loop was not created")
    observed = api.post(
        f"/api/stage1/target-loops/{loop_id}/observe",
        {
            "experiment_id": final_id,
            "backtests_used_delta": 4,
            "accepted": False,
            "plateau": False,
            "engine_blocked": False,
            "oos_return_pct": float(oos_metrics.get("total_return_pct") or 0.0),
            "duplicate_hypothesis": False,
            "parameter_spike_ratio": 1.0,
        },
    ).body
    require((observed.get("state") or {}).get("current_experiment_id") == final_id, "Target Loop did not observe the final Experiment")
    require((observed.get("state") or {}).get("applied_head_experiment_id") == base_id,
            "Target Loop mutated current head before explicit promotion")

    promoted = api.post("/api/stage1/promote", {"experiment_id": final_id}).body
    require(promoted.get("status") == "success", "Explicit promotion failed")
    require(int((promoted.get("head") or {}).get("id") or 0) == final_id, "Explicit promotion did not move current head")

    methodology = api.get(f"/api/stage1/methodology/{root_id}")
    require(methodology.get("schema") == "stage1_methodology_validation/v3", "Methodology schema mismatch")
    require((methodology.get("oos") or {}).get("available") is True, "Methodology did not observe OOS evidence")
    require(methodology.get("episode_rate_basis") == "POST_SEEKER_FINAL", "Methodology did not prefer finalized post-Seeker episodes")
    require(int(methodology.get("finalized_post_seeker_episodes") or 0) >= 1, "Methodology missing finalized structural episode")
    require(methodology.get("claim") == "descriptive_only_until_OOS_and_multi_strategy_methodology_validation", "Methodology claim boundary changed")

    chart_document = api.get(f"/api/stage1/chart-document/{final_id}")
    require((chart_document.get("document") or {}).get("version") == "chart-document/v1", "Chart Document endpoint failed")

    return {
        "baseline_id": base_id,
        "best_id": best_id,
        "structural_id": structural_id,
        "final_id": final_id,
        "root_id": root_id,
        "session_id": session_id,
        "reseek_id": reseek_id,
        "loop_id": loop_id,
        "oos_return_pct": float(oos_metrics.get("total_return_pct") or 0.0),
        "experiments": len(api.get("/api/stage1/experiments?" + query).get("experiments", [])),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the live Stage 1 operational smoke workflow.")
    parser.add_argument("--stage1-base", default="http://127.0.0.1:8000")
    parser.add_argument("--chart-base", default="http://127.0.0.1:5174")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    try:
        result = run(args.stage1_base, args.chart_base, args.timeout)
    except Exception as exc:
        print(f"[FAIL] Stage 1 operational smoke: {exc}")
        return 1
    print(
        "[PASS] Stage 1 operational smoke: "
        f"baseline #{result['baseline_id']} -> seeker #{result['best_id']} -> "
        f"structural #{result['structural_id']} -> reseeker #{result['final_id']} -> "
        f"OOS {result['oos_return_pct']:+.2f}%"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
