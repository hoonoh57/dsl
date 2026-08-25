"""Deterministic OHLC broker emulator with explicit order lifecycle evidence."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    TRIGGERED = "TRIGGERED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class BrokerOrder:
    id: str
    side: str
    type: str = "MARKET"
    quantity: float = 1.0
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: str = "GTC"
    oco: Optional[str] = None
    status: OrderStatus = OrderStatus.CREATED
    fill_price: Optional[float] = None
    reason: Optional[str] = None
    history: list[dict] = field(default_factory=list)


class BrokerEmulator:
    TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}
    TIFS = {"GTC", "DAY"}
    SIDES = {"BUY", "SELL_SHORT", "SELL", "COVER"}

    def __init__(self):
        self.orders: dict[str, BrokerOrder] = {}
        self.history: list[dict] = []
        self._sequence = 0

    def _transition(self, order: BrokerOrder, status: OrderStatus, *, reason=None, price=None, event=None):
        self._sequence += 1
        order.status = status
        if reason is not None:
            order.reason = str(reason)
        if price is not None:
            order.fill_price = float(price)
        row = {
            "sequence": self._sequence,
            "order_id": order.id,
            "side": order.side,
            "type": order.type,
            "quantity": float(order.quantity),
            "tif": order.tif,
            "status": status.value,
            "reason": order.reason,
            "fill_price": order.fill_price,
            "event": event,
        }
        order.history.append(dict(row))
        self.history.append(dict(row))
        return order

    def submit(self, order: BrokerOrder, event=None):
        order.type = str(order.type).upper()
        order.side = str(order.side).upper()
        order.tif = str(order.tif).upper()
        created_event = event if event is not None else "submit"
        accepted_event = event if event is not None else "accepted"
        self._transition(order, OrderStatus.CREATED, event=created_event)
        if order.id in self.orders:
            return self._reject(order, "duplicate id", event=event)
        if order.type not in self.TYPES:
            return self._reject(order, "unsupported order type", event=event)
        if order.tif not in self.TIFS:
            return self._reject(order, "unsupported tif", event=event)
        if order.side not in self.SIDES:
            return self._reject(order, "unsupported side", event=event)
        if order.quantity <= 0:
            return self._reject(order, "quantity must be positive", event=event)
        if order.type in {"LIMIT", "STOP_LIMIT"} and order.limit_price is None:
            return self._reject(order, "limit price required", event=event)
        if order.type in {"STOP", "STOP_LIMIT"} and order.stop_price is None:
            return self._reject(order, "stop price required", event=event)
        self.orders[order.id] = order
        return self._transition(order, OrderStatus.ACCEPTED, event=accepted_event)

    def _reject(self, order, reason, event=None):
        return self._transition(order, OrderStatus.REJECTED, reason=reason, event=event if event is not None else "rejected")

    def cancel(self, order_id, reason="user canceled", event=None):
        order = self.orders[order_id]
        if order.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
            self._transition(order, OrderStatus.CANCELED, reason=reason, event=event if event is not None else "canceled")
        return order

    def expire_day_orders(self, reason="DAY expired", event=None):
        expired = []
        for order in list(self.orders.values()):
            if order.tif == "DAY" and order.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
                self._transition(order, OrderStatus.EXPIRED, reason=reason, event=event if event is not None else "session_end")
                expired.append(order)
        return expired

    def process_bar(self, open_, high, low, close, end_of_session=False, event=None):
        fills = []
        for order in list(self.orders.values()):
            if order.status not in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
                continue
            buy = order.side in {"BUY", "COVER"}
            price = None
            if order.type == "MARKET":
                price = float(open_)
            elif order.type == "LIMIT" or order.status == OrderStatus.TRIGGERED:
                hit = low <= order.limit_price if buy else high >= order.limit_price
                if hit:
                    price = min(float(open_), order.limit_price) if buy else max(float(open_), order.limit_price)
            elif order.type in {"STOP", "STOP_LIMIT"}:
                hit = high >= order.stop_price if buy else low <= order.stop_price
                if hit:
                    if order.type == "STOP":
                        price = max(float(open_), order.stop_price) if buy else min(float(open_), order.stop_price)
                    else:
                        self._transition(order, OrderStatus.TRIGGERED, event=event if event is not None else "stop_triggered")
                        limit_hit = low <= order.limit_price if buy else high >= order.limit_price
                        if limit_hit:
                            price = float(order.limit_price)
            if price is not None:
                self._transition(order, OrderStatus.FILLED, price=price, event=event if event is not None else "bar_fill")
                fills.append(order)
                if order.oco:
                    for sibling in self.orders.values():
                        if sibling.id != order.id and sibling.oco == order.oco:
                            self.cancel(sibling.id, "OCO sibling filled", event=event)
            elif end_of_session and order.tif == "DAY":
                self._transition(order, OrderStatus.EXPIRED, reason="DAY expired", event=event if event is not None else "session_end")
        return fills

    def snapshot_history(self):
        return [dict(item) for item in self.history]
