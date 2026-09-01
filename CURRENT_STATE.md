# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE**  
Updated: 2026-09-02 KST

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
 -> next-session semantic exact restore
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

## Latest real-UI failure

최신 실제 UI 전수복원 gate는 다음을 보고했다.

```text
workspace.layout.primaryPanes.priceHeight expected 435 actual 195
persisted compare-1 / compare-2 / compare-3 pane layout actual missing
```

viewport / visibleCount mismatch는 이전 수정 후 이번 오류에서는 재발하지 않았다.

## Root-cause refinement

기존 whole-chart ratio 복원은 `native pane 수 = primary 2개 + persistence manager가 직접 관리하는 pane 수`라고 가정했다.

실제 차트에는 persistence manager 밖에서 생성된 native pane도 존재할 수 있으므로 이 가정이 깨지면 bulk ratio 경로가 비활성화되고, 다시 개별 `setHeight` fallback으로 내려가면서 primary 높이가 435 -> 195처럼 재배분됐다.

또한 runtime audit은 전체 native pane vector/index를 알지 못해 mixed pane 구조의 비율 복원을 정확히 판정할 수 없었다.

## Corrected restore authority

```text
hydrate chart-state.json
 -> construct primary chart
 -> restore registered Add-ons
 -> primary request becomes ready
 -> restore compare subjects
 -> assign stable native pane identity
 -> snapshot every native pane height
 -> overlay persisted weights onto their exact native indices
 -> one full native stretch-factor vector apply
 -> reassert persisted startup viewport
 -> capture complete live runtime layout including native indices
 -> exhaustive proportional audit against persisted JSON
 -> PASS: persistence attach
 -> FAIL: persistence remains detached + all mismatches reported
```

### Pane layout semantic

저장된 각 pane 높이는 전체 chart의 상대 배치 weight로 사용한다.

```text
all current native pane heights
 + persisted primary/add-on/compare pane weights at stable native indices
 -> one complete stretch-factor vector
 -> one bulk apply
```

persistence manager가 직접 관리하지 않는 pane도 전체 vector에는 포함되며 현재 weight를 유지한다. 저장된 pane 자체가 runtime에서 없으면 여전히 hard FAIL이다.

창 전체 높이가 달라져 실제 픽셀이 비례 변경되는 것은 정상이며, JSON 원본 높이 값은 그대로 보존한다.

### Compare subject private state

비교종목의 semantic state를 갱신할 때 기존 private persisted state를 병합하여 `__layout` 등 generic private state를 보존한다.

### Viewport semantic

startup 조립 중 발생하는 임시 logical range는 persisted authority를 바꾸지 않는다. 최종 layout 안정화 전후에 저장된 viewport를 다시 적용하고 workspace 문서도 원래 viewport/visibleCount로 복구한 뒤 audit한다.

## Verification scope now pinned

`dsl-live-studio`는 위 수정이 포함된 chart submodule을 가리킨다.

자동검증에 다음 회귀가 포함된다.

```text
whole-chart ratio layout restore
mixed managed/unmanaged native pane restore
stable native pane identity after pane removal
complete native pane vector runtime audit
missing persisted pane fail-closed
compare private layout state preservation
compare-subject deferred startup restore
startup viewport authority reassertion
single JSON SSOT / persistence / console / frozen-core guards
```

현재 상태:

```text
LATEST REAL UI FAILURE = CONFIRMED
MIXED NATIVE PANE ROOT CAUSE = FIXED IN SOURCE
DSL SUBMODULE = UPDATED
USER-LOCAL AUTO REVALIDATION = REQUIRED
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
