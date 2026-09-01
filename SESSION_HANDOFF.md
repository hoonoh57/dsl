# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 12 / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 외부 LLM은 초안 제안만 한다. 기능/데이터/축 경계/DSL 수용 여부는 local deterministic validator가 결정하며, 실행/저장/승격은 기존 AXIS 1/2/3 권한에 남는다.

---

## 현재 작업

```text
CURRENT_STEP = 12
CURRENT_SUBSTEP = 12-1 generated contract prompt + strict draft validation + bounded correction workflow
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
```

최근 checkpoint:

```text
STEP11_THREE_AXIS_E2E_BRIDGE_CHECKPOINT_2026-09-01.md
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

## 현재 Step 12 구현

구현 파일:

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

기존 schema:

```text
authoring/contracts/external_strategy_draft.v1.schema.json
authoring/contracts/authoring_validation_event.v1.schema.json
```

### Authoring manifest

AXIS 1 기능은 Step 6 capability registry에서 직접 생성한다.

```text
capability registry hash
supported / unavailable capability IDs
function signature / outputs / lookback / warmup / causality
feature capability status / boundary / limitation
order commands
```

AXIS 2 feature/data-source registry가 아직 별도 machine SSOT로 만들어지지 않았으므로 이름을 추측하지 않는다.
각 authoring request가 사용할 exact inventory를 명시적으로 받는다.

```text
feature_ids
data_source_ids
context_feature_types
```

### Prompt

`build_initial_prompt()`:

```text
verbatim user request
request identity
current manifest + hash
strict output schema
no-invention / point-in-time / axis separation rule
```

`SKILL.md`는 v2로 정리했고 정적 capability snapshot을 제거했다.
현재 권위는 prompt에 포함된 generated manifest다.

### Validation

고정 pipeline:

```text
SCHEMA
CAPABILITY
DATA_SOURCE
AXIS_BOUNDARY
TIMEFRAME_CAUSALITY
DSL_PARSER
DSL_SEMANTIC
COMPILE_DRY_RUN
PERSISTENCE(non-writing)
ACCEPTANCE
```

결과:

```text
ACCEPTED_DRAFT
REQUIRES_CORRECTION
BLOCKED_NEEDS_CAPABILITY
BLOCKED_USER_CLARIFICATION
```

핵심 fail-closed:

```text
unknown capability/function/feature/source/context 거부
known unavailable capability는 명시적 blocked
nearest/fill-forward/interpolation 거부
selection/strategy axis 혼합 거부
strategy timeframe vs DSL timeframe drift 거부
AXIS 1 current lowering/parser/semantic/runtime로 compile dry-run
blocking question/material assumption은 human 확인 전 blocked
```

`ACCEPTED_DRAFT`는 backtest 실행이나 Strategy/Condition persistence/promotion이 아니다.

### Human correction loop

`HumanMediatedAuthoringSession`:

```text
initial prompt 생성
external structured draft 제출
validator 결과
REQUIRES_CORRECTION이면 exact error correction prompt
human assumption acceptance
bounded iteration
```

외부 모델 API를 자동 호출하지 않는다.

### Validation event

`build_validation_event()`은 deterministic `authoring_validation_event/v1` payload를 만든다.
Step 13에서 반복 실패/root-cause 분석 입력으로 사용할 수 있다.

### 경계

```text
Axis2 selection 실행 없음
Axis3 CRUD/promotion 실행 없음
Axis1 backtest/order 실행 없음
Axis1 compile dry-run만 validation authority로 사용
external output eval/exec 없음
external URL/provider 자동 호출 없음
frozen core import/수정 없음
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
12 External LLM Authoring Lane                  CURRENT
13 Continuous Improvement tooling
14 natural-language E2E acceptance
15 legacy docs + repo-wide compliance audit
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_external_llm_authoring_lane.py" -v
python -m unittest discover -s tests -p "test_three_axis_e2e_bridge.py" -v
python -m unittest discover -s tests -p "test_axis3_crud_orchestration.py" -v
python -m unittest discover -s tests -p "test_axis1_capability_diagnostic_registry.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

모두 PASS하면 Step 12 checkpoint 후 Step 13 Continuous Improvement analysis tooling으로 이동한다.

실패 시 test defect / feature defect / authority drift / environment issue / unknown으로 먼저 분류하고 assertion/contract를 약화하지 않는다.
