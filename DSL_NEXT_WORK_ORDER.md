# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-09-01 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 현재 번호가 user-local 검증과 checkpoint를 통과하기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 6
CURRENT_STEP_NAME = AXIS 1 machine-readable capability/diagnostic registry
CURRENT_SUBSTEP = 6-1 canonical capability + diagnostic registry
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
STEP 5 COMPLETE = AXIS 1 신규 DSL 기능 개발 + 검증 전체 user-local PASS
  5-1 multi-output + destructuring
  5-2 tuple-aware generic projection
  5-3 capability/function metadata completeness
  5-4 user-defined functions
  5-5 bounded loops
  5-6 on_tick/on_fill commit/rollback
  5-7 partial fills / partial exits
  5-8 pyramiding / multi-position accounting
  5-9 full reference differential fixtures
  5-10 full-engine batch/streaming parity
  -> STEP5_10_FULL_ENGINE_PARITY_CHECKPOINT_2026-09-01.md
```

5-10 user-local evidence:

```text
test_axis1_full_engine_parity.py = OK
test_axis1_reference_differential.py = OK
test_axis1_pyramiding_execution.py = OK
test_axis1_partial_execution.py = OK
test_frozen_legacy_core_guard.py = OK
```

---

## Step 6 현재 — machine-readable capability/diagnostic registry

목표:

```text
AXIS 1이 무엇을 지원하고 무엇을 지원하지 않는지,
각 기능의 경계/권위/검증근거가 무엇인지,
각 진단값의 producer/path/authority/shape가 무엇인지
하나의 deterministic machine-readable registry에서 조회 가능하게 한다.
```

구현:

```text
axes/axis1_dsl/core/capability_diagnostic_registry.py
tests/test_axis1_capability_diagnostic_registry.py
```

기존 Step 5-3 관계:

```text
Step 5-3 capability_metadata = 함수 단위 output/lookback/warmup/NaN/causality metadata
Step 6 registry = 위 함수 metadata를 재사용 + DSL/runtime/execution/projection/verification capability + diagnostic contract를 한 manifest로 집계
```

Registry contract:

```text
schema = axis1_capability_diagnostic_registry/v1
canonical deterministic registry_hash 제공
모든 registered single/multi-output function을 자동 포함
feature capability는 SUPPORTED / SUPPORTED_WITH_BOUNDARY / VERIFICATION_ONLY / NOT_SUPPORTED / NOT_CERTIFIED로 명시
unknown capability/diagnostic 조회는 fail-closed
require_supported는 실행 가능한 capability만 허용
```

명시적 feature 범위:

```text
multi-output
user functions
bounded loops
exact parent context
confirmed MTF
intrabar provisional state
partial fills / partial exits
same-direction pyramiding
non-computing generic projection
reference differential verification
batch/stream parity verification
```

명시적 negative/boundary capability:

```text
execution.hedging = NOT_SUPPORTED
runtime.optimized_incremental_kernel = NOT_CERTIFIED
verification-only capability는 product execution support로 오인하지 않음
```

Diagnostic registry 범위:

```text
batch signal counts / rejections / broker history
parent-context / entry-policy diagnostics
bounded-loop / user-function / multi-output / projection facade diagnostics
intrabar transaction audit
partial execution broker/accounting snapshot
pyramiding lot/accounting snapshot
runtime/backtest parity report
```

Step 6 중요 원칙:

```text
registry는 선언/조회 계층이며 계산 kernel이 아님
execution/runtime/indicator/provider를 import하지 않음
frozen core import/수정 없음
검증결과를 임의로 SUPPORTED로 승격하지 않음
NOT_SUPPORTED/NOT_CERTIFIED 상태도 registry에서 숨기지 않음
```

Step 6 완료 조건:

```text
registry schema + deterministic hash PASS
모든 Step 5-3 function capability metadata가 exact registry record로 포함
Step 5 feature support/boundary/negative status machine-readable PASS
현재 Axis1BacktestEngine 주요 diagnostic output path 등록 PASS
unknown/unsupported capability fail-closed PASS
verification-only와 product support 분리 PASS
registry module execution/runtime/indicator/frozen-core import isolation PASS
기존 capability metadata test PASS
full-engine parity 회귀 PASS
frozen core guard PASS
focused user-local registry test PASS
```

Step 6 PASS + checkpoint 전 Step 7 시작 금지.

---

## 이후 고정 순서

```text
7 Bridge common + AXIS 1 execution contract
8 AXIS 2 exact-as-of snapshot contract
9 AXIS 2 selection engine / core selectors
10 AXIS 3 Condition / Strategy CRUD + orchestration
11 AXIS 2 -> AXIS 3 -> AXIS 1 versioned E2E Bridge
12 External LLM Authoring Lane implementation
13 Continuous Improvement analysis tooling
14 Final natural-language E2E acceptance
15 Legacy docs disposition + repo-wide compliance audit
```

---

## 절대 원칙

```text
frozen legacy core 수정 금지
검증된 migrated core를 신규기능 때문에 불필요하게 흔들지 않음
새 기능은 가능한 한 명시적 contract + 격리된 facade/session/registry로 추가
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 SESSION_HANDOFF.md에 함께 반영한다.
