# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / COMPARE RUNTIME OWNERSHIP REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-02 KST**

기존 remediation Steps 1~15는 USER-LOCAL PASS로 완료되었다. 현재 UIA-1의 구조 위반 제거는 원격 구현/검증까지 완료되었고, 다음 단계는 user-local 자동검증 + 실제 UI 재기동 acceptance다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = RUNTIME OWNERSHIP REMOTE PASS / USER-LOCAL REVALIDATION READY
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
```

이 계약은 구현 완료 후에도 regression authority로 유지한다.

## 현재 구현된 구조

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> generic subjectViews / ChartSubjectViewManager
 -> compare pane create/dispose/visibility/property/layout
```

UI shell:

```text
add / replace / remove / select / timeframe
 -> state-port write only
```

UI shell의 persistent pane / bar-window / projection / legend 직접 생성은 제거되었다.

## 실제 실행 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

검증 완료 Chart commit:

```text
1d7277eb2040c6d7c79a243573d2598bc5c8584c
```

원격 evidence:

```text
Add-on boundary audit = PASS
Chart platform npm test = 93 / 93 PASS
```

## 현재 SSOT

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

`enabled / visible / state / layout`가 같은 JSON이면 재기동 후 같은 persistent object graph가 생성되어야 한다.

## 자동검증 순서

`verify.bat`:

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

architecture-compliance FAIL은 behavior PASS로 덮지 않는다.

## 다음 작업 — user-local validation only

사용자 작업 브랜치는 `dsl-live-studio`다. `origin/main`을 섞지 않는다.

```text
1. git pull --ff-only
2. git submodule update --init --recursive
3. verify.bat
4. 자동검증 PASS면 실제 Market Chart 실행
5. 비교종목 add / replace / select / delete 확인
6. pane 높이 변경 후 재기동 높이 복원 확인
7. 저장된 비교종목 pane이 재기동 후 재조회/재추가 없이 자동 복원되는지 확인
8. TF동기 확인
9. 동일지표 ON/OFF 확인
```

실제 UI 재기동 acceptance가 PASS하기 전에는 UIA-1을 완료로 승격하지 않는다.

## 절대 규칙

```text
repository-root core/ 수정 금지
기능별 persistent side-store 금지
localStorage product-state authority 금지
UI controller의 Add-on lifecycle 우회 금지
동일 기능의 두 번째 restore path 금지
assertion 완화/skip/allowlist 금지
origin/main을 현재 작업브랜치에 pull하지 않음
user-local strategies.db / artifact_history evidence를 destructive reset으로 삭제하지 않음
실제 UI PASS 전 UIA-1 완료 금지
repository-wide compliance PASS 선언 금지
```
