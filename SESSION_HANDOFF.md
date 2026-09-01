# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 13 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> External LLM은 proposal-only, Continuous Improvement는 evidence-analysis-only다. 반복 오류가 보여도 시스템이 자동으로 Prompt/Skill/Validator/DSL을 변경하지 않는다.

---

## 현재 작업

```text
CURRENT_STEP = 13
CURRENT_SUBSTEP = 13-1 validation-event aggregation + evidence-gated remediation recommendations
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Step 4 AXIS 1 migration = COMPLETE / USER-LOCAL PASS
Step 5 AXIS 1 신규 DSL 기능/검증 = COMPLETE / USER-LOCAL PASS
Step 6 capability/diagnostic registry = COMPLETE / USER-LOCAL PASS
Step 7 Bridge common + AXIS 1 execution contract = COMPLETE / USER-LOCAL PASS
Step 8 AXIS 2 exact-as-of snapshot contract = COMPLETE / USER-LOCAL PASS
Step 9 AXIS 2 selection engine = COMPLETE / USER-LOCAL PASS
Step 10 AXIS 3 Condition/Strategy CRUD + orchestration = COMPLETE / USER-LOCAL PASS
Step 11 three-axis E2E Bridge = COMPLETE / USER-LOCAL PASS
Step 12 External LLM Authoring Lane = COMPLETE / USER-LOCAL PASS
```

최근 checkpoint:

```text
STEP12_EXTERNAL_LLM_AUTHORING_CHECKPOINT_2026-09-01.md
```

Step 12 user-local evidence:

```text
test_external_llm_authoring_lane.py = OK
test_three_axis_e2e_bridge.py = OK
test_axis3_crud_orchestration.py = OK
test_axis1_capability_diagnostic_registry.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## 현재 Step 13 구현

구현:

```text
authoring/continuous_improvement/analyzer.py
authoring/continuous_improvement/authoring_improvement_report.v1.schema.json
tests/test_authoring_continuous_improvement.py
```

### 입력

Step 12의 구조화 validation event만 사용한다.

```text
authoring_validation_event/v1
```

분석 전 다음을 fail-closed 검사한다.

```text
schema/field/enum
canonical event_id hash
duplicate event
duplicate request+iteration
```

raw user request나 외부 LLM 원문을 보고서에 복제하지 않는다.

### 분석 결과

```text
first-pass acceptance
평균 correction iteration
stage/error/root-cause별 실패율/빈도
blocked capability 빈도
unknown feature / ambiguity / repeat error 비율
prompt/skill/validator version별 결과 비교
request별 iteration summary
```

입력 event 순서와 무관하게 동일 report hash를 만든다.

### 개선 후보 생성 규칙

반복 evidence가 threshold에 미달하면 즉시 개선하지 않고 deferred candidate로 남긴다.

특히 parser/semantic/capability 같은 AXIS 1 변경은:

```text
반복 발생
AND 서로 다른 intent evidence 기본 2개 이상
```

일 때만 human review용 generic DSL tranche 후보가 된다.

같은 한 요청의 correction loop 반복만으로 DSL 변경 후보를 만들지 않는다.

좁은 경계 우선:

```text
Prompt 문제 -> Prompt
Skill 문제 -> Skill
LLM draft 문제 -> correction prompt/diagnostics
Validator/schema 문제 -> 해당 validator/schema
Data/Axis contract 문제 -> 해당 contract
사용자 의미 모호성 -> human clarification
실제 generic DSL gap -> 충분한 독립 evidence 뒤 AXIS 1 tranche 후보
```

모든 report는 다음을 고정한다.

```text
automatic_mutation = false
human_approval_required = true
```

### 금지

```text
AXIS 1/2/3 내부 import 없음
frozen core import/수정 없음
Prompt/Skill/Validator 자동 rewrite 없음
DSL/capability 자동 추가 없음
external provider/model 호출 없음
console text scraping 없음
```

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

---

## 다음 순서

```text
13 Continuous Improvement tooling          CURRENT
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_authoring_continuous_improvement.py" -v
python -m unittest discover -s tests -p "test_external_llm_authoring_lane.py" -v
python -m unittest discover -s tests -p "test_three_axis_e2e_bridge.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 13 checkpoint 후 Step 14 final natural-language E2E acceptance로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
