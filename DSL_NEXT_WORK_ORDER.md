# DSL Strict Sequential Next-Work Order

Status: **UI CONSISTENCY ACCEPTANCE ACTIVE / 2026-09-01 KST**

기존 remediation Steps 1~15는 모두 USER-LOCAL PASS로 완료되었다. 현재는 실제 UI 경로에서 이식된 DSL과 차트 상태의 일관성을 검증한다.

## 현재 포인터

```text
CURRENT_WORK = UI-ACCEPTANCE
CURRENT_SUBSTEP = UIA-1 unified chart state restore
SUBSTEP_STATUS = SUPERTrend REAL UI PASS / PANE HEIGHT FAIL / FIX WRITTEN / REVALIDATION REQUIRED
```

기준 정책:

```text
DSL_UI_CONSISTENCY_ACCEPTANCE_POLICY.md
DSL_HUMAN_COMMUNICATION_OUTPUT_POLICY.md
```

## 현재 영속성 SSOT

```text
의미 있는 화면 변경
 -> one logical Chart State
 -> monotonic stateRevision
 -> one JSON serialization/restore path
 -> one atomic runtime JSON file
```

canonical runtime state:

```text
vendor/kiwoom-condition/condition1516/chart-platform/.runtime/chart-addons/chart-state.json
```

문서 범위:

```text
workspace
  instrument / timeframe / base date / visible count
  price mode / viewport / recent instruments
  primary price + volume pane layout
display
addons
  enabled/visible / parameters / private state
  add-on pane layout / geometry points
```

## 최신 실제 UI 결과

```text
SuperTrend 재기동 복원 = PASS
거래량 pane 높이 복원 = FAIL
서브차트 지표 pane 높이 복원 = FAIL
```

현재 원인 분류:

```text
JSON persistence = height state authority 보유
startup projection = FAIL
```

startup 동안 native chart/add-on pane 생성이 저장 높이를 다시 배치하며, 그 자동 배치값이 사용자 상태처럼 관찰될 수 있었다.

수정:

```text
startup auto-layout observation -> 저장 금지
JSON persisted heights -> startup authority 유지
all add-ons idle -> primary/add-on pane 높이 재적용
multiple layout frames -> 재적용 반복
stabilization complete -> 이후 사용자 resize만 저장
```

회귀검증:

```text
persisted volume/sub-pane heights
 -> native startup auto-layout changes actual heights
 -> persisted state must remain unchanged
 -> stabilization
 -> actual panes must equal persisted heights
 -> later user resize must persist normally
```

## UIA-1 완료 조건

자동검증과 실제 UI 모두 통과해야 한다.

```text
SuperTrend 삽입
거래량/서브 패널 높이 변경
브라우저 종료
재기동
 -> SuperTrend 복원
 -> 거래량/서브 높이 복원
 -> 기존 timeframe/workspace 유지
 -> PERSISTENCE ERROR 없음
```

실제 UI 복원 PASS 전 다음 UI 기능으로 넘어가지 않는다.

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
UI 상태를 Core 하드코딩으로 복원 금지
Bridge/Runtime에서 지표/전략/선별 계산 금지
Add-on 기능특례를 Core에 흡수 금지
JSON persistence에서 계산/지표 의미판정 금지
기능별 persistent side-store 추가 금지
localStorage를 제품 상태 authority로 사용 금지
검증 assertion 약화/skip 금지
startup 자동 레이아웃이 persisted pane state를 authority처럼 덮어쓰는 것 금지
```

## 이후 UI 기능 검증 순서

```text
1. UI에서 기능 선택/작성
2. 실행
3. 화면 결과와 deterministic engine 결과 확인
4. 실패 원인 계층 분류
5. 해당 계층만 최소 수정
6. focused regression
7. cross-layer regression
8. frozen core guard
9. 동일 UI 동작 재확인
```
