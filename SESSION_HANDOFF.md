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
STATUS = AUTO USER-LOCAL PASS / REAL UI REVALIDATION REQUIRED
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

## 최신 실제 UI 실패와 수정

사용자 재현:

```text
SuperTrend 삽입
+ 메인/서브 패널 높이 변경
+ 브라우저 종료/재기동
 -> 복원 실패
```

추적에서 저장 순서 경쟁상태를 확인했다.

```text
older queued PUT
latest close POST/beacon
 -> arrival/completion inversion
 -> older state may overwrite latest state
```

현재 수정:

```text
Chart State semantic mutation -> stateRevision 증가
full JSON -> revision 포함
JSON writer -> serialization
lower revision write -> stale reject
unique atomic temp file
```

따라서 최신 종료상태가 먼저 저장된 후 과거 요청이 늦게 도착해도 최신 JSON을 되돌릴 수 없다.

회귀검증에는 다음 순서를 포함한다.

```text
latest state POST
 -> delayed stale PUT
 -> GET
 -> latest SuperTrend/layout/workspace 유지
```

2026-09-01 사용자 로컬 자동 재검증:

```text
verify.bat -> [PASS] current verification passed
```

## 계층 분리

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core: deterministic 의미/계산. repository-root `core/`는 frozen reference이며 수정 금지.
- Bridge / Runtime: lifecycle/state routing/observation. 계산 금지.
- Add-ons: 기능별 계산과 private state.
- JSON persistence: serialization/hydrate/atomic write/stale-write rejection만 담당.

## 다음 검증

남은 단계는 실제 UI 재검증이다.

```text
SuperTrend 삽입
메인/서브 패널 높이 변경
브라우저 종료
재기동
 -> 동일 상태 복원
 -> timeframe/workspace 유지
 -> PERSISTENCE ERROR 없음
```

실제 UI 복원 PASS 전 다음 UI 기능으로 넘어가지 않는다.

## Frozen legacy Core

```text
path: core/
freeze source: 20b963749052f0d0e42506024a02e4e218a4d05a
core tree: 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

수정/이동/추가/삭제 금지.
