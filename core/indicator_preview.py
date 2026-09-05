"""Authoritative WYSIWYG indicator evaluation on caller-supplied visible bars.

The preview path deliberately compiles the catalog's exact DSL expression
through ``DSLRuntime``. It does not dispatch to TA implementations directly,
so Chart consumers cannot acquire a parallel semantic calculation path.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from core.backtest import _validate_market
from core.dsl_runtime import DSLRuntime
from core.indicator_catalog import get_indicator_spec


INDICATOR_PREVIEW_SCHEMA = "dsl_indicator_preview/v1"
_PREVIEW_VALUE_NAME = "indicator_value"


def _market_from_bars(bars: Sequence[Mapping[str, Any]]) -> dict[str, list[Any]]:
    if isinstance(bars, (str, bytes)) or not isinstance(bars, Sequence):
        raise ValueError("bars는 순서가 있는 봉 배열이어야 합니다.")
    rows = list(bars)
    if len(rows) < 2:
        raise ValueError("indicator preview에는 최소 2개 봉이 필요합니다.")

    market: dict[str, list[Any]] = {
        "time": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
    }
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"bars[{index}]는 object여야 합니다.")
        raw_time = row.get("time", row.get("tradingDate"))
        if raw_time is None or str(raw_time).strip() == "":
            raise ValueError(f"bars[{index}]에 time 또는 tradingDate가 필요합니다.")
        market["time"].append(raw_time)
        for field in ("open", "high", "low", "close", "volume"):
            if field not in row:
                raise ValueError(f"bars[{index}]에 {field}가 필요합니다.")
            market[field].append(row[field])
    return market


def _preview_dsl(expression: str, timeframe: str) -> str:
    return (
        'strategy "IndicatorCatalogPreview" {\n'
        f'    timeframe = "{str(timeframe).strip()}"\n'
        f"    {_PREVIEW_VALUE_NAME} = {expression}\n"
        "}"
    )


def evaluate_indicator(
    indicator_id: str,
    *,
    parameters: Mapping[str, Any] | None,
    timeframe: str,
    bars: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate one catalog indicator on the exact supplied bar sequence."""
    spec = get_indicator_spec(indicator_id)
    expression = spec.expression(parameters)
    dsl_code = _preview_dsl(expression, timeframe)
    market = _market_from_bars(bars)
    numeric = _validate_market(market)
    compiled = DSLRuntime.compile(dsl_code, numeric)
    value = compiled.values.get(_PREVIEW_VALUE_NAME)
    if not isinstance(value, np.ndarray) or value.dtype == bool:
        raise ValueError(f"indicator preview가 numeric series를 생성하지 못했습니다: {spec.id}")
    if len(value) != len(market["time"]):
        raise ValueError("indicator preview 결과 길이가 입력 bars와 일치하지 않습니다.")

    directions = getattr(value, "trend_colors", None)
    direction_colored = isinstance(directions, np.ndarray) and len(directions) == len(value)
    points: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        try:
            number = float(raw)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(number):
            continue
        point: dict[str, Any] = {"time": market["time"][index], "value": number}
        if direction_colored:
            point["direction"] = 1 if float(directions[index]) >= 0 else -1
        points.append(point)

    return {
        "schema": INDICATOR_PREVIEW_SCHEMA,
        "indicator_id": spec.id,
        "title": spec.title,
        "timeframe": compiled.timeframe,
        "parameters": spec.resolve_parameters(parameters),
        "dsl_expression": expression,
        "dsl_code": dsl_code,
        "output_kind": spec.output_kind,
        "renderer": spec.renderer.public_dict(),
        "direction_colored": direction_colored,
        "points": points,
        "bar_count": len(market["time"]),
    }
