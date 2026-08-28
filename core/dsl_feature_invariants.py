"""Executable invariant catalog for DSL Live Studio Feature Catalog v2.

These cases go beyond "the example ran".  Each case exercises a declared Core
execution contract and asserts the observable invariant produced by the real
DSL/Backtest/Broker path.  No guard or semantic contract is weakened here.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np

from core.backtest import BacktestEngine
from core.dsl_runtime import DSLRuntimeError
from core.multitimeframe import MultiTimeframeContext
from core.parent_context_frame import ParentContextFrame
from core.parent_feature_provider import (
    ParentContextAssembler,
    ParentFeatureManifest,
    ParentFeatureProviderResult,
    ParentFeatureRegistry,
    ParentFeatureSpec,
)


@dataclass(frozen=True)
class InvariantCase:
    invariant_id: str
    category: str
    title: str
    description: str
    dsl_code: str

    def public_dict(self) -> dict:
        return asdict(self)


DSL_ALWAYS_LONG = '''strategy "Invariant_AlwaysLong" {
    timeframe = "1d"
    entry_cond = close > 0
    exit_cond = false
    on(entry_cond) { order.buy(type = "MARKET") }
}'''

DSL_NEXT_OPEN = '''strategy "Invariant_NextOpen" {
    timeframe = "1d"
    entry_cond = close > open
    exit_cond = false
    on(entry_cond) { order.buy(type = "MARKET") }
}'''

DSL_STOP = '''strategy "Invariant_Stop" {
    timeframe = "1d"
    arm = close > 0
    on(arm) { order.buy(type = "STOP", id = "stop-entry", stop = close * 1.01, tif = "GTC") }
}'''

DSL_STOP_LIMIT = '''strategy "Invariant_StopLimit" {
    timeframe = "1d"
    arm = close > 0
    on(arm) { order.buy(type = "STOP_LIMIT", id = "stop-limit-entry", stop = close * 1.01, limit = close * 1.02, tif = "GTC") }
}'''

DSL_DAY = '''strategy "Invariant_DAY" {
    timeframe = "1m"
    arm = close > 0
    on(arm) { order.buy(type = "LIMIT", id = "day-entry", limit = close * 0.50, tif = "DAY") }
}'''

DSL_CANCEL = '''strategy "Invariant_Cancel" {
    timeframe = "1d"
    arm = close > 0
    cancel_it = close > 0
    on(arm) { order.buy(type = "LIMIT", id = "stable-client-id", limit = close * 0.50, tif = "GTC") }
    on(cancel_it) { order.cancel(id = "stable-client-id") }
}'''

DSL_INTRADAY_CYCLES = '''strategy "Invariant_IntradayCycles" {
    timeframe = "1m"
    entry_cond = close > open
    exit_cond = close < open
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}'''

DSL_CTX = '''strategy "Invariant_CTX" {
    timeframe = "5m"
    entry_cond = ctx.market.entry_permitted and ctx.market.kospi_slope > 0 and ctx.market.regime_state == "RISK_ON"
    exit_cond = false
    on(entry_cond) { order.buy(type = "MARKET") }
}'''

DSL_MTF = '''strategy "Invariant_MTF" {
    timeframe = "1m"
    confirmed = mtf.close("5m")
    entry_cond = confirmed > 0
    exit_cond = false
    on(entry_cond) { order.buy(type = "MARKET") }
}'''


INVARIANT_CASES = {
    item.invariant_id: item for item in (
        InvariantCase("context.exact_binding", "context", "ctx exact binding", "DEPLOYMENT frame의 exact bar timestamp만 ctx.* 실행 입력이 되는지 검증", DSL_CTX),
        InvariantCase("context.missing_fail_closed", "context", "ctx missing fail-closed", "필수 context binding 없이 ctx.*를 실행하면 실패해야 함", DSL_CTX),
        InvariantCase("execution.entry_gate_suppression", "execution_contract", "entry gate suppression-only", "상위 gate=false가 진입만 제거하고 새 진입을 만들지 않는지 검증", DSL_ALWAYS_LONG),
        InvariantCase("execution.next_open_timing", "execution_contract", "next_open timing", "prior completed bar signal이 정확히 다음 open에서 체결되는지 검증", DSL_NEXT_OPEN),
        InvariantCase("execution.entry_time_window", "execution_contract", "entry time window", "허용 시간 밖 진입이 diagnostics로 차단되는지 검증", DSL_INTRADAY_CYCLES),
        InvariantCase("execution.max_entries_per_day", "execution_contract", "max entries/day", "일일 진입 횟수 제한이 초과 진입을 차단하는지 검증", DSL_INTRADAY_CYCLES),
        InvariantCase("order.stop_fill", "order_contract", "STOP lifecycle", "STOP pending 주문이 OHLC trigger 후 BrokerEmulator에서 체결되는지 검증", DSL_STOP),
        InvariantCase("order.stop_limit_fill", "order_contract", "STOP_LIMIT lifecycle", "STOP_LIMIT가 TRIGGERED -> FILLED lifecycle을 거치는지 검증", DSL_STOP_LIMIT),
        InvariantCase("order.day_expiry", "order_contract", "DAY expiry", "미체결 DAY pending 주문이 session end에서 EXPIRED 되는지 검증", DSL_DAY),
        InvariantCase("order.stable_client_cancel", "order_contract", "stable client id cancel", "DSL order.cancel(id=...)가 동일 client identity pending 주문을 취소하는지 검증", DSL_CANCEL),
        InvariantCase("mtf.confirmed_only", "time_contract", "MTF confirmed-only", "현재 미완성 상위봉 대신 직전 완료 상위봉만 노출되는지 검증", DSL_MTF),
    )
}


def _daily_market() -> dict:
    times = ["20200101", "20200102", "20200103", "20200104", "20200105"]
    open_ = [100.0, 100.0, 103.0, 102.0, 101.0]
    close = [100.0, 103.0, 102.0, 101.0, 100.0]
    high = [101.0, 105.0, 104.0, 103.0, 102.0]
    low = [99.0, 99.0, 100.0, 99.0, 98.0]
    return {
        "time": times,
        "open": open_, "high": high, "low": low, "close": close,
        "volume": [1000.0] * len(times),
        "_meta": {"source": "invariant_daily", "timeframe": "1d"},
    }


def _next_open_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 110.0, 100.0],
        "high": [106.0, 112.0, 101.0],
        "low": [99.0, 99.0, 99.0],
        "close": [105.0, 100.0, 100.0],
        "volume": [1000.0, 1000.0, 1000.0],
        "_meta": {"source": "invariant_next_open", "timeframe": "1d"},
    }


def _pending_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 100.0, 101.0],
        "high": [100.5, 103.0, 102.0],
        "low": [99.5, 99.0, 99.0],
        "close": [100.0, 101.0, 101.0],
        "volume": [1000.0, 1000.0, 1000.0],
        "_meta": {"source": "invariant_pending", "timeframe": "1d"},
    }


def _intraday_market() -> dict:
    times = [
        "20200102090000", "20200102090100", "20200102090200", "20200102090300",
        "20200102090400", "20200102090500", "20200102090600", "20200102090700",
    ]
    open_ = [100, 102, 100, 102, 100, 102, 100, 102]
    close = [102, 100, 102, 100, 102, 100, 102, 100]
    high = [103, 103, 103, 103, 103, 103, 103, 103]
    low = [99, 99, 99, 99, 99, 99, 99, 99]
    return {
        "time": times,
        "open": [float(x) for x in open_],
        "high": [float(x) for x in high],
        "low": [float(x) for x in low],
        "close": [float(x) for x in close],
        "volume": [1000.0] * len(times),
        "_meta": {"source": "invariant_intraday", "timeframe": "1m"},
    }


def _day_expiry_market() -> dict:
    return {
        "time": ["20200102090000", "20200102090100", "20200103090000"],
        "open": [100.0, 100.0, 100.0],
        "high": [101.0, 101.0, 101.0],
        "low": [99.0, 99.0, 99.0],
        "close": [100.0, 100.0, 100.0],
        "volume": [1000.0, 1000.0, 1000.0],
        "_meta": {"source": "invariant_day", "timeframe": "1m"},
    }


def _ctx_manifest() -> ParentFeatureManifest:
    return ParentFeatureManifest(
        provider_id="live_studio_ctx_fixture",
        provider_version="v1",
        layer="MARKET",
        context_id="KOSPI_REGIME",
        features=(
            ParentFeatureSpec("market.kospi_slope", "kospi_slope", "NUMBER"),
            ParentFeatureSpec("market.regime_state", "regime_state", "STRING"),
            ParentFeatureSpec("market.entry_permitted", "entry_permitted", "BOOLEAN"),
        ),
    )


def _ctx_fixture():
    manifest = _ctx_manifest()
    registry = ParentFeatureRegistry((manifest,))
    rows = [
        ("20260827090000", -0.2, "RISK_OFF", False),
        ("20260827090500", 0.4, "RISK_ON", True),
        ("20260827091000", 0.8, "RISK_ON", True),
    ]
    assemblies = []
    for timestamp, slope, regime, permitted in rows:
        result = ParentFeatureProviderResult(
            manifest=manifest,
            as_of=timestamp,
            knowledge_cutoff=timestamp,
            source="fixture://live-studio/context",
            features={"kospi_slope": slope, "regime_state": regime, "entry_permitted": permitted},
        )
        assemblies.append(ParentContextAssembler.assemble(
            as_of=timestamp,
            knowledge_cutoff=timestamp,
            results=(result,),
            mode="DEPLOYMENT",
        ))
    frame = ParentContextFrame.create(
        frame_id="LIVE_STUDIO_CTX",
        target_symbol="005930",
        registry=registry,
        assemblies=tuple(assemblies),
        mode="DEPLOYMENT",
    )
    market = {
        "time": [row[0] for row in rows],
        "open": [100.0, 101.0, 102.0],
        "high": [101.0, 102.0, 103.0],
        "low": [99.0, 100.0, 101.0],
        "close": [100.0, 101.0, 102.0],
        "volume": [1000.0, 1100.0, 1200.0],
        "_meta": {"source": "invariant_ctx", "timeframe": "5m", "instrument": "005930"},
    }
    return registry, frame, market


def _ok(case: InvariantCase, details: dict) -> dict:
    return {
        "ok": True,
        "invariant_id": case.invariant_id,
        "category": case.category,
        "title": case.title,
        "description": case.description,
        "dsl_code": case.dsl_code,
        "stage": "INVARIANT_PASS",
        "details": details,
    }


def _fail(case: InvariantCase, message: str, details: dict | None = None) -> dict:
    return {
        "ok": False,
        "invariant_id": case.invariant_id,
        "category": case.category,
        "title": case.title,
        "description": case.description,
        "dsl_code": case.dsl_code,
        "stage": "INVARIANT_FAIL",
        "message": message,
        "details": dict(details or {}),
    }


def _run_context_exact(case):
    registry, frame, market = _ctx_fixture()
    result = BacktestEngine.run(
        case.dsl_code,
        market=market,
        data_timeframe="5m",
        parent_context_frame=frame,
        parent_feature_registry=registry,
    )
    diag = result["diagnostics"]["parent_context"]
    if not diag.get("supplied") or diag.get("bar_count") != 3:
        return _fail(case, "exact context binding diagnostics mismatch", diag)
    if tuple(diag.get("feature_ids") or ()) != (
        "market.entry_permitted", "market.kospi_slope", "market.regime_state"
    ):
        return _fail(case, "exact context feature coverage mismatch", diag)
    if result["diagnostics"]["signal_counts"].get("__long_entry") != 2:
        return _fail(case, "ctx entry signal count must be exactly 2", result["diagnostics"]["signal_counts"])
    return _ok(case, {"binding_hash": diag.get("binding_hash"), "signal_count": 2})


def _run_context_missing(case):
    _registry, _frame, market = _ctx_fixture()
    try:
        BacktestEngine.run(case.dsl_code, market=market, data_timeframe="5m")
    except Exception as exc:
        text = str(exc).lower()
        if "binding" in text or "바인딩" in text:
            return _ok(case, {"error_type": type(exc).__name__, "message": str(exc)})
        return _fail(case, "ctx missing failed, but not for binding contract", {"message": str(exc)})
    return _fail(case, "ctx.* executed without required binding")


def _run_entry_gate(case):
    market = _daily_market()
    baseline = BacktestEngine.run(case.dsl_code, market=market, data_timeframe="1d")
    blocked = BacktestEngine.run(
        case.dsl_code,
        market=market,
        data_timeframe="1d",
        entry_gate=[False] * len(market["time"]),
    )
    if baseline["metrics_numeric"]["trade_count"] < 1:
        return _fail(case, "baseline must create at least one entry")
    if blocked["metrics_numeric"]["trade_count"] != 0:
        return _fail(case, "entry_gate=false must suppress all entries", blocked["metrics_numeric"])
    count = blocked["diagnostics"]["rejections"].get("higher_layer_gate_blocked", 0)
    if count < 1:
        return _fail(case, "suppression must be visible in rejection diagnostics")
    return _ok(case, {"baseline_entries": baseline["metrics_numeric"]["trade_count"], "blocked": count})


def _run_next_open(case):
    market = _next_open_market()
    result = BacktestEngine.run(
        case.dsl_code,
        market=market,
        data_timeframe="1d",
        settings={"signal_mode": "next_open"},
    )
    entries = [row for row in result["trades"] if row.get("kind") == "ENTRY"]
    if not entries:
        return _fail(case, "next_open example produced no entry")
    first = entries[0]
    if str(first.get("signal_time")) != market["time"][0] or str(first.get("time")) != market["time"][1]:
        return _fail(case, "next_open must fill bar N signal at bar N+1 open", first)
    if abs(float(first.get("price")) - float(market["open"][1])) > 1e-9:
        return _fail(case, "next_open fill price must equal next bar open", first)
    return _ok(case, first)


def _run_entry_time(case):
    market = _intraday_market()
    result = BacktestEngine.run(
        case.dsl_code,
        market=market,
        data_timeframe="1m",
        settings={"entry_start_time": 90500, "entry_end_time": 90700},
    )
    blocked = result["diagnostics"]["rejections"].get("entry_time_blocked", 0)
    if blocked < 1:
        return _fail(case, "outside-window entries were not blocked")
    entries = [row for row in result["trades"] if row.get("kind") == "ENTRY"]
    for row in entries:
        clock = int(str(row["time"])[8:14])
        if not 90500 <= clock < 90700:
            return _fail(case, "entry occurred outside declared time window", row)
    return _ok(case, {"blocked": blocked, "entries": len(entries)})


def _run_max_entries(case):
    market = _intraday_market()
    result = BacktestEngine.run(
        case.dsl_code,
        market=market,
        data_timeframe="1m",
        settings={"max_entries_per_day": 1},
    )
    entries = [row for row in result["trades"] if row.get("kind") == "ENTRY"]
    blocked = result["diagnostics"]["rejections"].get("entry_count_blocked", 0)
    if len(entries) != 1:
        return _fail(case, "max_entries_per_day=1 must permit exactly one entry in fixture", {"entries": entries})
    if blocked < 1:
        return _fail(case, "excess same-day entries must be diagnosed as entry_count_blocked")
    return _ok(case, {"entries": 1, "blocked": blocked})


def _pending_rows(result, client_id):
    return [row for row in result["diagnostics"]["pending_order_history"] if row.get("client_order_id") == client_id]


def _run_stop(case):
    result = BacktestEngine.run(case.dsl_code, market=_pending_market(), data_timeframe="1d")
    rows = _pending_rows(result, "stop-entry")
    statuses = [row.get("status") for row in rows]
    if "ACCEPTED" not in statuses or "FILLED" not in statuses:
        return _fail(case, "STOP must reach ACCEPTED and FILLED", {"statuses": statuses, "rows": rows})
    if not any(row.get("type") == "STOP" for row in rows):
        return _fail(case, "pending lifecycle lost STOP order type")
    return _ok(case, {"statuses": statuses})


def _run_stop_limit(case):
    result = BacktestEngine.run(case.dsl_code, market=_pending_market(), data_timeframe="1d")
    rows = _pending_rows(result, "stop-limit-entry")
    statuses = [row.get("status") for row in rows]
    if "TRIGGERED" not in statuses or "FILLED" not in statuses:
        return _fail(case, "STOP_LIMIT must reach TRIGGERED then FILLED", {"statuses": statuses, "rows": rows})
    if statuses.index("TRIGGERED") > statuses.index("FILLED"):
        return _fail(case, "STOP_LIMIT lifecycle order is invalid", {"statuses": statuses})
    return _ok(case, {"statuses": statuses})


def _run_day_expiry(case):
    result = BacktestEngine.run(case.dsl_code, market=_day_expiry_market(), data_timeframe="1m")
    rows = _pending_rows(result, "day-entry")
    if not any(row.get("status") == "EXPIRED" for row in rows):
        return _fail(case, "DAY pending order must expire at session end", {"rows": rows})
    return _ok(case, {"statuses": [row.get("status") for row in rows]})


def _run_cancel(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    rows = _pending_rows(result, "stable-client-id")
    if not rows:
        return _fail(case, "stable client id pending order was not created")
    if not any(row.get("status") == "CANCELED" and row.get("reason") == "DSL cancel" for row in rows):
        return _fail(case, "order.cancel did not cancel the exact stable client identity", {"rows": rows})
    return _ok(case, {"statuses": [row.get("status") for row in rows]})


def _run_mtf(case):
    market = {
        "time": [f"20200102090{i}00" for i in range(10)],
        "open": [100.0 + i for i in range(10)],
        "high": [101.0 + i for i in range(10)],
        "low": [99.0 + i for i in range(10)],
        "close": [100.0 + i for i in range(10)],
        "volume": [1000.0] * 10,
        "_meta": {"source": "invariant_mtf", "timeframe": "1m"},
    }
    BacktestEngine.run(case.dsl_code, market=market, data_timeframe="1m")
    values = {
        "date": np.asarray([20200102.0] * 10),
        "time": np.asarray([90000.0 + i * 100 for i in range(10)]),
        "open": np.asarray(market["open"]), "high": np.asarray(market["high"]),
        "low": np.asarray(market["low"]), "close": np.asarray(market["close"]),
        "volume": np.asarray(market["volume"]),
    }
    confirmed = MultiTimeframeContext(values).close("5m")
    if not np.all(np.isnan(confirmed[:5])):
        return _fail(case, "current uncompleted first 5m bucket leaked into output", {"confirmed": confirmed.tolist()})
    if not np.allclose(confirmed[5:], 104.0, equal_nan=False):
        return _fail(case, "second bucket must expose only prior completed 5m close=104", {"confirmed": confirmed.tolist()})
    return _ok(case, {"first_bucket": confirmed[:5].tolist(), "second_bucket": confirmed[5:].tolist()})


_RUNNERS: dict[str, Callable[[InvariantCase], dict]] = {
    "context.exact_binding": _run_context_exact,
    "context.missing_fail_closed": _run_context_missing,
    "execution.entry_gate_suppression": _run_entry_gate,
    "execution.next_open_timing": _run_next_open,
    "execution.entry_time_window": _run_entry_time,
    "execution.max_entries_per_day": _run_max_entries,
    "order.stop_fill": _run_stop,
    "order.stop_limit_fill": _run_stop_limit,
    "order.day_expiry": _run_day_expiry,
    "order.stable_client_cancel": _run_cancel,
    "mtf.confirmed_only": _run_mtf,
}


def run_invariant(invariant_id: str) -> dict:
    case = INVARIANT_CASES.get(invariant_id)
    if case is None:
        return {"ok": False, "invariant_id": invariant_id, "stage": "CATALOG", "message": "등록되지 않은 invariant"}
    try:
        return _RUNNERS[invariant_id](case)
    except Exception as exc:
        return _fail(case, f"unexpected {type(exc).__name__}: {exc}", {"error_type": type(exc).__name__})


def run_all_invariants() -> dict:
    results = [run_invariant(invariant_id) for invariant_id in INVARIANT_CASES]
    failed = [item for item in results if not item.get("ok")]
    return {
        "ok": not failed,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failed_invariant_ids": [item.get("invariant_id") for item in failed],
        "results": results,
    }
