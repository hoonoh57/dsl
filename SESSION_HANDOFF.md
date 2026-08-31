# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 3 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

가장 중요한 운영 원칙:

> **중요 방침/로직 변경은 그 턴에서 문서에 반영한다. 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호를 절대로 건너뛰지 않는다.**

> **사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다. 기계용 상세정보는 내부에서 관리하고 콘솔도 디버깅에 필요한 최소 정보만 출력한다.**

---

## 1. 복구 순서

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. STEP2_AXIS1_MIGRATION_PLAN_CHECKPOINT_2026-08-31.md
4. DSL_AXIS1_MIGRATION_MANIFEST.md
5. STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md
6. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
7. DSL_FROZEN_CORE_MIGRATION_POLICY.md
8. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
9. DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
10. DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
11. DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
12. DSL_THREE_AXIS_FINAL_TARGET.md
13. DSL_THREE_AXIS_MODULE_BOUNDARY.md
14. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
15. CURRENT_STATE.md
16. current `dsl-live-studio` HEAD
```

새 세션에서는 이미 확정된 사항을 사용자에게 다시 묻지 않는다.

---

## 2. 현재 작업 포인터

```text
CURRENT_STEP = 3
CURRENT_STEP_NAME = Frozen Core 보호 gate 검증
```

완료:

```text
Step 1 = 기존 DSL 남은 기능 점검 완료
Step 2 = 새 AXIS 1 이식 설계도와 9개 경계 순서 확정
```

Step 2 이식 순서:

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

첫 실제 이식 대상은 Parser/AST로 확정했다. Step 3 보호검사 PASS 전에는 실제 이식을 시작하지 않는다.

---

## 3. Frozen legacy Core

기존 검증 Core는 영구 read-only golden reference다.

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정 / 이동 / 삭제 / 신규 파일 추가
새 기능 역이식
새 AXIS가 legacy core 내부 구현에 영구 의존
```

허용:

```text
읽기 / regression / golden parity / migration source reference
```

현재 Step 3 검증:

```text
tests/test_frozen_legacy_core_guard.py
```

user-local PASS가 아직 필요하다.

---

## 4. 새 3축 구조

```text
axes/axis1_dsl/          = DSL Capability Engine
axes/axis2_selection/    = 사전계산 point-in-time 종목선별
axes/axis3_monetization/ = Condition/Strategy CRUD + 수익화/오케스트레이션
bridges/contracts/       = versioned Request -> Response 경계
```

축 간 직접 내부 import/DB/state 접근 금지. Chart는 계산하지 않고 projection/evidence만 표시한다.

시장레짐, 고베타, 섹터강도, 종목간 normalized Histogram 순위 등은 Instrument DSL 안에서 계산하지 않고 사전계산 exact as-of snapshot으로 AXIS 2가 사용한다.

---

## 5. Step 1에서 확정된 DSL gap

```text
JMA 기본 값은 전략에서 사용 가능
JMA 상승/하락 정식 DSL 출력은 부분구현
JMA normalized slope strength는 공식 측정값으로 미구현
숫자 중간값 차트 반환 가능
threshold/permission 일반 projection은 부분구현
Feature Catalog와 mutable persistence는 분리됨
최종 AXIS 3 Condition/Strategy CRUD 물리분리는 미완성
```

Migration parity 뒤 AXIS 1 신규 기능 우선순위:

```text
tuple/multi-output -> generic projection -> metadata -> user functions -> loops
-> tick/fill rollback -> partial fill -> pyramiding -> differential fixtures -> full parity
```

3축 전환 때문에 DSL 고유 기능 개발을 장기 보류하지 않는다.

---

## 6. AXIS 1 migration 경계 원칙

상세 authority: `DSL_AXIS1_MIGRATION_MANIFEST.md`

순수 DSL 실행엔진만 새 AXIS 1에 이식한다.

AXIS 1에 가져오지 않는 대표 legacy 책임:

```text
전략/artifact DB -> AXIS 3
multi-symbol / leader-follower / market-sector provider -> AXIS 2/외부 provider
prompt/transpiler -> Authoring/adapter
Kiwoom data adapter -> 외부 adapter
stage1/tactical/adaptive research -> Core에 재유입 금지
Feature Catalog/invariants -> frozen verification evidence
```

