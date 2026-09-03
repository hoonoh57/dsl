# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE / STARTUP RESTORE RACE FIX REMOTE PASS / USER-LOCAL REVALIDATION PENDING**  
Updated: 2026-09-03 KST

## Recovery authority

```text
1. SESSION_HANDOFF.md
2. DSL_NEXT_WORK_ORDER.md
3. CURRENT_STATE.md
4. DSL_DOCUMENT_AUTHORITY_INDEX.md
5. DSL_IMPLEMENTATION_COMPLIANCE_GATE.md
6. active architecture/policy documents
7. checkpoints/evidence
8. historical documents
```

## Current branch

```text
dsl-live-studio
```

`main`은 현재 작업 권한이 아니다.

기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다.

## Current active work — UIA-1

목표:

```text
meaningful UI state
 -> one logical Chart State
 -> one JSON persistence path
 -> Runtime-owned object graph
 -> next-session semantic exact restore
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

## Current corrected architecture

단일 경로:

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews / ChartSubjectViewManager
 -> persistent compare pane
```

UI shell:

```text
add / replace / remove / select / timeframe
 -> state-port write only
```

금지된 alternate lifecycle path는 없다.

## Latest real-UI evidence — 2026-09-03

사용자 로컬에서:

```text
dsl-live-studio = 3c4dcff
vendor/kiwoom-condition = 1d7277e
verify.bat = PASS
```

후 실제 재기동에서 fail-closed audit가 다음을 보고했다.

```text
compare-1/2/3 persisted height = expected
live compare pane records = actual missing
workspace instrument blank name -> resolved name mismatch
```

분류:

```text
compare missing = PRODUCT DEFECT / startup restore completion race
name mismatch = runtime audit semantic drift / display metadata enrichment
```

## Current remediation

Compare Runtime Add-on reconcile을 직렬화하여 같은 owner의 lifecycle 작업이 겹치지 않고 `whenIdle()`이 이전/현재 실제 restore 작업 전체를 포함하도록 수정했다.

runtime-state audit은 instrument `name` 보강을 identity 변경으로 취급하지 않되 다음은 계속 엄격하다.

```text
instrument kind
instrument code
workspace/timeframe
addon state
pane existence
layout proportions
active Add-ons
external compare pane ids
```

pane 높이 계산, Core, UI lifecycle authority는 수정하지 않았다.

## Active execution repository

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 검증 완료 Chart commit:

```text
vendor/kiwoom-condition target = b6ca51b5256349bf3f0dea2ede3c45449cd2e34a
```

원격 evidence:

```text
Add-on boundary audit = PASS
Chart platform npm test = PASS (95 tests)
kiwoom-condition/main push CI = PASS
```

## Implementation compliance gate

`DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`는 계속 active authority다.

`verify.bat`은 다음 순서로 fail-closed 검증한다.

```text
architecture-compliance
 -> generic Add-on boundary audit
 -> syntax
 -> focused chart/runtime regression
 -> compare runtime ownership regression
 -> single JSON persistence
 -> console policy
 -> frozen core
```

구조 위반은 behavior PASS로 덮지 않는다.

## Current status

```text
LATEST REAL UI FAILURE = CONFIRMED / NOT ACCEPTED
COMPARE OBJECT-LIFECYCLE AUTHORITY VIOLATION = REMEDIATED
STARTUP RESTORE COMPLETION RACE = REMOTE CODE REMEDIATED
INSTRUMENT NAME AUDIT DRIFT = REMOTE CODE REMEDIATED
REMOTE STRUCTURE / CONTRACT VERIFICATION = PASS
USER-LOCAL REVALIDATION = READY / PENDING
UIA-1 = NOT PASS YET UNTIL REAL UI RESTART ACCEPTANCE
GLOBAL COMPLIANCE = REMEDIATION_REQUIRED
```

## Next exact action

사용자 로컬 `dsl-live-studio`에서 generated/state evidence와 기존 chart-state JSON을 지우지 않고:

```text
git pull --ff-only
git submodule update --init --recursive
.\verify.bat
```

자동검증 PASS 뒤 동일한 저장 상태로 Market Chart를 완전 종료/재기동한다.

가장 중요한 acceptance:

```text
compare-1/2/3가 재조회/재추가 없이 자동 복원
persisted pane heights 복원
STATE RESTORE ERROR 없음
```

그 후 add/replace/select/delete, TF sync, 동일지표 ON/OFF를 확인한다.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
