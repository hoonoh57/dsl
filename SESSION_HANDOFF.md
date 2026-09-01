# DSL Session Handoff

Status: **PRIMARY HUMAN HANDOFF / UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

이 문서는 새 세션에서 가장 먼저 읽는 복구 문서다. 최신 사용자 결정 + user-local PASS + 현재 `dsl-live-studio` 상태가 stale 문서보다 우선한다.

핵심 운영 원칙:

> 사용자 진행보고는 기본적으로 `한 일 / 할 일`만 사람이 이해하는 용어로 짧게 한다.

> 정상 콘솔은 최종 `[PASS]` 한 줄만, 실패 시에는 실패한 부분의 오류 구간만 제한된 길이로 출력한다. 전체 원시 로그는 내부 파일에 유지한다.

> 실제 UI 재현이 자동검증보다 우선한다. 실제 UI 실패 상태에서는 PASS로 닫지 않는다.

## 현재 상태

```text
PREVIOUS REMEDIATION = Steps 1 through 15 COMPLETE / USER-LOCAL PASS
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
STATUS = SUPERTrend REAL UI PASS / PANE HEIGHT REAL UI FAIL / FIX WRITTEN / REVALIDATION REQUIRED
```

## JSON 상태 권한

```text
UI semantic change
 -> one logical Chart State
 -> monotonic stateRevision
 -> one JSON persistence path
 -> one atomic runtime state file
 -> next session hydrate
 -> UI projection restore
```

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

한 문서에 workspace/display/addons/layout/geometry를 함께 보존한다.

## 최신 실제 UI 결과

사용자 재검증:

```text
SuperTrend 재기동 복원 = PASS
거래량 pane 높이 복원 = FAIL
서브차트 지표 pane 높이 복원 = FAIL
```

이 결과로 Add-on 상태 자체와 pane layout 상태를 분리해 추적했다.

확인 원인:

```text
persisted pane heights hydrate
 -> native chart + add-on pane startup construction
 -> chart library auto-layout recalculates actual heights
 -> observer sees startup-generated heights
 -> startup layout can replace persisted layout authority before render settles
```

현재 수정:

```text
startup 동안 pane height observer persistence 억제
JSON persisted primary/add-on pane heights를 authority로 유지
all add-ons idle 후 persisted layout 재적용
여러 layout frame에 걸쳐 재적용
stabilization 완료 후 사용자 resize persistence 활성화
```

회귀검증은 startup auto-layout이 실제 pane 높이를 임의값으로 변경해도 JSON 높이가 유지되고, stabilization 후 실제 pane이 JSON 높이로 돌아오는 시나리오를 포함한다.

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle/state routing/observation/layout projection. 계산 금지.
- Add-ons: 기능별 계산과 private state.
- JSON persistence: serialization/hydrate/atomic write/stale-write rejection만 담당.

## 다음 검증

먼저 사용자 로컬 자동검증:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

PASS 후 실제 UI:

```text
거래량 pane 높이 변경
서브차트 지표 pane 높이 변경
브라우저 종료
재기동
 -> 두 높이 모두 복원
 -> SuperTrend/timeframe 등 기존 복원 상태 유지
```

실제 UI pane 높이 복원 PASS 전 UIA-1을 닫지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
