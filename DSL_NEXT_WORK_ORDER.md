# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-02 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 차트 상태의 완전 복원을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = UNMANAGED-PANE AUDIT FIX PINNED / USER-LOCAL REVALIDATION REQUIRED
```

## 현재 SSOT 원칙

```text
의미 있는 화면 변경
 -> one logical Chart State
 -> one JSON serialization/restore path
 -> one atomic runtime JSON file
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

`단일 파일 존재`만으로 PASS하지 않는다.

## 최신 실제 UI 실패

전수검사에서 다음이 확인됐다.

```text
메인 price pane 상대배치 불일치
저장된 compare-1 / compare-2 / compare-3 pane 누락
```

viewport 1봉 이동 문제는 이후 수정으로 제거됐다.

## 최신 자동검증 실패와 수정

`chart-state-runtime-audit` 회귀에서 저장 대상이 아닌 native pane 높이를 비율 분모에 넣어 false failure가 발생했다.

수정 기준:

```text
persisted managed panes만 상대비율 비교
unmanaged native panes는 비율 분모에서 제외
persisted pane missing은 hard FAIL 유지
```

같은 계산을 runtime audit과 layout stabilizer에 적용했다.

## UIA-1 restore gate

```text
1. chart-state.json hydrate
2. primary chart/runtime construction
3. registered Add-ons restore
4. primary request ready
5. persisted compare subjects restore
6. persisted pane layout restore as managed-pane ratio vector
7. persisted startup viewport reassert
8. actual live runtime snapshot capture
9. persisted JSON vs live runtime exhaustive comparison
10. PASS -> persistence attach
11. FAIL -> persistence detached + all mismatch paths reported
```

## Pane layout 규칙

```text
saved managed pane heights
 -> managed-pane relative weights
 -> stable native pane index mapping
 -> bulk stretch-factor application
 -> managed-pane proportional audit
```

저장되지 않은 native pane이 화면 높이를 소비해도 저장 대상 pane들 사이의 비율 판정에는 영향을 주지 않는다.

저장된 pane이 실제 runtime에서 누락되면 계속 hard FAIL이다.

## 자동검증 범위

`verify.bat`는 다음을 포함한다.

```text
single JSON SSOT
live state/persistence path
exhaustive runtime audit
managed-pane ratio layout restore
unmanaged native pane coexistence
persisted pane missing fail-closed
compare-subject startup restore
startup viewport authority
workspace startup
product restart
chart bridge
console policy
frozen core guard
```

## 다음 사용자 검증

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후 실제 UI 재기동을 다시 확인한다.

실제 UI PASS 전 UIA-1 완료 처리 금지.

## 수정 경계

```text
Core
 -> Bridge / Runtime
 -> Add-ons
 -> JSON persistence
```

절대 규칙:

```text
repository-root core/ 수정 금지
기능별 persistent side-store 추가 금지
localStorage를 product state authority로 사용 금지
검증 assertion 약화/skip 금지
startup incomplete state가 persisted JSON을 overwrite하는 것 금지
실제 UI PASS 전 UIA-1 완료 처리 금지
```
