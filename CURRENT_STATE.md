# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE**  
Updated: 2026-09-01 KST

## Recovery authority

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. active architecture/policy documents
6. checkpoints/evidence
7. historical documents
```

## Current branch

```text
dsl-live-studio
```

`main`은 현재 작업 권한이 아니다.

## Completed baseline

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다.

## Current active work — UIA-1

목표:

```text
모든 의미 있는 UI 변경
 -> one logical Chart State
 -> one JSON persistence path
 -> next-session exact restore
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

## Latest real-UI result

실제 UI에서 선택적 복원 실패가 반복 확인됐다.

```text
SuperTrend restore = PASS
volume / indicator pane height restore = FAIL
added compare subject restore = FAIL reported
```

따라서 `JSON 파일 하나`만으로는 충분하지 않으며, 저장된 전체 의미 상태가 재기동 후 실제 차트 전체 projection과 동일한지 확인하는 gate가 필요하다고 확정했다.

## Corrected restore authority

```text
hydrate chart-state.json
 -> construct complete runtime
 -> restore primary subject/timeframe/viewport/display
 -> restore Add-ons + compare subjects
 -> restore all persisted pane layouts
 -> capture actual live runtime snapshot
 -> exhaustive compare against persisted JSON
 -> PASS: persistence attach
 -> FAIL: persistence remains detached + all mismatches reported
```

전수 비교 범위:

```text
primary instrument
compare subjects
primary + compare timeframe
base date / adjusted mode
viewport / visible range
price display mode
registered active Add-ons
all persisted Add-on properties/private state
primary price + volume pane heights
all persisted Add-on pane heights
```

startup restore가 불완전하면 그 상태를 새 권한으로 저장하지 않는다. `STATE RESTORE ERROR`가 발생하면 기존 `chart-state.json`을 보존한다.

## Latest automated revalidation

2026-09-01 user-local `verify.bat`은 `workspace-startup`에서 실패했다.

분류:

```text
TEST DEFECT
```

기존 테스트가 과거의 단순 READY 반환 문자열만 찾고 있어, 새 restore audit 이후의 `restore:'PASS'` READY 계약을 따라가지 못했다. 제품 복원 로직 실행 실패로 분류하지 않는다.

수정된 startup 검증 순서:

```text
initial load
 -> compare subjects idle
 -> persisted layout stabilization
 -> exhaustive runtime audit
 -> persistence attach
 -> READY PASS
```

현재 상태:

```text
REAL UI SELECTIVE RESTORE FAILURE = CONFIRMED
EXHAUSTIVE RUNTIME AUDIT = WRITTEN
WORKSPACE STARTUP TEST CONTRACT = CORRECTED
DSL SUBMODULE PIN = UPDATED
AUTO REVALIDATION = REQUIRED
REAL UI REVALIDATION = REQUIRED
UIA-1 = NOT PASS YET
```

## Layer authority

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core = deterministic DSL/parser/runtime/indicator/execution meaning. UI 복원 특례 금지.
- Bridge/Runtime = lifecycle/routing/state observation/layout projection/runtime audit. feature calculation 금지.
- Add-ons = feature-specific behavior/private state.
- JSON persistence = serialization/hydrate/atomic write/stale-write rejection only.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
