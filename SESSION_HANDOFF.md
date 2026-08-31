# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / ACTIVE / STRICT-SEQUENTIAL-EXECUTION / CURRENT STEP 4 BOUNDARY 7 / 2026-08-31 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + exact user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 중요한 방침/로직 변경은 그 턴에서 문서에 반영한다. 구현은 `DSL_NEXT_WORK_ORDER.md`의 번호와 현재 boundary를 건너뛰지 않는다.

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다. 기계용 상세정보는 내부에서 관리하고 콘솔도 디버깅에 필요한 최소 정보만 출력한다.

---

## 현재 작업

```text
CURRENT_STEP = 4
CURRENT_BOUNDARY = 7 DSL Runtime
BOUNDARY_STATUS = REMOTE_UNVALIDATED
```

완료:

```text
Step 1 기존 DSL 남은 기능 점검 = COMPLETE
Step 2 AXIS 1 migration 설계/순서 = COMPLETE
Step 3 Frozen Core 보호 gate = COMPLETE / USER-LOCAL PASS
Boundary 1 Parser / AST = COMPLETE / USER-LOCAL PASS
Boundary 2 Function Registry = COMPLETE / USER-LOCAL PASS
Boundary 3 Assignment Flow + Semantic = COMPLETE / USER-LOCAL PASS
Boundary 4 Indicator Kernel = COMPLETE / USER-LOCAL PASS
Boundary 5 State + Bar Runtime = COMPLETE / USER-LOCAL PASS
Boundary 6 MTF + Read-Only Context Binding = COMPLETE / USER-LOCAL PASS
```

Boundary 6 user-local evidence:

```text
MTF/context parity = OK
frozen core guard = OK
```

Checkpoint:

```text
STEP4_BOUNDARY6_MTF_CONTEXT_PARITY_CHECKPOINT_2026-08-31.md
```

---

## 현재 Boundary 7

이식 대상:

```text
legacy:
  core/dsl_runtime.py

axis1:
  axes/axis1_dsl/runtime/dsl_runtime.py
```

현재 remote 상태:

```text
DSL 실행기 본체 이식 완료
내부 의존성은 새 AXIS 1 Parser/Semantic/Indicator/State/MTF/Context만 사용
focused parity test 추가:
  tests/test_axis1_dsl_runtime_parity.py
```

검증 대상:

```text
전략 이름/timeframe
assignment/indicator/session/MTF/state 계산값
이벤트 조건/주문 인자
prepared exact-time context compile
runtime fail-closed 오류
new runtime의 frozen-core production import 부재
```

Boundary 7은 user-local PASS 전 TRUSTED로 부르지 않는다. PASS 전 Boundary 8 Broker 시작 금지.

---

## Frozen legacy Core — 절대 보존

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

금지:

```text
core/ 수정 / 이동 / 삭제 / 신규 파일 추가
새 기능 역이식
새 AXIS production code가 frozen core 내부 구현에 영구 의존
expected frozen hash 변경으로 위반 수용
```

---

## Step 4 남은 순서

```text
7 DSL Runtime                          CURRENT
8 Broker
9 Backtest + Projection Output
```

각 boundary는 반드시:

```text
이식 -> focused parity -> frozen guard -> user-local PASS -> checkpoint -> 다음 boundary
```

---

## 이후 작업순서

```text
5. AXIS 1 신규 DSL 기능 개발
   tuple/multi-output가 첫 우선순위
6. machine-readable capability/diagnostic registry
7. Bridge common + AXIS 1 실행계약
8. AXIS 2 exact-as-of snapshot 계약
9. AXIS 2 종목선별 엔진/feature
10. AXIS 3 Condition/Strategy CRUD
11. 3축 E2E Bridge
12. 외부 LLM 자연어 작성 workflow
13. 지속개선 분석도구
14. 최종 자연어 E2E 검증
15. legacy 문서 정리 + repo-wide compliance audit
```

새 아이디어는 PARKING LOT에 기록만 하고 현재 순서를 계속한다.

---

## 3축 책임

```text
AXIS 1 = 단일종목 deterministic DSL 실행
AXIS 2 = 사전계산 exact-as-of 종목선별
AXIS 3 = Condition/Strategy CRUD + lineage/오케스트레이션
Chart = 계산 없이 projection/evidence 표시
```

시장레짐/고베타/섹터/종목간 Histogram rank는 AXIS 1에서 계산하지 않는다.

---

## External LLM / 지속개선

외부 LLM은 proposal only다. 구조화 반환은 local deterministic validation을 통과해야 한다. 반복 오류는 구조화 로그로 누적해 Prompt/Skill/Validator/DSL/Data contract 개선 근거로 사용하되 자동 self-modification이나 검증완화는 금지한다.

---

## 사용자 커뮤니케이션 / 콘솔

```text
사용자 화면 = 한 일 / 할 일
성공 콘솔 = 가능하면 [PASS] 한 줄
실패 콘솔 = 디버깅에 필요한 최소 원인/위치
상세 hash/schema/error code/event = 내부 관리
```

---

## 다음 exact action

사용자 local에서 최신 branch pull 후:

```text
python -m unittest discover -s tests -p "test_axis1_dsl_runtime_parity.py" -v
python -m unittest discover -s tests -p "test_frozen_legacy_core_guard.py" -v
```

둘 다 PASS하면 Boundary 7 checkpoint 후 Boundary 8 Broker로 이동한다.

실패 시 test defect / migration defect / authority drift / environment issue / unknown 순으로 원인분류하고 assertion이나 원칙을 약화하지 않는다.
