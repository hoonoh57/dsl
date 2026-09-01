# DSL Implementation Compliance Gate

Status: **ACTIVE PRE-IMPLEMENTATION AUTHORITY / 2026-09-02 KST**

이 문서는 모든 신규 로직 작성과 수정 전에 반드시 통과해야 하는 구조 준수 게이트다. 기능이 동작하는지보다 **권한 경계와 상태 권한을 지키며 동작하는지**를 먼저 판정한다.

## 1. 이번 위반의 원인

기존 원칙은 문서에 있었지만 구현 진입조건으로 강제되지 않았다.

```text
원칙 문서 존재
 != 구현 전 구조 검토 강제
 != 구조 위반 자동검출
```

이번 비교종목 복원 문제에서 확인된 실패 원인은 다음과 같다.

```text
1. 실패 증상부터 수정하고 기존 generic engine 경로를 먼저 끝까지 추적하지 않음
2. behavior regression은 있었지만 ownership regression이 없었음
3. JSON에 상태가 있다는 사실과 JSON이 실제 객체 생성 authority라는 사실을 혼동
4. UI 전용 controller가 Add-on runtime의 객체/pane 생성권한을 우회해도 검증이 통과함
5. 같은 기능에 runtime 복원경로와 UI 복원경로가 공존하는 것을 금지하는 자동 gate가 없었음
```

따라서 앞으로는 사람의 주의가 아니라 **절차 + 자동검증**으로 차단한다.

## 2. 두 종류의 분리 원칙을 모두 검사

### 제품 실행 4경계

```text
AXIS 1 = deterministic single-instrument DSL/runtime/execution
AXIS 2 = exact-PIT selection/evidence
AXIS 3 = Condition/Strategy version lifecycle/orchestration
Bridge = versioned Request -> Response composition only
```

세 축의 내부 구현을 섞거나 Bridge 밖에서 교차 조합하지 않는다.

### UI/Chart 4경계

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

```text
Core            = generic deterministic meaning
Bridge/Runtime  = lifecycle/routing/ports/composition
Add-on          = feature-specific object/state/projection ownership
JSON persistence= serialization/hydrate/atomic write only
```

UI는 명령을 전달하고 상태를 표시할 수 있지만 Add-on이 소유한 persistent 객체를 별도 경로로 재생성하는 authority를 갖지 않는다.

## 3. 구현 전 필수 체크

아래가 모두 답변되기 전에는 production code를 수정하지 않는다.

```text
A. 이 변경의 유일한 owning boundary는 어디인가?
B. 이미 존재하는 generic engine 경로는 무엇인가?
C. state SSOT는 무엇인가?
D. persistent object를 생성/삭제/표시하는 authority는 누구인가?
E. 인접 계층에서 절대 하면 안 되는 일은 무엇인가?
F. 동일 기능의 두 번째 실행/복원/저장 경로를 만들지 않는가?
G. 실패 시 default/보정/우회가 아니라 fail-closed 하는가?
H. 구조 위반을 직접 잡는 invariant test가 먼저 존재하는가?
```

하나라도 `unknown`이면 구현 대신 추적/감사를 먼저 한다.

## 4. 필수 구현 순서

```text
authority 문서 확인
 -> failure 계층 분류
 -> 기존 generic engine end-to-end 추적
 -> owner / SSOT / lifecycle authority 확정
 -> architecture invariant test 추가 또는 확인
 -> 그 테스트가 위반구조를 실제로 FAIL시키는지 확인
 -> production 구현
 -> focused behavior test
 -> 관련 regression
 -> architecture gate 재검증
 -> frozen core guard
 -> 실제 UI 검증
```

`production 구현 -> 나중에 architecture 설명` 순서를 금지한다.

## 5. JSON 착탈 구조 필수 규칙

persistent Add-on은 다음 한 경로만 허용한다.

```text
Chart State JSON node
 -> Runtime registration/reconcile
 -> Add-on instance create/dispose
 -> Add-on-owned pane/series/object create/dispose
 -> node state/visibility/property projection
```

금지:

```text
JSON node
 -> Runtime은 상태만 읽음
 -> UI controller가 같은 Add-on 객체/pane을 별도 생성
```

UI controller는 다음만 허용한다.

```text
사용자 명령 수집
 -> state-port에 선언적 상태 변경
 -> Runtime이 그 상태를 관찰하여 실제 객체를 reconcile
```

따라서 `enabled/visible/state`가 동일한 JSON이면 재기동 후 동일한 Add-on object graph가 생성되어야 한다.

## 6. Architecture gate가 반드시 잡아야 하는 것

```text
axis sibling direct import
Bridge contract의 axis implementation import
repository-root frozen core 의존/수정
feature-specific persistence side-store
localStorage product-state authority
UI shell의 Add-on-owned persistent pane 직접 생성
Runtime Add-on이 존재하지만 실제 object lifecycle을 UI가 대신 소유하는 이중경로
persistence layer의 feature-specific 조건
critical regression skip/expectedFailure/assertion 완화
```

## 7. 현재 compare-subject 판정

현재 확인된 구조:

```text
research.compare-subjects JSON node
 -> registered Runtime Add-on은 state normalize만 수행
 -> MarketChartWorkspace / ShellController가 compare pane을 별도 생성
```

이는 본 게이트 위반이다.

수정 완료 기준:

```text
JSON compare node
 -> Runtime Add-on
 -> generic subject-view capability
 -> compare panes
```

UI shell은 add/replace/remove/select를 JSON state에 기록하는 역할만 남는다.

## 8. 검증 우선순위

`verify.bat`은 기능 회귀보다 먼저 architecture compliance를 실행해야 한다.

```text
architecture-compliance
 -> syntax
 -> focused product tests
 -> persistence/runtime tests
 -> console policy
 -> frozen core
```

architecture-compliance가 FAIL하면 후속 기능 PASS로 덮을 수 없다.

## 9. 예외 금지

이 게이트를 통과시키기 위한 allowlist, temporary bypass, feature exception, compatibility exception을 추가하지 않는다.

새 일반 능력이 필요하면 먼저 generic boundary 확장으로 별도 설계하고, 그 뒤 feature가 사용한다.
