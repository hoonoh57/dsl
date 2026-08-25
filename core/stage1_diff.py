"""Deterministic, syntax-aware-enough DSL change summaries for Stage 1 review.

The diff is evidence only; it never rewrites or validates product semantics.
Validation remains the parser/semantic/runtime responsibility.
"""
from __future__ import annotations

import difflib
import re
from typing import Dict, Any

from core.dsl_parser import DSLParser


def _assignment_map(source: str) -> dict[str, str]:
    document = DSLParser.parse(source)
    values = {item.name: item.expression.strip() for item in document.assignments}
    for item in document.states:
        values[f"state:{item.name}"] = item.expression.strip()
    return values


def _event_signatures(source: str) -> list[str]:
    document = DSLParser.parse(source)
    output = []
    for event in document.events:
        commands = ",".join(order.command for order in event.orders)
        output.append(f"on({event.condition.strip()})->{commands}")
    return output


def summarize_dsl_change(before: str, after: str, *, max_diff_lines: int = 120) -> Dict[str, Any]:
    before_doc = DSLParser.parse(before)
    after_doc = DSLParser.parse(after)
    left = _assignment_map(before)
    right = _assignment_map(after)
    added = {name: right[name] for name in sorted(set(right) - set(left))}
    removed = {name: left[name] for name in sorted(set(left) - set(right))}
    changed = {
        name: {"before": left[name], "after": right[name]}
        for name in sorted(set(left) & set(right))
        if left[name] != right[name]
    }
    before_events = _event_signatures(before)
    after_events = _event_signatures(after)
    unified = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(), fromfile="before.dsl", tofile="after.dsl", lineterm=""
    ))
    truncated = len(unified) > max_diff_lines
    return {
        "schema": "stage1_dsl_change/v1",
        "strategy_name_changed": before_doc.name != after_doc.name,
        "before_strategy_name": before_doc.name,
        "after_strategy_name": after_doc.name,
        "timeframe_changed": before_doc.timeframe != after_doc.timeframe,
        "before_timeframe": before_doc.timeframe,
        "after_timeframe": after_doc.timeframe,
        "added_assignments": added,
        "removed_assignments": removed,
        "changed_assignments": changed,
        "events_changed": before_events != after_events,
        "before_events": before_events,
        "after_events": after_events,
        "changed_assignment_count": len(added) + len(removed) + len(changed),
        "unified_diff": unified[:max_diff_lines],
        "diff_truncated": truncated,
    }


def major_change_count(summary: Dict[str, Any]) -> int:
    count = int(summary.get("changed_assignment_count", 0))
    if summary.get("events_changed"):
        count += 1
    if summary.get("timeframe_changed"):
        count += 1
    return count
