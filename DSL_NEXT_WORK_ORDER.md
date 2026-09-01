# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 12
CURRENT_STEP_NAME = External LLM Authoring Lane implementation
CURRENT_SUBSTEP = 12-1 generated contract prompt + strict draft validation + bounded correction workflow
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 migration user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능/검증 user-local PASS
STEP 6 COMPLETE = capability/diagnostic registry user-local PASS
STEP 7 COMPLETE = Bridge common + AXIS 1 execution contract user-local PASS
STEP 8 COMPLETE = AXIS 2 exact-as-of snapshot contract user-local PASS
STEP 9 COMPLETE = AXIS 2 deterministic selection engine user-local PASS
STEP 10 COMPLETE = AXIS 3 Condition/Strategy CRUD + orchestration user-local PASS
STEP 11 COMPLETE = AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge user-local PASS
  -> STEP11_THREE_AXIS_E2E_BRIDGE_CHECKPOINT_2026-09-01.md
```

Step 11 user-local evidence:

```text
test_three_axis_e2e_bridge.py = OK
test_axis3_crud_orchestration.py = OK
test_axis2_selection_engine.py = OK
test_axis1_execution_bridge_contract.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 12 현재 — External LLM Authoring Lane

목표:

```text
자연어 사용자 요청
 -> 현재 machine contract가 포함된 prompt
 -> Human -> External LLM
 -> untrusted external_strategy_draft/v1
 -> local deterministic validation
 -> ACCEPTED_DRAFT / correction / blocked
```

외부 LLM은 proposal-only다. Backtest/live/order/CRUD promotion 권한을 가지지 않는다.

### 구현

```text
authoring/__init__.py
authoring/external_llm/__init__.py
authoring/external_llm/manifest.py
authoring/external_llm/prompt_builder.py
authoring/external_llm/validator.py
authoring/external_llm/workflow.py
skills/external_llm_strategy_authoring/SKILL.md
tests/test_external_llm_authoring_lane.py
```

기존 strict schemas 재사용:

```text
authoring/contracts/external_strategy_draft.v1.schema.json
authoring/contracts/authoring_validation_event.v1.schema.json
```

### Generated authoring manifest

AXIS 1 capability truth는 Step 6 machine registry에서 직접 가져온다.

```text
capability_registry_hash
supported / unavailable capability IDs
registered function signature/output/lookback/warmup/causality contract
feature capability boundary/status/limitations
registered order commands
```

AXIS 2 feature/data-source machine registry는 아직 별도 SSOT가 없으므로 Step 12가 이름을 추측하지 않는다.
호출자가 현재 authoring request에서 허용되는 exact feature/data-source/context identity를 명시적으로 주입한다.

```text
feature_ids[]
data_source_ids[]
context_feature_types{}
```

빈/unknown/중복 identity는 fail-closed다.

### Prompt builder

초기 prompt는 다음을 포함한다.

```text
verbatim user request
request_id
machine manifest + manifest hash
current supported/unavailable capabilities
function contracts
exact AXIS2 feature/data-source/context inventory
order commands
strict external_strategy_draft/v1 schema
no-invention / PIT causality / axis-boundary rules
```

정적 `SKILL.md`의 과거 capability 목록을 authority로 사용하지 않는다.
SKILL v2는 generated manifest가 현재 권위임을 명시한다.

### Deterministic validation pipeline

고정 순서:

```text
SCHEMA
 -> CAPABILITY
 -> DATA_SOURCE
 -> AXIS_BOUNDARY
 -> TIMEFRAME_CAUSALITY
 -> DSL_PARSER
 -> DSL_SEMANTIC
 -> COMPILE_DRY_RUN
 -> PERSISTENCE(non-writing readiness)
 -> ACCEPTANCE
```

규칙:

```text
unknown schema/field/opaque/nonfinite reject
unknown capability/function/command reject
known-but-unavailable capability -> BLOCKED_NEEDS_CAPABILITY
unknown feature/data-source/context reject
selection과 single-instrument strategy 의미 혼합 reject
nearest/fill-forward/interpolation mode reject
strategy_plan timeframe과 DSL timeframe drift reject
현재 AXIS1 lowering + Parser + Semantic + Runtime facade로 deterministic dry-run
material assumption은 human acceptance 전 BLOCKED_USER_CLARIFICATION
blocking unresolved question도 BLOCKED_USER_CLARIFICATION
```

`ACCEPTED_DRAFT`는 실행/저장/승격을 의미하지 않는다.
정확한 PIT snapshot binding과 AXIS 3 artifact 생성/승격은 기존 3축 workflow 권한에 남는다.

### Correction workflow

```text
original user request
+ previous structured draft
+ exact validator error
+ same current manifest
+ same response schema
 -> correction prompt
```

사용자 의도를 임의 변경하지 않으며, already-valid field를 보존하도록 요구한다.
iteration은 bounded다. 자동 외부 LLM 호출은 하지 않고 Human-mediated workflow만 제공한다.

### Validation event

각 결과는 기존 `authoring_validation_event/v1` 형태로 deterministic event를 만들 수 있다.

```text
request_id / draft_id / iteration
prompt/skill/validator versions
final validation stage/status/error/root-cause
resolution class
```

이는 Step 13 continuous-improvement 분석 입력이지 실행 권한이 아니다.

### Step 12 경계

```text
External LLM output eval/exec 금지
외부 URL/provider 자동 호출 금지
unknown function/feature 자동 등록 금지
validation failure 자동 의미변경 금지
Authoring Lane이 AXIS2 selection 실행하지 않음
Authoring Lane이 AXIS3 CRUD/promotion 실행하지 않음
Authoring Lane이 AXIS1 backtest/order 실행하지 않음
compile dry-run만 AXIS1 deterministic validation authority 사용
frozen core import/수정 없음
```

Step 12 완료 조건:

```text
current AXIS1 machine registry -> authoring manifest exact PASS
supported/unavailable capability separation PASS
exact supplied AXIS2 feature/data-source/context inventory PASS
prompt contains verbatim request + current contracts + strict output schema PASS
strict draft schema/unknown/opaque/nonfinite fail-closed PASS
unknown vs unavailable capability handling PASS
unknown feature/data-source/context handling PASS
axis-boundary + PIT causality + timeframe drift fail-closed PASS
AXIS1 parser/semantic/compile dry-run validation PASS
material assumptions require explicit human acceptance PASS
correction prompt preserves request_id/intent + exact validator errors PASS
bounded human-mediated iteration PASS
authoring_validation_event deterministic PASS
no Axis2/Axis3 execution or frozen-core authority leak PASS
Step 11 E2E Bridge regression PASS
Step 10 CRUD/orchestration regression PASS
frozen core guard PASS
focused user-local Step 12 test PASS
```

Step 12 PASS + checkpoint 전 Step 13 시작 금지.

---

## 이후 고정 순서

```text
13 Continuous Improvement analysis tooling
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
축간 연결 = versioned Request -> Response only
future value / nearest-time / fill-forward / default synthesis 금지
unknown capability/data identity 추측 금지
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
