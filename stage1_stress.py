"""Stage 1 operational/stress harness.

This is intentionally independent of external LLM and live Kiwoom credentials.
It stress-tests the deterministic product boundary.  Use --quick in CI and
--full before consolidated human UI verification.
"""
from __future__ import annotations

import argparse
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
from core.strategy_factory import DataContract, StrategyFactory, StrategyFactoryStore, extract_dsl, stable_hash
from core.stage1_target_loop import TargetLoopService
from core.stage1_llm_memory import LLMExchangeMemory


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


def market(n=360):
    # Deterministic multi-regime series: trend, pullback, trend, range.
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
            day = 1; month += 1
            if month > 12: month = 1; year += 1
    return {"time": times, "open": open_.tolist(), "high": high.tolist(), "low": low.tolist(),
            "close": close.tolist(), "volume": volume.tolist()}


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

    def close(self): self.temp.cleanup()

    def check(self, name, fn):
        started = time.perf_counter()
        try:
            detail = fn() or {}
            self.checks.append({"name": name, "status": "PASS", "seconds": time.perf_counter() - started, "detail": detail})
        except Exception as exc:
            self.failures.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})
            self.checks.append({"name": name, "status": "FAIL", "seconds": time.perf_counter() - started, "detail": self.failures[-1]})

    def invalid_dsl_pressure(self):
        corpus = [
            DSL.replace('input fast = 3', 'if close > open'),
            DSL.replace('ta.sma(close, fast)', 'ta.not_registered(close, fast)'),
            DSL.replace('close > slow_ma + threshold', 'close and true'),
            DSL.replace('close > slow_ma + threshold', 'close[-1] > 0'),
            DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "TELEPORT")'),
            DSL.replace('order.buy(type = "MARKET")', 'order.buy(type = "LIMIT", limit = 1, tif = "FOREVER")'),
            DSL.replace('ta.sma(close, fast)', 'ta.sma(true, fast)'),
        ]
        loops = 300 if self.full else 50
        rejected = 0
        for i in range(loops):
            source = corpus[i % len(corpus)]
            try: BacktestEngine.run(source, market=self.mkt)
            except (DSLRuntimeError, DSLParseError, ValueError): rejected += 1
        if rejected != loops: raise AssertionError(f"invalid DSL rejection {rejected}/{loops}")
        return {"rejected": rejected}

    def deterministic_replay(self):
        loops = 300 if self.full else 40
        hashes = set()
        for _ in range(loops):
            result = BacktestEngine.run(DSL, market=self.mkt)
            fingerprint = {
                "metrics": result["metrics_numeric"],
                "trades": result["closed_trades"],
                "signals": result["diagnostics"]["signal_counts"],
            }
            hashes.add(stable_hash(fingerprint))
        if len(hashes) != 1: raise AssertionError(f"determinism fingerprints={len(hashes)}")
        return {"runs": loops, "fingerprint": next(iter(hashes))}

    def execution_matrix(self):
        cases = 0
        for mode in ("bar_close", "next_open"):
            for commission in (0.0, 0.015, 0.05):
                for slippage in (0.0, 0.02, 0.10):
                    result = BacktestEngine.run(DSL, market=self.mkt, settings={
                        "signal_mode": mode, "commission_pct": commission,
                        "sell_tax_pct": 0.18, "slippage_pct": slippage,
                        "stop_loss_pct": 2.0, "take_profit_pct": 5.0,
                    })
                    if not math.isfinite(float(result["metrics_numeric"]["final_equity"])): raise AssertionError("non-finite equity")
                    cases += 1
        return {"cases": cases}

    def factory_vertical(self):
        baseline = self.factory.baseline(intent="stress vertical", dsl_code=DSL, market=self.mkt,
            instrument="STRESS", timeframe="1d", source="stress")
        dims = 8 if self.full else 4
        seeker = self.factory.seek(experiment_id=baseline["id"], market=self.mkt,
            parameter_specs=[
                {"name":"fast","values":list(range(2,2+dims))},
                {"name":"slow","values":list(range(8,8+dims))},
                {"name":"threshold","values":[0,0.5,1,1.5,2][:5 if self.full else 3]},
            ], method="grid", objective="MAX_RETURN", seed=42, max_candidates=2000)
        best = seeker["experiment"]
        prompt = self.factory.feedback_package(best["id"], target_return=50)
        revised = best["dsl_code"].replace("input threshold = 0", "input threshold = 0.5") if "input threshold = 0" in best["dsl_code"] else best["dsl_code"]
        applied = self.factory.apply_llm_response(experiment_id=best["id"], llm_response=f"```dsl\n{revised}\n```",
            market=self.mkt, hypothesis="structural-loop plumbing stress")
        self.memory.record(before_experiment_id=best["id"], after_experiment_id=applied["experiment"]["id"],
            prompt_text=prompt["prompt"], response_text=f"```dsl\n{revised}\n```", hypothesis="stress", status=applied["verdict"])
        audit = self.factory.chart_audit(applied["experiment"])
        if len(audit["candles"]) != len(self.mkt["close"]): raise AssertionError("chart candle mismatch")
        if len(self.store.lineage(applied["experiment"]["id"])) < 3: raise AssertionError("lineage too short")
        return {"root_id": baseline["root_id"], "study_evaluated": seeker["study"]["evaluated"],
                "child": applied["experiment"]["id"], "verdict": applied["verdict"]}

    def lineage_pressure(self):
        baseline = self.factory.baseline(intent="lineage pressure", dsl_code=DSL, market=self.mkt,
            instrument="LINEAGE", timeframe="1d", source="stress")
        count = 500 if self.full else 80
        parent = baseline
        for i in range(count):
            parent = self.store.create_experiment(parent_id=parent["id"], operation="PRESSURE",
                strategy_name=parent["strategy_name"], intent=parent["intent"], dsl_code=parent["dsl_code"],
                parameters={"i":i}, execution=parent["execution"], provenance=parent["provenance"],
                result=parent["result"], analysis=parent["analysis"])
        lineage = self.store.lineage(parent["id"])
        if len(lineage) != count + 1: raise AssertionError(f"lineage {len(lineage)} != {count+1}")
        if self.store.current_head(baseline["root_id"])["id"] != baseline["id"]: raise AssertionError("append mutated head")
        self.store.promote(parent["id"])
        if self.store.current_head(baseline["root_id"])["id"] != parent["id"]: raise AssertionError("promotion failed")
        return {"experiments": len(lineage)}

    def malformed_llm_pressure(self):
        count = 300 if self.full else 60
        bad = ["", "설명만", "```dsl\nstrategy 'x' {", "```python\nprint('x')\n```", "{not strategy}"]
        rejected = 0
        for i in range(count):
            try: extract_dsl(bad[i % len(bad)])
            except ValueError: rejected += 1
        if rejected != count: raise AssertionError(f"malformed LLM accepted {count-rejected}")
        return {"rejected": rejected}

    def target_loop_budget(self):
        baseline = self.factory.baseline(intent="loop budget", dsl_code=DSL, market=self.mkt,
            instrument="LOOP", timeframe="1d", source="stress")
        service = TargetLoopService(self.factory)
        loop = service.create(root_id=baseline["root_id"], target_return=9999, iteration_limit=100,
                              backtest_budget=1000, no_improvement_limit=3)
        state = None
        for _ in range(3): state = service.observe(loop_id=loop["id"], experiment_id=baseline["id"], accepted=False)
        if state["state"]["status"] != "PLATEAU": raise AssertionError(state["state"])
        return state["state"]

    def data_fail_closed(self):
        good, provenance = DataContract.normalize(self.mkt, instrument="DATA", timeframe="1d", source="stress")
        corrupt = dict(self.mkt); corrupt["high"] = list(corrupt["high"]); corrupt["high"][4] = -999
        try: DataContract.normalize(corrupt, instrument="DATA", timeframe="1d", source="stress")
        except ValueError: pass
        else: raise AssertionError("bad OHLC accepted")
        return {"data_hash": provenance.data_hash, "bars": provenance.bars}

    def run(self):
        tracemalloc.start()
        for name, fn in [
            ("invalid_dsl_pressure", self.invalid_dsl_pressure),
            ("deterministic_replay", self.deterministic_replay),
            ("execution_matrix", self.execution_matrix),
            ("data_fail_closed", self.data_fail_closed),
            ("factory_vertical", self.factory_vertical),
            ("lineage_pressure", self.lineage_pressure),
            ("malformed_llm_pressure", self.malformed_llm_pressure),
            ("target_loop_budget", self.target_loop_budget),
        ]: self.check(name, fn)
        current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        return {"mode":"full" if self.full else "quick", "status":"FAIL" if self.failures else "PASS",
                "seconds":time.perf_counter()-self.started, "memory_current_bytes":current, "memory_peak_bytes":peak,
                "checks":self.checks, "failures":self.failures}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--full", action="store_true"); parser.add_argument("--json", action="store_true")
    args = parser.parse_args(); harness = Harness(full=args.full)
    try: report = harness.run()
    finally: harness.close()
    if args.json: print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in report["checks"]: print(f"[{row['status']}] {row['name']} {row['seconds']:.3f}s")
        print(f"[{report['status']}] stage1-stress mode={report['mode']} total={report['seconds']:.3f}s peak={report['memory_peak_bytes']}")
    raise SystemExit(1 if report["failures"] else 0)


if __name__ == "__main__": main()
