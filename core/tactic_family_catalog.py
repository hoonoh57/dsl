"""Authoritative bounded tactic-family catalog for micro-warrior evolution.

The catalog is intentionally small.  Each family must be introduced and validated
independently; this module must not silently synthesize arbitrary families or
skills from indicator names.
"""
from __future__ import annotations

from core.tactic_family import TacticFamilyRegistry, TacticFamilySpec
from core.tactical_evolution import CapabilityBudget, SkillSpec


JMA_TREND_CROSS_RESUME_V1 = "JMA_TREND_CROSS_RESUME_V1"

JMA_BASE_DSL = '''strategy "JMA_Trend_Cross_Resume_Base" {
    timeframe = "5m"
    trend = ta.sma(close, 60)
    fast = ta.jma(close, 7, 50, 2)
    slow = ta.jma(close, 50, 50, 4)
    long_entry = close >= trend and ta.crossover(fast, slow)
    long_exit = ta.crossunder(fast, slow)
    short_entry = false
    short_exit = false
    on(long_entry) { order.buy(type = "MARKET") }
    on(long_exit) { order.close_long() }
}'''


def jma_trend_cross_resume_family() -> TacticFamilySpec:
    """Return the first production-style bounded JMA family contract.

    This is a declarative legal arsenal.  A SkillSpec does not mutate DSL by
    itself; a future structural generator must instantiate exactly one legal
    skill and the existing evolution arena must validate the child evidence.
    """

    return TacticFamilySpec(
        family_id=JMA_TREND_CROSS_RESUME_V1,
        base_candidate_id="JMA_TCR_G0",
        base_dsl=JMA_BASE_DSL,
        base_complexity_units=3,
        budget=CapabilityBudget(
            max_skills=3,
            max_complexity_units=8,
            max_indicators=5,
            max_parameters=12,
            max_state_variables=2,
            max_branches=7,
            max_setup_variants=2,
        ),
        base_usage={
            "skills": 0,
            "complexity_units": 3,
            "indicators": 3,
            "parameters": 7,
            "state_variables": 0,
            "branches": 2,
            "setup_variants": 1,
        },
        skills=(
            SkillSpec(
                skill_id="JMA_RANGE_COOLDOWN",
                capability="RANGE_DEFENSE",
                implementation="bars-since-crossunder cooldown before next long entry",
                addresses_failure_tags=("WHIPSAW", "DRAWDOWN"),
                cost={
                    "complexity_units": 1,
                    "parameters": 1,
                    "branches": 1,
                },
                metadata={
                    "dsl_pattern": "ta.bars_since(ta.crossunder(fast, slow)) > cooldown_bars",
                    "parameters": {
                        "cooldown_bars": {"type": "int", "min": 1, "max": 30, "default": 10}
                    },
                    "requires_skills": (),
                    "excludes_skills": (),
                },
            ),
            SkillSpec(
                skill_id="JMA_ADX_ENTRY_QUALITY",
                capability="ENTRY_QUALITY",
                implementation="ADX strength gate on JMA crossover entry",
                addresses_failure_tags=("LOSS", "ADVERSE_EXCURSION", "WHIPSAW"),
                cost={
                    "complexity_units": 1,
                    "indicators": 1,
                    "parameters": 2,
                    "branches": 1,
                },
                metadata={
                    "dsl_pattern": "ta.adx(adx_length) > adx_threshold",
                    "parameters": {
                        "adx_length": {"type": "int", "min": 5, "max": 40, "default": 14},
                        "adx_threshold": {"type": "number", "min": 10, "max": 40, "default": 20},
                    },
                    "requires_skills": (),
                    "excludes_skills": (),
                },
            ),
            SkillSpec(
                skill_id="JMA_CONFIRM_AFTER_RANGE",
                capability="ENGAGEMENT_DISCIPLINE",
                implementation="persistent post-range trend confirmation before re-engagement",
                addresses_failure_tags=("LOSS", "SEVERE_LOSS", "WHIPSAW"),
                cost={
                    "complexity_units": 2,
                    "parameters": 1,
                    "state_variables": 1,
                    "branches": 1,
                },
                metadata={
                    "dsl_pattern": "state.persist(fast > slow and close > fast, confirm_bars)",
                    "parameters": {
                        "confirm_bars": {"type": "int", "min": 2, "max": 8, "default": 2}
                    },
                    "requires_skills": ("JMA_RANGE_COOLDOWN",),
                    "excludes_skills": (),
                },
            ),
            SkillSpec(
                skill_id="JMA_FAST_PROFIT_PROTECTION",
                capability="PROFIT_PROTECTION",
                implementation="close long on fast-JMA loss before slow cross when local edge decays",
                addresses_failure_tags=("MFE_GIVEBACK", "UNRESOLVED_POSITION"),
                cost={
                    "complexity_units": 1,
                    "branches": 1,
                },
                metadata={
                    "dsl_pattern": "close < fast or ta.crossunder(fast, slow)",
                    "parameters": {},
                    "requires_skills": (),
                    "excludes_skills": (),
                },
            ),
        ),
        metadata={
            "research_scope": "Korean regular-session intraday micro tactic",
            "timeframe": "5m",
            "direction": "long",
            "family_stage": "E2-first-family",
            "mutation_policy": "one-skill-only",
        },
    )


def build_default_tactic_family_registry() -> TacticFamilyRegistry:
    """Return the explicit built-in family registry.

    Adding another family is a separate validated tranche.  Keep ordering stable
    because registry identity is used by evidence/UI layers.
    """

    return TacticFamilyRegistry((jma_trend_cross_resume_family(),))
