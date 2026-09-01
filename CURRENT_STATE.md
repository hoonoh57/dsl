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

2026-09-01 실제 UI 재검증:

```text
SuperTrend restore = PASS
volume pane height restore = FAIL
sub-chart indicator pane height restore = FAIL
```

따라서 JSON 문서와 Add-on 활성 상태 자체는 복구되지만 pane layout의 startup projection이 아직 실패한 것으로 분류했다.

추가 확인 원인:

```text
persisted pane heights hydrate
 -> startup add-on/native pane construction
 -> chart library auto-layout recalculates heights
 -> height observers can treat startup-generated heights as new semantic state
 -> persisted layout loses authority before startup settles
```

현재 수정:

```text
startup layout observation -> suppressed until add-on activation settles
persisted primary volume + add-on pane heights -> retained as authority
all add-ons idle -> persisted heights reapplied across multiple layout frames
restore complete -> user resize observation/persistence enabled
```

회귀검증은 startup auto-layout이 저장된 높이를 임의값으로 변경한 뒤 최종적으로 JSON 높이가 실제 pane에 다시 적용되는 시나리오를 포함한다.

현재 상태:

```text
SUPERTrend REAL UI = PASS
PANE HEIGHT REAL UI = FAIL CONFIRMED
PANE STARTUP RESTORE FIX = WRITTEN
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
- Bridge/Runtime = lifecycle/routing/state observation/layout projection. feature calculation 금지.
- Add-ons = feature-specific behavior/private state.
- JSON persistence = serialization/hydrate/atomic write/stale-write rejection only.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
