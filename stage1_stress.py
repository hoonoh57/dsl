"""Stage 1 operational/stress harness.

This harness is independent of external LLM and live Kiwoom credentials. It
exercises the deterministic product boundary after the Stage 1 vertical slice
is wired. Default mode is quick; use --full before consolidated human UI
verification. Normal success output is intentionally one [PASS] line.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import tempfile
import time
import tracemalloc
from pathlib import Path

import numpy as np

from core.backtest import BacktestEngine
from core.dsl_parser import DSLParser, DSLParseError
from core.dsl_runtime import DSLRuntimeError
from core.stage1_data_store import save_market_snapshot
from core.stage1_evidence import EvidenceBuilder
from core.stage1_llm_memory import LLMExchangeMemory
from core.stage1_methodology import MethodologyValidator
from core.stage1_oos import OOSRegistry
from core.stage1_resumable_seeker import ResumableSeekerService
from core.stage1_target_loop import TargetLoopService
from core.strategy_factory import DataContract, StrategyFactory, StrategyFactoryStore, extract_dsl, stable_hash


DSL = '''strategy "StressFactory" {
    timeframe = "1d"
    input fast = 3
    input slow = 12
    input threshold = 0
    fast_ma = ta.sma(close, fast)
    slow_ma = ta.sma(close, slow)
    raw_entry = ta.crossover(fast_ma, slow_ma) and close > slow_ma + threshold
    raw_exit = ta.crossunder(fast_ma, slow_ma)
    cooldown_ok = state.ready_after(raw_exit, 2)
    long_entry = raw_entry and cooldown_ok
    long_exit = raw_exit
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''

GOLDEN_DSL = '''strategy "StressGolden" {
    timeframe = "1d"
    enter = close > close[1]
    leave = close < close[1]
    on(enter) { order.buy(type = "MARKET") }
    on(leave) { order.close_long() }
}'''


def market(n=360):
    t = np.arange(n, dtype=float)
    close = 100 + 0.10 * t + 8 * np.sin(t / 7.0) + 4 * np.sin(t / 19.0)
    open_ = close + 0.7 * np.sin(t / 3.0)
    high = np.maximum(open_, close) + 1.8 + (t % 5) * 0.05
    low = np.minimum(open_, close) - 1.8 - (t % 7) * 0.04
    volume = 100000 + (t % 31) * 3500
    times = []
    year, month, day = 2022, 1, 1
    for _ in range(n):
        times.append(f"{year:04d}-{month:02d}-{day:02d}")
        day += 1
        if day > 28:
            day = 1
            month += 1
            if month > 12:
                month = 1
                year += 1
    return {
        "time": times,
        "open": open_.tolist(),
        "high": high.tolist(),
        "low": low.tolist(),
        "close": close.tolist(),
        "volume": volume.tolist(),
    }


def golden_market():
    return {
        "time": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "open": [100.0, 105.0, 95.0, 90.0],
        "high": [101.0, 111.0, 97.0, 92.0],
        "low": [99.0, 104.0, 89.0, 88.0],
        "close": [100.0, 110.0, 90.0, 89.0],
        "volume": [1000.0] * 4,
    }


class Harness:
    def __init__(self, full=False):
        self.full = full
        self.failures = []
        self.checks = []
        self.started = time.perf_counter()
        self.temp = tempfile.TemporaryDirectory()
        self.store = StrategyFactoryStore(Path(self.temp.name) / "stress.db")
        self.factory = StrategyFactory(self.store)
        self.memory = LLMExchangeMemory(self.store)
        self.mkt = market(720 if full else 280)

    def close(self):
        self.temp.cleanup()

    def check(self, name, fn):
        started = time.perf_counter()
        try:
            detail = fn() or {}
            self.checks.append({
                "name": name,
                "status": "PASS",
                "seconds": time.perf_counter() - started,
                "detail": detail,
            })
        except Exception as exc:
            failure = {"name": name, "error": f"{type(exc).__name__}: {exc}"}
            self.failures.append(failure)
            self.checks.append({
                "name": name,
                "status": "FAIL",
                "seconds": time.perf_counter() - started,
                "detail": failure,
            })

    def invalid_dsl_pressure(self):
        corpus = [
            DSL.replace("input fast = 3", "if close > open"),
            DSL.replace("ta.sma(close, fast)", "ta.not_registered(close, fast)"),
            DSL.replace("close > slow_ma + threshold", "close and true"),
            DSL.replace("close > slow_ma + threshold", "close[-1] > 0"),
            DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "TELEPORT")'),
            DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "LIMIT", limit = 1, tif = "FOREVER")'),
            DSL.replace("ta.sma(close, fast)", "ta.sma(true, fast)"),
            DSL.replace("input fast = 3", "input fast = 0"),
            DSL.replace("ta.sma(close, fast)", 'ta.ma(close, fast, "unknown")'),
            DSL.replace("ta.sma(close, fast)", "ta.jma(close, fast, 150, 2)"),
        ]
        loops = 500 if self.full else 80
        rejected = 0
        for i in range(loops):
            source = corpus[i % len(corpus)]
            try:
                BacktestEngine.run(source, market=self.mkt)
            except (DSLRuntimeError, DSLParseError, ValueError):
                rejected += 1
        if rejected != loops:
            raise AssertionError(f"invalid DSL rejection {rejected}/{loops}")
        return {"rejected": rejected}

    def deterministic_replay(self):
        loops = 400 if self.full else 50
        hashes = set()
        for _ in range(loops):
            result = BacktestEngine.run(DSL, market=self.mkt)
            fingerprint = {
                "metrics": result["metrics_numeric"],
                "trades": result["closed_trades"],
                "signals": result["diagnostics"]["signal_counts"],
                "broker_history": result["diagnostics"]["broker_history"],
            }
            hashes.add(stable_hash(fingerprint))
        if len(hashes) != 1:
            raise AssertionError(f"determinism fingerprints={len(hashes)}")
        return {"runs": loops, "fingerprint": next(iter(hashes))}

    def broker_authority_and_accounting(self):
        settings = {
            "signal_mode": "bar_close",
            "total_capital": 100_000.0,
            "allocation_pct": 50.0,
            "commission_pct": 0.1,
            "sell_tax_pct": 0.2,
            "slippage_pct": 0.0,
        }
        result = BacktestEngine.run(GOLDEN_DSL, market=golden_market(), settings=settings)
        diagnostics = result["diagnostics"]
        if diagnostics.get("execution_authority") != "BrokerEmulator":
            raise AssertionError("BrokerEmulator is not execution authority")
        if result["metrics_numeric"]["open_position"] != 0:
            raise AssertionError("golden fixture did not close")
        change = result["metrics_numeric"]["final_equity"] - result["metrics_numeric"]["initial_capital"]
        closed_net = sum(float(item["net_pnl"]) for item in result["closed_trades"])
        if abs(change - closed_net) > 1e-7:
            raise AssertionError(f"equity reconciliation mismatch: {change} vs {closed_net}")
        history = diagnostics.get("broker_history", [])
        by_order = {}
        for row in history:
            by_order.setdefault(row["order_id"], []).append(row)
        for execution in result["trades"]:
            order_id = execution.get("order_id")
            rows = by_order.get(order_id, [])
            if [row.get("status") for row in rows] != ["CREATED", "ACCEPTED", "FILLED"]:
                raise AssertionError(f"bad lifecycle for {order_id}: {rows}")
            if abs(float(rows[-1]["fill_price"]) - float(execution["price"])) > 1e-12:
                raise AssertionError(f"fill price drift for {order_id}")
            if abs(float(rows[-1]["quantity"]) - float(execution["quantity"])) > 1e-12:
                raise AssertionError(f"fill quantity drift for {order_id}")
        fake_experiment = {
            "id": 1,
            "provenance": {"instrument": "GOLDEN", "timeframe": "1d", "data_hash": "fixture"},
            "execution": settings,
            "result": result,
            "analysis": {},
        }
        evidence = EvidenceBuilder.build(fake_experiment)
        if evidence["order_lifecycle"]["authority"] != "BrokerEmulator":
            raise AssertionError("Evidence lost broker authority")
        if "audit replay" not in evidence["limitations"]["order_lifecycle"]:
            raise AssertionError("Evidence lifecycle limitation contract changed")
        return {"executions": len(result["trades"]), "closed_trades": len(result["closed_trades"])}

    def execution_matrix(self):
        cases = 0
        for mode in ("bar_close", "next_open"):
            for commission in (0.0, 0.015, 0.05):
                for slippage in (0.0, 0.02, 0.10):
                    result = BacktestEngine.run(
                        DSL,
                        market=self.mkt,
                        settings={
                            "signal_mode": mode,
                            "commission_pct": commission,
                            "sell_tax_pct": 0.18,
                            "slippage_pct": slippage,
                            "stop_loss_pct": 2.0,
                            "take_profit_pct": 5.0,
                        },
                    )
                    if not math.isfinite(float(result["metrics_numeric"]["final_equity"])):
                        raise AssertionError("non-finite equity")
                    if result["diagnostics"].get("execution_authority") != "BrokerEmulator":
                        raise AssertionError("execution matrix lost broker authority")
                    cases += 1
        return {"cases": cases}

    def factory_vertical(self):
        baseline = self.factory.baseline(
            intent="stress vertical",
            dsl_code=DSL,
            market=self.mkt,
            instrument="STRESS",
            timeframe="1d",
            source="stress",
        )
        dims = 8 if self.full else 4
        seeker = self.factory.seek(
            experiment_id=baseline["id"],
            market=self.mkt,
            parameter_specs=[
                {"name": "fast", "values": list(range(2, 2 + dims))},
                {"name": "slow", "values": list(range(8, 8 + dims))},
                {"name": "threshold", "values": [0, 0.5, 1, 1.5, 2][:5 if self.full else 3]},
            ],
            method="grid",
            objective="MAX_RETURN",
            seed=42,
            max_candidates=2000,
        )
        best = seeker["experiment"]
        prompt = self.factory.feedback_package(best["id"], target_return=50)
        revised = best["dsl_code"].replace("input threshold = 0", "input threshold = 0.5")
        applied = self.factory.apply_llm_response(
            experiment_id=best["id"],
            llm_response=f"```dsl\n{revised}\n```",
            market=self.mkt,
            hypothesis="structural-loop plumbing stress",
        )
        self.memory.record(
            before_experiment_id=best["id"],
            after_experiment_id=applied["experiment"]["id"],
            prompt_text=prompt["prompt"],
            response_text=f"```dsl\n{revised}\n```",
            hypothesis="stress",
            status=applied["verdict"],
        )
        audit = self.factory.chart_audit(applied["experiment"])
        if len(audit["candles"]) != len(self.mkt["close"]):
            raise AssertionError("chart candle mismatch")
        if len(self.store.lineage(applied["experiment"]["id"])) < 3:
            raise AssertionError("lineage too short")
        return {
            "root_id": baseline["root_id"],
            "study_evaluated": seeker["study"]["evaluated"],
            "child": applied["experiment"]["id"],
            "verdict": applied["verdict"],
        }

    def resumable_seeker_and_cache_pressure(self):
        normalized, _ = DataContract.normalize(
            self.mkt,
            instrument="RESUME",
            timeframe="1d",
            source="stress-resumable",
        )
        save_market_snapshot(normalized)
        baseline = self.factory.baseline(
            intent="resumable pressure",
            dsl_code=DSL,
            market=normalized,
            instrument="RESUME",
            timeframe="1d",
            source="stress-resumable",
        )
        service = ResumableSeekerService(self.factory)
        fast_values = list(range(2, 8 if self.full else 5))
        slow_values = list(range(9, 18 if self.full else 13))
        specs = [
            {"name": "fast", "values": fast_values},
            {"name": "slow", "values": slow_values},
        ]
        first = service.create(
            parent_experiment_id=baseline["id"],
            parameter_specs=specs,
            method="grid",
            objective="MAX_RETURN",
            seed=42,
            max_candidates=500,
        )
        partial = service.process(first["id"], batch_size=3)
        if int(partial["session"]["cursor"]) != 3:
            raise AssertionError("resumable cursor did not advance")
        if service.cancel(first["id"])["status"] != "CANCELED":
            raise AssertionError("seeker cancel failed")
        if service.resume(first["id"])["status"] != "READY":
            raise AssertionError("seeker resume failed")
        completed = None
        for _ in range(100):
            completed = service.process(first["id"], batch_size=25)
            if completed["session"]["status"] == "COMPLETED":
                break
        if completed is None or completed["session"]["status"] != "COMPLETED":
            raise AssertionError("resumable seeker did not complete")
        total = int(completed["session"]["total_candidates"])
        if int(completed["session"]["cursor"]) != total:
            raise AssertionError("resumable seeker cursor mismatch")

        second = service.create(
            parent_experiment_id=baseline["id"],
            parameter_specs=specs,
            method="grid",
            objective="MAX_RETURN",
            seed=42,
            max_candidates=500,
        )
        cached = service.process(second["id"], batch_size=500)
        rows = service.candidates(second["id"], limit=500)
        if cached["session"]["status"] != "COMPLETED":
            raise AssertionError("cache replay session did not complete")
        if len(rows) != total or not all(int(item["cache_hit"]) == 1 for item in rows):
            raise AssertionError("cross-session candidate cache missed")
        return {"candidates": total, "cache_hits": len(rows)}

    def post_seeker_episode_pressure(self):
        normalized, _ = DataContract.normalize(
            self.mkt,
            instrument="EPISODE",
            timeframe="1d",
            source="stress-episode",
        )
        save_market_snapshot(normalized)
        baseline = self.factory.baseline(
            intent="episode pressure",
            dsl_code=DSL,
            market=normalized,
            instrument="EPISODE",
            timeframe="1d",
            source="stress-episode",
        )
        revised = DSL.replace("input threshold = 0", "input threshold = 0.5")
        structural = self.factory.apply_llm_response(
            experiment_id=baseline["id"],
            llm_response=f"```dsl\n{revised}\n```",
            market=normalized,
            hypothesis="threshold structural candidate",
            expected_effect="stress after-seeker episode",
        )["experiment"]
        service = ResumableSeekerService(self.factory)
        session = service.create(
            parent_experiment_id=structural["id"],
            parameter_specs=[
                {"name": "fast", "values": [2, 3]},
                {"name": "slow", "values": [10, 12]},
            ],
            method="grid",
            objective="MAX_RETURN",
            seed=7,
            max_candidates=16,
        )
        completed = service.process(session["id"], batch_size=16)
        child = completed.get("experiment") or {}
        if child.get("operation") != "SEEKER_BEST":
            raise AssertionError("post-structural seeker did not create SEEKER_BEST")
        episodes = self.store.episodes_for_root(baseline["root_id"], 100)
        finalized = [
            item for item in episodes
            if item.get("after_experiment_id") == child.get("id") and "after_seeker" in str(item.get("reason") or "")
        ]
        if not finalized:
            raise AssertionError("finalized post-Seeker Improvement Episode missing")
        return {"experiment_id": child["id"], "finalized_episodes": len(finalized)}

    def oos_fixed_split_pressure(self):
        full, _ = DataContract.normalize(
            self.mkt,
            instrument="OOS",
            timeframe="1d",
            source="stress-oos",
        )
        registry = OOSRegistry(self.factory)
        train, holdout, split_index = registry.split_market(full, 0.20)
        save_market_snapshot(train)
        baseline = self.factory.baseline(
            intent="oos pressure",
            dsl_code=DSL,
            market=train,
            instrument="OOS",
            timeframe="1d",
            source=train["_meta"]["source"],
        )
        split = registry.bind_split(baseline["root_id"], full, train, holdout, 0.20, split_index)
        evaluated = registry.evaluate(baseline["id"])
        if evaluated["result"]["diagnostics"]["bars"] != len(holdout["close"]):
            raise AssertionError("OOS bar count mismatch")
        other_train, other_holdout, other_index = registry.split_market(full, 0.25)
        try:
            registry.bind_split(baseline["root_id"], full, other_train, other_holdout, 0.25, other_index)
        except ValueError:
            pass
        else:
            raise AssertionError("immutable OOS split was changed")
        summary = MethodologyValidator(self.store).summarize(baseline["root_id"])
        if not summary["oos"]["available"]:
            raise AssertionError("methodology did not observe OOS result")
        if summary["claim"] != "descriptive_only_until_OOS_and_multi_strategy_methodology_validation":
            raise AssertionError("methodology claim boundary drifted")
        return {"holdout_bars": len(holdout["close"]), "holdout_hash": split["holdout_data_hash"]}

    def lineage_pressure(self):
        baseline = self.factory.baseline(
            intent="lineage pressure",
            dsl_code=DSL,
            market=self.mkt,
            instrument="LINEAGE",
            timeframe="1d",
            source="stress",
        )
        count = 500 if self.full else 80
        parent = baseline
        for i in range(count):
            parent = self.store.create_experiment(
                parent_id=parent["id"],
                operation="PRESSURE",
                strategy_name=parent["strategy_name"],
                intent=parent["intent"],
                dsl_code=parent["dsl_code"],
                parameters={"i": i},
                execution=parent["execution"],
                provenance=parent["provenance"],
                result=parent["result"],
                analysis=parent["analysis"],
            )
        lineage = self.store.lineage(parent["id"])
        if len(lineage) != count + 1:
            raise AssertionError(f"lineage {len(lineage)} != {count + 1}")
        if self.store.current_head(baseline["root_id"])["id"] != baseline["id"]:
            raise AssertionError("append mutated head")
        self.store.promote(parent["id"])
        if self.store.current_head(baseline["root_id"])["id"] != parent["id"]:
            raise AssertionError("promotion failed")
        return {"experiments": len(lineage)}

    def malformed_llm_pressure(self):
        count = 400 if self.full else 80
        bad = ["", "설명만", "```dsl\nstrategy 'x' {", "```python\nprint('x')\n```", "{not strategy}"]
        rejected = 0
        for i in range(count):
            try:
                extract_dsl(bad[i % len(bad)])
            except ValueError:
                rejected += 1
        if rejected != count:
            raise AssertionError(f"malformed LLM accepted {count - rejected}")
        return {"rejected": rejected}

    def target_loop_guards(self):
        baseline = self.factory.baseline(
            intent="loop guards",
            dsl_code=DSL,
            market=self.mkt,
            instrument="LOOP",
            timeframe="1d",
            source="stress",
        )
        service = TargetLoopService(self.factory)
        original_head = self.store.current_head(baseline["root_id"])["id"]

        plateau_loop = service.create(
            root_id=baseline["root_id"], target_return=9999, iteration_limit=100,
            backtest_budget=1000, no_improvement_limit=3,
        )
        state = None
        for _ in range(3):
            state = service.observe(loop_id=plateau_loop["id"], experiment_id=baseline["id"], accepted=False)
        if state["state"]["status"] != "PLATEAU":
            raise AssertionError(state["state"])

        duplicate_loop = service.create(
            root_id=baseline["root_id"], target_return=9999, iteration_limit=100,
            backtest_budget=1000, no_improvement_limit=100, duplicate_hypothesis_limit=2,
        )
        service.observe(loop_id=duplicate_loop["id"], experiment_id=baseline["id"], duplicate_hypothesis=True)
        duplicate = service.observe(loop_id=duplicate_loop["id"], experiment_id=baseline["id"], duplicate_hypothesis=True)
        if duplicate["state"]["status"] != "NO_NEW_HYPOTHESIS":
            raise AssertionError(duplicate["state"])

        spike_loop = service.create(
            root_id=baseline["root_id"], target_return=9999, iteration_limit=100,
            backtest_budget=1000, no_improvement_limit=100, parameter_spike_limit=3.0,
        )
        spike = service.observe(
            loop_id=spike_loop["id"], experiment_id=baseline["id"], parameter_spike_ratio=3.5,
        )
        if spike["state"]["status"] != "PARAMETER_INSTABILITY":
            raise AssertionError(spike["state"])

        oos_loop = service.create(
            root_id=baseline["root_id"], target_return=9999, iteration_limit=100,
            backtest_budget=1000, no_improvement_limit=100, oos_degradation_limit_pct=2.0,
        )
        service.observe(loop_id=oos_loop["id"], experiment_id=baseline["id"], oos_return_pct=10.0)
        degraded = service.observe(loop_id=oos_loop["id"], experiment_id=baseline["id"], oos_return_pct=7.0)
        if degraded["state"]["status"] != "OOS_DEGRADED":
            raise AssertionError(degraded["state"])

        if self.store.current_head(baseline["root_id"])["id"] != original_head:
            raise AssertionError("Target Loop implicitly promoted an Experiment")
        return {
            "plateau": state["state"]["status"],
            "duplicate": duplicate["state"]["status"],
            "spike": spike["state"]["status"],
            "oos": degraded["state"]["status"],
        }

    def data_fail_closed(self):
        _, provenance = DataContract.normalize(self.mkt, instrument="DATA", timeframe="1d", source="stress")
        corrupt = dict(self.mkt)
        corrupt["high"] = list(corrupt["high"])
        corrupt["high"][4] = -999
        try:
            DataContract.normalize(corrupt, instrument="DATA", timeframe="1d", source="stress")
        except ValueError:
            pass
        else:
            raise AssertionError("bad OHLC accepted")
        return {"data_hash": provenance.data_hash, "bars": provenance.bars}

    def retained_memory_pressure(self):
        gc.collect()
        before = tracemalloc.get_traced_memory()[0]
        loops = 250 if self.full else 60
        for _ in range(loops):
            result = BacktestEngine.run(DSL, market=self.mkt)
            if result["diagnostics"].get("execution_authority") != "BrokerEmulator":
                raise AssertionError("repetition lost Broker authority")
        result = None
        gc.collect()
        after = tracemalloc.get_traced_memory()[0]
        retained = max(0, after - before)
        limit = 128 * 1024 * 1024 if self.full else 64 * 1024 * 1024
        if retained > limit:
            raise AssertionError(f"retained memory delta {retained} exceeds {limit}")
        return {"runs": loops, "retained_bytes": retained, "limit_bytes": limit}

    def run(self):
        tracemalloc.start()
        checks = [
            ("invalid_dsl_pressure", self.invalid_dsl_pressure),
            ("deterministic_replay", self.deterministic_replay),
            ("broker_authority_and_accounting", self.broker_authority_and_accounting),
            ("execution_matrix", self.execution_matrix),
            ("data_fail_closed", self.data_fail_closed),
            ("factory_vertical", self.factory_vertical),
            ("resumable_seeker_and_cache_pressure", self.resumable_seeker_and_cache_pressure),
            ("post_seeker_episode_pressure", self.post_seeker_episode_pressure),
            ("oos_fixed_split_pressure", self.oos_fixed_split_pressure),
            ("lineage_pressure", self.lineage_pressure),
            ("malformed_llm_pressure", self.malformed_llm_pressure),
            ("target_loop_guards", self.target_loop_guards),
            ("retained_memory_pressure", self.retained_memory_pressure),
        ]
        for name, fn in checks:
            self.check(name, fn)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "mode": "full" if self.full else "quick",
            "status": "FAIL" if self.failures else "PASS",
            "seconds": time.perf_counter() - self.started,
            "memory_current_bytes": current,
            "memory_peak_bytes": peak,
            "checks": self.checks,
            "failures": self.failures,
        }


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--quick", action="store_true", help="explicit quick mode (also the default)")
    mode.add_argument("--full", action="store_true", help="larger candidate/iteration pressure")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    harness = Harness(full=args.full)
    try:
        report = harness.run()
    finally:
        harness.close()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["failures"]:
        for row in report["failures"]:
            print(f"[FAIL] {row['name']}: {row['error']}")
        print(f"[FAIL] stage1-stress mode={report['mode']} failures={len(report['failures'])}")
    else:
        print(
            f"[PASS] stage1-stress mode={report['mode']} checks={len(report['checks'])} "
            f"total={report['seconds']:.3f}s peak={report['memory_peak_bytes']}"
        )
    raise SystemExit(1 if report["failures"] else 0)


if __name__ == "__main__":
    main()
