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
STATUS = MIXED NATIVE PANE FIX PINNED / USER-LOCAL AUTO + REAL UI REVALIDATION REQUIRED
```

## JSON 상태 권한

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 workspace/display/addons/layout/geometry를 함께 보존한다.

단일 JSON 파일 존재만으로 SSOT PASS로 인정하지 않는다. 저장된 의미 상태가 실제 재기동 차트 전체 projection과 동일해야 한다.

## 최신 실제 UI failure evidence

최신 전수복원 gate가 다음을 보고했다.

```text
workspace.layout.primaryPanes.priceHeight expected 435 actual 195
addons.research.compare-subjects.state.__layout.panes.compare-1.height actual missing
addons.research.compare-subjects.state.__layout.panes.compare-2.height actual missing
addons.research.compare-subjects.state.__layout.panes.compare-3.height actual missing
```

viewport / visibleCount mismatch는 이번 실패에서는 재발하지 않았다.

## 최신 root cause

whole-chart ratio 복원 코드가 다음을 암묵적으로 가정했다.

```text
native pane count = primary 2 + persistence manager owned panes
```

실제 chart에는 persistence manager 밖에서 생성된 native pane도 존재할 수 있다. 이 경우 bulk ratio 계획을 만들지 못하고 개별 `setHeight` fallback으로 내려가며, 각 높이 적용 때 chart engine이 다른 pane을 다시 배분해 primary가 435 -> 195처럼 변했다.

runtime audit도 전체 native pane vector/index를 모르므로 mixed pane 구조에서 복원 비율을 정확히 검증하지 못했다.

## 이번 구조 수정

### 1. Stable native pane identity

모든 add-on pane은 생성/삭제에 따라 현재 native index를 안정적으로 조회할 수 있다.

### 2. Complete native pane vector restore

```text
snapshot every native pane height
 -> persisted primary/add-on/compare weight를 exact native index에 덮어씀
 -> manager 밖 pane은 현재 weight 유지
 -> complete vector를 stretch factor로 한 번에 적용
```

더 이상 `native pane 수 == manager record 수 + 2`를 요구하지 않는다.

### 3. Runtime audit

live runtime snapshot에 전체 native pane height vector와 persisted pane의 native index를 포함한다. audit은 이 전체 vector 기준 비율을 검사한다.

저장된 pane 자체가 없다면 여전히 hard FAIL이다.

### 4. Compare private state

비교종목 semantic state 갱신 시 기존 private persisted state를 병합하여 `__layout` 등 generic private state를 보존한다.

### 5. Startup viewport authority

최초 JSON viewport/visibleCount를 startup authority로 별도 보존하고 전체 layout 안정화 전후에 다시 적용한다.

## Restore gate

```text
hydrate
 -> primary runtime construction
 -> registered Add-ons
 -> primary request ready
 -> compare subjects
 -> stable native pane identity
 -> complete native pane ratio restore
 -> startup viewport reassert
 -> live runtime snapshot including native pane vector
 -> persisted-vs-live exhaustive audit
 -> PASS: persistence attach
 -> FAIL: persistence detached, existing JSON preserved, mismatches reported
```

## 자동검증 범위

`verify.bat`에 다음 회귀가 포함되어 있다.

```text
whole-chart ratio restore
mixed managed/unmanaged native pane restore
stable native pane identity after pane removal
complete native pane vector audit
missing persisted pane fail-closed
compare private layout preservation
compare-subject deferred restore
startup viewport authority reassert
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
