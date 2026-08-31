# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> 방침은 즉시 기록하되, 현재 번호가 검증되기 전 다음 번호로 넘어가지 않는다.

---

## 현재 포인터

```text
CURRENT_STEP = 5
CURRENT_STEP_NAME = AXIS 1 신규 DSL 기능 개발
CURRENT_SUBSTEP = 5-3 capability/function metadata completeness
SUBSTEP_STATUS = WRITTEN / REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 COMPLETE = AXIS 1 9개 migration boundary 모두 user-local PASS
STEP 5-1 COMPLETE = tuple / multi-output + destructuring user-local PASS
  -> STEP5_1_MULTI_OUTPUT_CHECKPOINT_2026-08-31.md
STEP 5-2 COMPLETE = tuple-aware generic projection user-local PASS
  -> STEP5_2_GENERIC_PROJECTION_CHECKPOINT_2026-08-31.md
```

---

## 5-3 현재 — capability/function metadata completeness

목표:

```text
등록된 모든 AXIS 1 함수와 multi-output 기능에 대해
기계가 읽을 수 있는 실행/출력/인과성 정보를 빠짐없이 제공
```

현재 구현:

```text
axes/axis1_dsl/core/capability_metadata.py
tests/test_axis1_capability_metadata.py
```

Metadata contract:

```text
name / mode / category / signature
output_names / output_types
lookback / warmup / nan_policy
incremental_identity / reference_source / causality
```

중요 원칙:

```text
기존 migrated parser/runtime/backtest 동작 변경 없음
frozen core 수정 없음
새 등록 함수가 metadata policy 없이 추가되면 fail-closed
확인되지 않은 incremental identity를 PASS로 과장하지 않음
현재 full-engine streaming identity 미검증 상태는 명시적으로 NOT_YET_CERTIFIED 기록
MTF는 confirmed parent only + nearest/fill-forward/default 금지 명시
multi-output는 component 이름/type을 기존 typed contract와 exact 일치
```

5-3 완료 조건:

```text
FUNCTION_SPECS 모든 항목 metadata coverage 100%
MULTI_OUTPUT_SPECS 모든 항목 metadata coverage 100%
output type/name contract registry와 exact 일치
lookback/warmup/NaN/reference/causality 필드 공백 없음
single-output와 multi-output 동일 함수명은 mode로 구분
manifest deterministic
new metadata module frozen-core import 없음
frozen core guard PASS
user-local focused test PASS
```

5-3 PASS + checkpoint 전 5-4 시작 금지.

---

## 이후 고정 순서

```text
5-4 user-defined functions
5-5 bounded loops
5-6 on_tick / on_fill commit/rollback
5-7 partial fills / partial exits
5-8 pyramiding / multi-position accounting
5-9 full reference differential fixtures
5-10 full-engine batch/streaming parity
6 AXIS 1 machine-readable capability/diagnostic registry
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
새 기능은 가능한 한 명시적 contract + lowering/facade로 격리
fail-closed 유지
검증완화/compatibility exception 금지
현재 순서 건너뛰기 금지
```

중요 방침/로직/순서 변경은 그 턴에 이 문서와 `SESSION_HANDOFF.md`에 함께 반영한다.
