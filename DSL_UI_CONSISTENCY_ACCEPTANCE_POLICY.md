# DSL UI Consistency Acceptance Policy

Status: **ACTIVE UI ACCEPTANCE AUTHORITY / 2026-09-01 KST**

이 단계의 목적은 지금까지 이식·구현한 DSL 기능을 실제 UI 경로에서 하나씩 실행해 **UI -> Bridge/Runtime -> 각 기능 계층 -> 결과 표시/영속성**이 동일 의미를 유지하는지 확인하는 것이다.

## 1. 최우선 분리 원칙

수정 사유가 발생해도 다음 책임을 섞지 않는다.

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

여기서 `Core`는 현재 제품의 결정론적 DSL 계산/의미 계층을 뜻하며 신규 수정 위치는 `axes/axis1_dsl/`이다. repository-root `core/`는 frozen legacy reference이므로 수정하지 않는다.

### Core

소유:

```text
DSL 문법/타입/의미
지표 계산식
상태 전이
주문/체결의 결정론적 의미
백테스트 계산 의미
```

금지:

```text
UI 표시 특례
특정 화면/버튼 조건
JSON 저장형식 특례
Axis2/Axis3 제품정책 하드코딩
특정 전략만 위한 shortcut
```

### Bridge / Runtime

소유:

```text
입출력 계약 검증
UI 요청을 제품 계약으로 변환
실행 lifecycle/routing
context binding
오류 전달/진단 연결
```

금지:

```text
지표 재계산
선별/전략 의미 재구현
UI 결과를 맞추기 위한 계산값 보정
누락값 임의 default/fill
```

### Add-ons

소유:

```text
범용 Core 위의 기능별 의미
선별 기능
전략/Condition 제품 기능
차트 projection/관찰 기능
추가 사용자 지표 등 additive extension
```

원칙:

```text
일반 Core 능력이 이미 있으면 Add-on이 조합해서 사용
새 일반 능력이 실제로 부족할 때만 별도 generic tranche로 Core 확장
Add-on 요구를 이유로 Bridge나 Core에 해당 기능의 제품정책을 숨기지 않음
```

### JSON persistence

소유:

```text
versioned schema
저장/복원
artifact identity/version/hash
사용자 설정과 선언적 상태
```

금지:

```text
계산
조건 판정
지표 생성
주문 의미
실행시점 보정
```

JSON은 계산결과의 원인이 아니라 **이미 결정된 상태/계약을 보존하는 수단**이다.

## 2. UI 일관성 테스트 순서

각 기능은 다음 순서로 검증한다.

```text
1. UI에서 기능 선택/작성
2. 실제 실행
3. 화면 출력과 내부 deterministic 결과 비교
4. 오류 발생 시 먼저 원인 계층 분류
5. 해당 계층에서만 최소 수정
6. focused test
7. 관련 regression
8. frozen legacy core guard
9. 같은 UI 동작 재검증
```

한 기능이 PASS되기 전 다음 기능으로 넘어가지 않는 것을 기본으로 한다.

## 3. 실패 분류

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

분류 전에 수정하지 않는다.

## 4. 수정 금지 패턴

```text
UI를 통과시키기 위해 Core 결과를 덮어쓰기
Bridge가 지표/전략/선별을 재계산
Add-on 문제를 Core 특례로 흡수
JSON 로드 시 잘못된 값을 자동 보정
실패 assertion 약화
compatibility exception 추가로 경계 위반 숨기기
repository-root frozen core 수정
```

## 5. Axis 경계도 계속 유지

```text
AXIS 1 = single-instrument deterministic DSL/runtime/execution
AXIS 2 = exact-PIT selection semantics/evidence
AXIS 3 = Condition/Strategy version lifecycle/orchestration
Bridge = versioned Request -> Response composition
Chart/UI = 계산 authority가 아니라 입력/관찰 surface
```

UI 테스트는 이 경계를 우회하는 별도 실행경로를 만들지 않는다.

## 6. PASS 기준

기능별 PASS는 다음을 모두 만족해야 한다.

```text
UI 입력 의미 == contract 입력 의미
실행 결과 == deterministic engine 결과
화면 표시 == supplied result/projection
저장 후 복원 == 동일 선언/버전/해시 의미
다른 계층에 제품 특례 누수 없음
관련 자동 regression PASS
frozen legacy core guard PASS
```

이 정책은 UI acceptance 단계에서 발생하는 모든 수정의 우선 판단 기준이다.
