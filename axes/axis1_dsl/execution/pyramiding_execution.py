"""Deterministic same-direction pyramiding and multi-lot accounting for AXIS 1.

This Step 5-8 layer is additive. It reuses the Step 5-7 partial-fill broker but
keeps lot accounting separate from the migrated whole-fill batch engine.
Multiple entry orders may build one same-direction aggregate position. Each entry
order owns one lot; fills of the same order update that lot's weighted cost basis.
Exits consume lots deterministically (FIFO by default) or one explicitly named
lot. Opposite-direction hedging/netting is deliberately fail-closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional

from axes.axis1_dsl.execution.partial_execution import (
    PartialExecutionError,
    PartialFillBroker,
    PartialFillOrder,
    PartialOrderStatus,
)


_EPS = 1e-12


@dataclass
class PositionLot:
    lot_id: str
    entry_order_id: str
    position_side: int
    entry_sequence: int
    quantity: float = 0.0
    average_entry_price: float = 0.0
    entry_fee_remaining: float = 0.0
    cumulative_entry_quantity: float = 0.0

    @property
    def active(self) -> bool:
        return self.quantity > _EPS

    @property
    def direction(self) -> str:
        return "LONG" if self.position_side == 1 else "SHORT"

    def public_dict(self) -> dict:
        return {
            "lot_id": self.lot_id,
            "entry_order_id": self.entry_order_id,
            "direction": self.direction,
            "position_side": int(self.position_side),
            "entry_sequence": int(self.entry_sequence),
            "quantity": float(self.quantity),
            "average_entry_price": float(self.average_entry_price),
            "entry_fee_remaining": float(self.entry_fee_remaining),
            "cumulative_entry_quantity": float(self.cumulative_entry_quantity),
            "active": self.active,
        }


@dataclass(frozen=True)
class LotRealization:
    exit_order_id: str
    lot_id: str
    entry_order_id: str
    direction: str
    exit_side: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    allocated_entry_fee: float
    exit_fee: float
    net_pnl: float
    lot_remaining_quantity: float
    aggregate_remaining_quantity: float
    event: Optional[str] = None

    def public_dict(self) -> dict:
        return {
            "exit_order_id": self.exit_order_id,
            "lot_id": self.lot_id,
            "entry_order_id": self.entry_order_id,
            "direction": self.direction,
            "exit_side": self.exit_side,
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "quantity": float(self.quantity),
            "gross_pnl": float(self.gross_pnl),
            "allocated_entry_fee": float(self.allocated_entry_fee),
            "exit_fee": float(self.exit_fee),
            "net_pnl": float(self.net_pnl),
            "lot_remaining_quantity": float(self.lot_remaining_quantity),
            "aggregate_remaining_quantity": float(self.aggregate_remaining_quantity),
            "event": self.event,
        }


class PyramidingLedger:
    """Same-direction aggregate position composed from deterministic entry lots."""

    def __init__(
        self,
        *,
        initial_cash: float = 0.0,
        commission_pct: float = 0.0,
        sell_tax_pct: float = 0.0,
        max_lots: int = 4,
    ):
        self.cash = self._finite(initial_cash, "initial_cash")
        self.commission_pct = self._finite(commission_pct, "commission_pct", nonnegative=True)
        self.sell_tax_pct = self._finite(sell_tax_pct, "sell_tax_pct", nonnegative=True)
        if isinstance(max_lots, bool) or not isinstance(max_lots, int) or max_lots < 1:
            raise PartialExecutionError("max_lots must be an integer >= 1", "BAD_MAX_LOTS")
        self.max_lots = int(max_lots)
        self._lots: list[PositionLot] = []
        self._entry_order_to_lot: dict[str, PositionLot] = {}
        self._lot_sequence = 0
        self.realized_pnl = 0.0
        self.closed_cycle_count = 0
        self.realized_slices: list[LotRealization] = []
        self.audit: list[dict] = []

    @staticmethod
    def _finite(value, label: str, *, positive=False, nonnegative=False) -> float:
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

    def active_lots(self) -> tuple[PositionLot, ...]:
        return tuple(sorted((lot for lot in self._lots if lot.active), key=lambda item: item.entry_sequence))

    def lot(self, lot_id: str) -> PositionLot:
        identity = str(lot_id)
        for item in self._lots:
            if item.lot_id == identity:
                return item
        raise PartialExecutionError(f"unknown lot: {lot_id}", "UNKNOWN_LOT")

    def lot_for_entry_order(self, order_id: str) -> PositionLot | None:
        return self._entry_order_to_lot.get(str(order_id))

    @property
    def position(self) -> int:
        active = self.active_lots()
        if not active:
            return 0
        sides = {item.position_side for item in active}
        if len(sides) != 1:
            raise PartialExecutionError("mixed-direction active lots are forbidden", "MIXED_DIRECTION_LOTS")
        return int(active[0].position_side)

    @property
    def quantity(self) -> float:
        return float(sum(item.quantity for item in self.active_lots()))

    @property
    def average_entry_price(self) -> float:
        active = self.active_lots()
        total = sum(item.quantity for item in active)
        if total <= _EPS:
            return 0.0
        return float(sum(item.quantity * item.average_entry_price for item in active) / total)

    @property
    def entry_fee_remaining(self) -> float:
        return float(sum(item.entry_fee_remaining for item in self.active_lots()))

    def validate_entry_fill(self, order_id: str, side: str, quantity: float) -> None:
        order_identity = str(order_id)
        side_name = str(side).upper()
        if side_name not in {"BUY", "SELL_SHORT"}:
            raise PartialExecutionError(f"invalid entry side: {side}", "BAD_ENTRY_SIDE")
        self._finite(quantity, "entry fill quantity", positive=True)
        position_side = 1 if side_name == "BUY" else -1
        current_side = self.position
        if current_side and current_side != position_side:
            raise PartialExecutionError(
                "opposite-direction entry while exposure exists is not supported",
                "HEDGING_NOT_SUPPORTED",
            )
        existing = self._entry_order_to_lot.get(order_identity)
        if existing is not None and existing.position_side != position_side:
            raise PartialExecutionError("entry order direction changed", "ENTRY_DIRECTION_CHANGE")
        projected_active = len(self.active_lots())
        if existing is None or not existing.active:
            projected_active += 1
        if projected_active > self.max_lots:
            raise PartialExecutionError(
                f"pyramiding lot limit exceeded: {projected_active} > {self.max_lots}",
                "PYRAMIDING_LIMIT",
            )

    def apply_entry_fill(self, order_id: str, side: str, price: float, quantity: float, *, event=None) -> dict:
        self.validate_entry_fill(order_id, side, quantity)
        order_identity = str(order_id)
        side_name = str(side).upper()
        fill_price = self._finite(price, "entry fill price", positive=True)
        qty = self._finite(quantity, "entry fill quantity", positive=True)
        position_side = 1 if side_name == "BUY" else -1
        lot = self._entry_order_to_lot.get(order_identity)
        created = lot is None
        if lot is None:
            self._lot_sequence += 1
            lot = PositionLot(
                lot_id=f"lot-{self._lot_sequence}",
                entry_order_id=order_identity,
                position_side=position_side,
                entry_sequence=self._lot_sequence,
            )
            self._lots.append(lot)
            self._entry_order_to_lot[order_identity] = lot

        quantity_before = float(lot.quantity)
        new_quantity = quantity_before + qty
        weighted_cost = lot.average_entry_price * quantity_before + fill_price * qty
        fee = self._entry_fee(position_side, fill_price * qty)
        if position_side == 1:
            self.cash -= fill_price * qty + fee
        else:
            self.cash += fill_price * qty - fee
        lot.quantity = new_quantity
        lot.average_entry_price = weighted_cost / new_quantity
        lot.entry_fee_remaining += fee
        lot.cumulative_entry_quantity += qty
        row = {
            "kind": "ENTRY_FILL",
            "order_id": order_identity,
            "lot_id": lot.lot_id,
            "created_lot": created,
            "side": side_name,
            "price": fill_price,
            "quantity": qty,
            "lot_quantity": float(lot.quantity),
            "lot_average_entry_price": float(lot.average_entry_price),
            "aggregate_quantity": self.quantity,
            "aggregate_average_entry_price": self.average_entry_price,
            "active_lot_count": len(self.active_lots()),
            "fee": fee,
            "event": None if event is None else str(event),
        }
        self.audit.append(dict(row))
        return row

    def validate_exit_fill(self, side: str, quantity: float, *, lot_id: str | None = None) -> None:
        side_name = str(side).upper()
        qty = self._finite(quantity, "exit fill quantity", positive=True)
        current_side = self.position
        if current_side == 0:
            raise PartialExecutionError("cannot exit a flat position", "EXIT_WHILE_FLAT")
        expected = "SELL" if current_side == 1 else "COVER"
        if side_name != expected:
            raise PartialExecutionError(f"exit side must be {expected}", "BAD_EXIT_SIDE")
        available = self.quantity
        if lot_id is not None:
            lot = self.lot(lot_id)
            if not lot.active:
                raise PartialExecutionError(f"lot is not active: {lot_id}", "LOT_NOT_ACTIVE")
            if lot.position_side != current_side:
                raise PartialExecutionError("target lot direction mismatch", "LOT_DIRECTION_MISMATCH")
            available = float(lot.quantity)
        if qty > available + _EPS:
            code = "LOT_OVEREXIT" if lot_id is not None else "POSITION_OVEREXIT"
            raise PartialExecutionError(f"exit exceeds available quantity: {qty} > {available}", code)

    def apply_exit_fill(
        self,
        order_id: str,
        side: str,
        price: float,
        quantity: float,
        *,
        lot_id: str | None = None,
        event=None,
    ) -> tuple[LotRealization, ...]:
        self.validate_exit_fill(side, quantity, lot_id=lot_id)
        exit_order_id = str(order_id)
        side_name = str(side).upper()
        fill_price = self._finite(price, "exit fill price", positive=True)
        remaining_to_allocate = self._finite(quantity, "exit fill quantity", positive=True)
        cycle_was_open = self.position != 0
        candidates = (self.lot(lot_id),) if lot_id is not None else self.active_lots()
        realized: list[LotRealization] = []

        for lot in candidates:
            if remaining_to_allocate <= _EPS:
                break
            if not lot.active:
                continue
            allocation = min(float(lot.quantity), remaining_to_allocate)
            quantity_before = float(lot.quantity)
            entry_fee_alloc = lot.entry_fee_remaining * (allocation / quantity_before)
            notional = fill_price * allocation
            exit_fee = self._exit_fee(lot.position_side, notional)
            if lot.position_side == 1:
                self.cash += notional - exit_fee
                gross = allocation * (fill_price - lot.average_entry_price)
            else:
                self.cash -= notional + exit_fee
                gross = allocation * (lot.average_entry_price - fill_price)
            net = gross - entry_fee_alloc - exit_fee
            lot.quantity = max(0.0, quantity_before - allocation)
            lot.entry_fee_remaining = max(0.0, lot.entry_fee_remaining - entry_fee_alloc)
            if lot.quantity <= _EPS:
                lot.quantity = 0.0
                lot.entry_fee_remaining = 0.0
            self.realized_pnl += net
            remaining_to_allocate -= allocation
            if remaining_to_allocate <= _EPS:
                remaining_to_allocate = 0.0
            item = LotRealization(
                exit_order_id=exit_order_id,
                lot_id=lot.lot_id,
                entry_order_id=lot.entry_order_id,
                direction=lot.direction,
                exit_side=side_name,
                entry_price=float(lot.average_entry_price),
                exit_price=fill_price,
                quantity=allocation,
                gross_pnl=gross,
                allocated_entry_fee=entry_fee_alloc,
                exit_fee=exit_fee,
                net_pnl=net,
                lot_remaining_quantity=float(lot.quantity),
                aggregate_remaining_quantity=self.quantity,
                event=None if event is None else str(event),
            )
            self.realized_slices.append(item)
            realized.append(item)
            self.audit.append({"kind": "EXIT_ALLOCATION", **item.public_dict()})

        if remaining_to_allocate > _EPS:
            raise PartialExecutionError(
                f"exit allocation incomplete: {remaining_to_allocate}",
                "EXIT_ALLOCATION_DRIFT",
            )
        if cycle_was_open and self.position == 0:
            self.closed_cycle_count += 1
        return tuple(realized)

    def equity(self, mark_price: float) -> float:
        price = self._finite(mark_price, "mark_price", positive=True)
        side = self.position
        if side == 1:
            return self.cash + self.quantity * price
        if side == -1:
            return self.cash - self.quantity * price
        return self.cash

    def position_snapshot(self) -> dict:
        return {
            "position": self.position,
            "quantity": self.quantity,
            "average_entry_price": self.average_entry_price,
            "entry_fee_remaining": self.entry_fee_remaining,
            "active_lot_count": len(self.active_lots()),
            "max_lots": self.max_lots,
            "lots": tuple(item.public_dict() for item in sorted(self._lots, key=lambda lot: lot.entry_sequence)),
            "realized_pnl": float(self.realized_pnl),
            "closed_cycle_count": int(self.closed_cycle_count),
            "cash": float(self.cash),
        }


class PyramidingExecutionSession:
    """Partial-fill broker + deterministic same-direction multi-lot accounting."""

    def __init__(
        self,
        *,
        initial_cash: float = 0.0,
        commission_pct: float = 0.0,
        sell_tax_pct: float = 0.0,
        max_lots: int = 4,
    ):
        self.broker = PartialFillBroker()
        self.ledger = PyramidingLedger(
            initial_cash=initial_cash,
            commission_pct=commission_pct,
            sell_tax_pct=sell_tax_pct,
            max_lots=max_lots,
        )
        self._intent: dict[str, str] = {}
        self._exit_lot: dict[str, str | None] = {}

    def _active_intent(self, intent: str) -> list[PartialFillOrder]:
        return [
            order
            for order in self.broker.active_orders()
            if self._intent.get(order.id) == intent
        ]

    def _active_entry_direction(self) -> int:
        directions = {
            1 if order.side == "BUY" else -1
            for order in self._active_intent("ENTRY")
        }
        if len(directions) > 1:
            raise PartialExecutionError("mixed-direction active entry orders", "MIXED_ENTRY_DIRECTIONS")
        return next(iter(directions)) if directions else 0

    def _reserved_entry_slots(self) -> int:
        active_lot_ids = {lot.entry_order_id for lot in self.ledger.active_lots()}
        pending_without_active_lot = {
            order.id
            for order in self._active_intent("ENTRY")
            if order.id not in active_lot_ids
        }
        return len(self.ledger.active_lots()) + len(pending_without_active_lot)

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
        origin: str = "PYRAMID_ENTRY",
        signal_time=None,
        client_order_id=None,
        event=None,
    ) -> PartialFillOrder:
        side_name = str(side).upper()
        if side_name not in {"BUY", "SELL_SHORT"}:
            raise PartialExecutionError("entry side must be BUY or SELL_SHORT", "BAD_ENTRY_SIDE")
        requested_side = 1 if side_name == "BUY" else -1
        ledger_side = self.ledger.position
        active_order_side = self._active_entry_direction()
        if ledger_side and ledger_side != requested_side:
            raise PartialExecutionError("opposite-direction pyramiding is not supported", "HEDGING_NOT_SUPPORTED")
        if active_order_side and active_order_side != requested_side:
            raise PartialExecutionError("opposite-direction active entry order exists", "HEDGING_NOT_SUPPORTED")
        if self._reserved_entry_slots() >= self.ledger.max_lots:
            raise PartialExecutionError(
                f"pyramiding lot limit reached: {self.ledger.max_lots}",
                "PYRAMIDING_LIMIT",
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
        quantity: float | None = None,
        *,
        lot_id: str | None = None,
        type: str = "MARKET",
        limit_price=None,
        stop_price=None,
        tif: str = "GTC",
        oco=None,
        origin: str = "PYRAMID_EXIT",
        signal_time=None,
        client_order_id=None,
        event=None,
    ) -> PartialFillOrder:
        if self.ledger.position == 0:
            raise PartialExecutionError("cannot submit exit while flat", "EXIT_WHILE_FLAT")
        if self._active_intent("EXIT"):
            raise PartialExecutionError(
                "one active exit order at a time keeps lot allocation deterministic",
                "MULTIPLE_EXIT_ORDERS_UNSUPPORTED",
            )
        available = self.ledger.quantity
        target_lot = None
        if lot_id is not None:
            target_lot = self.ledger.lot(lot_id)
            if not target_lot.active:
                raise PartialExecutionError(f"lot is not active: {lot_id}", "LOT_NOT_ACTIVE")
            available = float(target_lot.quantity)
        requested = available if quantity is None else float(quantity)
        if not math.isfinite(requested) or requested <= 0 or requested > available + _EPS:
            code = "BAD_LOT_EXIT_QUANTITY" if lot_id is not None else "BAD_EXIT_QUANTITY"
            raise PartialExecutionError(
                f"exit quantity must be within available quantity: {requested} / {available}",
                code,
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
            self._exit_lot[submitted.id] = None if lot_id is None else str(lot_id)
        return submitted

    def fill(self, order_id: str, price: float, quantity: float, *, event=None) -> dict:
        identity = str(order_id)
        if identity not in self.broker.orders:
            raise PartialExecutionError(f"unknown order: {identity}", "UNKNOWN_ORDER")
        order = self.broker.orders[identity]
        intent = self._intent.get(identity)
        if intent is None:
            raise PartialExecutionError(f"order has no execution intent: {identity}", "ORDER_INTENT_MISSING")
        fill_qty = float(quantity)
        if intent == "ENTRY":
            self.ledger.validate_entry_fill(order.id, order.side, fill_qty)
        elif intent == "EXIT":
            self.ledger.validate_exit_fill(order.side, fill_qty, lot_id=self._exit_lot.get(identity))
        else:
            raise PartialExecutionError(f"unsupported order intent: {intent}", "BAD_ORDER_INTENT")

        fill = self.broker.fill(identity, price, fill_qty, event=event)
        if intent == "ENTRY":
            accounting = self.ledger.apply_entry_fill(
                order.id, order.side, fill.price, fill.quantity, event=event
            )
            realized: list[dict] = []
        else:
            allocations = self.ledger.apply_exit_fill(
                order.id,
                order.side,
                fill.price,
                fill.quantity,
                lot_id=self._exit_lot.get(identity),
                event=event,
            )
            realized = [item.public_dict() for item in allocations]
            accounting = {
                "allocation_count": len(realized),
                "allocations": realized,
                "realized_net_pnl": float(sum(item["net_pnl"] for item in realized)),
            }
        return {
            "fill": fill.public_dict(),
            "intent": intent,
            "accounting": accounting,
            "realized": realized,
            "position": self.ledger.position_snapshot(),
        }

    def cancel(self, order_id: str, reason: str = "user canceled", *, event=None) -> PartialFillOrder:
        return self.broker.cancel(str(order_id), reason=reason, event=event)

    @staticmethod
    def intrabar_fill_event(result: dict) -> dict:
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
            "realized_slices": tuple(item.public_dict() for item in self.ledger.realized_slices),
        }
