# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 현재 단계는 지금까지 이식한 DSL 기능을 실제 UI 경로에서 하나씩 일관성 검증하는 단계다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 migrated DSL feature-by-feature UI consistency verification
STATUS = ACTIVE / USER-DRIVEN UI TESTING
```

현재 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

최종 이전 checkpoint:

```text
STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

## UI 검증 수정 원칙

사용자가 명시한 계층 분리:

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

수정 사유가 생기면 먼저 어느 계층의 결함인지 분류하고 **그 계층에서만 최소 수정**한다.

### Core

현재 제품의 deterministic DSL 의미/계산 계층이다. 신규 수정 위치는 `axes/axis1_dsl/`이며 repository-root `core/`는 frozen reference로 계속 불변이다.

```text
소유: parser / semantic / indicator / state / execution / backtest meaning
금지: UI 특례 / JSON 특례 / 특정 전략 shortcut / Axis2·3 제품정책
```

### Bridge / Runtime

```text
소유: request/response validation, UI-to-contract adaptation, lifecycle/routing, context binding
금지: 지표/전략/선별 재계산, 결과 보정, 누락값 임의 fill/default
```

### Add-ons

```text
소유: generic Core 위의 기능별 조합/확장, selector/strategy/chart projection 등
원칙: Add-on 요구를 Core나 Bridge의 제품특례로 숨기지 않음
```

### JSON persistence

```text
소유: schema/version/hash 저장·복원
금지: 계산/조건판정/지표생성/주문의미/실행값 보정
```

## UI 기능별 검증 루프

```text
UI에서 실행
 -> 결과 확인
 -> 실패 시 원인 계층 분류
 -> 해당 계층 최소 수정
 -> focused test
 -> 관련 regression
 -> frozen-core guard
 -> 동일 UI 동작 재확인
```

기본적으로 한 기능 PASS 후 다음 기능으로 넘어간다.

## 실패 분류

```text
UI defect
Bridge / Runtime defect
Core semantic defect
Add-on defect
Persistence/schema defect
Test defect
Environment issue
Authority drift
Unknown
```

분류 전 수정하지 않는다.

## 영구 경계

```text
AXIS 1 = deterministic single-instrument DSL/runtime/execution
AXIS 2 = immutable exact-PIT selection semantics/evidence
AXIS 3 = Condition/Strategy immutable version lifecycle/orchestration
Bridge = versioned Request -> Response composition
Chart/UI = 입력/관찰 surface, 계산 authority 없음
```

UI 테스트를 이유로 별도 계산 shortcut이나 cross-axis 직접 의존을 만들지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.

## 다음 action

사용자가 UI에서 첫 DSL 기능을 실행하고 결과를 공유하면 그 기능부터 일관성 검증을 시작한다.

오류가 있으면 console/화면 evidence를 기준으로 먼저 계층을 분류하고 assertion/contract를 약화하지 않는다.
