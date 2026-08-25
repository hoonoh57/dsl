"""Causal, one-bar-at-a-time executor for persistent DSL state."""
from __future__ import annotations

import ast
import re
from typing import Dict, Iterable

import numpy as np

from core.dsl_parser import IfNode, SetNode


class BarRuntimeError(ValueError):
    pass


class BarExpression(ast.NodeVisitor):
    def __init__(self, values: Dict[str, object], state: Dict[str, object], index: int):
        self.values, self.state, self.index = values, state, index

    def evaluate(self, text: str):
        text = re.sub(r"\btrue\b", "True", text, flags=re.I)
        text = re.sub(r"\bfalse\b", "False", text, flags=re.I)
        return self.visit(ast.parse(text, mode="eval").body)

    def visit_Name(self, node):
        if node.id in self.state: return self.state[node.id]
        if node.id in self.values:
            value = self.values[node.id]
            return value[self.index] if isinstance(value, np.ndarray) else value
        if node.id == "True": return True
        if node.id == "False": return False
        raise BarRuntimeError(f"정의되지 않은 변수: {node.id}")

    def visit_Constant(self, node): return node.value

    def visit_Subscript(self, node):
        if not isinstance(node.value, ast.Name): raise BarRuntimeError("봉 참조 대상은 변수여야 합니다.")
        offset = self.visit(node.slice)
        if not isinstance(offset, int) or offset < 0: raise BarRuntimeError("과거 참조는 0 이상의 정수여야 합니다.")
        target = self.index - offset
        value = self.values.get(node.value.id)
        if not isinstance(value, np.ndarray): raise BarRuntimeError("과거 참조는 series에만 사용할 수 있습니다.")
        if target < 0: return np.nan
        return value[target]

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        if isinstance(node.op, ast.Not): return not bool(value)
        if isinstance(node.op, ast.USub): return -value
        if isinstance(node.op, ast.UAdd): return value
        raise BarRuntimeError("지원하지 않는 단항 연산자입니다.")

    def visit_BinOp(self, node):
        left, right = self.visit(node.left), self.visit(node.right)
        functions = {ast.Add: lambda a,b:a+b, ast.Sub:lambda a,b:a-b, ast.Mult:lambda a,b:a*b,
                     ast.Div:lambda a,b:a/b, ast.Mod:lambda a,b:a%b, ast.Pow:lambda a,b:a**b}
        fn = functions.get(type(node.op))
        if not fn: raise BarRuntimeError("지원하지 않는 산술 연산자입니다.")
        return fn(left, right)

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            return all(bool(self.visit(value)) for value in node.values)
        return any(bool(self.visit(value)) for value in node.values)

    def visit_Compare(self, node):
        functions = {ast.Eq:lambda a,b:a==b, ast.NotEq:lambda a,b:a!=b, ast.Gt:lambda a,b:a>b,
                     ast.GtE:lambda a,b:a>=b, ast.Lt:lambda a,b:a<b, ast.LtE:lambda a,b:a<=b}
        left = self.visit(node.left)
        for operator, item in zip(node.ops, node.comparators):
            right = self.visit(item); fn = functions.get(type(operator))
            if not fn or not bool(fn(left, right)): return False
            left = right
        return True

    def generic_visit(self, node): raise BarRuntimeError(f"on_bar에서 허용되지 않는 문법: {type(node).__name__}")


def execute_on_bar(values: Dict[str, object], states, statements: Iterable, size: int):
    persistent: Dict[str, object] = {}
    initializer = BarExpression(values, persistent, 0)
    for item in states: persistent[item.name] = initializer.evaluate(item.expression)
    outputs: Dict[str, np.ndarray] = {item.name: np.full(size, np.nan, dtype=object) for item in states}

    def run(items, evaluator):
        for item in items:
            if isinstance(item, SetNode):
                value = evaluator.evaluate(item.expression)
                persistent[item.name] = value
                outputs.setdefault(item.name, np.full(size, np.nan, dtype=object))[evaluator.index] = value
            elif isinstance(item, IfNode):
                run(item.body if bool(evaluator.evaluate(item.condition)) else item.otherwise, evaluator)

    for index in range(size):
        for name, value in persistent.items(): outputs[name][index] = value
        run(statements, BarExpression(values, persistent, index))
        for name, value in persistent.items(): outputs[name][index] = value
    for name, value in outputs.items():
        if all(isinstance(item, (bool, np.bool_)) for item in value): outputs[name] = value.astype(bool)
        elif all(isinstance(item, (int, float, np.number)) for item in value): outputs[name] = value.astype(float)
    values.update(outputs)
    return persistent
