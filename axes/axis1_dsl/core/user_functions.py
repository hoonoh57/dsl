"""Fail-closed user-defined function front-end for AXIS 1 DSL.

User functions are intentionally compiled away before the migrated parser and
runtime execute the strategy.  The v1 contract is pure and expression based:
functions may declare ordered local expressions and one final return expression,
but they cannot mutate strategy state, place orders, branch, loop or recurse.
This keeps the proven migrated execution core unchanged.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import re


IDENTIFIER = r"[A-Za-z_가-힣][\w가-힣]*"
RESERVED_LOCAL_NAMES = {
    "open", "high", "low", "close", "volume", "amount", "open_interest",
    "date", "time", "ctx", "timeframe", "strategy", "function", "return",
    "ta", "math", "logic", "state", "session", "mtf", "user", "order",
}
FUNCTION_NAMESPACE_ROOTS = {"ta", "math", "logic", "state", "session", "mtf", "user"}


class UserFunctionError(ValueError):
    def __init__(self, message: str, line: int = 1, column: int = 1, code: str = "USER_FUNCTION_ERROR"):
        self.line = int(line)
        self.column = int(column)
        self.code = str(code)
        super().__init__(f"line {self.line}, column {self.column}: {message}")


@dataclass(frozen=True)
class UserFunctionLocal:
    name: str
    expression: str
    line: int


@dataclass(frozen=True)
class UserFunctionSpec:
    name: str
    parameters: tuple[str, ...]
    locals: tuple[UserFunctionLocal, ...]
    return_expression: str
    line: int
    return_line: int

    def public_dict(self) -> dict:
        return {
            "name": self.name,
            "parameters": self.parameters,
            "locals": tuple(item.name for item in self.locals),
            "line": self.line,
            "return_line": self.return_line,
            "pure": True,
            "recursive": False,
        }


@dataclass(frozen=True)
class LoweredUserFunctions:
    source: str
    functions: tuple[UserFunctionSpec, ...]

    def manifest(self) -> tuple[dict, ...]:
        return tuple(item.public_dict() for item in self.functions)


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
        raise UserFunctionError(
            f"사용자 함수 수식 문법 오류: {exc.msg}",
            line,
            exc.offset or 1,
            "BAD_USER_FUNCTION_EXPRESSION",
        ) from exc


def _validate_expression_shape(node: ast.AST, line: int) -> None:
    allowed = (
        ast.Expression, ast.Name, ast.Constant, ast.Attribute, ast.Call, ast.keyword,
        ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Subscript, ast.Load,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    )
    for item in ast.walk(node):
        if not isinstance(item, allowed):
            raise UserFunctionError(
                f"사용자 함수에서 허용되지 않는 표현식: {type(item).__name__}",
                line,
                getattr(item, "col_offset", 0) + 1,
                "BAD_USER_FUNCTION_EXPRESSION_NODE",
            )


def _parse_function_block(
    header_line: str,
    body_lines: list[tuple[int, str]],
    line: int,
) -> UserFunctionSpec:
    header = re.match(
        rf"^\s*function\s+({IDENTIFIER})\s*\((.*?)\)\s*\{{\s*$",
        _code_before_comment(header_line),
    )
    if not header:
        raise UserFunctionError("function 이름(인수...) { 형식이 필요합니다.", line, code="BAD_USER_FUNCTION_DECLARATION")
    name, raw_parameters = header.groups()
    if name in RESERVED_LOCAL_NAMES:
        raise UserFunctionError(f"사용자 함수 이름으로 예약 이름을 사용할 수 없습니다: {name}", line, code="RESERVED_USER_FUNCTION_NAME")

    parameters: list[str] = []
    if raw_parameters.strip():
        for raw in raw_parameters.split(","):
            parameter = raw.strip()
            if not re.fullmatch(IDENTIFIER, parameter):
                raise UserFunctionError(f"사용자 함수 인수 이름이 올바르지 않습니다: {parameter}", line, code="BAD_USER_FUNCTION_PARAMETER")
            if parameter in RESERVED_LOCAL_NAMES:
                raise UserFunctionError(f"사용자 함수 인수에 예약 이름을 사용할 수 없습니다: {parameter}", line, code="RESERVED_USER_FUNCTION_PARAMETER")
            if parameter in parameters:
                raise UserFunctionError(f"사용자 함수 인수가 중복되었습니다: {parameter}", line, code="DUPLICATE_USER_FUNCTION_PARAMETER")
            parameters.append(parameter)

    locals_: list[UserFunctionLocal] = []
    declared = set(parameters)
    return_expression = None
    return_line = line
    returned = False

    for body_line, raw in body_lines:
        text = _code_before_comment(raw).strip().rstrip(";").strip()
        if not text:
            continue
        if returned:
            raise UserFunctionError("return 뒤에는 다른 사용자 함수 문장을 둘 수 없습니다.", body_line, code="STATEMENT_AFTER_USER_FUNCTION_RETURN")
        return_match = re.match(r"^return\s+(.+)$", text)
        if return_match:
            return_expression = return_match.group(1).strip()
            return_line = body_line
            node = _parse_expression(return_expression, body_line)
            _validate_expression_shape(node, body_line)
            returned = True
            continue
        local_match = re.match(rf"^({IDENTIFIER})\s*=\s*(.+)$", text)
        if not local_match:
            raise UserFunctionError(
                f"사용자 함수에서 인식할 수 없는 문장: {text}",
                body_line,
                code="BAD_USER_FUNCTION_STATEMENT",
            )
        local_name, expression = local_match.groups()
        if local_name in RESERVED_LOCAL_NAMES:
            raise UserFunctionError(f"사용자 함수 local에 예약 이름을 사용할 수 없습니다: {local_name}", body_line, code="RESERVED_USER_FUNCTION_LOCAL")
        if local_name in declared:
            raise UserFunctionError(f"사용자 함수 local이 중복되었습니다: {local_name}", body_line, code="DUPLICATE_USER_FUNCTION_LOCAL")
        node = _parse_expression(expression.strip(), body_line)
        _validate_expression_shape(node, body_line)
        locals_.append(UserFunctionLocal(local_name, expression.strip(), body_line))
        declared.add(local_name)

    if return_expression is None:
        raise UserFunctionError(f"사용자 함수에는 마지막 return 수식이 필요합니다: {name}", line, code="MISSING_USER_FUNCTION_RETURN")
    return UserFunctionSpec(
        name=name,
        parameters=tuple(parameters),
        locals=tuple(locals_),
        return_expression=return_expression,
        line=line,
        return_line=return_line,
    )


def _validate_scope(spec: UserFunctionSpec, function_names: set[str]) -> None:
    collisions = (set(spec.parameters) | {item.name for item in spec.locals}) & function_names
    if collisions:
        name = sorted(collisions)[0]
        raise UserFunctionError(
            f"사용자 함수의 인수/local은 함수 이름과 같을 수 없습니다: {name}",
            spec.line,
            code="USER_FUNCTION_SCOPE_COLLISION",
        )

    available = set(spec.parameters)
    callable_names = set(function_names) | FUNCTION_NAMESPACE_ROOTS

    def check(expression: str, line: int):
        node = _parse_expression(expression, line)
        for item in ast.walk(node):
            if not isinstance(item, ast.Name):
                continue
            if item.id in available or item.id in callable_names or item.id in {"True", "False"}:
                continue
            raise UserFunctionError(
                f"사용자 함수는 외부 값을 암묵적으로 참조할 수 없습니다: {item.id}",
                line,
                getattr(item, "col_offset", 0) + 1,
                "USER_FUNCTION_FREE_VARIABLE",
            )

    for local in spec.locals:
        check(local.expression, local.line)
        available.add(local.name)
    check(spec.return_expression, spec.return_line)


class _InlineTransformer(ast.NodeTransformer):
    def __init__(self, env: dict[str, ast.AST], specs: dict[str, UserFunctionSpec], stack: tuple[str, ...], line: int):
        self.env = env
        self.specs = specs
        self.stack = stack
        self.line = line

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load) and node.id in self.env:
            return copy.deepcopy(self.env[node.id])
        return node

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in self.specs:
            if node.keywords or any(isinstance(item, ast.Starred) for item in node.args):
                raise UserFunctionError(
                    "사용자 함수 호출 v1은 위치 인수만 허용합니다.",
                    self.line,
                    getattr(node, "col_offset", 0) + 1,
                    "USER_FUNCTION_KEYWORD_UNSUPPORTED",
                )
            args = tuple(self.visit(item) for item in node.args)
            return _instantiate_ast(self.specs[node.func.id], args, self.specs, self.stack, self.line)
        return self.generic_visit(node)


def _instantiate_ast(
    spec: UserFunctionSpec,
    args: tuple[ast.AST, ...],
    specs: dict[str, UserFunctionSpec],
    stack: tuple[str, ...],
    call_line: int,
) -> ast.AST:
    if spec.name in stack:
        cycle = " -> ".join(stack + (spec.name,))
        raise UserFunctionError(f"사용자 함수 재귀호출은 허용하지 않습니다: {cycle}", call_line, code="RECURSIVE_USER_FUNCTION")
    if len(args) != len(spec.parameters):
        raise UserFunctionError(
            f"{spec.name} 인수 개수 오류: {len(args)}개 (필요 {len(spec.parameters)}개)",
            call_line,
            code="BAD_USER_FUNCTION_ARITY",
        )

    next_stack = stack + (spec.name,)
    env = {name: copy.deepcopy(value) for name, value in zip(spec.parameters, args)}
    for local in spec.locals:
        node = _parse_expression(local.expression, local.line)
        node = _InlineTransformer(env, specs, next_stack, local.line).visit(node)
        ast.fix_missing_locations(node)
        env[local.name] = node
    result = _parse_expression(spec.return_expression, spec.return_line)
    result = _InlineTransformer(env, specs, next_stack, spec.return_line).visit(result)
    ast.fix_missing_locations(result)
    return result


def _find_call_close(text: str, opening: int, line: int) -> int:
    depth = 0
    quote = None
    escaped = False
    for index in range(opening, len(text)):
        char = text[index]
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
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise UserFunctionError("사용자 함수 호출의 닫는 괄호가 없습니다.", line, code="UNCLOSED_USER_FUNCTION_CALL")


def _parse_call_arguments(text: str, line: int) -> tuple[ast.AST, ...]:
    try:
        call = ast.parse(f"f({text})", mode="eval").body
    except SyntaxError as exc:
        raise UserFunctionError(
            f"사용자 함수 호출 인수 문법 오류: {exc.msg}",
            line,
            exc.offset or 1,
            "BAD_USER_FUNCTION_CALL",
        ) from exc
    if call.keywords or any(isinstance(item, ast.Starred) for item in call.args):
        raise UserFunctionError("사용자 함수 호출 v1은 위치 인수만 허용합니다.", line, code="USER_FUNCTION_KEYWORD_UNSUPPORTED")
    return tuple(call.args)


def _lower_calls_on_line(text: str, line: int, specs: dict[str, UserFunctionSpec]) -> str:
    output: list[str] = []
    index = 0
    quote = None
    escaped = False
    while index < len(text):
        char = text[index]
        if quote:
            output.append(char)
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
            output.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < len(text) and text[index + 1] == "/":
            output.append(text[index:])
            break
        if char.isalpha() or char == "_" or ("가" <= char <= "힣"):
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] == "_" or ("가" <= text[end] <= "힣")):
                end += 1
            name = text[index:end]
            cursor = end
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            previous = text[index - 1] if index else ""
            if name in specs and cursor < len(text) and text[cursor] == "(" and previous != ".":
                closing = _find_call_close(text, cursor, line)
                args = _parse_call_arguments(text[cursor + 1:closing], line)
                expanded = _instantiate_ast(specs[name], args, specs, (), line)
                output.append(f"({ast.unparse(expanded)})")
                index = closing + 1
                continue
            output.append(text[index:end])
            index = end
            continue
        output.append(char)
        index += 1
    return "".join(output)


def lower_user_functions(source: str) -> LoweredUserFunctions:
    """Remove pure user-function declarations and inline all of their calls.

    Function blocks are replaced by blank lines, preserving original source line
    numbers for diagnostics produced by the migrated parser/semantic/runtime.
    """
    if not isinstance(source, str):
        raise TypeError("DSL source는 문자열이어야 합니다.")
    lines = source.splitlines()
    if not lines:
        return LoweredUserFunctions(source=source, functions=())

    stripped_lines = list(lines)
    specs: dict[str, UserFunctionSpec] = {}
    depth = 0
    index = 0
    while index < len(lines):
        raw = lines[index]
        code = _code_before_comment(raw)
        current_depth = depth
        starts_function = current_depth == 1 and re.match(r"^\s*function\b", code)
        if starts_function:
            header = re.match(rf"^\s*function\s+({IDENTIFIER})\s*\((.*?)\)\s*\{{\s*$", code)
            if not header:
                raise UserFunctionError("function 이름(인수...) { 형식이 필요합니다.", index + 1, code="BAD_USER_FUNCTION_DECLARATION")
            function_depth = _brace_delta(code)
            if function_depth != 1:
                raise UserFunctionError("사용자 함수 선언 괄호가 올바르지 않습니다.", index + 1, code="BAD_USER_FUNCTION_BRACE")
            start = index
            body: list[tuple[int, str]] = []
            index += 1
            while index < len(lines):
                body_code = _code_before_comment(lines[index])
                delta = _brace_delta(body_code)
                if delta:
                    function_depth += delta
                    if function_depth < 0:
                        raise UserFunctionError("사용자 함수 괄호가 올바르지 않습니다.", index + 1, code="BAD_USER_FUNCTION_BRACE")
                    if function_depth == 0:
                        if body_code.strip() != "}":
                            raise UserFunctionError("사용자 함수 닫는 괄호는 단독 문장이어야 합니다.", index + 1, code="BAD_USER_FUNCTION_BRACE")
                        break
                    raise UserFunctionError(
                        "사용자 함수 v1 본문에는 중첩 블록을 허용하지 않습니다.",
                        index + 1,
                        code="USER_FUNCTION_BLOCK_UNSUPPORTED",
                    )
                body.append((index + 1, lines[index]))
                index += 1
            if index >= len(lines) or function_depth != 0:
                raise UserFunctionError("사용자 함수의 닫는 괄호가 없습니다.", start + 1, code="UNCLOSED_USER_FUNCTION")
            spec = _parse_function_block(lines[start], body, start + 1)
            if spec.name in specs:
                raise UserFunctionError(f"사용자 함수가 중복 선언되었습니다: {spec.name}", spec.line, code="DUPLICATE_USER_FUNCTION")
            specs[spec.name] = spec
            for blank in range(start, index + 1):
                stripped_lines[blank] = ""
            index += 1
            continue
        depth += _brace_delta(code)
        index += 1

    function_names = set(specs)
    for spec in specs.values():
        _validate_scope(spec, function_names)

    # Expand every definition once with neutral placeholder inputs.  This makes
    # recursion fail even when the recursive function is never called by the strategy.
    for spec in specs.values():
        placeholders = tuple(ast.Name(id=f"__arg_{i}", ctx=ast.Load()) for i in range(len(spec.parameters)))
        _instantiate_ast(spec, placeholders, specs, (), spec.line)

    lowered_lines = [
        _lower_calls_on_line(raw, line_number, specs) if raw else raw
        for line_number, raw in enumerate(stripped_lines, start=1)
    ]
    suffix = "\n" if source.endswith("\n") else ""
    return LoweredUserFunctions(
        source="\n".join(lowered_lines) + suffix,
        functions=tuple(sorted(specs.values(), key=lambda item: (item.line, item.name))),
    )
