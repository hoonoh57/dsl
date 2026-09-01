"""External LLM proposal lane with deterministic local validation."""

from authoring.external_llm.manifest import AuthoringManifest, build_authoring_manifest
from authoring.external_llm.prompt_builder import build_correction_prompt, build_initial_prompt
from authoring.external_llm.validator import (
    ValidationReport,
    build_validation_event,
    ingest_external_draft,
    validate_external_draft,
    validation_errors,
)
from authoring.external_llm.workflow import HumanMediatedAuthoringSession

__all__ = [
    "AuthoringManifest",
    "build_authoring_manifest",
    "build_initial_prompt",
    "build_correction_prompt",
    "ValidationReport",
    "ingest_external_draft",
    "validate_external_draft",
    "validation_errors",
    "build_validation_event",
    "HumanMediatedAuthoringSession",
]
