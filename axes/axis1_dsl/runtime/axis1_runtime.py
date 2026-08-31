"""Canonical AXIS 1 runtime facade for additive DSL features.

Feature syntax is lowered before entering the migrated deterministic runtime.
"""
from __future__ import annotations

from typing import Dict, Mapping, Sequence

import numpy as np

from axes.axis1_dsl.runtime.intrabar_lifecycle import extract_intrabar_handlers
from axes.axis1_dsl.core.bounded_loops import lower_bounded_loops
from axes.axis1_dsl.core.user_functions import lower_user_functions
from axes.axis1_dsl.core.multi_output import lower_multi_output
from axes.axis1_dsl.runtime.dsl_context import DSLContextSeriesBinding
from axes.axis1_dsl.runtime.dsl_runtime import DSLRuntime as MigratedDSLRuntime
from axes.axis1_dsl.runtime.dsl_runtime import DSLRuntimeError


class Axis1DSLRuntime:
    @staticmethod
    def compile(
        code: str,
        market: Dict[str, np.ndarray],
        *,
        context_binding: DSLContextSeriesBinding | None = None,
        target_times: Sequence[str] | None = None,
    ):
        intrabar_lowered = extract_intrabar_handlers(code)
        loops_lowered = lower_bounded_loops(intrabar_lowered.source)
        functions_lowered = lower_user_functions(loops_lowered.source)
        lowered = lower_multi_output(functions_lowered.source)
        try:
            compiled = MigratedDSLRuntime.compile(
                lowered.source,
                market,
                context_binding=context_binding,
                target_times=target_times,
            )
        except DSLRuntimeError as exc:
            mapped = lowered.remap_error_message(str(exc))
            if mapped == str(exc):
                raise
            raise DSLRuntimeError(mapped) from exc
        compiled.intrabar_program = intrabar_lowered.program
        compiled.intrabar_handlers = intrabar_lowered.program.manifest()
        compiled.bounded_loop_definitions = loops_lowered.manifest()
        compiled.user_function_definitions = functions_lowered.manifest()
        compiled.multi_output_bindings = tuple(item.public_dict() for item in lowered.bindings)
        return compiled

    @staticmethod
    def open_intrabar_session(compiled, initial_state: Mapping[str, object] | None = None):
        """Continue a compiled strategy from its last committed state snapshot."""
        program = getattr(compiled, "intrabar_program", None)
        if program is None:
            raise DSLRuntimeError("compiled strategy에 intrabar program이 없습니다.")
        if initial_state is None:
            snapshot: dict[str, object] = {}
            for name in program.state_names:
                if name not in compiled.values:
                    raise DSLRuntimeError(f"compiled strategy state를 찾을 수 없습니다: {name}")
                value = compiled.values[name]
                if isinstance(value, np.ndarray):
                    if not len(value):
                        raise DSLRuntimeError(f"빈 series에서는 intrabar state를 이어갈 수 없습니다: {name}")
                    value = value[-1]
                if isinstance(value, np.generic):
                    value = value.item()
                snapshot[name] = value
            initial_state = snapshot
        return program.new_session(initial_state)
