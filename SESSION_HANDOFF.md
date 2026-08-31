# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 2 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

가장 중요한 운영 원칙:

> **중요 방침/로직 변경은 그 턴에서 문서에 반영한다. 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호를 절대로 건너뛰지 않는다.**

> **사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다. 기계용 상세정보는 내부에서 관리한다. 콘솔도 디버깅에 필요한 최소 정보만 출력한다.**

---

## 1. 복구 순서

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md
4. DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
5. DSL_FROZEN_CORE_MIGRATION_POLICY.md
6. DSL_AXIS2_PRECOMPUTED_SELECTION_POLICY.md
7. DSL_EXTERNAL_LLM_STRATEGY_AUTHORING_POLICY.md
8. DSL_AUTHORING_CONTINUOUS_IMPROVEMENT_POLICY.md
9. DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
10. DSL_THREE_AXIS_FINAL_TARGET.md
11. DSL_THREE_AXIS_MODULE_BOUNDARY.md
12. PARENT_CONTEXT_FEATURE_PROVIDER_POLICY.md
13. CURRENT_STATE.md
14. current `dsl-live-studio` HEAD
```

새 세션에서는 이미 확정된 사항을 사용자에게 다시 묻지 않는다.

---

## 2. 현재 작업 포인터

```text
CURRENT_STEP = 2
CURRENT_STEP_NAME = AXIS 1 migration manifest 및 이식 경계 순서 확정
```

Step 1은 완료됐다.

```text
상세 결과: DSL_AXIS1_PRE_MIGRATION_CAPABILITY_AUDIT.md
checkpoint: STEP1_AXIS1_CAPABILITY_AUDIT_CHECKPOINT_2026-08-31.md
```

Step 1 핵심 결론:

```text
JMA 기본 값은 전략에서 사용 가능
JMA 상승/하락의 정식 DSL 출력은 부분구현
JMA 정규화 기울기 강도는 공식 측정값으로 미구현
숫자 중간값 차트 반환은 가능
threshold/permission 일반 projection은 부분구현
Feature Catalog와 mutable persistence는 분리됨
최종 AXIS 3 Condition/Strategy CRUD 물리분리는 미완성
```

Step 2가 끝나기 전 Step 3 보호 gate나 Step 4 실제 이식을 시작하지 않는다.

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

보호 테스트는 추가됐지만 user-local PASS는 아직 보고되지 않았다. 이 검증은 작업순서 Step 3에서 수행한다.

---

## 4. 새 3축 구조

```text
axes/axis1_dsl/        = DSL Capability Engine
axes/axis2_selection/  = 사전계산 point-in-time 종목선별
axes/axis3_monetization/ = Condition/Strategy CRUD + 수익화/오케스트레이션
bridges/contracts/     = versioned Request -> Response 경계
```

축 간 직접 내부 import/DB/state 접근은 금지한다. Chart는 계산하지 않고 projection/evidence만 표시한다.

AXIS 2의 시장레짐, 고베타, 섹터강도, 종목간 normalized Histogram 순위 등은 Instrument DSL 안에서 계산하지 않는다.

```text
사전계산 -> exact as_of snapshot -> AXIS 2 filter/rank/top-N -> Candidate Set
```

---

## 5. AXIS 1 이식 후 우선 개발 기능

3축 전환 때문에 DSL 고유 기능 개발을 장기 보류하지 않는다. migration parity 이후 다음 순서를 우선한다.

```text
1. tuple / multi-output + destructuring
2. generic projection
3. capability metadata 보강
4. user-defined functions
5. bounded loops
6. on_tick / on_fill rollback/commit
7. partial fills / partial exits
8. pyramiding / multi-position
9. full reference differential fixtures
10. full-engine batch/streaming parity
```

특정 전략을 위해 Core 문법을 하드코딩하지 않는다.

---

## 6. 최종 자연어 목표

궁극적으로 사용자가 자연어 한 문장으로 종목선별부터 매매/리스크까지 요청할 수 있어야 한다.

대표 형태:

```text
최근 EMA120 돌파와 Histogram 기준강도로 후보 선별
 -> 현재 동일/이상 강도로 재돌파 후보 선택
 -> 15분봉에서 EMA120/Histogram/MACD/JMA 조건으로 매수
 -> 수익상태와 EMA120 유지 여부를 고려해 JMA 하락전환 청산
```

책임:

```text
AXIS 2 = 종목선별
AXIS 3 = 전략버전/참조값 오케스트레이션
AXIS 1 = 단일종목 deterministic 실행
```

---

## 7. External LLM Authoring Lane

자연어를 로컬 범용 NLP로 완전히 이해하려 하지 않는다.

```text
사용자 자연어
 -> Local Prompt Builder
 -> 사람 -> 외부 LLM
 -> 구조화된 전략 초안
 -> Local deterministic validation
 -> PASS 또는 교정 Prompt
 -> 사람 -> 외부 LLM 재교정
