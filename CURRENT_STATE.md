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

현재 목표:

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

이전 자동검증 PASS 이후 실제 UI에서 다음 실패가 확인됐다.

```text
SuperTrend 삽입
+ 메인/서브 패널 높이 변경
+ browser restart
 -> state restore FAIL
```

화면에 `PERSISTENCE ERROR · Failed to fetch`가 나타났으며, 자동검증만으로 UIA-1을 PASS 처리할 수 없다는 것이 확인됐다.

확인된 구현 누락:

```text
primary price/volume pane layout persistence 없음
persistence load failure 후 defaults로 계속 진행 가능
regression이 live UI state-event path를 검증하지 않음
```

현재 수정:

```text
persistence transient fetch retry
JSON authority unavailable -> mutable state attach blocked
primary pane resize -> workspace.layout.primaryPanes
add-on pane resize -> addons[*].state.__layout
latest state coalesced save + unload full-state flush
live SuperTrend/layout SSOT regression added
```

현재 상태:

```text
FIX = WRITTEN
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
- Bridge/Runtime = lifecycle/routing/state observation. feature calculation 금지.
- Add-ons = feature-specific behavior/private state.
- JSON persistence = state serialization/hydrate/atomic write only.

## Final product architecture

```text
AXIS 2 exact-PIT selection
 -> Candidate Set + evidence
 -> AXIS 3 promoted Condition/Strategy versions + RunPlan
 -> versioned Bridge preflight
 -> AXIS 1 deterministic single-instrument execution
```

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
