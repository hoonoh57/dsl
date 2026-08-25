"""Project Stage 1 experiment evidence into the shared generic Chart document contract.

This module owns only Quant/experiment semantics: which series and events should
be requested.  It never imports or calls a chart library.  Chart-native drawing
is owned by the shared Chart SSOT in cascading-feature-solution.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _trading_date(source_time: Any) -> str:
    text = str(source_time)
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    raise ValueError(f"chart trading date를 결정할 수 없습니다: {source_time}")


def _chart_time(source_time: Any):
    text = str(source_time)
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 14:
        parsed = datetime.strptime(digits[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())
    if len(digits) >= 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return text


def _series_points(points):
    output = []
    for point in points or []:
        if "time" not in point or "value" not in point:
            continue
        item = {"time": point["time"], "value": float(point["value"])}
        if point.get("color"):
            item["color"] = str(point["color"])
        output.append(item)
    return output


def build_chart_document(experiment: Dict[str, Any], market: Dict[str, Any]) -> dict:
    result = experiment.get("result", {})
    candles = list(result.get("candles", []))
    times = list(market.get("time", []))
    volumes = list(market.get("volume", []))
    if len(candles) != len(times) or len(candles) != len(volumes):
        raise ValueError("Experiment chart evidence와 canonical market snapshot 길이가 일치하지 않습니다.")

    bars = []
    for index, candle in enumerate(candles):
        source_time = times[index]
        expected_time = _chart_time(source_time)
        candle_time = candle.get("time")
        if candle_time != expected_time:
            raise ValueError(f"chart time projection mismatch at index {index}: {candle_time} != {expected_time}")
        bars.append({
            "tradingDate": _trading_date(source_time),
            "time": candle_time,
            "sourceTime": str(source_time),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": float(volumes[index]),
        })

    panes = {}
    series = []
    for indicator in result.get("indicators", []):
        name = str(indicator.get("name", "")).strip()
        if not name:
            continue
        overlay = indicator.get("overlay") is not False
        pane = "price" if overlay else "indicator"
        if pane != "price":
            panes.setdefault(pane, {"height": 150})
        points = _series_points(indicator.get("data", []))
        if not points:
            continue
        series.append({
            "id": f"indicator:{name}",
            "kind": "line",
            "pane": pane,
            "options": {"inspectionLabel": name, "lineWidth": 2},
            "data": points,
        })

    equity = _series_points(result.get("equity_curve", []))
    if equity:
        panes.setdefault("equity", {"height": 120})
        series.append({
            "id": "account:equity",
            "kind": "line",
            "pane": "equity",
            "options": {"inspectionLabel": "Equity", "lineWidth": 2},
            "data": equity,
        })

    markers = []
    for marker in result.get("markers", []):
        if marker.get("time") is None:
            continue
        markers.append({key: value for key, value in marker.items()
                        if key in {"time", "position", "shape", "color", "text", "size"}})

    return {
        "version": "chart-document/v1",
        "bars": bars,
        "panes": panes,
        "series": series,
        "markers": markers,
        "references": [],
        "geometries": [],
        "meta": {
            "experimentId": experiment.get("id"),
            "rootId": experiment.get("root_id"),
            "strategyName": experiment.get("strategy_name"),
            "dataHash": experiment.get("provenance", {}).get("data_hash"),
        },
    }


def chart_time_for_source(document: dict, source_time: Any):
    needle = str(source_time)
    for bar in document.get("bars", []):
        if str(bar.get("sourceTime")) == needle:
            return bar.get("time")
    return None
