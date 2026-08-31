"""Fail-closed provisional intrabar state lifecycle for AXIS 1.

`on_tick` and `on_fill` blocks are extracted before the migrated parser runs.
They may mutate declared strategy state only. Mutations are provisional until the
open bar is committed; rollback restores the last committed snapshot exactly.
No runtime loop, order placement, indicator recomputation or provider access is
introduced here.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import math
import re
from typing import Mapping


IDENTIFIER = r"[A-Za-z_가-힣][\w가-힣]*"
HANDLER_KINDS = ("on_tick", "on_fill")
TICK_FIELDS = {"price", "volume", "time"}
FILL_FIELDS = {"price", "quantity", "side", "order_id", "time"}
FILL_SIDES = {"BUY", "SELL", "SELL_SHORT", "COVER"}


class IntrabarLifecycleError(ValueError):
    def __init__(self, message: str, line: int = 1, column: int = 1, code: str = "INTRABAR_LIFECYCLE_ERROR"):
        self.line = int(line)
        self.column = int(column)
        self.code = str(code)
        super().__init__(f"line {self.line}, column {self.column}: {message}")


@dataclass(frozen=True)
class IntrabarSet:
    name: str
    expression: str
    line: int


@dataclass(frozen=True)
class IntrabarIf:
    condition: str
    body: tuple[object, ...]
    otherwise: tuple[object, ...]
    line: int


@dataclass(frozen=True)
class IntrabarHandler:
    kind: str
    statements: tuple[object, ...]
    line: int

    def public_dict(self) -> dict:
        return {
            "kind": self.kind,
            "line": self.line,
            "statement_count": _statement_count(self.statements),
            "transactional": True,
            "provisional_until_commit": True,
        }


@dataclass(frozen=True)
class IntrabarProgram:
    state_names: tuple[str, ...]
    handlers: tuple[IntrabarHandler, ...]

    def handler(self, kind: str) -> IntrabarHandler | None:
        for item in self.handlers:
            if item.kind == kind:
                return item
        return None

    def manifest(self) -> tuple[dict, ...]:
        return tuple(item.public_dict() for item in self.handlers)

    def new_session(self, initial_state: Mapping[str, object]):
        return IntrabarStateSession(self, initial_state)


@dataclass(frozen=True)
class LoweredIntrabar:
    source: str
    program: IntrabarProgram


def _statement_count(statements) -> int:
    total = 0
    for item in statements:
        total += 1
        if isinstance(item, IntrabarIf):
            total += _statement_count(item.body) + _statement_count(item.otherwise)
    return total


def _code_before_comment(text: str) -> str:
    quote = None
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'":
            quote = char
            index += 1
            continue
        if char == "/" and index + 1 < len(text) and text[index + 1] == "/":
            return text[:index]
        index += 1
    return text


def _brace_delta(text: str) -> int:
    depth = 0
    quote = None
    escaped = False
    for char in text:
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    return depth


def _parse_expression(expression: str, line: int) -> ast.AST:
    normalized = re.sub(r"\btrue\b", "True", expression, flags=re.I)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.I)
    try:
        return ast.parse(normalized, mode="eval").body
    except SyntaxError as exc:
        raise IntrabarLifecycleError(
            f"intrabar 수식 문법 오류: {exc.msg}", line, exc.offset or 1, "BAD_INTRABAR_EXPRESSION"
        ) from exc


def _attribute_parts(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return _attribute_parts(node.value) + [node.attr]
    return []


def _validate_expression(expression: str, *, line: int, kind: str, state_names: set[str]) -> None:
    node = _parse_expression(expression, line)
    allowed_nodes = (
        ast.Name, ast.Constant, ast.Attribute, ast.Load,
        ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    )
    for item in ast.walk(node):
        if not isinstance(item, allowed_nodes):
            raise IntrabarLifecycleError(
                f"intrabar handler에서 허용되지 않는 문법: {type(item).__name__}",
                line,
                getattr(item, "col_offset", 0) + 1,
                "BAD_INTRABAR_EXPRESSION_NODE",
            )
        if isinstance(item, ast.Name):
            if item.id in state_names or item.id in {"True", "False", "tick", "fill"}:
                continue
            raise IntrabarLifecycleError(
                f"intrabar handler에서 정의되지 않은 이름: {item.id}",
                line,
                getattr(item, "col_offset", 0) + 1,
                "INTRABAR_FREE_VARIABLE",
            )
        if isinstance(item, ast.Attribute):
            parts = _attribute_parts(item)
            if len(parts) != 2:
                raise IntrabarLifecycleError("intrabar event field 형식이 올바르지 않습니다.", line, code="BAD_INTRABAR_EVENT_FIELD")
            root, field = parts
            if kind == "on_tick":
                if root != "tick" or field not in TICK_FIELDS:
                    raise IntrabarLifecycleError(
                        f"on_tick에서 허용되지 않는 event field: {'.'.join(parts)}",
                        line,
                        code="BAD_TICK_FIELD",
                    )
            elif kind == "on_fill":
                if root != "fill" or field not in FILL_FIELDS:
                    raise IntrabarLifecycleError(
                        f"on_fill에서 허용되지 않는 event field: {'.'.join(parts)}",
                        line,
                        code="BAD_FILL_FIELD",
                    )


def _parse_statements(lines: list[str], base_line: int, *, kind: str, state_names: set[str], start: int = 0, stop_on_brace: bool = False):
    result: list[object] = []
    index = start
    while index < len(lines):
        raw = _code_before_comment(lines[index])
        text = raw.strip().rstrip(";").strip()
        line = base_line + index
        if not text:
            index += 1
            continue
        if text == "}":
            if stop_on_brace:
                return tuple(result), index + 1
            raise IntrabarLifecycleError("예상하지 못한 intrabar 닫는 괄호입니다.", line, code="BAD_INTRABAR_BRACE")
        match_if = re.match(r"^if\s*\((.*)\)\s*\{$", text)
        if match_if:
            condition = match_if.group(1).strip()
            _validate_expression(condition, line=line, kind=kind, state_names=state_names)
            body, next_index = _parse_statements(
                lines, base_line, kind=kind, state_names=state_names, start=index + 1, stop_on_brace=True
            )
            otherwise: tuple[object, ...] = ()
            if next_index < len(lines):
                else_text = _code_before_comment(lines[next_index]).strip()
                if re.match(r"^else\s*\{$", else_text):
                    otherwise, next_index = _parse_statements(
                        lines, base_line, kind=kind, state_names=state_names, start=next_index + 1, stop_on_brace=True
                    )
            result.append(IntrabarIf(condition, body, otherwise, line))
            index = next_index
            continue
        match_set = re.match(rf"^(?:set\s+)?({IDENTIFIER})\s*=\s*(.+)$", text)
        if not match_set:
            raise IntrabarLifecycleError(
                f"intrabar handler에서 인식할 수 없는 문장: {text}", line, code="BAD_INTRABAR_STATEMENT"
            )
        name, expression = match_set.groups()
        if name not in state_names:
            raise IntrabarLifecycleError(
                f"intrabar handler는 선언된 state만 변경할 수 있습니다: {name}",
                line,
                code="INTRABAR_TARGET_NOT_STATE",
            )
        _validate_expression(expression, line=line, kind=kind, state_names=state_names)
        result.append(IntrabarSet(name, expression.strip(), line))
        index += 1
    if stop_on_brace:
        raise IntrabarLifecycleError("intrabar if/else 블록의 닫는 괄호가 없습니다.", base_line + start, code="UNCLOSED_INTRABAR_IF")
    return tuple(result), index


def extract_intrabar_handlers(source: str) -> LoweredIntrabar:
    """Strip top-level on_tick/on_fill blocks while preserving line count."""
    if not isinstance(source, str):
        raise TypeError("DSL source는 문자열이어야 합니다.")
    lines = source.splitlines()
    if not lines:
        return LoweredIntrabar(source=source, program=IntrabarProgram((), ()))

    state_pattern = re.compile(rf"^\s*state\s+({IDENTIFIER})\s*=")
    state_names: list[str] = []
    depth = 0
    for raw in lines:
        code = _code_before_comment(raw)
        current_depth = depth
        if current_depth == 1:
            match = state_pattern.match(code)
            if match:
                state_names.append(match.group(1))
        depth += _brace_delta(code)
    if len(state_names) != len(set(state_names)):
        raise IntrabarLifecycleError("intrabar state 이름이 중복되었습니다.", code="DUPLICATE_INTRABAR_STATE")
    state_set = set(state_names)

    output = list(lines)
    handlers: list[IntrabarHandler] = []
    seen: set[str] = set()
    depth = 0
    index = 0
    while index < len(lines):
        raw = lines[index]
        code = _code_before_comment(raw)
        current_depth = depth
        match = re.match(r"^\s*(on_tick|on_fill)\s*\{\s*$", code) if current_depth == 1 else None
        if match:
            kind = match.group(1)
            if kind in seen:
                raise IntrabarLifecycleError(f"{kind} 블록은 하나만 허용합니다.", index + 1, code="DUPLICATE_INTRABAR_HANDLER")
            block_depth = _brace_delta(code)
            if block_depth != 1:
                raise IntrabarLifecycleError(f"{kind} 괄호가 올바르지 않습니다.", index + 1, code="BAD_INTRABAR_BRACE")
            start = index
            cursor = index + 1
            body: list[str] = []
            while cursor < len(lines):
                body_code = _code_before_comment(lines[cursor])
                delta = _brace_delta(body_code)
                block_depth += delta
                if block_depth == 0:
                    if body_code.strip() != "}":
                        raise IntrabarLifecycleError(
                            f"{kind} 닫는 괄호는 단독 문장이어야 합니다.", cursor + 1, code="BAD_INTRABAR_BRACE"
                        )
                    break
                if block_depth < 0:
                    raise IntrabarLifecycleError(f"{kind} 괄호가 올바르지 않습니다.", cursor + 1, code="BAD_INTRABAR_BRACE")
                body.append(lines[cursor])
                cursor += 1
            if cursor >= len(lines) or block_depth != 0:
                raise IntrabarLifecycleError(f"{kind} 블록의 닫는 괄호가 없습니다.", start + 1, code="UNCLOSED_INTRABAR_HANDLER")
            statements, consumed = _parse_statements(body, start + 2, kind=kind, state_names=state_set)
            if consumed != len(body):
                raise IntrabarLifecycleError(f"{kind} handler parse가 완전하지 않습니다.", start + 1, code="BAD_INTRABAR_HANDLER")
            if not statements:
                raise IntrabarLifecycleError(f"{kind} 블록이 비어 있습니다.", start + 1, code="EMPTY_INTRABAR_HANDLER")
            handlers.append(IntrabarHandler(kind, statements, start + 1))
            seen.add(kind)
            for row in range(start, cursor + 1):
                output[row] = ""
            index = cursor + 1
            continue
        depth += _brace_delta(code)
        index += 1

    suffix = "\n" if source.endswith("\n") else ""
    lowered_source = "\n".join(output) + suffix
    if len(lowered_source.splitlines()) != len(source.splitlines()):
        raise RuntimeError("intrabar lowering line-count contract 오류")
    return LoweredIntrabar(
        source=lowered_source,
        program=IntrabarProgram(tuple(state_names), tuple(sorted(handlers, key=lambda item: item.line))),
    )


def _state_kind(value) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if not math.isfinite(number):
            raise IntrabarLifecycleError("state snapshot의 숫자는 유한해야 합니다.", code="BAD_INTRABAR_STATE_VALUE")
        return "number"
    raise IntrabarLifecycleError(
        f"지원하지 않는 intrabar state 형식: {type(value).__name__}", code="BAD_INTRABAR_STATE_TYPE"
    )


class _EventExpression(ast.NodeVisitor):
    def __init__(self, state: Mapping[str, object], event_root: str, event: Mapping[str, object]):
        self.state = state
        self.event_root = event_root
        self.event = event

    def evaluate(self, expression: str):
        normalized = re.sub(r"\btrue\b", "True", expression, flags=re.I)
        normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.I)
        return self.visit(ast.parse(normalized, mode="eval").body)

    def visit_Name(self, node):
        if node.id in self.state:
            return self.state[node.id]
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        raise IntrabarLifecycleError(f"intrabar 실행 중 정의되지 않은 이름: {node.id}", code="INTRABAR_RUNTIME_NAME")

    def visit_Constant(self, node):
        return node.value

    def visit_Attribute(self, node):
        parts = _attribute_parts(node)
        if len(parts) != 2 or parts[0] != self.event_root or parts[1] not in self.event:
            raise IntrabarLifecycleError(f"intrabar event field가 바인딩되지 않았습니다: {'.'.join(parts)}", code="INTRABAR_EVENT_UNBOUND")
        return self.event[parts[1]]

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not bool(value)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value
        raise IntrabarLifecycleError("지원하지 않는 intrabar 단항 연산자입니다.", code="BAD_INTRABAR_OPERATOR")

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        functions = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a ** b,
        }
        fn = functions.get(type(node.op))
        if fn is None:
            raise IntrabarLifecycleError("지원하지 않는 intrabar 산술 연산자입니다.", code="BAD_INTRABAR_OPERATOR")
        return fn(left, right)

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            return all(bool(self.visit(item)) for item in node.values)
        if isinstance(node.op, ast.Or):
            return any(bool(self.visit(item)) for item in node.values)
        raise IntrabarLifecycleError("지원하지 않는 intrabar 논리 연산자입니다.", code="BAD_INTRABAR_OPERATOR")

    def visit_Compare(self, node):
        functions = {
            ast.Eq: lambda a, b: a == b,
            ast.NotEq: lambda a, b: a != b,
            ast.Lt: lambda a, b: a < b,
            ast.LtE: lambda a, b: a <= b,
            ast.Gt: lambda a, b: a > b,
            ast.GtE: lambda a, b: a >= b,
        }
        left = self.visit(node.left)
        for operator, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            fn = functions.get(type(operator))
            if fn is None or not bool(fn(left, right)):
                return False
            left = right
        return True

    def generic_visit(self, node):
        raise IntrabarLifecycleError(f"intrabar 실행에서 허용되지 않는 문법: {type(node).__name__}", code="BAD_INTRABAR_RUNTIME_NODE")


class IntrabarStateSession:
    """Transactional state continuation for one open bar at a time."""

    def __init__(self, program: IntrabarProgram, initial_state: Mapping[str, object]):
        self.program = program
        supplied = dict(initial_state)
        expected = set(program.state_names)
        missing = sorted(expected - set(supplied))
        extra = sorted(set(supplied) - expected)
        if missing or extra:
            raise IntrabarLifecycleError(
                f"intrabar state snapshot coverage 오류: missing={missing}, extra={extra}",
                code="INTRABAR_STATE_COVERAGE",
            )
        self._kinds = {name: _state_kind(value) for name, value in supplied.items()}
        self._committed = copy.deepcopy(supplied)
        self._provisional: dict[str, object] | None = None
        self._bar_id: str | None = None
        self._revision = 0
        self._event_sequence = 0
        self.audit: list[dict] = []

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def bar_open(self) -> bool:
        return self._provisional is not None

    def committed_state(self) -> dict[str, object]:
        return copy.deepcopy(self._committed)

    def provisional_state(self) -> dict[str, object]:
        if self._provisional is None:
            raise IntrabarLifecycleError("열린 bar가 없습니다.", code="INTRABAR_BAR_NOT_OPEN")
        return copy.deepcopy(self._provisional)

    def begin_bar(self, bar_id) -> dict[str, object]:
        if self._provisional is not None:
            raise IntrabarLifecycleError("이미 열린 intrabar transaction이 있습니다.", code="INTRABAR_BAR_ALREADY_OPEN")
        identity = str(bar_id).strip()
        if not identity:
            raise IntrabarLifecycleError("bar_id는 비어 있을 수 없습니다.", code="BAD_INTRABAR_BAR_ID")
        self._bar_id = identity
        self._provisional = copy.deepcopy(self._committed)
        self.audit.append({"event": "BEGIN", "bar_id": identity, "revision": self._revision})
        return self.provisional_state()

    @staticmethod
    def _finite_number(value, label: str, *, positive=False, nonnegative=False) -> float:
        if isinstance(value, bool):
            raise IntrabarLifecycleError(f"{label}은 숫자여야 합니다.", code="BAD_INTRABAR_EVENT_VALUE")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise IntrabarLifecycleError(f"{label}은 숫자여야 합니다.", code="BAD_INTRABAR_EVENT_VALUE") from exc
        if not math.isfinite(number):
            raise IntrabarLifecycleError(f"{label}은 유한해야 합니다.", code="BAD_INTRABAR_EVENT_VALUE")
        if positive and number <= 0:
            raise IntrabarLifecycleError(f"{label}은 0보다 커야 합니다.", code="BAD_INTRABAR_EVENT_VALUE")
        if nonnegative and number < 0:
            raise IntrabarLifecycleError(f"{label}은 0 이상이어야 합니다.", code="BAD_INTRABAR_EVENT_VALUE")
        return number

    def on_tick(self, *, price, volume=0.0, time=None) -> dict[str, object]:
        event = {
            "price": self._finite_number(price, "tick.price", positive=True),
            "volume": self._finite_number(volume, "tick.volume", nonnegative=True),
            "time": "" if time is None else str(time),
        }
        return self._apply("on_tick", "tick", event)

    def on_fill(self, *, price, quantity, side, order_id=None, time=None) -> dict[str, object]:
        side_value = str(side).upper()
        if side_value not in FILL_SIDES:
            raise IntrabarLifecycleError(f"지원하지 않는 fill.side: {side}", code="BAD_INTRABAR_FILL_SIDE")
        event = {
            "price": self._finite_number(price, "fill.price", positive=True),
            "quantity": self._finite_number(quantity, "fill.quantity", positive=True),
            "side": side_value,
            "order_id": "" if order_id is None else str(order_id),
            "time": "" if time is None else str(time),
        }
        return self._apply("on_fill", "fill", event)

    def _apply(self, kind: str, root: str, event: Mapping[str, object]) -> dict[str, object]:
        if self._provisional is None:
            raise IntrabarLifecycleError("intrabar event 전에 begin_bar가 필요합니다.", code="INTRABAR_BAR_NOT_OPEN")
        handler = self.program.handler(kind)
        before = copy.deepcopy(self._provisional)
        self._event_sequence += 1
        try:
            if handler is not None:
                self._run(handler.statements, root, event)
        except Exception as exc:
            self._provisional = before
            self.audit.append({
                "event": kind.upper(), "bar_id": self._bar_id, "sequence": self._event_sequence,
                "status": "ROLLED_BACK_EVENT", "reason": str(exc),
            })
            if isinstance(exc, IntrabarLifecycleError):
                raise
            raise IntrabarLifecycleError(f"intrabar event 실행 실패: {exc}", code="INTRABAR_EVENT_FAILED") from exc
        self.audit.append({
            "event": kind.upper(), "bar_id": self._bar_id, "sequence": self._event_sequence,
            "status": "PROVISIONAL",
        })
        return self.provisional_state()

    def _run(self, statements, root: str, event: Mapping[str, object]) -> None:
        assert self._provisional is not None
        evaluator = _EventExpression(self._provisional, root, event)
        for item in statements:
            if isinstance(item, IntrabarSet):
                value = evaluator.evaluate(item.expression)
                expected_kind = self._kinds[item.name]
                actual_kind = _state_kind(value)
                if actual_kind != expected_kind:
                    raise IntrabarLifecycleError(
                        f"intrabar state 형식 변경은 허용되지 않습니다: {item.name} {expected_kind}->{actual_kind}",
                        item.line,
                        code="INTRABAR_STATE_TYPE_CHANGE",
                    )
                self._provisional[item.name] = value
                evaluator = _EventExpression(self._provisional, root, event)
            elif isinstance(item, IntrabarIf):
                branch = item.body if bool(evaluator.evaluate(item.condition)) else item.otherwise
                self._run(branch, root, event)
                evaluator = _EventExpression(self._provisional, root, event)
            else:
                raise IntrabarLifecycleError("알 수 없는 intrabar statement입니다.", code="BAD_INTRABAR_RUNTIME_STATEMENT")

    def commit_bar(self) -> dict[str, object]:
        if self._provisional is None:
            raise IntrabarLifecycleError("commit할 열린 bar가 없습니다.", code="INTRABAR_BAR_NOT_OPEN")
        self._committed = copy.deepcopy(self._provisional)
        identity = self._bar_id
        self._provisional = None
        self._bar_id = None
        self._revision += 1
        self.audit.append({"event": "COMMIT", "bar_id": identity, "revision": self._revision})
        return self.committed_state()

    def rollback_bar(self) -> dict[str, object]:
        if self._provisional is None:
            raise IntrabarLifecycleError("rollback할 열린 bar가 없습니다.", code="INTRABAR_BAR_NOT_OPEN")
        identity = self._bar_id
        self._provisional = None
        self._bar_id = None
        self.audit.append({"event": "ROLLBACK", "bar_id": identity, "revision": self._revision})
        return self.committed_state()
