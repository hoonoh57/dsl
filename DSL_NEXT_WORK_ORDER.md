# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / GENERIC SUBJECT RESTORE ATOMICITY REMOTE PASS / USER-LOCAL REVALIDATION PENDING / 2026-09-03 KST**

기존 remediation Steps 1~15는 USER-LOCAL PASS로 완료되었다. UIA-1은 Runtime ownership 수정과 startup reconcile serialization 후에도 실제 재기동에서 compare pane `actual missing`이 재현되었고, 추가 generic Runtime atomicity 결함을 수정/검증했다. 다음 단계는 동일 저장 상태 user-local 재검증이다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = GENERIC SUBJECT RESTORE ATOMICITY REMOTE PASS / USER-LOCAL REVALIDATION READY
```

## CURRENT_IMPLEMENTATION_CONTRACT

```text
CORE_OWNER = generic drawing/rendering primitives only
RUNTIME_OWNER = feature-blind subject lifecycle + pane service
ADDON_OWNER = compare semantics/state mapping only
JSON_OWNER = persistence only
STATE_SSOT = chart-state.json / addons.research.compare-subjects
LIFECYCLE_AUTHORITY = Compare Add-on -> generic subjectViews Runtime
FORBIDDEN_NEIGHBORS = UI persistent pane creation; compare branch in Runtime/Core; JSON live authority
ALTERNATE_PATHS = NONE
FAILURE_MODE = fail-closed; persisted JSON preserved
ATOMICITY_INVARIANT = failed subject replace leaves no partial owner panes and same-signature retry must rebuild
IDLE_INVARIANT = Runtime whenIdle must not resolve before all queued/in-flight Add-on lifecycle work completes
```

## 현재 구현된 구조

```text
Chart State JSON
 -> Runtime registration/reconcile
 -> Compare Runtime Add-on
 -> serialized subjectViews requests
 -> generic ChartSubjectViewManager atomic replace
 -> generic pane create/dispose/layout
```

UI shell은 add / replace / remove / select / timeframe state command만 수행한다.

## Latest WYSIWYG failure and new root cause

실제 재기동에서 여전히:

```text
compare-1 height expected 52 actual missing
compare-2 height expected 108 actual missing
compare-3 height expected 327 actual missing
```

추가 확인된 원인:

```text
subject restore 중 하나가 실패
 -> 실패 view pane dispose
 -> owner signature/부분 성공 views 잔존 가능
 -> 다음 동일 signature replace가 settled로 오인 가능
 -> Runtime pane records missing 상태 고착
```

수정 후 강제 계약:

```text
same signature no-op = signature 동일 + requested subject 수만큼 views 완성
하나라도 restore 실패 = 이번 owner의 모든 view/pane rollback
동일 signature retry = 전체 rebuild
```

generic 회귀테스트는 첫 시도 partial success + transient failure 후 active pane 0, 두 번째 동일 signature 시 전체 재생성까지 검증한다.

## 4축 준수

```text
Core = 변경 없음
Runtime = generic lifecycle atomicity만 수정
Add-on = 변경 없음
JSON = 변경 없음
UI = 변경 없음
feature-specific Runtime/Core branch = 없음
height workaround = 없음
```

## 실제 실행 연결

```text
dsl-live-studio
 -> vendor/kiwoom-condition
 -> condition1516/chart-platform
```

현재 검증 완료 Chart commit:

```text
e272e18adbb4530f0edfe5046a19e3b7e0272606
```

원격 evidence:

```text
PR #3 Add-on boundary audit = PASS
PR #3 npm test = PASS
kiwoom-condition/main push CI = PASS
```

## 현재 SSOT

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

기존 저장 JSON을 삭제/초기화하지 않고 복원해야 한다.

## 다음 작업 — 동일 상태 user-local revalidation only

사용자 작업 브랜치는 `dsl-live-studio`다. `origin/main`을 섞지 않는다.

```text
1. git pull --ff-only
2. git submodule update --init --recursive
3. .\verify.bat
4. 기존 chart-state JSON을 지우지 않고 Market Chart 완전 종료/재기동
5. compare-1/2/3 자동 복원 확인
6. persisted 52/108/327 pane heights 복원 확인
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
Runtime/Core의 compare-specific compatibility branch 금지
pane height workaround로 missing pane 문제 은폐 금지
assertion 완화/skip/allowlist 금지
origin/main을 현재 작업브랜치에 pull하지 않음
user-local strategies.db / artifact_history / chart-state evidence를 destructive reset으로 삭제하지 않음
실제 UI PASS 전 UIA-1 완료 금지
repository-wide compliance PASS 선언 금지
```
