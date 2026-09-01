"""Bounded human-mediated iteration workflow for external strategy drafts."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Mapping, Sequence

from authoring.external_llm.manifest import AuthoringManifest
from authoring.external_llm.prompt_builder import build_correction_prompt, build_initial_prompt
from authoring.external_llm.validator import ValidationReport, validate_external_draft, validation_errors


class AuthoringWorkflowError(ValueError):
    def __init__(self, message: str, code: str = "AUTHORING_WORKFLOW_ERROR"):
        self.code = str(code)
        super().__init__(message)


@dataclass(frozen=True)
class AuthoringIteration:
    iteration: int
    draft_id: str
    final_status: str
    correction_prompt: str | None


@dataclass
class HumanMediatedAuthoringSession:
    request_id: str
    user_request: str
    manifest: AuthoringManifest
    max_iterations: int = 6
    accepted_assumption_ids: set[str] = field(default_factory=set)
    history: list[AuthoringIteration] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.request_id = str(self.request_id).strip()
        if not self.request_id:
            raise AuthoringWorkflowError("request_id is required", "BAD_REQUEST_ID")
        if not str(self.user_request).strip():
            raise AuthoringWorkflowError("user_request is required", "BAD_USER_REQUEST")
        if not isinstance(self.manifest, AuthoringManifest):
            raise AuthoringWorkflowError("manifest must be AuthoringManifest", "BAD_MANIFEST")
        if isinstance(self.max_iterations, bool) or not isinstance(self.max_iterations, int) or self.max_iterations <= 0:
            raise AuthoringWorkflowError("max_iterations must be positive integer", "BAD_MAX_ITERATIONS")

    @property
    def user_request_hash(self) -> str:
        return hashlib.sha256(str(self.user_request).encode("utf-8")).hexdigest()

    def initial_prompt(self) -> str:
        return build_initial_prompt(
            request_id=self.request_id,
            user_request=self.user_request,
            manifest=self.manifest,
        )

    def accept_assumptions(self, assumption_ids: Sequence[str]) -> None:
        for identity in assumption_ids:
            text = str(identity).strip()
            if not text:
                raise AuthoringWorkflowError("assumption id is empty", "BAD_ASSUMPTION_ID")
            self.accepted_assumption_ids.add(text)

    def submit(self, raw: str | Mapping[str, Any]) -> tuple[ValidationReport, str | None]:
        if len(self.history) >= self.max_iterations:
            raise AuthoringWorkflowError("authoring iteration limit reached", "ITERATION_LIMIT")
        report = validate_external_draft(
            raw,
            request_id=self.request_id,
            manifest=self.manifest,
            accepted_assumption_ids=tuple(sorted(self.accepted_assumption_ids)),
        )
        correction: str | None = None
        if report.final_status == "REQUIRES_CORRECTION" and report.draft is not None:
            correction = build_correction_prompt(
                request_id=self.request_id,
                user_request=self.user_request,
                previous_draft=report.draft,
                errors=validation_errors(report),
                manifest=self.manifest,
            )
        self.history.append(
            AuthoringIteration(
                iteration=len(self.history),
                draft_id=report.draft_id,
                final_status=report.final_status,
                correction_prompt=correction,
            )
        )
        return report, correction
