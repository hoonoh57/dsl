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
from core.assignment_flow import partition_assignments
from core.state import CoreStateLib
from core.bar_runtime import BarRuntimeError, execute_on_bar
from core.multitimeframe import MultiTimeframeContext


class DSLRuntimeError(ValueError):
    pass


def _series(value, size: int):
    if isinstance(value, np.ndarray): return value
    return np.full(size, value)


def _finite_scalar(value, label: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise DSLRuntimeError(f"{label}은 유한한 숫자여야 합니다.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise DSLRuntimeError(f"{label}은 유한한 숫자여야 합니다.") from exc
    if not np.isfinite(number):
        raise DSLRuntimeError(f"{label}은 유한한 숫자여야 합니다.")
    return number


def _integer_at_least(value, minimum: int, label: str) -> int:
    number = _finite_scalar(value, label)
    if not number.is_integer() or number < minimum:
        raise DSLRuntimeError(f"{label}은 {minimum} 이상의 정수여야 합니다.")
    return int(number)


def _positive_period(value, label: str) -> int:
    return _integer_at_least(value, 1, label)


def _nonnegative_bars(value, label: str) -> int:
    return _integer_at_least(value, 0, label)


def _positive_number(value, label: str) -> float:
    number = _finite_scalar(value, label)
    if number <= 0:
        raise DSLRuntimeError(f"{label}은 0보다 커야 합니다.")
    return number


def _jma_phase(value) -> float:
    number = _finite_scalar(value, "ta.jma phase")
    if number < -100 or number > 100:
        raise DSLRuntimeError("ta.jma phase는 -100~100 범위여야 합니다.")
    return number


def _ma_method(value, label: str) -> str:
    method = str(value).strip().lower()
    allowed = {"simple", "단순", "exponential", "지수", "weighted", "가중"}
    if method not in allowed:
        raise DSLRuntimeError(f"{label}은 simple/exponential/weighted(단순/지수/가중) 중 하나여야 합니다.")
    return method


def _regime_initial(value) -> int:
    number = _finite_scalar(value, "state.regime initial")
    if not number.is_integer() or int(number) not in {-1, 0, 1}:
        raise DSLRuntimeError("state.regime initial은 -1, 0, 1 중 하나여야 합니다.")
    return int(number)


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

        def offset(fn, name):
            def apply(series, period, bars=0):
                safe_period = _positive_period(period, f"{name} period")
                safe_bars = _nonnegative_bars(bars, f"{name} bars")
                return CoreTALib.shift(fn(series, safe_period), safe_bars)
            return apply

        def ma_fn(series, period, method="simple", bars=0):
            safe_period = _positive_period(period, "ta.ma period")
            safe_method = _ma_method(method, "ta.ma method")
            safe_bars = _nonnegative_bars(bars, "ta.ma bars")
            return CoreTALib.shift(CoreTALib.ma(series, safe_period, safe_method), safe_bars)

        def rsi_fn(*args):
            if len(args) == 1:
                return CoreTALib.rsi(values["close"], _positive_period(args[0], "ta.rsi period"))
            return CoreTALib.rsi(args[0], _positive_period(args[1], "ta.rsi period"))

        def sum_fn(series, period=None, bars=0):
            safe_bars = _nonnegative_bars(bars, "ta.sum bars")
            result = np.cumsum(np.nan_to_num(series)) if period is None else CoreTALib.rolling_sum(
                series, _positive_period(period, "ta.sum period")
            )
            return CoreTALib.shift(result, safe_bars)

        def roc_fn(series, period):
            return CoreTALib.roc(series, _positive_period(period, "ta.roc period"))

        def jma_fn(*args):
            if len(args) == 3:
                series = values["close"]
                length, phase, power = args
            else:
                series, length, phase, power = args
            return CoreTALib.jma(
                series,
                _positive_period(length, "ta.jma length"),
                _jma_phase(phase),
                _positive_period(power, "ta.jma power"),
            )

        def supertrend_fn(period=10, multiplier=3.0, direction=False):
            result = CoreTALib.supertrend(
                values["high"], values["low"], values["close"],
                _positive_period(period, "ta.supertrend period"),
                _positive_number(multiplier, "ta.supertrend multiplier"),
            )
            return result[1] if direction else result[0]

        def macd_fn(series, short=12, long=26, method="exponential"):
            return CoreTALib.macd(
                series,
                _positive_period(short, "ta.macd short"),
                _positive_period(long, "ta.macd long"),
                _ma_method(method, "ta.macd method"),
            )

        def atr_fn(period=14):
            return CoreTALib.atr(values["high"], values["low"], values["close"], _positive_period(period, "ta.atr period"))

        def adx_fn(period=14):
            return CoreTALib.adx(values["high"], values["low"], values["close"], _positive_period(period, "ta.adx period"))

        def trix_fn(period=12):
            return CoreTALib.trix(values["close"], _positive_period(period, "ta.trix period"))

        def cci_fn(period=20):
            return CoreTALib.cci(values["high"], values["low"], values["close"], _positive_period(period, "ta.cci period"))

        def nrange_fn(period):
            return CoreTALib.nrange(values["high"], values["low"], _positive_period(period, "ta.nrange period"))

        def williams_r_fn(period):
            return CoreTALib.williams_r(
                values["high"], values["low"], values["close"], _positive_period(period, "ta.williams_r period")
            )

        def abs_range_fn(period):
            return CoreTALib.abs_range(values["close"], _positive_period(period, "ta.abs_range period"))

        def sum_abs_r_fn(period):
            return CoreTALib.sum_abs_r(values["close"], _positive_period(period, "ta.sum_abs_r period"))

        def vhf_fn(period):
            return CoreTALib.vhf(values["close"], _positive_period(period, "ta.vhf period"))

        def shift_fn(series, bars):
            return CoreTALib.shift(series, _nonnegative_bars(bars, "ta.shift bars"))

        def value_when_fn(occurrence, condition, series):
            return CoreTALib.value_when(_nonnegative_bars(occurrence, "ta.value_when occurrence"), condition, series)

        def ready_after_fn(trigger, bars):
            return CoreStateLib.ready_after(trigger, _nonnegative_bars(bars, "state.ready_after bars"))

        def hold_fn(condition, bars):
            return CoreStateLib.hold(condition, _nonnegative_bars(bars, "state.hold bars"))

        def persist_fn(condition, bars):
            return CoreStateLib.persist(condition, _positive_period(bars, "state.persist bars"))

        def regime_fn(bullish, bearish, initial=0):
            return CoreStateLib.regime(bullish, bearish, _regime_initial(initial))

        self.functions = {
            "ta.sma": offset(CoreTALib.sma, "ta.sma"),
            "ta.ema": offset(CoreTALib.ema, "ta.ema"),
            "ta.wma": offset(CoreTALib.wma, "ta.wma"),
            "ta.rma": offset(CoreTALib.rma, "ta.rma"),
            "ta.ma": ma_fn,
            "ta.rsi": rsi_fn,
            "ta.crossover": CoreTALib.crossover,
            "ta.crossunder": CoreTALib.crossunder,
            "ta.highest": offset(CoreTALib.highest, "ta.highest"),
            "ta.lowest": offset(CoreTALib.lowest, "ta.lowest"),
            "ta.sum": sum_fn,
            "ta.stdev": offset(CoreTALib.stdev, "ta.stdev"),
            "ta.roc": roc_fn,
            "ta.jma": jma_fn,
            "ta.supertrend": lambda period=10, multiplier=3.0: supertrend_fn(period, multiplier, False),
            "ta.supertrend_direction": lambda period=10, multiplier=3.0: supertrend_fn(period, multiplier, True),
            "ta.macd": macd_fn,
            "ta.atr": atr_fn,
            "ta.adx": adx_fn,
            "ta.trix": trix_fn,
            "ta.cci": cci_fn,
            "ta.nrange": nrange_fn,
            "ta.williams_r": williams_r_fn,
            "ta.abs_range": abs_range_fn,
            "ta.sum_abs_r": sum_abs_r_fn,
            "ta.vhf": vhf_fn,
            "ta.shift": shift_fn,
            "ta.count_since": CoreTALib.count_since,
            "ta.bars_since": CoreTALib.bars_since,
            "ta.highest_since": CoreTALib.highest_since,
            "ta.lowest_since": CoreTALib.lowest_since,
            "ta.value_when": value_when_fn,
            "logic.ifelse": np.where,
            "math.pow": np.power,
            "math.log": np.log,
            "math.log10": np.log10,
            "math.abs": np.abs,
            "math.sqrt": np.sqrt,
            "math.sin": np.sin,
            "math.cos": np.cos,
            "math.tan": np.tan,
            "math.asin": np.arcsin,
            "math.acos": np.arccos,
            "math.atan": np.arctan,
            "math.max": np.maximum,
            "math.min": np.minimum,
            "session.day_open": lambda: session_current("open", "open"),
            "session.day_high": lambda: session_current("high", "high"),
            "session.day_low": lambda: session_current("low", "low"),
            "session.prev_open": lambda: session_previous("open", "open"),
            "session.prev_high": lambda: session_previous("high", "high"),
            "session.prev_low": lambda: session_previous("low", "low"),
            "session.prev_close": lambda: session_previous("close", "close"),
            "state.edge": CoreStateLib.edge,
            "state.falling_edge": CoreStateLib.falling_edge,
            "state.ready_after": ready_after_fn,
            "state.hold": hold_fn,
            "state.persist": persist_fn,
            "state.latch": CoreStateLib.latch,
            "state.count": CoreStateLib.count,
            "state.regime": regime_fn,
        }
        mtf = MultiTimeframeContext(values)
        self.functions.update({
            "mtf.open": mtf.open,
            "mtf.high": mtf.high,
            "mtf.low": mtf.low,
            "mtf.close": mtf.close,
            "mtf.volume": mtf.volume,
            "mtf.sma": lambda timeframe, period: mtf.sma(timeframe, _positive_period(period, "mtf.sma period")),
        })

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
        before_bar, after_bar = partition_assignments(document)

        def evaluate_assignment(assignment):
            try:
                values[assignment.name] = evaluator.evaluate(assignment.expression)
            except DSLRuntimeError as exc:
                raise DSLRuntimeError(
                    f"line {assignment.line}, column 1: {exc}; expression: {assignment.name} = {assignment.expression}"
                ) from exc

        for assignment in before_bar:
            evaluate_assignment(assignment)

        if document.states or document.on_bar:
            try:
                execute_on_bar(values, document.states, document.on_bar, size)
            except (BarRuntimeError, ArithmeticError, ValueError) as exc:
                raise DSLRuntimeError(f"on_bar 실행 실패: {exc}") from exc

        for assignment in after_bar:
            evaluate_assignment(assignment)

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
