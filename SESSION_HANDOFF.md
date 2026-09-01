# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-02 KST**

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
STATUS = WHOLE-RESTORE FIX PINNED / USER-LOCAL AUTO + REAL UI REVALIDATION REQUIRED
```

## JSON 상태 권한

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 workspace/display/addons/layout/geometry를 함께 보존한다.

단일 JSON 파일 존재만으로 SSOT PASS로 인정하지 않는다. 저장된 의미 상태가 실제 재기동 차트 전체 projection과 동일해야 한다.

## 최신 실제 UI failure evidence

전수복원 gate가 다음을 함께 보고했다.

```text
workspace.layout.primaryPanes.priceHeight mismatch
workspace.viewport logicalRange one-bar shift
workspace.visibleCount one-count mismatch
persisted compare-1 / compare-2 / compare-3 pane missing
```

이 결과는 이전 자동검증 PASS보다 우선한다.

## 이번 구조 수정

### 1. Compare subject startup

저장된 비교종목은 primary chart request가 생기기 전에는 만들지 않는다. primary가 준비된 뒤 복원하며, 생성 실패는 pane별 실제 오류로 노출한다.

### 2. Whole-chart pane layout

개별 pane 픽셀 높이를 순차 적용하지 않는다. lightweight chart가 각 `setHeight` 때 다른 pane을 다시 배분하므로 exact restore가 구조적으로 불안정하다.

현재 복원 방식:

```text
persisted primary + add-on + compare pane heights
 -> one ordered whole-chart relative weight vector
 -> native pane stretch factors bulk apply
 -> proportional runtime audit
```

전체 window/canvas 높이가 달라져 픽셀값이 비례 변경될 수는 있다. 저장된 pane 누락은 계속 hard FAIL이다.

### 3. Startup viewport authority

최초 JSON viewport/visibleCount를 startup authority로 별도 보존하고, 전체 layout 안정화 전후에 다시 적용한다. startup 중 임시 viewport event가 persisted authority를 바꾸지 못하게 한다.

## Restore gate

```text
hydrate
 -> primary runtime construction
 -> registered Add-ons
 -> primary request ready
 -> compare subjects
 -> whole-chart ratio layout restore
 -> startup viewport reassert
 -> live runtime snapshot
 -> persisted-vs-live exhaustive audit
 -> PASS: persistence attach
 -> FAIL: persistence detached, existing JSON preserved, mismatches reported
```

## 자동검증 범위

`verify.bat`에 다음 회귀가 포함되어 있다.

```text
whole-chart ratio restore
missing persisted pane fail-closed
compare-subject deferred restore
compare concrete failure propagation
startup viewport authority reassert
exhaustive runtime audit
single JSON persistence
workspace/product restart
console policy
frozen core guard
```

## 다음 사용자 실행

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

`[PASS] current verification passed`가 나오면 `start.bat`으로 실제 UI 재기동 검증을 한다.

검증 상태 예:

```text
primary 종목
비교 종목 3개 이상
SuperTrend / 기타 Add-on 속성
메인/거래량/여러 서브 pane 배치
timeframe
viewport / 표시갯수
가격/수익률 표시모드
```

브라우저 종료·재실행 뒤 위 의미 상태가 모두 동일하고 `STATE RESTORE ERROR`, `PERSISTENCE ERROR`가 없어야 UIA-1 PASS다.

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
