"""Deterministic partial-fill and partial-exit execution primitives for AXIS 1.

This module is additive.  It deliberately does not modify the migrated whole-fill
BrokerEmulator or BacktestEngine.  One order may be filled in multiple slices and
one position may be exited in multiple slices, while pyramiding remains forbidden
until Step 5-8.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Optional


_EPS = 1e-12


class PartialExecutionError(ValueError):
    def __init__(self, message: str, code: str = "PARTIAL_EXECUTION_ERROR"):
        self.code = str(code)
        super().__init__(message)


class PartialOrderStatus(str, Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    TRIGGERED = "TRIGGERED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class PartialFillRecord:
    sequence: int
    order_id: str
    side: str
    price: float
    quantity: float
    cumulative_quantity: float
    remaining_quantity: float
    average_fill_price: float
    event: Optional[str] = None

    def public_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "order_id": self.order_id,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "cumulative_quantity": self.cumulative_quantity,
            "remaining_quantity": self.remaining_quantity,
            "average_fill_price": self.average_fill_price,
            "event": self.event,
        }


@dataclass
class PartialFillOrder:
    id: str
    side: str
    quantity: float
    type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: str = "GTC"
    oco: Optional[str] = None
    origin: str = "UNSPECIFIED"
    signal_time: Optional[str] = None
    client_order_id: Optional[str] = None
    status: PartialOrderStatus = PartialOrderStatus.CREATED
    reason: Optional[str] = None
    filled_quantity: float = 0.0
    remaining_quantity: float = field(init=False)
    average_fill_price: Optional[float] = None
    fill_notional: float = 0.0
    fills: list[PartialFillRecord] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.remaining_quantity = float(self.quantity)

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "side": self.side,
            "type": self.type,
            "quantity": float(self.quantity),
            "filled_quantity": float(self.filled_quantity),
            "remaining_quantity": float(self.remaining_quantity),
            "average_fill_price": self.average_fill_price,
            "tif": self.tif,
            "oco": self.oco,
            "status": self.status.value,
            "reason": self.reason,
            "origin": self.origin,
            "signal_time": self.signal_time,
            "client_order_id": self.client_order_id,
            "fills": [item.public_dict() for item in self.fills],
        }


class PartialFillBroker:
    """Order lifecycle with cumulative/remaining quantity and a fill ledger."""

    TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}
    TIFS = {"GTC", "DAY"}
    SIDES = {"BUY", "SELL_SHORT", "SELL", "COVER"}
    ACTIVE = {
        PartialOrderStatus.ACCEPTED,
        PartialOrderStatus.TRIGGERED,
        PartialOrderStatus.PARTIALLY_FILLED,
    }
    TERMINAL = {
        PartialOrderStatus.FILLED,
        PartialOrderStatus.CANCELED,
        PartialOrderStatus.REJECTED,
        PartialOrderStatus.EXPIRED,
    }

    def __init__(self):
        self.orders: dict[str, PartialFillOrder] = {}
        self.history: list[dict] = []
        self._transition_sequence = 0
        self._fill_sequence = 0

    @staticmethod
    def _finite_positive(value, label: str) -> float:
        if isinstance(value, bool):
            raise PartialExecutionError(f"{label} must be a positive finite number", "BAD_NUMERIC_VALUE")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise PartialExecutionError(f"{label} must be a positive finite number", "BAD_NUMERIC_VALUE") from exc
        if not math.isfinite(number) or number <= 0:
            raise PartialExecutionError(f"{label} must be a positive finite number", "BAD_NUMERIC_VALUE")
        return number

    def _transition(self, order: PartialFillOrder, status: PartialOrderStatus, *, reason=None, event=None):
        self._transition_sequence += 1
        order.status = status
        if reason is not None:
            order.reason = str(reason)
        row = {
            "sequence": self._transition_sequence,
            "order_id": order.id,
            "client_order_id": order.client_order_id,
            "origin": order.origin,
            "signal_time": order.signal_time,
            "side": order.side,
            "type": order.type,
            "quantity": float(order.quantity),
            "filled_quantity": float(order.filled_quantity),
            "remaining_quantity": float(order.remaining_quantity),
            "average_fill_price": order.average_fill_price,
            "tif": order.tif,
            "status": status.value,
            "reason": order.reason,
            "event": event,
        }
        order.history.append(dict(row))
        self.history.append(dict(row))
        return order

    def _reject(self, order: PartialFillOrder, reason: str, *, event=None):
        return self._transition(order, PartialOrderStatus.REJECTED, reason=reason, event=event)

    def submit(self, order: PartialFillOrder, *, event=None) -> PartialFillOrder:
        order.type = str(order.type).upper()
        order.side = str(order.side).upper()
        order.tif = str(order.tif).upper()
        order.id = str(order.id)
        created_event = event if event is not None else "submit"
        self._transition(order, PartialOrderStatus.CREATED, event=created_event)
        if not order.id:
            return self._reject(order, "empty id", event=event)
        if order.id in self.orders:
            return self._reject(order, "duplicate id", event=event)
        try:
            order.quantity = self._finite_positive(order.quantity, "quantity")
        except PartialExecutionError:
            return self._reject(order, "quantity must be positive", event=event)
        order.remaining_quantity = float(order.quantity)
        if order.type not in self.TYPES:
            return self._reject(order, "unsupported order type", event=event)
        if order.tif not in self.TIFS:
            return self._reject(order, "unsupported tif", event=event)
        if order.side not in self.SIDES:
            return self._reject(order, "unsupported side", event=event)
        if order.type in {"LIMIT", "STOP_LIMIT"} and order.limit_price is None:
            return self._reject(order, "limit price required", event=event)
        if order.type in {"STOP", "STOP_LIMIT"} and order.stop_price is None:
            return self._reject(order, "stop price required", event=event)
        if order.limit_price is not None:
            try:
                order.limit_price = self._finite_positive(order.limit_price, "limit_price")
            except PartialExecutionError:
                return self._reject(order, "limit price must be positive", event=event)
        if order.stop_price is not None:
            try:
                order.stop_price = self._finite_positive(order.stop_price, "stop_price")
            except PartialExecutionError:
                return self._reject(order, "stop price must be positive", event=event)
        self.orders[order.id] = order
        return self._transition(order, PartialOrderStatus.ACCEPTED, event=event if event is not None else "accepted")

    def fill(self, order_id: str, price: float, quantity: float, *, event=None) -> PartialFillRecord:
        if order_id not in self.orders:
            raise PartialExecutionError(f"unknown order: {order_id}", "UNKNOWN_ORDER")
        order = self.orders[order_id]
        if order.status not in self.ACTIVE:
            raise PartialExecutionError(
                f"order cannot fill from {order.status.value}: {order_id}", "BAD_FILL_TRANSITION"
            )
        fill_price = self._finite_positive(price, "fill price")
        fill_quantity = self._finite_positive(quantity, "fill quantity")
        if fill_quantity > order.remaining_quantity + _EPS:
            raise PartialExecutionError(
                f"fill exceeds remaining quantity: {fill_quantity} > {order.remaining_quantity}", "ORDER_OVERFILL"
            )
        if abs(fill_quantity - order.remaining_quantity) <= _EPS:
            fill_quantity = float(order.remaining_quantity)

        new_filled = float(order.filled_quantity + fill_quantity)
        new_remaining = max(0.0, float(order.quantity - new_filled))
        new_notional = float(order.fill_notional + fill_price * fill_quantity)
        new_average = new_notional / new_filled

        order.filled_quantity = new_filled
        order.remaining_quantity = new_remaining
        order.fill_notional = new_notional
        order.average_fill_price = new_average
        self._fill_sequence += 1
        record = PartialFillRecord(
            sequence=self._fill_sequence,
            order_id=order.id,
            side=order.side,
            price=fill_price,
            quantity=fill_quantity,
            cumulative_quantity=new_filled,
            remaining_quantity=new_remaining,
            average_fill_price=new_average,
            event=None if event is None else str(event),
        )
        order.fills.append(record)
        status = PartialOrderStatus.FILLED if new_remaining <= _EPS else PartialOrderStatus.PARTIALLY_FILLED
        self._transition(order, status, event=event if event is not None else "fill")

        # Once either OCO sibling starts executing, the opposite live order must
        # not later add exposure.  Existing filled quantity is never undone.
        if order.oco:
            for sibling in list(self.orders.values()):
                if sibling.id != order.id and sibling.oco == order.oco and sibling.status in self.ACTIVE:
                    self.cancel(sibling.id, reason="OCO sibling executed", event=event)
        return record

    def cancel(self, order_id: str, reason: str = "user canceled", *, event=None) -> PartialFillOrder:
        if order_id not in self.orders:
            raise PartialExecutionError(f"unknown order: {order_id}", "UNKNOWN_ORDER")
        order = self.orders[order_id]
        if order.status in self.ACTIVE:
            self._transition(order, PartialOrderStatus.CANCELED, reason=reason, event=event if event is not None else "canceled")
        return order

    def expire_day_orders(self, *, event=None) -> list[PartialFillOrder]:
        expired = []
        for order in list(self.orders.values()):
            if order.tif == "DAY" and order.status in self.ACTIVE:
                self._transition(
                    order,
                    PartialOrderStatus.EXPIRED,
                    reason="DAY expired",
                    event=event if event is not None else "session_end",
                )
                expired.append(order)
        return expired

    def active_orders(self) -> list[PartialFillOrder]:
        return [order for order in self.orders.values() if order.status in self.ACTIVE]

    def snapshot_history(self) -> list[dict]:
        return [dict(item) for item in self.history]

    def snapshot_orders(self) -> tuple[dict, ...]:
        return tuple(self.orders[key].public_dict() for key in sorted(self.orders))


@dataclass(frozen=True)
class RealizedExitSlice:
    order_id: str
    side: str
    price: float
    quantity: float
    gross_pnl: float
    allocated_entry_fee: float
    exit_fee: float
    net_pnl: float
    remaining_position_quantity: float
    event: Optional[str] = None

    def public_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "gross_pnl": self.gross_pnl,
            "allocated_entry_fee": self.allocated_entry_fee,
            "exit_fee": self.exit_fee,
            "net_pnl": self.net_pnl,
            "remaining_position_quantity": self.remaining_position_quantity,
            "event": self.event,
        }


class SinglePositionLedger:
    """Single-position accounting with weighted partial entry and partial exits.

    Additional entry orders while a position exists are intentionally rejected.
    Multiple fills belonging to the *same* original entry order are allowed so a
    partially-filled entry can complete without being misclassified as pyramiding.
    """

    def __init__(
        self,
        *,
        initial_cash: float = 0.0,
        commission_pct: float = 0.0,
        sell_tax_pct: float = 0.0,
    ):
        self.cash = self._finite(initial_cash, "initial_cash", nonnegative=False)
        self.commission_pct = self._finite(commission_pct, "commission_pct", nonnegative=True)
        self.sell_tax_pct = self._finite(sell_tax_pct, "sell_tax_pct", nonnegative=True)
        self.position = 0
        self.quantity = 0.0
        self.average_entry_price = 0.0
        self.entry_fee_remaining = 0.0
        self.entry_order_id: Optional[str] = None
        self.realized_pnl = 0.0
        self.closed_position_count = 0
        self.realized_exits: list[RealizedExitSlice] = []
        self.audit: list[dict] = []

    @staticmethod
    def _finite(value, label: str, *, nonnegative=False, positive=False) -> float:
        if isinstance(value, bool):
            raise PartialExecutionError(f"{label} must be numeric", "BAD_ACCOUNTING_VALUE")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise PartialExecutionError(f"{label} must be numeric", "BAD_ACCOUNTING_VALUE") from exc
        if not math.isfinite(number):
            raise PartialExecutionError(f"{label} must be finite", "BAD_ACCOUNTING_VALUE")
        if positive and number <= 0:
            raise PartialExecutionError(f"{label} must be positive", "BAD_ACCOUNTING_VALUE")
        if nonnegative and number < 0:
            raise PartialExecutionError(f"{label} must be nonnegative", "BAD_ACCOUNTING_VALUE")
        return number

    def _entry_fee(self, position_side: int, notional: float) -> float:
        pct = self.commission_pct + (self.sell_tax_pct if position_side == -1 else 0.0)
        return notional * pct / 100.0

    def _exit_fee(self, position_side: int, notional: float) -> float:
        pct = self.commission_pct + (self.sell_tax_pct if position_side == 1 else 0.0)
        return notional * pct / 100.0

    def validate_entry_fill(self, order_id: str, side: str, quantity: float) -> None:
        side_name = str(side).upper()
        if side_name not in {"BUY", "SELL_SHORT"}:
            raise PartialExecutionError(f"invalid entry side: {side}", "BAD_ENTRY_SIDE")
        self._finite(quantity, "entry fill quantity", positive=True)
        expected_position = 1 if side_name == "BUY" else -1
        if self.position == 0:
            return
        if self.position != expected_position or self.entry_order_id != str(order_id):
            raise PartialExecutionError(
                "additional entry while a position exists is reserved for Step 5-8 pyramiding",
                "PYRAMIDING_NOT_SUPPORTED",
            )

    def validate_exit_fill(self, side: str, quantity: float) -> None:
        side_name = str(side).upper()
        qty = self._finite(quantity, "exit fill quantity", positive=True)
        if self.position == 0:
            raise PartialExecutionError("cannot exit a flat position", "EXIT_WHILE_FLAT")
        expected = "SELL" if self.position == 1 else "COVER"
        if side_name != expected:
            raise PartialExecutionError(f"exit side must be {expected}", "BAD_EXIT_SIDE")
        if qty > self.quantity + _EPS:
            raise PartialExecutionError(
                f"exit exceeds position quantity: {qty} > {self.quantity}", "POSITION_OVEREXIT"
            )

    def apply_entry_fill(self, order_id: str, side: str, price: float, quantity: float, *, event=None) -> dict:
        self.validate_entry_fill(order_id, side, quantity)
        fill_price = self._finite(price, "entry fill price", positive=True)
        qty = self._finite(quantity, "entry fill quantity", positive=True)
        side_name = str(side).upper()
        position_side = 1 if side_name == "BUY" else -1
        old_qty = float(self.quantity)
        new_qty = old_qty + qty
        weighted_notional = self.average_entry_price * old_qty + fill_price * qty
        fee = self._entry_fee(position_side, fill_price * qty)
        if position_side == 1:
            self.cash -= fill_price * qty + fee
        else:
            self.cash += fill_price * qty - fee
        self.position = position_side
        self.quantity = new_qty
        self.average_entry_price = weighted_notional / new_qty
        self.entry_fee_remaining += fee
        if self.entry_order_id is None:
            self.entry_order_id = str(order_id)
        row = {
            "kind": "ENTRY_FILL",
            "order_id": str(order_id),
            "side": side_name,
            "price": fill_price,
            "quantity": qty,
            "position_quantity": self.quantity,
            "average_entry_price": self.average_entry_price,
            "fee": fee,
            "event": None if event is None else str(event),
        }
        self.audit.append(dict(row))
        return row

    def apply_exit_fill(self, order_id: str, side: str, price: float, quantity: float, *, event=None) -> RealizedExitSlice:
        self.validate_exit_fill(side, quantity)
        fill_price = self._finite(price, "exit fill price", positive=True)
        qty = self._finite(quantity, "exit fill quantity", positive=True)
        side_name = str(side).upper()
        quantity_before = float(self.quantity)
        position_side = int(self.position)
        entry_fee_alloc = self.entry_fee_remaining * (qty / quantity_before)
        notional = fill_price * qty
        exit_fee = self._exit_fee(position_side, notional)
        if position_side == 1:
            self.cash += notional - exit_fee
            gross = qty * (fill_price - self.average_entry_price)
        else:
            self.cash -= notional + exit_fee
            gross = qty * (self.average_entry_price - fill_price)
        net = gross - entry_fee_alloc - exit_fee
        remaining = max(0.0, quantity_before - qty)
        self.quantity = remaining
        self.entry_fee_remaining = max(0.0, self.entry_fee_remaining - entry_fee_alloc)
        self.realized_pnl += net
        result = RealizedExitSlice(
            order_id=str(order_id),
            side=side_name,
            price=fill_price,
            quantity=qty,
            gross_pnl=gross,
            allocated_entry_fee=entry_fee_alloc,
            exit_fee=exit_fee,
            net_pnl=net,
            remaining_position_quantity=remaining,
            event=None if event is None else str(event),
        )
        self.realized_exits.append(result)
        self.audit.append({"kind": "EXIT_FILL", **result.public_dict()})
        if remaining <= _EPS:
            self.position = 0
            self.quantity = 0.0
            self.average_entry_price = 0.0
            self.entry_fee_remaining = 0.0
            self.entry_order_id = None
            self.closed_position_count += 1
        return result

    def equity(self, mark_price: float) -> float:
        price = self._finite(mark_price, "mark_price", positive=True)
        if self.position == 1:
            return self.cash + self.quantity * price
        if self.position == -1:
            return self.cash - self.quantity * price
        return self.cash

    def position_snapshot(self) -> dict:
        return {
            "position": int(self.position),
            "quantity": float(self.quantity),
            "average_entry_price": float(self.average_entry_price),
            "entry_fee_remaining": float(self.entry_fee_remaining),
            "entry_order_id": self.entry_order_id,
            "realized_pnl": float(self.realized_pnl),
            "closed_position_count": int(self.closed_position_count),
            "cash": float(self.cash),
        }


class PartialExecutionSession:
    """Fail-closed coordinator for partial orders and one-position accounting."""

    def __init__(
        self,
        *,
        initial_cash: float = 0.0,
        commission_pct: float = 0.0,
        sell_tax_pct: float = 0.0,
    ):
        self.broker = PartialFillBroker()
        self.ledger = SinglePositionLedger(
            initial_cash=initial_cash,
            commission_pct=commission_pct,
            sell_tax_pct=sell_tax_pct,
        )
        self._intent: dict[str, str] = {}

    def _active_intent(self, intent: str) -> list[PartialFillOrder]:
        return [
            order
            for order in self.broker.active_orders()
            if self._intent.get(order.id) == intent
        ]

    def submit_entry(
        self,
        order_id: str,
        side: str,
        quantity: float,
        *,
        type: str = "MARKET",
        limit_price=None,
        stop_price=None,
        tif: str = "GTC",
        oco=None,
        origin: str = "PARTIAL_ENTRY",
        signal_time=None,
        client_order_id=None,
        event=None,
    ) -> PartialFillOrder:
        side_name = str(side).upper()
        if side_name not in {"BUY", "SELL_SHORT"}:
            raise PartialExecutionError("entry side must be BUY or SELL_SHORT", "BAD_ENTRY_SIDE")
        if self.ledger.position != 0 or self._active_intent("ENTRY"):
            raise PartialExecutionError(
                "additional entry order is reserved for Step 5-8 pyramiding",
                "PYRAMIDING_NOT_SUPPORTED",
            )
        order = PartialFillOrder(
            id=str(order_id),
            side=side_name,
            quantity=quantity,
            type=type,
            limit_price=limit_price,
            stop_price=stop_price,
            tif=tif,
            oco=oco,
            origin=origin,
            signal_time=None if signal_time is None else str(signal_time),
            client_order_id=client_order_id,
        )
        submitted = self.broker.submit(order, event=event)
        if submitted.status == PartialOrderStatus.ACCEPTED:
            self._intent[submitted.id] = "ENTRY"
        return submitted

    def submit_exit(
        self,
        order_id: str,
        quantity: Optional[float] = None,
        *,
        type: str = "MARKET",
        limit_price=None,
        stop_price=None,
        tif: str = "GTC",
        oco=None,
        origin: str = "PARTIAL_EXIT",
        signal_time=None,
        client_order_id=None,
        event=None,
    ) -> PartialFillOrder:
        if self.ledger.position == 0:
            raise PartialExecutionError("cannot submit exit while flat", "EXIT_WHILE_FLAT")
        if self._active_intent("EXIT"):
            raise PartialExecutionError("only one active exit order is allowed in Step 5-7", "MULTIPLE_EXIT_ORDERS_UNSUPPORTED")
        requested = self.ledger.quantity if quantity is None else float(quantity)
        if requested <= 0 or requested > self.ledger.quantity + _EPS:
            raise PartialExecutionError(
                f"exit quantity must be within current position: {requested} / {self.ledger.quantity}",
                "BAD_EXIT_QUANTITY",
            )
        side = "SELL" if self.ledger.position == 1 else "COVER"
        order = PartialFillOrder(
            id=str(order_id),
            side=side,
            quantity=requested,
            type=type,
            limit_price=limit_price,
            stop_price=stop_price,
            tif=tif,
            oco=oco,
            origin=origin,
            signal_time=None if signal_time is None else str(signal_time),
            client_order_id=client_order_id,
        )
        submitted = self.broker.submit(order, event=event)
        if submitted.status == PartialOrderStatus.ACCEPTED:
            self._intent[submitted.id] = "EXIT"
        return submitted

    def fill(self, order_id: str, price: float, quantity: float, *, event=None) -> dict:
        if order_id not in self.broker.orders:
            raise PartialExecutionError(f"unknown order: {order_id}", "UNKNOWN_ORDER")
        order = self.broker.orders[order_id]
        intent = self._intent.get(order_id)
        if intent is None:
            raise PartialExecutionError(f"order has no execution intent: {order_id}", "ORDER_INTENT_MISSING")
        fill_qty = float(quantity)
        if intent == "ENTRY":
            self.ledger.validate_entry_fill(order.id, order.side, fill_qty)
        elif intent == "EXIT":
            self.ledger.validate_exit_fill(order.side, fill_qty)
        else:
            raise PartialExecutionError(f"unsupported order intent: {intent}", "BAD_ORDER_INTENT")

        record = self.broker.fill(order_id, price, fill_qty, event=event)
        if intent == "ENTRY":
            accounting = self.ledger.apply_entry_fill(
                order.id, order.side, record.price, record.quantity, event=event
            )
            realized = None
        else:
            realized_slice = self.ledger.apply_exit_fill(
                order.id, order.side, record.price, record.quantity, event=event
            )
            accounting = realized_slice.public_dict()
            realized = accounting
        return {
            "fill": record.public_dict(),
            "intent": intent,
            "accounting": accounting,
            "realized": realized,
            "position": self.ledger.position_snapshot(),
        }

    def cancel(self, order_id: str, reason: str = "user canceled", *, event=None) -> PartialFillOrder:
        return self.broker.cancel(order_id, reason=reason, event=event)

    @staticmethod
    def intrabar_fill_event(result: dict) -> dict:
        """Return the exact event payload expected by IntrabarStateSession.on_fill.

        The caller decides whether/how to apply the event.  Execution facts are
        authoritative and are never rolled back merely because a strategy state
        handler rejects its own provisional mutation.
        """
        fill = dict(result["fill"])
        return {
            "price": fill["price"],
            "quantity": fill["quantity"],
            "side": fill["side"],
            "order_id": fill["order_id"],
            "time": "" if fill.get("event") is None else str(fill["event"]),
        }

    def snapshot(self) -> dict:
        return {
            "orders": self.broker.snapshot_orders(),
            "broker_history": self.broker.snapshot_history(),
            "position": self.ledger.position_snapshot(),
            "realized_exits": [item.public_dict() for item in self.ledger.realized_exits],
        }
