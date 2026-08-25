"""Safe, vectorised interpreter for the local strategy DSL."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Dict

import numpy as np

from core.indicators import CoreTALib
from core.dsl_parser import DSLParseError, DSLParser
from core.dsl_semantic import DSLSemanticAnalyzer, DSLSemanticError
from core.state import CoreStateLib
from core.bar_runtime import BarRuntimeError, execute_on_bar
from core.multitimeframe import MultiTimeframeContext


class DSLRuntimeError(ValueError):
    pass


def _series(value, size: int):
    if isinstance(value, np.ndarray): return value
    return np.full(size, value)


class ExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, values: Dict[str, object], size: int):
        self.values, self.size = values, size
        def session_current(field, operation):
            source, dates = np.asarray(values[field], float), np.asarray(values["date"])
            out = np.full(size, np.nan); current_date = None; current = np.nan
            for i in range(size):
                if dates[i] != current_date: current_date, current = dates[i], source[i]
                elif operation == "high": current = max(current, source[i])
                elif operation == "low": current = min(current, source[i])
                out[i] = current
            return out
        def session_previous(field, operation):
            source, dates = np.asarray(values[field], float), np.asarray(values["date"])
            out = np.full(size, np.nan); previous = np.nan; current_date = None; aggregate = np.nan
            for i in range(size):
                if dates[i] != current_date:
                    if current_date is not None: previous = aggregate
                    current_date, aggregate = dates[i], source[i]
                elif operation == "high": aggregate = max(aggregate, source[i])
                elif operation == "low": aggregate = min(aggregate, source[i])
                elif operation == "close": aggregate = source[i]
                out[i] = previous
            return out
        def offset(fn):
            return lambda series, period, bars=0: CoreTALib.shift(fn(series, period), int(bars))
        def sum_fn(series, period=None, bars=0):
            result = np.cumsum(np.nan_to_num(series)) if period is None else CoreTALib.rolling_sum(series, period)
            return CoreTALib.shift(result, int(bars))
        self.functions = {
            "ta.sma": offset(CoreTALib.sma), "ta.ema": offset(CoreTALib.ema), "ta.wma": offset(CoreTALib.wma),
            "ta.rma": offset(CoreTALib.rma),
            "ta.ma": lambda series, period, method="simple", bars=0: CoreTALib.shift(CoreTALib.ma(series, period, method), int(bars)),
            "ta.rsi": lambda *args: CoreTALib.rsi(values["close"], args[0]) if len(args) == 1 else CoreTALib.rsi(args[0], args[1]),
            "ta.crossover": CoreTALib.crossover,
            "ta.crossunder": CoreTALib.crossunder, "ta.highest": offset(CoreTALib.highest),
            "ta.lowest": offset(CoreTALib.lowest), "ta.sum": sum_fn,
            "ta.stdev": offset(CoreTALib.stdev), "ta.roc": CoreTALib.roc,
            "ta.jma": lambda *args: (CoreTALib.jma(values["close"], *args) if len(args) <= 3 else CoreTALib.jma(*args)),
            "ta.supertrend": lambda period=10, multiplier=3.0: CoreTALib.supertrend(
                values["high"], values["low"], values["close"], period, multiplier)[0],
            "ta.supertrend_direction": lambda period=10, multiplier=3.0: CoreTALib.supertrend(
                values["high"], values["low"], values["close"], period, multiplier)[1],
            "ta.macd": CoreTALib.macd,
            "ta.atr": lambda period=14: CoreTALib.atr(values["high"], values["low"], values["close"], period),
            "ta.adx": lambda period=14: CoreTALib.adx(values["high"], values["low"], values["close"], period),
            "ta.trix": lambda period=12: CoreTALib.trix(values["close"], period),
            "ta.cci": lambda period=20: CoreTALib.cci(values["high"], values["low"], values["close"], period),
            "ta.nrange": lambda period: CoreTALib.nrange(values["high"], values["low"], period),
            "ta.williams_r": lambda period: CoreTALib.williams_r(values["high"], values["low"], values["close"], period),
            "ta.abs_range": lambda period: CoreTALib.abs_range(values["close"], period),
            "ta.sum_abs_r": lambda period: CoreTALib.sum_abs_r(values["close"], period),
            "ta.vhf": lambda period: CoreTALib.vhf(values["close"], period),
            "ta.shift": CoreTALib.shift, "ta.count_since": CoreTALib.count_since,
            "ta.bars_since": CoreTALib.bars_since, "ta.highest_since": CoreTALib.highest_since,
            "ta.lowest_since": CoreTALib.lowest_since, "ta.value_when": CoreTALib.value_when,
            "logic.ifelse": np.where,
            "math.pow": np.power, "math.log": np.log, "math.log10": np.log10, "math.abs": np.abs,
            "math.sqrt": np.sqrt, "math.sin": np.sin, "math.cos": np.cos, "math.tan": np.tan,
            "math.asin": np.arcsin, "math.acos": np.arccos, "math.atan": np.arctan,
            "math.max": np.maximum, "math.min": np.minimum,
            "session.day_open": lambda: session_current("open", "open"),
            "session.day_high": lambda: session_current("high", "high"),
            "session.day_low": lambda: session_current("low", "low"),
            "session.prev_open": lambda: session_previous("open", "open"),
            "session.prev_high": lambda: session_previous("high", "high"),
            "session.prev_low": lambda: session_previous("low", "low"),
            "session.prev_close": lambda: session_previous("close", "close"),
            "state.edge": CoreStateLib.edge, "state.falling_edge": CoreStateLib.falling_edge,
            "state.ready_after": CoreStateLib.ready_after, "state.hold": CoreStateLib.hold,
            "state.persist": CoreStateLib.persist, "state.latch": CoreStateLib.latch,
            "state.count": CoreStateLib.count, "state.regime": CoreStateLib.regime,
        }
        mtf = MultiTimeframeContext(values)
        self.functions.update({"mtf.open":mtf.open,"mtf.high":mtf.high,"mtf.low":mtf.low,
                               "mtf.close":mtf.close,"mtf.volume":mtf.volume,"mtf.sma":mtf.sma})

    def evaluate(self, expression: str):
        expression = re.sub(r"\btrue\b", "True", expression, flags=re.I)
        expression = re.sub(r"\bfalse\b", "False", expression, flags=re.I)
        try: return self.visit(ast.parse(expression, mode="eval").body)
        except DSLRuntimeError: raise
        except Exception as exc: raise DSLRuntimeError(f"수식 평가 실패: {expression}: {exc}") from exc

    def visit_Name(self, node):
        if node.id in self.values: return self.values[node.id]
        if node.id == "True": return True
        if node.id == "False": return False
        raise DSLRuntimeError(f"정의되지 않은 변수: {node.id}")

    def visit_Constant(self, node): return node.value
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name): return f"{node.value.id}.{node.attr}"
        raise DSLRuntimeError("허용되지 않은 속성 접근입니다.")

    def visit_Call(self, node):
        name = self.visit(node.func)
        if name not in self.functions: raise DSLRuntimeError(f"지원하지 않는 함수: {name}")
        args = [self.visit(arg) for arg in node.args]
        kwargs = {item.arg: self.visit(item.value) for item in node.keywords}
        return self.functions[name](*args, **kwargs)

    def visit_Subscript(self, node):
        value, offset = self.visit(node.value), self.visit(node.slice)
        if not isinstance(offset, int) or offset < 0: raise DSLRuntimeError("과거 참조는 0 이상의 정수여야 합니다.")
        return CoreTALib.shift(value, offset)

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.Not): return np.logical_not(value)
        if isinstance(node.op, ast.USub): return -value
        if isinstance(node.op, ast.UAdd): return value
        raise DSLRuntimeError("지원하지 않는 단항 연산자입니다.")

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        ops = {ast.Add: np.add, ast.Sub: np.subtract, ast.Mult: np.multiply,
               ast.Div: np.divide, ast.Mod: np.mod, ast.Pow: np.power}
        fn = ops.get(type(node.op))
        if not fn: raise DSLRuntimeError("지원하지 않는 산술 연산자입니다.")
        return fn(left, right)

    def visit_BoolOp(self, node):
        values = [self.visit(value) for value in node.values]
        fn = np.logical_and if isinstance(node.op, ast.And) else np.logical_or
        result = values[0]
        for value in values[1:]: result = fn(result, value)
        return result

    def visit_Compare(self, node):
        operators = {ast.Eq: np.equal, ast.NotEq: np.not_equal, ast.Gt: np.greater,
                     ast.GtE: np.greater_equal, ast.Lt: np.less, ast.LtE: np.less_equal}
        left, result = self.visit(node.left), True
        for op, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            fn = operators.get(type(op))
            if not fn: raise DSLRuntimeError("지원하지 않는 비교 연산자입니다.")
            result = np.logical_and(result, fn(left, right)); left = right
        return result

    def generic_visit(self, node):
        raise DSLRuntimeError(f"허용되지 않은 문법: {type(node).__name__}")


@dataclass
class CompiledOrder:
    command: str
    arguments: Dict[str, object]


@dataclass
class CompiledEvent:
    condition: np.ndarray
    orders: tuple[CompiledOrder, ...]
    line: int

    @property
    def commands(self): return tuple(order.command for order in self.orders)


@dataclass
class CompiledStrategy:
    name: str
    timeframe: str
    values: Dict[str, object]
    events: tuple[CompiledEvent, ...] = ()

    def signal(self, name: str, size: int) -> np.ndarray:
        return np.asarray(_series(self.values.get(name, False), size), dtype=bool)


class DSLRuntime:
    RESERVED = {"timeframe"}

    @staticmethod
    def compile(code: str, market: Dict[str, np.ndarray]) -> CompiledStrategy:
        try:
            document = DSLParser.parse(code)
            DSLSemanticAnalyzer.analyze(document)
        except (DSLParseError, DSLSemanticError) as exc:
            raise DSLRuntimeError(str(exc)) from exc
        size = len(market["close"])
        values: Dict[str, object] = dict(market)
        values.setdefault("amount", values["close"] * values["volume"])
        values.setdefault("open_interest", np.zeros(size))
        values.setdefault("date", np.arange(size, dtype=float))
        values.setdefault("time", np.arange(size, dtype=float))
        evaluator = ExpressionEvaluator(values, size)
        for assignment in document.assignments:
            try:
                values[assignment.name] = evaluator.evaluate(assignment.expression)
            except DSLRuntimeError as exc:
                raise DSLRuntimeError(
                    f"line {assignment.line}, column 1: {exc}; expression: {assignment.name} = {assignment.expression}"
                ) from exc
        if document.states or document.on_bar:
            try:
                execute_on_bar(values, document.states, document.on_bar, size)
            except (BarRuntimeError, ArithmeticError, ValueError) as exc:
                raise DSLRuntimeError(f"on_bar 실행 실패: {exc}") from exc
        events = []
        for event in document.events:
            try:
                raw_condition = evaluator.evaluate(event.condition)
                condition_value = np.asarray(_series(raw_condition, size))
                if condition_value.dtype != bool:
                    raise DSLRuntimeError("on 조건은 boolean 또는 boolean series여야 합니다.")
                condition = condition_value.astype(bool, copy=False)
            except DSLRuntimeError as exc:
                raise DSLRuntimeError(
                    f"line {event.line}, column 1: 이벤트 조건 오류: {exc}; expression: {event.condition}"
                ) from exc
            compiled_orders=[]
            for order in event.orders:
                call=ast.parse(f"f({order.arguments})",mode="eval").body
                arguments={item.arg:evaluator.visit(item.value) for item in call.keywords}
                compiled_orders.append(CompiledOrder(order.command,arguments))
            events.append(CompiledEvent(condition, tuple(compiled_orders), event.line))
        return CompiledStrategy(document.name, document.timeframe, values, tuple(events))
