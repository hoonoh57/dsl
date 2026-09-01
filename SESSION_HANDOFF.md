# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local 결과 + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = SELECTIVE REAL UI RESTORE FAILURE CONFIRMED / EXHAUSTIVE RUNTIME AUDIT WRITTEN / REVALIDATION REQUIRED
```

## JSON 상태 권한

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 workspace/display/addons/layout/geometry를 함께 보존한다.

그러나 단일 JSON 파일 존재만으로 SSOT PASS로 인정하지 않는다. 저장된 의미 상태가 실제 재기동 차트 전체 projection과 동일해야 한다.

## 최신 사용자 결정

기능별 복구 패치를 계속 추가하지 않는다.

```text
current live chart state
 -> one JSON
restart
 -> restore JSON
 -> capture complete live runtime state
 -> exhaustive compare
```

전수 비교 범위:

```text
primary instrument
compare subjects
timeframe / base date / adjusted
viewport / visible range
price display mode
all active registered Add-ons
all persisted Add-on properties/private state
primary price + volume pane heights
all persisted Add-on pane heights
```

## Restore gate

```text
hydrate
 -> runtime construction
 -> Add-on/subject/layout restore
 -> live runtime snapshot
 -> persisted-vs-live exhaustive audit
 -> PASS: persistence attach
 -> FAIL: persistence detached, existing JSON preserved, mismatch paths reported together
```

불완전하게 복원된 화면이 기존 `chart-state.json`을 덮어쓰지 못하게 한다.

관련 evidence:

```text
UIA1_FULL_RUNTIME_STATE_AUDIT_2026-09-01.md
```

## 다음 사용자 로컬 검증

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후 실제 UI에서 종목/비교종목/Add-on 속성/거래량 및 서브차트 높이/timeframe/viewport/display mode를 변경하고 종료·재기동한다.

정상은 전부 동일하게 복원되는 것이다. 실패 시 `STATE RESTORE ERROR`의 mismatch 목록을 받아 해당 경로를 한 번에 수정한다.

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle/state routing/layout projection/runtime audit. 계산 금지.
- Add-ons: 기능별 계산과 private state.
- JSON persistence: serialization/hydrate/atomic write/stale-write rejection만 담당.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
