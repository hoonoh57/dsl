# Quant DSL Current State

Status: **FINAL THREE-AXIS BASELINE PASS / UI CONSISTENCY ACCEPTANCE ACTIVE / GENERIC SUBJECT RESTORE ATOMICITY REMOTE PASS / USER-LOCAL REVALIDATION PENDING**  
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

`main`은 현재 작업 권한이 아니다. 기존 strict remediation Steps 1~15는 모두 **COMPLETE / USER-LOCAL PASS**다.

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

## 4-axis invariant

```text
Core    = generic drawing/rendering SSOT and reusable primitives
Runtime = feature-blind lifecycle/routing/capabilities
Add-on  = feature-specific semantics/private state
JSON    = persistence only
```

현재 compare 정상 경로:

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews / ChartSubjectViewManager
 -> persistent compare pane
```

UI shell은 state command만 쓴다. alternate lifecycle path는 없다.

## Latest real-UI evidence — 2026-09-03

startup reconcile serialization fix `b6ca51b` 적용 후에도 실제 재기동에서:

```text
compare-1 height expected 52 actual missing
compare-2 height expected 108 actual missing
compare-3 height expected 327 actual missing
```

이 재현으로 이전 설명인 단순 idle race만으로는 부족함이 확인됐다.

## Additional root cause

generic `ChartSubjectViewManager.replace()`는 subject restore 실패 후 incomplete owner/signature를 남길 수 있었다. 다음 동일 signature reconcile이 incomplete owner를 settled로 오인하면 live pane records가 없는 상태가 고착된다.

## Current remediation

feature-blind Runtime invariant로 수정했다.

```text
same signature settled = signature 같음 + mounted views 수가 requested subjects 수와 같음
restore failure = current owner 전체 rollback
partial success panes = rollback
retry same signature = complete rebuild
```

Core, Compare Add-on semantics, JSON persistence, UI는 수정하지 않았다. height fallback도 없다.

## Active execution repository

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 검증 완료 Chart commit:

```text
vendor/kiwoom-condition target = e272e18adbb4530f0edfe5046a19e3b7e0272606
```

원격 evidence:

```text
PR #3 Add-on boundary audit = PASS
PR #3 Chart platform npm test = PASS
kiwoom-condition/main push CI = PASS
```

## Implementation compliance gate

`DSL_IMPLEMENTATION_COMPLIANCE_GATE.md`는 계속 active authority다.

`verify.bat`은 architecture-compliance를 behavior보다 먼저 fail-closed 검증한다. 구조 위반은 기능 PASS로 덮지 않는다.

## Current status

```text
LATEST REAL UI FAILURE = CONFIRMED / NOT ACCEPTED
COMPARE OBJECT-LIFECYCLE AUTHORITY VIOLATION = REMEDIATED
STARTUP RECONCILE SERIALIZATION = REMEDIATED
GENERIC SUBJECT RESTORE ATOMICITY = REMOTE CODE REMEDIATED
4-AXIS BOUNDARY VERIFICATION = PASS FOR THIS TRANCHE
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

자동검증 PASS 뒤 동일 저장 상태로 Market Chart를 완전 종료/재기동한다.

최우선 acceptance:

```text
compare-1/2/3가 재조회/재추가 없이 자동 복원
persisted 52/108/327 pane heights 복원
STATE RESTORE ERROR 없음
```

그 후 add/replace/select/delete, TF sync, 동일지표 ON/OFF를 확인한다.

## Frozen legacy Core

```text
freeze source commit = 20b963749052f0d0e42506024a02e4e218a4d05a
frozen core tree     = 8b3f081de926f5c9f69e9cdbc158b81b2275176c
```

No modification/move/add/delete under repository-root `core/`.
