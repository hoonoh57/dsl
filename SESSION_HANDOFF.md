# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 현재 단계는 지금까지 이식한 DSL 기능을 실제 UI 경로에서 하나씩 일관성 검증하는 단계다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = REAL UI FAILURE FIX WRITTEN / USER-LOCAL REVALIDATION REQUIRED
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
```

## JSON 상태 권한

의미 있는 화면 변경은 기능별 하드코딩 저장소로 나누지 않는다.

```text
UI semantic change
 -> one logical Chart State
 -> one JSON persistence path
 -> one atomic runtime state file
 -> next session hydrate
 -> UI projection restore
```

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 다음을 함께 보존한다.

```text
workspace
  primary instrument / timeframe / base date
  visible count / price display mode / viewport / recent instruments
  primary price + volume pane layout

display
  global chart display state

addons
  enabled/visible
  feature parameters
  strategy/compare state
  add-on pane layout
  exact geometry/point coordinates
```

## UIA-1 실제 UI 실패와 수정

이전 자동검증은 단순 JSON roundtrip을 확인했지만 실제 UI 이벤트가 SSOT까지 도달하는지를 충분히 검증하지 못했다.

사용자 실제 재현:

```text
SuperTrend 삽입
 + 메인/서브 패널 높이 변경
 -> 브라우저 종료
 -> 재기동
 -> SuperTrend 및 layout 복원 실패
```

화면에는 `PERSISTENCE ERROR · Failed to fetch`도 확인됐다.

확인된 결함:

```text
1. transient persistence fetch 실패 시 기본상태로 계속 진행 가능
2. main price/volume pane 높이는 JSON state에 연결되지 않음
3. 이전 regression은 실제 UI state-event path를 검증하지 않음
```

현재 수정:

```text
persistence load transient failure -> bounded retry
persistence authority unavailable -> mutable chart attach 차단
primary price/volume resize -> workspace.layout.primaryPanes
add-on pane resize -> addons[*].state.__layout
rapid UI changes -> latest document coalesced save
unload -> latest full-state flush
```

SuperTrend 추가 + 메인/서브 패널 높이 변경을 실제 state store/controller 경로로 통과시키는 회귀검증을 `verify.bat`에 포함했다.

## 콘솔 출력

```text
start/restart/stop 성공 -> 최종 PASS 한 줄
verify 성공             -> 최종 PASS 한 줄
실패                     -> 실패한 명령/서비스 + 오류 구간만 출력
전체 stdout/stderr       -> .runtime 내부 로그 파일에 유지
```

PowerShell 5.1 native command는 stderr 존재가 아니라 process exit code로 성공/실패를 판정한다.

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle, state routing, pane-state observation. 계산/보정 금지.
- Add-ons: 기능별 계산과 private state.
- JSON persistence: full state serialization/hydrate/atomic write only.

## 다음 검증

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

그 후 실제 UI에서:

```text
SuperTrend 삽입
메인/서브 패널 높이 변경
브라우저 종료
재기동
 -> 동일 상태 복원
 -> PERSISTENCE ERROR 없음
```

이 실제 UI 복원까지 PASS 전 다음 UI 기능으로 넘어가지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
