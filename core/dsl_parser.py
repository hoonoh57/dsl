"""Fail-closed parser and AST for Quant DSL 2.0-compatible scripts."""
from __future__ import annotations
import ast
import re
from dataclasses import dataclass
from typing import List, Union


class DSLParseError(ValueError):
    def __init__(self, message: str, line: int = 1, column: int = 1, code: str = "PARSE_ERROR"):
        self.line, self.column, self.code = line, column, code
        super().__init__(f"line {line}, column {column}: {message}")


@dataclass(frozen=True)
class AssignmentNode:
    name: str; expression: str; line: int; is_input: bool = False

@dataclass(frozen=True)
class OrderNode:
    command: str; arguments: str; line: int

@dataclass(frozen=True)
class EventNode:
    condition: str; orders: List[OrderNode]; line: int

@dataclass(frozen=True)
class StateNode:
    name: str; expression: str; line: int

@dataclass(frozen=True)
class SetNode:
    name: str; expression: str; line: int

@dataclass(frozen=True)
class IfNode:
    condition: str; body: List["BarStatement"]; otherwise: List["BarStatement"]; line: int

BarStatement = Union[SetNode, IfNode]

@dataclass(frozen=True)
class StrategyNode:
    name: str; timeframe: str; assignments: List[AssignmentNode]; events: List[EventNode]
    states: List[StateNode]; on_bar: List[BarStatement]


