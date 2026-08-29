"""Feature Catalog v4: focused executable order/risk invariants.

This tranche verifies existing Core/Broker behavior only. It does not add or
weaken Parser, Runtime, Backtest, Broker, or risk rules.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable

from core.backtest import BacktestEngine


@dataclass(frozen=True)
class InvariantV4Case:
    invariant_id: str
    category: str
    title: str
    description: str
    dsl_code: str

    def public_dict(self) -> dict:
        return asdict(self)


DSL_LIMIT_FILL = '''strategy "Invariant_LimitFill" {
    timeframe = "1d"
    arm = close > 0
    on(arm) { order.buy(type = "LIMIT", id = "limit-entry", limit = close * 0.99, tif = "GTC") }
}'''

DSL_CANCEL_UNKNOWN = '''strategy "Invariant_CancelUnknown" {
    timeframe = "1d"
    cancel_now = close > 0
    on(cancel_now) { order.cancel(id = "missing-client-id") }
}'''

DSL_TAKE_PROFIT = '''strategy "Invariant_TakeProfit" {
    timeframe = "1d"
    enter = close > 0
    strategy_exit = close < open
    on(enter) { order.buy(type = "MARKET") }
    on(strategy_exit) { order.close_position() }
}'''

DSL_TRAILING_STOP = '''strategy "Invariant_TrailingStop" {
    timeframe = "1d"
    enter = close > 0
    strategy_exit = false
    on(enter) { order.buy(type = "MARKET") }
    on(strategy_exit) { order.close_position() }
}'''


INVARIANT_V4_CASES = {
    item.invariant_id: item for item in (
        InvariantV4Case(
            "order.limit_fill",
            "order_contract_v4",
            "LIMIT fill",
            "BUY LIMIT가 다음 OHLC에서 체결되고 favorable open gap이면 open 가격으로 체결되는지 검증",
            DSL_LIMIT_FILL,
        ),
        InvariantV4Case(
            "order.cancel_unknown_fail_closed",
            "order_contract_v4",
            "unknown cancel fail-closed",
            "존재하지 않는 client order id를 order.cancel하면 조용히 무시하지 않고 fail-closed 되는지 검증",
            DSL_CANCEL_UNKNOWN,
        ),
        InvariantV4Case(
            "execution.take_profit_precedence",
            "execution_contract_v4",
            "take-profit precedence",
            "TAKE_PROFIT이 같은 bar의 strategy exit보다 먼저 적용되는지 검증",
            DSL_TAKE_PROFIT,
        ),
        InvariantV4Case(
            "execution.trailing_stop",
            "execution_contract_v4",
            "trailing stop",
            "trailing activation 이후 OHLC low가 trailing price를 침범하면 TRAILING_STOP으로 청산되는지 검증",
            DSL_TRAILING_STOP,
        ),
    )
}


def _limit_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 98.0, 99.0],
        "high": [101.0, 100.0, 100.0],
        "low": [100.0, 97.0, 98.0],
        "close": [100.0, 99.0, 99.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v4_limit", "timeframe": "1d"},
    }


def _cancel_market() -> dict:
    return {
        "time": ["20200101", "20200102"],
        "open": [100.0, 100.0],
        "high": [101.0, 101.0],
        "low": [99.0, 99.0],
        "close": [100.0, 100.0],
        "volume": [1000.0, 1000.0],
        "_meta": {"source": "invariant_v4_cancel", "timeframe": "1d"},
    }


def _take_profit_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 103.0, 100.0],
        "high": [101.0, 106.0, 101.0],
        "low": [99.0, 98.0, 99.0],
        "close": [100.0, 99.0, 100.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v4_take_profit", "timeframe": "1d"},
    }


def _trailing_market() -> dict:
    return {
        "time": ["20200101", "20200102", "20200103"],
        "open": [100.0, 105.0, 106.0],
        "high": [101.0, 110.0, 107.0],
        "low": [99.0, 104.0, 105.0],
        "close": [100.0, 108.0, 106.0],
        "volume": [1000.0] * 3,
        "_meta": {"source": "invariant_v4_trailing", "timeframe": "1d"},
    }


def _ok(case, details):
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


def _fail(case, message, details=None):
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


def _run_limit_fill(case):
    result = BacktestEngine.run(case.dsl_code, market=_limit_market(), data_timeframe="1d")
    rows = [
        row for row in result["diagnostics"]["pending_order_history"]
        if row.get("client_order_id") == "limit-entry"
    ]
    fills = [row for row in rows if row.get("status") == "FILLED"]
    entries = [row for row in result["trades"] if row.get("kind") == "ENTRY"]
    if not fills or not entries:
        return _fail(case, "LIMIT order did not fill", {"pending_rows": rows, "trades": result["trades"]})
    fill_price = float(fills[0]["fill_price"])
    entry_price = float(entries[0]["price"])
    if abs(fill_price - 98.0) > 1e-9 or abs(entry_price - 98.0) > 1e-9:
        return _fail(case, "LIMIT favorable-open fill price mismatch", {"fill_price": fill_price, "entry_price": entry_price})
    return _ok(case, {"fill_price": fill_price, "entry_price": entry_price})


def _run_cancel_unknown(case):
    try:
        BacktestEngine.run(case.dsl_code, market=_cancel_market(), data_timeframe="1d")
    except KeyError as exc:
        if "unknown client_order_id" in str(exc):
            return _ok(case, {"error_type": type(exc).__name__, "message": str(exc)})
        return _fail(case, "cancel failed for unexpected KeyError", {"message": str(exc)})
    except Exception as exc:
        return _fail(case, "cancel failed for unexpected exception", {"error_type": type(exc).__name__, "message": str(exc)})
    return _fail(case, "unknown client order cancel was silently accepted")


def _run_take_profit(case):
    result = BacktestEngine.run(
        case.dsl_code,
        market=_take_profit_market(),
        data_timeframe="1d",
        settings={"take_profit_pct": 5.0},
    )
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits:
        return _fail(case, "TAKE_PROFIT produced no exit", {"trades": result["trades"]})
    first = exits[0]
    if first.get("reason") != "TAKE_PROFIT" or abs(float(first.get("price")) - 105.0) > 1e-9:
        return _fail(case, "TAKE_PROFIT did not precede strategy exit", {"first_exit": first, "trades": result["trades"]})
    return _ok(case, {"first_exit_reason": first["reason"], "price": float(first["price"])})


def _run_trailing_stop(case):
    result = BacktestEngine.run(
        case.dsl_code,
        market=_trailing_market(),
        data_timeframe="1d",
        settings={
            "trailing_enabled": True,
            "trailing_activation_pct": 5.0,
            "trailing_distance_pct": 3.0,
        },
    )
    exits = [row for row in result["trades"] if row.get("kind") == "EXIT"]
    if not exits:
        return _fail(case, "TRAILING_STOP produced no exit", {"trades": result["trades"]})
    first = exits[0]
    expected = 110.0 * 0.97
    if first.get("reason") != "TRAILING_STOP" or abs(float(first.get("price")) - expected) > 1e-9:
        return _fail(case, "TRAILING_STOP reason/price mismatch", {"expected": expected, "first_exit": first})
    return _ok(case, {"first_exit_reason": first["reason"], "price": float(first["price"]), "expected": expected})


_RUNNERS: dict[str, Callable[[InvariantV4Case], dict]] = {
    "order.limit_fill": _run_limit_fill,
    "order.cancel_unknown_fail_closed": _run_cancel_unknown,
    "execution.take_profit_precedence": _run_take_profit,
    "execution.trailing_stop": _run_trailing_stop,
}


def run_invariant_v4(invariant_id: str) -> dict:
    case = INVARIANT_V4_CASES.get(invariant_id)
    if case is None:
        return {"ok": False, "invariant_id": invariant_id, "stage": "CATALOG", "message": "등록되지 않은 v4 invariant"}
    try:
        return _RUNNERS[invariant_id](case)
    except Exception as exc:
        return _fail(case, f"unexpected {type(exc).__name__}: {exc}", {"error_type": type(exc).__name__})


def run_all_invariants_v4() -> dict:
    results = [run_invariant_v4(key) for key in INVARIANT_V4_CASES]
    failed = [item for item in results if not item.get("ok")]
    return {
        "ok": not failed,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "failed_invariant_ids": [item.get("invariant_id") for item in failed],
        "results": results,
    }
