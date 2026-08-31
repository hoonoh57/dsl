"""Dependency classification for assignments that consume persistent on_bar outputs."""
from __future__ import annotations

import ast
import re
from typing import Iterable

from axes.axis1_dsl.core.dsl_parser import IfNode, SetNode, StrategyNode


def expression_names(expression: str) -> set[str]:
    normalized = re.sub(r"\btrue\b", "True", expression, flags=re.I)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.I)
    tree = ast.parse(normalized, mode="eval")
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id not in {"True", "False"}}


def collect_bar_output_names(statements: Iterable) -> set[str]:
    names: set[str] = set()
    for item in statements:
        if isinstance(item, SetNode):
            names.add(item.name)
        elif isinstance(item, IfNode):
            names.update(collect_bar_output_names(item.body))
            names.update(collect_bar_output_names(item.otherwise))
    return names


def partition_assignments(document: StrategyNode):
    """Return assignments executable before and after on_bar state materialization.

    State-dependent status is transitive through other assignments.  Declaration
    order is preserved inside each partition; forward references remain invalid
    and are rejected by the normal semantic/runtime evaluator.
    """
    assignment_by_name = {item.name: item for item in document.assignments}
    dynamic_names = {item.name for item in document.states}
    dynamic_names.update(collect_bar_output_names(document.on_bar))
    memo: dict[str, bool] = {}

    def depends_on_dynamic(name: str, stack: set[str]) -> bool:
        if name in memo:
            return memo[name]
        item = assignment_by_name.get(name)
        if item is None:
            return False
        if name in stack:
            # A cyclic/forward declaration remains a normal undefined-symbol
            # error during ordered evaluation; do not silently legalize it here.
            return False
        refs = expression_names(item.expression)
        if refs & dynamic_names:
            memo[name] = True
            return True
        nested_stack = set(stack)
        nested_stack.add(name)
        result = any(
            depends_on_dynamic(ref, nested_stack)
            for ref in refs
            if ref in assignment_by_name
        )
        memo[name] = result
        return result

    before, after = [], []
    for item in document.assignments:
        (after if depends_on_dynamic(item.name, set()) else before).append(item)
    return before, after
