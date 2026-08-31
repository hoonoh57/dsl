"""Fail-closed compile-time bounded loops for AXIS 1 user functions.

Loops are deliberately restricted to pure user-function local accumulators and
are fully unrolled before the existing user-function/multi-output lowerers and
migrated runtime execute the strategy.  No runtime loop authority is added.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import re


IDENTIFIER = r"[A-Za-z_가-힣][\w가-힣]*"
INTERNAL_PREFIX = "__axis1_loop_"
MAX_BOUNDED_LOOP_ITERATIONS = 64
MAX_EXPANDED_AST_NODES = 20_000


class BoundedLoopError(ValueError):
    def __init__(self, message: str, line: int = 1, column: int = 1, code: str = "BOUNDED_LOOP_ERROR"):
        self.line = int(line)
        self.column = int(column)
        self.code = str(code)
        super().__init__(f"line {self.line}, column {self.column}: {message}")


@dataclass(frozen=True)
class BoundedLoopSpec:
    function: str
    index: str
    start: int
    stop: int
    step: int
    iterations: int
    targets: tuple[str, ...]
    line: int

    def public_dict(self) -> dict:
        return {
            "function": self.function,
            "index": self.index,
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
            "iterations": self.iterations,
            "targets": self.targets,
            "line": self.line,
            "compile_time": True,
            "runtime_loop": False,
        }


@dataclass(frozen=True)
class LoweredBoundedLoops:
    source: str
    loops: tuple[BoundedLoopSpec, ...]

    def manifest(self) -> tuple[dict, ...]:
        return tuple(item.public_dict() for item in self.loops)


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
        raise BoundedLoopError(
            f"반복문 수식 문법 오류: {exc.msg}",
            line,
            exc.offset or 1,
            "BAD_LOOP_EXPRESSION",
        ) from exc


def _node_size(node: ast.AST) -> int:
    return sum(1 for _ in ast.walk(node))


class _NameSubstituter(ast.NodeTransformer):
    def __init__(
        self,
        *,
        aliases: dict[str, str] | None = None,
        values: dict[str, ast.AST] | None = None,
        index_name: str | None = None,
        index_value: int | None = None,
    ):
        self.aliases = dict(aliases or {})
        self.values = dict(values or {})
        self.index_name = index_name
        self.index_value = index_value

    def visit_Name(self, node: ast.Name):
        if not isinstance(node.ctx, ast.Load):
            return node
        if self.index_name is not None and node.id == self.index_name:
            return ast.copy_location(ast.Constant(value=int(self.index_value)), node)
        if node.id in self.values:
            return ast.copy_location(copy.deepcopy(self.values[node.id]), node)
        if node.id in self.aliases:
            return ast.copy_location(ast.Name(id=self.aliases[node.id], ctx=ast.Load()), node)
        return node


def _rewrite_expression(expression: str, line: int, aliases: dict[str, str]) -> str:
    if not aliases:
        return expression.strip()
    node = _parse_expression(expression.strip(), line)
    node = _NameSubstituter(aliases=aliases).visit(node)
    ast.fix_missing_locations(node)
    return ast.unparse(node)


def _parse_range(header: str, line: int) -> tuple[str, tuple[int, ...], int, int, int]:
    match = re.match(
        rf"^\s*for\s+({IDENTIFIER})\s+in\s+range\s*\((.*?)\)\s*\{{\s*$",
        header,
    )
    if not match:
        raise BoundedLoopError(
            "반복문은 for 이름 in range(정수...) { 형식이어야 합니다.",
            line,
            code="BAD_BOUNDED_LOOP_DECLARATION",
        )
    index_name, raw_args = match.groups()
    try:
        call = ast.parse(f"range({raw_args})", mode="eval").body
    except SyntaxError as exc:
        raise BoundedLoopError(
            f"range 인수 문법 오류: {exc.msg}",
            line,
            exc.offset or 1,
            "BAD_LOOP_RANGE",
        ) from exc
    if not isinstance(call, ast.Call) or call.keywords or not 1 <= len(call.args) <= 3:
        raise BoundedLoopError("range는 1~3개의 정수 위치 인수만 허용합니다.", line, code="BAD_LOOP_RANGE")
    values: list[int] = []
    for argument in call.args:
        if not isinstance(argument, ast.Constant) or isinstance(argument.value, bool) or not isinstance(argument.value, int):
            raise BoundedLoopError(
                "반복 범위는 compile-time 정수 상수만 허용합니다.",
                line,
                getattr(argument, "col_offset", 0) + 1,
                "LOOP_BOUND_LITERAL_REQUIRED",
            )
        values.append(int(argument.value))
    if len(values) == 1:
        start, stop, step = 0, values[0], 1
    elif len(values) == 2:
        start, stop, step = values[0], values[1], 1
    else:
        start, stop, step = values
    if step == 0:
        raise BoundedLoopError("반복 step은 0일 수 없습니다.", line, code="LOOP_ZERO_STEP")
    iterations = tuple(range(start, stop, step))
    if len(iterations) > MAX_BOUNDED_LOOP_ITERATIONS:
        raise BoundedLoopError(
            f"반복 횟수는 최대 {MAX_BOUNDED_LOOP_ITERATIONS}회까지 허용합니다: {len(iterations)}회",
            line,
            code="LOOP_ITERATION_LIMIT",
        )
    return index_name, iterations, start, stop, step


def _rewrite_plain_function_line(raw: str, line: int, aliases: dict[str, str]) -> str:
    code = _code_before_comment(raw)
    suffix = raw[len(code):]
    stripped = code.strip().rstrip(";").strip()
    if not stripped or not aliases:
        return raw
    indent = code[: len(code) - len(code.lstrip())]
    return_match = re.match(r"^return\s+(.+)$", stripped)
    if return_match:
        expression = _rewrite_expression(return_match.group(1), line, aliases)
        return f"{indent}return {expression}{suffix}"
    local_match = re.match(rf"^({IDENTIFIER})\s*=\s*(.+)$", stripped)
    if local_match:
        name, expression = local_match.groups()
        expression = _rewrite_expression(expression, line, aliases)
        return f"{indent}{name} = {expression}{suffix}"
    return raw


def _lower_function_block(
    block: list[str],
    *,
    start_line: int,
    function_name: str,
    parameters: tuple[str, ...],
    loop_number_start: int,
) -> tuple[list[str], list[BoundedLoopSpec], int]:
    if any(INTERNAL_PREFIX in _code_before_comment(raw) for raw in block):
        raise BoundedLoopError(
            f"{INTERNAL_PREFIX} 접두사는 반복문 내부 이름으로 예약되어 있습니다.",
            start_line,
            code="RESERVED_LOOP_INTERNAL_NAME",
        )

    output = list(block)
    declared_locals: set[str] = set()
    aliases: dict[str, str] = {}
    loops: list[BoundedLoopSpec] = []
    loop_number = int(loop_number_start)
    index = 1
    end_body = len(block) - 1

    while index < end_body:
        raw = block[index]
        global_line = start_line + index
        code = _code_before_comment(raw)
        stripped = code.strip().rstrip(";").strip()
        if not stripped:
            index += 1
            continue

        if re.match(r"^for\b", stripped):
            index_name, iteration_values, start, stop, step = _parse_range(code, global_line)
            if index_name in parameters or index_name in declared_locals or index_name in aliases:
                raise BoundedLoopError(
                    f"반복 index가 기존 함수 이름공간과 충돌합니다: {index_name}",
                    global_line,
                    code="LOOP_INDEX_COLLISION",
                )
            loop_depth = _brace_delta(code)
            if loop_depth != 1:
                raise BoundedLoopError("반복문 괄호가 올바르지 않습니다.", global_line, code="BAD_BOUNDED_LOOP_BRACE")
            body_start = index + 1
            cursor = body_start
            body_rows: list[tuple[int, str, str, str]] = []
            while cursor < end_body:
                body_raw = block[cursor]
                body_code = _code_before_comment(body_raw)
                delta = _brace_delta(body_code)
                if delta:
                    loop_depth += delta
                    if loop_depth == 0:
                        if body_code.strip() != "}":
                            raise BoundedLoopError(
                                "반복문 닫는 괄호는 단독 문장이어야 합니다.",
                                start_line + cursor,
                                code="BAD_BOUNDED_LOOP_BRACE",
                            )
                        break
                    raise BoundedLoopError(
                        "bounded loop v1은 중첩 control block을 허용하지 않습니다.",
                        start_line + cursor,
                        code="NESTED_LOOP_UNSUPPORTED",
                    )
                body_text = body_code.strip().rstrip(";").strip()
                if body_text:
                    assignment = re.match(rf"^({IDENTIFIER})\s*=\s*(.+)$", body_text)
                    if not assignment:
                        raise BoundedLoopError(
                            f"반복문 본문은 기존 local accumulator 대입만 허용합니다: {body_text}",
                            start_line + cursor,
                            code="BAD_LOOP_STATEMENT",
                        )
                    target, expression = assignment.groups()
                    if target == index_name:
                        raise BoundedLoopError("반복 index는 읽기 전용입니다.", start_line + cursor, code="LOOP_INDEX_READ_ONLY")
                    if target in parameters or target not in declared_locals:
                        raise BoundedLoopError(
                            f"반복문 대상은 앞에서 선언한 함수 local이어야 합니다: {target}",
                            start_line + cursor,
                            code="LOOP_TARGET_MUST_BE_LOCAL",
                        )
                    body_rows.append((cursor, target, expression.strip(), body_raw))
                cursor += 1
            if cursor >= end_body or loop_depth != 0:
                raise BoundedLoopError("반복문의 닫는 괄호가 없습니다.", global_line, code="UNCLOSED_BOUNDED_LOOP")
            if not body_rows:
                raise BoundedLoopError("반복문 본문이 비어 있습니다.", global_line, code="EMPTY_BOUNDED_LOOP")

            target_order: list[str] = []
            first_target_line: dict[str, int] = {}
            for row_index, target, _expression, _raw in body_rows:
                if target not in first_target_line:
                    target_order.append(target)
                    first_target_line[target] = row_index

            current_values: dict[str, ast.AST] = {
                target: ast.Name(id=aliases.get(target, target), ctx=ast.Load())
                for target in target_order
            }
            for iteration_value in iteration_values:
                for row_index, target, expression, _raw in body_rows:
                    node = _parse_expression(expression, start_line + row_index)
                    node = _NameSubstituter(
                        aliases=aliases,
                        values=current_values,
                        index_name=index_name,
                        index_value=iteration_value,
                    ).visit(node)
                    ast.fix_missing_locations(node)
                    if _node_size(node) > MAX_EXPANDED_AST_NODES:
                        raise BoundedLoopError(
                            "반복문 compile-time 전개식이 안전 한도를 초과했습니다.",
                            start_line + row_index,
                            code="LOOP_EXPANSION_LIMIT",
                        )
                    current_values[target] = node

            loop_number += 1
            output[index] = ""
            for row in range(body_start, cursor + 1):
                output[row] = ""
            generated_aliases: dict[str, str] = {}
            for target in target_order:
                if not iteration_values:
                    continue
                generated = f"{INTERNAL_PREFIX}{loop_number}_{target}"
                generated_aliases[target] = generated
                row_index = first_target_line[target]
                indent_source = block[row_index]
                indent = indent_source[: len(indent_source) - len(indent_source.lstrip())]
                expression = ast.unparse(current_values[target])
                output[row_index] = f"{indent}{generated} = {expression}"
            aliases.update(generated_aliases)
            loops.append(
                BoundedLoopSpec(
                    function=function_name,
                    index=index_name,
                    start=start,
                    stop=stop,
                    step=step,
                    iterations=len(iteration_values),
                    targets=tuple(target_order),
                    line=global_line,
                )
            )
            index = cursor + 1
            continue

        output[index] = _rewrite_plain_function_line(raw, global_line, aliases)
        local_match = re.match(rf"^({IDENTIFIER})\s*=\s*(.+)$", stripped)
        if local_match:
            declared_locals.add(local_match.group(1))
        index += 1

    return output, loops, loop_number


def lower_bounded_loops(source: str) -> LoweredBoundedLoops:
    """Compile pure bounded loops inside user-defined functions into expressions.

    v1 intentionally allows loops only inside user-function bodies and only for
    reassignment of locals declared before the loop.  Bounds are integer
    literals and the iteration count is capped.  Source line count is preserved.
    """
    if not isinstance(source, str):
        raise TypeError("DSL source는 문자열이어야 합니다.")
    lines = source.splitlines()
    if not lines:
        return LoweredBoundedLoops(source=source, loops=())

    active_for = [
        index
        for index, raw in enumerate(lines)
        if re.match(r"^\s*for\b", _code_before_comment(raw))
    ]
    if not active_for:
        return LoweredBoundedLoops(source=source, loops=())

    output = list(lines)
    covered: set[int] = set()
    loop_specs: list[BoundedLoopSpec] = []
    loop_number = 0
    depth = 0
    index = 0
    function_header = re.compile(rf"^\s*function\s+({IDENTIFIER})\s*\((.*?)\)\s*\{{\s*$")

    while index < len(lines):
        raw = lines[index]
        code = _code_before_comment(raw)
        current_depth = depth
        header = function_header.match(code) if current_depth == 1 else None
        if header:
            function_name, raw_parameters = header.groups()
            parameters = tuple(item.strip() for item in raw_parameters.split(",") if item.strip())
            function_depth = _brace_delta(code)
            cursor = index + 1
            while cursor < len(lines) and function_depth > 0:
                function_depth += _brace_delta(_code_before_comment(lines[cursor]))
                cursor += 1
            if function_depth != 0:
                # Let the user-function lowerer own malformed declarations when
                # they do not contain a bounded loop.  With a loop present the
                # context itself cannot be resolved safely.
                if any(index < item < cursor for item in active_for):
                    raise BoundedLoopError("반복문이 있는 사용자 함수의 닫는 괄호가 없습니다.", index + 1, code="UNCLOSED_LOOP_FUNCTION")
                depth += _brace_delta(code)
                index += 1
                continue
            end = cursor - 1
            contained = [item for item in active_for if index < item < end]
            if contained:
                lowered, found, loop_number = _lower_function_block(
                    lines[index:end + 1],
                    start_line=index + 1,
                    function_name=function_name,
                    parameters=parameters,
                    loop_number_start=loop_number,
                )
                output[index:end + 1] = lowered
                covered.update(contained)
                loop_specs.extend(found)
            index = end + 1
            # A complete function block starts and ends at strategy depth 1.
            continue
        depth += _brace_delta(code)
        index += 1

    uncovered = [item for item in active_for if item not in covered]
    if uncovered:
        line = uncovered[0] + 1
        raise BoundedLoopError(
            "bounded loop v1은 사용자 정의 함수 내부에서만 허용합니다.",
            line,
            code="LOOP_SCOPE_UNSUPPORTED",
        )

    suffix = "\n" if source.endswith("\n") else ""
    lowered_source = "\n".join(output) + suffix
    if len(lowered_source.splitlines()) != len(source.splitlines()):
        raise RuntimeError("bounded loop lowering line-count contract 오류")
    return LoweredBoundedLoops(
        source=lowered_source,
        loops=tuple(loop_specs),
    )
