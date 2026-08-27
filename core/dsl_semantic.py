"""Static semantic and series-type analysis for Quant DSL."""
from __future__ import annotations
import ast
import re
from enum import Enum
from typing import Dict, Mapping
from core.dsl_parser import IfNode, SetNode, StrategyNode
from core.function_registry import FUNCTION_SPECS
from core.assignment_flow import collect_bar_output_names, partition_assignments


class ValueType(str, Enum):
    SCALAR_NUMBER = "scalar<number>"
    SCALAR_BOOL = "scalar<bool>"
    STRING = "string"
    SERIES_NUMBER = "series<number>"
    SERIES_BOOL = "series<bool>"
    SERIES_STRING = "series<string>"


class DSLSemanticError(ValueError):
    def __init__(self, message, line=1, column=1, code="SEMANTIC_ERROR"):
        self.line, self.column, self.code = line, column, code
        super().__init__(f"line {line}, column {column}: {message}")


def _series(value): return value in {ValueType.SERIES_NUMBER, ValueType.SERIES_BOOL, ValueType.SERIES_STRING}
def _boolean(value): return value in {ValueType.SCALAR_BOOL, ValueType.SERIES_BOOL}
def _number(value): return value in {ValueType.SCALAR_NUMBER, ValueType.SERIES_NUMBER}
def _string(value): return value in {ValueType.STRING, ValueType.SERIES_STRING}
def _scalar_number(value): return value == ValueType.SCALAR_NUMBER


