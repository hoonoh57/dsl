# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 13
CURRENT_STEP_NAME = Continuous Improvement analysis tooling
CURRENT_SUBSTEP = 13-1 validation-event aggregation + evidence-gated remediation recommendations
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 migration user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능/검증 user-local PASS
STEP 6 COMPLETE = capability/diagnostic registry user-local PASS
STEP 7 COMPLETE = Bridge common + AXIS 1 execution contract user-local PASS
STEP 8 COMPLETE = AXIS 2 exact-as-of snapshot contract user-local PASS
STEP 9 COMPLETE = AXIS 2 deterministic selection engine user-local PASS
STEP 10 COMPLETE = AXIS 3 Condition/Strategy CRUD + orchestration user-local PASS
STEP 11 COMPLETE = AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge user-local PASS
STEP 12 COMPLETE = External LLM Authoring Lane user-local PASS
  -> STEP12_EXTERNAL_LLM_AUTHORING_CHECKPOINT_2026-09-01.md
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

## Step 13 현재 — Continuous Improvement analysis tooling

목표:

```text
authoring_validation_event/v1 evidence
 -> deterministic aggregation
 -> failure/retry/version metrics
 -> recurrence + independent-intent gate
 -> human-reviewed remediation candidates
```

분석기는 어떠한 코드/Prompt/Skill/Registry/DSL도 자동 수정하지 않는다.

### 구현

```text
authoring/continuous_improvement/__init__.py
authoring/continuous_improvement/analyzer.py
authoring/continuous_improvement/authoring_improvement_report.v1.schema.json
tests/test_authoring_continuous_improvement.py
```

### Input evidence contract

Step 12의 `authoring_validation_event/v1`만 소비한다.

```text
strict field/schema/enum validation
event_id canonical hash 재검증
duplicate event_id reject
duplicate request_id + iteration reject
raw user request / arbitrary payload 추가 금지
```

원문 자연어와 외부 LLM 응답 전체를 집계 보고서에 복제하지 않는다.

### 운영 metric

```text
first_pass_acceptance_rate
mean_correction_iterations
non_pass_event_rate
capability_block_rate
schema/parser/semantic failure rate
unknown_feature_rate
ambiguous_intent_rate
repeat_error_rate
stage별 failure rate
error/root-cause 빈도
blocked capability 빈도
prompt/skill/validator version별 failure/acceptance count
request별 iteration summary
```

같은 event set은 입력 순서와 무관하게 같은 `event_set_hash` / `report_hash`를 생성한다.

### Evidence-gated recommendation

기본 recurrence threshold 미만은 remediation recommendation으로 승격하지 않고 deferred evidence로 남긴다.

특히 generic DSL 변경 후보:

```text
DSL_PARSER_GAP
DSL_SEMANTIC_GAP
DSL_CAPABILITY_GAP
```

는 recurrence뿐 아니라 **서로 다른 intent evidence**가 기본 2개 이상 있어야 parser/semantic/capability tranche 후보가 된다.

같은 요청의 correction loop에서 동일 오류가 반복된 것만으로 DSL을 변경하지 않는다.

개선 우선권은 좁은 경계를 유지한다.

```text
PROMPT_DEFECT -> Prompt wording/examples
SKILL_GAP -> Skill guidance
LLM_DRAFT_DEFECT -> correction prompt/diagnostics
schema/validator gap -> schema/validator
DATA/AXIS contract gap -> 해당 contract
USER_INTENT_AMBIGUITY -> human clarification
generic DSL gap -> 증거 충족 시에만 AXIS1 micro-tranche 후보
```

모든 recommendation은:

```text
requires_human_approval = true
automatic_mutation = false
```

### Step 13 경계

```text
analysis module은 AXIS 1/2/3 내부 import 없음
frozen core import/수정 없음
Prompt/Skill/Validator 자동 rewrite 없음
capability registry 자동 등록 없음
DSL parser/semantic/runtime 자동 수정 없음
external model/provider/network 호출 없음
raw console scraping 없음
```

Step 13 완료 조건:

```text
validation event strict/tamper/duplicate fail-closed PASS
input order independent deterministic report/hash PASS
first-pass/correction/failure metrics PASS
stage/error/root-cause/capability aggregation PASS
prompt/skill/validator version comparison PASS
repeat-error metric PASS
recurrence threshold gate PASS
single-intent repeated DSL gap cannot promote DSL change PASS
multiple independent intents can surface generic DSL tranche candidate PASS
user ambiguity remains clarification candidate, not DSL change PASS
report marks human approval required / auto mutation false PASS
analysis layer AXIS/frozen-core/provider isolation PASS
Step 12 authoring regression PASS
Step 11 E2E Bridge regression PASS
frozen core guard PASS
focused user-local Step 13 test PASS
```

Step 13 PASS + checkpoint 전 Step 14 시작 금지.

---

## 이후 고정 순서

```text
14 Final natural-language E2E acceptance
15 Legacy docs disposition + repo-wide compliance audit
```

---

## 절대 원칙

```text
frozen legacy core 수정 금지
AXIS 1 = single-instrument deterministic execution
AXIS 2 = immutable PIT selection semantics
AXIS 3 = versioned Condition/Strategy lifecycle + orchestration
External LLM = proposal only
Continuous Improvement = evidence analysis only, automatic mutation 없음
축간 연결 = versioned Request -> Response only
future value / nearest-time / fill-forward / default synthesis 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
