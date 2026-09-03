# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / STARTUP RESTORE RACE FIX REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-03 KST**

기존 remediation Steps 1~15는 USER-LOCAL PASS로 완료되었다. UIA-1은 Runtime ownership 구조 수정 후 실제 재기동에서 startup restore completion race가 추가 확인되었고, 해당 원격 수정/검증까지 완료되었다. 다음 단계는 동일 저장 상태로 user-local 재검증이다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = STARTUP RESTORE RACE REMOTE PASS / USER-LOCAL REVALIDATION READY
```

## CURRENT_IMPLEMENTATION_CONTRACT

```text
OWNER_BOUNDARY = Add-on + generic Chart Runtime capability
STATE_SSOT = chart-state.json / addons.research.compare-subjects
LIFECYCLE_AUTHORITY = Compare Runtime Add-on through generic subjectViews
FORBIDDEN_NEIGHBORS = UI persistent pane creation; feature logic in persistence; Core special-case
ALTERNATE_PATHS = NONE
FAILURE_MODE = fail-closed; persisted JSON preserved
ARCH_INVARIANT = JSON compare node alone must create/dispose/visible the same runtime panes without UI view factory
IDLE_INVARIANT = Runtime whenIdle must not resolve before all prior/in-flight compare lifecycle work completes
```

## 현재 구현된 구조

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> serialized generic subjectViews reconciliation
 -> ChartSubjectViewManager
 -> compare pane create/dispose/visibility/property/layout
```

UI shell:

```text
add / replace / remove / select / timeframe
 -> state-port write only
```

UI shell의 persistent pane / bar-window / projection / legend 직접 생성은 금지 상태를 유지한다.

## Latest WYSIWYG failure and remediation

실제 재기동에서:

```text
compare-1/2/3 persisted height expected, runtime actual missing
primary/recent instrument blank name expected, resolved name actual
```

확인된 원인:

```text
1. Compare Runtime의 연속 reconcile이 겹쳐 최신 pending이 이전 실제 pane restore보다 먼저 완료될 수 있음
2. runtime audit가 startup name enrichment를 identity mismatch로 과잉 판정
```

수정 후 강제 계약:

```text
same-owner compare reconcile overlap = forbidden
whenIdle = all prior/in-flight lifecycle work 포함
instrument identity = kind + code strict
instrument display name enrichment = audit identity 아님
pane existence/layout audit = strict 유지
```

pane 높이 계산이나 Core는 수정하지 않았다.

## 실제 실행 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 검증 완료 Chart commit:

```text
b6ca51b5256349bf3f0dea2ede3c45449cd2e34a
```

원격 evidence:

```text
PR #2 Add-on boundary audit = PASS
PR #2 Chart platform npm test = PASS (95 tests)
kiwoom-condition/main push CI = PASS
```

## 현재 SSOT

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

기존 저장 JSON을 삭제/초기화하지 않고 복원해야 한다.

## 자동검증 순서

`verify.bat`:

```text
architecture-compliance
 -> generic Add-on boundary audit
 -> syntax
 -> focused chart/runtime regression
 -> compare runtime ownership / serialized idle regression
 -> runtime state audit regression
 -> single JSON persistence
 -> console policy
 -> frozen core
```

architecture-compliance FAIL은 behavior PASS로 덮지 않는다.

## 다음 작업 — 동일 상태 user-local revalidation only

사용자 작업 브랜치는 `dsl-live-studio`다. `origin/main`을 섞지 않는다.

```text
1. git pull --ff-only
2. git submodule update --init --recursive
3. .\verify.bat
4. 기존 chart-state JSON을 지우지 않고 Market Chart 완전 종료/재기동
5. compare-1/2/3 자동 복원 확인
6. persisted pane heights 복원 확인
7. STATE RESTORE ERROR가 없는지 확인
8. 통과 후 add / replace / select / delete 확인
9. TF동기 확인
10. 동일지표 ON/OFF 확인
```

실제 UI 재기동 acceptance가 PASS하기 전에는 UIA-1을 완료로 승격하지 않는다.

## 절대 규칙

```text
repository-root core/ 수정 금지
기능별 persistent side-store 금지
localStorage product-state authority 금지
UI controller의 Add-on lifecycle 우회 금지
동일 기능의 두 번째 restore path 금지
pane height workaround로 missing pane 문제 은폐 금지
assertion 완화/skip/allowlist 금지
origin/main을 현재 작업브랜치에 pull하지 않음
user-local strategies.db / artifact_history / chart-state evidence를 destructive reset으로 삭제하지 않음
실제 UI PASS 전 UIA-1 완료 금지
repository-wide compliance PASS 선언 금지
```
