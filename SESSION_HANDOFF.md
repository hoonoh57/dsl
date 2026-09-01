# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / ARCHITECTURE GATE ENFORCED / 2026-09-02 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local 결과 + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

> 모든 production 로직 수정 전에 `DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`를 먼저 적용한다. 구조가 불명확하면 코드를 쓰지 않고 generic engine 경로를 먼저 추적한다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = COMPARE OBJECT-LIFECYCLE AUTHORITY VIOLATION CONFIRMED / RUNTIME REFACTOR REQUIRED
```

## 이번에 확인된 근본 원인

저장 JSON 자체가 틀린 것이 아니었다.

```text
JSON에는 compare-1 / compare-2 / compare-3 + layout 존재
Runtime 실제 object graph에는 compare pane missing
```

기본엔진을 재추적한 결과 비교종목만 일반 Add-on lifecycle을 우회하고 있었다.

```text
위반 구조
JSON compare node
 -> registered Runtime Add-on: state normalize only
 -> UI Workspace / ShellController: persistent compare pane 직접 생성
```

따라서 state authority와 object lifecycle authority가 둘로 갈라져 선택적 복원이 발생했다.

## 정상 JSON 착탈 구조

```text
JSON add-on node
 -> Runtime registration/reconcile
 -> Add-on instance
 -> Add-on-owned object/pane create/dispose/visible
 -> state/property/layout projection
```

비교종목도 예외 없이:

```text
JSON compare node
 -> Compare Runtime Add-on
 -> generic subjectViews capability
 -> compare panes
```

이어야 한다.

UI shell은 add/replace/remove/select를 state-port에 쓰는 역할만 갖는다.

## 신규 구현 준수 게이트

신규 active authority:

```text
DSL_IMPLEMENTATION_COMPLIANCE_GATE.md
```

production 수정 전에 반드시:

```text
owner boundary
existing generic engine path
state SSOT
persistent object lifecycle authority
forbidden adjacent-layer behavior
architecture invariant regression
```

을 확정한다.

`verify.bat`은 이제 모든 기능 테스트보다 먼저 `architecture-compliance`를 실행한다.

현재 gate는 특히 다음 구조를 금지한다.

```text
axis sibling imports
Bridge contract implementation import
UI shell의 compare persistent pane 직접 생성
Compare Runtime Add-on이 object lifecycle을 소유하지 않는 구조
feature-specific persistence authority
localStorage product state
frozen legacy core dependency
```

## 현재 다음 작업

```text
1. Compare Runtime Add-on -> generic subjectViews로 JSON subjects reconcile
2. Compare ShellController의 view factory/object creation authority 제거
3. MarketChartWorkspace의 compare pane 직접 생성 제거
4. JSON만으로 add/remove/visible/property/layout 재생성 검증
5. architecture-compliance PASS
6. 전체 verify PASS
7. 실제 UI 재기동 검증
```

구조 수정이 끝나기 전에는 pane 높이/비율/타이밍을 더 보정하지 않는다.

## 분리 원칙

제품 실행:

```text
AXIS 1
AXIS 2
AXIS 3
Bridge
```

UI/Chart:

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

둘 다 항상 준수한다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
