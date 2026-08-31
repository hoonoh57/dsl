"""Canonical AXIS 1 runtime facade for additive DSL features.

Feature syntax is lowered before entering the migrated deterministic runtime.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

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
        loops_lowered = lower_bounded_loops(code)
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
        compiled.bounded_loop_definitions = loops_lowered.manifest()
        compiled.user_function_definitions = functions_lowered.manifest()
        compiled.multi_output_bindings = tuple(item.public_dict() for item in lowered.bindings)
        return compiled
