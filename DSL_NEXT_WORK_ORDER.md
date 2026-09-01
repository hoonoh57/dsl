# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 차트 상태의 완전 복원을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = SELECTIVE RESTORE FAILURE CONFIRMED / EXHAUSTIVE AUDIT WRITTEN / REVALIDATION REQUIRED
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

하지만 `단일 파일 존재`만으로 PASS하지 않는다.

## UIA-1 restore gate

재기동은 반드시 다음 순서를 통과해야 한다.

```text
1. chart-state.json hydrate
2. complete chart/runtime construction
3. primary instrument/timeframe/viewport/display restore
4. Add-ons + compare subjects restore
5. primary/add-on pane layout restore
6. actual live runtime snapshot capture
7. persisted JSON vs live runtime exhaustive comparison
8. PASS -> persistence attach
9. FAIL -> persistence detached + all mismatch paths reported
```

전수 비교 대상:

```text
primary instrument
compare subjects
timeframe / base date / adjusted
viewport / visible range
price display mode
all registered active Add-ons
all persisted Add-on properties/private state
primary price + volume pane heights
all persisted Add-on pane heights
```

불완전한 재기동 상태가 기존 JSON을 덮어쓰는 것을 금지한다.

## 검증

먼저:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후 실제 UI에서 다음을 한 번에 변경하고 재기동한다.

```text
primary 종목
비교 종목 추가
SuperTrend 등 Add-on + 속성
거래량 pane 높이
서브차트 pane 높이
timeframe
viewport / 표시갯수
가격/수익률 표시모드
```

PASS 기준:

```text
재기동 후 전부 동일
STATE RESTORE ERROR 없음
PERSISTENCE ERROR 없음
```

FAIL이면 기능별 추측 패치를 하지 않는다. `STATE RESTORE ERROR`의 전체 mismatch 목록을 기준으로 owning layer만 수정한다.

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
