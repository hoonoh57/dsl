# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재부터는 새 제품 검증 tranche인 UI 일관성 검증을 수행한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 migrated DSL feature-by-feature UI consistency verification
SUBSTEP_STATUS = READY / USER-DRIVEN UI TESTING
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
```

## 완료된 기반

```text
Steps 1~15 = COMPLETE / USER-LOCAL PASS
Final checkpoint = STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md
```

이 완료 상태는 UI 검증 중 임의로 되돌리거나 검증을 약화하지 않는다.

## UIA-1 실행 순서

각 UI 기능을 하나씩 다음 순서로 검증한다.

```text
1. UI에서 기능 선택/작성
2. 실행
3. 화면 결과와 deterministic engine 결과 확인
4. 실패 시 원인 계층 분류
5. 해당 계층에서만 최소 수정
6. focused regression
7. 관련 cross-layer regression
8. frozen core guard
9. 같은 UI 동작 재확인
```

한 기능이 안정적으로 PASS되기 전 다음 기능으로 넘어가지 않는 것을 기본으로 한다.

## 수정 분리 원칙

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

절대 규칙:

```text
repository-root core/ 수정 금지
UI를 맞추기 위해 engine 결과 덮어쓰기 금지
Bridge/Runtime에서 지표/전략/선별 재계산 금지
Add-on 문제를 Core 특례로 흡수 금지
JSON persistence에서 계산/보정 금지
Axis 1/2/3 책임 혼합 금지
검증완화/skip/compatibility exception 금지
```

`Core` 수정이 실제로 필요한 경우에도 신규 변경 위치는 `axes/axis1_dsl/`이며, 특정 UI/전략 특례가 아니라 모든 전략에 적용되는 generic capability여야 한다.

## 실패 분류

수정 전에 반드시 다음 중 하나로 분류한다.

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

분류가 불명확하면 먼저 재현과 evidence를 확보한다.

## PASS 정의

기능별 PASS:

```text
UI 입력 의미 == contract 입력 의미
engine 결과 == UI 실행 결과
화면 표시 == supplied result/projection
저장/복원 == 동일 선언/버전/해시 의미
다른 계층으로 제품 특례 누수 없음
관련 regression PASS
frozen legacy core guard PASS
```

## 기존 최종 제품 권한

```text
AXIS 1 = deterministic single-instrument DSL/runtime/execution
AXIS 2 = immutable exact-PIT selection semantics + evidence
AXIS 3 = versioned Condition/Strategy lifecycle + orchestration
Bridge = versioned Request -> Response composition
Chart/UI = 입력/관찰 surface, 계산 authority 아님
```

UI acceptance는 이 경계를 우회하는 별도 계산경로를 만들지 않는다.
