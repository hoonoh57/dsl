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

사용자 실제 UI 재검증에서 다음 실패가 확인됐다.

```text
SuperTrend 삽입
+ 메인/서브 패널 높이 변경
+ browser restart
 -> state restore FAIL
```

추적 결과 종료 직전 저장 경쟁상태를 확인했고 다음과 같이 수정했다.

```text
semantic state mutation -> monotonic stateRevision 증가
single JSON document -> stateRevision 포함
JSON writes -> serialized
incoming revision < persisted revision -> stale write reject
atomic temporary file -> unique path
```

회귀검증은 다음 실제 실패 순서를 포함한다.

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

현재 상태:

```text
REAL UI FAILURE = PREVIOUSLY CONFIRMED
ORDERING FIX = WRITTEN
AUTO REVALIDATION = USER-LOCAL PASS
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
- JSON persistence = serialization/hydrate/atomic write/stale-write rejection only.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
