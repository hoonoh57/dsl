# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE / COMPARE RUNTIME OWNERSHIP REMOTE PASS / USER-LOCAL REVALIDATION PENDING**  
Updated: 2026-09-02 KST

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

## Confirmed prior real-UI failure

```text
persisted compare-1 / compare-2 / compare-3 pane missing
```

원인은 JSON 손상이 아니라 `research.compare-subjects`의 object lifecycle이 일반 Add-on Runtime을 우회하고 UI에 존재했던 것이었다.

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

## Active execution repository

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 gitlink:

```text
vendor/kiwoom-condition = 1d7277eb2040c6d7c79a243573d2598bc5c8584c
```

원격 검증 evidence:

```text
kiwoom-condition Add-on boundary audit = PASS
kiwoom-condition Chart platform npm test = 93 / 93 PASS
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
LATEST REAL UI FAILURE = PREVIOUSLY CONFIRMED
COMPARE OBJECT-LIFECYCLE AUTHORITY VIOLATION = REMOTE CODE REMEDIATED
REMOTE STRUCTURE / CONTRACT VERIFICATION = PASS
DSL SUBMODULE LINK = UPDATED TO VERIFIED CHART COMMIT
USER-LOCAL REVALIDATION = READY / PENDING
UIA-1 = NOT PASS YET UNTIL REAL UI RESTART ACCEPTANCE
GLOBAL COMPLIANCE = REMEDIATION_REQUIRED
```

## Next exact action

사용자 로컬 `dsl-live-studio`에서 generated/state evidence를 지우지 않고:

```text
git pull --ff-only
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 뒤 실제 UI 재기동으로 compare add/replace/select/delete, persisted auto-restore, pane height, TF sync, 동일지표를 확인한다.

가장 중요한 acceptance는 저장된 compare pane이 재기동 후 재추가/재조회 없이 자동 복원되는 것이다.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
