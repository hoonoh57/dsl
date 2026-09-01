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
STATUS = WRITTEN / REMOTE_UNVALIDATED
```

현재 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
```

## 사용자 최신 영속성 권한

의미 있는 화면 변경은 기능별 하드코딩 저장소로 나누지 않는다.

```text
UI semantic change
 -> one logical Chart State
 -> one JSON persistence path
 -> one atomic runtime state file
 -> next session hydrate
 -> UI projection restore
```

현재 canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

이 파일 한 개에 다음 상태를 함께 보존한다.

```text
workspace
  primary instrument
  timeframe
  base date
  visible count
  price display mode
  viewport logical range
  recent instruments

display
  global chart display state

addons
  enabled/visible
  feature parameters
  strategy state
  compare-subject state
  pane layout
  arbitrary instance geometry such as exact point coordinates
```

마우스 hover/focus 같은 순간 UI 이벤트 자체는 영속 상태가 아니지만, 사용자가 만든 선/도형의 점 좌표처럼 다음 세션에 의미가 있는 결과 상태는 Add-on instance state에 JSON으로 정확히 들어가야 한다.

## UIA-1 수정

### 시작 직후 빈 차트

분류: Bridge / Runtime startup ordering defect.

```text
state hydrate
 -> UI/runtime wiring
 -> existing loadInitial() 자동 1회
 -> READY
```

### timeframe 재기동 복원 실패

초기 localStorage/timeframe 전용 JSON 방식은 최신 사용자 권한과 맞지 않아 폐기했다.

현재 수정:

```text
single Chart State hydrate
 -> workspace timeframe/instrument/baseDate/display/viewport 복원
 -> primary chart 자동 loadInitial()
 -> Add-on/layout/instance state 같은 document에서 복원
```

제품 경로에서는 `WorkspaceTimeframePreference`, timeframe 전용 browser port, timeframe 전용 route/file을 사용하지 않는다.

기존 `_chart.json` + Add-on별 JSON shard가 남아 있는 환경은 unified state가 없을 때 한 번 읽어 `chart-state.json`으로 migration한 뒤 shard를 제거한다. 이후 모든 semantic change는 full document atomic rewrite로 같은 파일 하나에 저장한다.

## 콘솔 출력 수정

기존 raw test output과 startup 단계별 INFO/PASS가 오류를 밀어내는 문제가 있었다.

현재 규칙:

```text
start/restart/stop 성공 -> 최종 PASS 한 줄
verify 성공             -> 최종 PASS 한 줄
실패                     -> 실패한 명령/서비스 + 오류 구간만 출력
전체 stdout/stderr       -> .runtime 내부 로그 파일에 유지
```

현재 검증은 raw `node --test ...` 묶음을 사용자에게 직접 실행시키지 않고 `verify.bat` 하나로 수행한다.

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle, request/response, state-port routing. 계산/보정 금지.
- Add-ons: 기능별 계산과 private semantic state. 선/도형 좌표도 자신의 JSON-compatible state로 기록.
- JSON persistence: full state document의 serialization/hydrate/atomic write만 담당. 전략/지표 의미를 계산하지 않음.

## UIA-1 다음 검증

사용자 local:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

정상이면 콘솔은 다음 한 줄만 보여야 한다.

```text
[PASS] current verification passed
```

실패하면 성공한 테스트 출력은 숨기고 실패한 명령의 오류 구간만 보여야 한다.

UI에서는 5분봉뿐 아니라 종목/표시범위/수익률 모드/지표 파라미터 등 의미 있는 상태를 바꾼 뒤 브라우저를 종료·재기동하여 동일하게 복원되는지 확인한다.

파일 확인:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/
 -> chart-state.json 하나만 runtime state JSON으로 존재
```

PASS 전 다음 UI 기능으로 넘어가지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
