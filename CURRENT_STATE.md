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

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다. Final baseline checkpoint는 `STEP15_REPO_WIDE_COMPLIANCE_CHECKPOINT_2026-09-01.md`다.

## Current active work — UI consistency acceptance

현재 UIA-1은 시작상태와 영속상태의 일관성을 검증한다.

```text
UI semantic state
 -> one logical Chart State
 -> Bridge/Runtime state port
 -> one JSON serialization/restore path
 -> next-session UI restore
```

사용자 최신 권한에 따라 timeframe만 별도로 저장하거나 localStorage를 제품 상태 SSOT로 사용하는 방식은 폐기했다.

canonical runtime state file:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

runtime state document:

```text
schemaVersion
visualsVisible
display
workspace
addons
```

`workspace`는 종목, timeframe, 기준일, 표시 봉 수, price/return mode, viewport, 최근 종목 등 다음 세션에 의미가 있는 화면 상태를 보존한다.

`addons[*].state`는 지표/전략/비교차트 파라미터와 layout, exact geometry/point coordinates를 JSON-compatible state로 보존한다.

이 파일은 full-document atomic write를 사용한다. 기존 `_chart.json` + Add-on별 shard는 unified file이 없을 때 한 번 migration한 뒤 제거한다.

## Startup restore

```text
single chart state hydrate
 -> chart/runtime wiring
 -> workspace state projection
 -> existing loadInitial() automatic run
 -> Add-on/layout/geometry restore
 -> READY
```

2026-09-01 사용자 로컬 `verify.bat`는 `[PASS] current verification passed`로 완료됐다. 따라서 자동 회귀검증은 **USER-LOCAL PASS**다.

UIA-1 전체 상태:

```text
AUTOMATED = USER-LOCAL PASS
MANUAL UI RESTORE = PENDING
```

실제 브라우저 종료/재기동 후 5분봉, 종목, 표시범위, 수익률 모드, 지표 설정 등 동일 semantic state 복원 확인 전에는 UIA-1 전체 PASS로 닫지 않는다.

## Layer authority

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

- Core = deterministic DSL/parser/runtime/indicator/execution meaning. UI 복원 특례 금지.
- Bridge/Runtime = lifecycle/routing/state-port adaptation. feature calculation 금지.
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
