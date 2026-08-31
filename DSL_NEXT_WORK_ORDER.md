# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 작업 순서 SSOT다.

> **방침은 즉시 기록하되, 구현은 현재 번호/경계가 끝나기 전 다음으로 넘어가지 않는다.**

새 아이디어는 PARKING LOT에 기록하고 현재 작업을 계속한다. 순서를 바꾸려면 사용자 명시 결정 후 이 문서를 먼저 수정한다.

---

## 현재 포인터

```text
CURRENT_STEP = 4
CURRENT_STEP_NAME = AXIS 1 경계별 이식 + parity
CURRENT_BOUNDARY = 3 Assignment Flow + Semantic
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
STEP 2 COMPLETE = AXIS 1 migration manifest + 9개 boundary 순서
STEP 3 COMPLETE = Frozen Core 보호 gate user-local PASS
STEP 4 / BOUNDARY 1 COMPLETE = Parser / AST user-local parity PASS
STEP 4 / BOUNDARY 2 COMPLETE = Function Registry user-local parity PASS
```

현재 경계를 완료할 때마다:

```text
결과 기록 -> PASS/FAIL 원인분류 -> authority/handoff/checkpoint 갱신 -> 다음 경계
```

---

## 1. 기존 DSL 남은 기능 점검 — COMPLETE

JMA 접근, projection, Strategy CRUD 경계를 실제 코드/테스트로 확인했다.

---

## 2. 새 DSL 이식 설계도 + 경계 순서 — COMPLETE

9개 boundary:

```text
1 Parser / AST
2 Function Registry
3 Assignment Flow + Semantic
4 Indicator Kernel
5 State + Bar Runtime
6 MTF + Read-Only Context Binding
7 DSL Runtime
8 Broker
9 Backtest + Projection Output
```

상세 mapping/exclusion/parity는 `DSL_AXIS1_MIGRATION_MANIFEST.md`가 권한이다.

---

## 3. Frozen Core 보호 gate — COMPLETE

User-local guard PASS 확인. 기존 `core/`는 영구 immutable reference다.

---

## 4. AXIS 1 경계별 이식 + parity — CURRENT

원칙:

```text
한 boundary 이식
 -> focused parity
 -> frozen comparison
 -> regression
 -> checkpoint
 -> 다음 boundary
```

완료:

```text
Boundary 1 Parser / AST = USER-LOCAL PASS
Boundary 2 Function Registry = USER-LOCAL PASS
```

현재:

```text
Boundary 3 = Assignment Flow + Semantic
source = core/assignment_flow.py + core/dsl_semantic.py
target = axes/axis1_dsl/core/assignment_flow.py + axes/axis1_dsl/core/dsl_semantic.py
mode = behavior-preserving migration with internal import rewrite
status = source written / focused parity test written / waiting user-local PASS
```

Boundary 3 완료 조건:

```text
assignment before/after on_bar partition 동일
valid DSL semantic result 동일
invalid DSL fail-closed 동일
value type 판정 동일
function arity/type error 동일
error line/column/code 동일
new semantic boundary에 frozen-core runtime import 없음
frozen core guard PASS
focused user-local parity PASS
```

금지:

```text
전체 core/ 일괄복사
migration 중 신규기능 추가
legacy core 수정
parity 차이를 compatibility exception으로 숨기기
```

Boundary 3 PASS + checkpoint 전 Boundary 4 시작 금지.

---

## 5. AXIS 1 신규 DSL 기능 개발

Migration parity 뒤 다음 순서로 진행한다.

```text
5-1 tuple / multi-output + destructuring
5-2 generic projection
5-3 capability metadata
5-4 user-defined functions
5-5 bounded loops
5-6 on_tick / on_fill rollback/commit
5-7 partial fills / partial exits
5-8 pyramiding / multi-position
5-9 full reference differential fixtures
5-10 full-engine batch/streaming parity
```

---

## 6. AXIS 1 기계판독 capability / diagnostic registry

DSL 문법·함수·입출력형·지원상태·진단코드를 machine SSOT로 만든다.

---

## 7. Bridge common + AXIS 1 실행계약

표준 Request/Response와 AXIS 1 실행 입출력을 versioned contract로 고정한다.

---

## 8. AXIS 2 사전계산 snapshot 계약

시장레짐, 고베타, 섹터강도, 종목별 normalized Histogram 등 exact-as-of snapshot 계약을 만든다.

---

## 9. AXIS 2 종목선별 엔진 / 핵심 feature

```text
universe -> filter -> rank -> top-N -> evidence -> Candidate Set
```

---

## 10. AXIS 3 Condition / Strategy CRUD

Feature Catalog와 분리된 Condition/Strategy 저장·버전·lineage·오케스트레이션을 구현한다.

---

## 11. 3축 E2E Bridge

```text
AXIS 2 Candidate Set -> AXIS 3 Strategy -> AXIS 1 execution -> AXIS 3 validation
```

---

## 12. 외부 LLM 자연어 작성 workflow

Prompt Builder, 구조화 반환 검증, DSL 검증, Correction Prompt, human-mediated 반복 workflow를 구현한다.

---

## 13. 지속개선 분석도구

LLM 반환/검증 오류를 누적해 Prompt/Skill/DSL/Data contract 개선 후보를 증거 기반으로 분석한다.

---

## 14. 최종 자연어 E2E 검증

자연어 요청부터 종목선별→전략→실행→차트/백테스트까지 검증한다.

---

## 15. Legacy 문서 정리 + repo-wide compliance audit

새 구조 안정화 후 문서를 정리하고 전체 경계검사를 수행한다. frozen core source는 계속 보존한다.

---

## PARKING LOT / 예외

현재 번호와 무관한 아이디어는 기록만 한다. 긴급한 신뢰경계 훼손 문제만 현재 작업을 중단할 수 있다.

중요 방침/로직/순서 변경은 그 턴에서 관련 authority + 이 문서(순서 영향 시) + `SESSION_HANDOFF.md`에 반영한다.
