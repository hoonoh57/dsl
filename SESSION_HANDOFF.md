# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / FINAL STEP 15 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 세 축의 계산 권한을 섞지 않는다. Historical 문서는 evidence로 보존하되 current authority가 아니다.

---

## 현재 작업

```text
CURRENT_STEP = 15
CURRENT_SUBSTEP = 15-1 legacy docs disposition + deterministic repo-wide compliance audit
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1~13 = COMPLETE / USER-LOCAL PASS
Step 14 Final natural-language E2E acceptance = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP14_FINAL_NATURAL_LANGUAGE_E2E_CHECKPOINT_2026-09-01.md
```

Step 14 user-local evidence:

```text
test_final_natural_language_e2e.py = OK
test_three_axis_e2e_bridge.py = OK
test_axis1_execution_bridge_contract.py = OK
test_external_llm_authoring_lane.py = OK
test_authoring_continuous_improvement.py = OK
test_frozen_legacy_core_guard.py = OK
```

Step 14 중 tamper test가 immutable tuple을 직접 수정한 test defect가 1건 있었고 test fixture만 수정 후 focused + regression이 모두 PASS했다.

---

## 현재 Step 15 구현

### 문서 authority 정리

신규:

```text
DSL_DOCUMENT_AUTHORITY_INDEX.md
```

지위:

```text
ACTIVE AUTHORITY
FROZEN AUDIT / MIGRATION EVIDENCE
HISTORICAL / NON-AUTHORITATIVE
```

과거 `DSL_LIVE_STUDIO_FEATURE_CATALOG_V2/V3/V4`, `CTX*.md`, `E*.md`, `H*.md`, `ADAPTIVE_*.md` 등은 삭제하지 않고 historical evidence로 보존한다. 현재 기능지원/아키텍처 SSOT로 사용하지 않는다.

정렬한 active 문서:

```text
CURRENT_STATE.md
DSL_THREE_AXIS_FINAL_TARGET.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
axes/axis1_dsl/README.md
axes/axis2_selection/README.md
```

현재 exact 책임:

```text
AXIS 1 = single-instrument DSL/runtime/execution
AXIS 2 = exact-PIT selection semantics / filter / rank / top-N / evidence
AXIS 3 = Condition/Strategy immutable version lifecycle + orchestration
Bridge = versioned Request -> Response composition
External LLM = proposal-only
Continuous Improvement = analysis-only / no automatic mutation
```

Condition:

```text
selection semantics = AXIS 2
artifact lifecycle  = AXIS 3
```

최종 호출 순서:

```text
AXIS 2 CandidateSet
 -> AXIS 3 promoted exact artifacts + RunPlan
 -> Bridge all-candidate preflight
 -> AXIS 1 one-symbol execution
```

### Repo compliance audit

신규:

```text
compliance/__init__.py
compliance/repo_audit.py
tests/test_repo_wide_compliance.py
```

read-only deterministic audit:

```text
axis sibling direct imports
frozen root core runtime imports
Bridge contract data-only
Bridge composition allowlist
External authoring execution authority leak
Continuous Improvement axis/Bridge authority leak
critical regression skip/expectedFailure
active document ownership/order
legacy document disposition
stable report hash
```

Frozen core tree exact 검증은 기존 guard test를 그대로 사용한다.

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_repo_wide_compliance.py" -v
python -m unittest discover -s tests -p "test_final_natural_language_e2e.py" -v
python -m unittest discover -s tests -p "test_three_axis_e2e_bridge.py" -v
python -m unittest discover -s tests -p "test_axis1_execution_bridge_contract.py" -v
python -m unittest discover -s tests -p "test_axis2_selection_engine.py" -v
python -m unittest discover -s tests -p "test_axis3_crud_orchestration.py" -v
python -m unittest discover -s tests -p "test_external_llm_authoring_lane.py" -v
python -m unittest discover -s tests -p "test_authoring_continuous_improvement.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 15 final checkpoint를 만들고 모든 계획된 작업을 COMPLETE로 닫는다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
