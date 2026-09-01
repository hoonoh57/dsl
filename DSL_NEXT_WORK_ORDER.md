# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-02 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 차트 상태의 완전 복원을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = WHOLE-RESTORE FIX PINNED / USER-LOCAL REVALIDATION REQUIRED
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

전수검사에서 다음이 동시에 확인됐다.

```text
메인 price pane 높이 불일치
viewport 1봉 이동 / visibleCount 1 감소
저장된 compare-1 / compare-2 / compare-3 pane 누락
```

이 실패를 기준으로 owning layer를 수정했다.

## UIA-1 restore gate

재기동은 반드시 다음 순서를 통과해야 한다.

```text
1. chart-state.json hydrate
2. primary chart/runtime construction
3. registered Add-ons restore
4. primary request ready
5. persisted compare subjects restore
6. all pane layout restore as one whole-chart ratio vector
7. persisted startup viewport reassert
8. actual live runtime snapshot capture
9. persisted JSON vs live runtime exhaustive comparison
10. PASS -> persistence attach
11. FAIL -> persistence detached + all mismatch paths reported
```

## Pane layout 규칙

개별 pane의 저장 픽셀 높이를 순차 적용하지 않는다. 차트 엔진이 다른 pane을 자동 재배치하기 때문이다.

```text
saved pane heights
 -> ordered relative weights for every native pane
 -> one bulk stretch-factor application
 -> ratio audit
```

전체 창 높이가 달라져 픽셀값이 비례 변경되는 것은 허용한다. 그러나 저장된 pane이 실제 runtime에서 누락되는 것은 계속 hard FAIL이다.

## Viewport 규칙

startup 조립 중 발생한 임시 viewport event는 authority가 아니다. 최종 layout 안정화 전후에 최초 JSON viewport/visibleCount를 다시 적용하고 그 값으로 전수검사한다.

## Compare subject 규칙

저장 비교종목은 primary request가 준비된 뒤 생성한다. 생성 실패는 단순 `missing`이 아니라 실제 pane별 실패 원인을 보고한다.

## 자동검증 범위

`verify.bat`는 다음을 포함한다.

```text
single JSON SSOT
live state/persistence path
exhaustive runtime audit
whole-chart ratio layout restore
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

먼저:

```text
git pull --ff-only origin dsl-live-studio
git submodule update --init --recursive
verify.bat
```

자동검증 PASS 후 `start.bat`으로 실제 UI를 확인한다.

한 번에 다음 상태를 만든 뒤 종료·재기동한다.

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
