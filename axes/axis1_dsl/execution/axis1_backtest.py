"""AXIS 1 backtest facade for additive DSL features and generic projection."""
from __future__ import annotations

from axes.axis1_dsl.core.bounded_loops import lower_bounded_loops
from axes.axis1_dsl.core.user_functions import lower_user_functions
from axes.axis1_dsl.core.multi_output import lower_multi_output
from axes.axis1_dsl.execution.backtest import BacktestEngine as MigratedBacktestEngine
from axes.axis1_dsl.execution.generic_projection import attach_generic_projection
from axes.axis1_dsl.runtime.dsl_runtime import DSLRuntimeError


class Axis1BacktestEngine:
    @staticmethod
    def run(dsl_code: str, *args, **kwargs):
        loops_lowered = lower_bounded_loops(dsl_code)
        functions_lowered = lower_user_functions(loops_lowered.source)
        lowered = lower_multi_output(functions_lowered.source)
        try:
            result = MigratedBacktestEngine.run(lowered.source, *args, **kwargs)
        except DSLRuntimeError as exc:
            mapped = lowered.remap_error_message(str(exc))
            if mapped == str(exc):
                raise
            raise DSLRuntimeError(mapped) from exc
        diagnostics = result.setdefault("diagnostics", {})
        diagnostics["bounded_loops"] = {
            "supplied": bool(loops_lowered.loops),
            "loops": list(loops_lowered.manifest()),
        }
        diagnostics["user_functions"] = {
            "supplied": bool(functions_lowered.functions),
            "definitions": list(functions_lowered.manifest()),
        }
        diagnostics["multi_output"] = {
            "supplied": bool(lowered.bindings),
            "bindings": [item.public_dict() for item in lowered.bindings],
        }
        attach_generic_projection(result, lowered.bindings)
        return result