```

외부 LLM은 proposal only다. 지원하지 않는 기능이 필요하면 임의 문법을 만들지 않고 capability 부족으로 반환한다.

기존 준비물:

```text
skills/external_llm_strategy_authoring/SKILL.md
authoring/contracts/external_strategy_draft.v1.schema.json
authoring/contracts/authoring_validation_event.v1.schema.json
```

이 workflow 구현은 작업순서 Step 12에서 한다.

---

## 8. Continuous Improvement

LLM 반환 오류를 버리지 않고 구조화해 누적한다.

```text
오류 누적
 -> 주기적 종합검토
 -> Prompt / Skill / Validator / DSL / Data contract 중 실제 원인 판별
 -> 가장 좁은 부분만 개선
 -> focused test + regression
 -> 개선 전후 비교
```

Parser/Prompt/Skill/Core 자동 self-modification이나 검증 완화는 금지한다.

---

## 9. 사용자 커뮤니케이션 / 콘솔

사용자 진행보고 기본 형식:

```text
한 일
할 일
```

사람이 이해하는 용어를 쓰고 내부 hash/schema/error code/class 이름은 기본적으로 생략한다.

콘솔:

```text
정상 = 가능하면 [PASS] 한 줄
오류 = 디버깅에 필요한 최소 원인/위치만
상세 trace/structured event = 내부 로그
```

---

## 10. 엄격한 작업 순서

상세 완료조건은 `DSL_NEXT_WORK_ORDER.md`가 SSOT다.

```text
1. 기존 DSL 남은 기능 점검 [COMPLETE]
2. 새 DSL 이식 설계도 + 경계 순서 [CURRENT]
3. Frozen Core 보호 gate PASS
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

새 아이디어는 PARKING LOT에 기록만 하고 현재 번호를 계속한다. 순서를 바꾸려면 사용자 명시 결정 후 `DSL_NEXT_WORK_ORDER.md`를 먼저 수정한다.

---

## 11. 현재 검증 상태

```text
frozen legacy core: immutable policy established
Step 1 capability audit: COMPLETE
Step 2 migration planning: IN PROGRESS
AXIS 1 migration: NOT STARTED
AXIS 2 implementation: NOT STARTED
AXIS 3 implementation: scaffold only
external LLM workflow implementation: NOT STARTED
repository-wide compliance: REMEDIATION_REQUIRED
```

부분 결과를 전체 완료나 실전 수익성/live readiness/repository-wide PASS로 과장하지 않는다.

---

## 12. 중요 방침 변경 문서화

다음이 바뀌면 그 턴에서 즉시 관련 authority와 `SESSION_HANDOFF.md`를 갱신한다. 작업순서에 영향이 있으면 `DSL_NEXT_WORK_ORDER.md`도 먼저 갱신한다.

```text
architecture / AXIS 책임
DSL 문법/실행 의미
데이터/causality
Bridge contract
검증 기준
외부 LLM protocol
지속개선 정책
사용자 커뮤니케이션/콘솔 정책
작업순서/중요 backlog
```

---

## 13. 금지사항

```text
frozen core 수정
현재 Step 건너뛰기
여러 미래 Step 동시 구현
특정 종목/venue/timeframe/전략 예외를 Core에 추가
Feature Catalog baseline 수정
Chart 계산 재구현
AXIS 간 내부 구현 직접 참조
LLM output validation 없이 실행
LLM 발명 capability/data source 자동 등록
실패 assertion 완화
근거 없는 Parser 완화
Prompt/Skill/Core 자동 self-modification
사용자에게 불필요한 기계정보 나열
정상 콘솔에 상세 trace/JSON dump 출력
```

---

## 14. 세션 복구 행동

새 세션에서 `세션이어가!`, `세션복구`, `계속` 요청 시:

```text
1. 복구 문서를 순서대로 읽는다.
2. current HEAD와 CURRENT_STEP을 확인한다.
3. frozen Core 무변경을 전제로 한다.
4. 기존 결정을 다시 묻지 않는다.
5. 사용자에게 `한 일 / 할 일`만 짧게 제시한다.
6. CURRENT_STEP 외 구현을 시작하지 않는다.
7. 현재 Step의 실제 코드/테스트를 먼저 확인한다.
8. 실패는 원인분류 후 수정하며 원칙/assertion을 약화하지 않는다.
9. Step 완료 시 authority/session/checkpoint/current pointer를 함께 갱신한다.
```

이 문서와 `DSL_NEXT_WORK_ORDER.md`가 다음 세션의 첫 실행 authority다.
