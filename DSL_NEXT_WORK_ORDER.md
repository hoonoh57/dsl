# DSL Strict Sequential Next-Work Order

Status: **ACTIVE EXECUTION-ORDER AUTHORITY / DO-NOT-SKIP / 2026-08-31 KST**

이 문서는 현재 프로젝트의 **작업 순서 SSOT**다.

핵심:

> **방침은 즉시 기록하되, 구현은 현재 번호가 끝나기 전 다음 번호로 넘어가지 않는다.**

새 아이디어는 PARKING LOT에 기록하고 현재 작업을 계속한다. 순서를 바꾸려면 사용자 명시 결정 후 이 문서를 먼저 수정한다.

---

## 현재 포인터

```text
CURRENT_STEP = 3
CURRENT_STEP_NAME = Frozen Core 보호 gate 검증
```

완료:

```text
STEP 1 COMPLETE = 기존 DSL 남은 기능 exact audit
  -> DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
  -> STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md

STEP 2 COMPLETE = 새 AXIS 1 이식 설계도 + 경계 순서
  -> DSL_AXIS1_MIGRATION_MANIFEST.md
  -> STEP2_AXIS1_MIGRATION_PLAN_CHECKPOINT_2026-08-31.md
```

현재 Step을 완료할 때마다:

```text
결과 기록 -> PASS/FAIL 원인분류 -> authority/handoff/checkpoint 갱신 -> 다음 번호
```

---

## 1. 기존 DSL 남은 기능 점검 — COMPLETE

JMA 접근, projection, Strategy CRUD 경계를 실제 코드/테스트로 확인했다. 상세 결과는 Step 1 문서가 권한이다.

---

## 2. 새 DSL 이식 설계도 + 경계 순서 — COMPLETE

9개 boundary를 확정했다.

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

첫 실제 이식은 Parser/AST다. 상세 mapping/exclusion/parity는 `DSL_AXIS1_MIGRATION_MANIFEST.md`가 권한이다.

---

## 3. Frozen Core 보호 gate 검증 — CURRENT

첫 migration write 전에 기존 `core/`가 동결 기준과 동일한지 확인한다.

기준:

```text
frozen tree = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

검증:

```text
tests/test_frozen_legacy_core_guard.py
```

완료 조건:

```text
frozen core unchanged
user-local guard PASS evidence
```

PASS 전 Step 4 시작 금지.

---

## 4. AXIS 1 경계별 이식 + parity

Step 2에서 확정한 9개 boundary를 **한 번에 하나씩** 이식한다.

각 boundary:

```text
이식 -> focused parity -> frozen comparison -> regression -> checkpoint
```

전체 `core/` 일괄복사, migration 중 신규기능 추가, legacy core 수정 금지.

---

## 5. AXIS 1 신규 DSL 기능 개발

Migration parity 뒤 DSL 고유 기능 개발을 즉시 재개한다.

고정 순서:

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

DSL 문법·함수·입출력형·지원상태·진단코드를 machine SSOT로 만든다. 이후 외부 LLM Skill/Prompt도 이 등록정보에서 생성할 수 있어야 한다.

---

## 7. Bridge common + AXIS 1 실행계약

표준 Request/Response와 AXIS 1 실행 입출력을 versioned contract로 고정한다. Bridge는 계산하지 않는다.

---

## 8. AXIS 2 사전계산 snapshot 계약

시장레짐, 고베타, 섹터강도, 종목별 normalized Histogram 등 point-in-time feature snapshot의 exact as-of 계약을 만든다.

---

## 9. AXIS 2 종목선별 엔진 / 핵심 feature

```text
universe -> filter -> rank -> top-N -> evidence -> Candidate Set
```

시장레짐/고베타/주도섹터/Histogram 순위/상대강도 등을 사전계산 결과로 조합한다.

---

## 10. AXIS 3 Condition / Strategy CRUD

Feature Catalog와 분리된 Condition CRUD, Strategy CRUD, baseline/version/lineage, Candidate Set→Strategy 오케스트레이션을 구현한다.

---

## 11. 3축 E2E Bridge

```text
AXIS 2 Candidate Set -> AXIS 3 Strategy -> AXIS 1 execution -> AXIS 3 validation
```

축 간 내부 import 없이 versioned Request/Response만 사용한다.

---

## 12. 외부 LLM 자연어 작성 workflow

Prompt Builder, 구조화 반환 검증, capability/data-source 검증, DSL 검증, Correction Prompt, 사람이 매개하는 반복 workflow를 구현한다.

---

## 13. 지속개선 분석도구

LLM 반환/검증 오류를 누적해 Prompt/Skill/DSL/Data contract 개선 후보를 증거 기반으로 분석한다. 자동 self-modification은 금지한다.

---

## 14. 최종 자연어 E2E 검증

자연어 한 문장으로 종목선별→전략→실행→차트/백테스트까지 전체 흐름을 검증한다. 여러 종목/기간/timeframe에서 재현성을 확인한다.

---

## 15. Legacy 문서 정리 + repo-wide compliance audit

새 구조 안정화 후 KEEP/ARCHIVE/RETIRE를 결정하고 전체 경계검사를 수행한다. frozen core source는 계속 보존한다.

---

## PARKING LOT / 예외

현재 번호와 무관한 아이디어는 기록만 한다. 긴급한 신뢰경계 훼손 문제만 현재 Step을 중단할 수 있으며, 이 경우에도 먼저 문서에 원인과 중단상태를 남긴다.

중요 방침/로직/순서가 바뀌면 그 턴에서 관련 authority + 이 문서(순서 영향 시) + `SESSION_HANDOFF.md`를 함께 갱신한다.
