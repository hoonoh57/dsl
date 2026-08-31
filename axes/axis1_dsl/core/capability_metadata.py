"""Machine-readable capability metadata for AXIS 1 DSL functions.

This module is additive.  It does not change migrated parser/runtime behavior.
It describes the execution capabilities already exposed by FUNCTION_SPECS and
Step 5 multi-output contracts, including explicit uncertainty where full
incremental identity has not yet been certified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from axes.axis1_dsl.core.function_registry import FUNCTION_SPECS
from axes.axis1_dsl.core.multi_output import MULTI_OUTPUT_SPECS


INCREMENTAL_NOT_CERTIFIED = "BATCH_AUTHORITATIVE_INCREMENTAL_NOT_YET_CERTIFIED"


@dataclass(frozen=True)
class CapabilityMetadata:
    name: str
    mode: str
    category: str
    signature: str
    output_names: tuple[str, ...]
    output_types: tuple[str, ...]
    lookback: str
    warmup: str
    nan_policy: str
    incremental_identity: str
    reference_source: str
    causality: str

    def validate(self) -> None:
        required = {
            "name": self.name,
            "mode": self.mode,
            "category": self.category,
            "signature": self.signature,
            "lookback": self.lookback,
            "warmup": self.warmup,
            "nan_policy": self.nan_policy,
            "incremental_identity": self.incremental_identity,
            "reference_source": self.reference_source,
            "causality": self.causality,
        }
        missing = [key for key, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"capability metadata 필드 누락: {', '.join(missing)}")
        if not self.output_names or len(self.output_names) != len(self.output_types):
            raise ValueError(f"capability output contract 오류: {self.mode}:{self.name}")
        if any(not str(item).strip() for item in self.output_names + self.output_types):
            raise ValueError(f"capability output metadata 공백: {self.mode}:{self.name}")

    def public_dict(self) -> dict:
        return asdict(self)


def _reference_for(category: str, name: str) -> str:
    if category == "ta":
        return "axes.axis1_dsl.indicators.indicators"
    if category == "user":
        return "axes.axis1_dsl.indicators.user_indicators"
    if category == "state":
        return "axes.axis1_dsl.runtime.state"
    if category == "mtf":
        return "axes.axis1_dsl.runtime.multitimeframe"
    return "axes.axis1_dsl.runtime.dsl_runtime"


def _function_policy(name: str, category: str) -> tuple[str, str, str, str]:
    """Return lookback, warmup, NaN policy and causality.

    Every currently registered function is handled explicitly by family.  A new
    registry entry that is not covered here fails during module import instead
    of silently inheriting vague metadata.
    """

    if name in {
        "ta.sma", "ta.ema", "ta.wma", "ta.rma", "ta.ma", "ta.highest",
        "ta.lowest", "ta.sum", "ta.stdev", "ta.roc", "ta.rsi",
        "ta.atr", "ta.nrange", "ta.williams_r", "ta.abs_range",
        "ta.sum_abs_r", "ta.vhf",
    }:
        return (
            "period/optional-bars parameterized history",
            "kernel-defined period warmup",
            "preserve kernel NaN/undefined values",
            "current and past bars only",
        )
    if name in {"ta.adx", "ta.trix", "ta.cci"}:
        return (
            "recursive period-dependent history",
            "kernel-defined recursive warmup",
            "preserve kernel NaN/undefined values",
            "current and past bars only",
        )
    if name in {"ta.crossover", "ta.crossunder"}:
        return (
            "previous bar plus input history",
            "inherits input warmup plus previous-bar requirement",
            "undefined input comparisons do not synthesize values",
            "current and past bars only",
        )
    if name == "ta.jma":
        return (
            "recursive length-dependent history",
            "kernel starts from first bar; stabilization is length-dependent",
            "preserve kernel numeric/trend metadata behavior",
            "current and past bars only",
        )
    if name in {"ta.supertrend", "ta.supertrend_direction"}:
        return (
            "ATR period-dependent recursive history",
            "ATR/kernel-defined warmup",
            "preserve kernel NaN/direction establishment behavior",
            "current and past bars only",
        )
    if name == "ta.macd":
        return (
            "short/long moving-average parameterized history",
            "moving-average kernel-defined warmup",
            "preserve kernel NaN/undefined values",
            "current and past bars only",
        )
    if name == "user.macd_normalized":
        return (
            "short/long/signal moving-average chain",
            "component-specific moving-average chain warmup",
            "preserve component NaN; zero denominator is not default-filled",
            "current and past bars only",
        )
    if name == "ta.shift":
        return (
            "bars offset parameter",
            "offset-sized unavailable prefix",
            "unavailable shifted prefix remains NaN",
            "past bars only",
        )
    if name in {"ta.bars_since", "ta.count_since", "ta.highest_since", "ta.lowest_since", "ta.value_when"}:
        return (
            "event/trigger history",
            "function-specific trigger-history warmup",
            "preserve function-defined pre-trigger undefined values",
            "current and past bars only",
        )
    if category == "math":
        return (
            "input values only",
            "inherits input warmup",
            "inherits numeric input NaN semantics",
            "input causality preserved",
        )
    if name == "logic.ifelse":
        return (
            "input values only",
            "inherits input warmup",
            "selected branch preserves input undefined values",
            "input causality preserved",
        )
    if category == "session":
        return (
            "current/prior session history as required by function",
            "session-boundary dependent",
            "missing prior-session values remain kernel-defined undefined values",
            "current and prior sessions only",
        )
    if category == "state":
        return (
            "ordered state/event history",
            "state-rule dependent",
            "state kernel owns initialization/undefined semantics",
            "ordered current and past state only",
        )
    if category == "mtf":
        return (
            "confirmed parent-timeframe bars",
            "parent-timeframe confirmation dependent",
            "no nearest-time/fill-forward/default synthesis",
            "confirmed parent bars only",
        )
    raise ValueError(f"metadata policy가 없는 FUNCTION_SPECS 항목: {name} ({category})")


def _single_output_capability(name: str):
    spec = FUNCTION_SPECS[name]
    lookback, warmup, nan_policy, causality = _function_policy(name, spec.category)
    item = CapabilityMetadata(
        name=name,
        mode="single_output",
        category=spec.category,
        signature=spec.signature,
        output_names=("value",),
        output_types=(spec.returns,),
        lookback=lookback,
        warmup=warmup,
        nan_policy=nan_policy,
        incremental_identity=INCREMENTAL_NOT_CERTIFIED,
        reference_source=_reference_for(spec.category, name),
        causality=causality,
    )
    item.validate()
    return item


def _multi_output_policy(name: str) -> tuple[str, str, str, str, str]:
    if name == "ta.supertrend":
        return (
            "ATR period-dependent recursive history",
            "ATR/kernel-defined warmup",
            "preserve line NaN and direction establishment behavior",
            "current and past bars only",
            "axes.axis1_dsl.indicators.indicators",
        )
    if name == "ta.bbands":
        return (
            "period parameterized rolling history",
            "period/kernel-defined warmup",
            "preserve rolling kernel NaN/undefined values",
            "current and past bars only",
            "axes.axis1_dsl.core.multi_output + axes.axis1_dsl.indicators.indicators",
        )
    if name == "user.macd_normalized_all":
        return (
            "short/long/signal moving-average chain",
            "component-specific moving-average chain warmup",
            "preserve component NaN; zero denominator is not default-filled",
            "current and past bars only",
            "axes.axis1_dsl.core.multi_output + axes.axis1_dsl.indicators.user_indicators",
        )
    raise ValueError(f"metadata policy가 없는 MULTI_OUTPUT_SPECS 항목: {name}")


def _multi_output_capability(name: str):
    spec = MULTI_OUTPUT_SPECS[name]
    lookback, warmup, nan_policy, causality, reference_source = _multi_output_policy(name)
    category = name.split(".", 1)[0]
    item = CapabilityMetadata(
        name=name,
        mode="multi_output",
        category=category,
        signature=spec.signature,
        output_names=spec.components,
        output_types=spec.component_types,
        lookback=lookback,
        warmup=warmup,
        nan_policy=nan_policy,
        incremental_identity=INCREMENTAL_NOT_CERTIFIED,
        reference_source=reference_source,
        causality=causality,
    )
    item.validate()
    return item


FUNCTION_CAPABILITIES = {
    name: _single_output_capability(name)
    for name in FUNCTION_SPECS
}

MULTI_OUTPUT_CAPABILITIES = {
    name: _multi_output_capability(name)
    for name in MULTI_OUTPUT_SPECS
}


def capability_manifest() -> tuple[dict, ...]:
    items = list(FUNCTION_CAPABILITIES.values()) + list(MULTI_OUTPUT_CAPABILITIES.values())
    return tuple(
        item.public_dict()
        for item in sorted(items, key=lambda value: (value.name, value.mode))
    )


def capability_for(name: str, *, mode: str = "single_output") -> CapabilityMetadata:
    if mode == "single_output":
        return FUNCTION_CAPABILITIES[name]
    if mode == "multi_output":
        return MULTI_OUTPUT_CAPABILITIES[name]
    raise KeyError(f"지원하지 않는 capability mode: {mode}")
