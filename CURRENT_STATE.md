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

실제 UI 전수복원 gate가 다음 실패를 함께 검출했다.

```text
primary price pane layout mismatch
viewport one-bar shift + visibleCount mismatch
persisted compare-1 / compare-2 / compare-3 pane missing
```

이 결과로 이전 자동검증 PASS만으로 UIA-1을 닫을 수 없음을 재확인했다.

## Corrected restore authority

```text
hydrate chart-state.json
 -> construct primary chart
 -> restore registered Add-ons
 -> primary request becomes ready
 -> restore compare subjects
 -> restore complete pane layout as one ratio vector
 -> reassert persisted startup viewport
 -> capture actual live runtime snapshot
 -> exhaustive compare against persisted JSON
 -> PASS: persistence attach
 -> FAIL: persistence remains detached + all mismatches reported
```

### Pane layout semantic

여러 pane의 픽셀 높이를 순서대로 `setHeight`하면 뒤 pane 적용이 앞 pane 높이를 다시 바꾸므로 복원 authority로 사용할 수 없다.

따라서 저장된 각 pane 높이는 **전체 pane 간 상대 배치 비율**의 근거로 사용하고, 재기동 시 모든 native pane에 한 번에 stretch-factor vector로 적용한다.

```text
saved price / volume / add-on / compare pane heights
 -> one ordered whole-chart weight vector
 -> one bulk native layout application
 -> proportional runtime audit
```

창 전체 높이가 달라져도 동일한 상대 배치를 의미상 동일한 복원으로 본다. 단, 저장된 pane 자체가 누락되면 여전히 hard FAIL이다.

### Viewport semantic

startup 조립 중 발생하는 임시 logical range는 persisted authority를 바꾸지 않는다. 최종 layout 안정화 전후에 저장된 viewport를 다시 적용하고 workspace 문서도 원래 viewport/visibleCount로 복구한 뒤 audit한다.

### Compare subject semantic

저장된 비교종목은 primary request가 준비된 뒤 생성한다. 생성 실패는 `missing`으로 숨기지 않고 실제 pane별 원인을 restore failure로 노출한다.

## Verification scope now pinned

`dsl-live-studio`는 위 수정이 포함된 chart submodule을 가리킨다.

자동검증에 다음 회귀를 추가했다.

```text
whole-chart ratio layout restore
missing persisted pane fail-closed
compare-subject deferred startup restore
concrete compare restore error propagation
startup viewport authority reassertion
existing exhaustive runtime audit
single JSON SSOT / persistence / console / frozen-core guards
```

현재 상태:

```text
LATEST REAL UI FAILURE = CONFIRMED
WHOLE-PANE RATIO RESTORE FIX = PINNED
COMPARE STARTUP RESTORE FIX = PINNED
VIEWPORT AUTHORITY FIX = PINNED
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
