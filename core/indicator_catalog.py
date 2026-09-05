"""Authoritative machine-readable catalog for user-selectable DSL indicators.

The catalog owns indicator identity, editable parameter contracts and the exact
DSL expression emitted for WYSIWYG consumers.  It deliberately does not
calculate indicator values; calculation remains in ``core.indicators`` through
the normal DSL runtime path.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Tuple

from core.function_registry import FUNCTION_SPECS


INDICATOR_CATALOG_SCHEMA = "dsl_indicator_catalog/v1"


@dataclass(frozen=True)
class IndicatorParameterSpec:
    name: str
    label: str
    value_type: str
    default: int | float
    minimum: int | float | None = None
    maximum: int | float | None = None
    exclusive_minimum: bool = False

    def validate(self, value: Any) -> int | float:
        if isinstance(value, bool):
            raise ValueError(f"{self.name}은 숫자여야 합니다.")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{self.name}은 숫자여야 합니다.") from exc
        if not math.isfinite(number):
            raise ValueError(f"{self.name}은 유한한 숫자여야 합니다.")
        if self.value_type == "integer":
            if not number.is_integer():
                raise ValueError(f"{self.name}은 정수여야 합니다.")
            result: int | float = int(number)
        elif self.value_type == "number":
            result = number
        else:
            raise ValueError(f"지원하지 않는 parameter type: {self.value_type}")
        if self.minimum is not None:
            if self.exclusive_minimum and result <= self.minimum:
                raise ValueError(f"{self.name}은 {self.minimum}보다 커야 합니다.")
            if not self.exclusive_minimum and result < self.minimum:
                raise ValueError(f"{self.name}은 {self.minimum} 이상이어야 합니다.")
        if self.maximum is not None and result > self.maximum:
            raise ValueError(f"{self.name}은 {self.maximum} 이하여야 합니다.")
        return result

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.value_type,
            "default": self.default,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "exclusive_minimum": self.exclusive_minimum,
        }


@dataclass(frozen=True)
class IndicatorSpec:
    id: str
    title: str
    capability: str
    source_fields: Tuple[str, ...]
    parameters: Tuple[IndicatorParameterSpec, ...]
    expression_template: str
    output_kind: str

    def resolve_parameters(self, values: Mapping[str, Any] | None = None) -> dict[str, int | float]:
        supplied = dict(values or {})
        known = {parameter.name for parameter in self.parameters}
        unknown = sorted(set(supplied) - known)
        if unknown:
            raise ValueError(f"지원하지 않는 {self.id} parameter: {', '.join(unknown)}")
        return {
            parameter.name: parameter.validate(supplied.get(parameter.name, parameter.default))
            for parameter in self.parameters
        }

    def expression(self, values: Mapping[str, Any] | None = None) -> str:
        params = self.resolve_parameters(values)
        formatted = {name: _dsl_number(value) for name, value in params.items()}
        return self.expression_template.format(**formatted)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": INDICATOR_CATALOG_SCHEMA,
            "id": self.id,
            "title": self.title,
            "capability": self.capability,
            "signature": FUNCTION_SPECS[self.capability].signature,
            "source_fields": list(self.source_fields),
            "parameters": [parameter.public_dict() for parameter in self.parameters],
            "default_parameters": self.resolve_parameters(),
            "default_dsl_expression": self.expression(),
            "output_kind": self.output_kind,
        }


def _dsl_number(value: int | float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return format(number, ".15g")


_INDICATORS: Tuple[IndicatorSpec, ...] = (
    IndicatorSpec(
        id="jma",
        title="JMA",
        capability="ta.jma",
        source_fields=("close",),
        parameters=(
            IndicatorParameterSpec("length", "Length", "integer", 20, minimum=1),
            IndicatorParameterSpec("phase", "Phase", "number", 0, minimum=-100, maximum=100),
            IndicatorParameterSpec("power", "Power", "integer", 2, minimum=1),
        ),
        expression_template="ta.jma(close, {length}, {phase}, {power})",
        output_kind="trend_series",
    ),
    IndicatorSpec(
        id="supertrend",
        title="Supertrend",
        capability="ta.supertrend",
        source_fields=("high", "low", "close"),
        parameters=(
            IndicatorParameterSpec("period", "ATR Period", "integer", 10, minimum=1),
            IndicatorParameterSpec("multiplier", "Multiplier", "number", 3.0, minimum=0.0, exclusive_minimum=True),
        ),
        expression_template="ta.supertrend({period}, {multiplier})",
        output_kind="trend_series",
    ),
    IndicatorSpec(
        id="atr",
        title="ATR",
        capability="ta.atr",
        source_fields=("high", "low", "close"),
        parameters=(IndicatorParameterSpec("period", "Period", "integer", 14, minimum=1),),
        expression_template="ta.atr({period})",
        output_kind="series<number>",
    ),
)


def indicator_specs() -> Tuple[IndicatorSpec, ...]:
    return _INDICATORS


def get_indicator_spec(indicator_id: str) -> IndicatorSpec:
    normalized = str(indicator_id).strip().lower()
    for item in _INDICATORS:
        if item.id == normalized:
            return item
    raise KeyError(indicator_id)


def indicator_catalog_payload() -> dict[str, Any]:
    return {
        "schema": INDICATOR_CATALOG_SCHEMA,
        "indicators": [item.public_dict() for item in _INDICATORS],
    }
