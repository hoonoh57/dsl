# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-02 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 차트 상태의 완전 복원을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = MIXED NATIVE PANE FIX PINNED / USER-LOCAL REVALIDATION REQUIRED
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

최신 전수검사에서 다음이 확인됐다.

```text
메인 price pane: expected 435 / actual 195
compare-1 / compare-2 / compare-3 persisted pane layout: actual missing
```

이 오류에서 viewport / visibleCount mismatch는 재발하지 않았다.

## 최신 owning-layer 수정

기존 ratio restore는 모든 add-on pane이 persistence layout manager에 등록되어 있다고 가정했다. 실제 native chart에는 manager 밖의 pane도 존재할 수 있으므로 이 가정이 깨지면 bulk restore가 비활성화되고 순차 높이 적용으로 fallback됐다.

현재는 각 pane에 stable native index를 부여하고 전체 native pane vector를 기준으로 복원한다.

```text
all native panes snapshot
 -> persisted pane을 stable native index로 매핑
 -> unmanaged pane은 현재 weight 유지
 -> one complete stretch-factor vector
 -> one bulk apply
 -> whole-native-vector runtime audit
```

저장된 pane이 실제 runtime에 없으면 계속 hard FAIL이다.

비교종목 semantic state 쓰기는 기존 private persisted state를 병합하여 `__layout` 등 generic private state를 보존한다.

## UIA-1 restore gate

재기동은 반드시 다음 순서를 통과해야 한다.

```text
1. chart-state.json hydrate
2. primary chart/runtime construction
3. registered Add-ons restore
4. primary request ready
5. persisted compare subjects restore
6. stable native pane identity resolution
7. complete native pane ratio restore
8. persisted startup viewport reassert
9. actual live runtime snapshot capture
10. persisted JSON vs live runtime exhaustive comparison
11. PASS -> persistence attach
12. FAIL -> persistence detached + all mismatch paths reported
```

## 자동검증 범위

`verify.bat`는 다음을 포함한다.

```text
single JSON SSOT
live state/persistence path
exhaustive runtime audit
whole-chart ratio layout restore
mixed managed/unmanaged native pane restore
stable native pane identity
persisted pane missing fail-closed
compare private layout state preservation
compare-subject startup restore
startup viewport authority
workspace startup
product restart
chart bridge
console policy
frozen core guard
```

## 다음 사용자 검증

먼저:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후 `start.bat`으로 실제 UI를 확인한다.

기존 `chart-state.json` 상태를 그대로 사용해 재기동해도 되며, 필요하면 한 번 다시 다음 상태를 만든 뒤 종료·재기동한다.

```text
primary 종목
비교 종목 3개 이상
SuperTrend 등 Add-on + 속성
거래량 pane 높이
여러 서브차트 pane 높이
timeframe
viewport / 표시갯수
가격/수익률 표시모드
```

PASS 기준:

```text
재기동 후 의미 상태 전부 동일
모든 비교 pane 복원
전체 pane 상대 배치 동일
viewport / 표시갯수 동일
STATE RESTORE ERROR 없음
PERSISTENCE ERROR 없음
```

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
