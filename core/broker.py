"""Deterministic OHLC broker emulator with explicit authoritative order lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


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
    origin: str = "UNSPECIFIED"
    signal_time: Optional[str] = None
    client_order_id: Optional[str] = None


FillResolver = Callable[[BrokerOrder, float], Optional[tuple[float, float]]]


class BrokerEmulator:
    """Owns the lifecycle of every order used by the Stage 1 execution engine.

    Price matching and lifecycle state live here.  Portfolio/accounting policy may
    provide a ``fill_resolver`` that converts a matched raw OHLC price into the
    actual execution price and quantity (for example slippage + capital sizing).
    The resolved values are written into the authoritative FILLED transition.
    """

    TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}
    TIFS = {"GTC", "DAY"}
    SIDES = {"BUY", "SELL_SHORT", "SELL", "COVER"}
    TERMINAL = {OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED}

    def __init__(self):
        self.orders: dict[str, BrokerOrder] = {}
        self.history: list[dict] = []
        self._sequence = 0

    def _transition(self, order: BrokerOrder, status: OrderStatus, *, reason=None, price=None,
                    quantity=None, event=None):
        self._sequence += 1
        order.status = status
        if reason is not None:
            order.reason = str(reason)
        if price is not None:
            order.fill_price = float(price)
        if quantity is not None:
            order.quantity = float(quantity)
        row = {
            "sequence": self._sequence,
            "order_id": order.id,
            "client_order_id": order.client_order_id,
            "origin": order.origin,
            "signal_time": order.signal_time,
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
        if order.signal_time is None and event is not None:
            order.signal_time = str(event)
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
        return self._transition(order, OrderStatus.REJECTED, reason=reason,
                                event=event if event is not None else "rejected")

    def fill(self, order_id: str, price: float, *, quantity: Optional[float] = None, event=None):
        """Fill one already-accepted order at an explicit execution price.

        This is the authoritative path for strategy MARKET fills and is also used
        by ``process_bar`` after OHLC matching.  A terminal order cannot be filled
        again.
        """
        order = self.orders[order_id]
        if order.status not in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
            raise ValueError(f"order cannot fill from {order.status.value}: {order_id}")
        resolved_price = float(price)
        resolved_quantity = float(order.quantity if quantity is None else quantity)
        if resolved_price <= 0:
            raise ValueError("fill price must be positive")
        if resolved_quantity <= 0:
            raise ValueError("fill quantity must be positive")
        self._transition(order, OrderStatus.FILLED, price=resolved_price, quantity=resolved_quantity,
                         event=event if event is not None else "fill")
        if order.oco:
            for sibling in list(self.orders.values()):
                if sibling.id != order.id and sibling.oco == order.oco and sibling.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
                    self.cancel(sibling.id, "OCO sibling filled", event=event)
        return order

    def cancel(self, order_id, reason="user canceled", event=None):
        order = self.orders[order_id]
        if order.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
            self._transition(order, OrderStatus.CANCELED, reason=reason,
                             event=event if event is not None else "canceled")
        return order

    def expire_day_orders(self, reason="DAY expired", event=None):
        expired = []
        for order in list(self.orders.values()):
            if order.tif == "DAY" and order.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
                self._transition(order, OrderStatus.EXPIRED, reason=reason,
                                 event=event if event is not None else "session_end")
                expired.append(order)
        return expired

    def active_orders(self):
        return [order for order in self.orders.values()
                if order.status in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}]

    def process_bar(self, open_, high, low, close, end_of_session=False, event=None,
                    fill_resolver: Optional[FillResolver] = None):
        """Match active orders against one OHLC bar and authoritatively fill them.

        ``fill_resolver(order, raw_price)`` may return ``(execution_price,
        execution_quantity)``.  Returning ``None`` leaves the order active.
        """
        fills = []
        for order in list(self.orders.values()):
            if order.status not in {OrderStatus.ACCEPTED, OrderStatus.TRIGGERED}:
                continue
            buy = order.side in {"BUY", "COVER"}
            raw_price = None
            if order.type == "MARKET":
                raw_price = float(open_)
            elif order.type == "LIMIT" or order.status == OrderStatus.TRIGGERED:
                hit = low <= order.limit_price if buy else high >= order.limit_price
                if hit:
                    raw_price = min(float(open_), order.limit_price) if buy else max(float(open_), order.limit_price)
            elif order.type in {"STOP", "STOP_LIMIT"}:
                hit = high >= order.stop_price if buy else low <= order.stop_price
                if hit:
                    if order.type == "STOP":
                        raw_price = max(float(open_), order.stop_price) if buy else min(float(open_), order.stop_price)
                    else:
                        self._transition(order, OrderStatus.TRIGGERED,
                                         event=event if event is not None else "stop_triggered")
                        limit_hit = low <= order.limit_price if buy else high >= order.limit_price
                        if limit_hit:
                            raw_price = float(order.limit_price)
            if raw_price is not None:
                resolved_price = float(raw_price)
                resolved_quantity = float(order.quantity)
                if fill_resolver is not None:
                    resolved = fill_resolver(order, resolved_price)
                    if resolved is None:
                        continue
                    resolved_price, resolved_quantity = resolved
                self.fill(order.id, resolved_price, quantity=resolved_quantity,
                          event=event if event is not None else "bar_fill")
                fills.append(order)
            elif end_of_session and order.tif == "DAY":
                self._transition(order, OrderStatus.EXPIRED, reason="DAY expired",
                                 event=event if event is not None else "session_end")
        return fills

    def snapshot_history(self):
        return [dict(item) for item in self.history]
