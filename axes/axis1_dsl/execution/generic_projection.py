"""Generic chart-projection metadata for AXIS 1 execution results.

This layer never recalculates indicators.  It only annotates the numeric series
already emitted by the migrated backtest and joins them with optional multi-output
binding metadata produced by the additive DSL front-end.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from axes.axis1_dsl.core.multi_output import MultiOutputBinding


PROJECTION_SCHEMA = "axis1_generic_projection/v1"


class ProjectionError(ValueError):
    pass


def _projection_kind(value_type: str) -> str:
    kind = str(value_type).strip().lower()
    return {
        "series<number>": "numeric_series",
        "series<bool>": "condition_series",
        "series<string>": "label_series",
        "scalar<number>": "scalar_number",
        "scalar<bool>": "scalar_condition",
        "string": "scalar_string",
    }.get(kind, "unknown")


def _multi_output_targets(bindings: Iterable[MultiOutputBinding]) -> dict[str, dict[str, Any]]:
    targets: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, MultiOutputBinding):
            raise ProjectionError("multi-output projection binding 형식이 올바르지 않습니다.")
        lengths = {len(binding.targets), len(binding.components), len(binding.component_types)}
        if len(lengths) != 1:
            raise ProjectionError("multi-output projection binding component contract가 올바르지 않습니다.")
        for target, component, value_type in zip(
            binding.targets,
            binding.components,
            binding.component_types,
        ):
            if target in targets:
                raise ProjectionError(f"projection target이 중복되었습니다: {target}")
            targets[target] = {
                "function": binding.function,
                "component": component,
                "value_type": value_type,
                "line": binding.line,
            }
    return targets


def attach_generic_projection(
    result: dict[str, Any],
    bindings: Iterable[MultiOutputBinding] = (),
) -> dict[str, Any]:
    """Attach a non-computing projection manifest to one backtest result.

    Existing ``indicators`` data remains authoritative.  Missing multi-output
    targets are represented as unavailable instead of being synthesized from
    defaults, fill-forward values, or a second indicator calculation.
    """

    if not isinstance(result, dict):
        raise ProjectionError("projection 대상 backtest result는 dict여야 합니다.")
    indicators = result.get("indicators")
    if not isinstance(indicators, list):
        raise ProjectionError("backtest result indicators가 list여야 합니다.")

    target_meta = _multi_output_targets(tuple(bindings))
    items: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    projected_multi_output = 0

    for index, indicator in enumerate(indicators):
        if not isinstance(indicator, dict):
            raise ProjectionError("indicator projection item은 dict여야 합니다.")
        name = str(indicator.get("name") or "").strip()
        if not name:
            raise ProjectionError("indicator projection item에 name이 필요합니다.")
        if name in seen_names:
            raise ProjectionError(f"indicator projection name이 중복되었습니다: {name}")
        seen_names.add(name)

        metadata = target_meta.get(name)
        if metadata is None:
            value_type = "series<number>"
            source = {"kind": "assignment"}
        else:
            value_type = metadata["value_type"]
            source = {
                "kind": "multi_output_component",
                "function": metadata["function"],
                "component": metadata["component"],
                "line": metadata["line"],
            }
            projected_multi_output += 1

        overlay = bool(indicator.get("overlay"))
        direction_colored = bool(indicator.get("direction_colored"))
        projection_id = f"series:{name}"
        projection_kind = _projection_kind(value_type)
        pane = "overlay" if overlay else "pane"
        style = "direction_line" if direction_colored else "line"

        indicator["projection_id"] = projection_id
        indicator["projection_kind"] = projection_kind
        indicator["projection_pane"] = pane

        items.append(
            {
                "id": projection_id,
                "name": name,
                "value_type": value_type,
                "kind": projection_kind,
                "available": True,
                "indicator_index": index,
                "pane": pane,
                "style": style,
                "direction_colored": direction_colored,
                "source": source,
            }
        )

    for target, metadata in target_meta.items():
        if target in seen_names:
            continue
        items.append(
            {
                "id": f"series:{target}",
                "name": target,
                "value_type": metadata["value_type"],
                "kind": _projection_kind(metadata["value_type"]),
                "available": False,
                "indicator_index": None,
                "pane": None,
                "style": None,
                "direction_colored": False,
                "source": {
                    "kind": "multi_output_component",
                    "function": metadata["function"],
                    "component": metadata["component"],
                    "line": metadata["line"],
                },
            }
        )

    result["projection"] = {
        "schema": PROJECTION_SCHEMA,
        "items": items,
        "multi_output_target_count": len(target_meta),
        "projected_multi_output_target_count": projected_multi_output,
        "policy": "EXECUTION_OUTPUT_ONLY_NO_RECOMPUTE_NO_DEFAULT",
    }

    diagnostics = result.setdefault("diagnostics", {})
    if not isinstance(diagnostics, dict):
        raise ProjectionError("backtest diagnostics는 dict여야 합니다.")
    diagnostics["projection"] = {
        "schema": PROJECTION_SCHEMA,
        "item_count": len(items),
        "multi_output_target_count": len(target_meta),
        "projected_multi_output_target_count": projected_multi_output,
        "policy": "EXECUTION_OUTPUT_ONLY_NO_RECOMPUTE_NO_DEFAULT",
    }
    return result
