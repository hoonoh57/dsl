from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Sequence

import numpy as np

from core.dsl_runtime import DSLRuntime
from core.broker import BrokerEmulator, BrokerOrder, OrderStatus
from core.backtest_parent_context import prepare_backtest_parent_context


@dataclass
class StrategySettings:
    total_capital: float = 10_000_000.0
    allocation_pct: float = 100.0
    signal_mode: str = "bar_close"
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    trailing_enabled: bool = False
    trailing_activation_pct: float = 0.0
    trailing_distance_pct: float = 0.0
    commission_pct: float = 0.015
    sell_tax_pct: float = 0.18
    slippage_pct: float = 0.0
    entry_start_time: int = 0
    entry_end_time: int = 240000
    max_entries_per_day: int = 0

    @staticmethod
    def _valid_hhmmss(value: int, *, allow_24: bool = False) -> bool:
        if allow_24 and value == 240000:
            return True
        if value < 0 or value > 235959:
            return False
        hh, remainder = divmod(int(value), 10000)
        mm, ss = divmod(remainder, 100)
        return 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59

    def validate(self):
        if self.total_capital <= 0:
            raise ValueError("총 자금은 0보다 커야 합니다.")
        if not 0 < self.allocation_pct <= 100:
            raise ValueError("투입 비율은 0 초과 100 이하여야 합니다.")
        for name in ("stop_loss_pct", "take_profit_pct", "trailing_activation_pct", "trailing_distance_pct"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name}은 음수일 수 없습니다.")
        for name in ("commission_pct", "sell_tax_pct", "slippage_pct"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name}은 음수일 수 없습니다.")
        if self.signal_mode not in {"bar_close", "next_open"}:
            raise ValueError("signal_mode는 bar_close 또는 next_open이어야 합니다.")
        if not isinstance(self.entry_start_time, int) or not self._valid_hhmmss(self.entry_start_time):
            raise ValueError("entry_start_time은 유효한 HHMMSS 정수여야 합니다.")
        if not isinstance(self.entry_end_time, int) or not self._valid_hhmmss(self.entry_end_time, allow_24=True):
            raise ValueError("entry_end_time은 유효한 HHMMSS 정수 또는 240000이어야 합니다.")
        if self.entry_start_time >= self.entry_end_time:
            raise ValueError("entry_start_time은 entry_end_time보다 빨라야 합니다.")
        if not isinstance(self.max_entries_per_day, int) or self.max_entries_per_day < 0:
            raise ValueError("max_entries_per_day는 0 이상의 정수여야 합니다.")


def synthetic_market(bars_count=200):
    """Deterministic synthetic fixture. Product data adapters must opt in explicitly."""
    np.random.seed(42)
    base_time = datetime(2020, 1, 1) + timedelta(days=max(0, 400 - bars_count))
    times = [(base_time + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(bars_count)]
    close = 1000.0 + np.cumsum(np.random.randn(bars_count) * 12)
    high = close + np.random.rand(bars_count) * 8
    low = close - np.random.rand(bars_count) * 8
    open_ = (high + low) / 2.0
    volume = np.random.randint(10_000, 100_000, bars_count).astype(float)
    return {
        "time": times,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "_meta": {"source": "synthetic_fixture", "timeframe": "1d"},
    }


def _validate_market(data: Dict):
    required = ("time", "open", "high", "low", "close", "volume")
    missing = [name for name in required if name not in data]
    if missing:
        raise ValueError(f"시장 데이터 필드 누락: {', '.join(missing)}")
    lengths = {name: len(data[name]) for name in required}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"시장 데이터 길이가 일치하지 않습니다: {lengths}")
    size = lengths["close"]
    if size < 2:
        raise ValueError("백테스트에는 최소 2개 봉이 필요합니다.")
    numeric = {key: np.asarray(data[key], dtype=float) for key in ("open", "high", "low", "close", "volume")}
    if not all(np.all(np.isfinite(value)) for value in numeric.values()):
        raise ValueError("OHLCV에 NaN/Infinity가 포함되어 있습니다.")
    if np.any(numeric["high"] < np.maximum(numeric["open"], numeric["close"])) or np.any(
        numeric["low"] > np.minimum(numeric["open"], numeric["close"])
    ):
        raise ValueError("OHLC 가격 관계가 올바르지 않습니다.")
    if np.any(numeric["high"] < numeric["low"]):
        raise ValueError("high < low 데이터가 있습니다.")
    text_times = [str(item) for item in data["time"]]
    if len(set(text_times)) != len(text_times):
        raise ValueError("중복 timestamp가 있습니다.")
    if any(text_times[i] >= text_times[i + 1] for i in range(len(text_times) - 1)):
        raise ValueError("시장 데이터 시간이 엄격한 오름차순이 아닙니다.")
    return numeric


