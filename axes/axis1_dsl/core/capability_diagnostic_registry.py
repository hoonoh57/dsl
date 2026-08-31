"""Machine-readable AXIS 1 capability and diagnostic registry.

Step 6 is intentionally declarative.  It aggregates already-proven function
metadata and explicit feature/diagnostic contracts without importing execution
kernels, providers, the migrated backtest engine, or the frozen legacy core.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Mapping

from axes.axis1_dsl.core.capability_metadata import capability_manifest


REGISTRY_SCHEMA = "axis1_capability_diagnostic_registry/v1"
CAPABILITY_STATUSES = frozenset(
    {
        "SUPPORTED",
        "SUPPORTED_WITH_BOUNDARY",
        "VERIFICATION_ONLY",
        "NOT_SUPPORTED",
        "NOT_CERTIFIED",
    }
)
SUPPORTED_STATUSES = frozenset({"SUPPORTED", "SUPPORTED_WITH_BOUNDARY"})


class CapabilityRegistryError(ValueError):
    def __init__(self, message: str, code: str = "CAPABILITY_REGISTRY_ERROR"):
        self.code = str(code)
        super().__init__(message)


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    kind: str
    status: str
    version: str
    summary: str
    authority: str
    deterministic: bool
    causal: bool
    support_scope: str
    verification: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    details: Mapping[str, object] | None = None

    def validate(self) -> None:
        if not self.capability_id.strip():
            raise CapabilityRegistryError("capability_id is required", "BAD_CAPABILITY_ID")
        if self.status not in CAPABILITY_STATUSES:
            raise CapabilityRegistryError(
                f"unsupported capability status: {self.status}", "BAD_CAPABILITY_STATUS"
            )
        for label, value in (
            ("kind", self.kind),
            ("version", self.version),
            ("summary", self.summary),
            ("authority", self.authority),
            ("support_scope", self.support_scope),
        ):
            if not str(value).strip():
                raise CapabilityRegistryError(
                    f"capability field is empty: {self.capability_id}.{label}",
                    "BAD_CAPABILITY_RECORD",
                )
        if not self.verification:
            raise CapabilityRegistryError(
                f"verification evidence is required: {self.capability_id}",
                "CAPABILITY_EVIDENCE_REQUIRED",
            )

    def public_dict(self) -> dict:
        value = asdict(self)
        if value["details"] is None:
            value["details"] = {}
        return value


@dataclass(frozen=True)
class DiagnosticRecord:
    diagnostic_id: str
    path: str
    producer: str
    authority: str
    value_shape: str
    required_fields: tuple[str, ...]
    semantics: str
    stability: str = "v1"

    def validate(self) -> None:
        for label, value in (
            ("diagnostic_id", self.diagnostic_id),
            ("path", self.path),
            ("producer", self.producer),
            ("authority", self.authority),
            ("value_shape", self.value_shape),
            ("semantics", self.semantics),
            ("stability", self.stability),
        ):
            if not str(value).strip():
                raise CapabilityRegistryError(
                    f"diagnostic field is empty: {self.diagnostic_id}.{label}",
                    "BAD_DIAGNOSTIC_RECORD",
                )

    def public_dict(self) -> dict:
        return asdict(self)


def _function_records() -> tuple[CapabilityRecord, ...]:
    records: list[CapabilityRecord] = []
    for item in capability_manifest():
        name = str(item["name"])
        mode = str(item["mode"])
        capability_id = f"function:{mode}:{name}"
        records.append(
            CapabilityRecord(
                capability_id=capability_id,
                kind="function",
                status="SUPPORTED",
                version="v1",
                summary=f"Registered AXIS 1 DSL function contract for {name} ({mode})",
                authority=str(item["reference_source"]),
                deterministic=True,
                causal=True,
                support_scope=str(item["signature"]),
                verification=(
                    "test_axis1_capability_metadata.py",
                    "test_axis1_reference_differential.py",
                ),
                limitations=(str(item["incremental_identity"]),),
                details={
                    "name": name,
                    "mode": mode,
                    "category": item["category"],
                    "signature": item["signature"],
                    "output_names": tuple(item["output_names"]),
                    "output_types": tuple(item["output_types"]),
                    "lookback": item["lookback"],
                    "warmup": item["warmup"],
                    "nan_policy": item["nan_policy"],
                    "incremental_identity": item["incremental_identity"],
                    "reference_source": item["reference_source"],
                    "causality": item["causality"],
                },
            )
        )
    return tuple(records)


FEATURE_CAPABILITIES = (
    CapabilityRecord(
        "dsl.multi_output",
        "dsl_feature",
        "SUPPORTED",
        "v1",
        "Typed multi-output return and destructuring for registered contracts.",
        "axes.axis1_dsl.core.multi_output",
        True,
        True,
        "Registered multi-output calls only; exact target arity and component types.",
        ("test_axis1_multi_output.py",),
    ),
    CapabilityRecord(
        "dsl.user_functions",
        "dsl_feature",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Pure user-defined functions lowered before migrated runtime execution.",
        "axes.axis1_dsl.core.user_functions",
        True,
        True,
        "Compile-time pure functions; no runtime registration or hidden mutable scope.",
        ("test_axis1_user_functions.py",),
    ),
    CapabilityRecord(
        "dsl.bounded_loops",
        "dsl_feature",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Compile-time bounded loops with a fixed iteration ceiling.",
        "axes.axis1_dsl.core.bounded_loops",
        True,
        True,
        "Loop bounds are resolved before execution; dynamic/unbounded loops are rejected.",
        ("test_axis1_bounded_loops.py",),
    ),
    CapabilityRecord(
        "runtime.parent_context",
        "runtime",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Read-only exact-time parent context binding.",
        "axes.axis1_dsl.runtime.dsl_context",
        True,
        True,
        "Exact target-time alignment only; no nearest-time, fill-forward, interpolation, or default synthesis.",
        ("test_axis1_mtf_context_parity.py", "test_axis1_full_engine_parity.py"),
    ),
    CapabilityRecord(
        "runtime.mtf_confirmed",
        "runtime",
        "SUPPORTED",
        "v1",
        "Confirmed higher-timeframe series without repainting incomplete parent bars.",
        "axes.axis1_dsl.runtime.multitimeframe",
        True,
        True,
        "Confirmed parent bars only.",
        ("test_axis1_mtf_context_parity.py", "test_axis1_full_engine_parity.py"),
    ),
    CapabilityRecord(
        "runtime.intrabar_state",
        "runtime",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Transactional on_tick/on_fill provisional state with commit and rollback.",
        "axes.axis1_dsl.runtime.intrabar_lifecycle",
        True,
        True,
        "State mutation only; no indicator recomputation, provider access, or order placement inside handlers.",
        ("test_axis1_intrabar_lifecycle.py", "test_axis1_full_engine_parity.py"),
    ),
    CapabilityRecord(
        "execution.partial_fills",
        "execution",
        "SUPPORTED",
        "v1",
        "Cumulative partial-fill order lifecycle and partial-exit accounting.",
        "axes.axis1_dsl.execution.partial_execution",
        True,
        True,
        "Separate execution session; migrated whole-fill batch engine remains unchanged.",
        ("test_axis1_partial_execution.py", "test_axis1_full_engine_parity.py"),
    ),
    CapabilityRecord(
        "execution.pyramiding",
        "execution",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Same-direction multi-lot pyramiding with deterministic FIFO or targeted lot exits.",
        "axes.axis1_dsl.execution.pyramiding_execution",
        True,
        True,
        "No simultaneous long/short hedge; bounded active lot count.",
        ("test_axis1_pyramiding_execution.py", "test_axis1_full_engine_parity.py"),
    ),
    CapabilityRecord(
        "execution.hedging",
        "execution",
        "NOT_SUPPORTED",
        "v1",
        "Simultaneous long and short exposure is intentionally rejected.",
        "axes.axis1_dsl.execution.pyramiding_execution",
        True,
        True,
        "Opposite-direction exposure while a cycle is open fails closed.",
        ("test_axis1_pyramiding_execution.py",),
    ),
    CapabilityRecord(
        "projection.generic",
        "projection",
        "SUPPORTED_WITH_BOUNDARY",
        "v1",
        "Non-computing projection manifest over execution-produced series.",
        "axes.axis1_dsl.execution.generic_projection",
        True,
        True,
        "Projection consumes existing output only and never recomputes missing values.",
        ("test_axis1_generic_projection.py",),
    ),
    CapabilityRecord(
        "verification.reference_differential",
        "verification",
        "VERIFICATION_ONLY",
        "v1",
        "Independent NumPy reference differential suite for registered TA/user functions.",
        "tests.axis1_reference_indicators",
        True,
        True,
        "Test-side certification only; not a production calculation authority.",
        ("test_axis1_reference_differential.py",),
    ),
    CapabilityRecord(
        "verification.batch_stream_parity",
        "verification",
        "VERIFICATION_ONLY",
        "v1",
        "Causal prefix and ordered event-tape parity certification.",
        "axes.axis1_dsl.execution.full_engine_parity",
        True,
        True,
        "Correctness oracle; not a performance-optimized incremental engine.",
        ("test_axis1_full_engine_parity.py",),
    ),
    CapabilityRecord(
        "runtime.optimized_incremental_kernel",
        "runtime",
        "NOT_CERTIFIED",
        "v1",
        "Performance-optimized one-pass incremental indicator kernel is not certified by Step 5-10.",
        "DSL_NEXT_WORK_ORDER.md",
        False,
        True,
        "Prefix replay certifies causality but does not claim incremental performance identity.",
        ("test_axis1_full_engine_parity.py",),
    ),
)


DIAGNOSTICS = (
    DiagnosticRecord(
        "backtest.signal_counts",
        "diagnostics.signal_counts",
        "axes.axis1_dsl.execution.backtest.BacktestEngine",
        "execution observation",
        "mapping<string, integer>",
        (),
        "Counts emitted boolean strategy/runtime signals and canonical entry/exit signals.",
    ),
    DiagnosticRecord(
        "backtest.rejections",
        "diagnostics.rejections",
        "axes.axis1_dsl.execution.backtest.BacktestEngine",
        "execution policy observation",
        "mapping<string, integer>",
        (),
        "Counts fail-closed or policy-blocked execution paths.",
    ),
    DiagnosticRecord(
        "backtest.broker_history",
        "diagnostics.broker_history",
        "axes.axis1_dsl.execution.backtest.BacktestEngine",
        "broker lifecycle fact",
        "list<order_transition>",
        ("order_id", "status"),
        "Ordered broker lifecycle transitions emitted by the authoritative batch broker.",
    ),
    DiagnosticRecord(
        "backtest.parent_context",
        "diagnostics.parent_context",
        "axes.axis1_dsl.execution.backtest_parent_context",
        "context binding observation",
        "mapping",
        (),
        "Reports exact-as-bound parent-context usage and binding identity.",
    ),
    DiagnosticRecord(
        "backtest.entry_policy",
        "diagnostics.entry_policy",
        "axes.axis1_dsl.execution.backtest.BacktestEngine",
        "execution policy configuration",
        "mapping",
        ("entry_start_time", "entry_end_time", "max_entries_per_day", "higher_layer_gate_supplied"),
        "Echoes the effective entry-policy constraints used for the run.",
    ),
    DiagnosticRecord(
        "facade.bounded_loops",
        "diagnostics.bounded_loops",
        "axes.axis1_dsl.execution.axis1_backtest.Axis1BacktestEngine",
        "compile-time lowering observation",
        "mapping",
        ("supplied", "loops"),
        "Reports bounded-loop lowering definitions supplied by the user DSL.",
    ),
    DiagnosticRecord(
        "facade.user_functions",
        "diagnostics.user_functions",
        "axes.axis1_dsl.execution.axis1_backtest.Axis1BacktestEngine",
        "compile-time lowering observation",
        "mapping",
        ("supplied", "definitions"),
        "Reports pure user-function definitions consumed by compile-time lowering.",
    ),
    DiagnosticRecord(
        "facade.multi_output",
        "diagnostics.multi_output",
        "axes.axis1_dsl.execution.axis1_backtest.Axis1BacktestEngine",
        "compile-time lowering observation",
        "mapping",
        ("supplied", "bindings"),
        "Reports typed multi-output destructuring bindings.",
    ),
    DiagnosticRecord(
        "facade.projection",
        "diagnostics.projection",
        "axes.axis1_dsl.execution.generic_projection",
        "projection observation",
        "mapping",
        (),
        "Summarizes generic projection coverage without recalculating strategy values.",
    ),
    DiagnosticRecord(
        "intrabar.audit",
        "IntrabarStateSession.audit",
        "axes.axis1_dsl.runtime.intrabar_lifecycle.IntrabarStateSession",
        "strategy state transaction fact",
        "list<intrabar_event>",
        ("event",),
        "Ordered BEGIN/TICK/FILL/COMMIT/ROLLBACK transaction audit for provisional strategy state.",
    ),
    DiagnosticRecord(
        "partial.broker_history",
        "PartialExecutionSession.snapshot.broker_history",
        "axes.axis1_dsl.execution.partial_execution.PartialExecutionSession",
        "partial execution fact",
        "list<order_transition>",
        ("order_id", "status"),
        "Ordered cumulative partial-fill lifecycle transitions.",
    ),
    DiagnosticRecord(
        "partial.position",
        "PartialExecutionSession.snapshot.position",
        "axes.axis1_dsl.execution.partial_execution.PartialExecutionSession",
        "accounting fact",
        "mapping",
        ("position", "quantity", "average_entry_price", "realized_pnl", "cash"),
        "Single-position partial-fill/partial-exit accounting snapshot.",
    ),
    DiagnosticRecord(
        "pyramiding.position",
        "PyramidingExecutionSession.snapshot.position",
        "axes.axis1_dsl.execution.pyramiding_execution.PyramidingExecutionSession",
        "multi-lot accounting fact",
        "mapping",
        ("position", "quantity", "average_entry_price", "lots", "realized_pnl", "cash"),
        "Aggregate and per-lot same-direction pyramiding accounting snapshot.",
    ),
    DiagnosticRecord(
        "parity.runtime_report",
        "RuntimeParityReport",
        "axes.axis1_dsl.execution.full_engine_parity.verify_runtime_prefix_parity",
        "verification evidence",
        "mapping",
        ("bars", "prefixes_checked", "series_checked", "event_count"),
        "Runtime causal-prefix parity certification summary.",
    ),
    DiagnosticRecord(
        "parity.backtest_report",
        "BacktestParityReport",
        "axes.axis1_dsl.execution.full_engine_parity.verify_backtest_prefix_parity",
        "verification evidence",
        "mapping",
        ("bars", "prefixes_checked", "trade_count", "closed_trade_count", "broker_history_count"),
        "Backtest causal-prefix parity certification summary.",
    ),
)


def _all_capabilities() -> tuple[CapabilityRecord, ...]:
    return _function_records() + FEATURE_CAPABILITIES


def validate_registry() -> None:
    capabilities = _all_capabilities()
    ids = [item.capability_id for item in capabilities]
    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        raise CapabilityRegistryError(f"duplicate capability ids: {duplicates}", "DUPLICATE_CAPABILITY_ID")
    for item in capabilities:
        item.validate()

    diagnostic_ids = [item.diagnostic_id for item in DIAGNOSTICS]
    diagnostic_paths = [item.path for item in DIAGNOSTICS]
    if len(diagnostic_ids) != len(set(diagnostic_ids)):
        raise CapabilityRegistryError("duplicate diagnostic ids", "DUPLICATE_DIAGNOSTIC_ID")
    if len(diagnostic_paths) != len(set(diagnostic_paths)):
        raise CapabilityRegistryError("duplicate diagnostic paths", "DUPLICATE_DIAGNOSTIC_PATH")
    for item in DIAGNOSTICS:
        item.validate()


def capability_records() -> tuple[dict, ...]:
    validate_registry()
    return tuple(
        item.public_dict()
        for item in sorted(_all_capabilities(), key=lambda value: value.capability_id)
    )


def diagnostic_records() -> tuple[dict, ...]:
    validate_registry()
    return tuple(
        item.public_dict()
        for item in sorted(DIAGNOSTICS, key=lambda value: value.diagnostic_id)
    )


def capability_record(capability_id: str) -> dict:
    identity = str(capability_id)
    for item in _all_capabilities():
        if item.capability_id == identity:
            item.validate()
            return item.public_dict()
    raise CapabilityRegistryError(f"unknown capability: {identity}", "UNKNOWN_CAPABILITY")


def diagnostic_record(diagnostic_id: str) -> dict:
    identity = str(diagnostic_id)
    for item in DIAGNOSTICS:
        if item.diagnostic_id == identity:
            item.validate()
            return item.public_dict()
    raise CapabilityRegistryError(f"unknown diagnostic: {identity}", "UNKNOWN_DIAGNOSTIC")


def require_supported(capability_id: str, *, allow_boundary: bool = True) -> dict:
    item = capability_record(capability_id)
    allowed = {"SUPPORTED"}
    if allow_boundary:
        allowed.add("SUPPORTED_WITH_BOUNDARY")
    if item["status"] not in allowed:
        raise CapabilityRegistryError(
            f"capability is not supported for execution: {capability_id} ({item['status']})",
            "CAPABILITY_NOT_SUPPORTED",
        )
    return item


def registry_snapshot() -> dict:
    body = {
        "schema": REGISTRY_SCHEMA,
        "capabilities": capability_records(),
        "diagnostics": diagnostic_records(),
    }
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        **body,
        "registry_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def registry_hash() -> str:
    return str(registry_snapshot()["registry_hash"])


validate_registry()
