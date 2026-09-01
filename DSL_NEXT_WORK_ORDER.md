# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / FINAL STEP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 Step 15가 user-local 검증과 final checkpoint를 통과하기 전 repo-wide final PASS를 선언하지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 15
CURRENT_STEP_NAME = Legacy docs disposition + repo-wide compliance audit
CURRENT_SUBSTEP = 15-1 authority alignment + deterministic architecture/import/test-hygiene audit
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1~13 COMPLETE = USER-LOCAL PASS
STEP 14 COMPLETE = Final natural-language E2E acceptance USER-LOCAL PASS
  -> STEP14_FINAL_NATURAL_LANGUAGE_E2E_CHECKPOINT_2026-09-01.md
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

검증 중 immutable tuple을 직접 변조하던 focused test defect 1건은 test fixture만 수정했고 제품 assertion/로직은 약화하지 않았다.

---

## Step 15 현재 — Legacy docs disposition + repo-wide compliance audit

목표:

```text
누적 historical 문서를 삭제하지 않고 지위를 명확히 분리
+ active authority 문서의 현재 3축 구조를 exact 정렬
+ current product source import graph audit
+ Bridge contract data-only audit
+ External LLM / Continuous Improvement 권한 누수 audit
+ critical regression skip/expectedFailure audit
+ frozen core exact tree regression
```

### 문서 disposition

신규 authority index:

```text
DSL_DOCUMENT_AUTHORITY_INDEX.md
```

문서 지위를 세 층으로 고정한다.

```text
ACTIVE AUTHORITY
FROZEN AUDIT / MIGRATION EVIDENCE
HISTORICAL / NON-AUTHORITATIVE
```

Historical 문서는 당시 evidence 보존을 위해 삭제하지 않는다.

대표 historical 범주:

```text
DSL_LIVE_STUDIO_FEATURE_CATALOG_V2/V3/V4.md
CTX*.md
E*.md
H*.md
ADAPTIVE_*.md
과거 개별 integration / experiment 기록
```

과거 static Feature Catalog count는 current support SSOT가 아니다.

```text
current support SSOT = axes/axis1_dsl/core/capability_diagnostic_registry.py
```

### Active authority drift remediation

정렬한 문서:

```text
CURRENT_STATE.md
DSL_THREE_AXIS_FINAL_TARGET.md
DSL_THREE_AXIS_MODULE_BOUNDARY.md
axes/axis1_dsl/README.md
axes/axis2_selection/README.md
```

제거한 stale authority:

```text
AXIS1 migration not started 표현
AXIS2가 Condition CRUD lifecycle을 소유한다는 표현
AXIS2 -> AXIS1 -> AXIS3 실행순서 표현
REMEDIATION_REQUIRED stale current-state 표시
```

최종 책임:

```text
AXIS1 = single-instrument deterministic DSL/runtime/execution
AXIS2 = immutable exact-PIT selection semantics + CandidateSet evidence
AXIS3 = versioned Condition/Strategy artifact lifecycle + orchestration
Bridge = versioned cross-axis composition
External LLM = proposal only
Continuous Improvement = evidence analysis only; automatic mutation 없음
```

Condition 책임은 다음처럼 분리한다.

```text
selection semantics = AXIS2
artifact lifecycle  = AXIS3
```

### Deterministic audit implementation

```text
compliance/__init__.py
compliance/repo_audit.py
tests/test_repo_wide_compliance.py
```

Audit은 read-only다.

검사:

```text
AXIS sibling direct import 없음
current axes/bridges/authoring/acceptance/compliance -> frozen root core runtime import 없음
bridges/contracts data-only
AXIS1 Bridge가 AXIS2/3 직접 import하지 않음
three-axis Bridge가 AXIS1 internals를 bypass하지 않음
External authoring이 AXIS2/3 또는 execution Bridge를 호출하지 않음
Continuous Improvement가 axes/bridges를 import하지 않음
critical current regression test에 skip/expectedFailure bypass 없음
active docs의 최종 ownership/execution order exact
legacy document disposition explicit
동일 repository -> 동일 audit report/hash
```

Frozen `core/` tree 자체의 exact immutability는 기존 `test_frozen_legacy_core_guard.py`가 계속 별도 authority다.

### Step 15 완료 조건

```text
test_repo_wide_compliance.py PASS
final natural-language E2E regression PASS
three-axis Bridge regression PASS
AXIS1 execution Bridge regression PASS
AXIS2 selection regression PASS
AXIS3 CRUD/orchestration regression PASS
External LLM authoring regression PASS
Continuous Improvement regression PASS
frozen legacy core guard PASS
```

모두 user-local PASS 후:

```text
STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md 생성
CURRENT_STATE = FINAL USER-LOCAL PASS
DSL_NEXT_WORK_ORDER = ALL PLANNED STEPS COMPLETE
SESSION_HANDOFF = final stable state
```

그 전에는 final PASS를 선언하지 않는다.

---

## 절대 원칙

```text
frozen legacy core 수정 금지
AXIS 1/2/3 권한 혼합 금지
cross-axis 연결은 versioned Bridge only
future / nearest / fill-forward / interpolation / default synthesis 금지
특정 전략 Core shortcut 금지
External LLM execution authority 금지
Continuous Improvement automatic mutation 금지
historical 문서를 current SSOT로 부활시키지 않음
검증완화/skip/compatibility exception 금지
```