새 AXIS 1 production code는 완료 시 frozen `core/`를 import하지 않는다. parity test만 legacy/new를 동시에 불러 비교할 수 있다.

---

## 7. 최종 자연어 목표

자연어 한 문장으로 종목선별부터 매매/리스크까지 요청할 수 있어야 한다.

```text
AXIS 2 = 후보선별
AXIS 3 = 전략버전/참조값 오케스트레이션
AXIS 1 = 단일종목 deterministic 실행
```

외부 LLM은 proposal only이며 Local deterministic validation을 통과한 구조만 사용한다.

---

## 8. External LLM + 지속개선

```text
사용자 자연어 -> Prompt Builder -> 사람 -> 외부 LLM -> 구조화 초안
-> Local validation -> PASS 또는 Correction Prompt -> 반복
```

기존 준비물:

```text
skills/external_llm_strategy_authoring/SKILL.md
authoring/contracts/external_strategy_draft.v1.schema.json
authoring/contracts/authoring_validation_event.v1.schema.json
```

LLM 오류는 누적해 주기적으로 Prompt/Skill/Validator/DSL/Data contract 개선 근거로 사용한다. Parser/Prompt/Skill/Core 자동 self-modification이나 검증완화는 금지한다.

---

## 9. 사용자 커뮤니케이션 / 콘솔

사용자 진행보고 기본 형식:

```text
한 일
할 일
```

내부 hash/schema/error code/class 이름은 기본적으로 생략한다.

콘솔:

```text
정상 = 가능하면 [PASS] 한 줄
오류 = 디버깅에 필요한 최소 원인/위치만
상세 trace/structured event = 내부 로그
```

---

## 10. 엄격한 작업 순서

```text
1. 기존 DSL 남은 기능 점검 [COMPLETE]
2. 새 DSL 이식 설계도 + 경계 순서 [COMPLETE]
3. Frozen Core 보호 gate PASS [CURRENT]
4. AXIS 1 경계별 이식 + parity
5. AXIS 1 신규 DSL 기능 개발
6. AXIS 1 기계판독 capability/diagnostic registry
7. Bridge common + AXIS 1 실행계약
8. AXIS 2 사전계산 snapshot 계약
9. AXIS 2 종목선별 엔진/핵심 feature
10. AXIS 3 Condition/Strategy CRUD
11. 3축 E2E Bridge
12. 외부 LLM 자연어 작성 workflow
13. 지속개선 분석도구
14. 최종 자연어 E2E 검증
15. legacy 문서 정리 + repo-wide compliance audit
```

새 아이디어는 PARKING LOT에 기록만 하고 현재 번호를 계속한다.

---

## 11. 현재 상태

```text
Step 1: COMPLETE
Step 2: COMPLETE
Step 3 frozen guard: WAITING USER-LOCAL PASS
AXIS 1 source migration: NOT STARTED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
external LLM workflow implementation: NOT STARTED
repository-wide compliance: REMEDIATION_REQUIRED
```

부분 결과를 전체 완료나 실전 수익성/live readiness/repository-wide PASS로 과장하지 않는다.

---

## 12. 중요 방침 변경 문서화

architecture/AXIS 책임/DSL 의미/data causality/Bridge/검증/LLM protocol/지속개선/사용자 출력/작업순서가 바뀌면 그 턴에서 관련 authority와 `SESSION_HANDOFF.md`를 갱신한다. 작업순서 영향 시 `DSL_NEXT_WORK_ORDER.md`를 먼저 갱신한다.

---

## 13. 세션 복구 행동

```text
1. 복구 문서를 순서대로 읽는다.
2. current HEAD와 CURRENT_STEP을 확인한다.
3. frozen Core 무변경을 전제로 한다.
4. 기존 결정을 다시 묻지 않는다.
5. 사용자에게 `한 일 / 할 일`만 짧게 제시한다.
6. CURRENT_STEP 외 구현을 시작하지 않는다.
7. 실패는 원인분류 후 수정하며 원칙/assertion을 약화하지 않는다.
8. Step 완료 시 authority/session/checkpoint/current pointer를 함께 갱신한다.
```

이 문서와 `DSL_NEXT_WORK_ORDER.md`가 다음 세션의 첫 실행 authority다.