class DSLParser:
    ORDER_COMMANDS = {"order.buy", "order.sell_short", "order.close_long", "order.close_short", "order.close_position"}
    ORDER_TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}
    TIFS = {"GTC", "DAY"}
    IDENTIFIER = r"[A-Za-z_가-힣][\w가-힣]*"

    @classmethod
    def parse(cls, source: str) -> StrategyNode:
        if not source.strip(): raise DSLParseError("DSL이 비어 있습니다.", code="EMPTY_SOURCE")
        cleaned = cls._strip_comments(source)
        header = re.search(r'''\A\s*strategy\s+["']([^"']+)["']\s*\{''', cleaned)
        if not header: raise DSLParseError('strategy "이름" { 선언이 필요합니다.', code="MISSING_STRATEGY")
        closing = cls._matching_brace(cleaned, header.end() - 1)
        if cleaned[closing + 1:].strip():
            line = cleaned.count("\n", 0, closing + 1) + 1
            raise DSLParseError("strategy 블록 뒤에 허용되지 않은 내용이 있습니다.", line, code="TRAILING_CONTENT")
        body_start = header.end(); body = cleaned[body_start:closing]
        base_line = cleaned.count("\n", 0, body_start) + 1
        assignments: List[AssignmentNode] = []; events: List[EventNode] = []; states: List[StateNode] = []; on_bar: List[BarStatement] = []
        declared = set(); timeframe = "1d"; lines = body.splitlines(); index = 0
        while index < len(lines):
            raw, line_number = lines[index], base_line + index; text = raw.strip()
            if not text: index += 1; continue
            if re.match(r"^on\s*\(", text):
                block_lines = [raw]; depth = cls._brace_delta(raw)
                while depth > 0:
                    index += 1
                    if index >= len(lines): raise DSLParseError("on 블록의 닫는 괄호가 없습니다.", line_number, code="UNCLOSED_EVENT")
                    block_lines.append(lines[index]); depth += cls._brace_delta(lines[index])
                if depth != 0: raise DSLParseError("on 블록 괄호가 올바르지 않습니다.", line_number, code="BAD_EVENT_BRACE")
                events.append(cls._parse_event("\n".join(block_lines), line_number)); index += 1; continue
            if re.match(r"^on_bar\s*\{", text):
                block_lines = [raw]; depth = cls._brace_delta(raw)
                while depth > 0:
                    index += 1
                    if index >= len(lines): raise DSLParseError("on_bar 블록의 닫는 괄호가 없습니다.", line_number, code="UNCLOSED_ON_BAR")
                    block_lines.append(lines[index]); depth += cls._brace_delta(lines[index])
                if on_bar: raise DSLParseError("on_bar 블록은 하나만 허용합니다.", line_number, code="DUPLICATE_ON_BAR")
                block = "\n".join(block_lines); match_bar = re.match(r"^\s*on_bar\s*\{(.*)\}\s*$", block, flags=re.S)
                if not match_bar: raise DSLParseError("on_bar { ... } 형식이 올바르지 않습니다.", line_number, code="BAD_ON_BAR")
                bar_body = re.sub(r"}\s*else\s*{", "}\nelse {", match_bar.group(1))
                on_bar, _ = cls._parse_bar_statements(bar_body.splitlines(), line_number + 1); index += 1; continue
            statement = text.rstrip(";").strip()
            state_match = re.match(rf"^state\s+({cls.IDENTIFIER})\s*=\s*(.+)$", statement)
            if state_match:
                name, expression = state_match.groups(); cls._validate_expression_syntax(expression, line_number)
                if name in declared: raise DSLParseError(f"변수가 중복 선언되었습니다: {name}", line_number, code="DUPLICATE_SYMBOL")
                declared.add(name); states.append(StateNode(name, expression, line_number)); index += 1; continue
            match = re.match(rf"^(input\s+)?({cls.IDENTIFIER})\s*=\s*(.+)$", statement)
            if not match: raise DSLParseError(f"인식할 수 없는 문장: {text}", line_number, code="UNKNOWN_STATEMENT")
            input_prefix, name, expression = match.groups(); cls._validate_expression_syntax(expression, line_number)
            if name == "timeframe":
                value = expression.strip().strip('"\'')
                if not re.match(r"^\d+(?:m|h|d|w|M)$", value): raise DSLParseError(f"지원하지 않는 timeframe: {value}", line_number, code="BAD_TIMEFRAME")
                timeframe = value
            else:
                if name in {"open","high","low","close","volume","amount","open_interest","date","time"}: raise DSLParseError(f"시장 데이터 이름은 다시 할당할 수 없습니다: {name}", line_number, code="RESERVED_NAME")
                if name in declared: raise DSLParseError(f"변수가 중복 선언되었습니다: {name}", line_number, code="DUPLICATE_SYMBOL")
                declared.add(name); assignments.append(AssignmentNode(name, expression, line_number, bool(input_prefix)))
            index += 1
        return StrategyNode(header.group(1), timeframe, assignments, events, states, on_bar)

    @classmethod
    def _parse_bar_statements(cls, lines: List[str], base_line: int, start: int = 0, stop_on_brace: bool = False):
        result: List[BarStatement] = []; index = start
        while index < len(lines):
            text = lines[index].strip().rstrip(";").strip(); line = base_line + index
            if not text: index += 1; continue
            if text == "}":
                if stop_on_brace: return result, index + 1
                raise DSLParseError("예상하지 못한 닫는 괄호입니다.", line, code="BAD_ON_BAR_BRACE")
            match_if = re.match(r"^if\s*\((.*)\)\s*\{$", text)
            if match_if:
                condition = match_if.group(1).strip(); cls._validate_expression_syntax(condition, line)
                body, index = cls._parse_bar_statements(lines, base_line, index + 1, True); otherwise: List[BarStatement] = []
                if index < len(lines) and re.match(r"^else\s*\{$", lines[index].strip()): otherwise, index = cls._parse_bar_statements(lines, base_line, index + 1, True)
                result.append(IfNode(condition, body, otherwise, line)); continue
            match_set = re.match(rf"^(?:set\s+)?({cls.IDENTIFIER})\s*=\s*(.+)$", text)
            if not match_set: raise DSLParseError(f"on_bar에서 인식할 수 없는 문장: {text}", line, code="BAD_ON_BAR_STATEMENT")
            name, expression = match_set.groups(); cls._validate_expression_syntax(expression, line); result.append(SetNode(name, expression, line)); index += 1
        if stop_on_brace: raise DSLParseError("if/else 블록의 닫는 괄호가 없습니다.", base_line + start, code="UNCLOSED_IF")
        return result, index

    @staticmethod
    def _strip_comments(source: str) -> str:
        return "\n".join(line.split("//", 1)[0] for line in source.splitlines())

    @staticmethod
    def _brace_delta(text: str) -> int:
        depth = 0; quote = None; escaped = False
        for char in text:
            if quote:
                if escaped: escaped = False
                elif char == "\\": escaped = True
                elif char == quote: quote = None
                continue
            if char in "\"'": quote = char
            elif char == "{": depth += 1
            elif char == "}": depth -= 1
        return depth

    @staticmethod
    def _matching_brace(source: str, opening: int) -> int:
        depth = 0; quote = None; escaped = False
        for index in range(opening, len(source)):
            char = source[index]
            if quote:
                if escaped: escaped = False
                elif char == "\\": escaped = True
                elif char == quote: quote = None
                continue
            if char in "\"'": quote = char
            elif char == "{": depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0: return index
        line = source.count("\n", 0, opening) + 1
        raise DSLParseError("strategy 블록의 닫는 괄호가 없습니다.", line, code="UNCLOSED_STRATEGY")

    @classmethod
    def _parse_event(cls, block: str, line: int) -> EventNode:
        match = re.match(r"^\s*on\s*\((.*?)\)\s*\{(.*)\}\s*$", block, flags=re.S)
        if not match: raise DSLParseError("on(조건) { 주문 } 형식이 올바르지 않습니다.", line, code="BAD_EVENT")
        condition, body = match.groups(); cls._validate_expression_syntax(condition.strip(), line); orders = []
        for statement in cls._split_order_statements(body):
            order_match = re.match(r"^([A-Za-z_][\w]*\.[A-Za-z_][\w]*)\s*\((.*)\)$", statement, flags=re.S)
            if not order_match: raise DSLParseError(f"잘못된 주문 문장: {statement}", line, code="BAD_ORDER")
            command, arguments = order_match.groups()
            if command not in cls.ORDER_COMMANDS: raise DSLParseError(f"지원하지 않는 주문 명령: {command}", line, code="UNSUPPORTED_ORDER")
            cls._validate_order_arguments(command, arguments, line); orders.append(OrderNode(command, arguments.strip(), line))
        if not orders: raise DSLParseError("on 블록에는 하나 이상의 주문이 필요합니다.", line, code="EMPTY_EVENT")
        commands = {order.command for order in orders}
        if commands & {"order.buy","order.sell_short"} and commands & {"order.close_long","order.close_short","order.close_position"}: raise DSLParseError("하나의 on 블록에서 진입과 청산을 동시에 실행할 수 없습니다.", line, code="CONFLICTING_ORDERS")
        return EventNode(condition.strip(), orders, line)

    @staticmethod
    def _split_order_statements(body: str) -> List[str]:
        values, buffer, depth, quote, escaped = [], [], 0, None, False
        for char in body:
            if quote:
                buffer.append(char)
                if escaped: escaped = False
                elif char == "\\": escaped = True
                elif char == quote: quote = None
                continue
            if char in "\"'": quote = char; buffer.append(char); continue
            if char == "(": depth += 1
            elif char == ")": depth -= 1
            if char in ";\n" and depth == 0:
                value = "".join(buffer).strip()
                if value: values.append(value)
                buffer = []
            else: buffer.append(char)
        value = "".join(buffer).strip()
        if value: values.append(value)
        return values

    @staticmethod
    def _validate_expression_syntax(expression: str, line: int):
        normalized = re.sub(r"\btrue\b", "True", expression, flags=re.I); normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.I)
        try: ast.parse(normalized, mode="eval")
        except SyntaxError as exc: raise DSLParseError(f"수식 문법 오류: {exc.msg}", line, exc.offset or 1, "BAD_EXPRESSION") from exc

    @classmethod
    def _validate_order_arguments(cls, command: str, arguments: str, line: int):
        if not arguments.strip(): return
        try: call = ast.parse(f"f({arguments})", mode="eval").body
        except SyntaxError as exc: raise DSLParseError(f"주문 인수 문법 오류: {exc.msg}", line, exc.offset or 1, "BAD_ORDER_ARGS") from exc
        if call.args: raise DSLParseError("주문 인수는 이름=값 형식만 허용합니다.", line, code="POSITIONAL_ORDER_ARG")
        allowed = {"type", "id", "quantity", "limit", "stop", "tif", "oco"}; names = [item.arg for item in call.keywords]
        if len(names) != len(set(names)): raise DSLParseError("주문 인수가 중복되었습니다.", line, code="DUPLICATE_ORDER_ARG")
        for item in call.keywords:
            if item.arg not in allowed: raise DSLParseError(f"지원하지 않는 주문 인수: {item.arg}", line, code="BAD_ORDER_ARG")
        if command.startswith("order.close") and call.keywords: raise DSLParseError(f"{command}은 현재 인수를 지원하지 않습니다.", line, code="BAD_CLOSE_ARG")
        if command in {"order.buy", "order.sell_short"}:
            order_type = "MARKET"; tif = "GTC"
            for item in call.keywords:
                if item.arg in {"type", "tif", "id", "oco"} and not isinstance(item.value, ast.Constant): raise DSLParseError(f"주문 {item.arg}은 문자열 상수여야 합니다.", line, code="BAD_ORDER_LITERAL")
                if item.arg == "type": order_type = str(item.value.value).upper()
                elif item.arg == "tif": tif = str(item.value.value).upper()
            if order_type not in cls.ORDER_TYPES: raise DSLParseError(f"지원하지 않는 주문 유형: {order_type}", line, code="UNSUPPORTED_ORDER_TYPE")
            if tif not in cls.TIFS: raise DSLParseError(f"지원하지 않는 TIF: {tif}", line, code="UNSUPPORTED_TIF")
            name_set = set(names)
            if order_type in {"LIMIT", "STOP_LIMIT"} and "limit" not in name_set: raise DSLParseError("LIMIT 주문에는 limit 가격이 필요합니다.", line, code="MISSING_LIMIT")
            if order_type in {"STOP", "STOP_LIMIT"} and "stop" not in name_set: raise DSLParseError("STOP 주문에는 stop 가격이 필요합니다.", line, code="MISSING_STOP")
