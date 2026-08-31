"""Fail-closed typed multi-output/destructuring front-end for AXIS 1 DSL.

The proven migrated parser/semantic/runtime remain unchanged.  This module adds a
small compiler-lowering layer: registered multi-output calls are type/arity
checked and lowered into ordinary scalar/series assignments before the canonical
DSL parser sees them.  This keeps execution deterministic and prevents feature
work from contaminating the migrated core.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import re
from typing import Callable


IDENTIFIER = r"[A-Za-z_가-힣][\w가-힣]*"
RESERVED_NAMES = {
    "open", "high", "low", "close", "volume", "amount", "open_interest", "date", "time", "ctx", "timeframe"
}


class MultiOutputError(ValueError):
    def __init__(self, message: str, line: int = 1, column: int = 1, code: str = "MULTI_OUTPUT_ERROR"):
        self.line, self.column, self.code = int(line), int(column), str(code)
        super().__init__(f"line {self.line}, column {self.column}: {message}")


@dataclass(frozen=True)
class MultiOutputSpec:
    name: str
    minimum: int
    maximum: int
    components: tuple[str, ...]
    component_types: tuple[str, ...]
    signature: str
    lowerer: Callable[[tuple[str, ...]], tuple[str, ...]]

    def validate(self) -> None:
        if len(self.components) < 2:
            raise ValueError("multi-output spec에는 2개 이상의 component가 필요합니다.")
        if len(self.components) != len(self.component_types):
            raise ValueError("multi-output component/type 개수가 다릅니다.")
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("multi-output arity 범위가 올바르지 않습니다.")


@dataclass(frozen=True)
class MultiOutputBinding:
    line: int
    function: str
    targets: tuple[str, ...]
    components: tuple[str, ...]
    component_types: tuple[str, ...]

    def public_dict(self) -> dict:
        return {
            "line": self.line,
            "function": self.function,
            "targets": self.targets,
            "components": self.components,
            "component_types": self.component_types,
        }


@dataclass(frozen=True)
class LoweredDSL:
    source: str
    bindings: tuple[MultiOutputBinding, ...]
    line_map: tuple[int, ...]

    def remap_error_message(self, message: str) -> str:
        match = re.search(r"\bline\s+(\d+),\s*column\s+(\d+)", str(message))
        if not match:
            return str(message)
        lowered_line = int(match.group(1))
        if lowered_line < 1 or lowered_line > len(self.line_map):
            return str(message)
        original_line = self.line_map[lowered_line - 1]
        return str(message)[: match.start(1)] + str(original_line) + str(message)[match.end(1) :]


def _supertrend(args: tuple[str, ...]) -> tuple[str, ...]:
    joined = ", ".join(args)
    return (
        f"ta.supertrend({joined})",
        f"ta.supertrend_direction({joined})",
    )


def _bbands(args: tuple[str, ...]) -> tuple[str, ...]:
    series = args[0]
    period = args[1] if len(args) >= 2 else "20"
    mult = args[2] if len(args) >= 3 else "2.0"

    # CoreTALib.bbands intentionally has different NaN behavior for its middle
    # and deviation components: sma() treats NaN samples as zero inside its
    # rolling sum, while the direct np.std() window used by bbands keeps the
    # deviation undefined whenever any sample in that window is NaN. Reproduce
    # that exact legacy/kernel contract instead of imposing one shared mask.
    invalid = f"(({series}) != ({series}))"
    finite = f"(({series}) == ({series}))"
    consecutive = f"ta.count_since({invalid}, {finite})"
    undefined = f"ta.value_when(0, {invalid}, ({series}))"
    poison = f"logic.ifelse(({consecutive}) >= ({period}), 0, {undefined})"

    middle = f"ta.sma({series}, {period})"
    deviation_base = f"ta.stdev({series}, {period})"
    deviation = f"({deviation_base}) + ({poison})"
    return (
        f"({middle}) + (({mult}) * ({deviation}))",
        middle,
        f"({middle}) - (({mult}) * ({deviation}))",
    )


def _normalized_macd_all(args: tuple[str, ...]) -> tuple[str, ...]:
    series = args[0]
    rest = args[1:]

    def component(name: str) -> str:
        tail = "" if not rest else ", " + ", ".join(rest)
        return f'user.macd_normalized({series}, "{name}"{tail})'

    return tuple(component(name) for name in ("macd", "signal", "hist", "hist_abs_pct"))


MULTI_OUTPUT_SPECS = {
    item.name: item
    for item in (
        MultiOutputSpec(
            name="ta.supertrend",
            minimum=0,
            maximum=2,
            components=("line", "direction"),
            component_types=("series<number>", "series<number>"),
            signature="line, direction = ta.supertrend([period, multiplier])",
            lowerer=_supertrend,
        ),
        MultiOutputSpec(
            name="ta.bbands",
            minimum=1,
            maximum=3,
            components=("upper", "middle", "lower"),
            component_types=("series<number>", "series<number>", "series<number>"),
            signature="upper, middle, lower = ta.bbands(series[, period, multiplier])",
            lowerer=_bbands,
        ),
        MultiOutputSpec(
            name="user.macd_normalized_all",
            minimum=1,
            maximum=5,
            components=("macd", "signal", "hist", "hist_abs_pct"),
            component_types=("series<number>",) * 4,
            signature="macd, signal, hist, strength = user.macd_normalized_all(series[, short, long, signal, method])",
            lowerer=_normalized_macd_all,
        ),
    )
}
for _spec in MULTI_OUTPUT_SPECS.values():
    _spec.validate()


def _attribute_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    else:
        return None
    return ".".join(reversed(parts))


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


def _call_parts(expression: str, line: int) -> tuple[str, tuple[str, ...]]:
    try:
        node = ast.parse(expression, mode="eval").body
    except SyntaxError as exc:
        raise MultiOutputError(
            f"multi-output 수식 문법 오류: {exc.msg}", line, exc.offset or 1, "BAD_MULTI_OUTPUT_EXPRESSION"
        ) from exc
    if not isinstance(node, ast.Call):
        raise MultiOutputError(
            "multi-output 우변은 등록된 함수 호출 하나여야 합니다.", line, code="MULTI_OUTPUT_CALL_REQUIRED"
        )
    if node.keywords:
        raise MultiOutputError(
            "multi-output v1은 위치 인수만 허용합니다.", line, code="MULTI_OUTPUT_KEYWORD_UNSUPPORTED"
        )
    if any(isinstance(item, ast.Starred) for item in node.args):
        raise MultiOutputError("multi-output *args는 지원하지 않습니다.", line, code="MULTI_OUTPUT_STARRED_UNSUPPORTED")
    name = _attribute_name(node.func)
    if not name:
        raise MultiOutputError("multi-output 호출 대상이 올바르지 않습니다.", line, code="BAD_MULTI_OUTPUT_FUNCTION")
    return name, tuple(ast.unparse(item) for item in node.args)


def lower_multi_output(source: str) -> LoweredDSL:
    """Lower top-level ``a, b = registered.multi_output(...)`` declarations.

    Only strategy top-level declarations are transformed.  on/on_bar bodies are
    deliberately untouched, keeping mutation/event semantics deterministic.
    """

    if not isinstance(source, str):
        raise TypeError("DSL source는 문자열이어야 합니다.")
    lines = source.splitlines()
    if not lines:
        return LoweredDSL(source=source, bindings=(), line_map=())

    destructuring = re.compile(
        rf"^(?P<indent>\s*)(?P<lhs>{IDENTIFIER}(?:\s*,\s*{IDENTIFIER})+)\s*=\s*(?P<rhs>.+?)\s*;?\s*$"
    )
    normal_decl = re.compile(rf"^\s*(?:input\s+)?(?P<name>{IDENTIFIER})\s*=")
    state_decl = re.compile(rf"^\s*state\s+(?P<name>{IDENTIFIER})\s*=")

    depth = 0
    output: list[str] = []
    line_map: list[int] = []
    bindings: list[MultiOutputBinding] = []
    declared: set[str] = set()
    destructured_names: set[str] = set()

    for line_number, raw in enumerate(lines, start=1):
        code = raw.split("//", 1)[0]
        current_depth = depth
        match = destructuring.match(code) if current_depth == 1 else None
        if match:
            targets = tuple(item.strip() for item in match.group("lhs").split(","))
            if len(set(targets)) != len(targets):
                raise MultiOutputError("multi-output 대상 변수가 중복되었습니다.", line_number, code="DUPLICATE_MULTI_OUTPUT_TARGET")
            for target in targets:
                if target in RESERVED_NAMES:
                    raise MultiOutputError(
                        f"multi-output 대상에 예약 이름을 사용할 수 없습니다: {target}",
                        line_number,
                        code="RESERVED_MULTI_OUTPUT_TARGET",
                    )
                if target in declared:
                    raise MultiOutputError(
                        f"변수가 중복 선언되었습니다: {target}", line_number, code="DUPLICATE_MULTI_OUTPUT_SYMBOL"
                    )
            function, args = _call_parts(match.group("rhs").strip(), line_number)
            spec = MULTI_OUTPUT_SPECS.get(function)
            if spec is None:
                raise MultiOutputError(
                    f"등록되지 않은 multi-output 함수: {function}", line_number, code="UNREGISTERED_MULTI_OUTPUT_FUNCTION"
                )
            if not spec.minimum <= len(args) <= spec.maximum:
                raise MultiOutputError(
                    f"{function} 인수 개수 오류: {len(args)}개 (허용 {spec.minimum}~{spec.maximum})",
                    line_number,
                    code="BAD_MULTI_OUTPUT_ARITY",
                )
            if len(targets) != len(spec.components):
                raise MultiOutputError(
                    f"{function}은 {len(spec.components)}개 값을 반환하므로 대상 변수도 {len(spec.components)}개여야 합니다.",
                    line_number,
                    code="BAD_DESTRUCTURING_ARITY",
                )
            expressions = spec.lowerer(args)
            if len(expressions) != len(targets):
                raise RuntimeError(f"multi-output lowerer contract 오류: {function}")
            for target, expression in zip(targets, expressions):
                output.append(f"{match.group('indent')}{target} = {expression}")
                line_map.append(line_number)
                declared.add(target)
                destructured_names.add(target)
            bindings.append(
                MultiOutputBinding(
                    line=line_number,
                    function=function,
                    targets=targets,
                    components=spec.components,
                    component_types=spec.component_types,
                )
            )
        else:
            if current_depth == 1:
                declaration = state_decl.match(code) or normal_decl.match(code)
                if declaration:
                    name = declaration.group("name")
                    if name != "timeframe":
                        if name in destructured_names:
                            raise MultiOutputError(
                                f"변수가 중복 선언되었습니다: {name}", line_number, code="DUPLICATE_MULTI_OUTPUT_SYMBOL"
                            )
                        declared.add(name)
            output.append(raw)
            line_map.append(line_number)
        depth += _brace_delta(code)

    suffix = "\n" if source.endswith("\n") else ""
    return LoweredDSL(source="\n".join(output) + suffix, bindings=tuple(bindings), line_map=tuple(line_map))


def multi_output_manifest() -> tuple[dict, ...]:
    return tuple(
        {
            "name": spec.name,
            "minimum": spec.minimum,
            "maximum": spec.maximum,
            "components": spec.components,
            "component_types": spec.component_types,
            "signature": spec.signature,
        }
        for spec in MULTI_OUTPUT_SPECS.values()
    )
