"""Shared fail-closed order-shape guards for validated context integration.

The current validated-context entry gate is defined only for immediate MARKET
entry intent. Deferred LIMIT/STOP/STOP_LIMIT orders have a distinct signal-time
versus fill-time authority problem and therefore require a later, separately
validated contract.
"""
from __future__ import annotations

import ast

from core.dsl_parser import DSLParser


DEFERRED_ENTRY_ORDER_TYPES = {"LIMIT", "STOP", "STOP_LIMIT"}


def entry_order_types(dsl_code: str) -> tuple[str, ...]:
    """Return declared entry order types after the normal DSL parser validates syntax."""
    strategy = DSLParser.parse(dsl_code)
    result: list[str] = []
    for event in strategy.events:
        for order in event.orders:
            if order.command not in {"order.buy", "order.sell_short"}:
                continue
            order_type = "MARKET"
            arguments = str(order.arguments or "").strip()
            if arguments:
                call = ast.parse(f"f({arguments})", mode="eval").body
                for keyword in call.keywords:
                    if keyword.arg == "type":
                        if not isinstance(keyword.value, ast.Constant) or not isinstance(keyword.value.value, str):
                            raise ValueError("validated context integration 주문 type은 문자열 상수여야 합니다.")
                        order_type = str(keyword.value.value).strip().upper()
                        break
            result.append(order_type)
    return tuple(result)


def require_market_entry_orders_only(dsl_code: str, *, label: str) -> tuple[str, ...]:
    """Fail closed until deferred-order context timing receives its own authority contract."""
    types = entry_order_types(dsl_code)
    unsupported = tuple(sorted({item for item in types if item != "MARKET"}))
    if unsupported:
        raise ValueError(
            f"{label}은 MARKET 진입만 허용합니다. 예약주문 체결시점 정책은 별도 검증 전까지 금지됩니다: {unsupported}"
        )
    return types
