"""Deterministic final repository compliance audit.

The audit is intentionally read-only. It checks the current product surface,
active authority documents, import boundaries and critical-test hygiene. It does
not rewrite code or documents and it does not replace the frozen-core tree guard.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable


REPORT_SCHEMA = "dsl_repo_compliance_report/v1"

AXIS_ROOTS = {
    "AXIS1": "axes/axis1_dsl",
    "AXIS2": "axes/axis2_selection",
    "AXIS3": "axes/axis3_monetization",
}

CRITICAL_TESTS = (
    "tests/test_axis1_full_engine_parity.py",
    "tests/test_axis1_execution_bridge_contract.py",
    "tests/test_axis2_exact_asof_snapshot.py",
    "tests/test_axis2_selection_engine.py",
    "tests/test_axis3_crud_orchestration.py",
    "tests/test_three_axis_e2e_bridge.py",
    "tests/test_external_llm_authoring_lane.py",
    "tests/test_authoring_continuous_improvement.py",
    "tests/test_final_natural_language_e2e.py",
    "tests/test_frozen_legacy_core_guard.py",
)

ACTIVE_DOCS = (
    "SESSION_HANDOFF.md",
    "DSL_NEXT_WORK_ORDER.md",
    "CURRENT_STATE.md",
    "DSL_DOCUMENT_AUTHORITY_INDEX.md",
    "DSL_THREE_AXIS_FINAL_TARGET.md",
    "DSL_THREE_AXIS_MODULE_BOUNDARY.md",
    "DSL_FROZEN_CORE_MIGRATION_POLICY.md",
    "DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md",
    "DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md",
    "DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md",
    "DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md",
    "axes/axis1_dsl/README.md",
    "axes/axis2_selection/README.md",
    "axes/axis3_monetization/README.md",
)


@dataclass(frozen=True, order=True)
class AuditFinding:
    check_id: str
    path: str
    message: str

    def public_dict(self) -> dict[str, str]:
        return {
            "check_id": self.check_id,
            "path": self.path,
            "message": self.message,
        }


@dataclass(frozen=True)
class RepoComplianceReport:
    checks_run: tuple[str, ...]
    findings: tuple[AuditFinding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    def canonical_dict(self) -> dict:
        return {
            "schema": REPORT_SCHEMA,
            "status": "PASS" if self.passed else "FAIL",
            "checks_run": list(self.checks_run),
            "findings": [item.public_dict() for item in self.findings],
        }

    @property
    def report_hash(self) -> str:
        payload = json.dumps(
            self.canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def public_dict(self) -> dict:
        return {**self.canonical_dict(), "report_hash": self.report_hash}


def _repo_root(root: str | Path | None) -> Path:
    if root is None:
        return Path(__file__).resolve().parents[1]
    return Path(root).resolve()


def _python_files(root: Path, relative: str) -> tuple[Path, ...]:
    base = root / relative
    if not base.exists():
        return ()
    return tuple(sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts))


def _imports(path: Path) -> tuple[tuple[str, int], ...]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, 0) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append((node.module or "", int(node.level or 0)))
    return tuple(found)


def _absolute_matches(name: str, level: int, prefix: str) -> bool:
    return level == 0 and (name == prefix or name.startswith(prefix + "."))


def _finding(check_id: str, root: Path, path: Path, message: str) -> AuditFinding:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()
    return AuditFinding(check_id, rel, message)


def _audit_axis_imports(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    prefixes = {
        "AXIS1": "axes.axis1_dsl",
        "AXIS2": "axes.axis2_selection",
        "AXIS3": "axes.axis3_monetization",
    }
    for axis, relative in AXIS_ROOTS.items():
        forbidden_axes = {name: prefix for name, prefix in prefixes.items() if name != axis}
        for path in _python_files(root, relative):
            try:
                imports = _imports(path)
            except (SyntaxError, UnicodeError) as exc:
                findings.append(_finding("AXIS_IMPORT_BOUNDARY", root, path, f"cannot parse Python source: {exc}"))
                continue
            for name, level in imports:
                if _absolute_matches(name, level, "core"):
                    findings.append(_finding("AXIS_IMPORT_BOUNDARY", root, path, "imports frozen repository-root core"))
                for other_axis, prefix in forbidden_axes.items():
                    if _absolute_matches(name, level, prefix):
                        findings.append(
                            _finding(
                                "AXIS_IMPORT_BOUNDARY",
                                root,
                                path,
                                f"directly imports {other_axis} implementation: {name}",
                            )
                        )
    return findings


def _audit_bridge_boundaries(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    contracts = root / "bridges" / "contracts"
    for path in sorted(contracts.rglob("*.py")) if contracts.exists() else ():
        try:
            imports = _imports(path)
        except (SyntaxError, UnicodeError) as exc:
            findings.append(_finding("BRIDGE_CONTRACT_DATA_ONLY", root, path, f"cannot parse Python source: {exc}"))
            continue
        for name, level in imports:
            if any(
                _absolute_matches(name, level, prefix)
                for prefix in ("axes", "authoring", "acceptance", "core")
            ):
                findings.append(
                    _finding(
                        "BRIDGE_CONTRACT_DATA_ONLY",
                        root,
                        path,
                        f"data-only contract imports implementation authority: {name}",
                    )
                )

    bridge_root = root / "bridges"
    for path in sorted(bridge_root.glob("*.py")) if bridge_root.exists() else ():
        try:
            imports = _imports(path)
        except (SyntaxError, UnicodeError) as exc:
            findings.append(_finding("BRIDGE_COMPOSITION_BOUNDARY", root, path, f"cannot parse Python source: {exc}"))
            continue
        name = path.name
        for imported, level in imports:
            if _absolute_matches(imported, level, "core"):
                findings.append(_finding("BRIDGE_COMPOSITION_BOUNDARY", root, path, "imports frozen repository-root core"))
            if name == "axis1_execution_bridge.py":
                for prefix in ("axes.axis2_selection", "axes.axis3_monetization"):
                    if _absolute_matches(imported, level, prefix):
                        findings.append(
                            _finding(
                                "BRIDGE_COMPOSITION_BOUNDARY",
                                root,
                                path,
                                f"AXIS1 adapter imports unrelated axis: {imported}",
                            )
                        )
            elif name == "three_axis_e2e_bridge.py":
                if _absolute_matches(imported, level, "axes.axis1_dsl"):
                    findings.append(
                        _finding(
                            "BRIDGE_COMPOSITION_BOUNDARY",
                            root,
                            path,
                            "three-axis router bypasses AXIS1 execution Bridge",
                        )
                    )
            elif name != "__init__.py" and _absolute_matches(imported, level, "axes"):
                findings.append(
                    _finding(
                        "BRIDGE_COMPOSITION_BOUNDARY",
                        root,
                        path,
                        f"unregistered Bridge module imports axis implementation: {imported}",
                    )
                )
    return findings


def _audit_authoring_boundaries(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    external_root = root / "authoring" / "external_llm"
    for path in sorted(external_root.rglob("*.py")) if external_root.exists() else ():
        try:
            imports = _imports(path)
        except (SyntaxError, UnicodeError) as exc:
            findings.append(_finding("AUTHORING_AUTHORITY", root, path, f"cannot parse Python source: {exc}"))
            continue
        for name, level in imports:
            if any(
                _absolute_matches(name, level, prefix)
                for prefix in ("axes.axis2_selection", "axes.axis3_monetization", "core")
            ):
                findings.append(_finding("AUTHORING_AUTHORITY", root, path, f"proposal lane imports forbidden authority: {name}"))
            if any(
                _absolute_matches(name, level, prefix)
                for prefix in ("bridges.axis1_execution_bridge", "bridges.three_axis_e2e_bridge")
            ):
                findings.append(_finding("AUTHORING_AUTHORITY", root, path, f"proposal lane imports execution Bridge: {name}"))

    improvement_root = root / "authoring" / "continuous_improvement"
    for path in sorted(improvement_root.rglob("*.py")) if improvement_root.exists() else ():
        try:
            imports = _imports(path)
        except (SyntaxError, UnicodeError) as exc:
            findings.append(_finding("CONTINUOUS_IMPROVEMENT_AUTHORITY", root, path, f"cannot parse Python source: {exc}"))
            continue
        for name, level in imports:
            if any(
                _absolute_matches(name, level, prefix)
                for prefix in ("axes", "bridges", "core")
            ):
                findings.append(
                    _finding(
                        "CONTINUOUS_IMPROVEMENT_AUTHORITY",
                        root,
                        path,
                        f"analysis-only tooling imports execution/product authority: {name}",
                    )
                )
    return findings


def _audit_no_frozen_core_runtime_imports(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for relative in ("axes", "bridges", "authoring", "acceptance", "compliance"):
        for path in _python_files(root, relative):
            try:
                imports = _imports(path)
            except (SyntaxError, UnicodeError):
                continue
            for name, level in imports:
                if _absolute_matches(name, level, "core"):
                    findings.append(
                        _finding(
                            "FROZEN_CORE_RUNTIME_DEPENDENCY",
                            root,
                            path,
                            f"current product surface imports frozen core: {name}",
                        )
                    )
    return findings


def _audit_critical_tests(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    forbidden = re.compile(
        r"@\s*(?:unittest\.)?skip\b|@\s*pytest\.mark\.skip\b|"
        r"\bskipTest\s*\(|\bpytest\.skip\s*\(|@\s*(?:unittest\.)?expectedFailure\b"
    )
    for relative in CRITICAL_TESTS:
        path = root / relative
        if not path.exists():
            findings.append(AuditFinding("CRITICAL_TEST_HYGIENE", relative, "critical regression test is missing"))
            continue
        text = path.read_text(encoding="utf-8")
        if forbidden.search(text):
            findings.append(AuditFinding("CRITICAL_TEST_HYGIENE", relative, "critical regression contains skip/expectedFailure bypass"))
    return findings


def _require_tokens(
    root: Path,
    relative: str,
    *,
    required: Iterable[str] = (),
    forbidden: Iterable[str] = (),
) -> list[AuditFinding]:
    path = root / relative
    if not path.exists():
        return [AuditFinding("DOCUMENT_AUTHORITY", relative, "active authority document is missing")]
    text = path.read_text(encoding="utf-8")
    findings: list[AuditFinding] = []
    for token in required:
        if token not in text:
            findings.append(AuditFinding("DOCUMENT_AUTHORITY", relative, f"required authority statement missing: {token}"))
    for token in forbidden:
        if token in text:
            findings.append(AuditFinding("DOCUMENT_AUTHORITY", relative, f"stale/conflicting authority statement remains: {token}"))
    return findings


def _audit_documents(root: Path) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    for relative in ACTIVE_DOCS:
        if not (root / relative).exists():
            findings.append(AuditFinding("DOCUMENT_AUTHORITY", relative, "active authority document is missing"))

    findings.extend(
        _require_tokens(
            root,
            "CURRENT_STATE.md",
            required=(
                "AXIS 2 exact-PIT selection",
                "AXIS 3 exact promoted Condition/Strategy versions + run plan",
                "Only Step 15 remains",
            ),
            forbidden=("REMEDIATION_REQUIRED", "MIGRATION NOT YET STARTED"),
        )
    )
    findings.extend(
        _require_tokens(
            root,
            "DSL_THREE_AXIS_FINAL_TARGET.md",
            required=(
                "AXIS 2 exact-PIT selection",
                "AXIS 3 promoted Condition/Strategy versions + deterministic run plan",
                "Condition의 **선별 의미**는 AXIS 2",
                "Condition의 저장·버전·계보·승격 lifecycle은 AXIS 3",
            ),
        )
    )
    findings.extend(
        _require_tokens(
            root,
            "DSL_THREE_AXIS_MODULE_BOUNDARY.md",
            required=(
                "AXIS 2 snapshot/spec",
                "-> AXIS 3 exact promoted Condition/Strategy + RunPlan",
                "-> AXIS 1 one-symbol execution requests",
            ),
        )
    )
    findings.extend(
        _require_tokens(
            root,
            "axes/axis1_dsl/README.md",
            required=("MIGRATION COMPLETE", "capability_diagnostic_registry.py"),
            forbidden=("MIGRATION NOT YET STARTED",),
        )
    )
    findings.extend(
        _require_tokens(
            root,
            "axes/axis2_selection/README.md",
            required=("Condition **selection semantics**", "AXIS 3 owns Condition **artifact lifecycle**"),
            forbidden=("generic Condition CRUD",),
        )
    )
    findings.extend(
        _require_tokens(
            root,
            "DSL_DOCUMENT_AUTHORITY_INDEX.md",
            required=(
                "ACTIVE AUTHORITY",
                "HISTORICAL / NON-AUTHORITATIVE",
                "DSL_LIVE_STUDIO_FEATURE_CATALOG_V2.md",
                "CTX*.md",
                "current support SSOT",
            ),
        )
    )
    return findings


def audit_repository(root: str | Path | None = None) -> RepoComplianceReport:
    repo = _repo_root(root)
    checks = (
        "AXIS_IMPORT_BOUNDARY",
        "BRIDGE_CONTRACT_DATA_ONLY",
        "BRIDGE_COMPOSITION_BOUNDARY",
        "AUTHORING_AUTHORITY",
        "CONTINUOUS_IMPROVEMENT_AUTHORITY",
        "FROZEN_CORE_RUNTIME_DEPENDENCY",
        "CRITICAL_TEST_HYGIENE",
        "DOCUMENT_AUTHORITY",
    )
    findings: list[AuditFinding] = []
    findings.extend(_audit_axis_imports(repo))
    findings.extend(_audit_bridge_boundaries(repo))
    findings.extend(_audit_authoring_boundaries(repo))
    findings.extend(_audit_no_frozen_core_runtime_imports(repo))
    findings.extend(_audit_critical_tests(repo))
    findings.extend(_audit_documents(repo))
    return RepoComplianceReport(checks_run=checks, findings=tuple(sorted(set(findings))))