class BacktestEngine:
    @staticmethod
    def run(
        dsl_code: str,
        bars_count: int = 200,
        initial_capital: Optional[float] = None,
        settings: Optional[Dict] = None,
        market: Optional[Dict] = None,
        data_timeframe: Optional[str] = None,
        entry_gate: Optional[Sequence[bool]] = None,
        parent_context_frame=None,
        parent_feature_registry=None,
    ):
        config = StrategySettings(**(settings or {}))
        if initial_capital is not None:
            config.total_capital = float(initial_capital)
        config.validate()
        data = market if market is not None else synthetic_market(bars_count)
        numeric = _validate_market(data)

        def chart_time(value):
            text = "".join(ch for ch in str(value) if ch.isdigit())
            if len(text) >= 14:
                parsed = datetime.strptime(text[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                return int(parsed.timestamp())
            if len(text) >= 8:
                return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
            return str(value)

        digits = ["".join(ch for ch in str(value) if ch.isdigit()) for value in data["time"]]
        numeric["date"] = np.asarray([float(value[:8] or index) for index, value in enumerate(digits)])
        numeric["time"] = np.asarray([float(value[8:14] or 0) for value in digits])
        context_binding, parent_context_diagnostics = prepare_backtest_parent_context(
            market=data,
            frame=parent_context_frame,
            registry=parent_feature_registry,
        )
        compiled = DSLRuntime.compile(
            dsl_code,
            numeric,
            context_binding=context_binding,
            target_times=data["time"] if context_binding is not None else None,
        )
        actual_timeframe = data_timeframe or (data.get("_meta") or {}).get("timeframe")
        if actual_timeframe and str(actual_timeframe) != str(compiled.timeframe):
            raise ValueError(
                f"DSL timeframe({compiled.timeframe})과 데이터 timeframe({actual_timeframe})이 일치하지 않습니다."
            )

        size = len(numeric["close"])
        if entry_gate is None:
            higher_layer_gate = np.ones(size, dtype=bool)
        else:
            higher_layer_gate = np.asarray(entry_gate, dtype=bool)
            if higher_layer_gate.ndim != 1 or len(higher_layer_gate) != size:
                raise ValueError(f"entry_gate 길이는 시장 데이터 bar 수와 같아야 합니다: {len(higher_layer_gate)} != {size}")
        long_entry = np.zeros(size, dtype=bool)
        long_exit = np.zeros(size, dtype=bool)
        short_entry = np.zeros(size, dtype=bool)
        short_exit = np.zeros(size, dtype=bool)
        deferred_orders = []
        cancel_orders = []
        if compiled.events:
            for event in compiled.events:
                market_commands = set()
                for order in event.orders:
                    if order.command == "order.cancel":
                        cancel_orders.append((event.condition, order))
                        continue
                    order_type = str(order.arguments.get("type", "MARKET")).upper()
                    if order_type == "MARKET":
                        market_commands.add(order.command)
                    else:
                        deferred_orders.append((event.condition, order))
                if "order.buy" in market_commands:
                    long_entry |= event.condition
                if "order.sell_short" in market_commands:
                    short_entry |= event.condition
                if "order.close_long" in market_commands or "order.close_position" in market_commands:
                    long_exit |= event.condition
                if "order.close_short" in market_commands or "order.close_position" in market_commands:
                    short_exit |= event.condition
        else:
            long_entry = compiled.signal("long_entry", size) | compiled.signal("entry_cond", size)
            long_exit = compiled.signal("long_exit", size) | compiled.signal("exit_cond", size)
            short_entry = compiled.signal("short_entry", size)
            short_exit = compiled.signal("short_exit", size)

        cash = float(config.total_capital)
        position = 0
        quantity = 0.0
        entry_price = 0.0
        entry_fee = 0.0
        peak_price = 0.0
        trough_price = 0.0
        open_trade = None
        trade_count = 0
        closed_trade_count = 0
        win_count = 0
        equity_curve = []
        markers = []
        executions = []
        closed_trades = []
        broker = BrokerEmulator()
        order_sequence = 0
        entries_by_date = {}
        rejection_counts = {
            "same_bar_reentry": 0,
            "position_occupied": 0,
            "broker_fill_while_occupied": 0,
            "broker_rejected": 0,
            "pending_canceled_position_occupied": 0,
            "pending_suppressed_position_occupied": 0,
            "higher_layer_gate_blocked": 0,
            "entry_time_blocked": 0,
            "entry_count_blocked": 0,
        }

        def next_order_id(prefix="bt"):
            nonlocal order_sequence
            order_sequence += 1
            return f"{prefix}-{order_sequence}"

        def entry_policy_reason(i: int):
            if not bool(higher_layer_gate[i]):
                return "higher_layer_gate_blocked"
            current_time = int(numeric["time"][i])
            if current_time < config.entry_start_time or current_time >= config.entry_end_time:
                return "entry_time_blocked"
            current_date = int(numeric["date"][i])
            if config.max_entries_per_day and entries_by_date.get(current_date, 0) >= config.max_entries_per_day:
                return "entry_count_blocked"
            return None

        def equity_at(price: float):
            if position == 1:
                return cash + quantity * price
            if position == -1:
                return cash - quantity * price
            return cash

        def entry_cost(side: int, notional: float):
            pct = config.commission_pct + (config.sell_tax_pct if side == -1 else 0.0)
            return notional * pct / 100.0

        def exit_cost(side: int, notional: float):
            pct = config.commission_pct + (config.sell_tax_pct if side == 1 else 0.0)
            return notional * pct / 100.0

        def entry_terms(i: int, side: int, raw_price: float):
            fill = float(raw_price) * (1.0 + config.slippage_pct / 100.0 * side)
            available_equity = max(0.0, equity_at(float(numeric["close"][i])))
            budget = min(available_equity, config.total_capital * config.allocation_pct / 100.0)
            if budget <= 0 or fill <= 0:
                return None
            qty = budget / fill
            fee = entry_cost(side, qty * fill)
            if side == 1 and cash < qty * fill + fee:
                qty = max(0.0, cash / (fill * (1.0 + config.commission_pct / 100.0)))
                fee = entry_cost(side, qty * fill)
            if qty <= 0:
                return None
            return fill, qty, fee

        def submit_market_order(side_name: str, qty: float, fill_price: float, *, signal_time, fill_time,
                                origin: str, reason: str):
            order = BrokerOrder(
                id=next_order_id("market"),
                side=side_name,
                type="MARKET",
                quantity=float(qty),
                tif="GTC",
                origin=origin,
                signal_time=str(signal_time),
            )
            submitted = broker.submit(order, event=str(signal_time))
            if submitted.status != OrderStatus.ACCEPTED:
                rejection_counts["broker_rejected"] += 1
                return None
            submitted.reason = str(reason)
            broker.fill(submitted.id, float(fill_price), quantity=float(qty), event=str(fill_time))
            return submitted

        def cancel_other_pending_entry_orders(except_order_id=None, event=None):
            for active in list(broker.active_orders()):
                if active.id == except_order_id:
                    continue
                if active.origin == "DSL_PENDING" and active.side in {"BUY", "SELL_SHORT"}:
                    broker.cancel(active.id, "position occupied", event=event)
                    rejection_counts["pending_canceled_position_occupied"] += 1

        def apply_cancel_orders(signal_index: int, event_index: int):
            if signal_index < 0:
                return
            for condition, order in cancel_orders:
                if not bool(condition[signal_index]):
                    continue
                broker.cancel_client_order(
                    str(order.arguments["id"]),
                    reason="DSL cancel",
                    event=str(data["time"][event_index]),
                )

        def update_excursion(bar_high: float, bar_low: float):
            nonlocal peak_price, trough_price, open_trade
            if not position or open_trade is None:
                return
            peak_price = max(peak_price, float(bar_high))
            trough_price = min(trough_price, float(bar_low))
            if position == 1:
                mfe = (peak_price / entry_price - 1.0) * 100.0
                mae = (trough_price / entry_price - 1.0) * 100.0
            else:
                mfe = (entry_price / trough_price - 1.0) * 100.0 if trough_price > 0 else 0.0
                mae = (entry_price / peak_price - 1.0) * 100.0 if peak_price > 0 else 0.0
            open_trade["mfe_pct"] = max(float(open_trade.get("mfe_pct", 0.0)), float(mfe))
            open_trade["mae_pct"] = min(float(open_trade.get("mae_pct", 0.0)), float(mae))

        def open_position(
            i: int,
            side: int,
            raw_price: float,
            reason="STRATEGY_SIGNAL",
            signal_index=None,
            broker_order: Optional[BrokerOrder] = None,
        ):
            nonlocal cash, position, quantity, entry_price, entry_fee, peak_price, trough_price, trade_count, open_trade
            if position:
                rejection_counts["position_occupied"] += 1
                return False
            policy_reason = entry_policy_reason(i)
            if policy_reason:
                rejection_counts[policy_reason] += 1
                return False
            signal_i = i if signal_index is None else int(signal_index)
            signal_time = data["time"][signal_i]
            fill_time = data["time"][i]
            if broker_order is None:
                terms = entry_terms(i, side, raw_price)
                if terms is None:
                    return False
                fill, qty, fee = terms
                broker_side = "BUY" if side == 1 else "SELL_SHORT"
                broker_order = submit_market_order(
                    broker_side,
                    qty,
                    fill,
                    signal_time=signal_time,
                    fill_time=fill_time,
                    origin="STRATEGY_MARKET",
                    reason=reason,
                )
                if broker_order is None:
                    return False
            else:
                if broker_order.status != OrderStatus.FILLED:
                    raise ValueError(f"accounting received non-filled broker order: {broker_order.id}")
                fill = float(broker_order.fill_price)
                qty = float(broker_order.quantity)
                fee = entry_cost(side, qty * fill)
                if broker_order.signal_time is not None:
                    signal_time = broker_order.signal_time
            if side == 1:
                cash -= qty * fill + fee
            else:
                cash += qty * fill - fee
            position = side
            quantity = qty
            entry_price = fill
            entry_fee = fee
            peak_price = fill
            trough_price = fill
            trade_count += 1
            current_date = int(numeric["date"][i])
            entries_by_date[current_date] = entries_by_date.get(current_date, 0) + 1
            label = "BUY" if side == 1 else "SHORT"
            marker_position = "belowBar" if side == 1 else "aboveBar"
            marker_shape = "arrowUp" if side == 1 else "arrowDown"
            markers.append({
                "time": chart_time(fill_time),
                "position": marker_position,
                "color": "#26a69a",
                "shape": marker_shape,
                "text": f"{label} @ {fill:.1f}",
            })
            execution = {
                "kind": "ENTRY",
                "order_id": broker_order.id,
                "time": fill_time,
                "signal_time": signal_time,
                "side": label,
                "price": fill,
                "quantity": qty,
                "fee": fee,
                "reason": reason,
                "origin": broker_order.origin,
            }
            executions.append(execution)
            open_trade = {
                "trade_id": trade_count,
                "entry_order_id": broker_order.id,
                "direction": "LONG" if side == 1 else "SHORT",
                "signal_time": signal_time,
                "entry_time": fill_time,
                "entry_index": i,
                "entry_price": fill,
                "entry_fee": fee,
                "quantity": qty,
                "entry_reason": reason,
                "mfe_pct": 0.0,
                "mae_pct": 0.0,
            }
            cancel_other_pending_entry_orders(except_order_id=broker_order.id, event=str(fill_time))
            return True

        def close_position(i: int, raw_price: float, reason: str, signal_index=None):
            nonlocal cash, position, quantity, entry_price, entry_fee, peak_price, trough_price
            nonlocal win_count, closed_trade_count, open_trade
            if not position or open_trade is None:
                return False
            side = position
            fill = float(raw_price) * (1.0 - config.slippage_pct / 100.0 * side)
            qty = float(quantity)
            signal_i = i if signal_index is None else int(signal_index)
            signal_time = data["time"][signal_i]
            fill_time = data["time"][i]
            broker_side = "SELL" if side == 1 else "COVER"
            origin = "STRATEGY_MARKET" if reason == "STRATEGY_SIGNAL" else "RISK_EXIT"
            broker_order = submit_market_order(
                broker_side,
                qty,
                fill,
                signal_time=signal_time,
                fill_time=fill_time,
                origin=origin,
                reason=reason,
            )
            if broker_order is None:
                return False
            notional = qty * fill
            fee = exit_cost(side, notional)
            if side == 1:
                cash += notional - fee
                gross = qty * (fill - entry_price)
                label = "SELL"
            else:
                cash -= notional + fee
                gross = qty * (entry_price - fill)
                label = "COVER"
            net = gross - entry_fee - fee
            closed_trade_count += 1
            if net > 0:
                win_count += 1
            markers.append({
                "time": chart_time(fill_time),
                "position": "aboveBar" if side == 1 else "belowBar",
                "color": "#ef5350",
                "shape": "arrowDown" if side == 1 else "arrowUp",
                "text": f"{label} @ {fill:.1f}",
            })
            executions.append({
                "kind": "EXIT",
                "order_id": broker_order.id,
                "time": fill_time,
                "signal_time": signal_time,
                "side": label,
                "price": fill,
                "quantity": qty,
                "fee": fee,
                "pnl": net,
                "reason": reason,
                "origin": broker_order.origin,
            })
            trade = dict(open_trade)
            trade.update({
                "exit_order_id": broker_order.id,
                "exit_signal_time": signal_time,
                "exit_time": fill_time,
                "exit_index": i,
                "exit_price": fill,
                "exit_fee": fee,
                "exit_reason": reason,
                "gross_pnl": gross,
                "net_pnl": net,
                "pnl": net,
                "return_pct": (net / max(1e-12, qty * entry_price + entry_fee)) * 100.0,
                "holding_bars": i - int(open_trade["entry_index"]) + 1,
            })
            closed_trades.append(trade)
            position = 0
            quantity = 0.0
            entry_price = 0.0
            entry_fee = 0.0
            peak_price = 0.0
            trough_price = 0.0
            open_trade = None
            return True

        def value_at(value, index):
            return float(value[index]) if isinstance(value, np.ndarray) else value

        def submit_deferred(signal_index: int, *, entry_blocked=False):
            if signal_index < 0:
                return
            for condition, order in deferred_orders:
                if not bool(condition[signal_index]):
                    continue
                if entry_blocked:
                    rejection_counts["same_bar_reentry"] += 1
                    continue
                if position != 0:
                    rejection_counts["pending_suppressed_position_occupied"] += 1
                    continue
                args = order.arguments
                side_name = "BUY" if order.command == "order.buy" else "SELL_SHORT"
                client_order_id = str(args.get("id")) if args.get("id") is not None else None
                submitted = broker.submit(
                    BrokerOrder(
                        id=next_order_id("pending"),
                        side=side_name,
                        type=str(args.get("type", "MARKET")),
                        quantity=1.0,
                        limit_price=value_at(args.get("limit"), signal_index) if "limit" in args else None,
                        stop_price=value_at(args.get("stop"), signal_index) if "stop" in args else None,
                        tif=str(args.get("tif", "GTC")),
                        oco=str(args.get("oco")) if args.get("oco") is not None else None,
                        origin="DSL_PENDING",
                        signal_time=str(data["time"][signal_index]),
                        client_order_id=client_order_id,
                    ),
                    event=str(data["time"][signal_index]),
                )
                if submitted.status == OrderStatus.REJECTED:
                    rejection_counts["broker_rejected"] += 1

        for i in range(size):
            price = float(numeric["close"][i])
            bar_open = float(numeric["open"][i])
            bar_high = float(numeric["high"][i])
            bar_low = float(numeric["low"][i])
            session_end = i == size - 1 or numeric["date"][i + 1] != numeric["date"][i]
            closed_this_bar = False
            prior_index = i - 1

            if position and config.signal_mode == "next_open" and prior_index >= 0:
                should_exit = (position == 1 and bool(long_exit[prior_index])) or (
                    position == -1 and bool(short_exit[prior_index])
                )
                if should_exit:
                    close_position(i, bar_open, "STRATEGY_SIGNAL", prior_index)
                    closed_this_bar = True

            if config.signal_mode == "next_open":
                apply_cancel_orders(prior_index, i)
                submit_deferred(prior_index, entry_blocked=closed_this_bar)

            matched_entry_reserved = False

            def pending_fill_resolver(order: BrokerOrder, raw_match_price: float):
                nonlocal matched_entry_reserved
                if order.origin != "DSL_PENDING":
                    return float(raw_match_price), float(order.quantity)
                if position != 0 or matched_entry_reserved:
                    broker.cancel(order.id, "position occupied", event=str(data["time"][i]))
                    rejection_counts["pending_canceled_position_occupied"] += 1
                    return None
                policy_reason = entry_policy_reason(i)
                if policy_reason:
                    broker.cancel(order.id, policy_reason, event=str(data["time"][i]))
                    rejection_counts[policy_reason] += 1
                    return None
                side = 1 if order.side == "BUY" else -1
                terms = entry_terms(i, side, raw_match_price)
                if terms is None:
                    broker.cancel(order.id, "insufficient capital", event=str(data["time"][i]))
                    rejection_counts["broker_rejected"] += 1
                    return None
                fill, qty, _fee = terms
                matched_entry_reserved = True
                return fill, qty

            pending_fills = broker.process_bar(
                bar_open,
                bar_high,
                bar_low,
                price,
                end_of_session=False,
                event=str(data["time"][i]),
                fill_resolver=pending_fill_resolver,
            )
            for filled_order in pending_fills:
                if filled_order.origin != "DSL_PENDING":
                    continue
                if position == 0:
                    open_position(
                        i,
                        1 if filled_order.side == "BUY" else -1,
                        float(filled_order.fill_price),
                        "PENDING_ORDER_FILL",
                        i,
                        broker_order=filled_order,
                    )
                else:
                    rejection_counts["broker_fill_while_occupied"] += 1

            if position:
                update_excursion(bar_high, bar_low)
                reason = None
                exit_price = price
                stop_price = entry_price * (1.0 - config.stop_loss_pct / 100.0 * position)
                target_price = entry_price * (1.0 + config.take_profit_pct / 100.0 * position)
                stop_hit = bool(config.stop_loss_pct) and (
                    bar_low <= stop_price if position == 1 else bar_high >= stop_price
                )
                target_hit = bool(config.take_profit_pct) and (
                    bar_high >= target_price if position == 1 else bar_low <= target_price
                )
                if stop_hit:
                    reason, exit_price = "STOP_LOSS", stop_price
                elif target_hit:
                    reason, exit_price = "TAKE_PROFIT", target_price
                elif config.trailing_enabled and config.trailing_distance_pct:
                    if position == 1:
                        peak_gain = (peak_price / entry_price - 1.0) * 100.0
                        trailing_price = peak_price * (1.0 - config.trailing_distance_pct / 100.0)
                        if peak_gain >= config.trailing_activation_pct and bar_low <= trailing_price:
                            reason, exit_price = "TRAILING_STOP", trailing_price
                    else:
                        peak_gain = (entry_price / trough_price - 1.0) * 100.0 if trough_price > 0 else 0.0
                        trailing_price = trough_price * (1.0 + config.trailing_distance_pct / 100.0)
                        if peak_gain >= config.trailing_activation_pct and bar_high >= trailing_price:
                            reason, exit_price = "TRAILING_STOP", trailing_price
                if reason:
                    close_position(i, exit_price, reason, i)
                    closed_this_bar = True
                elif config.signal_mode == "bar_close":
                    should_exit = (position == 1 and bool(long_exit[i])) or (
                        position == -1 and bool(short_exit[i])
                    )
                    if should_exit:
                        close_position(i, price, "STRATEGY_SIGNAL", i)
                        closed_this_bar = True

            signal_index = prior_index if config.signal_mode == "next_open" else i
            fill_price = bar_open if config.signal_mode == "next_open" else price
            may_enter = signal_index >= 0 and not closed_this_bar
            enter_long = bool(may_enter and long_entry[signal_index])
            enter_short = bool(may_enter and short_entry[signal_index])
            if position == 0 and (enter_long or enter_short):
                open_position(i, 1 if enter_long else -1, fill_price, "STRATEGY_SIGNAL", signal_index)
            elif closed_this_bar and signal_index >= 0 and (long_entry[signal_index] or short_entry[signal_index]):
                rejection_counts["same_bar_reentry"] += 1

            if config.signal_mode == "bar_close":
                apply_cancel_orders(i, i)
                submit_deferred(i, entry_blocked=closed_this_bar)

            if session_end:
                broker.expire_day_orders(event=str(data["time"][i]))

            equity_curve.append(equity_at(price))

        final_equity = float(equity_curve[-1])
        equity_arr = np.asarray(equity_curve, dtype=float)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = np.divide(equity_arr - peak, peak, out=np.zeros_like(equity_arr), where=peak != 0)
        gains = sum(max(0.0, float(item["net_pnl"])) for item in closed_trades)
        losses = abs(sum(min(0.0, float(item["net_pnl"])) for item in closed_trades))
        profit_factor = gains / losses if losses else (float("inf") if gains else 0.0)
        total_fees = sum(float(item.get("fee", 0.0) or 0.0) for item in executions)
        return_pct = ((final_equity / config.total_capital) - 1.0) * 100.0
        mdd_pct = float(np.min(drawdown) * 100.0)
        win_rate = win_count / closed_trade_count * 100.0 if closed_trade_count else 0.0
        metrics_numeric = {
            "initial_capital": float(config.total_capital),
            "final_equity": final_equity,
            "total_return_pct": return_pct,
            "trade_count": trade_count,
            "closed_trade_count": closed_trade_count,
            "win_rate_pct": win_rate,
            "mdd_pct": mdd_pct,
            "profit_factor": profit_factor,
            "gross_profit": gains,
            "gross_loss": losses,
            "total_cost": total_fees,
            "open_position": position,
        }
        metrics = {
            "initial_capital": f"{config.total_capital:,.0f}원",
            "final_equity": f"{final_equity:,.0f}원",
            "total_return": f"{return_pct:+.2f}%",
            "trade_count": f"{trade_count}회",
            "closed_trade_count": f"{closed_trade_count}회",
            "win_rate": f"{win_rate:.1f}%",
            "mdd": f"{mdd_pct:.2f}%",
            "profit_factor": "∞" if np.isinf(profit_factor) else f"{profit_factor:.3f}",
            "total_cost": f"{total_fees:,.2f}원",
        }

        candles = [
            {
                "time": chart_time(data["time"][i]),
                **{key: float(numeric[key][i]) for key in ("open", "high", "low", "close")},
            }
            for i in range(size)
        ]

        def trend_colors(name, value):
            directions = getattr(value, "trend_colors", None)
            return directions if isinstance(directions, np.ndarray) and len(directions) == size else None

        def plot(name):
            value = compiled.values.get(name)
            if not isinstance(value, np.ndarray):
                return []
            directions = trend_colors(name, value)
            points = []
            for i in range(size):
                try:
                    finite_value = float(value[i])
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(finite_value):
                    continue
                point = {"time": chart_time(data["time"][i]), "value": finite_value}
                if directions is not None:
                    point["color"] = "#10b981" if directions[i] >= 0 else "#ef5350"
                points.append(point)
            return points

        reserved = {
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "open_interest",
            "date",
            "time",
            "long_entry",
            "long_exit",
            "short_entry",
            "short_exit",
            "entry_cond",
            "exit_cond",
        }
        indicators, fingerprints = [], set()
        for name, value in compiled.values.items():
            if name in reserved or not isinstance(value, np.ndarray) or value.dtype == bool:
                continue
            try:
                finite = np.asarray(value, dtype=float)
            except (TypeError, ValueError):
                continue
            fingerprint = np.nan_to_num(finite, nan=9.87654321e307).tobytes()
            if fingerprint in fingerprints:
                continue
            fingerprints.add(fingerprint)
            points = plot(name)
            if points:
                price_median = float(np.nanmedian(numeric["close"]))
                valid_values = finite[np.isfinite(finite)]
                value_median = float(np.nanmedian(np.abs(valid_values))) if len(valid_values) else 0.0
                overlay = price_median == 0 or 0.2 <= value_median / abs(price_median) <= 5.0
                direction_colored = trend_colors(name, value) is not None
                indicators.append(
                    {
                        "name": name,
                        "data": points,
                        "overlay": overlay,
                        "direction_colored": direction_colored,
                        "up_color": "#10b981",
                        "down_color": "#ef5350",
                    }
                )

        signal_counts = {
            name: int(np.count_nonzero(value))
            for name, value in compiled.values.items()
            if isinstance(value, np.ndarray) and value.dtype == bool
        }
        signal_counts.update(
            {
                "__long_entry": int(np.count_nonzero(long_entry)),
                "__long_exit": int(np.count_nonzero(long_exit)),
                "__short_entry": int(np.count_nonzero(short_entry)),
                "__short_exit": int(np.count_nonzero(short_exit)),
            }
        )
        mfe_values = [float(item.get("mfe_pct", 0.0)) for item in closed_trades]
        mae_values = [float(item.get("mae_pct", 0.0)) for item in closed_trades]
        realized_values = [float(item.get("return_pct", 0.0)) for item in closed_trades]
        broker_history = broker.snapshot_history()
        diagnostics = {
            "bars": size,
            "signal_counts": signal_counts,
            "rejections": rejection_counts,
            "broker_history": broker_history,
            "strategy_market_order_history": [row for row in broker_history if row.get("origin") == "STRATEGY_MARKET"],
            "risk_exit_order_history": [row for row in broker_history if row.get("origin") == "RISK_EXIT"],
            "pending_order_history": [row for row in broker_history if row.get("origin") == "DSL_PENDING"],
            "closed_trade_count": closed_trade_count,
            "average_mfe_pct": float(np.mean(mfe_values)) if mfe_values else 0.0,
            "average_mae_pct": float(np.mean(mae_values)) if mae_values else 0.0,
            "average_realized_return_pct": float(np.mean(realized_values)) if realized_values else 0.0,
            "mfe_giveback_pct": (
                float(np.mean(mfe_values)) - float(np.mean(realized_values))
            ) if mfe_values else 0.0,
            "data_meta": dict(data.get("_meta") or {}),
            "execution_authority": "BrokerEmulator",
            "parent_context": parent_context_diagnostics,
            "entry_policy": {
                "entry_start_time": config.entry_start_time,
                "entry_end_time": config.entry_end_time,
                "max_entries_per_day": config.max_entries_per_day,
                "higher_layer_gate_supplied": entry_gate is not None,
            },
        }
        return {
            "candles": candles,
            "ma5": plot("ma_fast"),
            "ma20": plot("ma_slow"),
            "bb_upper": [],
            "bb_lower": [],
            "markers": markers,
            "trades": executions,
            "closed_trades": closed_trades,
            "indicators": indicators,
            "metrics": metrics,
            "metrics_numeric": metrics_numeric,
            "equity_curve": [
                {"time": chart_time(data["time"][i]), "value": float(equity_curve[i])}
                for i in range(size)
            ],
            "strategy": {"name": compiled.name, "timeframe": compiled.timeframe},
            "settings": asdict(config),
            "diagnostics": diagnostics,
        }
