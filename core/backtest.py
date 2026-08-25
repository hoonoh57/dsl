from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import numpy as np

from core.dsl_runtime import DSLRuntime
from core.broker import BrokerEmulator, BrokerOrder


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

    def validate(self):
        if self.total_capital <= 0: raise ValueError("총 자금은 0보다 커야 합니다.")
        if not 0 < self.allocation_pct <= 100: raise ValueError("투입 비율은 0 초과 100 이하여야 합니다.")
        for name in ("stop_loss_pct", "take_profit_pct", "trailing_activation_pct", "trailing_distance_pct"):
            if getattr(self, name) < 0: raise ValueError(f"{name}은 음수일 수 없습니다.")
        if self.signal_mode not in {"bar_close", "next_open"}:
            raise ValueError("signal_mode는 bar_close 또는 next_open이어야 합니다.")


def synthetic_market(bars_count=200):
    np.random.seed(42)
    base_time = datetime.now() - timedelta(days=bars_count)
    times = [(base_time + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(bars_count)]
    close = 1000.0 + np.cumsum(np.random.randn(bars_count) * 12)
    high = close + np.random.rand(bars_count) * 8
    low = close - np.random.rand(bars_count) * 8
    open_ = (high + low) / 2.0
    volume = np.random.randint(10_000, 100_000, bars_count).astype(float)
    return {"time": times, "open": open_, "high": high, "low": low, "close": close, "volume": volume}


class BacktestEngine:
    @staticmethod
    def run(dsl_code: str, bars_count: int = 200, initial_capital: Optional[float] = None,
            settings: Optional[Dict] = None, market: Optional[Dict] = None):
        config = StrategySettings(**(settings or {}))
        if initial_capital is not None: config.total_capital = float(initial_capital)
        config.validate()
        data = market or synthetic_market(bars_count)
        def chart_time(value):
            """Convert Kiwoom YYYYMMDD[HHMMSS] into Lightweight Charts time."""
            text = ''.join(ch for ch in str(value) if ch.isdigit())
            if len(text) >= 14:
                # Lightweight Charts renders timestamps as UTC. Treat the market
                # clock components as UTC so the label remains the supplied KST time.
                parsed = datetime.strptime(text[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                return int(parsed.timestamp())
            if len(text) >= 8:
                return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
            return str(value)
        numeric = {key: np.asarray(data[key], dtype=float) for key in ("open", "high", "low", "close", "volume")}
        digits = [''.join(ch for ch in str(value) if ch.isdigit()) for value in data["time"]]
        numeric["date"] = np.asarray([float(value[:8] or index) for index, value in enumerate(digits)])
        numeric["time"] = np.asarray([float(value[8:14] or 0) for value in digits])
        compiled = DSLRuntime.compile(dsl_code, numeric)
        size = len(numeric["close"])
        long_entry = np.zeros(size, dtype=bool)
        long_exit = np.zeros(size, dtype=bool)
        short_entry = np.zeros(size, dtype=bool)
        short_exit = np.zeros(size, dtype=bool)
        deferred_orders=[]
        if compiled.events:
            for event in compiled.events:
                market_commands=set()
                for order in event.orders:
                    order_type=str(order.arguments.get("type","MARKET")).upper()
                    if order_type=="MARKET":market_commands.add(order.command)
                    else:deferred_orders.append((event.condition,order))
                commands = market_commands
                if "order.buy" in commands: long_entry |= event.condition
                if "order.sell_short" in commands: short_entry |= event.condition
                if "order.close_long" in commands or "order.close_position" in commands:
                    long_exit |= event.condition
                if "order.close_short" in commands or "order.close_position" in commands:
                    short_exit |= event.condition
        else:
            # Indicator/signal artifacts may intentionally have no order block.
            long_entry = compiled.signal("long_entry", size) | compiled.signal("entry_cond", size)
            long_exit = compiled.signal("long_exit", size) | compiled.signal("exit_cond", size)
            short_entry = compiled.signal("short_entry", size)
            short_exit = compiled.signal("short_exit", size)

        cash = config.total_capital
        position, quantity, entry_price, peak_price = 0, 0.0, 0.0, 0.0
        trade_count = closed_trade_count = win_count = 0
        equity_curve, markers, trades = [], [], []
        broker=BrokerEmulator();order_sequence=0

        def close_position(i: int, price: float, reason: str):
            nonlocal cash, position, quantity, entry_price, peak_price, win_count, closed_trade_count
            price *= 1.0 - (config.slippage_pct / 100.0 * position)
            gross = quantity * (price - entry_price) * position
            exit_cost_pct = config.commission_pct + (config.sell_tax_pct if position == 1 else 0.0)
            fees = quantity * price * exit_cost_pct / 100.0
            cash += quantity * entry_price + gross - fees
            closed_trade_count += 1
            if gross - fees > 0: win_count += 1
            side = "SELL" if position == 1 else "COVER"
            markers.append({"time": chart_time(data["time"][i]), "position": "aboveBar", "color": "#ef5350", "shape": "arrowDown", "text": f"{side} @ {price:.1f}"})
            trades.append({"time": data["time"][i], "side": side, "price": price, "pnl": gross - fees, "reason": reason})
            position, quantity, entry_price, peak_price = 0, 0.0, 0.0, 0.0

        def open_position(i:int, side:int, price:float, reason="STRATEGY_SIGNAL"):
            nonlocal cash,position,quantity,entry_price,peak_price,trade_count
            position=side
            budget=min(cash,config.total_capital*config.allocation_pct/100.0)
            entry_price=float(price)*(1+config.slippage_pct/100.0*position)
            quantity=budget/entry_price
            entry_cost_pct=config.commission_pct+(config.sell_tax_pct if position==-1 else 0.0)
            cash-=budget+budget*entry_cost_pct/100.0;peak_price=entry_price;trade_count+=1
            label="BUY" if position==1 else "SHORT"
            markers.append({"time":chart_time(data["time"][i]),"position":"belowBar","color":"#26a69a","shape":"arrowUp","text":f"{label} @ {entry_price:.1f}"})
            trades.append({"time":data["time"][i],"side":label,"price":entry_price,"reason":reason})

        for i in range(size):
            price, bar_high, bar_low = numeric["close"][i], numeric["high"][i], numeric["low"][i]
            closed_this_bar = False
            pending_fills=broker.process_bar(numeric["open"][i],bar_high,bar_low,price)
            if position==0 and pending_fills:
                fill=pending_fills[0];open_position(i,1 if fill.side=="BUY" else -1,fill.fill_price,"PENDING_ORDER_FILL")
            if position:
                peak_price = max(peak_price, bar_high) if position == 1 else min(peak_price, bar_low)
                pnl_pct = ((price / entry_price) - 1.0) * 100.0 * position
                reason, exit_price = None, price
                stop_price = entry_price * (1.0 - config.stop_loss_pct / 100.0 * position)
                target_price = entry_price * (1.0 + config.take_profit_pct / 100.0 * position)
                stop_hit = config.stop_loss_pct and (bar_low <= stop_price if position == 1 else bar_high >= stop_price)
                target_hit = config.take_profit_pct and (bar_high >= target_price if position == 1 else bar_low <= target_price)
                # If OHLC cannot reveal which threshold was reached first, use
                # the conservative stop-first assumption.
                if stop_hit: reason, exit_price = "STOP_LOSS", stop_price
                elif target_hit: reason, exit_price = "TAKE_PROFIT", target_price
                elif config.trailing_enabled and config.trailing_distance_pct:
                    peak_gain = ((peak_price / entry_price) - 1.0) * 100.0 * position
                    retrace = ((price / peak_price) - 1.0) * 100.0 * position
                    if peak_gain >= config.trailing_activation_pct and retrace <= -config.trailing_distance_pct:
                        reason = "TRAILING_STOP"
                if reason or (position == 1 and long_exit[i]) or (position == -1 and short_exit[i]):
                    close_position(i, exit_price, reason or "STRATEGY_SIGNAL")
                    closed_this_bar = True

            signal_index = i - 1 if config.signal_mode == "next_open" else i
            fill_price = numeric["open"][i] if config.signal_mode == "next_open" else price
            may_enter = signal_index >= 0 and not closed_this_bar
            enter_long = may_enter and long_entry[signal_index]
            enter_short = may_enter and short_entry[signal_index]
            if position == 0 and (enter_long or enter_short):
                open_position(i,1 if enter_long else -1,fill_price)
            if position==0:
                for condition,order in deferred_orders:
                    if not condition[i]:continue
                    def at(value):return float(value[i]) if isinstance(value,np.ndarray) else value
                    order_sequence+=1
                    args=order.arguments
                    broker.submit(BrokerOrder(str(args.get("id",f"dsl-{order_sequence}")),
                        "BUY" if order.command=="order.buy" else "SELL_SHORT",str(args.get("type","MARKET")),
                        float(at(args.get("quantity",1))),at(args.get("limit")) if "limit" in args else None,
                        at(args.get("stop")) if "stop" in args else None,str(args.get("tif","GTC")),str(args.get("oco")) if "oco" in args else None))
            unrealized = quantity * (price - entry_price) * position if position else 0.0
            equity_curve.append(cash + (quantity * entry_price if position else 0.0) + unrealized)

        final_equity = equity_curve[-1]
        equity_arr = np.asarray(equity_curve)
        peak = np.maximum.accumulate(equity_arr)
        drawdown = np.divide(equity_arr - peak, peak, out=np.zeros_like(equity_arr), where=peak != 0)
        metrics = {
            "initial_capital": f"{config.total_capital:,.0f}원", "final_equity": f"{final_equity:,.0f}원",
            "total_return": f"{((final_equity/config.total_capital)-1)*100:+.2f}%",
            "trade_count": f"{trade_count}회", "closed_trade_count": f"{closed_trade_count}회",
            "win_rate": f"{(win_count/closed_trade_count*100 if closed_trade_count else 0):.1f}%",
            "mdd": f"{np.min(drawdown)*100:.2f}%",
        }
        candles = [{"time": chart_time(data["time"][i]), **{key: float(numeric[key][i]) for key in ("open", "high", "low", "close")}} for i in range(size)]
        def trend_colors(name, value):
            """Read the colour state cached while the indicator was calculated."""
            directions = getattr(value, "trend_colors", None)
            return directions if isinstance(directions, np.ndarray) and len(directions) == size else None
        def plot(name):
            value = compiled.values.get(name)
            if not isinstance(value, np.ndarray): return []
            directions = trend_colors(name, value)
            points = []
            for i in range(size):
                if not np.isfinite(value[i]):
                    continue
                point = {"time": chart_time(data["time"][i]), "value": float(value[i])}
                if directions is not None:
                    point["color"] = "#10b981" if directions[i] >= 0 else "#ef5350"
                points.append(point)
            return points
        reserved = {"open", "high", "low", "close", "volume", "amount", "open_interest", "date", "time",
                    "long_entry", "long_exit", "short_entry", "short_exit", "entry_cond", "exit_cond"}
        indicators, fingerprints = [], set()
        for name, value in compiled.values.items():
            if name in reserved or not isinstance(value, np.ndarray) or value.dtype == bool:
                continue
            finite = np.asarray(value, dtype=float)
            # Entry/exit tabs often repeat the same indicator declarations.
            fingerprint = np.nan_to_num(finite, nan=9.87654321e307).tobytes()
            if fingerprint in fingerprints:
                continue
            fingerprints.add(fingerprint)
            points = plot(name)
            if points:
                price_median = float(np.nanmedian(numeric["close"]))
                value_median = float(np.nanmedian(np.abs(finite[np.isfinite(finite)])))
                overlay = price_median == 0 or 0.2 <= value_median / abs(price_median) <= 5.0
                direction_colored = trend_colors(name, value) is not None
                indicators.append({"name": name, "data": points, "overlay": overlay,
                                   "direction_colored": direction_colored,
                                   "up_color": "#10b981", "down_color": "#ef5350"})
        signal_counts={name:int(np.count_nonzero(value)) for name,value in compiled.values.items()
                       if isinstance(value,np.ndarray) and value.dtype==bool}
        signal_counts.update({"__long_entry":int(np.count_nonzero(long_entry)),"__long_exit":int(np.count_nonzero(long_exit)),
                              "__short_entry":int(np.count_nonzero(short_entry)),"__short_exit":int(np.count_nonzero(short_exit))})
        return {"candles": candles, "ma5": plot("ma_fast"), "ma20": plot("ma_slow"),
                "bb_upper": [], "bb_lower": [], "markers": markers, "trades": trades,
                "indicators": indicators,
                "metrics": metrics, "strategy": {"name": compiled.name, "timeframe": compiled.timeframe},
                "settings": asdict(config),"diagnostics":{"bars":size,"signal_counts":signal_counts}}
