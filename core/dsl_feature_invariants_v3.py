"""Feature Catalog v3: additional executable DSL/Broker invariants.

This module extends the trusted v2 invariant harness without mutating it.  Each
case asserts an observable execution contract rather than mere non-exception.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable

from core.backtest import BacktestEngine


@dataclass(frozen=True)
class InvariantV3Case:
    invariant_id: str
    category: str
    title: str
    description: str
    dsl_code: str

    def public_dict(self) -> dict:
        return asdict(self)


DSL_OCO = '''strategy "Invariant_OCO" {
    timeframe = "1d"
    arm = close > 0
    on(arm) {
        order.buy(type = "LIMIT", id = "oco-near", limit = close * 0.99, tif = "GTC", oco = "entry-pair")
        order.buy(type = "LIMIT", id = "oco-far", limit = close * 0.90, tif = "GTC", oco = "entry-pair")
    }
}'''

DSL_GTC = '''strategy "Invariant_GTC" {
    timeframe = "1m"
    arm = close > 0
    on(arm) { order.buy(type = "LIMIT", id = "gtc-persist", limit = close * 0.50, tif = "GTC") }
}'''

DSL_CLOSE_LONG = '''strategy "Invariant_CloseLong" {
    timeframe = "1d"
    entry_cond = close > 0
    exit_cond = close < open
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_long() }
}'''

DSL_CLOSE_SHORT = '''strategy "Invariant_CloseShort" {
    timeframe = "1d"
    entry_cond = close > 0
    exit_cond = close > open
    on(entry_cond) { order.sell_short(type = "MARKET") }
    on(exit_cond) { order.close_short() }
}'''

DSL_CLOSE_POSITION = '''strategy "Invariant_ClosePosition" {
    timeframe = "1d"
    entry_cond = close > 0
    exit_cond = close < open
    on(entry_cond) { order.buy(type = "MARKET") }
    on(exit_cond) { order.close_position() }
}'''

DSL_PENDING_OCCUPIED = '''strategy "Invariant_PendingOccupied" {
    timeframe = "1d"
    enter_now = close > 0
    arm_pending = close > 0
    on(enter_now) { order.buy(type = "MARKET") }
    on(arm_pending) { order.buy(type = "LIMIT", id = "blocked-pending", limit = close * 0.50, tif = "GTC") }
}'''

DSL_SAME_BAR_REENTRY = '''strategy "Invariant_SameBarReentry" {
    timeframe = "1d"
    enter = close > 0
    exit = close < open
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_position() }
}'''

DSL_RISK_PRECEDENCE = '''strategy "Invariant_RiskPrecedence" {
    timeframe = "1d"
    enter = close > 0
    exit = close < open
    on(enter) { order.buy(type = "MARKET") }
    on(exit) { order.close_position() }
}'''


INVARIANT_V3_CASES = {
    item.invariant_id: item for item in (
        InvariantV3Case("order.oco_sibling_cancel", "order_contract_v3", "OCO sibling cancel", "한 OCO 주문 체결 시 sibling pending 주문이 BrokerEmulator에서 취소되는지 검증", DSL_OCO),
        InvariantV3Case("order.gtc_persistence", "order_contract_v3", "GTC persistence", "GTC pending 주문이 session 경계를 넘어 EXPIRED 되지 않고 유지되는지 검증", DSL_GTC),
        InvariantV3Case("order.close_long", "order_contract_v3", "close_long", "long position만 SELL로 정상 청산되는지 검증", DSL_CLOSE_LONG),
        InvariantV3Case("order.close_short", "order_contract_v3", "close_short", "short position만 COVER로 정상 청산되는지 검증", DSL_CLOSE_SHORT),
        InvariantV3Case("order.close_position", "order_contract_v3", "close_position", "현재 포지션 방향과 무관한 generic close 경로를 검증", DSL_CLOSE_POSITION),
        InvariantV3Case("execution.pending_suppressed_position_occupied", "execution_contract_v3", "pending suppressed while occupied", "포지션 보유 중 신규 deferred entry가 제출되지 않고 diagnostics에 기록되는지 검증", DSL_PENDING_OCCUPIED),
        InvariantV3Case("execution.same_bar_reentry", "execution_contract_v3", "same-bar reentry blocked", "같은 bar에서 청산 후 재진입이 차단되는지 검증", DSL_SAME_BAR_REENTRY),
        InvariantV3Case("execution.risk_exit_precedence", "execution_contract_v3", "risk exit precedence", "STOP_LOSS가 같은 bar의 strategy exit보다 먼저 적용되는지 검증", DSL_RISK_PRECEDENCE),
    )
}


def _daily_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103", "20200104"],
        "open": [100.0, 103.0, 103.0, 102.0],
        "high": [101.0, 104.0, 104.0, 103.0],
        "low": [99.0, 98.0, 97.0, 98.0],
        "close": [100.0, 102.0, 99.0, 101.0],
        "volume": [1000.0] * 4,
        "_meta": {"source": "invariant_v3_daily", "timeframe": "1d"},
    }


def _oco_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 100.0, 100.0],
        "high": [101.0, 101.0, 101.0],
        "low": [100.0, 98.0, 98.0],
        "close": [100.0, 100.0, 100.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v3_oco", "timeframe": "1d"},
    }


def _gtc_market() -> dict:
    return {
        "time": ["20200102153000", "20200103090000", "20200103090100"],
        "open": [100.0, 100.0, 100.0],
        "high": [101.0, 101.0, 101.0],
        "low": [99.0, 99.0, 99.0],
        "close": [100.0, 100.0, 100.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v3_gtc", "timeframe": "1m"},
    }


def _pending_rows(result, client_id):
    return [row for row in result["diagnostics"]["pending_order_history"] if row.get("client_order_id") == client_id]


def _ok(case, details):
    return {"ok": True, "invariant_id": case.invariant_id, "category": case.category, "title": case.title,
            "description": case.description, "dsl_code": case.dsl_code, "stage": "INVARIANT_PASS", "details": details}


def _fail(case, message, details=None):
    return {"ok": False, "invariant_id": case.invariant_id, "category": case.category, "title": case.title,
            "description": case.description, "dsl_code": case.dsl_code, "stage": "INVARIANT_FAIL",
            "message": message, "details": dict(details or {})}


def _run_oco(case):
    result = BacktestEngine.run(case.dsl_code, market=_oco_market(), data_timeframe="1d")
    near = _pending_rows(result, "oco-near")
    far = _pending_rows(result, "oco-far")
    near_status = [row.get("status") for row in near]
    far_status = [row.get("status") for row in far]
    if "FILLED" not in near_status:
        return _fail(case, "near OCO order did not fill", {"near": near, "far": far})
    if not any(row.get("status") == "CANCELED" and row.get("reason") == "OCO sibling filled" for row in far):
        return _fail(case, "OCO sibling was not canceled by broker", {"near": near, "far": far})
    return _ok(case, {"near_status": near_status, "far_status": far_status})


def _run_gtc(case):
    rows = _pending_rows(BacktestEngine.run(case.dsl_code, market=_gtc_market(), data_timeframe="1m"), "gtc-persist")
    statuses = [row.get("status") for row in rows]
    if "ACCEPTED" not in statuses or "EXPIRED" in statuses:
        return _fail(case, "GTC order did not persist across session boundary", {"rows": rows})
    return _ok(case, {"statuses": statuses})


def _run_close_long(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits or exits[0].get("side") != "SELL":
        return _fail(case, "close_long did not produce SELL exit", {"trades": result["trades"]})
    return _ok(case, {"exit_side": exits[0]["side"]})


def _run_close_short(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits or exits[0].get("side") != "COVER":
        return _fail(case, "close_short did not produce COVER exit", {"trades": result["trades"]})
    return _ok(case, {"exit_side": exits[0]["side"]})


def _run_close_position(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits or exits[0].get("reason") != "STRATEGY_SIGNAL":
        return _fail(case, "close_position generic exit missing", {"trades": result["trades"]})
    return _ok(case, {"exit_side": exits[0].get("side"), "reason": exits[0].get("reason")})


def _run_pending_occupied(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    blocked = result["diagnostics"]["rejections"].get("pending_suppressed_position_occupied", 0)
    rows = _pending_rows(result, "blocked-pending")
    if blocked < 1:
        return _fail(case, "pending entry was not suppressed while position occupied", {"rejections": result["diagnostics"]["rejections"]})
    if any(row.get("status") == "FILLED" for row in rows):
        return _fail(case, "suppressed pending entry unexpectedly filled", {"rows": rows})
    return _ok(case, {"blocked": blocked, "pending_rows": rows})


def _run_same_bar(case):
    result = BacktestEngine.run(case.dsl_code, market=_daily_market(), data_timeframe="1d")
    blocked = result["diagnostics"]["rejections"].get("same_bar_reentry", 0)
    if blocked < 1:
        return _fail(case, "same-bar reentry was not blocked", {"rejections": result["diagnostics"]["rejections"], "trades": result["trades"]})
    return _ok(case, {"same_bar_reentry": blocked})


def _run_risk_precedence(case):
    market = {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 103.0, 100.0],
        "high": [101.0, 104.0, 101.0],
        "low": [99.0, 95.0, 99.0],
        "close": [100.0, 99.0, 100.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v3_risk", "timeframe": "1d"},
    }
    result = BacktestEngine.run(case.dsl_code, market=market, data_timeframe="1d", settings={"stop_loss_pct": 3.0})
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits or exits[0].get("reason") != "STOP_LOSS":
        return _fail(case, "risk exit did not take precedence over same-bar strategy exit", {"trades": result["trades"]})
    return _ok(case, {"first_exit_reason": exits[0]["reason"]})


_RUNNERS: dict[str, Callable[[InvariantV3Case], dict]] = {
    "order.oco_sibling_cancel": _run_oco,
    "order.gtc_persistence": _run_gtc,
    "order.close_long": _run_close_long,
    "order.close_short": _run_close_short,
    "order.close_position": _run_close_position,
    "execution.pending_suppressed_position_occupied": _run_pending_occupied,
    "execution.same_bar_reentry": _run_same_bar,
    "execution.risk_exit_precedence": _run_risk_precedence,
}


def run_invariant_v3(invariant_id: str) -> dict:
    case = INVARIANT_V3_CASES.get(invariant_id)
    if case is None:
        return {"ok": False, "invariant_id": invariant_id, "stage": "CATALOG", "message": "등록되지 않은 v3 invariant"}
    try:
        return _RUNNERS[invariant_id](case)
    except Exception as exc:
        return _fail(case, f"unexpected {type(exc).__name__}: {exc}", {"error_type": type(exc).__name__})


def run_all_invariants_v3() -> dict:
    results = [run_invariant_v3(key) for key in INVARIANT_V3_CASES]
    failed = [item for item in results if not item.get("ok")]
    return {
        "ok": not failed,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failed_invariant_ids": [item.get("invariant_id") for item in failed],
        "results": results,
    }
