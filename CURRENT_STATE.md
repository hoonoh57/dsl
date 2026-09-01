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
persisted compare-1 / compare-2 / compare-3 pane missing
```

viewport one-bar shift는 이후 수정으로 제거되었다.

## Latest automated failure classification

2026-09-02 user-local `verify.bat`에서 `chart-state-runtime-audit`가 실패했다.

원인은 저장 대상이 아닌 native pane의 높이까지 비율 분모에 포함시킨 **검증 계산 결함**이었다.

수정 원칙:

```text
persisted managed panes = restore authority
unmanaged native panes  = 비율 분모에서 제외
persisted pane missing  = hard FAIL 유지
```

동일 계산을 runtime audit과 layout stabilizer 양쪽에 적용했다.

## Corrected restore authority

```text
hydrate chart-state.json
 -> construct primary chart
 -> restore registered Add-ons
 -> primary request becomes ready
 -> restore compare subjects
 -> restore complete persisted pane layout as one ratio vector
 -> reassert persisted startup viewport
 -> capture actual live runtime snapshot
 -> exhaustive compare against persisted JSON
 -> PASS: persistence attach
 -> FAIL: persistence remains detached + all mismatches reported
```

### Pane layout semantic

저장된 각 pane 높이는 **저장 대상 pane들 사이의 상대 배치 비율**의 근거다.

저장 대상이 아닌 native pane은 전체 canvas 높이를 소비할 수 있으므로 persisted ratio의 분모가 아니다.

```text
saved managed pane heights
 -> managed-pane relative weights
 -> native pane indices에 bulk 적용
 -> managed-pane proportional runtime audit
```

저장된 pane 자체가 누락되면 계속 hard FAIL이다.

### Viewport semantic

startup 조립 중 발생하는 임시 logical range는 persisted authority를 바꾸지 않는다. 최종 layout 안정화 전후에 저장된 viewport를 다시 적용하고 workspace 문서도 원래 viewport/visibleCount로 복구한 뒤 audit한다.

### Compare subject semantic

저장된 비교종목은 primary request가 준비된 뒤 생성한다. 생성 실패는 `missing`으로 숨기지 않고 실제 pane별 원인을 restore failure로 노출한다.

## Verification scope now pinned

자동검증 범위:

```text
whole-chart ratio layout restore
unmanaged native pane coexistence
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
UNMANAGED-PANE AUDIT DEFECT = FIXED
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
