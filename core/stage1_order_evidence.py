"""Broker-model lifecycle evidence for executed strategy MARKET orders.

The execution engine remains the accounting authority.  This module replays each
actual strategy-signal MARKET execution through the same BrokerEmulator solely
to expose the CREATED -> ACCEPTED -> FILLED lifecycle with separate signal and
fill timestamps.  Pending LIMIT/STOP lifecycle remains native backtest broker
history and is not duplicated here.
"""
from __future__ import annotations

from typing import Iterable

from core.broker import BrokerEmulator, BrokerOrder, OrderStatus


_SIDE = {
    "BUY": "BUY",
    "SHORT": "SELL_SHORT",
    "SELL": "SELL",
    "COVER": "COVER",
}


def strategy_market_order_lifecycle(executions: Iterable[dict]) -> list[dict]:
    broker = BrokerEmulator()
    output = []
    sequence = 0
    for execution_index, execution in enumerate(executions):
        if str(execution.get("reason", "")) != "STRATEGY_SIGNAL":
            continue
        side = _SIDE.get(str(execution.get("side", "")).upper())
        if not side:
            continue
        price = float(execution.get("price", 0.0) or 0.0)
        quantity = float(execution.get("quantity", 0.0) or 0.0)
        if price <= 0 or quantity <= 0:
            continue
        sequence += 1
        order_id = f"strategy-market-{sequence}"
        signal_time = execution.get("signal_time")
        fill_time = execution.get("time")
        order = broker.submit(
            BrokerOrder(order_id, side, type="MARKET", quantity=quantity),
            event=str(signal_time),
        )
        if order.status != OrderStatus.ACCEPTED:
            raise ValueError(f"strategy MARKET audit order rejected: {order_id}: {order.reason}")
        broker.process_bar(price, price, price, price, event=str(fill_time))
        if order.status != OrderStatus.FILLED:
            raise ValueError(f"strategy MARKET audit order did not fill: {order_id}")
        for row in order.history:
            output.append({
                **row,
                "execution_index": execution_index,
                "execution_kind": execution.get("kind"),
                "signal_time": signal_time,
                "fill_time": fill_time,
            })
    return output
