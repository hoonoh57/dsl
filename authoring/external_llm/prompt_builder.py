"""Deterministic prompts for human-mediated external LLM authoring."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from authoring.external_llm.manifest import AuthoringManifest


PROMPT_BUILDER_VERSION = "external_authoring_prompt_builder/v1"
PROMPT_TEMPLATE_VERSION = "external_authoring_prompt/v1"
CORRECTION_TEMPLATE_VERSION = "external_authoring_correction_prompt/v1"
SKILL_VERSION = "dsl-external-authoring-skill/v2-generated-manifest"

DSL_SYNTAX_REFERENCE = r'''AXIS 1 DSL syntax reference (use an advanced form only when its capability is SUPPORTED):

strategy "NAME" {
    timeframe = "15m"
    input threshold = 1.0

    function centered(source, period) {
        basis_local = ta.sma(source, period)
        return source - basis_local
    }

    centered_value = centered(close, 20)
    basis = ta.ema(close, 20)
    state armed = false

    on_bar {
        if (close > basis) {
            set armed = true
        }
        else {
            set armed = false
        }
    }

    enter = armed and ta.crossover(close, basis)
    on(enter) { order.buy(type = "MARKET") }
}

Bounded loop (inside a supported user function; compile-time constant range only):
function mean3(source) {
    total = 0
    for i in range(0, 3) {
        total = total + source[i]
    }
    return total / 3
}

Registered multi-output destructuring inside the strategy body:
upper, middle, lower = ta.bbands(close, 20, 2)

Intrabar state handlers inside the strategy body:
on_tick {
    if (tick.price > peak) {
        set peak = tick.price
    }
}
on_fill {
    set fill_count = fill_count + 1
}

Read-only context uses exact manifest IDs only:
reference_hist = ctx.selection.reference_hist

Do not invent syntax for partial fills, pyramiding, universe search, peer ranking, provider calls, or persistence. Those are separate execution/product capabilities, not implied DSL grammar.'''


class PromptBuildError(ValueError):
    pass


def _schema_text() -> str:
    path = Path(__file__).resolve().parents[1] / "contracts" / "external_strategy_draft.v1.schema.json"
    return path.read_text(encoding="utf-8")


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)


def build_initial_prompt(*, request_id: str, user_request: str, manifest: AuthoringManifest) -> str:
    request_identity = str(request_id).strip()
    request_text = str(user_request)
    if not request_identity:
        raise PromptBuildError("request_id is required")
    if not request_text.strip():
        raise PromptBuildError("user_request is required")
    if not isinstance(manifest, AuthoringManifest):
        raise PromptBuildError("manifest must be AuthoringManifest")

    envelope = {
        "prompt_builder_version": PROMPT_BUILDER_VERSION,
        "prompt_template_version": PROMPT_TEMPLATE_VERSION,
        "skill_version": SKILL_VERSION,
        "request_id": request_identity,
        "manifest_hash": manifest.manifest_hash,
        "manifest": manifest.public_dict(),
    }
    return "\n".join(
        [
            "EXTERNAL STRATEGY AUTHORING TASK",
            "You are proposal-only. You have no execution authority.",
            "Use only identities present in AUTHORING_MANIFEST. Do not invent functions, features, data sources, context IDs, order commands, or bridge fields.",
            "Keep AXIS 2 selection separate from AXIS 1 single-instrument DSL. Put material ambiguity in assumptions/unresolved_questions.",
            "Never use future data, nearest-time lookup, fill-forward, interpolation, or silent defaults.",
            "Return exactly one JSON object matching OUTPUT_SCHEMA and no prose outside it.",
            "If a required listed capability is unavailable, place its exact capability_id in needs_capability.",
            "",
            "REQUEST_METADATA",
            _dump(envelope),
            "",
            "DSL_SYNTAX_REFERENCE",
            DSL_SYNTAX_REFERENCE,
            "",
            "VERBATIM_USER_REQUEST",
            request_text,
            "",
            "OUTPUT_SCHEMA",
            _schema_text(),
        ]
    )


def build_correction_prompt(
    *,
    request_id: str,
    user_request: str,
    previous_draft: Mapping[str, Any],
    errors: Sequence[Mapping[str, Any]],
    manifest: AuthoringManifest,
) -> str:
    if not errors:
        raise PromptBuildError("correction prompt requires validation errors")
    request_identity = str(request_id).strip()
    if not request_identity:
        raise PromptBuildError("request_id is required")
    if not isinstance(previous_draft, Mapping):
        raise PromptBuildError("previous_draft must be a mapping")
    if str(previous_draft.get("request_id") or "") != request_identity:
        raise PromptBuildError("previous draft request_id mismatch")

    correction = {
        "prompt_builder_version": PROMPT_BUILDER_VERSION,
        "prompt_template_version": CORRECTION_TEMPLATE_VERSION,
        "request_id": request_identity,
        "manifest_hash": manifest.manifest_hash,
        "validation_errors": list(errors),
        "manifest": manifest.public_dict(),
    }
    return "\n".join(
        [
            "EXTERNAL STRATEGY AUTHORING CORRECTION TASK",
            "Preserve the original user intent and all already-valid fields. Change only what is required by VALIDATION_ERRORS and directly dependent fields.",
            "Do not work around missing capabilities by inventing syntax or data sources. Keep the same request_id.",
            "Return exactly one corrected JSON object matching OUTPUT_SCHEMA and no surrounding prose.",
            "",
            "CORRECTION_METADATA",
            _dump(correction),
            "",
            "DSL_SYNTAX_REFERENCE",
            DSL_SYNTAX_REFERENCE,
            "",
            "ORIGINAL_USER_REQUEST",
            str(user_request),
            "",
            "PREVIOUS_DRAFT",
            _dump(dict(previous_draft)),
            "",
            "OUTPUT_SCHEMA",
            _schema_text(),
        ]
    )