def _attribute_parts(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return _attribute_parts(node.value) + [node.attr]
    return []


def _context_value_type(value_type: str) -> ValueType:
    kind = str(value_type).strip().upper()
    if kind == "NUMBER": return ValueType.SERIES_NUMBER
    if kind == "BOOLEAN": return ValueType.SERIES_BOOL
    if kind == "STRING": return ValueType.SERIES_STRING
    raise ValueError(f"지원하지 않는 parent context value_type: {value_type!r}")


RETURNS = {
    "scalar<number>": ValueType.SCALAR_NUMBER,
    "scalar<bool>": ValueType.SCALAR_BOOL,
    "series<number>": ValueType.SERIES_NUMBER,
    "series<bool>": ValueType.SERIES_BOOL,
    "string": ValueType.STRING,
}


class ExpressionTypeChecker(ast.NodeVisitor):
    def __init__(
        self,
        symbols: Dict[str, ValueType],
        line: int,
        allow_calls: bool = True,
        context_feature_types: Mapping[str, str] | None = None,
    ):
        self.symbols = symbols
        self.line = line
        self.allow_calls = allow_calls
        self.context_feature_types = dict(context_feature_types or {})

    def check(self, text):
        text = re.sub(r"\btrue\b", "True", text, flags=re.I)
        text = re.sub(r"\bfalse\b", "False", text, flags=re.I)
        return self.visit(ast.parse(text, mode="eval").body)

    def visit_Name(self, node):
        if node.id in self.symbols: return self.symbols[node.id]
        if node.id in {"True", "False"}: return ValueType.SCALAR_BOOL
        if node.id == "ctx":
            raise DSLSemanticError(
                "ctx는 단독 값이 아니라 ctx.<layer>.<feature> 형식으로만 사용할 수 있습니다.",
                self.line, node.col_offset + 1, "BAD_CONTEXT_REFERENCE"
            )
        raise DSLSemanticError(f"정의되지 않은 변수: {node.id}", self.line, node.col_offset + 1, "UNDEFINED_SYMBOL")

    def visit_Constant(self, node):
        if isinstance(node.value, bool): return ValueType.SCALAR_BOOL
        if isinstance(node.value, (int, float)): return ValueType.SCALAR_NUMBER
        if isinstance(node.value, str): return ValueType.STRING
        raise DSLSemanticError("지원하지 않는 상수 형식", self.line, node.col_offset + 1, "BAD_CONSTANT")

    def visit_Attribute(self, node):
        parts = _attribute_parts(node)
        if parts and parts[0] == "ctx":
            if len(parts) < 3:
                raise DSLSemanticError(
                    "parent context는 ctx.<layer>.<feature> 형식이어야 합니다.",
                    self.line, node.col_offset + 1, "BAD_CONTEXT_REFERENCE"
                )
            feature_id = ".".join(parts[1:])
            if not self.context_feature_types:
                raise DSLSemanticError(
                    f"ctx parent-context binding이 제공되지 않았습니다: {feature_id}",
                    self.line, node.col_offset + 1, "CONTEXT_BINDING_REQUIRED"
                )
            value_type = self.context_feature_types.get(feature_id)
            if value_type is None:
                raise DSLSemanticError(
                    f"등록/실행 바인딩되지 않은 parent feature: {feature_id}",
                    self.line, node.col_offset + 1, "UNKNOWN_CONTEXT_FEATURE"
                )
            try:
                return _context_value_type(value_type)
            except ValueError as exc:
                raise DSLSemanticError(
                    str(exc), self.line, node.col_offset + 1, "BAD_CONTEXT_TYPE"
                ) from exc
        if len(parts) == 2:
            return f"{parts[0]}.{parts[1]}"
        raise DSLSemanticError("지원하지 않는 속성 접근", self.line, node.col_offset + 1, "BAD_ATTRIBUTE")

    def _require(self, condition, message, node):
        if not condition:
            raise DSLSemanticError(message, self.line, node.col_offset + 1, "BAD_ARGUMENT_TYPE")

    def _validate_arguments(self, name, args, node):
        if name in {"ta.crossover", "ta.crossunder"}:
            self._require(all(_number(v) for v in args), f"{name}에는 숫자형 인수가 필요합니다.", node)
        elif name in {"ta.sma", "ta.ema", "ta.wma", "ta.rma", "ta.highest", "ta.lowest", "ta.stdev"}:
            self._require(_number(args[0]) and _scalar_number(args[1]), f"{name}은 (numeric series, scalar period)가 필요합니다.", node)
            if len(args) == 3: self._require(_scalar_number(args[2]), f"{name} bars는 scalar number여야 합니다.", node)
        elif name == "ta.ma":
            self._require(_number(args[0]) and _scalar_number(args[1]), "ta.ma의 series/period 형식이 올바르지 않습니다.", node)
            if len(args) >= 3: self._require(args[2] == ValueType.STRING, "ta.ma method는 string이어야 합니다.", node)
            if len(args) == 4: self._require(_scalar_number(args[3]), "ta.ma bars는 scalar number여야 합니다.", node)
        elif name == "ta.sum":
            self._require(_number(args[0]), "ta.sum 첫 인수는 숫자형 series여야 합니다.", node)
            if len(args) >= 2: self._require(_scalar_number(args[1]), "ta.sum period는 scalar number여야 합니다.", node)
            if len(args) == 3: self._require(_scalar_number(args[2]), "ta.sum bars는 scalar number여야 합니다.", node)
        elif name == "ta.roc":
            self._require(_number(args[0]) and _scalar_number(args[1]), "ta.roc(series, period) 형식이 올바르지 않습니다.", node)
        elif name == "ta.rsi":
            if len(args) == 1: self._require(_scalar_number(args[0]), "ta.rsi(period)의 period는 scalar number여야 합니다.", node)
            else: self._require(_number(args[0]) and _scalar_number(args[1]), "ta.rsi(series, period) 형식이 올바르지 않습니다.", node)
        elif name == "ta.jma":
            if len(args) == 3: self._require(all(_scalar_number(v) for v in args), "ta.jma(length, phase, power)는 scalar number가 필요합니다.", node)
            else: self._require(_number(args[0]) and all(_scalar_number(v) for v in args[1:]), "ta.jma(series,length,phase,power) 형식이 올바르지 않습니다.", node)
        elif name in {"ta.supertrend", "ta.supertrend_direction"}:
            self._require(all(_scalar_number(v) for v in args), f"{name}의 period/multiplier는 scalar number여야 합니다.", node)
        elif name == "ta.macd":
            self._require(_number(args[0]), "ta.macd 첫 인수는 숫자형 series여야 합니다.", node)
            if len(args) >= 2: self._require(_scalar_number(args[1]), "ta.macd short는 scalar number여야 합니다.", node)
            if len(args) >= 3: self._require(_scalar_number(args[2]), "ta.macd long은 scalar number여야 합니다.", node)
            if len(args) == 4: self._require(args[3] == ValueType.STRING, "ta.macd method는 string이어야 합니다.", node)
        elif name in {"ta.atr", "ta.adx", "ta.trix", "ta.cci", "ta.nrange", "ta.williams_r", "ta.abs_range", "ta.sum_abs_r", "ta.vhf"}:
            self._require(all(_scalar_number(v) for v in args), f"{name} period는 scalar number여야 합니다.", node)
        elif name == "ta.shift":
            self._require(_number(args[0]) and _scalar_number(args[1]), "ta.shift(series,bars) 형식이 올바르지 않습니다.", node)
        elif name == "ta.bars_since":
            self._require(_boolean(args[0]), "ta.bars_since 조건은 boolean이어야 합니다.", node)
        elif name == "ta.count_since":
            self._require(all(_boolean(v) for v in args), "ta.count_since 인수는 boolean이어야 합니다.", node)
        elif name in {"ta.highest_since", "ta.lowest_since"}:
            self._require(_boolean(args[0]) and _number(args[1]), f"{name}(condition,series) 형식이 올바르지 않습니다.", node)
        elif name == "ta.value_when":
            self._require(_scalar_number(args[0]) and _boolean(args[1]) and _number(args[2]), "ta.value_when(occurrence,condition,series) 형식이 올바르지 않습니다.", node)
        elif name == "logic.ifelse":
            self._require(_boolean(args[0]), "logic.ifelse 첫 인수는 boolean이어야 합니다.", node)
            self._require(_number(args[1]) and _number(args[2]), "logic.ifelse 분기값은 숫자형이어야 합니다.", node)
        elif name in {"state.edge", "state.falling_edge"}:
            self._require(_boolean(args[0]), f"{name} 조건은 boolean이어야 합니다.", node)
        elif name in {"state.ready_after", "state.hold", "state.persist"}:
            self._require(_boolean(args[0]) and _scalar_number(args[1]), f"{name}(condition,bars) 형식이 올바르지 않습니다.", node)
        elif name == "state.latch":
            self._require(_boolean(args[0]) and _boolean(args[1]), "state.latch set/reset은 boolean이어야 합니다.", node)
            if len(args) == 3: self._require(args[2] == ValueType.SCALAR_BOOL, "state.latch initial은 scalar bool이어야 합니다.", node)
        elif name == "state.count":
            self._require(_boolean(args[0]) and _boolean(args[1]), "state.count condition/reset은 boolean이어야 합니다.", node)
        elif name == "state.regime":
            self._require(_boolean(args[0]) and _boolean(args[1]), "state.regime bullish/bearish는 boolean이어야 합니다.", node)
            if len(args) == 3: self._require(_scalar_number(args[2]), "state.regime initial은 scalar number여야 합니다.", node)
        elif name.startswith("mtf."):
            self._require(args and args[0] == ValueType.STRING, f"{name}의 timeframe은 string이어야 합니다.", node)
            if name == "mtf.sma": self._require(_scalar_number(args[1]), "mtf.sma period는 scalar number여야 합니다.", node)
        elif name.startswith("math."):
            self._require(all(_number(v) for v in args), f"{name}에는 숫자형 인수가 필요합니다.", node)

    def visit_Call(self, node):
        if not self.allow_calls:
            raise DSLSemanticError("on_bar에서는 함수 호출을 허용하지 않습니다. 함수 결과를 바깥 변수로 먼저 선언하세요.", self.line, node.col_offset + 1, "ON_BAR_CALL_UNSUPPORTED")
        name = self.visit(node.func)
        if not isinstance(name, str):
            raise DSLSemanticError("호출 대상은 등록된 함수여야 합니다.", self.line, node.col_offset + 1, "UNSUPPORTED_FUNCTION")
        spec = FUNCTION_SPECS.get(name)
        if not spec:
            raise DSLSemanticError(f"지원하지 않는 함수: {name}", self.line, node.col_offset + 1, "UNSUPPORTED_FUNCTION")
        count = len(node.args) + len(node.keywords)
        if not spec.minimum <= count <= spec.maximum:
            raise DSLSemanticError(f"{name} 인수 개수 오류: {count}개 (허용 {spec.minimum}~{spec.maximum})", self.line, node.col_offset + 1, "BAD_ARITY")
        args = [self.visit(item) for item in node.args] + [self.visit(item.value) for item in node.keywords]
        self._validate_arguments(name, args, node)
        if name.startswith("math.") and args and not any(_series(v) for v in args): return ValueType.SCALAR_NUMBER
        if name == "logic.ifelse": return ValueType.SERIES_NUMBER if any(_series(v) for v in args) else ValueType.SCALAR_NUMBER
        return RETURNS[spec.returns]

    def visit_Subscript(self, node):
        parts = _attribute_parts(node.value)
        if parts and parts[0] == "ctx":
            raise DSLSemanticError(
                "ctx.* v1은 별도 과거참조 문법을 지원하지 않습니다. provider/frame에서 원하는 causal feature를 선언하세요.",
                self.line, node.col_offset + 1, "CONTEXT_HISTORY_UNSUPPORTED"
            )
        value = self.visit(node.value)
        if not _series(value):
            raise DSLSemanticError("과거 참조는 series에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_HISTORY_TARGET")
        offset_node = node.slice
        if not isinstance(offset_node, ast.Constant) or not isinstance(offset_node.value, int) or offset_node.value < 0:
            raise DSLSemanticError("과거 참조는 0 이상의 정수 상수만 허용합니다.", self.line, node.col_offset + 1, "BAD_HISTORY_OFFSET")
        return value

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            if not _boolean(value): raise DSLSemanticError("not은 boolean에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_UNARY_TYPE")
            return value
        if not _number(value): raise DSLSemanticError("부호 연산은 숫자형에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_UNARY_TYPE")
        return value

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        if not _number(left) or not _number(right): raise DSLSemanticError("산술 연산은 숫자형에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_BINARY_TYPE")
        return ValueType.SERIES_NUMBER if _series(left) or _series(right) else ValueType.SCALAR_NUMBER

    def visit_BoolOp(self, node):
        values = [self.visit(value) for value in node.values]
        if not all(_boolean(value) for value in values): raise DSLSemanticError("and/or는 boolean에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_BOOLEAN_TYPE")
        return ValueType.SERIES_BOOL if any(_series(value) for value in values) else ValueType.SCALAR_BOOL

    def visit_Compare(self, node):
        values = [self.visit(node.left)] + [self.visit(value) for value in node.comparators]
        for index, operator in enumerate(node.ops):
            left, right = values[index], values[index + 1]
            if isinstance(operator, (ast.Eq, ast.NotEq)):
                compatible = (
                    (_number(left) and _number(right))
                    or (_boolean(left) and _boolean(right))
                    or (_string(left) and _string(right))
                )
                if not compatible:
                    raise DSLSemanticError("동등 비교 양쪽 형식이 호환되지 않습니다.", self.line, node.col_offset + 1, "BAD_COMPARE_TYPE")
            elif not (_number(left) and _number(right)):
                raise DSLSemanticError("대소 비교는 숫자형에만 사용할 수 있습니다.", self.line, node.col_offset + 1, "BAD_COMPARE_TYPE")
        return ValueType.SERIES_BOOL if any(_series(value) for value in values) else ValueType.SCALAR_BOOL

    def generic_visit(self, node):
        raise DSLSemanticError(f"허용되지 않는 표현식: {type(node).__name__}", self.line, getattr(node, "col_offset", 0) + 1, "BAD_EXPRESSION_NODE")


class DSLSemanticAnalyzer:
    MARKET = {name: ValueType.SERIES_NUMBER for name in ("open", "high", "low", "close", "volume", "amount", "open_interest", "date", "time")}

    @classmethod
    def analyze(cls, document: StrategyNode, context_feature_types: Mapping[str, str] | None = None):
        before_bar, after_bar = partition_assignments(document)
        symbols = dict(cls.MARKET)
        context_types = dict(context_feature_types or {})

        def checker(current_symbols, line, allow_calls=True):
            return ExpressionTypeChecker(
                current_symbols,
                line,
                allow_calls=allow_calls,
                context_feature_types=context_types,
            )

        for item in before_bar:
            value = checker(symbols, item.line).check(item.expression)
            if item.is_input and value not in {ValueType.SCALAR_NUMBER, ValueType.SCALAR_BOOL, ValueType.STRING}:
                raise DSLSemanticError(f"input은 scalar만 허용합니다: {item.name}", item.line, code="SERIES_INPUT")
            symbols[item.name] = value

        state_names = set()
        state_scalar_types: dict[str, ValueType] = {}
        for item in document.states:
            value = checker(symbols, item.line).check(item.expression)
            if value not in {ValueType.SCALAR_NUMBER, ValueType.SCALAR_BOOL}:
                raise DSLSemanticError(f"state 초기값은 scalar 숫자/boolean만 허용합니다: {item.name}", item.line, code="BAD_STATE_INITIALIZER")
            symbols[item.name] = value
            state_names.add(item.name)
            state_scalar_types[item.name] = value

        event_symbols = dict(symbols)

        def analyze_bar(items):
            for item in items:
                if isinstance(item, IfNode):
                    condition = checker(symbols, item.line, allow_calls=False).check(item.condition)
                    if not _boolean(condition):
                        raise DSLSemanticError("if 조건은 boolean이어야 합니다.", item.line, code="BAD_IF_TYPE")
                    analyze_bar(item.body)
                    analyze_bar(item.otherwise)
                elif isinstance(item, SetNode):
                    value = checker(symbols, item.line, allow_calls=False).check(item.expression)
                    if _string(value):
                        raise DSLSemanticError("on_bar set/state는 string 값을 저장할 수 없습니다.", item.line, code="BAD_ON_BAR_VALUE_TYPE")
                    scalar_value = ValueType.SCALAR_BOOL if value in {ValueType.SCALAR_BOOL, ValueType.SERIES_BOOL} else ValueType.SCALAR_NUMBER
                    if item.name in state_names:
                        current = state_scalar_types[item.name]
                        if _boolean(current) != _boolean(scalar_value):
                            raise DSLSemanticError(f"state 형식을 변경할 수 없습니다: {item.name}", item.line, code="STATE_TYPE_CHANGE")
                    symbols[item.name] = scalar_value
                    event_symbols[item.name] = ValueType.SERIES_BOOL if _boolean(scalar_value) else ValueType.SERIES_NUMBER

        analyze_bar(document.on_bar)

        for name, scalar_type in state_scalar_types.items():
            event_symbols[name] = ValueType.SERIES_BOOL if _boolean(scalar_type) else ValueType.SERIES_NUMBER
        for name in collect_bar_output_names(document.on_bar):
            if name not in event_symbols and name in symbols:
                scalar_type = symbols[name]
                event_symbols[name] = ValueType.SERIES_BOOL if _boolean(scalar_type) else ValueType.SERIES_NUMBER

        for item in after_bar:
            value = checker(event_symbols, item.line).check(item.expression)
            if item.is_input and value not in {ValueType.SCALAR_NUMBER, ValueType.SCALAR_BOOL, ValueType.STRING}:
                raise DSLSemanticError(f"input은 scalar만 허용합니다: {item.name}", item.line, code="SERIES_INPUT")
            event_symbols[item.name] = value

        for event in document.events:
            event_checker = checker(event_symbols, event.line)
            value = event_checker.check(event.condition)
            if not _boolean(value):
                raise DSLSemanticError("on 조건은 boolean이어야 합니다.", event.line, code="BAD_EVENT_TYPE")
            for order in event.orders:
                if not order.arguments.strip():
                    continue
                call = ast.parse(f"f({order.arguments})", mode="eval").body
                for keyword in call.keywords:
                    if keyword.arg not in {"limit", "stop"}:
                        continue
                    expression = ast.unparse(keyword.value)
                    price_type = event_checker.check(expression)
                    if not _number(price_type):
                        raise DSLSemanticError(
                            f"주문 {keyword.arg} 가격은 숫자형 scalar/series여야 합니다.",
                            order.line,
                            code="BAD_ORDER_PRICE_TYPE",
                        )
        return event_symbols
