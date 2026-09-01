# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / ARCHITECTURE GATE ENFORCED / 2026-09-02 KST**

기존 remediation Steps 1~15는 USER-LOCAL PASS로 완료되었다. 현재 UIA-1은 기능 패치가 아니라 구조 위반 제거를 먼저 수행한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = ARCHITECTURE VIOLATION CONFIRMED / RUNTIME OWNERSHIP REFACTOR REQUIRED
```

## CURRENT_IMPLEMENTATION_CONTRACT

모든 production 수정 전에 이 계약을 먼저 확정하며, 구현 중 소유권이 바뀌면 코드를 멈추고 계약부터 다시 작성한다.

```text
OWNER_BOUNDARY = Add-on + generic Chart Runtime capability
STATE_SSOT = chart-state.json / addons.research.compare-subjects
LIFECYCLE_AUTHORITY = Compare Runtime Add-on through generic subjectViews
FORBIDDEN_NEIGHBORS = UI persistent pane creation; feature logic in persistence; Core special-case
ALTERNATE_PATHS = NONE
FAILURE_MODE = fail-closed; persisted JSON preserved
ARCH_INVARIANT = JSON compare node alone must create/dispose/visible the same runtime panes without UI view factory
```

## 구현 전 강제 게이트

모든 production 코드 수정 전에 `DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`를 적용한다.

```text
1. owner boundary 확정
2. existing generic engine path end-to-end 추적
3. state SSOT 확정
4. persistent object lifecycle authority 확정
5. forbidden adjacent-layer behavior 명시
6. architecture invariant test로 위반구조를 먼저 FAIL시킴
7. 그 뒤 production 구현
```

하나라도 unknown이면 구현하지 않고 감사/추적을 계속한다.

## 현재 확인된 compare 위반

```text
JSON research.compare-subjects
 -> Runtime Add-on은 state normalize만 수행
 -> MarketChartWorkspace / ShellController가 pane을 별도 생성
```

이 이중경로 때문에 JSON에 저장된 `compare-1/2/3`가 정상이어도 재기동 Runtime object graph에는 pane이 없을 수 있었다.

## 이번 수정의 유일한 목표 구조

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews capability
 -> compare pane create/dispose/visibility/property/layout
```

UI shell:

```text
add / replace / remove / select 명령
 -> state-port write only
```

UI shell의 persistent pane 직접 생성은 금지한다.

## 현재 SSOT

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

`enabled / visible / state`가 같은 JSON이면 재기동 후 동일한 Add-on object graph가 만들어져야 한다.

## 자동검증 순서

`verify.bat`:

```text
architecture-compliance
 -> syntax
 -> focused chart/runtime regression
 -> single JSON persistence
 -> console policy
 -> frozen core
```

architecture-compliance FAIL은 behavior PASS로 덮지 않는다.

현재 architecture gate는 다음을 직접 검사한다.

```text
current implementation contract 존재
axis sibling direct import 금지
Bridge contract data-only
UI shell의 compare persistent pane 직접 생성 금지
Compare Runtime Add-on의 generic subjectViews 사용 필수
persistence layer feature-specific authority 금지
frozen legacy core dependency 금지
```

## 다음 구현 작업

```text
1. Compare Runtime Add-on이 JSON subjects를 generic subjectViews로 reconcile
2. ShellController에서 persistent view factory/pane 생성 authority 제거
3. Workspace에서 compare pane 직접 생성 코드 제거
4. JSON -> Runtime Add-on -> pane 생성/삭제/표시 회귀검증
5. 기존 compare UI 명령은 state-port write만 수행하도록 유지
6. architecture-compliance PASS
7. 전체 verify PASS
8. 실제 UI 재기동 검증
```

이 구조 수정이 끝나기 전에는 높이/비율/타이밍 보정을 추가하지 않는다.

## 절대 규칙

```text
repository-root core/ 수정 금지
기능별 persistent side-store 금지
localStorage product-state authority 금지
UI controller의 Add-on lifecycle 우회 금지
동일 기능의 두 번째 restore path 금지
assertion 완화/skip/allowlist 금지
실제 UI PASS 전 UIA-1 완료 금지
```
